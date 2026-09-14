"""실시간 타겟 수집. 모든 원문과 모델 응답은 명시적인 합성 테스트 자료다."""
from datetime import timedelta
import json

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config.settings import settings
from app.core.llm import LLMError, reset_llm, set_llm
from app.schemas.collections import TargetProfile
from app.schemas.models import Category, SourceKind
from app.tools import collection_tool, corpus_tool, search_tool
from app.tools.collection_tool import _is_alive as actual_worker_liveness
from app.tools.target_query_tool import build_target_queries
from app.workers import collection_worker
from main import app


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setattr(settings, "LLM_DRY_RUN", False)
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "synthetic-key")
    monkeypatch.setattr(settings, "NAVER_CLIENT_ID", "synthetic-id")
    monkeypatch.setattr(settings, "NAVER_CLIENT_SECRET", "synthetic-secret")
    monkeypatch.setattr(settings, "KAKAO_REST_API_KEY", "synthetic-key")
    monkeypatch.setattr(collection_tool, "_launch_worker", lambda _: 12345)
    monkeypatch.setattr(collection_tool, "_is_alive", lambda _: True)
    yield
    reset_llm()


def target(**kw):
    return TargetProfile(age="30대", jobs=["군인"], **kw)


def prepare_worker(run, monkeypatch):
    monkeypatch.setattr(settings, "CORPUS_DIR", collection_tool.run_dir(run.id) / "corpus")
    monkeypatch.setattr(settings, "PROBLEMS_DIR", collection_tool.run_dir(run.id) / "private-problems")


@pytest.mark.parametrize("payload", [
    {}, {"age": "30대"}, {"age": "30대", "jobs": [" "]},
    {"age": "30대", "jobs": ["군인"] * 6}, {"age": "30대", "jobs": ["a" * 31]},
    {"age": "30대", "jobs": ["군인\n명령"]}, {"age": "30대", "jobs": ["a OR b"]},
    {"age": "30대", "jobs": ["<script>"]}, {"age": "30대", "jobs": [42]},
    {"age": "60대", "jobs": ["군인"]},
])
def test_target_rejects_invalid_or_underfilled_input(payload):
    with pytest.raises(ValidationError):
        TargetProfile.model_validate(payload)


def test_target_normalizes_aliases_and_set_order():
    value = TargetProfile(age="30대", gender="남자", jobs=["  군인  ", "군인", "개발자"])
    assert value.gender == "남성" and value.jobs == ["개발자", "군인"]


def test_query_plan_is_budgeted_and_searches_broad_context():
    value = TargetProfile(age="20대", gender="여성", jobs=["디자이너", "개발자"], places=["집", "사무실"])
    queries = build_target_queries(value)
    assert len(queries) == settings.COLLECTION_QUERY_BUDGET
    assert {q.category for q in queries} == set(Category)
    assert len({q.intent for q in queries}) == 9
    assert any(value.age not in q.keyword and value.gender not in q.keyword for q in queries)
    assert {q.source_name for q in queries} == {"네이버 뉴스", "네이버 지식iN", "네이버 카페", "다음 블로그"}
    assert len(build_target_queries(TargetProfile(jobs=[f"직업{i}" for i in range(5)], places=[f"장소{i}" for i in range(5)]))) == settings.COLLECTION_QUERY_BUDGET


def test_same_target_is_reused_and_different_active_request_is_blocked(configured):
    first = collection_tool.create_run(target())
    second = collection_tool.create_run(target())
    assert first.id == second.id and second.reused
    with pytest.raises(collection_tool.CollectionBusyError):
        collection_tool.create_run(TargetProfile(age="20대", jobs=["학생"]))


def test_completed_ttl_reuse_then_fresh_run(configured):
    first = collection_tool.create_run(target())
    collection_tool.update_run(first.id, status="completed", stage="completed")
    assert collection_tool.create_run(target()).id == first.id
    with collection_tool.store_lock():
        record = collection_tool._read(first.id)
        record["updated_at"] = (collection_tool.now() - timedelta(hours=2)).isoformat()
        # write directly only to simulate old recorded clock; _write normally advances it.
        (collection_tool.run_dir(first.id) / "run.json").write_text(json.dumps(record), encoding="utf-8")
    assert collection_tool.create_run(target()).id != first.id


def test_dead_worker_is_failed_and_explicit_retry_gets_new_id(configured, monkeypatch):
    first = collection_tool.create_run(target())
    monkeypatch.setattr(collection_tool, "_is_alive", lambda _: False)
    failed = collection_tool.get_run(first.id)
    assert failed.status == "failed" and "중단" in failed.error
    second = collection_tool.create_run(target())
    assert second.id != first.id


def test_dry_run_or_missing_key_is_explicit_failure_without_launch(monkeypatch):
    called = []
    monkeypatch.setattr(collection_tool, "_launch_worker", lambda rid: called.append(rid))
    result = collection_tool.create_run(target())
    assert result.status == "failed" and "LLM_DRY_RUN" in result.error and not called
    monkeypatch.setattr(settings, "LLM_DRY_RUN", False)
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    result = collection_tool.create_run(target())
    assert result.status == "failed" and "GEMINI_API_KEY" in result.error and not called


