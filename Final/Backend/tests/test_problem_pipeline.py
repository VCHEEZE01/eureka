"""Synthetic 20-case integration: corpus → evidence → text → human gate → public API."""
from fastapi.testclient import TestClient

from app.config.settings import settings
from app.graph.pipeline import build_problem_outputs
from app.schemas.models import Category, ProblemCandidate, ReviewResult
from app.tools import corpus_tool, db_tool, llm_tool
from app.agents.evidence_agent import EvidenceAgent, EvidenceInput
from main import app


def test_complete_detail_contract_and_human_publication_gate(make_raw_item, make_judgement, monkeypatch):
    category = Category.IT_PRODUCTIVITY
    monkeypatch.setattr(settings, "LLM_DRY_RUN", False)
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    ids = []
    for n in range(20):
        item = make_raw_item(id=f"integration-{n}", source_name=f"합성 출처 {n % 3}",
                             snippet="합성 테스트 자료: 회의록 정리가 번거롭고 정리 방법을 찾고 있다.")
        corpus_tool.save_raw_items([item], category=category)
        corpus_tool.save_judgements([make_judgement(
            raw_item_id=item.id, is_pain=True, confidence="높음", severity="중간",
            pain_summary="회의록을 정리하는 번거로움", has_need_signal=True,
        )], category)
        ids.append(item.id)
    candidate = ProblemCandidate(id="integration-problem", raw_item_ids=ids, category=category,
                                 pain_summaries=["회의록 정리의 번거로움"], theme_hint="회의록 정리")
    calls = []
    answers = iter([
        {"title": "회의록 정리의 번거로움", "one_liner": "회의록 정리 과정이 번거롭다.",
         "description": "회의록 정리를 번거롭게 느끼며 정리 방법을 찾고 있다.",
         "context": "회의록을 정리하는 상황이다. 원인은 자료만으로 확인하기 어렵다.",
         "complexity_note": "현재 정리 절차와 자료 형식을 먼저 확인해야 한다."},
        {"decision": "publish", "reason": "합성 원문에 나타난 상황과 일치함"},
    ])
    class MockModel:
        def complete_json(self, prompt, **kwargs):
            calls.append(prompt)
            return next(answers)
    monkeypatch.setattr(llm_tool, "get_llm", lambda: MockModel())
    output = build_problem_outputs([candidate])[0]
    assert len(calls) == 2
    assert output.review.decision == "hold" and "사람" in output.review.reason
    assert output.problem.gate.passed
    assert output.problem.case_count == 20 and output.problem.source_count == 3
    assert len(output.problem.evidence) == 5
    assert output.problem.signals.severity_labeled_count == 20
    assert db_tool.list_problems() == []

    # Explicit human approval is simulated only inside this isolated test fixture.
    bundle = EvidenceAgent().run(EvidenceInput(candidates=[candidate]))[0]
    published = db_tool.publish_problem(output.draft, candidate.id, category, bundle=bundle,
        candidate=candidate, review=ReviewResult(decision="publish", reason="합성 검수 통과"),
        human_reviewed=True)
    with TestClient(app) as client:
        assert client.get("/problems").json() == [published.model_dump(mode="json")]
        detail = client.get(f"/problems/{candidate.id}").json()
        assert detail == published.model_dump(mode="json")
        assert all(e["source_url"].startswith("https://") for e in detail["evidence"])
        assert detail["gate"]["min_cases"] == 20
    assert len(calls) == 2, "Public reads must not invoke the model"
