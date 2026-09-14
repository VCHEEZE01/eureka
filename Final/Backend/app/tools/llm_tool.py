"""
LLM 도구 — 모델을 부르는 유일한 곳.

쓰는 사람: 전원 (각자 자기 함수만 채운다)

★ 프롬프트 문자열은 여기 쓰지 말고 prompts/ 에서 가져올 것.
★ 모델 클라이언트는 core/llm.py 에 만들고 여기서 가져다 쓸 것.
"""

import json
import logging
import re
from difflib import SequenceMatcher
from typing import Optional

from app.config.settings import settings
from app.schemas.collections import TargetProfile
from app.tools import target_evidence_tool
from app.core.llm import LLMError, get_llm
from app.prompts.interpreter_prompts import judge_pains_prompt
from app.prompts.problem_prompts import (
    write_problem_prompt, repair_problem_format_prompt, review_problem_prompt,
)
from app.schemas.models import (
    AGE_BANDS,
    GENDERS,
    GENDER_SELF_MENTION_WORDS,
    SUFFERER_ROLES,
    Idea,
    Judgement,
    Problem,
    ProblemCandidate,
    ProblemDraft,
    RawItem,
    ReviewResult,
    UserCondition,
)
from app.tools import text_tool, corpus_tool


# ── ② 해석기가 쓰는 것 ──────────────────────────
#
# ★ judge_pains 는 "모델 말을 믿지 않는" 함수다.
#   한 번에 여러 건을 넣어 호출 수를 줄이되, 돌아온 응답은 전부 의심하고
#   아래 다섯 가지를 직접 확인한다. 그래야 모델이 흔들려도 코퍼스가 안 썩는다.
#
#     1. 환각 id 폐기        — 입력에 없는 id 는 버린다
#     2. 응답 누락 보정      — 빠진 입력 건은 "낮음"으로 채운다 (조용한 유실 금지)
#     3. 집계성 숫자 차단    — 요약 속 "137건" 같은 수치를 지운다 (제1규칙)
#     4. 원문 복제 차단      — 요약이 원문과 겹치면 버린다 (요약이지 복제가 아니다)
#     5. 값 정규화           — 라벨이 아닌 값·근거 없는 is_pain 을 안전하게 내린다
#
#   LLM 호출·파싱이 실패하면 그 배치를 통째로 confidence="낮음" 으로 강등하고
#   계속 간다. 예외를 위로 올리지 않는다 — 한 배치 때문에 주간 배치가 죽으면
#   그 주의 수집이 통째로 날아간다. 강등된 건은 다음 주에 다시 본다.

logger = logging.getLogger(__name__)

#: 판정 라벨. 이 셋 말고는 받지 않는다.
JUDGE_LABELS: tuple[str, ...] = ("높음", "중간", "낮음")

#: 라벨이 이상할 때 쓰는 값. 모르면 낮게 본다.
_SAFE_CONFIDENCE = "낮음"

#: 요약이 원문과 이만큼 겹치면 복제로 보고 버린다.
COPY_RATIO_LIMIT = 0.8

#: 요약 길이 상한. 프롬프트는 80자를 요구하지만 넘겨 오는 경우가 있다.
_SUMMARY_MAX_LEN = 120

#: 요약을 살려 둘 최소 길이. 숫자를 걷어낸 뒤 이보다 짧으면 버린다.
_SUMMARY_MIN_LEN = 4

#: 집계성 수치. conftest.AGGREGATE_NUMBER_RE 와 같은 패턴이다.
_AGGREGATE_NUMBER_RE = re.compile(r"\d+\s*(?:건|명|개|%|퍼센트|배|위|만|억|천|백)")

_WS_RE = re.compile(r"\s+")

#: 응답이 배열이 아니라 객체로 올 때 배열이 들어 있을 만한 키.
_LIST_KEYS = ("judgements", "results", "items", "data", "output")

_TRUE_WORDS = frozenset({"true", "1", "yes", "y", "예", "참"})
_FALSE_WORDS = frozenset({"false", "0", "no", "n", "아니오", "거짓", "null", "none", ""})