def test_worker_environment_isolated_and_quota_shared(configured):
    before = settings.CORPUS_DIR
    first = collection_tool.create_run(target())
    env = collection_tool._worker_environment(first.id)
    assert env["CORPUS_DIR"] == str((collection_tool.run_dir(first.id) / "corpus").resolve())
    assert env["SEARCH_QUOTA_DIR"] == str(before.resolve())
    assert settings.CORPUS_DIR == before and env["COLLECT_MAX_PAGES"] == "1"


def test_gets_do_not_start_collection_and_api_hides_internal_fields(configured, monkeypatch):
    called = []
    monkeypatch.setattr(collection_tool, "_launch_worker", lambda rid: called.append(rid) or 12345)
    with TestClient(app) as client:
        assert client.get("/").status_code == 200
        assert client.get("/collections/col-" + "0" * 24).status_code == 404
        assert not called
        response = client.post("/collections", json={"target": target().model_dump()})
        assert response.status_code == 202
        data = response.json()
        assert len(called) == 1 and data["counts"]["queries_total"] == settings.COLLECTION_QUERY_BUDGET
        assert "worker_pid" not in data and "fingerprint" not in data and "schema_version" not in data
        assert client.get(f"/collections/{data['id']}").status_code == 200
        assert len(called) == 1
        assert client.post("/collections", json={"target": {"age": "30대"}}).status_code == 422


def test_worker_distinguishes_successful_empty_and_total_search_failure(configured, monkeypatch):
    run = collection_tool.create_run(target())
    prepare_worker(run, monkeypatch)
    monkeypatch.setattr(search_tool, "search_endpoint", lambda *a, **kw: search_tool.SearchReport([], True))
    collection_worker.execute(run.id)
    assert collection_tool.get_run(run.id).status == "completed"
    assert collection_tool.get_run(run.id).counts.search_succeeded == settings.COLLECTION_QUERY_BUDGET
    # Different target creates another independent run; no prior items enter it.
    second = collection_tool.create_run(TargetProfile(age="20대", jobs=["학생"]))
    prepare_worker(second, monkeypatch)
    monkeypatch.setattr(search_tool, "search_endpoint", lambda *a, **kw: search_tool.SearchReport([], False, "합성 검색 실패"))
    collection_worker.execute(second.id)
    failed = collection_tool.get_run(second.id)
    assert failed.status == "failed" and "모든 검색" in failed.error
    assert failed.counts.search_failed == settings.COLLECTION_QUERY_BUDGET and failed.counts.collected == 0


def test_worker_partial_search_failure_is_visible(configured, monkeypatch):
    run = collection_tool.create_run(target())
    prepare_worker(run, monkeypatch)
    def partial(keyword, *args, **kw):
        return search_tool.SearchReport([], "가계부" not in keyword, "합성 검색 실패")
    monkeypatch.setattr(search_tool, "search_endpoint", partial)
    collection_worker.execute(run.id)
    result = collection_tool.get_run(run.id)
    assert result.status == "completed" and result.counts.search_failed == 1
    assert "일부 검색 실패" in result.message and result.warnings


def test_synthetic_positive_chain_collects_judges_builds_private_problem(configured, monkeypatch, make_raw_item):
    """검색·LLM 외에는 실제 수집→판별→묶기→근거→문제생성 코드 경로를 통과한다."""
    run = collection_tool.create_run(target())
    prepare_worker(run, monkeypatch)
    snippets = [
        "합성 자료입니다. 저는 30대 군인인데 회의록 정리할 때 매번 담당자가 쓴 내용을 옮기는 일이 번거롭습니다. 기록을 정리하는 방식이 개선됐으면 좋겠습니다.",
        "합성 자료입니다. 저는 30대 군인인데 회의록 정리할 때 매번 내용을 옮겨야 하는 일이 번거롭습니다. 정리 방식이 개선됐으면 좋겠습니다.",
    ]
    rows = [make_raw_item(id=f"synthetic-live-{i}", title="회의록 정리가 번거롭습니다", snippet=text,
                          query_keyword="30대 군인 회의록 불편", source_kind=SourceKind.COMMUNITY,
                          source_name="네이버 카페") for i, text in enumerate(snippets)]
    monkeypatch.setattr(search_tool, "search_endpoint", lambda keyword, *args, **kw:
                        search_tool.SearchReport(rows if "회의록" in keyword else [], True))
    class SyntheticLLM:
        def complete_json(self, prompt, **kw):
            if "불편 판별" in prompt or '"is_pain"' in prompt:
                return [{"id": row.id, "is_pain": True, "confidence": "높음", "severity": "높음",
                         "pain_summary": "기록 내용을 다른 문서에 재작성하는 과정의 부담", "has_need_signal": True,
                         "pain_status": "pain", "experience_type": "self", "experience_evidence": row.snippet,
                         "target_field_status": {"age": "confirmed", "jobs": "confirmed"},
                         "target_values": {"age": "30대", "jobs": "군인"},
                         "target_evidence": {"age": "저는 30대 군인인데", "jobs": "저는 30대 군인인데"}} for row in rows]
            if "검수자" in prompt:
                return {"decision": "hold", "reason": "합성 자료 검토 전용이며 게시 근거가 부족합니다"}
            return {"title": "회의 기록 재정리의 번거로움", "one_liner": "회의 기록을 다시 정리하는 과정에서 불편이 나타난다.",
                    "description": "회의 기록을 옮겨 정리하는 작업의 번거로움이 언급된다.",
                    "context": "회의 기록 정리 상황이다. 구체적인 원인은 확인이 필요하다.",
                    "complexity_note": "현재 기록 정리 절차와 자료 형식을 확인해야 한다."}
    set_llm(SyntheticLLM())
    collection_worker.execute(run.id)
    result = collection_tool.get_run(run.id)
    assert result.status == "completed", result.error
    assert result.counts.collected == 2 and result.counts.judged == 2
    assert result.counts.pain_items == 2 and result.problems
    problem = result.problems[0]
    assert problem.evidence and problem.evidence[0].source_url
    assert result.reviews[problem.id].decision == "hold"
    assert not settings.PROBLEMS_DIR.exists()
    assert all(item.collected_by.value == "realtime" for item in corpus_tool.load_raw_items())
    assert result.counts.llm_calls == 3


