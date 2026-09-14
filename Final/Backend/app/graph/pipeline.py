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
from app.agents.collector_agent import CollectInput, CollectorAgent
from app.agents.evidence_agent import EvidenceAgent, EvidenceInput
from app.agents.interpreter_agent import InterpretInput, InterpreterAgent
from app.agents.problem_agent import ProblemAgent, ProblemInput, ProblemOutput
from app.schemas.models import (
    Category,
    EvidenceBundle,
    Idea,
    Problem,
    ProblemCandidate,
    SourceKind,
    UserCondition,
)


def run_collect_pipeline(
    category: Category,
    source_kinds: Optional[list[SourceKind]] = None,
    on_progress: Optional[ProgressFn] = None,
    *,
    use_llm: bool = True,
) -> list[EvidenceBundle]:
    """
    [배치] 수집 → 해석 → 근거 조립. ★ ③ 문제정의 생성기 이전까지다.

    ③(ProblemAgent)이 아직 스텁이라 Problem 객체를 만들 수 없다. 대신 근거
    조립기(②′)까지 연결해 두면, ③이 없어도 근거 상세 페이지가 필요로 하는
    ProblemSignals·PublishGate·근거 선별이 전부 나온다 — ③을 기다리지 않는다.

    on_progress 를 세 에이전트에 그대로 넘기면 steps 9개
    (수집 3 + 해석 3 + 근거 3)가 순서대로 흐른다.

    실패해도 사용자 화면에는 영향이 없어야 한다 — 각 에이전트가 자기 선에서
    예외를 삼킨다(CollectorAgent 는 쿼리 단위, InterpreterAgent 는 판정 단위).
    """
    # docs/DATA_SPEC.md 0절: 배치는 항상 전체 출처를 수집한다.
    kinds = source_kinds if source_kinds else list(SourceKind)
    items = CollectorAgent(on_progress).run(
        CollectInput(category=category, source_kinds=kinds)
    )
    candidates = InterpreterAgent(on_progress).run(
        InterpretInput(items=items, category=category, use_llm=use_llm)
    )
    bundles = EvidenceAgent(on_progress).run(EvidenceInput(candidates=candidates))
    return bundles


def build_problem_outputs(
    candidates: list[ProblemCandidate],
    on_progress: Optional[ProgressFn] = None,
    *,
    persist: bool = True,
    allow_hold_draft: bool = False,
) -> list[ProblemOutput]:
    """저장된 후보 → 근거 집계 → 문제정의·검수. 보류 미리보기는 명시적으로 요청한다."""
    unique = {candidate.id: candidate for candidate in candidates}
    bundles = EvidenceAgent(on_progress).run(EvidenceInput(candidates=list(unique.values())))
    agent = ProblemAgent(on_progress)
    return [agent.run(ProblemInput(
        candidate=unique[bundle.candidate_id], evidence_bundle=bundle,
        persist=persist, allow_hold_draft=allow_hold_draft,
    )) for bundle in bundles]


def run_problem_pipeline(
    category: Category,
    source_kinds: Optional[list[SourceKind]] = None,
    on_progress: Optional[ProgressFn] = None,
    *,
    limit: int = 50,
    keyword_limit: Optional[int] = None,
) -> list[ProblemOutput]:
    """명시적으로 실행하는 배치 경로. 조회 API에서는 호출하지 않는다."""
    items = CollectorAgent(on_progress).run(CollectInput(
        category=category, source_kinds=source_kinds or list(SourceKind),
        limit=limit, keyword_limit=keyword_limit,
    ))
    candidates = InterpreterAgent(on_progress).run(InterpretInput(
        items=items, category=category, use_llm=True, max_llm_items=limit,
    ))
    return build_problem_outputs(candidates, on_progress)


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
