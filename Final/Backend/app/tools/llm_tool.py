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
from app.core.llm import LLMError, get_llm
from app.prompts.interpreter_prompts import judge_pains_prompt
from app.schemas.models import (
    Idea,
    Judgement,
    Problem,
    ProblemCandidate,
    ProblemDraft,
    RawItem,
    ReviewResult,
    UserCondition,
)
from app.tools import text_tool


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


def judge_pains(items: list[RawItem]) -> list[Judgement]:
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
        out.extend(_judge_batch(items[start : start + batch_size]))
    return out


def judge_call_count(item_count: int) -> int:
    """LLM 호출이 몇 번 나갈지. 실행 전 비용 안내와 매니페스트에 쓴다."""
    if item_count <= 0:
        return 0
    batch_size = max(int(settings.JUDGE_BATCH_SIZE), 1)
    return -(-item_count // batch_size)


# ── judge_pains 내부 ────────────────────────────


def _judge_batch(batch: list[RawItem]) -> list[Judgement]:
    """배치 하나. 여기서 실패해도 예외를 올리지 않는다."""
    prompt = judge_pains_prompt(
        json.dumps([_payload(i) for i in batch], ensure_ascii=False, indent=1)
    )
    kwargs: dict = {"max_tokens": 220 * len(batch) + 400, "temperature": 0.0}
    if settings.judge_model:
        kwargs["model"] = settings.judge_model

    try:
        raw = get_llm().complete_json(prompt, **kwargs)
    except LLMError as e:
        logger.warning("판별 배치 %d건 실패 — '낮음'으로 강등한다: %s", len(batch), e)
        return [_degraded(i) for i in batch]

    rows = _as_rows(raw)
    if rows is None:
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
        judged[item_id] = _to_judgement(row, by_id[item_id])

    # 방어 2 — 응답 누락 보정. 빠진 건을 조용히 버리지 않는다.
    missing = [i for i in batch if i.id not in judged]
    if missing:
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
    has_need_signal 은 규칙으로 세는 값이라 모델과 무관하게 채운다.
    """
    return Judgement(
        raw_item_id=item.id,
        is_pain=False,
        pain_summary=None,
        confidence=_SAFE_CONFIDENCE,
        severity=None,
        has_need_signal=text_tool.has_need_signal(f"{item.title} {item.snippet}"),
    )


def _to_judgement(row: dict, item: RawItem) -> Judgement:
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

    need = row.get("has_need_signal")
    has_need = (
        _as_bool(need, default=False)
        if isinstance(need, bool)
        # 모델이 안 줬으면 규칙으로 보완한다 (docs/DATA_SPEC.md 4절 필요도 재료).
        else text_tool.has_need_signal(f"{item.title} {item.snippet}")
    )

    return Judgement(
        raw_item_id=item.id,
        is_pain=is_pain,
        pain_summary=summary,
        confidence=confidence,
        severity=severity,
        has_need_signal=has_need,
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

def candidate_material(candidate: ProblemCandidate) -> str:
    """묶음을 LLM에 넣을 재료 텍스트로."""
    raise NotImplementedError


def merge_material(problems: list[Problem]) -> str:
    """기존 문제 2~3개를 합칠 재료 텍스트로 (F05)."""
    raise NotImplementedError


def write_problem(material: str) -> ProblemDraft:
    """재료를 읽고 문제정의를 쓴다. ★ 숫자를 만들지 않는다."""
    raise NotImplementedError


def review_problem(draft: ProblemDraft, similar: list[Problem]) -> ReviewResult:
    """근거가 충분한가 / 기존과 겹치는가 → 게시·보류·병합."""
    raise NotImplementedError


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