def test_structured_search_report_does_not_hide_blocked_or_invalid_payload(configured, monkeypatch):
    monkeypatch.setattr(search_tool, "is_blocked", lambda _: True)
    assert not search_tool.search_endpoint("합성 검색", SourceKind.NEWS, "naver", "news").succeeded
    monkeypatch.setattr(search_tool, "is_blocked", lambda _: False)
    monkeypatch.setattr(search_tool, "_get_json", lambda *a: {"unexpected": []})
    assert not search_tool.search_endpoint("합성 검색", SourceKind.NEWS, "naver", "news").succeeded


def test_shared_quota_path_does_not_reset_with_new_corpus(configured, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "SEARCH_QUOTA_DIR", tmp_path / "shared-quota")
    monkeypatch.setattr(settings, "CORPUS_DIR", tmp_path / "first-corpus")
    search_tool._consume_quota("naver")
    monkeypatch.setattr(settings, "CORPUS_DIR", tmp_path / "second-corpus")
    search_tool._consume_quota("naver")
    assert search_tool.read_quota()["naver"] == 2


def test_all_received_raws_are_saved_but_judging_selection_is_capped(configured, monkeypatch, make_raw_item):
    monkeypatch.setattr(settings, "COLLECTION_QUERY_BUDGET", 40)
    monkeypatch.setattr(settings, "COLLECTION_ITEMS_PER_QUERY", 10)
    monkeypatch.setattr(settings, "COLLECTION_JUDGE_PER_CATEGORY", 40)
    monkeypatch.setattr(settings, "COLLECTION_JUDGE_BUDGET", 200)
    run = collection_tool.create_run(TargetProfile(age="30대", jobs=["군인", "개발자"]))
    prepare_worker(run, monkeypatch)
    index = {"next": 0}
    def abundant(keyword, kind, *args, **kw):
        rows = []
        for i in range(10):
            index["next"] += 1
            rows.append(make_raw_item(id=f"synthetic-many-{index['next']}", query_keyword=keyword,
                                      title="합성 일반 자료", snippet="30대 군인 합성 테스트의 신호 없는 글입니다", source_kind=kind))
        return search_tool.SearchReport(rows, True)
    monkeypatch.setattr(search_tool, "search_endpoint", abundant)
    collection_worker.execute(run.id)
    result = collection_tool.get_run(run.id)
    assert result.status == "completed", result.error
    assert result.counts.fetched == 400 and result.counts.collected == 400
    assert result.counts.selected == 200 and result.counts.unselected == 200
    assert len(corpus_tool.load_raw_items()) == 400
    assert result.limits.collected_items == 400 and result.limits.judged_items == 200


def test_judge_call_failure_cannot_be_reported_as_successful_empty(configured, monkeypatch, make_raw_item):
    run = collection_tool.create_run(target())
    prepare_worker(run, monkeypatch)
    row = make_raw_item(id="synthetic-llm-fail", title="회의록 작성이 번거롭습니다",
                        snippet="30대 군인인데 회의록 내용을 매번 다시 정리하는 작업이 너무 번거롭습니다. 개선됐으면 좋겠습니다", query_keyword="회의록 불편")
    monkeypatch.setattr(search_tool, "search_endpoint", lambda keyword, *a, **kw:
                        search_tool.SearchReport([row] if "회의록" in keyword else [], True))
    class BrokenLLM:
        def complete_json(self, *a, **kw):
            raise LLMError("synthetic unavailable")
    set_llm(BrokenLLM())
    collection_worker.execute(run.id)
    result = collection_tool.get_run(run.id)
    assert result.status == "failed" and "모델 판별" in result.error
    assert not result.problems


def test_worker_timeout_is_terminal_and_has_explicit_error(configured, monkeypatch):
    run = collection_tool.create_run(target())
    prepare_worker(run, monkeypatch)
    def timeout(*a, **kw):
        raise collection_worker.CollectionTimeout("합성 실행 시간 초과")
    monkeypatch.setattr(search_tool, "search_endpoint", timeout)
    collection_worker.execute(run.id)
    result = collection_tool.get_run(run.id)
    assert result.status == "failed" and "시간 초과" in result.error


def test_deadline_reconciliation_does_not_leave_running_forever(configured):
    run = collection_tool.create_run(target())
    with collection_tool.store_lock():
        record = collection_tool._read(run.id)
        record["created_at"] = (collection_tool.now() - timedelta(hours=2)).isoformat()
        collection_tool._write(record)
    assert collection_tool.get_run(run.id).status == "failed"


