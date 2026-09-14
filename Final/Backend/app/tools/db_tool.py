"""게시 저장소. 집계·근거는 원문과 재대조하고 승인된 문제만 JSON으로 저장한다.

문제별 단일 파일에 Problem과 원문 스냅샷을 함께 저장한다. 기존 파일은
자동 덮어쓰지 않으며, 손상된 저장소를 빈 목록인 것처럼 숨기지 않는다.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.config.settings import settings
from app.schemas.models import (
    Category, EvidenceBundle, Problem, ProblemCandidate, ProblemDraft, RawItem, ReviewResult,
)
from app.tools import aggregate_tool, corpus_tool, text_tool


class ProblemStoreError(ValueError):
    """손상 또는 불일치로 안전하게 읽거나 게시할 수 없다."""


def _root() -> Path:
    return Path(settings.PROBLEMS_DIR)


def _path(problem_id: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,199}", problem_id):
        raise ProblemStoreError("잘못된 문제 ID입니다")
    return _root() / f"{problem_id}.json"


def save_raw_items(items: list[RawItem]) -> None:
    """원문의 유일한 정본 저장 방식인 코퍼스에 위임한다."""
    corpus_tool.save_raw_items(items)


def _read(problem_id: str) -> Optional[dict]:
    path = _path(problem_id)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != 1:
            raise ValueError("지원하지 않는 저장 형식")
        if payload.get("human_reviewed") is not True:
            raise ValueError("사람 검수 승인 기록이 없습니다")
        problem = Problem.model_validate(payload["problem"])
        items = [RawItem.model_validate(i) for i in payload["raw_items"]]
        if problem.id != problem_id or not problem.gate.passed:
            raise ValueError("게시 ID 또는 게시 기준 불일치")
        ids = {i.id for i in items}
        if len(ids) != problem.case_count or any(e.raw_item_id not in ids for e in problem.evidence):
            raise ValueError("근거 스냅샷 불일치")
        return {"problem": problem, "raw_items": items}
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        raise ProblemStoreError(f"문제 저장 파일이 손상되었습니다: {path.name}") from exc


def get_problem(problem_id: str) -> Optional[Problem]:
    record = _read(problem_id)
    return record["problem"] if record else None


def get_problem_raw_items(problem_id: str) -> list[RawItem]:
    record = _read(problem_id)
    return record["raw_items"] if record else []


def list_problems() -> list[Problem]:
    """게시 문제만 최신순으로 조회한다. GET은 디렉터리도 만들지 않는다."""
    if not _root().exists():
        return []
    problems = [get_problem(path.stem) for path in sorted(_root().glob("*.json"))]
    return sorted((p for p in problems if p is not None),
                  key=lambda p: (p.updated_at.isoformat(), p.id), reverse=True)


def find_similar_problems(title: str) -> list[Problem]:
    """확실한 중복만 반환한다. 의미 유사성 추정으로 자동 병합하지 않는다."""
    key = re.sub(r"\s+", "", title).casefold()
    return [p for p in list_problems() if re.sub(r"\s+", "", p.title).casefold() == key]


def _assemble(draft: ProblemDraft, problem_id: str, category: Category,
              bundle: EvidenceBundle, candidate: ProblemCandidate) -> tuple[Problem, list[RawItem]]:
    _path(problem_id)
    if bundle.candidate_id != candidate.id or bundle.category != category or candidate.category != category:
        raise ProblemStoreError("후보와 근거 묶음이 일치하지 않습니다")
    ids = list(dict.fromkeys(candidate.raw_item_ids))
    raw_map = corpus_tool.load_raw_items_by_ids(ids, weeks=settings.EVIDENCE_LOOKBACK_WEEKS)
    judgement_map = corpus_tool.load_judgements_by_ids(ids, weeks=settings.EVIDENCE_LOOKBACK_WEEKS)
    items = [raw_map[rid] for rid in ids if rid in raw_map]
    judgements = [judgement_map[rid] for rid in ids if rid in judgement_map]
    signals = aggregate_tool.signals_for(items, judgements)
    if signals != bundle.signals:
        raise ProblemStoreError("근거 조립 이후 집계가 변경되었습니다. 근거를 다시 조립하세요")
    if draft.evidence != bundle.evidence:
        raise ProblemStoreError("초안이 근거 묶음을 변경했습니다")
    seen: set[str] = set()
    for evidence in bundle.evidence:
        j = judgement_map.get(evidence.raw_item_id)
        if (evidence.raw_item_id in seen or evidence.raw_item_id not in raw_map
                or not j or not j.is_pain or not j.pain_summary
                or evidence.summary != j.pain_summary
                or evidence.severity != j.severity
                or evidence.has_need_signal != j.has_need_signal
                or evidence.has_payment_signal != j.has_payment_signal):
            raise ProblemStoreError("근거가 저장된 원문·판정과 일치하지 않습니다")
        item = raw_map[evidence.raw_item_id]
        if (evidence.excerpt != text_tool.pick_excerpt(item)
                or evidence.source_name != item.source_name
                or evidence.source_url != str(item.url)
                or evidence.source_kind != item.source_kind
                or evidence.posted_at != item.posted_at):
            raise ProblemStoreError("근거 출처 또는 발췌가 원문과 일치하지 않습니다")
        seen.add(evidence.raw_item_id)
    gate = aggregate_tool.publish_gate(signals, len(items), len(bundle.evidence))
    if gate != bundle.gate:
        raise ProblemStoreError("게시 기준이 변경되었습니다. 근거를 다시 조립하세요")
    problem = Problem(
        **draft.model_dump(), id=problem_id, category=category,
        case_count=len(items), source_count=len(signals.source_name_counts),
        signals=signals, gate=gate, updated_at=datetime.now(timezone.utc),
    )
    return problem, items


def compose_problem(draft: ProblemDraft, problem_id: str, category: Category, *,
                    bundle: EvidenceBundle, candidate: ProblemCandidate) -> Problem:
    """운영자 검토용 조립. 미달 gate를 보존하며 어떤 파일도 쓰지 않는다."""
    return _assemble(draft, problem_id, category, bundle, candidate)[0]


def publish_problem(draft: ProblemDraft, problem_id: str, category: Category, *,
                    bundle: EvidenceBundle, candidate: ProblemCandidate,
                    review: ReviewResult, persist: bool = True,
                    human_reviewed: bool = False) -> Problem:
    """근거 기준과 텍스트 검수를 모두 통과한 결과만 원자적으로 신규 게시한다."""
    if review.decision != "publish" or not bundle.gate.passed:
        raise ProblemStoreError("검수·게시 기준을 통과하지 못한 문제는 게시할 수 없습니다")
    if persist and not human_reviewed:
        raise ProblemStoreError("게시 전 사람 검수와 공개 승인이 필요합니다")
    if persist and (settings.LLM_DRY_RUN or settings.LLM_PROVIDER == "echo"):
        raise ProblemStoreError("모의 실행 결과는 게시 저장소에 저장할 수 없습니다")
    problem, items = _assemble(draft, problem_id, category, bundle, candidate)
    if not persist:
        return problem
    path = _path(problem_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": 1, "human_reviewed": True,
               "review": review.model_dump(mode="json"),
               "problem": problem.model_dump(mode="json"),
               "raw_items": [i.model_dump(mode="json") for i in items]}
    # 같은 파일시스템 안에서 hard link 생성은 원자적이고 기존 경로를 덮어쓰지 않는다.
    fd, temp_name = tempfile.mkstemp(prefix=".problem-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temp_name, path)
        except FileExistsError as exc:
            raise ProblemStoreError("이미 게시된 문제 ID입니다. 기존 내용을 보존했습니다") from exc
    finally:
        Path(temp_name).unlink(missing_ok=True)
    return problem
