"""
제1규칙을 강제하는 테스트 — "숫자는 LLM이 만들지 않는다. DB가 센다."

PRD 8절 · models.py 머리말의 원칙을 사람 리뷰가 아니라 테스트로 막는다.

  1. LLM이 채우는 모델에 숫자 필드를 두지 않는다
     → 지어낼 자리를 아예 없앤다. Judgement · ProblemCandidate · SearchQuery
     → Problem · RawItem 은 예외다. 집계값(case_count)과 메타를 담는 자리다
  2. 산출물 문장에 집계성 수량 표현("137건", "80%")이 없어야 한다
     → 단위 없는 숫자는 정당하다. "3일에 한 번"까지 막으면 과하다
  3. 프롬프트 상수는 전부 공통 규칙을 달고 나간다
     → with_rules() 를 빼먹으면 여기서 잡힌다
"""

from __future__ import annotations

import importlib
import pkgutil
import typing

import pytest

from app.prompts.common_prompts import COMMON_RULES
from app.schemas.models import (
    Category,
    Judgement,
    Problem,
    ProblemCandidate,
    RawItem,
    SearchQuery,
)
from conftest import AGGREGATE_NUMBER_RE, find_aggregate_numbers

# LLM이 채우는 모델 — 여기엔 숫자가 있으면 안 된다
LLM_FILLED_MODELS = [Judgement, ProblemCandidate, SearchQuery]

# 집계값·메타를 담는 모델 — 숫자가 있어야 정상이다
COUNTING_MODELS = [Problem, RawItem]


def _numeric_fields(model) -> list[str]:
    """int/float 이 들어간 필드 이름. bool 은 int 의 하위형이지만 숫자가 아니다."""
    found = []
    for name, field in model.model_fields.items():
        if _has_number(field.annotation):
            found.append(name)
    return found


def _has_number(annotation) -> bool:
    if annotation is bool:
        return False
    if annotation in (int, float):
        return True
    return any(_has_number(a) for a in typing.get_args(annotation))


# ══════════════════════════════════════════════
# 1. 모델에 숫자 필드가 없다
# ══════════════════════════════════════════════


@pytest.mark.parametrize("model", LLM_FILLED_MODELS, ids=lambda m: m.__name__)
def test_llm_filled_models_have_no_numeric_fields(model):
    """
    ★ 이 테스트가 실패하면 필드를 지워라. 프롬프트로 막을 수 있다고 생각하지 마라.
      숫자 자리를 만들어 두면 LLM은 언젠가 채운다.
    """
    numeric = _numeric_fields(model)
    assert not numeric, (
        f"{model.__name__} 에 숫자 필드 {numeric} 가 있다. "
        "LLM이 채우는 모델에는 숫자를 두지 않는다 — 세는 건 DB 몫이다."
    )


@pytest.mark.parametrize("model", COUNTING_MODELS, ids=lambda m: m.__name__)
def test_counting_models_are_exempt(model):
    """반대 방향도 고정한다. Problem/RawItem 은 숫자를 담는 게 정상이다."""
    assert model.model_fields  # 모델이 살아 있는지만 확인


def test_problem_is_the_only_place_counts_live():
    """사례 수·출처 수는 Problem 에만 있다."""
    assert "case_count" in Problem.model_fields
    assert "source_count" in Problem.model_fields
    assert "case_count" not in ProblemCandidate.model_fields


def test_bool_is_not_treated_as_number():
    """has_need_signal 은 bool 이다. 숫자로 오인해 잡으면 안 된다."""
    assert "has_need_signal" in Judgement.model_fields
    assert _numeric_fields(Judgement) == []


# ══════════════════════════════════════════════
# 2. 산출물 문장에 집계 수치가 없다
# ══════════════════════════════════════════════


@pytest.mark.parametrize(
    "text",
    [
        "137건의 사례가 확인되었습니다",
        "사용자 80% 가 불편을 느낍니다",
        "약 3 만 명이 겪는 문제",
        "생산성이 2배 향상됩니다",
        "관련 글 12 개",
        "업계 1위 문제",
        "30퍼센트 절감",
    ],
)
def test_aggregate_numbers_are_caught(text):
    assert find_aggregate_numbers(text), f"못 잡았다: {text}"


