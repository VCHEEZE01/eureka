"""
① 수집 에이전트 테스트.

★ search_tool 을 통째로 가짜로 바꿔 검사한다.
  에이전트가 tools 를 거쳐서만 바깥과 대화하기 때문에 이게 가능하다
  (app/agents/base.py 규칙 3). httpx 를 여기서 볼 일이 없어야 정상이다.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from app.agents.collector_agent import CollectInput, CollectorAgent
from app.config.dictionaries import (
    DICT_VERSION,
    DOMAIN_KEYWORDS,
    PAIN_SIGNALS_TIER1,
    PAIN_SIGNALS_TIER2,
)
from app.schemas.models import (
    Category,
    CollectMode,
    LicensePolicy,
    ProgressEvent,
    RawItem,
    SourceKind,
)
from app.tools import corpus_tool
from app.agents import collector_agent as agent_module
from app.tools.search_tool import QuotaExceeded, SearchError


# ══════════════════════════════════════════════
# 도우미
# ══════════════════════════════════════════════


def raw(n: int, keyword: str = "가계부 번거롭", kind: SourceKind = SourceKind.BLOG) -> RawItem:
    return RawItem(
        id=f"naver:{n:016d}",
        title=f"가계부가 번거롭다 {n}",
        snippet=f"매번 손으로 옮겨 적는다 {n}",
        url=f"https://blog.example/{n}",
        source_name="네이버 블로그",
        source_kind=kind,
        collected_at=datetime(2026, 9, 9, 3, 0, 0),
        query_keyword=keyword,
        content_hash=f"hash-{n:04d}",
    )


class FakeSearch:
    """search_tool 대역. 호출 기록을 남기고 정해진 응답을 돌려준다."""

    def __init__(self, per_call=None, error_at=None, quota_at=None):
        self.calls: list[tuple[str, SourceKind, int]] = []
        self.reset_calls = 0
        self._per_call = per_call
        self._error_at = error_at or {}
        self._quota_at = quota_at

    def reset_run_state(self) -> None:
        self.reset_calls += 1

    def search(self, keyword: str, source_kind: SourceKind, limit: int = 50):
        index = len(self.calls)
        self.calls.append((keyword, source_kind, limit))
        if self._quota_at is not None and index >= self._quota_at:
            raise QuotaExceeded("일일 한도 소진")
        if index in self._error_at:
            raise self._error_at[index]
        if self._per_call is None:
            return [raw(index, keyword, source_kind)]
        return list(self._per_call(index, keyword, source_kind))


@pytest.fixture
def fake(monkeypatch):
    """기본 대역을 꽂는다. 필요하면 테스트에서 install() 로 바꾼다."""

    def install(**kwargs) -> FakeSearch:
        stub = FakeSearch(**kwargs)
        monkeypatch.setattr(agent_module, "search_tool", stub)
        return stub

    return install


def collect_events() -> tuple[list[ProgressEvent], CollectorAgent]:
    events: list[ProgressEvent] = []
    return events, CollectorAgent(on_progress=events.append)


SMALL = dict(keyword_limit=2, source_kinds=[SourceKind.BLOG])


# ══════════════════════════════════════════════
# 1단계 — 검색어 조합
# ══════════════════════════════════════════════


def test_쿼리_수는_키워드_x_표현_x_소스_다():
    data = CollectInput(
        category=Category.FINANCE,
        source_kinds=[SourceKind.BLOG, SourceKind.NEWS],
        keyword_limit=3,
    )

    queries = CollectorAgent()._build_queries(data)

    assert len(queries) == 3 * len(PAIN_SIGNALS_TIER1) * 2


def test_keyword_limit_이_없으면_사전_전체를_돈다():
    data = CollectInput(category=Category.FINANCE, source_kinds=[SourceKind.BLOG])

    queries = CollectorAgent()._build_queries(data)

    assert len(queries) == len(DOMAIN_KEYWORDS[Category.FINANCE]) * len(PAIN_SIGNALS_TIER1)


def test_검색어는_도메인_키워드와_불편표현의_조합이다():
    data = CollectInput(category=Category.FINANCE, keyword_limit=1, **{
        "source_kinds": [SourceKind.BLOG]})

    queries = CollectorAgent()._build_queries(data)

    first_keyword = DOMAIN_KEYWORDS[Category.FINANCE][0]
    assert queries[0].keyword == f"{first_keyword} {PAIN_SIGNALS_TIER1[0]}"
    assert {q.keyword.split(" ", 1)[0] for q in queries} == {first_keyword}


def test_reason_에_사전_버전이_들어간다():
    data = CollectInput(category=Category.FINANCE, keyword_limit=1,
                        source_kinds=[SourceKind.BLOG])

    queries = CollectorAgent()._build_queries(data)

    assert all(f"사전 v{DICT_VERSION}" in q.reason for q in queries)
    assert "도메인" in queries[0].reason and "불편표현" in queries[0].reason


def test_카테고리와_소스가_쿼리에_그대로_박힌다():
    data = CollectInput(
        category=Category.EDUCATION_CAREER,
        source_kinds=[SourceKind.NEWS],
        keyword_limit=2,
    )

    queries = CollectorAgent()._build_queries(data)

    assert all(q.category is Category.EDUCATION_CAREER for q in queries)
    assert all(q.source_kind is SourceKind.NEWS for q in queries)


def test_signal_tier_all_이면_Tier2_가_더해진다():
    base = CollectInput(category=Category.FINANCE, keyword_limit=1,
                        source_kinds=[SourceKind.BLOG])
    wide = base.model_copy(update={"signal_tier": "all"})

    narrow_q = CollectorAgent()._build_queries(base)
    wide_q = CollectorAgent()._build_queries(wide)

    assert len(wide_q) == 2 * len(narrow_q)
    expressions = {q.keyword.split(" ", 1)[1] for q in wide_q}
    assert expressions & set(PAIN_SIGNALS_TIER2)


def test_week_rotation_이_다르면_Tier2_창이_달라진다():
    def exprs(rotation: int) -> set[str]:
        data = CollectInput(
            category=Category.FINANCE,
            source_kinds=[SourceKind.BLOG],
            keyword_limit=1,
            signal_tier="all",
            week_rotation=rotation,
        )
        return {q.keyword.split(" ", 1)[1] for q in CollectorAgent()._build_queries(data)}

    assert exprs(0) != exprs(1)
    # Tier1 은 매주 고정이다 — 주 단위 비교가 되려면 기준선이 흔들리면 안 된다
    assert set(PAIN_SIGNALS_TIER1) <= exprs(0)
    assert set(PAIN_SIGNALS_TIER1) <= exprs(1)


def test_예상_API_호출_수를_로그로_남긴다(caplog, isolated_settings):
    data = CollectInput(category=Category.FINANCE, keyword_limit=1,
                        source_kinds=[SourceKind.BLOG])

    with caplog.at_level("INFO"):
        CollectorAgent()._build_queries(data)

    expected = len(PAIN_SIGNALS_TIER1) * int(isolated_settings.COLLECT_MAX_PAGES)
    assert f"{expected}회" in caplog.text


# ══════════════════════════════════════════════
# 2단계 — 수집
# ══════════════════════════════════════════════


def test_쿼리마다_search_를_부른다(fake):
    stub = fake()
    data = CollectInput(category=Category.FINANCE, limit=1000, **SMALL)

    items = CollectorAgent().run(data)

    assert len(stub.calls) == 2 * len(PAIN_SIGNALS_TIER1)
    assert len(items) == len(stub.calls)


def test_per_query_limit_이_search_에_전달된다(fake):
    stub = fake()
    data = CollectInput(category=Category.FINANCE, per_query_limit=17, **SMALL)

    CollectorAgent().run(data)

    assert all(call[2] == 17 for call in stub.calls)


def test_per_query_limit_은_설정_상한을_넘지_못한다(fake, isolated_settings, monkeypatch):
    monkeypatch.setattr(isolated_settings, "COLLECT_PER_QUERY_LIMIT", 30)
    stub = fake()
    data = CollectInput(category=Category.FINANCE, per_query_limit=999, **SMALL)

    CollectorAgent().run(data)

    assert all(call[2] == 30 for call in stub.calls)


def test_쿼리_하나가_실패해도_배치는_계속된다(fake, caplog):
    stub = fake(error_at={0: SearchError("HTTP 500"), 3: SearchError("타임아웃")})
    data = CollectInput(category=Category.FINANCE, limit=1000, **SMALL)

    with caplog.at_level("WARNING"):
        items = CollectorAgent().run(data)

    total = 2 * len(PAIN_SIGNALS_TIER1)
    assert len(stub.calls) == total  # 전부 시도했다
    assert len(items) == total - 2  # 실패한 두 건만 빠졌다
    assert "다음 쿼리로" in caplog.text


def test_쿼터가_소진되면_그때까지_수집분으로_정상_종료한다(fake, caplog):
    stub = fake(quota_at=4)
    data = CollectInput(category=Category.FINANCE, limit=1000, **SMALL)

    with caplog.at_level("WARNING"):
        items = CollectorAgent().run(data)  # 예외가 올라오면 안 된다

    assert len(stub.calls) == 5  # 5번째에서 QuotaExceeded 를 만나고 멈췄다
    assert len(items) == 4
    assert "쿼터" in caplog.text


def test_첫_쿼리부터_쿼터가_소진되면_빈_목록으로_끝난다(fake):
    fake(quota_at=0)
    data = CollectInput(category=Category.FINANCE, **SMALL)

    assert CollectorAgent().run(data) == []


def test_실행마다_provider_차단_기록을_지운다(fake):
    stub = fake()
    data = CollectInput(category=Category.FINANCE, **SMALL)

    CollectorAgent().run(data)

    assert stub.reset_calls == 1


# ══════════════════════════════════════════════
# 3단계 — 중복 제거·저장·반환
# ══════════════════════════════════════════════


def test_같은_id_는_한_번만_남는다(fake):
    fake(per_call=lambda i, kw, sk: [raw(1, kw, sk), raw(1, kw, sk), raw(2, kw, sk)])
    data = CollectInput(category=Category.FINANCE, limit=1000, keyword_limit=1,
                        source_kinds=[SourceKind.BLOG])

    items = CollectorAgent().run(data)

    assert len(items) == 2
    assert {i.id for i in items} == {raw(1).id, raw(2).id}


def test_content_hash_가_같으면_버린다(fake):
    same = raw(9)
    twin = raw(10).model_copy(update={"content_hash": same.content_hash})
    fake(per_call=lambda i, kw, sk: [same, twin] if i == 0 else [])
    data = CollectInput(category=Category.FINANCE, limit=1000, keyword_limit=1,
                        source_kinds=[SourceKind.BLOG])

    items = CollectorAgent().run(data)

    assert [i.id for i in items] == [same.id]


def test_지난_배치에서_본_것은_다시_담지_않는다(fake):
    corpus_tool.save_raw_items([raw(1)], category=Category.FINANCE)
    fake(per_call=lambda i, kw, sk: [raw(1, kw, sk), raw(2, kw, sk)] if i == 0 else [])
    data = CollectInput(category=Category.FINANCE, limit=1000, keyword_limit=1,
                        source_kinds=[SourceKind.BLOG])

    items = CollectorAgent().run(data)

    assert [i.id for i in items] == [raw(2).id]


def test_collected_by_와_license_를_채운다(fake):
    fake()
    data = CollectInput(category=Category.FINANCE, mode=CollectMode.REALTIME, **SMALL)

    items = CollectorAgent().run(data)

    assert items
    assert all(i.collected_by is CollectMode.REALTIME for i in items)
    assert all(i.license is LicensePolicy.SUMMARY_ONLY for i in items)


def test_기본_모드는_배치다(fake):
    fake()
    data = CollectInput(category=Category.FINANCE, **SMALL)

    assert all(i.collected_by is CollectMode.BATCH for i in CollectorAgent().run(data))


def test_limit_까지만_돌려준다(fake):
    fake()
    data = CollectInput(category=Category.FINANCE, limit=3, **SMALL)

    assert len(CollectorAgent().run(data)) == 3


def test_코퍼스에_카테고리별로_저장된다(fake):
    fake()
    data = CollectInput(category=Category.HEALTHCARE, limit=3, keyword_limit=1,
                        source_kinds=[SourceKind.BLOG])

    CollectorAgent().run(data)

    saved = corpus_tool.load_raw_items(category=Category.HEALTHCARE)
    # limit 은 반환 개수일 뿐이다 — 수집한 것은 버리지 않는다
    assert len(saved) == len(PAIN_SIGNALS_TIER1)


def test_저장하면_seen_인덱스가_갱신되어_다음_배치가_건너뛴다(fake):
    fake()
    data = CollectInput(category=Category.FINANCE, limit=1000, **SMALL)
    first = CollectorAgent().run(data)
    assert first

    fake()  # 같은 결과를 다시 돌려주는 새 대역
    second = CollectorAgent().run(data)

    assert second == []


# ══════════════════════════════════════════════
# 진행 상태
# ══════════════════════════════════════════════


def test_report_가_단계_순서대로_불린다(fake):
    fake()
    events, agent = collect_events()

    agent.run(CollectInput(category=Category.FINANCE, **SMALL))

    assert [(e.index, e.done) for e in events] == [
        (0, False), (0, True), (1, False), (1, True), (2, False), (2, True)
    ]
    assert [e.step for e in events[::2]] == CollectorAgent.steps
    assert all(e.total == 3 for e in events)


def test_쿼터가_소진돼도_마지막_단계까지_보고한다(fake):
    fake(quota_at=1)
    events, agent = collect_events()

    agent.run(CollectInput(category=Category.FINANCE, **SMALL))

    assert [(e.index, e.done) for e in events][-1] == (2, True)


def test_진행_콜백이_없어도_돈다(fake):
    fake()

    assert CollectorAgent().run(CollectInput(category=Category.FINANCE, **SMALL))


# ══════════════════════════════════════════════
# 계약 — pipeline.py 가 쓰던 호출이 살아 있어야 한다
# ══════════════════════════════════════════════


def test_기존_호출_형태가_그대로_동작한다():
    data = CollectInput(category=Category.FINANCE, source_kinds=[SourceKind.BLOG])

    assert data.limit == 50
    assert data.mode is CollectMode.BATCH
    assert data.per_query_limit == 100
    assert data.keyword_limit is None
    assert data.signal_tier == "tier1"
    assert data.week_rotation == 0


def test_에이전트_이름과_단계가_고정이다():
    assert CollectorAgent.name == "수집 에이전트"
    assert CollectorAgent.steps == ["검색어 만들기", "원문 긁어오기", "정리"]
