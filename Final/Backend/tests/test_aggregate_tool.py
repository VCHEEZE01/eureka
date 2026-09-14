"""
aggregate_tool 테스트 — 근거 상세 페이지 숫자의 정본.

여기서 고정하는 것 (계획 문서 "Step 3" 계약 3개 + 세부 규칙)
  1. items 와 judgements 는 raw_item_id 교집합만 본다
     → RawItem 을 못 찾은 Judgement 는 라벨 집계에서 빠진다
  2. observed_until=None 이면 어떤 주차도 partial=True 가 아니다
  3. 빈 입력이면 전 필드 0/빈 dict, 예외 없음
  + undated_count > 0 케이스
  + severity_labeled_count < case_count 케이스
  + payment_signal_count / signal_type_counts 재계산 정확성
  + mentioned_services 정렬 (count 내림차순 → 이름 사전순)
"""

from __future__ import annotations

from datetime import date, datetime

import pytest

from app.config.settings import settings
from app.schemas.models import Judgement, RawItem, SourceKind
from app.tools import aggregate_tool as at
from app.tools.corpus_tool import week_key as ct_week_key


# ══════════════════════════════════════════════
# 주차 키 — corpus_tool.week_key() 와 형식이 같아야 한다
# ══════════════════════════════════════════════


@pytest.mark.parametrize(
    "d",
    [date(2026, 9, 9), date(2027, 1, 1), date(2026, 1, 8), date(2026, 12, 31)],
)
def test_week_key_matches_corpus_tool(d):
    assert at._week_key(d) == ct_week_key(d)


# ══════════════════════════════════════════════
# 빈 입력
# ══════════════════════════════════════════════


def test_empty_input_returns_zeroed_signals_without_raising():
    signals = at.signals_for([], [])

    assert signals.source_kind_counts == {}
    assert signals.source_name_counts == {}
    assert signals.first_posted_at is None
    assert signals.last_posted_at is None
    assert signals.observed_weeks == 0
    assert signals.weekly_counts == []
    assert signals.undated_count == 0
    assert signals.severity_counts == {}
    assert signals.severity_labeled_count == 0
    assert signals.need_signal_count == 0
    assert signals.signal_type_counts == {}
    assert signals.payment_signal_count == 0
    assert signals.role_counts == {}
    assert signals.role_labeled_count == 0
    assert signals.age_counts == {}
    assert signals.age_labeled_count == 0
    assert signals.gender_counts == {}
    assert signals.gender_labeled_count == 0
    assert signals.mentioned_services == []


def test_empty_input_publish_gate_fails_cleanly():
    signals = at.signals_for([], [])
    gate = at.publish_gate(signals, case_count=0, evidence_count=0)

    assert gate.passed is False
    assert gate.case_count_ok is False
    assert gate.source_count_ok is False
    assert gate.evidence_count_ok is False
    assert gate.reason


# ══════════════════════════════════════════════
# 계약 1 — raw_item_id 교집합만 본다
# ══════════════════════════════════════════════


def _item(id: str, **kw) -> RawItem:
    defaults = dict(
        title="가계부 정리가 번거롭다",
        snippet="매번 카드 명세서를 손으로 옮겨 적는 게 번거롭습니다",
        url=f"https://example.test/{id}",
        source_name="네이버 카페",
        source_kind=SourceKind.COMMUNITY,
        collected_at=datetime(2026, 9, 9, 3, 0, 0),
        query_keyword="가계부 번거롭",
        content_hash=f"hash-{id}",
    )
    defaults.update(kw)
    return RawItem(id=id, **defaults)


def _judgement(raw_item_id: str, **kw) -> Judgement:
    defaults = dict(is_pain=True, confidence="높음")
    defaults.update(kw)
    return Judgement(raw_item_id=raw_item_id, **defaults)


def test_judgement_without_matching_raw_item_is_excluded_from_label_counts():
    items = [_item("a")]
    judgements = [
        _judgement("a", severity="높음", sufferer_role="직장인"),
        # "b" 는 items 에 없다 — 근거를 확인할 수 없는 라벨이라 세지 않는다
        _judgement("b", severity="높음", sufferer_role="학생"),
    ]

    signals = at.signals_for(items, judgements)

    assert signals.severity_counts == {"높음": 1}
    assert signals.severity_labeled_count == 1
    assert signals.role_counts == {"직장인": 1}
    assert signals.role_labeled_count == 1