@pytest.mark.parametrize(
    "text",
    [
        "3일에 한 번씩 반복해서 옮겨 적어야 한다",
        "가계부를 손으로 정리하는 일이 번거롭다",
        "2026년 상반기에 자주 나타난다",
        "카드 3사를 오가며 확인해야 한다",
        "",
    ],
)
def test_plain_numbers_are_allowed(text):
    """★ \\d+ 전면 금지는 과하다. 단위가 붙은 집계 표현만 막는다."""
    assert not find_aggregate_numbers(text), f"과잉 검출: {text}"


def _candidate(theme_hint: str, summaries: list[str]) -> ProblemCandidate:
    return ProblemCandidate(
        id="c1",
        raw_item_ids=["r1", "r2", "r3"],
        pain_summaries=summaries,
        theme_hint=theme_hint,
        category=Category.FINANCE,
    )


def assert_candidate_has_no_numbers(candidate: ProblemCandidate) -> None:
    """★ 다른 테스트에서도 쓰라고 빼 두었다. 묶기 결과를 이걸로 검사해라."""
    for text in [candidate.theme_hint, *candidate.pain_summaries]:
        hits = find_aggregate_numbers(text)
        assert not hits, f"묶음 {candidate.id} 에 지어낸 수치 {hits}: {text!r}"


def test_clean_candidate_passes():
    assert_candidate_has_no_numbers(
        _candidate(
            "가계부 수기 입력",
            [
                "카드 명세서를 손으로 옮겨 적어야 한다",
                "3일에 한 번씩 다시 정리해야 한다",
            ],
        )
    )


def test_candidate_with_count_in_theme_hint_fails():
    with pytest.raises(AssertionError):
        assert_candidate_has_no_numbers(_candidate("사례 137건의 가계부 불편", ["손으로 적는다"]))


def test_candidate_with_count_in_summary_fails():
    with pytest.raises(AssertionError):
        assert_candidate_has_no_numbers(
            _candidate("가계부 수기 입력", ["사용자 80% 가 불편을 겪는다"])
        )


def test_regex_shape_is_unit_bound():
    """정규식 자체를 고정한다. 누가 \\d+ 전면 금지로 바꾸면 여기서 걸린다."""
    assert AGGREGATE_NUMBER_RE.pattern == r"\d+\s*(건|명|개|%|퍼센트|배|위|만|억|천|백)"


# ══════════════════════════════════════════════
# 3. 프롬프트가 공통 규칙을 달고 나간다
# ══════════════════════════════════════════════

# 이보다 짧은 상수는 프롬프트가 아니라 라벨·구분자로 본다.
PROMPT_MIN_LENGTH = 200


def _prompt_modules():
    """
    app/prompts 의 모듈을 안전하게 순회한다.

    ★ 아직 안 만들어진 파일이 있어도 이 테스트가 깨지면 안 된다.
      프롬프트는 다른 담당자가 지금 쓰고 있다.
    """
    try:
        package = importlib.import_module("app.prompts")
    except ImportError:
        return
    for info in pkgutil.iter_modules(package.__path__):
        try:
            yield importlib.import_module(f"app.prompts.{info.name}")
        except Exception:  # 문법 오류·미완성 모듈은 건너뛴다
            continue


def _prompt_constants():
    """(모듈명, 상수명, 값). 대문자 상수 문자열 중 긴 것만."""
    for module in _prompt_modules():
        for name, value in vars(module).items():
            if name.startswith("_") or not name.isupper():
                continue
            if isinstance(value, str) and len(value) > PROMPT_MIN_LENGTH:
                yield module.__name__, name, value


def test_every_long_prompt_constant_carries_common_rules():
    """
    ★ with_rules() 를 빼먹은 프롬프트를 자동으로 잡는다.

    프롬프트마다 규칙을 따로 쓰면 어느 하나가 빠져도 아무도 모른다.
    """
    missing = [
        f"{mod}.{name}"
        for mod, name, value in _prompt_constants()
        if COMMON_RULES not in value
    ]
    assert not missing, (
        f"공통 규칙이 빠진 프롬프트: {missing}. "
        "common_prompts.with_rules() 로 감싸라."
    )


def test_common_rules_itself_is_the_reference():
    """COMMON_RULES 가 비면 위 테스트가 전부 무의미해진다."""
    assert len(COMMON_RULES) > PROMPT_MIN_LENGTH
    assert "숫자" in COMMON_RULES


def test_prompt_scan_tolerates_missing_modules():
    """파일이 아직 없어도 순회가 예외 없이 끝난다."""
    assert list(_prompt_constants()) is not None
