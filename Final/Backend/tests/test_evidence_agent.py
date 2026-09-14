"""
②′ 근거 조립기(EvidenceAgent) 테스트.

★ llm_tool 을 절대 안 부른다 — 부르면 conftest 의 네트워크 차단이 잡는다
  (LLM_DRY_RUN 이더라도 이 에이전트는애초에 llm_tool 을 import하지 않는다).

여기서 고정하는 것
  · 근거 선별은 출처 라운드로빈이다 — 한 출처가 5건을 독식하지 못한다
  · 같은 출처 안에서는 severity 높음 → pain_summary 있음 → id 순
  · is_pain=True 인 판정이 있는 원문만 근거 후보다
  · gate.passed=False 면 reason 이 채워진다
  · 원문을 못 찾은 id 는 예외 없이 그 candidate 에서 빠진다
  · 빈 candidates 는 빈 결과 + 매니페스트를 안 남긴다
  · 매니페스트에 "근거조립" 카테고리별 통계가 남는다
"""

from __future__ import annotations

from datetime import datetime

import pytest

from app.agents.evidence_agent import EvidenceAgent, EvidenceInput
from app.config.settings import settings
from app.schemas.models import Category, ProblemCandidate, ProgressEvent
from app.tools import corpus_tool

CATEGORY = Category.IT_PRODUCTIVITY
NOW = datetime.now()


# ══════════════════════════════════════════════
# 도우미
# ══════════════════════════════════════════════


def seed_item(id: str, source_name: str, *, make_raw_item, category=CATEGORY, **kw):
    item = make_raw_item(id=id, source_name=source_name, collected_at=NOW, **kw)
    corpus_tool.save_raw_items([item], category=category)
    return item


def seed_judgement(raw_item_id: str, *, make_judgement, category=CATEGORY, **kw):
    j = make_judgement(raw_item_id=raw_item_id, **kw)
    corpus_tool.save_judgements([j], category)
    return j


def candidate(cid: str, raw_item_ids: list[str], category=CATEGORY) -> ProblemCandidate:
    return ProblemCandidate(
        id=cid,
        raw_item_ids=raw_item_ids,
        pain_summaries=["번거롭다"] * len(raw_item_ids),
        theme_hint="테스트 묶음",
        category=category,
    )


def run(candidates: list[ProblemCandidate], **kw):
    return EvidenceAgent(**kw.pop("agent_kw", {})).run(
        EvidenceInput(candidates=candidates, **kw)
    )


# ══════════════════════════════════════════════
# 계약 — 이름 · 단계 · llm_tool 미참조
# ══════════════════════════════════════════════


def test_에이전트_이름과_단계():
    assert EvidenceAgent.name == "근거 조립기"
    assert EvidenceAgent.steps == ["근거 모으기", "신호 세기", "게시 기준 확인"]


def test_llm_tool_을_import하지_않는다():
    import app.agents.evidence_agent as mod

    assert "llm_tool" not in vars(mod)


def test_진행_상태를_0_0완료_1_1완료_2_2완료_순으로_알린다(make_raw_item, make_judgement):
    seed_item("r1", "지식iN", make_raw_item=make_raw_item)
    seed_judgement("r1", make_judgement=make_judgement, severity="높음")

    events: list[ProgressEvent] = []
    EvidenceAgent(on_progress=events.append).run(
        EvidenceInput(candidates=[candidate("c1", ["r1"])])
    )

    assert [(e.index, e.done) for e in events] == [
        (0, False), (0, True),
        (1, False), (1, True),
        (2, False), (2, True),
    ]
    assert [e.step for e in events[::2]] == EvidenceAgent.steps


# ══════════════════════════════════════════════
# 빈 입력
# ══════════════════════════════════════════════


def test_빈_candidates_는_빈_결과를_낸다():
    assert run([]) == []


def test_빈_candidates_는_매니페스트를_안_남긴다(corpus_dir):
    run([])
    assert corpus_tool.read_manifest() is None


def test_진행_콜백이_없어도_돈다():
    assert run([]) == []


