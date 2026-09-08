"""
④ 아이디어 생성기

역할  : 문제 하나에서 "이걸 이렇게 만들어보면?" 아이디어를 뽑는다
입력  : 문제  ＋  사용자 조건(선택)
출력  : 아이디어 3~5개

★ 조건이 선택 입력인 것이 핵심
    · 조건 없이 부르면 → 기본 아이디어      (F06)
    · 조건을 넣으면    → 개인화 아이디어    (F07)
  같은 생성기를 재사용한다. 별도 에이전트를 만들지 않는다.

할 일
  1. 서로 다른 해결 접근으로 3~5개를 만든다   → LLM
  2. 각각 "왜 이 문제와 연결되는지"를 쓴다
  3. 조건이 있으면 조건에 맞게 고치고 이유를 붙인다
  4. 리소스가 적으면 기능 범위를 줄여 제안한다

규칙
  · 시장 규모·성공 확률 같은 근거 없는 수치를 만들지 말 것
  · "검증된 아이디어"처럼 표현하지 말 것 → 어디까지나 "추천 후보"
"""

from typing import Optional

from app.agents.base import Agent
from app.schemas.models import Idea, Problem, UserCondition
from pydantic import BaseModel


class IdeaInput(BaseModel):
    problem: Problem
    condition: Optional[UserCondition] = None  # 없으면 기본 아이디어
    count: int = 3


class IdeaAgent(Agent[IdeaInput, list[Idea]]):
    name = "아이디어 생성기"
    steps = ["문제 읽기", "아이디어 뽑기", "조건 반영", "범위 조정"]

    def run(self, data: IdeaInput) -> list[Idea]:
        raise NotImplementedError("④ 담당자가 구현합니다")
