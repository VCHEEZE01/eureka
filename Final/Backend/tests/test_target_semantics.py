"""Grounding regressions derived from real mixed-person/Q&A pilot failures. No API calls."""
import pytest

from app.agents.interpreter_agent import InterpreterAgent
from app.schemas.collections import TargetProfile
from app.schemas.models import Category, Judgement
from app.tools import corpus_tool, llm_tool, target_evidence_tool, text_tool


def target(**changes):
    values = dict(age="30대", gender="여성", jobs=["마케터"], places=["회사"])
    values.update(changes)
    return TargetProfile(**values)


def judgement(item, profile, **changes):
    quote = item.snippet
    row = dict(id=item.id, is_pain=True, pain_status="pain", pain_summary="자료를 여러 곳에 따로 옮기느라 업무 마감이 늦어지는 어려움",
               confidence="높음", severity="중간", experience_type="self", experience_evidence=quote,
               sufferer_gender="여자", sufferer_age_band="30대",
               target_values={"age":"30대", "gender":"여성", "jobs":"마케터", "places":"회사"},
               target_evidence={field:quote for field in ["age","gender","jobs","places"]},
               target_field_status={field:"confirmed" for field in ["age","gender","jobs","places"]})
    row.update(changes)
    return llm_tool._to_judgement(row, item, target_profile=profile)


def test_all_fields_must_describe_one_grounded_experience(make_raw_item):
    item=make_raw_item(snippet="저는 30대 여성 마케터이고 회사에서 자료를 시트별로 옮겨 적다가 마감 시각을 넘겼습니다.")
    j=judgement(item,target())
    assert j.is_pain and j.target_status == "confirmed"
    assert set(j.target_evidence)=={"age","gender","jobs","places"}
    assert j.target_profile_key == target_evidence_tool.profile_key(target())


def test_invented_or_wrong_person_attribute_quote_does_not_confirm(make_raw_item):
    item=make_raw_item(snippet="저는 20대이고 남자친구는 30대 남자입니다. 회사 자료를 옮기다 마감 시각을 넘겼습니다.")
    j=judgement(item,target(age="30대",gender="남성"))
    assert j.target_status == "unconfirmed"
    assert j.sufferer_gender is None and j.sufferer_age_band is None
    quotes={"age":"저는 30대이고", "gender":"저는 남성입니다"}
    assert judgement(item,target(),target_evidence=quotes).target_status=="unconfirmed"


def test_explicit_self_conflict_is_distinct_from_unknown(make_raw_item):
    item=make_raw_item(snippet="저는 20대 남자이고 회사에서 자료를 시트별로 옮기다 마감 시간을 넘겼습니다.")
    j=judgement(item,target(age="30대",gender="남성",jobs=[]),target_values={"age":"20대","gender":"남자","places":"회사"})
    assert j.target_status == "conflict" and j.target_field_status["age"]=="conflict"
    assert j.target_field_status["gender"]=="confirmed"


def test_boyfriend_or_nurse_does_not_imply_gender(make_raw_item):
    for quote in ["저는 20대 후반이고 오빠는 30대 직장인입니다. 남자친구가 배가 아프대서 걱정입니다.",
                  "저는 간호사이고 회사 서류를 여러 곳에 옮겨 적다가 마감 시간을 넘겼습니다."]:
        item=make_raw_item(snippet=quote)
        assert judgement(item,target()).sufferer_gender is None


def test_q_and_a_mixture_is_insufficient_not_no_pain(make_raw_item):
    item=make_raw_item(url="https://kin.naver.com/qna/detail.naver?docId=490674367&answerNo=1",snippet="저는 20대 남자인데 집에서 계속 입력하다 마감 시간을 넘겼습니다. 안녕하세요. 하이닥 상담의입니다.")
    j=judgement(item,target(age="20대",gender="남성",jobs=[],places=[]))
    assert j.experience_type == "mixed" and j.pain_status == "insufficient"
    assert not j.is_pain and j.target_status=="unconfirmed"
    assert j.sufferer_gender is None


def test_real_pain_with_missing_target_stays_pain_but_does_not_confirm(make_raw_item):
    item=make_raw_item(snippet="저는 회사에서 자료를 시트별로 옮겨 적다가 마감 시간을 넘겨 상사에게 설명해야 했습니다.")
    j=judgement(item,target(),target_evidence={},target_values={})
    assert j.is_pain and j.pain_status=="pain" and j.target_status=="unconfirmed"


