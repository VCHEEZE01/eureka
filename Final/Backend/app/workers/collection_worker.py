"""타겟 수집 전용 독립 프로세스. app.workers.collection_worker RUN_ID로 실행한다."""
from __future__ import annotations

import logging
import fcntl
import json
import os
import signal
import sys
import time
from collections import defaultdict

from app.agents.evidence_agent import EvidenceAgent, EvidenceInput
from app.agents.interpreter_agent import InterpretInput, InterpreterAgent
from app.agents.problem_agent import ProblemAgent, ProblemInput
from app.config.settings import settings
from app.core.llm import get_llm, set_llm
from app.schemas.collections import CollectionCounts, CollectionRun, QueryResult, ReviewCandidate
from app.schemas.models import Category, CollectMode, LicensePolicy
from app.tools import collection_tool, corpus_tool, search_tool
from app.tools.target_query_tool import canonical_item_key, coverage_for
from app.tools.target_evidence_tool import profile_key

logger = logging.getLogger(__name__)


class CollectionTimeout(Exception):
    pass


class CollectionFailed(Exception):
    pass


def _on_timeout(signum, frame):
    raise CollectionTimeout("전체 실행 제한 시간에 도달했습니다")


class CollectionBudgetReached(Exception):
    def __init__(self, reason):
        self.reason = reason


