"""
③ 문제정의 생성기

역할  : 불편 뭉치를 읽고 "하나의 문제"로 써낸다. 그리고 검수한다
입력  : 문제 후보  ★또는★  기존 문제 2~3개
출력  : 문제정의 초안 + 검수 결과

★ 입력이 두 가지인 것이 핵심
    · 후보를 넣으면      → 새 문제를 만든다   (배치)
    · 기존 문제를 넣으면 → 문제 조합이 된다   (F05, 실시간)
  같은 생성기를 재사용한다. 별도 에이전트를 만들지 않는다.

할 일
  1. 뭉치를 읽고 제목·설명·맥락을 쓴다     → LLM
  2. 근거를 3~5건 골라 정리한다
  3. 검수한다 → publish(게시) / hold(보류) / merge(병합)

규칙
  · "사례 137건" 같은 숫자를 만들지 말 것
    → ProblemDraft 에 숫자 필드가 없는 이유. 숫자는 DB가 센다
"""

from typing import Optional

from app.agents.base import Agent
from app.schemas.models import Problem, ProblemCandidate, ProblemDraft, ReviewResult
from pydantic import BaseModel


class ProblemInput(BaseModel):
    """둘 중 하나만 채운다."""

    candidate: Optional[ProblemCandidate] = None
    existing_problems: Optional[list[Problem]] = None  # F05 조합용


class ProblemOutput(BaseModel):
    draft: ProblemDraft
    review: ReviewResult


class ProblemAgent(Agent[ProblemInput, ProblemOutput]):
    name = "문제정의 생성기"
    steps = ["재료 읽기", "문제정의 쓰기", "근거 정리", "검수"]

    def run(self, data: ProblemInput) -> ProblemOutput:
        raise NotImplementedError("③ 담당자가 구현합니다")