def test_all_missing_model_ids_fail_instead_of_counting_as_judged(configured, monkeypatch, make_raw_item):
    run = collection_tool.create_run(target())
    prepare_worker(run, monkeypatch)
    row = make_raw_item(id="synthetic-missing", title="회의록 작성이 번거롭습니다",
                        snippet="30대 군인인데 회의록 내용을 매번 다시 정리하는 작업이 너무 번거롭습니다. 개선됐으면 좋겠습니다", query_keyword="회의록 불편")
    monkeypatch.setattr(search_tool, "search_endpoint", lambda keyword, *a, **kw:
                        search_tool.SearchReport([row] if "회의록" in keyword else [], True))
    class MissingLLM:
        def complete_json(self, *a, **kw):
            return []
    set_llm(MissingLLM())
    collection_worker.execute(run.id)
    result = collection_tool.get_run(run.id)
    assert result.status == "failed" and result.counts.judged == 0
    assert result.counts.judge_failed == 1


def test_raw_received_before_timeout_is_already_preserved(configured, monkeypatch, make_raw_item):
    run = collection_tool.create_run(target())
    prepare_worker(run, monkeypatch)
    row = make_raw_item(id="synthetic-before-timeout")
    calls = {"n": 0}
    def stop_after_first(*a, **kw):
        calls["n"] += 1
        if calls["n"] > 1:
            raise collection_worker.CollectionTimeout("합성 실행 시간 초과")
        return search_tool.SearchReport([row], True)
    monkeypatch.setattr(search_tool, "search_endpoint", stop_after_first)
    collection_worker.execute(run.id)
    result = collection_tool.get_run(run.id)
    assert result.status == "failed" and result.counts.collected == 1
    assert [item.id for item in corpus_tool.load_raw_items()] == [row.id]


def test_target_mentions_checks_all_fields_on_raw_text_only(make_raw_item):
    from app.tools.target_query_tool import input_mentions
    profile = TargetProfile(age="30대", gender="남성", jobs=["군인", "개발자"], places=["사무실", "집"])
    assert input_mentions(profile, make_raw_item(title="３０대 남자 개발자", snippet="사 무 실에서 겪는 불편"))
    assert not input_mentions(profile, make_raw_item(title="30대 남자 개발자", snippet="회의가 번거롭다"))
    assert not input_mentions(profile, make_raw_item(title="회의록 정리 불편", snippet="번거롭습니다", query_keyword="30대 남성 군인 사무실"))


def test_unconfirmed_pain_is_judged_and_preserved_as_separate_review_candidate(configured, monkeypatch, make_raw_item):
    run = collection_tool.create_run(target())
    prepare_worker(run, monkeypatch)
    row = make_raw_item(id="synthetic-unrelated", title="회의록 작성이 번거롭습니다",
                        snippet="저는 회의록 내용을 매번 다시 정리하는 작업이 너무 번거롭습니다. 개선됐으면 좋겠습니다")
    monkeypatch.setattr(search_tool, "search_endpoint", lambda *a, **kw: search_tool.SearchReport([row], True))
    class UnconfirmedLLM:
        def complete_json(self, *a, **kw):
            return [{"id": row.id, "is_pain": True, "pain_status": "pain", "confidence": "높음",
                     "experience_type": "self", "experience_evidence": row.snippet,
                     "pain_summary": "회의록 재정리의 번거로움"}]
    set_llm(UnconfirmedLLM())
    collection_worker.execute(run.id)
    result = collection_tool.get_run(run.id)
    assert result.status == "completed", result.error
    assert not result.problems and result.counts.collected == 1
    assert result.counts.target_unconfirmed == result.counts.judged == result.counts.pain_detected == 1
    assert result.counts.target_confirmed == result.counts.pain_items == 0
    assert result.review_candidates[0].source_url == row.url
    assert result.review_candidates[0].pain_summary == "회의록 재정리의 번거로움"
    assert result.target_match_policy == "evidence_v2"


def test_old_record_is_preserved_as_not_checked_and_not_reused(configured):
    old = collection_tool.create_run(target())
    collection_tool.update_run(old.id, status="completed", stage="completed")
    with collection_tool.store_lock():
        record = collection_tool._read(old.id)
        del record["target_match_policy"]
        record["fingerprint"] = "old-query-plan-fingerprint"
        record["plan_version"] = "catalog-v3:synthetic-old-plan"
        collection_tool._write(record)
    before = (collection_tool.run_dir(old.id) / "run.json").read_bytes()
    legacy = collection_tool.get_run(old.id)
    assert legacy.target_match_policy == "not_checked"
    assert legacy.current_plan_version != legacy.plan_version and not legacy.can_resume
    with pytest.raises(collection_tool.CollectionRequestError):
        collection_tool.create_run(target(), resume_from=old.id)
    assert collection_tool.create_run(target()).id != old.id
    assert (collection_tool.run_dir(old.id) / "run.json").read_bytes() == before