def test_extra_judgement_ids_do_not_inflate_service_mentions():
    items = [_item("a")]
    judgements = [
        _judgement("a", mentioned_service="토스"),
        _judgement("b", mentioned_service="뱅크샐러드"),  # 원문 없음 → 제외
    ]

    signals = at.signals_for(items, judgements)

    assert [s.name for s in signals.mentioned_services] == ["토스"]


def test_rule_recomputed_fields_use_all_items_regardless_of_judgement():
    """signal_type_counts·payment_signal_count 는 판정 유무와 무관하게 items 전부를 본다."""
    items = [
        _item("a", title="가계부 정리 번거롭다", snippet="돈 아깝고 번거롭다"),
        _item("b", title="가계부 정리 번거롭다", snippet="돈 아깝고 번거롭다"),
    ]
    # 판정은 하나도 안 줬다 — 그래도 재계산된다
    signals = at.signals_for(items, [])

    assert signals.payment_signal_count == 2
    assert signals.signal_type_counts.get("직접 불만") == 2


# ══════════════════════════════════════════════
# 계약 2 — observed_until=None 이면 partial 이 없다
# ══════════════════════════════════════════════


def test_observed_until_none_never_marks_partial():
    items = [_item("a", posted_at=date(2026, 9, 9))]
    signals = at.signals_for(items, [], observed_until=None)

    assert all(not w.partial for w in signals.weekly_counts)


def test_observed_until_marks_last_week_partial_when_not_sunday():
    items = [_item("a", posted_at=date(2026, 9, 9))]  # 2026-W37
    # 2026-09-09 은 수요일이다 — 그 주의 관측이 아직 안 끝났다
    signals = at.signals_for(items, [], observed_until=date(2026, 9, 9))

    assert len(signals.weekly_counts) == 1
    assert signals.weekly_counts[0].partial is True


def test_observed_until_on_sunday_is_not_partial():
    items = [_item("a", posted_at=date(2026, 9, 6))]  # 2026-W36, 일요일
    signals = at.signals_for(items, [], observed_until=date(2026, 9, 6))

    assert signals.weekly_counts[0].partial is False


def test_observed_until_does_not_mark_earlier_weeks_partial():
    items = [
        _item("a", posted_at=date(2026, 8, 31)),  # 2026-W36 (월)
        _item("b", posted_at=date(2026, 9, 9)),  # 2026-W37 (수) — 관측 시점과 같은 주
    ]
    signals = at.signals_for(items, [], observed_until=date(2026, 9, 9))

    by_week = {w.week: w.partial for w in signals.weekly_counts}
    assert by_week["2026-W36"] is False
    assert by_week["2026-W37"] is True


# ══════════════════════════════════════════════
# 계약 3 — 빈 입력은 위에서 이미 확인했다. 여기는 세부 규칙.
# ══════════════════════════════════════════════


def test_undated_count_counts_items_without_posted_at():
    items = [
        _item("a", posted_at=date(2026, 9, 9)),
        _item("b", posted_at=None),
        _item("c", posted_at=None),
    ]
    signals = at.signals_for(items, [])

    assert signals.undated_count == 2
    assert signals.observed_weeks == 1


def test_severity_labeled_count_can_be_smaller_than_case_count():
    """severity 가 없는 판정도 case_count 에는 들어가지만 분모에서는 빠진다."""
    items = [_item("a"), _item("b"), _item("c")]
    judgements = [
        _judgement("a", severity="높음"),
        _judgement("b", severity=None),  # 판정 못 함
        _judgement("c", severity=None),
    ]
    signals = at.signals_for(items, judgements)
    case_count = len(items)

    assert signals.severity_labeled_count == 1
    assert signals.severity_labeled_count < case_count


def test_severity_only_counted_when_is_pain_true():
    items = [_item("a")]
    judgements = [_judgement("a", is_pain=False, severity="높음")]

    signals = at.signals_for(items, judgements)

    assert signals.severity_counts == {}
    assert signals.severity_labeled_count == 0


def test_need_signal_count_does_not_require_severity():
    items = [_item("a")]
    judgements = [_judgement("a", severity=None, has_need_signal=True)]

    signals = at.signals_for(items, judgements)

    assert signals.need_signal_count == 1


def test_mentioned_services_sorted_by_count_desc_then_name_asc():
    items = [_item(f"i{i}") for i in range(5)]
    judgements = [
        _judgement("i0", mentioned_service="가계부앱"),
        _judgement("i1", mentioned_service="나은행"),
        _judgement("i2", mentioned_service="나은행"),
        _judgement("i3", mentioned_service="다뱅크"),
        _judgement("i4", mentioned_service="다뱅크"),
    ]
    signals = at.signals_for(items, judgements)

    assert [(s.name, s.count) for s in signals.mentioned_services] == [
        ("나은행", 2),
        ("다뱅크", 2),
        ("가계부앱", 1),
    ]