def test_explicit_not_pain_and_insufficient_are_different(make_raw_item):
    item=make_raw_item(snippet="저는 30대 여성이고 회사에서 자료를 시트별로 옮겨 적었습니다. 그 뒤에는...")
    assert judgement(item,target(),pain_status="insufficient",is_pain=False).pain_status=="insufficient"
    assert judgement(item,target(),pain_status="not_pain",is_pain=False).pain_status=="not_pain"


def test_semantic_path_admits_keyword_free_items_but_keeps_rule_only_behavior(make_raw_item):
    item=make_raw_item(title="업무 기록",snippet="회계 자료를 시트별로 복사한 뒤 셀을 대조하다 퇴근 시각을 넘겼다는 이야기를 남깁니다.")
    assert text_tool.signal_hits(text_tool.item_text(item))=={}
    assert InterpreterAgent._rule_filter([item])[0]==[]
    assert InterpreterAgent._rule_filter([item],allow_semantic=True)[0]==[item]


def test_pending_requires_same_target_and_policy(monkeypatch,make_raw_item):
    items=[make_raw_item(id=f"raw-{i}") for i in range(3)]
    good=Judgement(raw_item_id=items[0].id,is_pain=True,pain_summary="동일한 자료를 따로 옮기느라 마감이 지연됨",confidence="높음",target_status="confirmed",target_profile_key=target_evidence_tool.profile_key(target()),target_policy="evidence_v2")
    other=good.model_copy(update={"raw_item_id":items[1].id,"target_profile_key":"different"})
    old=good.model_copy(update={"raw_item_id":items[2].id,"target_policy":None})
    monkeypatch.setattr(corpus_tool,"recent_weeks",lambda *args:["2026-W37"])
    monkeypatch.setattr(corpus_tool,"load_judgements",lambda **kwargs:[good,other,old])
    agent=InterpreterAgent()
    monkeypatch.setattr(agent,"_recent_raw_map",lambda category:{i.id:i for i in items})
    pool=[]
    _,count=agent._merge_pending(pool,{},Category.IT_PRODUCTIVITY,target_profile=target())
    assert count==1 and pool==[good]

@pytest.mark.parametrize("quote", ["저는 20대 남성을 봤어요", "저는 20대 남자분을 만났는데요", "저는 20대 남성 고객을 도와드리는 마케터인데 자료를 옮깁니다", "제 친구는 20대 남자인데 저는 자료를 옮겨 적었습니다"])
def test_other_person_object_is_not_self_attribute(quote):
    assert not target_evidence_tool.self_attribute("20대",quote,"age")
    assert not target_evidence_tool.self_attribute("남자",quote,"gender")

@pytest.mark.parametrize("quote, band", [("저는 23살입니다", "20대"), ("저는 60대입니다", "50대 이상"), ("23살 남자인데 회사 기록을 옮깁니다", "20대"), ("제 나이는 23살", "20대")])
def test_numeric_age_self_introduction_is_normalized(quote,band):
    assert target_evidence_tool.self_attribute(band,quote,"age")

@pytest.mark.parametrize("wanted,actual",[("의사","수의사"),("집","편집실")])
def test_partial_job_place_words_do_not_confirm(make_raw_item,wanted,actual):
    field="jobs" if wanted=="의사" else "places"
    quote=f"저는 30대 여성이고 {actual}{'인데' if field=='jobs' else '에서'} 자료를 시트별로 옮기다 마감 시간을 넘겼습니다."
    item=make_raw_item(snippet=quote)
    profile=target(**{field:[wanted]})
    j=judgement(item,profile,target_values={field:wanted},target_evidence={field:quote})
    assert j.target_field_status[field]=="unconfirmed"


def test_clear_advertisement_is_not_pain_even_without_self_target_quote(make_raw_item):
    item=make_raw_item(snippet="추천 제품을 안내하고 구매를 권하는 정보입니다. 지금 상품을 신청해보세요.")
    j=judgement(item,target(),is_pain=False,pain_status="not_pain",experience_type="other",experience_evidence=None)
    assert j.pain_status=="not_pain" and j.target_status=="unconfirmed"


def test_malformed_semantic_fields_fail_closed_without_throwing(make_raw_item):
    item=make_raw_item(snippet="저는 30대 여성이고 회사에서 자료를 시트별로 옮기다 마감 시간을 넘겼습니다.")
    j=judgement(item,target(),experience_type=[],pain_status={},target_values=[],target_evidence=[])
    assert j.pain_status=="insufficient" and j.target_status=="unconfirmed"