def test_known_demographic_label_conflict_excludes_candidate_but_unknown_is_not_invented(make_judgement):
    from app.tools.target_query_tool import target_label_conflicts
    profile = TargetProfile(age="30대", gender="여성")
    assert target_label_conflicts(profile, make_judgement(sufferer_age_band="20대"))
    assert target_label_conflicts(profile, make_judgement(sufferer_gender="남자"))
    unknown = make_judgement(sufferer_age_band=None, sufferer_gender=None)
    assert not target_label_conflicts(profile, unknown)
    assert unknown.sufferer_age_band is None and unknown.sufferer_gender is None


def test_explicit_conflicting_age_is_not_in_problem_candidates(configured, monkeypatch, make_raw_item):
    run = collection_tool.create_run(target())
    prepare_worker(run, monkeypatch)
    row = make_raw_item(id="synthetic-age-conflict", title="30대 군인 관련 회의록 질문",
                        snippet="저는 20대인데 30대 군인 선배의 회의록 정리 요청이 매번 너무 번거롭습니다. 개선됐으면 좋겠습니다", query_keyword="회의록 불편")
    monkeypatch.setattr(search_tool, "search_endpoint", lambda keyword, *a, **kw:
                        search_tool.SearchReport([row] if "회의록" in keyword else [], True))
    class ConflictingLLM:
        def complete_json(self, *a, **kw):
            return [{"id": row.id, "is_pain": True, "confidence": "높음", "severity": "높음",
                     "pain_summary": "기록 재작성 과정의 번거로움", "sufferer_age_band": "20대",
                     "pain_status": "pain", "experience_type": "self", "experience_evidence": row.snippet,
                     "target_values": {"age": "20대"}, "target_evidence": {"age": "저는 20대인데"}}]
    set_llm(ConflictingLLM())
    collection_worker.execute(run.id)
    result = collection_tool.get_run(run.id)
    assert result.status == "completed" and result.counts.target_matched == 0
    assert result.counts.target_conflicts == 1 and not result.problems
    assert result.counts.candidates == 0


def test_timeout_does_not_release_slot_when_worker_exit_is_unconfirmed(configured, monkeypatch):
    run = collection_tool.create_run(target())
    with collection_tool.store_lock():
        record = collection_tool._read(run.id)
        record["created_at"] = (collection_tool.now() - timedelta(hours=2)).isoformat()
        collection_tool._write(record)
    monkeypatch.setattr(collection_tool, "_terminate_timed_out_worker", lambda _: False)
    assert collection_tool.get_run(run.id).status == "queued"
    with pytest.raises(collection_tool.CollectionBusyError):
        collection_tool.create_run(TargetProfile(age="20대", jobs=["학생"]))