def execute(run_id: str) -> None:
    """실제 검색·판정만 사용하며 부모 실행은 불변 스냅샷으로 이어 간다."""
    with collection_tool.store_lock():
        record = collection_tool._read(run_id)
    if record is None or record["status"] not in {"queued", "running"}:
        return
    run = CollectionRun.model_validate(record)
    if settings.CORPUS_DIR.resolve() != (collection_tool.run_dir(run_id) / "corpus").resolve():
        message = "실행별 저장소 격리 설정이 올바르지 않습니다"
        collection_tool.update_run(run_id, status="failed", stage="failed", message=message, error=message, stop_reason="failed")
        return
    error = collection_tool.configuration_error(run.queries)
    if error:
        collection_tool.update_run(run_id, status="failed", stage="failed", message=error, error=error, stop_reason="failed")
        return
    counts = CollectionCounts(queries_total=len(run.queries))
    baseline = run.cumulative_counts
    warnings = list(run.warnings)
    completed = set(record.get("completed_query_ids", []))
    topic_ids = set(record.get("searched_topic_ids", []))
    intents = set(record.get("searched_intents", []))
    processed = set(record.get("processed_raw_ids", []))
    generated = set(record.get("generated_candidate_ids", []))
    problems = {p.id: p for p in run.problems}
    reviews = dict(run.reviews)
    query_results = []
    selected_ids = set()
    new_judged_ids = set()
    failed_ids = set()
    candidates = {}
    pending_candidate_ids = set(record.get("pending_candidate_ids", []))
    started = time.monotonic()
    actual_llm = get_llm()
    current_profile_key = profile_key(run.target)

    def check_budget():
        if time.monotonic() - started >= max(1, run.limits.timeout_seconds - 5):
            raise CollectionBudgetReached("time_budget")

    class MeteredLLM:
        def complete_json(self, prompt, **kwargs):
            check_budget()
            if counts.llm_calls >= run.limits.llm_logical_calls:
                raise CollectionBudgetReached("llm_budget")
            counts.llm_calls += 1
            return actual_llm.complete_json(prompt, **kwargs)

        def complete(self, prompt, **kwargs):
            check_budget()
            if counts.llm_calls >= run.limits.llm_logical_calls:
                raise CollectionBudgetReached("llm_budget")
            counts.llm_calls += 1
            return actual_llm.complete(prompt, **kwargs)

    def statistics():
        raw = {r.id: r for r in corpus_tool.load_raw_items()}
        judged = {j.raw_item_id: j for j in corpus_tool.load_judgements()
                  if j.raw_item_id in processed and j.target_policy == "evidence_v2"
                  and j.target_profile_key == current_profile_key}
        def assign(destination, rows):
            destination.judged = len(rows)
            destination.target_confirmed = sum(j.target_status == "confirmed" for j in rows)
            destination.target_matched = destination.target_confirmed  # legacy display alias, not literal matching
            destination.target_unconfirmed = sum(j.target_status == "unconfirmed" for j in rows)
            destination.target_conflicts = sum(j.target_status == "conflict" for j in rows)
            destination.pain_detected = sum(j.is_pain for j in rows)
            destination.pain_items = sum(j.is_pain and j.confidence != "낮음" and j.target_status == "confirmed" for j in rows)
        assign(counts, [j for rid, j in judged.items() if rid in new_judged_ids])
        counts.judge_failed = len(failed_ids)
        counts.selected = len(selected_ids)
        counts.unselected = len(set(raw) - processed - selected_ids)
        cumulative = CollectionCounts(**{key: getattr(baseline, key) + getattr(counts, key) for key in CollectionCounts.model_fields})
        assign(cumulative, list(judged.values()))
        cumulative.collected = len(raw)
        cumulative.unselected = len(set(raw) - processed)
        cumulative.problems = len(problems)
        cumulative.candidates = len(candidates)
        cumulative.held = sum(r.decision != "publish" for r in reviews.values())
        review_candidates = [ReviewCandidate(
            raw_item_id=j.raw_item_id, pain_summary=j.pain_summary,
            target_status=j.target_status,
            reason="불편 경험은 발견했으나 입력한 타겟의 동일 경험임을 확인하지 못했습니다" if j.target_status == "unconfirmed" else "원문에서 확인된 경험자의 조건이 입력한 타겟과 다릅니다",
            source_url=str(raw[j.raw_item_id].url), source_name=raw[j.raw_item_id].source_name,
        ) for j in judged.values() if j.is_pain and j.pain_summary and j.target_status != "confirmed" and j.raw_item_id in raw]
        exclusions = {"target_unconfirmed": cumulative.target_unconfirmed,
                      "target_conflict": cumulative.target_conflicts,
                      "not_pain": sum(j.pain_status == "not_pain" for j in judged.values()),
                      "insufficient": sum(j.pain_status == "insufficient" for j in judged.values()),
                      "rule_filtered": len(processed - set(judged)),
                      "awaiting_judgement": len(set(raw) - processed)}
        coverage = coverage_for(run.target, completed_ids=completed, topic_ids=topic_ids, intents=intents)
        has_more = bool(coverage.catalog_remaining or set(raw) - processed or (set(candidates) | pending_candidate_ids) - generated)
        return dict(counts=counts.model_dump(), cumulative_counts=cumulative.model_dump(),
                    problems=[p.model_dump(mode="json") for p in problems.values()],
                    reviews={key: value.model_dump(mode="json") for key, value in reviews.items()},
                    warnings=list(dict.fromkeys(warnings)), query_results=[q.model_dump(mode="json") for q in query_results],
                    coverage=coverage.model_dump(), has_more=has_more,
                    review_candidates=[r.model_dump(mode="json") for r in review_candidates], exclusion_reasons=exclusions,
                    completed_query_ids=sorted(completed), searched_topic_ids=sorted(topic_ids), searched_intents=sorted(intents),
                    processed_raw_ids=sorted(processed), generated_candidate_ids=sorted(generated),
                    pending_candidate_ids=sorted((set(candidates) | pending_candidate_ids) - generated))

    def report(stage, message):
        collection_tool.update_run(run_id, status="running", stage=stage, message=message, **statistics())

    set_llm(MeteredLLM())
    try:
        collection_tool.prepare_corpus_snapshot(run)
        report("searching", "전체 주제와 타겟 맥락의 검색어를 이번 회차 예산에 맞춰 수집합니다")
        search_tool.reset_run_state()
        previous_raw = corpus_tool.load_raw_items()
        seen_keys = {canonical_item_key(item) for item in previous_raw}
        seen_hashes = {item.content_hash for item in previous_raw if item.content_hash}
        for query in run.queries:
            check_budget()
            result = search_tool.search_endpoint(query.keyword, query.source_kind, query.provider,
                                                 query.endpoint, limit=run.limits.items_per_query)
            counts.queries_done += 1
            fresh = []
            if result.succeeded:
                counts.search_succeeded += 1
                counts.fetched += len(result.items)
                for item in result.items:
                    key = canonical_item_key(item)
                    if key in seen_keys or (item.content_hash and item.content_hash in seen_hashes):
                        continue
                    seen_keys.add(key)
                    if item.content_hash:
                        seen_hashes.add(item.content_hash)
                    fresh.append(item.model_copy(update={"collected_by": CollectMode.REALTIME,
                                                         "license": LicensePolicy.SUMMARY_ONLY}))
                corpus_tool.save_raw_items(fresh, category=query.category)
                counts.collected += len(fresh)
            else:
                counts.search_failed += 1
                if result.error:
                    warnings.append(result.error)
            # 실패한 검색도 시도 이력을 남긴다. 같은 실패 쿼리에 모든 회차가 갇히지 않는다.
            completed.add(query.id)
            topic_ids.add(query.topic_id)
            intents.add(query.intent)
            query_results.append(QueryResult(query_id=query.id, keyword=query.keyword, category=query.category,
                topic=query.topic, intent=query.intent, source_name=query.source_name,
                status="succeeded" if result.succeeded else "failed", result_count=len(result.items),
                new_count=len(fresh), error=result.error if not result.succeeded else None))
            report("searching", f"검색 요청 {counts.queries_done}/{counts.queries_total} 처리")
        if run.queries and counts.search_succeeded == 0:
            raise CollectionFailed("모든 검색 요청에 실패했습니다. 빈 검색 결과로 처리하지 않았습니다")
        if counts.search_failed:
            warnings.append("일부 검색 요청이 실패했습니다. 성공한 출처의 결과만 반영했습니다.")
        report("interpreting", "입력 문구가 생략된 글도 실제 불편과 경험자의 타겟 근거를 함께 판별합니다")
        remaining = run.limits.judged_items
        for category in Category:
            check_budget()
            raw = corpus_tool.load_raw_items(category=category)
            if not raw:
                continue
            # 쿼리별 순환 표집. 원문 저장량과 판별 예산을 분리한다.
            pools = defaultdict(list)
            for item in raw:
                if item.id not in processed:
                    pools[item.query_keyword].append(item)
            items = []
            cap = min(run.limits.items_per_category, remaining)
            for offset in range(max((len(pool) for pool in pools.values()), default=0)):
                for pool in pools.values():
                    if offset < len(pool) and len(items) < cap:
                        items.append(pool[offset])
            if items and counts.llm_calls >= run.limits.llm_logical_calls:
                raise CollectionBudgetReached("llm_budget")
            remaining -= len(items)
            # LLM 한 batch마다 판정을 저장·체크포인트한다. 호출 예산이 작아도
            # 앞 batch의 성공 판정을 다음 회차에서 다시 과금하지 않는다.
            batch_size = max(1, settings.JUDGE_BATCH_SIZE)
            batches = [items[offset:offset + batch_size] for offset in range(0, len(items), batch_size)] or [[]]
            for batch in batches:
                check_budget()
                if batch and counts.llm_calls >= run.limits.llm_logical_calls:
                    raise CollectionBudgetReached("llm_budget")
                selected_set = {item.id for item in batch}
                selected_ids.update(selected_set)
                agent = InterpreterAgent()
                found = agent.run(InterpretInput(items=batch, category=category, use_llm=True,
                    include_pending=True, max_llm_items=len(batch), track_llm_failures=True,
                    target_profile=run.target, require_target_confirmation=True))
                candidates.update({c.id: c for c in found})
                candidates.update({c.id: c for c in corpus_tool.load_pending_candidates()})
                diagnostics = agent.llm_diagnostics
                if hasattr(agent, "processed_raw_ids"):
                    successful = set(agent.processed_raw_ids)
                else:
                    successful = set() if diagnostics.get("failed_items") or diagnostics.get("missing_items") else selected_set
                processed.update(successful)
                new_judged_ids.update(successful)
                failed_ids.update(selected_set - successful)
                if selected_set - successful:
                    warnings.append(f"{category.value} 모델 판별에 실패하거나 응답이 누락된 자료는 다음 회차에 다시 처리합니다.")
                report("interpreting", f"{category.value} 분석 저장 · 이번 탐색에서 {len(processed)}건 처리했습니다")
        if failed_ids and not counts.judged:
            raise CollectionFailed("모델 판별 요청에 실패했습니다. 불편이 없다는 결과로 처리하지 않았습니다")
        for candidate in corpus_tool.load_pending_candidates():
            candidates[candidate.id] = candidate
        # 배치마다 누적 묶기를 수행하므로 이전 배치의 부분집합은 최종 후보가 아니다.
        candidates = {key: candidate for key, candidate in candidates.items()
                      if not any(candidate.category == other.category and set(candidate.raw_item_ids) < set(other.raw_item_ids)
                                 for other in candidates.values())}
        pending_candidate_ids = set(candidates) - generated
        counts.candidates = len(candidates)
        # 새 누적 묶음에서 사라진 과거 분할 문제는 중복으로 남기지 않는다.
        problems = {key: value for key, value in problems.items() if key in candidates}
        reviews = {key: value for key, value in reviews.items() if key in candidates}
        queues = {category: sorted((c for c in candidates.values() if c.category == category and c.id not in generated),
                                  key=lambda c: (-len(c.raw_item_ids), c.id)) for category in Category}
        selected = []
        for offset in range(run.limits.problem_candidates):
            for category in Category:
                if offset < len(queues[category]) and len(selected) < run.limits.problem_candidates:
                    selected.append(queues[category][offset])
        report("evidence", "확인된 동일 경험의 근거로 건수와 게시 기준을 계산합니다")
        bundles = EvidenceAgent().run(EvidenceInput(candidates=selected))
        by_id = {c.id: c for c in selected}
        generation_failures = 0
        for bundle in bundles:
            check_budget()
            if run.limits.llm_logical_calls - counts.llm_calls < 3:
                raise CollectionBudgetReached("llm_budget")
            report("generating", "확인된 근거의 문제정의와 검토용 설명을 작성합니다")
            output = ProblemAgent().run(ProblemInput(candidate=by_id[bundle.candidate_id], evidence_bundle=bundle,
                                                     persist=False, allow_hold_draft=True))
            reviews[bundle.candidate_id] = output.review
            counts.generation_retries += max(0, getattr(output, "generation_attempts", 0) - 1)
            if "생성 또는 검수 실패" in output.review.reason:
                generation_failures += 1
                counts.generation_failed += 1
            else:
                generated.add(bundle.candidate_id)
            if output.problem is not None:
                problems[output.problem.id] = output.problem
                counts.problems += 1
            counts.held += int(output.review.decision != "publish")
            report("generating", f"이번 회차 문제정의 {counts.problems}개 생성")
        if generation_failures:
            if not counts.problems:
                raise CollectionFailed("문제정의 생성 또는 검수 호출에 실패했습니다. 다음 회차에서 재시도할 수 있습니다")
            warnings.append("일부 문제정의 생성·검수에 실패했습니다. 해당 후보는 다음 회차에서 재시도합니다.")
        payload = statistics()
        message = f"검토용 문제정의 {len(problems)}개를 만들었습니다. 타겟 미확인 불편은 검토 후보로 별도 보존합니다"
        if counts.search_failed:
            message = "일부 검색 실패 · " + message
        collection_tool.update_run(run_id, status="completed", stage="completed", message=message,
            stop_reason="round_budget" if payload["has_more"] else "catalog_exhausted", **payload)
    except CollectionBudgetReached as exc:
        collection_tool.update_run(run_id, status="completed", stage="completed", stop_reason=exc.reason,
            message="이번 회차 예산에 도달했습니다. 저장된 자료와 남은 탐색을 이어서 처리할 수 있습니다", **statistics())
    except (CollectionFailed, CollectionTimeout) as exc:
        message = str(exc)
        collection_tool.update_run(run_id, status="failed", stage="failed", message=message, error=message,
                                   stop_reason="failed", **statistics())
    except Exception:
        logger.exception("수집 worker 실패: %s", run_id)
        message = "수집 실행 중 오류가 발생했습니다. 서버의 실행 기록을 확인하세요"
        collection_tool.update_run(run_id, status="failed", stage="failed", message=message, error=message,
                                   stop_reason="failed", **statistics())
    finally:
        set_llm(actual_llm)


def main() -> int:
    if len(sys.argv) != 2:
        return 2
    run_id = sys.argv[1]
    # 커널이 worker 종료 시 자동 해제하는 lock으로 서버 재시작 뒤에도 생존을 확인한다.
    lock_path = collection_tool.run_dir(run_id) / "worker.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as worker_lock:
        try:
            fcntl.flock(worker_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 0  # 같은 실행의 worker가 이미 살아 있다. 중복 외부 호출을 하지 않는다.
        worker_lock.seek(0)
        worker_lock.truncate()
        json.dump({"pid": os.getpid(), "run_id": run_id}, worker_lock)
        worker_lock.flush()
        with collection_tool.store_lock():
            record = collection_tool._read(run_id)
        if record is None:
            return 2
        signal.signal(signal.SIGALRM, _on_timeout)
        signal.alarm(record["limits"]["timeout_seconds"])
        try:
            execute(run_id)
        finally:
            signal.alarm(0)
    return 0



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())