def test_source_metadata_comes_from_raw_item(make_raw_item, make_judgement):
    item = seed_item("link1", "실제 출처", make_raw_item=make_raw_item,
                     url="https://example.test/post/one")
    seed_judgement(item.id, make_judgement=make_judgement)
    evidence = run([candidate("link-candidate", [item.id])])[0].evidence[0]
    assert evidence.source_url == item.url
    assert evidence.source_name == item.source_name
    assert evidence.source_kind == item.source_kind
    assert evidence.posted_at == item.posted_at


@pytest.mark.parametrize("url", ["javascript:alert(1)", "https://", "https://[invalid", "https://secret@example.test/"])
def test_source_url_rejects_unsafe_or_malformed_values(url):
    from app.agents.evidence_agent import _public_source_url
    assert _public_source_url(url) is None


# ══════════════════════════════════════════════
# 원문을 못 찾은 id — 예외 없이 그 candidate 에서 뺀다
# ══════════════════════════════════════════════


def test_원문을_못_찾은_id는_예외_없이_처리된다(make_raw_item, make_judgement):
    seed_item("r1", "지식iN", make_raw_item=make_raw_item)
    seed_judgement("r1", make_judgement=make_judgement, severity="높음")

    (bundle,) = run([candidate("c1", ["r1", "없는-id-1", "없는-id-2"])])

    assert bundle.gate.case_count_ok is False or bundle.gate.reason  # 3건 중 1건만 찾음
    assert len(bundle.evidence) <= 1


def test_원문을_하나도_못_찾으면_case_count_0으로_처리된다():
    (bundle,) = run([candidate("c1", ["유령-1", "유령-2"])])

    assert bundle.evidence == []
    assert bundle.gate.passed is False
    assert bundle.gate.case_count_ok is False


# ══════════════════════════════════════════════
# 게시 기준 — passed / reason
# ══════════════════════════════════════════════


def _many_sourced_items(n: int, make_raw_item, make_judgement) -> list[str]:
    """서로 다른 출처를 가진 n건의 강한 불편 판정 원문을 만든다."""
    sources = ["지식iN", "네이버 카페", "네이버 블로그", "티스토리", "브런치"]
    ids = []
    for i in range(n):
        rid = f"r{i:03d}"
        seed_item(rid, sources[i % len(sources)], make_raw_item=make_raw_item)
        seed_judgement(rid, make_judgement=make_judgement, severity="높음")
        ids.append(rid)
    return ids


def test_기준_미달이면_reason이_채워진다(make_raw_item, make_judgement):
    ids = _many_sourced_items(2, make_raw_item, make_judgement)  # 사례도 출처도 기준 미달

    (bundle,) = run([candidate("c1", ids)])

    assert bundle.gate.passed is False
    assert bundle.gate.reason
    assert "관련 사례 부족" in bundle.gate.reason


def test_기준을_다_채우면_통과한다(monkeypatch, make_raw_item, make_judgement):
    monkeypatch.setattr(settings, "PUBLISH_MIN_CASES", 5)
    monkeypatch.setattr(settings, "PUBLISH_MIN_SOURCES", 3)
    monkeypatch.setattr(settings, "PUBLISH_MIN_EVIDENCE", 3)

    ids = _many_sourced_items(5, make_raw_item, make_judgement)

    (bundle,) = run([candidate("c1", ids)])

    assert bundle.gate.passed is True
    assert bundle.gate.reason == ""


# ══════════════════════════════════════════════
# 근거 선별 — 라운드로빈
# ══════════════════════════════════════════════


