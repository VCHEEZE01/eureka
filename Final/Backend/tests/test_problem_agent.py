"""합성 fixture로 문제생성부터 저장·조회까지 검증. 실제 수집/모델 결과가 아니다."""
import json

import pytest

from app.agents.evidence_agent import EvidenceAgent, EvidenceInput
from app.agents.problem_agent import ProblemAgent, ProblemInput
from app.config.settings import settings
from app.core.llm import LLMError
from app.schemas.models import Category, ProblemCandidate, ProblemDraft, ReviewResult
from app.tools import corpus_tool, db_tool, llm_tool

TEXT = {
    "title": "회의 자료를 옮겨 정리할 때 남는 수기 작업",
    "one_liner": "회의 내용이 흩어져 있어 담당자가 직접 다시 정리해야 한다.",
    "description": "회의 후 기록을 업무에 활용하려면 내용을 다시 옮기는 번거로움이 있다.",
    "context": "회의 기록을 정리하는 상황에서 나타난다. 원인은 자료만으로 확인하기 어렵다.",
    "complexity_note": "기록 형식과 기존 업무 흐름의 연동 가능성을 확인해야 한다.",
}


@pytest.fixture
def material(make_raw_item, make_judgement, monkeypatch):
    monkeypatch.setattr(settings, "PUBLISH_MIN_CASES", 3)
    monkeypatch.setattr(settings, "PUBLISH_MIN_SOURCES", 3)
    monkeypatch.setattr(settings, "PUBLISH_MIN_EVIDENCE", 3)
    monkeypatch.setattr(settings, "LLM_DRY_RUN", False)
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    ids = []
    for n, source in enumerate(["합성 지식인", "합성 카페", "합성 블로그"]):
        item = make_raw_item(id=f"synthetic-{n}", source_name=source,
                             snippet="테스트용 합성 사례: 회의록을 옮겨 적기가 번거로워 자동 정리가 있었으면 합니다.")
        corpus_tool.save_raw_items([item], category=Category.IT_PRODUCTIVITY)
        judgement = make_judgement(raw_item_id=item.id, pain_summary="기록 이동 과정의 수기 정리가 번거롭다",
                                  is_pain=True, severity="높음", has_need_signal=True)
        corpus_tool.save_judgements([judgement], Category.IT_PRODUCTIVITY)
        ids.append(item.id)
    candidate = ProblemCandidate(id="synthetic-candidate", raw_item_ids=ids,
                                 pain_summaries=["회의 기록 정리 불편"], theme_hint="회의 기록 정리",
                                 category=Category.IT_PRODUCTIVITY)
    bundle = EvidenceAgent().run(EvidenceInput(candidates=[candidate]))[0]
    return candidate, bundle


def fake_llm(monkeypatch, *responses):
    calls = []
    results = iter(responses)
    class Client:
        def complete_json(self, prompt, **kwargs):
            calls.append(prompt)
            result = next(results)
            if isinstance(result, Exception):
                raise result
            return result
    monkeypatch.setattr(llm_tool, "get_llm", lambda: Client())
    return calls


def run(material, **kwargs):
    candidate, bundle = material
    # 공개 저장을 검증하는 합성 테스트만 명시적으로 사람 검수 완료를 모의한다.
    kwargs.setdefault("human_reviewed", True)
    return ProblemAgent().run(ProblemInput(candidate=candidate, evidence_bundle=bundle, **kwargs))


def test_publish_roundtrip_preserves_counts_evidence_and_raw_metadata(material, monkeypatch):
    calls = fake_llm(monkeypatch, TEXT, {"decision": "publish", "reason": "자료에 나타난 불편과 일치합니다"})
    result = run(material)
    assert result.review.decision == "publish"
    assert len(calls) == 2
    assert result.generation_attempts == 1
    assert result.problem.case_count == 3
    assert result.problem.source_count == 3
    assert result.problem.signals.severity_counts == {"높음": 3}
    assert result.problem.evidence == material[1].evidence
    assert db_tool.get_problem(result.problem.id) == result.problem
    assert len(db_tool.list_problems()) == 1
    assert {r.id for r in db_tool.get_problem_raw_items(result.problem.id)} == set(material[0].raw_item_ids)
    assert all(e.source_url for e in result.problem.evidence)


