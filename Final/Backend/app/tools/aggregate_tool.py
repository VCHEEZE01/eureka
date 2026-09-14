"""
집계 도구 — 근거 상세 페이지가 보여줄 숫자를 전부 여기서 만든다.

쓰는 사람: ②′ 근거 조립기 (EvidenceAgent)

★★ 원칙 (docs/DATA_SPEC.md 4절) — AI는 라벨만 붙이고, 숫자는 여기가 센다.
  이 파일은 순수 함수만 담는다.
    · llm_tool 을 절대 import하지 않는다 — 숫자를 만드는 자리에 LLM을 들이지 않는다.
    · corpus_tool 도 import하지 않는다 — 파일 IO를 하는 순간 "같은 입력 → 같은
      출력"이 깨질 수 있다. 주차 키 형식은 corpus_tool.week_key() 와 맞추되
      로직만 그대로 복제해 둔다(아래 _week_key). 두 함수가 어긋나면
      tests/test_aggregate_tool.py 의 회귀 테스트가 잡는다.
    · 파일 IO를 하지 않는다.
  같은 입력이면 언제 불러도 같은 출력이 나와야 "왜 12건인지"를 재현할 수 있다.

계약 3개 (tests/test_aggregate_tool.py 가 고정한다)
  1. items 와 judgements 는 raw_item_id 로 교집합만 본다.
     RawItem 원본을 못 찾은 Judgement 는 라벨 집계(label_counts·service_mentions)
     에서 제외한다. source_kind_counts 등 RawItem 자체에서만 나오는 값과
     signal_type_counts·payment_signal_count(RawItem 텍스트에서 재계산하는 값)는
     judgements 유무와 무관하게 items 전부를 본다.
  2. observed_until=None 이면 어떤 주차도 partial=True 로 세우지 않는다.
     현재 시각을 몰래 읽지 않는다 — 호출자가 "관측 시점"을 명시적으로 준 경우에만
     그 주차가 관측 창을 온전히 덮었는지 판단한다.
  3. 빈 입력이면 전 필드 0/빈 dict 로 예외 없이 끝난다.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from typing import Optional

from app.config.settings import settings
from app.schemas.models import Judgement, ProblemSignals, PublishGate, RawItem, ServiceMention, WeekCount
from app.tools import text_tool


# ══════════════════════════════════════════════
# 주차 키 — corpus_tool.week_key() 와 형식을 맞춘다 (로직만 복제, import는 안 한다)
# ══════════════════════════════════════════════


def _week_key(d: date) -> str:
    """ISO 주차 문자열. 예: 2026-W37. corpus_tool.week_key() 와 동일한 형식이어야 한다."""
    if isinstance(d, datetime):
        d = d.date()
    iso = d.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def _week_is_partial(week: str, observed_until: date) -> bool:
    """
    observed_until 이 이 주차를 온전히 덮지 못했으면 True.

    ISO 주는 일요일에 끝난다. observed_until 의 주차가 이 주차와 같고
    observed_until 이 그 주의 마지막 날(일요일)이 아니면, 이 주는 아직
    관측 창 안에서 다 채워지지 않은 것이다.
    """
    if _week_key(observed_until) != week:
        return False
    return observed_until.isoweekday() != 7


# ══════════════════════════════════════════════
# 순수 함수 5개
# ══════════════════════════════════════════════


def source_breakdown(items: list[RawItem]) -> tuple[dict[str, int], dict[str, int]]:
    """⑧ 표본의 폭 — 출처 유형별·매체명별 건수."""
    kind_counts = Counter(i.source_kind.value for i in items)
    name_counts = Counter(i.source_name for i in items)
    return dict(kind_counts), dict(name_counts)


def time_distribution(
    items: list[RawItem], *, observed_until: Optional[date] = None
) -> tuple[Optional[date], Optional[date], int, list[WeekCount], int]:
    """
    ④ 시간 분포 — (첫 작성일, 마지막 작성일, 관측 주차 수, 주별 건수, 작성일 없는 건수).

    posted_at 이 있는 것만 본다. undated_count 는 posted_at 이 없어서
    빠진 건수다 — 지식iN·카페는 작성일을 주지 않는다.
    """
    dated = [i for i in items if i.posted_at is not None]
    undated_count = len(items) - len(dated)
    if not dated:
        return None, None, 0, [], undated_count

    first_posted = min(i.posted_at for i in dated)
    last_posted = max(i.posted_at for i in dated)

    counts: Counter = Counter(_week_key(i.posted_at) for i in dated)
    weeks_sorted = sorted(counts)
    weekly_counts = [
        WeekCount(
            week=w,
            count=counts[w],
            partial=bool(observed_until is not None and _week_is_partial(w, observed_until)),
        )
        for w in weeks_sorted
    ]
    return first_posted, last_posted, len(weeks_sorted), weekly_counts, undated_count


def label_counts(items: list[RawItem], judgements: list[Judgement]) -> dict:
    """
    ⑦⑤ Judgement 라벨의 합.

    ★ 계약 1 — RawItem 을 못 찾은 Judgement 는 여기서 제외한다.
      items 에 없는 raw_item_id 를 가진 판정은 "근거를 확인할 수 없는 라벨"이라
      세지 않는다.
    """
    item_ids = {i.id for i in items}
    matched = [j for j in judgements if j.raw_item_id in item_ids]

    severity_counts: Counter = Counter()
    severity_labeled_count = 0
    need_signal_count = 0
    role_counts: Counter = Counter()
    role_labeled_count = 0
    age_counts: Counter = Counter()
    age_labeled_count = 0
    gender_counts: Counter = Counter()
    gender_labeled_count = 0

    for j in matched:
        if j.is_pain and j.severity is not None:
            severity_counts[j.severity] += 1
            severity_labeled_count += 1
        if j.has_need_signal:
            need_signal_count += 1
        if j.sufferer_role is not None:
            role_counts[j.sufferer_role] += 1
            role_labeled_count += 1
        if j.sufferer_age_band is not None:
            age_counts[j.sufferer_age_band] += 1
            age_labeled_count += 1
        if j.sufferer_gender is not None:
            gender_counts[j.sufferer_gender] += 1
            gender_labeled_count += 1

    return {
        "severity_counts": dict(severity_counts),
        "severity_labeled_count": severity_labeled_count,
        "need_signal_count": need_signal_count,
        "role_counts": dict(role_counts),
        "role_labeled_count": role_labeled_count,
        "age_counts": dict(age_counts),
        "age_labeled_count": age_labeled_count,
        "gender_counts": dict(gender_counts),
        "gender_labeled_count": gender_labeled_count,
    }


def rule_counts(items: list[RawItem]) -> tuple[dict[str, int], int]:
    """
    ⑦① 규칙 재계산 — (signal_type_counts, payment_signal_count).

    ★ Judgement 가 아니라 RawItem 에서 text_tool.item_text() + 규칙 함수로
      다시 계산한다. 판별 때와 정확히 같은 텍스트를 봐야 건수가 어긋나지 않는다.
      judgements 유무와 무관하게 items 전부를 본다 — 계약 1의 예외.
    """
    signal_type_counts: Counter = Counter()
    payment_signal_count = 0
    for item in items:
        text = text_tool.item_text(item)
        for signal_type in text_tool.signal_hits(text):
            signal_type_counts[signal_type] += 1
        if text_tool.has_payment_signal(text):
            payment_signal_count += 1
    return dict(signal_type_counts), payment_signal_count


def service_mentions(items: list[RawItem], judgements: list[Judgement]) -> list[ServiceMention]:
    """
    ② 유사 서비스 — Judgement.mentioned_service 를 이름별로 센다.

    ★ 계약 1 적용 — RawItem 을 못 찾은 판정은 제외한다.
    정렬: count 내림차순 → 이름 사전순.
    """
    item_ids = {i.id for i in items}
    matched = [j for j in judgements if j.raw_item_id in item_ids]

    counts: Counter = Counter(j.mentioned_service for j in matched if j.mentioned_service)
    ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [ServiceMention(name=name, count=count) for name, count in ordered]


# ══════════════════════════════════════════════
# 공개 API
# ══════════════════════════════════════════════


def signals_for(
    items: list[RawItem],
    judgements: list[Judgement],
    *,
    observed_until: Optional[date] = None,
) -> ProblemSignals:
    """문제 후보 1건의 원문·판정을 전부 세어 ProblemSignals 로 만든다."""
    source_kind_counts, source_name_counts = source_breakdown(items)
    first_posted_at, last_posted_at, observed_weeks, weekly_counts, undated_count = (
        time_distribution(items, observed_until=observed_until)
    )
    labels = label_counts(items, judgements)
    signal_type_counts, payment_signal_count = rule_counts(items)
    mentioned_services = service_mentions(items, judgements)

    return ProblemSignals(
        source_kind_counts=source_kind_counts,
        source_name_counts=source_name_counts,
        first_posted_at=first_posted_at,
        last_posted_at=last_posted_at,
        observed_weeks=observed_weeks,
        weekly_counts=weekly_counts,
        undated_count=undated_count,
        severity_counts=labels["severity_counts"],
        severity_labeled_count=labels["severity_labeled_count"],
        need_signal_count=labels["need_signal_count"],
        signal_type_counts=signal_type_counts,
        payment_signal_count=payment_signal_count,
        role_counts=labels["role_counts"],
        role_labeled_count=labels["role_labeled_count"],
        age_counts=labels["age_counts"],
        age_labeled_count=labels["age_labeled_count"],
        gender_counts=labels["gender_counts"],
        gender_labeled_count=labels["gender_labeled_count"],
        mentioned_services=mentioned_services,
    )


def publish_gate(signals: ProblemSignals, case_count: int, evidence_count: int) -> PublishGate:
    """
    docs/DATA_COLLECTION.md 6절 게시 기준 판정.

    ★ settings 는 호출 시점에 읽는다 — 모듈 레벨 상수로 캡처하지 않는다.
      테스트가 PUBLISH_MIN_* 를 갈아끼울 수 있어야 한다.
    """
    min_cases = int(settings.PUBLISH_MIN_CASES)
    min_sources = int(settings.PUBLISH_MIN_SOURCES)
    min_evidence = int(settings.PUBLISH_MIN_EVIDENCE)

    source_count = len(signals.source_name_counts)

    case_count_ok = case_count >= min_cases
    source_count_ok = source_count >= min_sources
    evidence_count_ok = evidence_count >= min_evidence
    passed = case_count_ok and source_count_ok and evidence_count_ok

    reasons: list[str] = []
    if not case_count_ok:
        reasons.append(f"관련 사례 부족({case_count}/{min_cases})")
    if not source_count_ok:
        reasons.append(f"서로 다른 출처 부족({source_count}/{min_sources})")
    if not evidence_count_ok:
        reasons.append(f"근거 요약 부족({evidence_count}/{min_evidence})")

    return PublishGate(
        case_count_ok=case_count_ok,
        source_count_ok=source_count_ok,
        evidence_count_ok=evidence_count_ok,
        passed=passed,
        reason=" · ".join(reasons),
        min_cases=min_cases,
        min_sources=min_sources,
        min_evidence=min_evidence,
    )