def test_한_출처가_근거를_독식하지_못한다(monkeypatch, make_raw_item, make_judgement):
    monkeypatch.setattr(settings, "EVIDENCE_SHOW_MAX", 5)

    ids = []
    # 지식iN 은 강한 불편 판정이 10건 있다 — 독식 시도
    for i in range(10):
        rid = f"heavy-{i:03d}"
        seed_item(rid, "지식iN", make_raw_item=make_raw_item)
        seed_judgement(rid, make_judgement=make_judgement, severity="높음")
        ids.append(rid)
    # 다른 출처 둘은 1건씩만 있다
    for name, rid in [("네이버 카페", "light-a"), ("네이버 블로그", "light-b")]:
        seed_item(rid, name, make_raw_item=make_raw_item)
        seed_judgement(rid, make_judgement=make_judgement, severity="높음")
        ids.append(rid)

    (bundle,) = run([candidate("c1", ids)])

    sources = [
        item.source_name
        for item in (corpus_tool.load_raw_items_by_ids([e.raw_item_id for e in bundle.evidence])).values()
    ]
    assert sources.count("지식iN") < len(bundle.evidence)  # 독식하지 않는다
    assert "네이버 카페" in sources
    assert "네이버 블로그" in sources


def test_근거는_EVIDENCE_SHOW_MAX_를_넘지_않는다(monkeypatch, make_raw_item, make_judgement):
    monkeypatch.setattr(settings, "EVIDENCE_SHOW_MAX", 3)
    ids = _many_sourced_items(20, make_raw_item, make_judgement)

    (bundle,) = run([candidate("c1", ids)])

    assert len(bundle.evidence) == 3


def test_is_pain_False_인_원문은_근거_후보가_아니다(make_raw_item, make_judgement):
    seed_item("r1", "지식iN", make_raw_item=make_raw_item)
    seed_judgement("r1", make_judgement=make_judgement, is_pain=False, pain_summary=None)

    (bundle,) = run([candidate("c1", ["r1"])])

    assert bundle.evidence == []


def test_판정을_못_찾은_원문은_근거_후보가_아니다(make_raw_item):
    seed_item("r1", "지식iN", make_raw_item=make_raw_item)
    # 판정을 저장하지 않는다

    (bundle,) = run([candidate("c1", ["r1"])])

    assert bundle.evidence == []
    # case_count 는 여전히 1이다 — 원문은 찾았다
    assert bundle.gate.case_count_ok == (1 >= settings.PUBLISH_MIN_CASES)


def test_같은_출처_안에서는_severity_높음이_먼저다(monkeypatch, make_raw_item, make_judgement):
    monkeypatch.setattr(settings, "EVIDENCE_SHOW_MAX", 1)
    seed_item("low", "지식iN", make_raw_item=make_raw_item)
    seed_judgement("low", make_judgement=make_judgement, severity="낮음")
    seed_item("high", "지식iN", make_raw_item=make_raw_item)
    seed_judgement("high", make_judgement=make_judgement, severity="높음")

    (bundle,) = run([candidate("c1", ["low", "high"])])

    assert [e.raw_item_id for e in bundle.evidence] == ["high"]


def test_evidence_summary_는_judgement_의_pain_summary_다(make_raw_item, make_judgement):
    seed_item("r1", "지식iN", make_raw_item=make_raw_item)
    seed_judgement("r1", make_judgement=make_judgement, pain_summary="가계부 정리가 번거롭다")

    (bundle,) = run([candidate("c1", ["r1"])])

    assert bundle.evidence[0].summary == "가계부 정리가 번거롭다"
    assert bundle.evidence[0].raw_item_id == "r1"


def test_선별된_evidence_는_judgement_의_필터_라벨을_보존한다(
    make_raw_item, make_judgement
):
    seed_item("r1", "지식iN", make_raw_item=make_raw_item)
    seed_judgement(
        "r1",
        make_judgement=make_judgement,
        severity="높음",
        has_payment_signal=True,
        has_need_signal=True,
    )

    (bundle,) = run([candidate("c1", ["r1"])])

    evidence = bundle.evidence[0]
    assert evidence.severity == "높음"
    assert evidence.has_payment_signal is True
    assert evidence.has_need_signal is True


# ══════════════════════════════════════════════
# 신호 (ProblemSignals) — aggregate_tool 위임 확인
# ══════════════════════════════════════════════