def test_gate_hold_does_not_call_llm(material, monkeypatch):
    monkeypatch.setattr(settings, "PUBLISH_MIN_CASES", 20)
    candidate, _ = material
    bundle = EvidenceAgent().run(EvidenceInput(candidates=[candidate]))[0]
    calls = fake_llm(monkeypatch)
    result = run((candidate, bundle))
    assert result.review.decision == "hold"
    assert result.draft is None and result.problem is None
    assert not calls and db_tool.list_problems() == []


def test_opt_in_hold_preview_never_publishes(material, monkeypatch):
    monkeypatch.setattr(settings, "PUBLISH_MIN_CASES", 20)
    candidate, _ = material
    bundle = EvidenceAgent().run(EvidenceInput(candidates=[candidate]))[0]
    fake_llm(monkeypatch, TEXT, {"decision": "publish", "reason": "사례 내 상황과 일치합니다"})
    result = run((candidate, bundle), allow_hold_draft=True)
    assert result.review.decision == "hold"
    assert result.problem is not None and not result.problem.gate.passed
    assert result.problem.case_count == 3
    assert db_tool.list_problems() == []


@pytest.mark.parametrize("bad", [[], {}, {**TEXT, "case_count": 999}, {**TEXT, "title": 1},
                                 {**TEXT, "description": "관련 사례 137건이 확인됩니다"},
                                 {**TEXT, "complexity_note": "복잡도: 높음"},
                                 LLMError("invalid JSON")])
def test_invalid_generation_returns_hold_without_fake_problem(material, monkeypatch, bad):
    calls = fake_llm(monkeypatch, bad, bad)
    result = run(material)
    assert result.review.decision == "hold"
    assert result.problem is None and db_tool.list_problems() == []
    shape_error = (not isinstance(bad, Exception) and
                   (not isinstance(bad, dict) or set(bad) != set(TEXT)
                    or any(not isinstance(value, str) for value in bad.values())))
    assert len(calls) == (2 if shape_error else 1)
    assert result.generation_attempts == len(calls)


@pytest.mark.parametrize("bad", [
    {"problem": TEXT}, [TEXT], {}, {**TEXT, "title": ["중첩 제목"]},
    {**TEXT, "case_count": 999, "evidence": [{"summary": "위조된 근거"}]},
])
def test_generation_shape_repair_once_keeps_real_evidence(material, monkeypatch, bad):
    calls = fake_llm(monkeypatch, bad, TEXT, {"decision": "publish", "reason": "근거 일치"})
    result = run(material)
    assert len(calls) == 3 and result.generation_attempts == 2
    assert "이전 응답은 JSON 필드" in calls[1]
    assert "위조된 근거" not in calls[1]
    assert llm_tool.candidate_material(material[0]) in calls[1]
    assert result.review.decision == "publish"
    assert result.problem.case_count == 3
    assert result.problem.evidence == material[1].evidence


@pytest.mark.parametrize("second", [
    {**TEXT, "evidence": []},
    {**TEXT, "description": "관련 사례 137건이 확인됩니다"},
    {**TEXT, "complexity_note": "복잡도: 높음"},
    {**TEXT, "title": ""},
    LLMError("invalid JSON"),
])
def test_generation_repair_does_not_relax_validation_or_loop(material, monkeypatch, second):
    calls = fake_llm(monkeypatch, {"problem": TEXT}, second)
    result = run(material)
    assert len(calls) == 2 and result.generation_attempts == 2
    assert result.review.decision == "hold" and "생성 또는 검수 실패" in result.review.reason
    assert result.problem is None and db_tool.list_problems() == []


def test_repaired_generation_still_requires_source_review(material, monkeypatch):
    calls = fake_llm(monkeypatch, {}, TEXT, {"decision": "hold", "reason": "원문 근거 부족"})
    result = run(material)
    assert len(calls) == 3
    assert result.review.decision == "hold" and result.problem is None
    assert db_tool.list_problems() == []


