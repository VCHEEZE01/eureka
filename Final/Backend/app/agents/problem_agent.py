"""③ 문제정의 생성기: 근거 묶음 → 서술 → 원문 대조 검수 → 게시/보류.

아이디어·조합은 잠금 상태다. 숫자나 출처를 LLM에서 받지 않는다.
"""
from typing import Optional

from pydantic import BaseModel, model_validator

from app.agents.base import Agent
from app.core.llm import LLMError
from app.schemas.models import EvidenceBundle, Problem, ProblemCandidate, ProblemDraft, ReviewResult
from app.tools import db_tool, llm_tool


class ProblemInput(BaseModel):
    candidate: Optional[ProblemCandidate] = None
    evidence_bundle: Optional[EvidenceBundle] = None
    existing_problems: Optional[list[Problem]] = None
    persist: bool = True
    allow_hold_draft: bool = False
    human_reviewed: bool = False

    @model_validator(mode="after")
    def validate_material(self):
        if self.existing_problems is not None:
            if self.candidate is not None or self.evidence_bundle is not None:
                raise ValueError("후보와 기존 문제를 함께 입력할 수 없습니다")
            return self
        if self.candidate is None or self.evidence_bundle is None:
            raise ValueError("후보와 근거 묶음이 모두 필요합니다")
        if (self.candidate.id != self.evidence_bundle.candidate_id
                or self.candidate.category != self.evidence_bundle.category):
            raise ValueError("후보와 근거 묶음이 일치하지 않습니다")
        return self


class ProblemOutput(BaseModel):
    draft: Optional[ProblemDraft] = None
    review: ReviewResult
    problem: Optional[Problem] = None
    generation_attempts: int = 0


class ProblemAgent(Agent[ProblemInput, ProblemOutput]):
    name = "문제정의 생성기"
    steps = ["재료 읽기", "문제정의 쓰기", "근거 정리", "검수"]

    def run(self, data: ProblemInput) -> ProblemOutput:
        if data.existing_problems is not None:
            raise NotImplementedError("문제 조합은 아직 제공하지 않습니다")
        candidate, bundle = data.candidate, data.evidence_bundle
        assert candidate is not None and bundle is not None
        self.report(0)
        if not bundle.gate.passed and not data.allow_hold_draft:
            self.report(0, done=True)
            return ProblemOutput(review=ReviewResult(decision="hold", reason=bundle.gate.reason))
        draft = None
        diagnostics = {}
        try:
            material = llm_tool.candidate_material(candidate)
            self.report(0, done=True)
            self.report(1)
            draft = llm_tool.write_problem(material, diagnostics=diagnostics)
            self.report(1, done=True)
            self.report(2)
            draft.evidence = [e.model_copy(deep=True) for e in bundle.evidence]
            self.report(2, done=True)
            self.report(3)
            similar = [p for p in db_tool.find_similar_problems(draft.title)
                       if p.category == candidate.category and p.id != candidate.id]
            review = llm_tool.review_problem(draft, similar, material=material)
            if not bundle.gate.passed:
                review = ReviewResult(decision="hold", reason=f"{bundle.gate.reason} · {review.reason}")
            if review.decision == "publish" and data.persist and not data.human_reviewed:
                # 초기 운영 정책: AI 검수와 게시 기준 통과는 사람의 공개 승인을 대신하지 않는다.
                problem = db_tool.compose_problem(
                    draft, candidate.id, candidate.category, bundle=bundle, candidate=candidate,
                )
                review = ReviewResult(decision="hold", reason=f"사람 검수 대기 · {review.reason}")
            elif review.decision == "publish":
                problem = db_tool.publish_problem(
                    draft, candidate.id, candidate.category, bundle=bundle, candidate=candidate,
                    review=review, persist=data.persist, human_reviewed=data.human_reviewed,
                )
            elif data.allow_hold_draft:
                problem = db_tool.compose_problem(
                    draft, candidate.id, candidate.category, bundle=bundle, candidate=candidate,
                )
            else:
                problem = None
            self.report(3, done=True)
            return ProblemOutput(draft=draft, review=review, problem=problem,
                                 generation_attempts=diagnostics.get("generation_attempts", 0))
        except (LLMError, ValueError) as exc:
            # 실패한 생성/검수를 성공한 것처럼 바꾸지 않는다. 초안은 검토용으로만 보존한다.
            return ProblemOutput(draft=draft, generation_attempts=diagnostics.get("generation_attempts", 0), review=ReviewResult(
                decision="hold", reason=f"생성 또는 검수 실패: {type(exc).__name__}: {exc}",
            ))