def judge_pains(items: list[RawItem], *, diagnostics: Optional[dict] = None, target_profile: Optional[TargetProfile] = None) -> list[Judgement]:
    """
    각 원문이 진짜 불편인지 판별한다.

    settings.JUDGE_BATCH_SIZE 건씩 묶어 부른다. 반환은 입력과 같은 순서·같은
    개수다 — 한 건도 조용히 사라지지 않는다.
    """
    if not items:
        return []

    # ★ settings 는 호출 시점에 읽는다. 모듈 레벨에 캡처하면 테스트가 못 갈아끼운다.
    batch_size = max(int(settings.JUDGE_BATCH_SIZE), 1)

    out: list[Judgement] = []
    for start in range(0, len(items), batch_size):
        out.extend(_judge_batch(items[start : start + batch_size], diagnostics=diagnostics, target_profile=target_profile))
    return out


def judge_call_count(item_count: int) -> int:
    """LLM 호출이 몇 번 나갈지. 실행 전 비용 안내와 매니페스트에 쓴다."""
    if item_count <= 0:
        return 0
    batch_size = max(int(settings.JUDGE_BATCH_SIZE), 1)
    return -(-item_count // batch_size)


# ── judge_pains 내부 ────────────────────────────


def _judge_batch(batch: list[RawItem], *, diagnostics: Optional[dict] = None, target_profile: Optional[TargetProfile] = None) -> list[Judgement]:
    """배치 하나. 여기서 실패해도 예외를 올리지 않는다."""
    prompt = judge_pains_prompt(
        json.dumps([_payload(i) for i in batch], ensure_ascii=False, indent=1), target_profile=target_profile
    )
    kwargs: dict = {"max_tokens": (750 if target_profile else 400) * len(batch) + 400, "temperature": 0.0}
    if settings.judge_model:
        kwargs["model"] = settings.judge_model

    try:
        raw = get_llm().complete_json(prompt, **kwargs)
    except LLMError as e:
        if diagnostics is not None:
            diagnostics["failed_batches"] = diagnostics.get("failed_batches", 0) + 1
            diagnostics["failed_items"] = diagnostics.get("failed_items", 0) + len(batch)
            diagnostics.setdefault("failed_raw_ids", []).extend(i.id for i in batch)
        logger.warning("판별 배치 %d건 실패 — '낮음'으로 강등한다: %s", len(batch), e)
        return [_degraded(i) for i in batch]

    rows = _as_rows(raw)
    if rows is None:
        if diagnostics is not None:
            diagnostics["failed_batches"] = diagnostics.get("failed_batches", 0) + 1
            diagnostics["failed_items"] = diagnostics.get("failed_items", 0) + len(batch)
            diagnostics.setdefault("failed_raw_ids", []).extend(i.id for i in batch)
        logger.warning(
            "판별 응답이 배열이 아니다 (%s) — %d건을 '낮음'으로 강등한다",
            type(raw).__name__,
            len(batch),
        )
        return [_degraded(i) for i in batch]

    by_id = {i.id: i for i in batch}
    judged: dict[str, Judgement] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        item_id = str(row.get("id") or "").strip()
        # 방어 1 — 환각 id. 입력에 없거나 이미 채운 id 는 버린다.
        if item_id not in by_id or item_id in judged:
            if item_id not in by_id:
                logger.warning("입력에 없는 id 를 응답이 만들었다 — 버린다: %r", item_id)
            continue
        judged[item_id] = _to_judgement(row, by_id[item_id], target_profile=target_profile)

    # 방어 2 — 응답 누락 보정. 빠진 건을 조용히 버리지 않는다.
    missing = [i for i in batch if i.id not in judged]
    if missing:
        if diagnostics is not None:
            diagnostics["missing_items"] = diagnostics.get("missing_items", 0) + len(missing)
            diagnostics.setdefault("failed_raw_ids", []).extend(i.id for i in missing)
            diagnostics["failed_items"] = diagnostics.get("failed_items", 0) + len(missing)
            if not judged:
                diagnostics["failed_batches"] = diagnostics.get("failed_batches", 0) + 1
        logger.warning(
            "응답에 %d/%d건이 빠졌다 — '낮음'으로 채운다", len(missing), len(batch)
        )
    return [judged.get(i.id) or _degraded(i) for i in batch]


def _payload(item: RawItem) -> dict:
    """모델에 넣을 한 건. 원문 전체가 아니라 정제한 스니펫만 넘긴다."""
    return {
        "id": item.id,
        "title": text_tool.clean_text(item.title, 120),
        "text": text_tool.clean_text(item.snippet, 400),
        "source": f"{item.source_kind.value}/{item.source_name}",
    }


def _as_rows(raw: object) -> Optional[list]:
    """응답에서 판정 배열을 꺼낸다. 못 꺼내면 None."""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        for key in _LIST_KEYS:
            value = raw.get(key)
            if isinstance(value, list):
                return value
        # 판정 하나만 객체로 온 경우
        if "id" in raw:
            return [raw]
    return None


def _degraded(item: RawItem) -> Judgement:
    """
    안전 강등. 판정을 못 했다는 뜻이지 "불편이 아니다"라는 판단이 아니다.

    confidence="낮음" 이라 묶기로 넘어가지 않고, 다음 주에 다시 본다.
    has_need_signal · has_payment_signal 은 규칙으로 세는 값이라 모델과 무관하게 채운다.
    sufferer_role·sufferer_age_band·sufferer_gender·mentioned_service 는 LLM 라벨이라
    판정 실패 시 전부 None — "드러나지 않음"과 같은 값이라 안전하다.
    """
    text = f"{item.title} {item.snippet}"
    return Judgement(
        raw_item_id=item.id,
        is_pain=False,
        pain_summary=None,
        confidence=_SAFE_CONFIDENCE,
        severity=None,
        has_need_signal=text_tool.has_need_signal(text),
        has_payment_signal=text_tool.has_payment_signal(text),
    )


def _to_judgement(row: dict, item: RawItem, *, target_profile: Optional[TargetProfile] = None) -> Judgement:
    """응답 한 줄 → Judgement. 방어 3·4·5 가 여기 모여 있다."""
    is_pain = _as_bool(row.get("is_pain"), default=False)
    summary = _clean_summary(row.get("pain_summary"), item)

    # 방어 5 — 근거 없는 is_pain 은 내린다. 요약을 못 쓰면 불편이라 부르지 않는다.
    if is_pain and not summary:
        is_pain = False
    if not is_pain:
        summary = None

    confidence = _label(row.get("confidence")) or _SAFE_CONFIDENCE
    severity = _label(row.get("severity")) if is_pain else None

    text = f"{item.title} {item.snippet}"
    need = row.get("has_need_signal")
    has_need = (
        _as_bool(need, default=False)
        if isinstance(need, bool)
        # 모델이 안 줬으면 규칙으로 보완한다 (docs/DATA_SPEC.md 4절 필요도 재료).
        else text_tool.has_need_signal(text)
    )
    # ★ 지불 신호는 항상 규칙으로 센다. LLM에게 판정을 맡기지 않는다 —
    #   "PAIN_SIGNALS 와 섞지 않는다"는 원칙과 같은 이유로, 지불 신호도
    #   판별이 아니라 집계이므로 재현 가능한 규칙 쪽을 정본으로 둔다.
    has_payment = text_tool.has_payment_signal(text)

    sufferer_role = _clean_role(row.get("sufferer_role"))
    sufferer_age_band = _clean_age_band(row.get("sufferer_age_band"), text)
    # ★ 성별은 원문에 자기 서술 표현이 없으면 모델이 뭘 주든 버린다.
    #   직업·말투로 성별을 추측하는 것은 편견이다 (2026-09-11 결정).
    sufferer_gender = _clean_gender(row.get("sufferer_gender"), text)
    mentioned_service = _clean_service(row.get("mentioned_service"), item)
    payload = _payload(item)
    source = f"{payload['title']} {payload['text']}"
    experience_raw = row.get("experience_type")
    experience_type = experience_raw if isinstance(experience_raw, str) and experience_raw in {"self", "other", "mixed", "unknown"} else "unknown"
    experience = target_evidence_tool.grounded_quote(row.get("experience_evidence"), source, 300)
    status_raw = row.get("pain_status")
    status = status_raw if isinstance(status_raw, str) and status_raw in {"pain", "not_pain", "insufficient"} else ("pain" if is_pain else "not_pain" if confidence != "낮음" else "insufficient")
    if target_evidence_tool.qa_mixed(source, item.url) or experience_type == "mixed":
        experience_type, status = "mixed", "insufficient"
        sufferer_role = sufferer_age_band = sufferer_gender = None
    elif experience_type == "other":
        status = "not_pain"
        sufferer_role = sufferer_age_band = sufferer_gender = None
    if target_profile is not None and status == "pain" and (experience_type != "self" or not experience):
        status = "insufficient"
    if status != "pain":
        is_pain, summary, severity = False, None, None
    elif not is_pain:
        status = "insufficient"
    if status == "insufficient":
        confidence = "낮음"
    target_fields = target_evidence_tool.verify_target(row, source, target_profile,
        experience_type=experience_type, experience=experience) if target_profile is not None else {}

    return Judgement(
        pain_status=status,
        assessment_reason=str(row.get("assessment_reason") or "")[:300] or None,
        experience_type=experience_type,
        experience_evidence=experience,
        **target_fields,
        raw_item_id=item.id,
        is_pain=is_pain,
        pain_summary=summary,
        confidence=confidence,
        severity=severity,
        has_need_signal=has_need,
        has_payment_signal=has_payment,
        sufferer_role=sufferer_role,
        sufferer_age_band=sufferer_age_band,
        sufferer_gender=sufferer_gender,
        mentioned_service=mentioned_service,
    )


def _clean_summary(value: object, item: RawItem) -> Optional[str]:
    """방어 3·4 — 지어낸 숫자를 지우고, 원문 복제면 통째로 버린다."""
    if not isinstance(value, str):
        return None
    summary = _WS_RE.sub(" ", value).strip()
    if not summary:
        return None

    # 방어 3 — 집계성 숫자 차단. 제1규칙: 숫자는 LLM이 만들지 않는다.
    stripped = _AGGREGATE_NUMBER_RE.sub(" ", summary)
    if stripped != summary:
        logger.warning("요약에서 집계성 수치를 지웠다: %r", summary)
    summary = _WS_RE.sub(" ", stripped).strip(" ,.·")
    if len(summary) < _SUMMARY_MIN_LEN:
        return None

    # 방어 4 — 원문 복제 차단. 요약이지 복제가 아니어야 한다.
    source = text_tool.clean_text(f"{item.title} {item.snippet}", 1000)
    if copy_ratio(summary, source) > COPY_RATIO_LIMIT:
        logger.warning("요약이 원문 복제에 가깝다 — 버린다: %r", summary[:40])
        return None

    return summary[:_SUMMARY_MAX_LEN].rstrip()


def copy_ratio(summary: str, source: str) -> float:
    """
    요약의 몇 할이 원문에 그대로 들어 있는가. 1.0 이면 통째로 베낀 것이다.

    ★ 공백을 지우고 센다. 줄바꿈만 바꿔 넣는 눈속임을 막는다.
    ★ 유사도가 아니라 포함률이다 — 긴 원문에서 한 문장만 베껴도 1.0 이 나온다.
      SequenceMatcher.ratio() 를 쓰면 원문이 길다는 이유로 값이 낮아진다.
    """
    a = _WS_RE.sub("", summary or "")
    b = _WS_RE.sub("", source or "")
    if not a or not b:
        return 0.0
    matcher = SequenceMatcher(None, a, b, autojunk=False)
    matched = sum(block.size for block in matcher.get_matching_blocks())
    return matched / len(a)


def _label(value: object) -> Optional[str]:
    """"높음"|"중간"|"낮음" 이면 그대로, 아니면 None."""
    if isinstance(value, str):
        text = value.strip()
        if text in JUDGE_LABELS:
            return text
    return None


def _clean_role(value: object) -> Optional[str]:
    """SUFFERER_ROLES 고정 목록에 있는 값만 통과. 모델이 지어낸 라벨은 버린다."""
    if isinstance(value, str) and value.strip() in SUFFERER_ROLES:
        return value.strip()
    return None


def _clean_age_band(value: object, source_text: Optional[str] = None) -> Optional[str]:
    """AGE_BANDS 고정 목록에 있는 값만 통과."""
    if isinstance(value, str) and value.strip() in AGE_BANDS:
        if source_text is not None and not target_evidence_tool.self_attribute(value.strip(), source_text, "age"):
            return None
        return value.strip()
    return None


def _clean_gender(value: object, source_text: str) -> Optional[str]:
    """
    ★★ 원문에 성별 자기 서술 표현이 하나도 없으면 모델이 뭘 주든 None.

    직업·말투·문체로 성별을 추측하는 것은 편견이다 (2026-09-11 결정).
    "간호사인데 매번 번거로워요" 에는 성별 자기 서술이 없으므로 절대 채워지지
    않는다 — GENDERS 값과 일치하더라도 이 검문을 통과 못 하면 버린다.
    """
    if not isinstance(value, str) or value.strip() not in GENDERS:
        return None
    if not target_evidence_tool.self_attribute(value.strip(), source_text, "gender"):
        return None
    return value.strip()


def _clean_service(value: object, item: RawItem) -> Optional[str]:
    """
    ★ 원문에 글자 그대로(verbatim) 등장하지 않으면 None.

    브랜드명은 LLM이 가장 잘 지어내는 종류다. _clean_summary의 copy_ratio
    검증과 반대 방향 — 여기서는 "원문에 있어야만" 통과시킨다.
    """
    if not isinstance(value, str):
        return None
    name = value.strip()
    if not (1 < len(name) <= 30):
        return None
    source = f"{item.title} {item.snippet}"
    return name if name in source else None


def _as_bool(value: object, *, default: bool) -> bool:
    """모델이 "false" 같은 문자열을 보내는 경우까지 받아 준다."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in _TRUE_WORDS:
            return True
        if text in _FALSE_WORDS:
            return False
    if isinstance(value, (int, float)):
        return bool(value)
    return default


# ── ③ 문제정의 생성기가 쓰는 것 ────────────────

_PROBLEM_TEXT_FIELDS = ("title", "one_liner", "description", "context", "complexity_note")
_PROBLEM_TEXT_LIMITS = {"title": 100, "one_liner": 180, "description": 1600,
                        "context": 1200, "complexity_note": 1200}
_COMPLEXITY_GRADE_RE = re.compile(
    r"(?:복잡도|난이도)\s*[:：은는]?\s*(?:높음|중간|낮음|상|중|하|쉬움|어려움)|"
    r"\d+\s*점|[A-F]\s*등급"
)


def candidate_material(candidate: ProblemCandidate) -> str:
    """정제된 원문을 근거로 넘긴다. 집계값이나 가상 사례를 넣지 않는다."""
    ids = list(dict.fromkeys(candidate.raw_item_ids))
    items = corpus_tool.load_raw_items_by_ids(ids, weeks=settings.EVIDENCE_LOOKBACK_WEEKS)
    rows = [_payload(items[rid]) for rid in ids if rid in items]
    if not rows:
        raise ValueError("문제정의에 사용할 원문을 찾지 못했습니다")
    return json.dumps({"category": candidate.category.value,
                       "theme_hint": candidate.theme_hint, "items": rows}, ensure_ascii=False)


def merge_material(problems: list[Problem]) -> str:
    """문제 조합은 현재 잠금 상태다."""
    raise NotImplementedError("문제 조합은 아직 제공하지 않습니다")


def validate_problem_text(draft: ProblemDraft) -> None:
    """규칙 위반은 지우거나 가짜 문장으로 보정하지 않고 보류시킨다."""
    for field in _PROBLEM_TEXT_FIELDS:
        value = getattr(draft, field)
        if not value.strip() or len(value) > _PROBLEM_TEXT_LIMITS[field]:
            raise ValueError(f"문제정의 {field}가 비어 있거나 길이 제한을 넘었습니다")
        if _AGGREGATE_NUMBER_RE.search(value):
            raise ValueError(f"문제정의 {field}에 집계성 수치가 포함되었습니다")
    if _COMPLEXITY_GRADE_RE.search(draft.complexity_note):
        raise ValueError("복잡도는 점수·등급 대신 서술해야 합니다")


class _ProblemResponseShapeError(ValueError):
    """파싱은 됐지만 서술 응답의 구조가 계약과 다르다."""


def _problem_draft_from_response(raw) -> ProblemDraft:
    if not isinstance(raw, dict) or set(raw) != set(_PROBLEM_TEXT_FIELDS):
        raise _ProblemResponseShapeError("문제정의 JSON의 필드가 계약과 다릅니다")
    if any(not isinstance(raw[k], str) for k in _PROBLEM_TEXT_FIELDS):
        raise _ProblemResponseShapeError("문제정의 JSON의 서술은 문자열이어야 합니다")
    draft = ProblemDraft(**{k: raw[k].strip() for k in _PROBLEM_TEXT_FIELDS}, evidence=[])
    validate_problem_text(draft)
    return draft


def write_problem(material: str, *, diagnostics: Optional[dict] = None) -> ProblemDraft:
    """형식 오류만 한 번 재생성한다. 근거·수치·의미 검증을 완화하지 않는다."""
    if diagnostics is not None:
        diagnostics["generation_attempts"] = 0
    for attempt in range(2):
        prompt = (write_problem_prompt(material) if attempt == 0
                  else repair_problem_format_prompt(material))
        if diagnostics is not None:
            diagnostics["generation_attempts"] += 1
        # JSON 파싱 실패는 core가 이미 재시도한다. LLMError/예산 종료는 여기서 잡지 않는다.
        raw = get_llm().complete_json(prompt, max_tokens=2200, temperature=0.0)
        try:
            return _problem_draft_from_response(raw)
        except _ProblemResponseShapeError as exc:
            if attempt == 1:
                raise ValueError(f"문제정의 형식 재생성 후에도 계약 불일치: {exc}") from exc
    raise AssertionError("unreachable")



def _unsupported_problem_claim(draft: ProblemDraft, material: str) -> Optional[str]:
    """과대 해석이 확인된 사실 유형은 원문 표현 없이는 검수 단계에서 막는다.

    전체 의미 검증을 대신하지 않는다. 재담당→복귀, 비유→음성 입력,
    귀찮음→피로 같은 이미 관측한 실패를 모델 재량에만 맡기지 않는 방어다.
    """
    try:
        payload = json.loads(material)
        source = " ".join(f"{row.get('title', '')} {row.get('text', '')}"
                          for row in payload["items"])
    except (ValueError, KeyError, TypeError, AttributeError):
        return "원문 대조 자료 형식이 올바르지 않습니다"
    narrative = " ".join(getattr(draft, field) for field in _PROBLEM_TEXT_FIELDS)
    # 수집 스니펫에 없는 민감한 원인·감정·매체 전제를 도입하지 않는다.
    for term, supported_forms in {
        "복귀": ("복귀",), "휴직": ("휴직",), "이직": ("이직",),
        "퇴사": ("퇴사",), "음성": ("음성", "목소리", "오디오"),
        "녹음": ("녹음",), "피로": ("피로", "피곤"),
        "스트레스": ("스트레스",),
    }.items():
        if term in narrative and not any(form in source for form in supported_forms):
            return f"원문에 확인되지 않은 표현을 추가했습니다: {term}"
    return None

def review_problem(draft: ProblemDraft, similar: list[Problem], *, material: str = "") -> ReviewResult:
    """숫자·중복 방어 후 모델이 원문과 대조한다. 근거 없으면 게시하지 않는다."""
    validate_problem_text(draft)
    title_key = _WS_RE.sub("", draft.title).casefold()
    for problem in similar:
        if _WS_RE.sub("", problem.title).casefold() == title_key:
            return ReviewResult(decision="merge", reason="동일한 제목의 기존 문제가 있어 검토가 필요합니다",
                                merge_into_problem_id=problem.id)
    if not material:
        return ReviewResult(decision="hold", reason="원문 대조 자료가 없습니다")
    unsupported = _unsupported_problem_claim(draft, material)
    if unsupported:
        return ReviewResult(decision="hold", reason=unsupported)
    raw = get_llm().complete_json(
        review_problem_prompt(material, json.dumps(
            {k: getattr(draft, k) for k in _PROBLEM_TEXT_FIELDS}, ensure_ascii=False)),
        max_tokens=700, temperature=0.0,
    )
    if (not isinstance(raw, dict) or set(raw) != {"decision", "reason"}
            or raw.get("decision") not in {"publish", "hold"}
            or not isinstance(raw.get("reason"), str) or not raw["reason"].strip()
            or _AGGREGATE_NUMBER_RE.search(raw["reason"])):
        raise ValueError("근거 검수 JSON이 올바르지 않습니다")
    return ReviewResult(decision=raw["decision"], reason=raw["reason"].strip())


# ── ④ 아이디어 생성기가 쓰는 것 ────────────────

def problem_material(problem: Problem) -> str:
    """문제를 LLM에 넣을 재료 텍스트로."""
    raise NotImplementedError


def write_ideas(material: str, count: int = 3) -> list[Idea]:
    """서로 다른 접근으로 아이디어 3~5개. ★ 시장 수치를 만들지 않는다."""
    raise NotImplementedError


def adapt_to_condition(ideas: list[Idea], condition: UserCondition) -> list[Idea]:
    """사용자 조건에 맞게 고치고 적합 이유를 붙인다 (F07)."""
    raise NotImplementedError