@pytest.mark.parametrize("responses", [
    ({},), ({}, TEXT),
])
def test_generation_repair_budget_stop_propagates(material, monkeypatch, responses):
    from app.workers.collection_worker import CollectionBudgetReached
    calls = fake_llm(monkeypatch, *responses, CollectionBudgetReached("llm_budget"))
    with pytest.raises(CollectionBudgetReached):
        run(material)
    assert len(calls) == len(responses) + 1
    assert db_tool.list_problems() == []


def test_unsubstantiated_claim_is_held_by_review(material, monkeypatch):
    fake_llm(monkeypatch, TEXT, {"decision": "hold", "reason": "원문에서 공통 업무 상황이 충분히 확인되지 않습니다"})
    result = run(material)
    assert result.review.decision == "hold" and result.problem is None
    assert db_tool.list_problems() == []


def test_invalid_review_does_not_publish(material, monkeypatch):
    fake_llm(monkeypatch, TEXT, {"decision": "publish"})
    result = run(material)
    assert result.review.decision == "hold" and result.problem is None


def test_existing_id_is_not_overwritten(material, monkeypatch):
    fake_llm(monkeypatch, TEXT, {"decision": "publish", "reason": "근거 일치"},
             {**TEXT, "title": "변경된 합성 제목"}, {"decision": "publish", "reason": "근거 일치"})
    first = run(material).problem
    second = run(material)
    assert first is not None and second.review.decision == "hold"
    assert db_tool.get_problem(first.id) == first


def test_dry_run_cannot_publish(material, monkeypatch):
    monkeypatch.setattr(settings, "LLM_DRY_RUN", True)
    fake_llm(monkeypatch, TEXT, {"decision": "publish", "reason": "합성 검수"})
    result = run(material)
    assert result.review.decision == "hold" and db_tool.list_problems() == []


def test_forged_bundle_counts_fail_closed(material, monkeypatch):
    candidate, bundle = material
    bundle.signals.source_name_counts["없는 출처"] = 100
    fake_llm(monkeypatch, TEXT, {"decision": "publish", "reason": "근거 일치"})
    result = run((candidate, bundle))
    assert result.review.decision == "hold" and db_tool.list_problems() == []


def test_duplicate_raw_ids_cannot_inflate_counts(material):
    candidate, bundle = material
    candidate.raw_item_ids *= 2
    draft = ProblemDraft(**TEXT, evidence=bundle.evidence)
    problem = db_tool.compose_problem(draft, candidate.id, candidate.category, bundle=bundle, candidate=candidate)
    assert problem.case_count == 3


def test_store_corruption_is_visible(material, monkeypatch):
    fake_llm(monkeypatch, TEXT, {"decision": "publish", "reason": "근거 일치"})
    problem = run(material).problem
    path = settings.PROBLEMS_DIR / f"{problem.id}.json"
    path.write_text("{ broken", encoding="utf-8")
    with pytest.raises(db_tool.ProblemStoreError):
        db_tool.list_problems()


def test_path_traversal_is_rejected():
    with pytest.raises(db_tool.ProblemStoreError):
        db_tool.get_problem("../outside")


def test_locked_combine_stays_locked():
    with pytest.raises(NotImplementedError):
        ProblemAgent().run(ProblemInput(existing_problems=[]))


def test_material_contains_actual_raws_only(material):
    candidate, _ = material
    payload = json.loads(llm_tool.candidate_material(candidate))
    assert {i["id"] for i in payload["items"]} == set(candidate.raw_item_ids)
    assert "case_count" not in payload and "signals" not in payload


def test_forged_source_link_is_rejected(material, monkeypatch):
    candidate, bundle = material
    bundle.evidence[0].source_url = "https://unrelated.invalid/example"
    fake_llm(monkeypatch, TEXT, {"decision": "publish", "reason": "근거 일치"})
    result = run((candidate, bundle))
    assert result.review.decision == "hold" and db_tool.list_problems() == []


def test_unlicensed_excerpt_is_rejected(material, monkeypatch):
    candidate, bundle = material
    bundle.evidence[0].excerpt = "LLM이 만들어 낸 인용문"
    fake_llm(monkeypatch, TEXT, {"decision": "publish", "reason": "근거 일치"})
    result = run((candidate, bundle))
    assert result.review.decision == "hold" and db_tool.list_problems() == []


