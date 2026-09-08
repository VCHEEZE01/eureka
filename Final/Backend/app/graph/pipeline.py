"""
에이전트 4개를 잇는 곳.

★ 각자 만든 에이전트가 여기서 합쳐진다.
  담당자들은 이 파일을 건드릴 일이 거의 없다 — 자기 에이전트만 채우면 된다.

두 가지 흐름이 있다.

  [배치]   run_collect_pipeline()
           ① 수집 → ② 해석 → ③ 문제정의 → 게시/보류/병합
           스케줄러가 주기적으로 부른다. 사용자와 무관.

  [실시간] run_combine() / run_ideas()
           사용자가 누를 때 그 자리에서 돈다. 진행 상태를 흘려보낸다.

나중에 LangGraph로 바꿀 때도 이 함수들의 입출력은 그대로 두면 된다.
"""

from typing import Optional

from app.agents.base import ProgressFn
from app.agents.problem_agent import ProblemOutput
from app.schemas.models import Category, Idea, Problem, SourceKind, UserCondition


def run_collect_pipeline(
    category: Category,
    source_kinds: Optional[list[SourceKind]] = None,
    on_progress: Optional[ProgressFn] = None,
) -> list[Problem]:
    """
    [배치] 수집 → 해석 → 문제정의 → 게시.

    실패해도 사용자 화면에는 영향이 없어야 한다.
    """
    raise NotImplementedError


def run_combine(
    problems: list[Problem],
    on_progress: Optional[ProgressFn] = None,
) -> ProblemOutput:
    """
    [실시간] F05 문제정의 조합. 기존 문제 2~3개를 하나로 합친다.

    ★ 새 에이전트가 아니라 ③ 문제정의 생성기를 재사용한다.
      입력만 candidate 대신 existing_problems 로 바꾼다.
    """
    raise NotImplementedError


def run_ideas(
    problem: Problem,
    condition: Optional[UserCondition] = None,
    on_progress: Optional[ProgressFn] = None,
) -> list[Idea]:
    """
    [실시간] F06 기본 아이디어 / F07 개인화.

    ★ 하나의 함수다. condition 이 있으면 개인화, 없으면 기본.
      별도 에이전트를 만들지 않는다.
    """
    raise NotImplementedError