def test_source_breakdown_counts_kind_and_name():
    items = [
        _item("a", source_kind=SourceKind.COMMUNITY, source_name="지식iN"),
        _item("b", source_kind=SourceKind.COMMUNITY, source_name="지식iN"),
        _item("c", source_kind=SourceKind.BLOG, source_name="네이버 블로그"),
    ]
    signals = at.signals_for(items, [])

    assert signals.source_kind_counts == {"커뮤니티": 2, "블로그": 1}
    assert signals.source_name_counts == {"지식iN": 2, "네이버 블로그": 1}


def test_first_and_last_posted_at():
    items = [
        _item("a", posted_at=date(2026, 8, 1)),
        _item("b", posted_at=date(2026, 9, 9)),
        _item("c", posted_at=date(2026, 8, 15)),
    ]
    signals = at.signals_for(items, [])

    assert signals.first_posted_at == date(2026, 8, 1)
    assert signals.last_posted_at == date(2026, 9, 9)


def test_same_input_always_returns_same_output():
    """재현 가능성 — 같은 입력이면 몇 번을 불러도 같은 결과."""
    items = [_item("a", posted_at=date(2026, 9, 9))]
    judgements = [_judgement("a", severity="높음", mentioned_service="토스")]

    first = at.signals_for(items, judgements)
    second = at.signals_for(items, judgements)

    assert first == second


# ══════════════════════════════════════════════
# publish_gate
# ══════════════════════════════════════════════


def test_publish_gate_passes_when_all_thresholds_met(monkeypatch):
    monkeypatch.setattr(settings, "PUBLISH_MIN_CASES", 2)
    monkeypatch.setattr(settings, "PUBLISH_MIN_SOURCES", 2)
    monkeypatch.setattr(settings, "PUBLISH_MIN_EVIDENCE", 1)

    items = [
        _item("a", source_name="지식iN"),
        _item("b", source_name="네이버 카페"),
    ]
    signals = at.signals_for(items, [])
    gate = at.publish_gate(signals, case_count=2, evidence_count=1)

    assert gate.passed is True
    assert gate.reason == ""
    assert gate.min_cases == settings.PUBLISH_MIN_CASES
    assert gate.min_sources == settings.PUBLISH_MIN_SOURCES
    assert gate.min_evidence == settings.PUBLISH_MIN_EVIDENCE


def test_publish_gate_reports_korean_reason_for_each_shortfall(monkeypatch):
    monkeypatch.setattr(settings, "PUBLISH_MIN_CASES", 20)
    monkeypatch.setattr(settings, "PUBLISH_MIN_SOURCES", 3)
    monkeypatch.setattr(settings, "PUBLISH_MIN_EVIDENCE", 3)

    items = [_item("a", source_name="지식iN")]
    signals = at.signals_for(items, [])
    gate = at.publish_gate(signals, case_count=12, evidence_count=1)

    assert gate.passed is False
    assert gate.case_count_ok is False
    assert gate.source_count_ok is False
    assert gate.evidence_count_ok is False
    assert "관련 사례 부족(12/20)" in gate.reason
    assert "서로 다른 출처 부족(1/3)" in gate.reason
    assert "근거 요약 부족(1/3)" in gate.reason


def test_publish_gate_reads_settings_at_call_time(monkeypatch):
    """모듈 레벨로 캡처하지 않는다 — 테스트가 settings 를 갈아끼울 수 있어야 한다."""
    items = [_item(f"i{i}") for i in range(3)]
    signals = at.signals_for(items, [])

    monkeypatch.setattr(settings, "PUBLISH_MIN_CASES", 3)
    assert at.publish_gate(signals, case_count=3, evidence_count=0).case_count_ok is True

    monkeypatch.setattr(settings, "PUBLISH_MIN_CASES", 4)
    assert at.publish_gate(signals, case_count=3, evidence_count=0).case_count_ok is False


def test_source_count_derived_from_source_name_counts_length():
    items = [
        _item("a", source_name="지식iN"),
        _item("b", source_name="네이버 카페"),
        _item("c", source_name="네이버 블로그"),
    ]
    signals = at.signals_for(items, [])

    gate = at.publish_gate(signals, case_count=3, evidence_count=3)
    assert len(signals.source_name_counts) == 3
    assert gate.source_count_ok == (3 >= settings.PUBLISH_MIN_SOURCES)