def test_signals가_실제_출처_수를_반영한다(make_raw_item, make_judgement):
    ids = _many_sourced_items(3, make_raw_item, make_judgement)

    (bundle,) = run([candidate("c1", ids)])

    assert len(bundle.signals.source_name_counts) == 3
    assert sum(bundle.signals.source_name_counts.values()) == 3


def test_bundle이_candidate_id와_category를_보존한다(make_raw_item, make_judgement):
    seed_item("r1", "지식iN", make_raw_item=make_raw_item)
    seed_judgement("r1", make_judgement=make_judgement)

    (bundle,) = run([candidate("c1", ["r1"], category=Category.FINANCE)])

    assert bundle.candidate_id == "c1"
    assert bundle.category is Category.FINANCE


# ══════════════════════════════════════════════
# 여러 후보 — 전체 스캔은 한 번만
# ══════════════════════════════════════════════


def test_여러_후보를_한번에_처리한다(make_raw_item, make_judgement):
    seed_item("r1", "지식iN", make_raw_item=make_raw_item)
    seed_judgement("r1", make_judgement=make_judgement)
    seed_item("r2", "네이버 카페", make_raw_item=make_raw_item)
    seed_judgement("r2", make_judgement=make_judgement)

    bundles = run([candidate("c1", ["r1"]), candidate("c2", ["r2"])])

    assert {b.candidate_id for b in bundles} == {"c1", "c2"}


def test_load_by_ids는_후보마다가_아니라_합쳐서_한번_불린다(monkeypatch, make_raw_item, make_judgement):
    seed_item("r1", "지식iN", make_raw_item=make_raw_item)
    seed_judgement("r1", make_judgement=make_judgement)
    seed_item("r2", "네이버 카페", make_raw_item=make_raw_item)
    seed_judgement("r2", make_judgement=make_judgement)

    calls = {"raw": 0, "judgement": 0}
    orig_raw = corpus_tool.load_raw_items_by_ids
    orig_j = corpus_tool.load_judgements_by_ids

    def counted_raw(*a, **kw):
        calls["raw"] += 1
        return orig_raw(*a, **kw)

    def counted_j(*a, **kw):
        calls["judgement"] += 1
        return orig_j(*a, **kw)

    monkeypatch.setattr(corpus_tool, "load_raw_items_by_ids", counted_raw)
    monkeypatch.setattr(corpus_tool, "load_judgements_by_ids", counted_j)

    import app.agents.evidence_agent as mod

    monkeypatch.setattr(mod.corpus_tool, "load_raw_items_by_ids", counted_raw)
    monkeypatch.setattr(mod.corpus_tool, "load_judgements_by_ids", counted_j)

    run([candidate("c1", ["r1"]), candidate("c2", ["r2"])])

    assert calls["raw"] == 1
    assert calls["judgement"] == 1


# ══════════════════════════════════════════════
# 매니페스트 — 카테고리별 게시 가능/미달
# ══════════════════════════════════════════════


def test_매니페스트에_카테고리별_통계가_남는다(make_raw_item, make_judgement):
    ids = _many_sourced_items(2, make_raw_item, make_judgement)  # 미달

    run([candidate("c1", ids, category=Category.FINANCE)])

    manifest = corpus_tool.read_manifest()
    stats = manifest["근거조립"][Category.FINANCE.value]

    assert stats["후보_입력"] == 1
    assert stats["게시가능"] == 0
    assert stats["게시미달"] == 1
    assert stats["미달사유"]  # 사유가 채워져 있다


def test_매니페스트는_다른_카테고리를_지우지_않는다(make_raw_item, make_judgement):
    seed_item("r1", "지식iN", make_raw_item=make_raw_item, category=Category.FINANCE)
    seed_judgement("r1", make_judgement=make_judgement, category=Category.FINANCE)

    run([candidate("c1", ["r1"], category=Category.FINANCE)])
    run([candidate("c2", [], category=Category.HEALTHCARE)])

    근거조립 = corpus_tool.read_manifest()["근거조립"]
    assert Category.FINANCE.value in 근거조립
    assert Category.HEALTHCARE.value in 근거조립
