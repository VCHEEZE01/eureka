"""운영 검색이 초기 소수 주제/모든 속성 AND에 다시 갇히지 않도록 검증한다."""
from app.config.dictionaries import DOMAIN_KEYWORDS, SEARCH_PAIN_INTENTS
from app.schemas.collections import TargetProfile
from app.schemas.models import Category
from app.tools.target_query_tool import CONTEXT_INTENT, build_target_queries, catalog_size, iter_query_catalog, topic_catalog


def test_first_round_covers_intents_sources_and_broad_marketer_context():
    target = TargetProfile(age="20대", gender="남성", jobs=["마케터"], places=["회사"])
    queries = build_target_queries(target, budget=40)
    assert {q.intent for q in queries} == set(SEARCH_PAIN_INTENTS) | {CONTEXT_INTENT}
    assert {q.category for q in queries} == set(Category)
    assert len({q.topic_id for q in queries}) == 40
    assert {q.endpoint for q in queries} >= {"news", "kin", "cafearticle", "blog"}
    assert any("20대" not in q.keyword and "남성" not in q.keyword for q in queries)
    assert any("광고 성과" in q.keyword for q in queries)
    topics = {topic for _, topic, _ in topic_catalog(target)}
    assert "회의실 예약" in topics
    assert all(topic in topics for values in DOMAIN_KEYWORDS.values() for topic in values)


def test_age_gender_only_search_also_separates_retrieval_anchors():
    queries = build_target_queries(TargetProfile(age="20대", gender="남성"), budget=40)
    assert any("20대" in q.keyword and "남성" not in q.keyword for q in queries)
    assert any("남성" in q.keyword and "20대" not in q.keyword for q in queries)


def test_catalog_exact_size_unique_requests_and_continuation():
    target = TargetProfile(jobs=["마케터"], places=["회사"])
    catalog = list(iter_query_catalog(target))
    assert len(catalog) == catalog_size(target) == len({q.id for q in catalog})
    assert len({(q.keyword, q.provider, q.endpoint) for q in catalog}) == len(catalog)
    first = build_target_queries(target, budget=40)
    second = build_target_queries(target, completed_ids=[q.id for q in first], budget=40)
    assert not {q.id for q in first} & {q.id for q in second}
    assert build_target_queries(target, completed_ids=[q.id for q in catalog], budget=40) == []


def test_fifty_plus_range_is_available_from_first_round():
    queries = build_target_queries(TargetProfile(age="50대 이상", gender="여성"), budget=40)
    assert any("60대" in q.keyword for q in queries)
    assert any("70대" in q.keyword for q in queries)


def test_unknown_job_retains_all_base_topics_and_its_search_anchor():
    target = TargetProfile(jobs=["로봇 조련사"], places=["창고"])
    topics = {topic for _, topic, _ in topic_catalog(target)}
    assert all(topic in topics for values in DOMAIN_KEYWORDS.values() for topic in values)
    assert any("로봇 조련사" in q.keyword for q in build_target_queries(target, budget=40))


def test_first_large_search_visits_all_base_topics_and_includes_neutral_queries():
    target = TargetProfile(age="20대", gender="남성")
    queries = build_target_queries(target, budget=120)
    assert {q.topic for q in queries} == {t for topics in DOMAIN_KEYWORDS.values() for t in topics}
    neutral = [q for q in queries if q.intent == CONTEXT_INTENT]
    assert neutral
    assert all(not any(phrase in q.keyword for phrases in SEARCH_PAIN_INTENTS.values() for phrase in phrases) for q in neutral)
    assert all(q.keyword == q.keyword.strip() for q in queries)