def test_publish_rejects_hold_even_with_passing_gate(material):
    candidate, bundle = material
    with pytest.raises(db_tool.ProblemStoreError):
        db_tool.publish_problem(
            ProblemDraft(**TEXT, evidence=bundle.evidence), candidate.id, candidate.category,
            bundle=bundle, candidate=candidate,
            review=ReviewResult(decision="hold", reason="불충분한 근거"),
        )
    assert db_tool.list_problems() == []


def test_same_title_requires_merge_review_without_llm(material, monkeypatch):
    fake_llm(monkeypatch, TEXT, {"decision": "publish", "reason": "근거 일치"})
    published = run(material).problem
    calls = fake_llm(monkeypatch)
    result = llm_tool.review_problem(ProblemDraft(**TEXT, evidence=material[1].evidence),
                                    [published], material="합성 데이터")
    assert result.decision == "merge" and result.merge_into_problem_id == published.id
    assert not calls


def test_model_hold_preview_remains_private(material, monkeypatch):
    fake_llm(monkeypatch, TEXT, {"decision": "hold", "reason": "공통 맥락 추가 검토 필요"})
    result = run(material, allow_hold_draft=True)
    assert result.review.decision == "hold" and result.problem is not None
    assert db_tool.list_problems() == []


@pytest.mark.parametrize("unsupported", ["업무 복귀 이후 회의록 정리가 귀찮다", "음성 내용을 옮기는 불편이 있다", "정리 과정에서 피로감이 발생한다"])
def test_source_metaphor_or_annoyance_does_not_license_extra_claims(monkeypatch, unsupported):
    source = json.dumps({"items": [{"title": "회의록 다시 담당", "text": "몇 년 만에 회의록 담당을 하게 됐는데 자막 텍스트 따는 것 같다. 귀찮다."}]}, ensure_ascii=False)
    calls = fake_llm(monkeypatch)
    draft = ProblemDraft(**{**TEXT, "description": unsupported}, evidence=[])
    review = llm_tool.review_problem(draft, [], material=source)
    assert review.decision == "hold" and not calls


def test_explicit_source_claim_is_sent_to_semantic_review(monkeypatch):
    source = json.dumps({"items": [{"title": "회의 기록", "text": "음성을 옮기는 과정에 피로를 느낀다"}]}, ensure_ascii=False)
    calls = fake_llm(monkeypatch, {"decision": "publish", "reason": "명시된 표현과 일치합니다"})
    draft = ProblemDraft(**{**TEXT, "description": "음성을 옮기는 과정에 피로가 언급된다"}, evidence=[])
    assert llm_tool.review_problem(draft, [], material=source).decision == "publish"
    assert len(calls) == 1



def test_ai_approval_without_human_review_stays_private(material, monkeypatch):
    fake_llm(monkeypatch, TEXT, {"decision": "publish", "reason": "원문 근거 일치"})
    candidate, bundle = material
    # 기본 입력에는 공개 승인 플래그가 없다.
    result = ProblemAgent().run(ProblemInput(candidate=candidate, evidence_bundle=bundle))
    assert result.review.decision == "hold" and "사람 검수 대기" in result.review.reason
    assert result.problem is not None and result.problem.gate.passed
    assert db_tool.list_problems() == []


def test_direct_publication_requires_human_approval(material):
    candidate, bundle = material
    with pytest.raises(db_tool.ProblemStoreError, match="사람 검수"):
        db_tool.publish_problem(
            ProblemDraft(**TEXT, evidence=bundle.evidence), candidate.id, candidate.category,
            bundle=bundle, candidate=candidate,
            review=ReviewResult(decision="publish", reason="원문 근거 일치"),
        )
    assert db_tool.list_problems() == []



def test_saved_record_retains_human_approval_and_rejects_missing_approval(material, monkeypatch):
    fake_llm(monkeypatch, TEXT, {"decision": "publish", "reason": "원문 근거 일치"})
    problem = run(material).problem
    path = settings.PROBLEMS_DIR / f"{problem.id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["human_reviewed"] is True
    assert payload["review"]["decision"] == "publish"
    del payload["human_reviewed"]
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(db_tool.ProblemStoreError):
        db_tool.get_problem(problem.id)
