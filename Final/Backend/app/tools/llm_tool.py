"""
LLM 도구 — 모델을 부르는 유일한 곳.

쓰는 사람: 전원 (각자 자기 함수만 채운다)

★ 프롬프트 문자열은 여기 쓰지 말고 prompts/ 에서 가져올 것.
★ 모델 클라이언트는 core/llm.py 에 만들고 여기서 가져다 쓸 것.
"""

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


# ── ② 해석기가 쓰는 것 ──────────────────────────

def judge_pains(items: list[RawItem]) -> list[Judgement]:
    """각 원문이 진짜 불편인지 판별한다."""
    raise NotImplementedError


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