def test_worker_lock_is_authoritative_and_released_when_owner_exits(configured):
    import fcntl
    run = collection_tool.create_run(target())
    record = collection_tool._read(run.id)
    path = collection_tool.run_dir(run.id) / "worker.lock"
    assert not collection_tool._worker_lock_held(record)
    with path.open("a+") as owner:
        fcntl.flock(owner.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert collection_tool._worker_lock_held(record)
    assert not collection_tool._worker_lock_held(record)



def test_queued_import_gap_is_not_false_dead_but_expired_unlocked_run_is(configured):
    run = collection_tool.create_run(target())
    record = collection_tool._read(run.id)
    assert actual_worker_liveness(record)
    record["created_at"] = (collection_tool.now() - timedelta(seconds=20)).isoformat()
    assert not actual_worker_liveness(record)


def test_late_worker_does_not_execute_already_failed_run(configured, monkeypatch):
    run = collection_tool.create_run(target())
    collection_tool.update_run(run.id, status="failed", stage="failed", error="합성 시작 지연")
    calls = []
    monkeypatch.setattr(search_tool, "search_endpoint", lambda *a, **kw: calls.append(a))
    collection_worker.execute(run.id)
    assert not calls and collection_tool.get_run(run.id).status == "failed"


def test_second_worker_for_same_run_exits_without_external_calls(configured, monkeypatch):
    import fcntl
    import sys
    run = collection_tool.create_run(target())
    monkeypatch.setattr(sys, "argv", ["worker", run.id])
    path = collection_tool.run_dir(run.id) / "worker.lock"
    with path.open("a+") as owner:
        fcntl.flock(owner.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert collection_worker.main() == 0
    assert collection_tool.get_run(run.id).counts.queries_done == 0


def synthetic_catalog(monkeypatch, size=1):
    """Small, explicitly synthetic catalogue lets tests reach the final backlog round."""
    from app.schemas.collections import CollectionCoverage
    queries = build_target_queries(target(), budget=size)
    monkeypatch.setattr(collection_tool, "build_target_queries", lambda target, completed_ids: [q for q in queries if q.id not in completed_ids][:1])
    def coverage(target, *, completed_ids, topic_ids, intents):
        done = len(set(completed_ids))
        return CollectionCoverage(catalog_total=size, catalog_completed=done, catalog_remaining=max(0, size-done),
                                  topics_total=size, topics_searched=len(set(topic_ids)), intents_searched=len(set(intents)))
    monkeypatch.setattr(collection_tool, "coverage_for", coverage)
    monkeypatch.setattr(collection_worker, "coverage_for", coverage)
    return queries


class SyntheticEvidenceLLM:
    def __init__(self, rows, confirmed=True):
        self.rows, self.confirmed, self.judged_ids = rows, confirmed, []

    def complete_json(self, prompt, **kwargs):
        if '"is_pain"' in prompt:
            selected = [row for row in self.rows if row.id in prompt]
            self.judged_ids.extend(row.id for row in selected)
            return [{"id": row.id, "is_pain": True, "pain_status": "pain", "confidence": "높음",
                     "severity": "높음", "pain_summary": "회의 기록을 매번 옮기는 번거로움",
                     "experience_type": "self", "experience_evidence": row.snippet,
                     "target_field_status": {"age": "confirmed", "jobs": "confirmed"},
                     "target_values": {"age": "30대", "jobs": "군인"},
                     "target_evidence": {"age": "저는 30대 군인인데", "jobs": "저는 30대 군인인데"} if self.confirmed else {}}
                    for row in selected]
        if "검수자" in prompt:
            return {"decision": "hold", "reason": "합성 테스트의 검토용 결과입니다"}
        return {"title": "회의 기록 재작성의 번거로움", "one_liner": "회의 기록을 다시 옮기는 작업에서 번거로움이 나타난다.",
                "description": "회의 내용을 매번 옮겨 적는 과정이 번거롭다는 경험이다.",
                "context": "회의 기록을 정리하는 상황이다.", "complexity_note": "기록을 옮기는 절차를 확인해야 한다."}


def test_queryless_resume_drains_raw_backlog_without_rejudging_processed(configured, monkeypatch, make_raw_item):
    synthetic_catalog(monkeypatch)
    monkeypatch.setattr(settings, "COLLECTION_JUDGE_PER_CATEGORY", 2)
    monkeypatch.setattr(settings, "COLLECTION_JUDGE_BUDGET", 2)
    rows = [make_raw_item(id=f"synthetic-backlog-{i}", title="합성 일반 안내", snippet="판별 신호 없는 안내문입니다") for i in range(3)]
    monkeypatch.setattr(search_tool, "search_endpoint", lambda *a, **kw: search_tool.SearchReport(rows, True))
    first = collection_tool.create_run(target())
    prepare_worker(first, monkeypatch)
    collection_worker.execute(first.id)
    done = collection_tool.get_run(first.id)
    assert done.has_more and done.can_resume and done.coverage.catalog_remaining == 0
    assert done.counts.selected == 2 and done.exclusion_reasons["awaiting_judgement"] == 1
    before = (collection_tool.run_dir(first.id) / "run.json").read_bytes()
    child = collection_tool.create_run(target(), resume_from=first.id)
    assert child.queries == [] and child.cumulative_counts.collected == 3
    assert collection_tool.create_run(target(), resume_from=first.id).id == child.id
    prepare_worker(child, monkeypatch)
    collection_worker.execute(child.id)
    result = collection_tool.get_run(child.id)
    assert result.status == "completed" and result.counts.queries_done == 0
    assert result.counts.selected == 1 and result.cumulative_counts.collected == 3
    assert result.exclusion_reasons["rule_filtered"] == 3
    assert not result.has_more and result.stop_reason == "catalog_exhausted"
    assert (collection_tool.run_dir(first.id) / "run.json").read_bytes() == before


def test_one_call_budget_saves_first_batch_and_resumes_remaining_without_repeat(configured, monkeypatch, make_raw_item):
    synthetic_catalog(monkeypatch)
    monkeypatch.setattr(settings, "COLLECTION_LLM_CALL_BUDGET", 1)
    monkeypatch.setattr(settings, "JUDGE_BATCH_SIZE", 2)
    rows = [make_raw_item(id=f"synthetic-meter-{i}", title="회의록 정리가 번거롭습니다",
                         snippet="저는 회의록 내용을 매번 옮겨 적는 일이 번거롭습니다. 개선됐으면 좋겠습니다") for i in range(3)]
    llm = SyntheticEvidenceLLM(rows, confirmed=False)
    set_llm(llm)
    monkeypatch.setattr(search_tool, "search_endpoint", lambda *a, **kw: search_tool.SearchReport(rows, True))
    first = collection_tool.create_run(target())
    prepare_worker(first, monkeypatch)
    collection_worker.execute(first.id)
    done = collection_tool.get_run(first.id)
    assert done.stop_reason == "llm_budget" and done.counts.judged == 2 and done.has_more
    child = collection_tool.create_run(target(), resume_from=first.id)
    prepare_worker(child, monkeypatch)
    collection_worker.execute(child.id)
    result = collection_tool.get_run(child.id)
    assert result.status == "completed", result.error
    assert result.counts.judged == 1 and result.cumulative_counts.judged == 3
    assert len(llm.judged_ids) == len(set(llm.judged_ids)) == 3
    assert not result.problems and len(result.review_candidates) == 3
    assert not result.has_more


def test_two_rounds_accumulate_confirmed_evidence_without_cross_target_corpus(configured, monkeypatch, make_raw_item):
    queries = synthetic_catalog(monkeypatch, size=2)
    queries[1] = queries[1].model_copy(update={"category": queries[0].category})
    rows = [make_raw_item(id=f"synthetic-accumulate-{i}", title="회의록 정리가 번거롭습니다", source_name=f"합성 출처{i}",
                         snippet="저는 30대 군인인데 회의록 내용을 매번 옮겨 적는 일이 번거롭습니다. 개선됐으면 좋겠습니다") for i in range(4)]
    set_llm(SyntheticEvidenceLLM(rows))
    monkeypatch.setattr(search_tool, "search_endpoint", lambda keyword, *a, **kw:
                        search_tool.SearchReport(rows[:2] if keyword == queries[0].keyword else rows[2:], True))
    first = collection_tool.create_run(target())
    prepare_worker(first, monkeypatch)
    collection_worker.execute(first.id)
    before = collection_tool.get_run(first.id)
    assert before.counts.pain_items == 2 and before.problems
    with pytest.raises(collection_tool.CollectionRequestError):
        collection_tool.create_run(TargetProfile(age="20대", jobs=["학생"]), resume_from=first.id)
    child = collection_tool.create_run(target(), resume_from=first.id)
    prepare_worker(child, monkeypatch)
    collection_worker.execute(child.id)
    result = collection_tool.get_run(child.id)
    assert result.status == "completed", result.error
    assert result.counts.collected == result.counts.judged == 2
    assert result.cumulative_counts.collected == result.cumulative_counts.pain_items == 4
    assert len(corpus_tool.load_raw_items()) == 4 and len(corpus_tool.load_judgements()) == 4
    assert result.problems and max(p.case_count for p in result.problems) == 4
    assert not settings.PROBLEMS_DIR.exists()


def test_failed_judgement_resume_does_not_reuse_degraded_snapshot(configured, monkeypatch, make_raw_item):
    synthetic_catalog(monkeypatch)
    row = make_raw_item(id="synthetic-recovery", title="회의록 정리가 번거롭습니다",
                        snippet="저는 회의록 내용을 매번 옮겨 적는 일이 번거롭습니다. 개선됐으면 좋겠습니다")
    monkeypatch.setattr(search_tool, "search_endpoint", lambda *a, **kw: search_tool.SearchReport([row], True))
    class FailingLLM:
        def complete_json(self, *a, **kw):
            raise LLMError("synthetic failure")
    set_llm(FailingLLM())
    first = collection_tool.create_run(target())
    prepare_worker(first, monkeypatch)
    collection_worker.execute(first.id)
    failed = collection_tool.get_run(first.id)
    assert failed.status == "failed" and failed.has_more and failed.counts.judge_failed == 1
    parent_judgements = corpus_tool.load_judgements()
    set_llm(SyntheticEvidenceLLM([row], confirmed=False))
    child = collection_tool.create_run(target(), resume_from=first.id)
    prepare_worker(child, monkeypatch)
    collection_worker.execute(child.id)
    result = collection_tool.get_run(child.id)
    assert result.status == "completed" and result.cumulative_counts.judged == 1
    assert result.review_candidates and len(corpus_tool.load_judgements()) == 1
    assert parent_judgements and not parent_judgements[0].is_pain


def test_canonical_qa_result_dedup_preserves_received_count(configured, monkeypatch, make_raw_item):
    synthetic_catalog(monkeypatch)
    rows = [make_raw_item(id=f"synthetic-qa-{i}", url=url, title="합성 일반 안내", snippet="질문 안내문입니다") for i, url in enumerate([
        "https://kin.naver.com/qna/detail.naver?d1id=1&docId=123456", "https://m.kin.naver.com/mobile/qna/detail.naver?docId=123456&answerNo=2"])]
    monkeypatch.setattr(search_tool, "search_endpoint", lambda *a, **kw: search_tool.SearchReport(rows, True))
    run = collection_tool.create_run(target())
    prepare_worker(run, monkeypatch)
    collection_worker.execute(run.id)
    result = collection_tool.get_run(run.id)
    assert result.counts.fetched == 2 and result.counts.collected == 1
    assert result.query_results[0].result_count == 2 and result.query_results[0].new_count == 1


def test_partial_model_response_keeps_success_and_retries_only_missing(configured, monkeypatch, make_raw_item):
    synthetic_catalog(monkeypatch)
    rows = [make_raw_item(id=f"synthetic-partial-{i}", title="회의록 정리가 번거롭습니다",
                         snippet="저는 회의록 내용을 매번 옮겨 적는 일이 번거롭습니다. 개선됐으면 좋겠습니다") for i in range(2)]
    monkeypatch.setattr(search_tool, "search_endpoint", lambda *a, **kw: search_tool.SearchReport(rows, True))
    set_llm(SyntheticEvidenceLLM(rows[:1], confirmed=False))
    first = collection_tool.create_run(target())
    prepare_worker(first, monkeypatch)
    collection_worker.execute(first.id)
    result = collection_tool.get_run(first.id)
    assert result.status == "completed" and result.counts.judged == result.counts.judge_failed == 1
    child = collection_tool.create_run(target(), resume_from=first.id)
    prepare_worker(child, monkeypatch)
    recovered = SyntheticEvidenceLLM(rows, confirmed=False)
    set_llm(recovered)
    collection_worker.execute(child.id)
    result = collection_tool.get_run(child.id)
    assert result.counts.judged == 1 and result.cumulative_counts.judged == 2
    assert recovered.judged_ids == [rows[1].id]
    assert len(corpus_tool.load_judgements()) == 2


def test_generation_failure_can_resume_after_catalog_and_judging_are_complete(configured, monkeypatch, make_raw_item):
    synthetic_catalog(monkeypatch)
    row = make_raw_item(id="synthetic-generate-retry", title="회의록 정리가 번거롭습니다",
                        snippet="저는 30대 군인인데 회의록 내용을 매번 옮겨 적는 일이 번거롭습니다. 개선됐으면 좋겠습니다")
    monkeypatch.setattr(search_tool, "search_endpoint", lambda *a, **kw: search_tool.SearchReport([row], True))
    class GenerationFailure(SyntheticEvidenceLLM):
        def complete_json(self, prompt, **kw):
            if '"is_pain"' not in prompt:
                raise LLMError("synthetic generation unavailable")
            return super().complete_json(prompt, **kw)
    set_llm(GenerationFailure([row]))
    first = collection_tool.create_run(target())
    prepare_worker(first, monkeypatch)
    collection_worker.execute(first.id)
    failed = collection_tool.get_run(first.id)
    assert failed.status == "failed" and failed.has_more and failed.coverage.catalog_remaining == 0
    assert failed.exclusion_reasons["awaiting_judgement"] == 0
    assert failed.counts.generation_failed == 1
    child = collection_tool.create_run(target(), resume_from=first.id)
    assert child.queries == []
    prepare_worker(child, monkeypatch)
    recovered = SyntheticEvidenceLLM([row])
    set_llm(recovered)
    collection_worker.execute(child.id)
    result = collection_tool.get_run(child.id)
    assert result.status == "completed" and result.problems and not result.has_more
    assert not recovered.judged_ids and result.counts.llm_calls == 2
    assert result.counts.generation_failed == 0
    assert result.cumulative_counts.generation_failed == 1


def test_collection_budget_validation_and_llm_environment_inheritance(configured, monkeypatch):
    from app.config.settings import Settings
    with pytest.raises(ValidationError):
        Settings(COLLECTION_QUERY_BUDGET=0)
    with pytest.raises(ValidationError):
        Settings(COLLECTION_ITEMS_PER_QUERY=101)
    monkeypatch.setattr(settings, "LLM_TIMEOUT_SEC", 75)
    monkeypatch.setattr(settings, "JUDGE_BATCH_SIZE", 7)
    monkeypatch.setattr(settings, "LLM_MAX_RETRIES", 1)
    run = collection_tool.create_run(target())
    env = collection_tool._worker_environment(run.id)
    assert env["LLM_TIMEOUT_SEC"] == "75" and env["JUDGE_BATCH_SIZE"] == "7"
    assert run.limits.llm_http_attempts == run.limits.llm_logical_calls * 4


def test_default_volume_finishes_all_received_items_in_one_job_with_live_progress(configured, monkeypatch, make_raw_item):
    """2,400 synthetic texts, real interpreter/storage, fake search/LLM and virtual time only."""
    from types import SimpleNamespace
    run = collection_tool.create_run(target())
    assert len(run.queries) == 120
    assert run.limits.items_per_query == 20 and run.limits.collected_items == 2400
    assert run.limits.judged_items == 2400 and run.limits.items_per_category == 1000
    assert run.limits.problem_candidates == 20 and run.limits.llm_logical_calls == 200
    assert run.limits.timeout_seconds == 3600
    prepare_worker(run, monkeypatch)
    rows_by_query = {}
    all_rows = []
    for index, query in enumerate(run.queries):
        rows = [make_raw_item(id=f"synthetic-volume-{index:03d}-{offset:02d}", title="문서를 옮기는 일이 번거롭습니다",
                             snippet="저는 문서를 매번 옮겨 적는 일이 번거롭습니다. 개선됐으면 좋겠습니다",
                             query_keyword=query.keyword, source_kind=query.source_kind) for offset in range(20)]
        rows_by_query[query.keyword] = rows
        all_rows.extend(rows)
    monkeypatch.setattr(search_tool, "search_endpoint", lambda keyword, *a, **kw:
                        search_tool.SearchReport(rows_by_query[keyword], True))
    clock = {"seconds": 0}
    monkeypatch.setattr(collection_worker, "time", SimpleNamespace(monotonic=lambda: clock["seconds"]))
    class SlowSyntheticLLM(SyntheticEvidenceLLM):
        def complete_json(self, prompt, **kw):
            clock["seconds"] += 5  # No sleep or external call: simulate a job lasting over eight minutes.
            return super().complete_json(prompt, **kw)
    llm = SlowSyntheticLLM(all_rows, confirmed=False)
    set_llm(llm)
    actual_update = collection_tool.update_run
    checkpoints = []
    def update(run_id, **changes):
        if changes.get("stage") == "interpreting" and changes.get("status") == "running":
            checkpoints.append((clock["seconds"], changes["cumulative_counts"]["judged"],
                                len(changes["review_candidates"])))
        return actual_update(run_id, **changes)
    monkeypatch.setattr(collection_tool, "update_run", update)
    collection_worker.execute(run.id)
    result = collection_tool.get_run(run.id)
    assert result.status == "completed", result.error
    assert result.counts.collected == result.counts.selected == result.counts.judged == 2400
    assert result.counts.llm_calls == 120 and len(set(llm.judged_ids)) == 2400
    assert result.exclusion_reasons["awaiting_judgement"] == 0 and result.counts.unselected == 0
    assert any(seconds >= 480 and 0 < judged < 2400 and candidates for seconds, judged, candidates in checkpoints)
    assert len(result.review_candidates) == 2400 and not result.problems
