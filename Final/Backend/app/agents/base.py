"""
에이전트 공통 인터페이스.

★ 규칙 — 이것만 지키면 각자 따로 짜도 합쳐진다.

  1. 모든 에이전트는 Agent를 상속하고 run() 하나만 구현한다.
  2. 입력과 출력은 schemas/models.py 의 타입만 쓴다.
  3. 에이전트 안에서 외부 API·DB를 직접 부르지 않는다. tools/ 를 거친다.
  4. 프롬프트 문자열을 코드에 쓰지 않는다. prompts/ 에서 가져온다.

  3번이 중요한 이유: 테스트할 때 tools만 가짜로 바꾸면 되고,
  API 키가 여기저기 흩어지지 않는다.
"""

from abc import ABC, abstractmethod
from typing import Callable, Generic, Optional, TypeVar

from app.schemas.models import ProgressEvent

TIn = TypeVar("TIn")
TOut = TypeVar("TOut")

# 진행 상태를 프론트로 보낼 때 쓰는 콜백. 없으면 아무것도 안 한다.
ProgressFn = Callable[[ProgressEvent], None]


class Agent(ABC, Generic[TIn, TOut]):
    """
    모든 에이전트의 부모.

    사용 예:
        agent = CollectorAgent()
        result = agent.run(input_data)
    """

    # 화면에 보여줄 이름. 진행 상태 UI에 그대로 뜬다.
    name: str = "이름 없는 에이전트"

    # 이 에이전트가 거치는 단계들. 진행 상태 UI가 이걸로 목록을 그린다.
    steps: list[str] = []

    def __init__(self, on_progress: Optional[ProgressFn] = None):
        self._on_progress = on_progress

    @abstractmethod
    def run(self, data: TIn) -> TOut:
        """
        실제 작업. 각자 여기만 구현하면 된다.

        주의: 여기서 requests·httpx로 외부를 직접 부르지 말 것.
             app.tools 의 함수를 쓸 것.
        """
        raise NotImplementedError

    # ── 진행 상태 알리기 ──────────────────────────

    def report(self, index: int, done: bool = False) -> None:
        """
        단계 하나가 끝났음을 알린다. steps에 정의한 순서대로 부르면 된다.

        예:  self.report(0)   # "검색어 만들기" 시작
             ... 작업 ...
             self.report(0, done=True)
        """
        if self._on_progress is None or index >= len(self.steps):
            return
        self._on_progress(
            ProgressEvent(
                step=self.steps[index],
                index=index,
                total=len(self.steps),
                done=done,
            )
        )
