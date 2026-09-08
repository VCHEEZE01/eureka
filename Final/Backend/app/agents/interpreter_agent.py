"""
② 해석기

역할  : 긁어온 글 중 진짜 불편만 골라내고, 비슷한 것끼리 묶는다
입력  : 원문(RawItem) 목록
출력  : 문제 후보(ProblemCandidate) 목록

할 일
  1. 각 글이 진짜 불편인지 판별한다 (광고·잡담 거르기)  → LLM
  2. 남은 것들을 비슷한 것끼리 묶는다                    → tools/cluster_tool.py
  3. 묶음마다 주제 힌트를 붙인다

규칙
  · 묶기 결과에 "몇 건" 같은 숫자를 넣지 말 것
    → raw_item_ids 길이를 세면 된다
"""

from app.agents.base import Agent
from app.schemas.models import Category, ProblemCandidate, RawItem
from pydantic import BaseModel


class InterpretInput(BaseModel):
    items: list[RawItem]
    category: Category


class InterpreterAgent(Agent[InterpretInput, list[ProblemCandidate]]):
    name = "해석기"
    steps = ["불편 판별", "묶기", "묶음 정리"]

    def run(self, data: InterpretInput) -> list[ProblemCandidate]:
        raise NotImplementedError("② 담당자가 구현합니다")
