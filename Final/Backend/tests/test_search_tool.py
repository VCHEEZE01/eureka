"""
search_tool 테스트.

★ 진짜 API를 부르지 않는다. respx 로 httpx 를 목킹한다.
  conftest 의 no_network fixture 가 httpcore 를 막아 두었으므로,
  목킹을 빠뜨리면 그 자리에서 NetworkBlockedError 로 실패한다.

응답 형식은 공식 문서 그대로다.
  · 네이버  https://naverapihub.apigw.ntruss.com/search/v1/{blog|news|kin|cafearticle}
            items[] {title, link, description, (postdate|pubDate|cafename|originallink)}
  · 카카오  https://dapi.kakao.com/v2/search/{web|blog}
            meta{is_end} + documents[] {title, contents, url, datetime}
"""

from __future__ import annotations

import json
from datetime import date

import httpx
import pytest
import respx

from app.schemas.models import SourceKind
from app.tools import search_tool
from app.tools.search_tool import QuotaExceeded, SearchError

NAVER_BLOG_URL = "https://naverapihub.apigw.ntruss.com/search/v1/blog"
NAVER_NEWS_URL = "https://naverapihub.apigw.ntruss.com/search/v1/news"
NAVER_KIN_URL = "https://naverapihub.apigw.ntruss.com/search/v1/kin"
NAVER_CAFE_URL = "https://naverapihub.apigw.ntruss.com/search/v1/cafearticle"
KAKAO_BLOG_URL = "https://dapi.kakao.com/v2/search/blog"
KAKAO_WEB_URL = "https://dapi.kakao.com/v2/search/web"


# ══════════════════════════════════════════════
# 공통 준비
# ══════════════════════════════════════════════


@pytest.fixture(autouse=True)
def _keys_and_clean_state(isolated_settings, monkeypatch):
    """키를 채우고, 실행 단위 상태와 백오프 대기를 초기화한다."""
    monkeypatch.setattr(isolated_settings, "NAVER_CLIENT_ID", "test-id")
    monkeypatch.setattr(isolated_settings, "NAVER_CLIENT_SECRET", "test-secret")
    monkeypatch.setattr(isolated_settings, "KAKAO_REST_API_KEY", "test-kakao")
    monkeypatch.setattr(search_tool, "_sleep", lambda _s: None)
    search_tool.reset_run_state()
    yield
    search_tool.reset_run_state()


def naver_body(items: list[dict]) -> dict:
    return {"lastBuildDate": "Tue, 09 Sep 2026 03:00:00 +0900",
            "total": len(items), "start": 1, "display": len(items), "items": items}


def kakao_body(docs: list[dict], is_end: bool = True) -> dict:
    return {
        "meta": {"total_count": len(docs), "pageable_count": len(docs), "is_end": is_end},
        "documents": docs,
    }


def blog_item(n: int = 1, **over) -> dict:
    row = {
        "title": f"가계부 정리가 <b>번거롭</b>다 {n}",
        "link": f"https://blog.naver.com/user/{n}",
        "description": f"매번 카드 명세서를 손으로 옮겨 적는 게 <b>번거롭</b>네요 {n}",
        "bloggername": "테스터",
        "bloggerlink": "https://blog.naver.com/user",
        "postdate": "20260901",
    }
    row.update(over)
    return row


def kakao_doc(n: int = 1, **over) -> dict:
    row = {
        "title": f"<b>가계부</b> 앱 후기 {n}",
        "contents": f"입력이 <b>귀찮</b>아서 오래 못 씁니다 {n}",
        "url": f"https://tistory.example/{n}",
        "datetime": "2026-09-01T12:00:00.000+09:00",
    }
    row.update(over)
    return row


def only_naver_blog():
    """BLOG 매핑에서 네이버 블로그만 남긴다. 한 엔드포인트를 좁혀 볼 때 쓴다."""
    return {SourceKind.BLOG: (search_tool._NAVER_BLOG,)}


@respx.mock
def test_target_search_respects_configured_count_above_ten():
    route = respx.get(NAVER_BLOG_URL).mock(return_value=httpx.Response(
        200, json=naver_body([blog_item(i) for i in range(25)])))
    result = search_tool.search_endpoint("보고서 수작업", SourceKind.BLOG, "naver", "blog", limit=25)
    assert result.succeeded and len(result.items) == 25
    assert len(route.calls) == 1
    assert route.calls[0].request.url.params["display"] == "25"


@respx.mock
def test_target_search_clips_to_provider_page_limit():
    route = respx.get(KAKAO_BLOG_URL).mock(return_value=httpx.Response(
        200, json=kakao_body([kakao_doc(i) for i in range(50)])))
    result = search_tool.search_endpoint("보고서 수작업", SourceKind.BLOG, "kakao", "blog", limit=100)
    assert result.succeeded and len(result.items) == 50
    assert len(route.calls) == 1
    assert route.calls[0].request.url.params["size"] == "50"


# ══════════════════════════════════════════════
# 응답 → RawItem 매핑
# ══════════════════════════════════════════════


@respx.mock
def test_네이버_블로그_응답이_RawItem_으로_매핑된다(monkeypatch):
    monkeypatch.setattr(search_tool, "ENDPOINTS", only_naver_blog())
    respx.get(NAVER_BLOG_URL).mock(
        return_value=httpx.Response(200, json=naver_body([blog_item(1)]))
    )

    items = search_tool.search("가계부 번거롭", SourceKind.BLOG, limit=10)

    assert len(items) == 1
    item = items[0]
    assert item.id.startswith("naver:")
    assert item.url == "https://blog.naver.com/user/1"
    assert item.source_name == "네이버 블로그"
    assert item.source_kind is SourceKind.BLOG
    assert item.query_keyword == "가계부 번거롭"
    assert item.posted_at == date(2026, 9, 1)
    assert item.content_hash


@respx.mock
def test_b_하이라이트_태그가_제거된다(monkeypatch):
    monkeypatch.setattr(search_tool, "ENDPOINTS", only_naver_blog())
    respx.get(NAVER_BLOG_URL).mock(
        return_value=httpx.Response(200, json=naver_body([blog_item(1)]))
    )

    item = search_tool.search("가계부 번거롭", SourceKind.BLOG, limit=10)[0]

    assert "<b>" not in item.title and "</b>" not in item.title
    assert "<b>" not in item.snippet and "</b>" not in item.snippet
    assert "번거롭다" in item.title  # 태그가 단어를 쪼개지 않았다


@respx.mock
def test_HTML_엔티티와_개인정보가_정제된다(monkeypatch):
    monkeypatch.setattr(search_tool, "ENDPOINTS", only_naver_blog())
    row = blog_item(1, title="정산 &amp; 청구", description="문의는 hong@example.com 으로")
    respx.get(NAVER_BLOG_URL).mock(
        return_value=httpx.Response(200, json=naver_body([row]))
    )

    item = search_tool.search("가계부 번거롭", SourceKind.BLOG, limit=10)[0]

    assert item.title == "정산 & 청구"
    assert "@" not in item.snippet


@respx.mock
def test_뉴스는_originallink_와_pubDate_를_쓴다(monkeypatch):
    respx.get(NAVER_NEWS_URL).mock(
        return_value=httpx.Response(
            200,
            json=naver_body([{
                "title": "가계부 앱 이용 확산",
                "originallink": "https://news.example/article/1",
                "link": "https://n.news.naver.com/1",
                "description": "설명",
                "pubDate": "Mon, 01 Sep 2026 07:50:00 +0900",
            }]),
        )
    )

    item = search_tool.search("가계부", SourceKind.NEWS, limit=5)[0]

    assert item.url == "https://news.example/article/1"
    assert item.posted_at == date(2026, 9, 1)
    assert item.source_name == "네이버 뉴스"


@respx.mock
def test_지식iN_과_카페는_날짜가_없어_None_이다():
    respx.get(NAVER_KIN_URL).mock(
        return_value=httpx.Response(200, json=naver_body([
            {"title": "가계부 어떻게 쓰나요", "link": "https://kin.naver.com/1",
             "description": "방법 없나요"}]))
    )
    respx.get(NAVER_CAFE_URL).mock(
        return_value=httpx.Response(200, json=naver_body([
            {"title": "가계부 공유", "link": "https://cafe.naver.com/x/1",
             "description": "매번 귀찮아요", "cafename": "재테크 카페",
             "cafeurl": "https://cafe.naver.com/x"}]))
    )

    items = search_tool.search("가계부", SourceKind.COMMUNITY, limit=10)

    assert len(items) == 2
    assert all(i.posted_at is None for i in items)
    assert {i.source_name for i in items} == {"네이버 지식iN", "네이버 카페"}


@respx.mock
def test_깨진_날짜는_예외가_아니라_None_이다(monkeypatch):
    monkeypatch.setattr(search_tool, "ENDPOINTS", only_naver_blog())
    respx.get(NAVER_BLOG_URL).mock(
        return_value=httpx.Response(
            200, json=naver_body([blog_item(1, postdate="이건 날짜가 아니다")])
        )
    )

    assert search_tool.search("가계부", SourceKind.BLOG, limit=5)[0].posted_at is None


@respx.mock
def test_카카오_응답도_같은_RawItem_으로_매핑된다(monkeypatch):
    monkeypatch.setattr(
        search_tool, "ENDPOINTS", {SourceKind.BLOG: (search_tool._KAKAO_BLOG,)}
    )
    route = respx.get(KAKAO_BLOG_URL).mock(
        return_value=httpx.Response(200, json=kakao_body([kakao_doc(1)]))
    )

    item = search_tool.search("가계부 귀찮", SourceKind.BLOG, limit=5)[0]

    assert item.id.startswith("kakao:")
    assert item.source_name == "다음 블로그"
    assert item.posted_at == date(2026, 9, 1)
    assert route.calls[0].request.headers["Authorization"] == "KakaoAK test-kakao"


# ══════════════════════════════════════════════
# 요청 파라미터 — 공식 문서 계약
# ══════════════════════════════════════════════


@respx.mock
def test_네이버_인증헤더와_최신순_정렬을_보낸다(monkeypatch):
    monkeypatch.setattr(search_tool, "ENDPOINTS", only_naver_blog())
    route = respx.get(NAVER_BLOG_URL).mock(
        return_value=httpx.Response(200, json=naver_body([blog_item(1)]))
    )

    search_tool.search("가계부 번거롭", SourceKind.BLOG, limit=10)

    request = route.calls[0].request
    assert request.headers["X-NCP-APIGW-API-KEY-ID"] == "test-id"
    assert request.headers["X-NCP-APIGW-API-KEY"] == "test-secret"
    assert "X-Naver-Client-Id" not in request.headers
    assert "X-Naver-Client-Secret" not in request.headers
    assert request.url.params["format"] == "json"
    assert request.url.params["sort"] == "date"  # 최신순 — 반복 수집 방지
    assert request.url.params["start"] == "1"


@pytest.mark.parametrize("endpoint,url", [
    (search_tool._NAVER_BLOG, NAVER_BLOG_URL),
    (search_tool._NAVER_NEWS, NAVER_NEWS_URL),
    (search_tool._NAVER_KIN, NAVER_KIN_URL),
    (search_tool._NAVER_CAFE, NAVER_CAFE_URL),
])
@respx.mock
def test_API_Hub_전체_검색_경로와_인증_계약(endpoint, url):
    route = respx.get(url).mock(return_value=httpx.Response(200, json=naver_body([])))

    assert search_tool._fetch_endpoint("가계부", SourceKind.BLOG, endpoint, 1) == []

    request = route.calls[0].request
    assert request.headers["X-NCP-APIGW-API-KEY-ID"] == "test-id"
    assert request.headers["X-NCP-APIGW-API-KEY"] == "test-secret"
    assert request.url.params["format"] == "json"
    assert request.url.params["display"] == "1"


@respx.mock
def test_카카오는_recency_정렬을_보낸다(monkeypatch):
    monkeypatch.setattr(
        search_tool, "ENDPOINTS", {SourceKind.BLOG: (search_tool._KAKAO_BLOG,)}
    )
    route = respx.get(KAKAO_BLOG_URL).mock(
        return_value=httpx.Response(200, json=kakao_body([kakao_doc(1)]))
    )

    search_tool.search("가계부", SourceKind.BLOG, limit=5)

    assert route.calls[0].request.url.params["sort"] == "recency"


@respx.mock
def test_display_는_문서상_상한_100_을_넘지_않는다(monkeypatch):
    monkeypatch.setattr(search_tool, "ENDPOINTS", only_naver_blog())
    route = respx.get(NAVER_BLOG_URL).mock(
        return_value=httpx.Response(
            200, json=naver_body([blog_item(i) for i in range(100)])
        )
    )

    search_tool.search("가계부", SourceKind.BLOG, limit=500)

    for call in route.calls:
        assert int(call.request.url.params["display"]) <= search_tool.NAVER_MAX_DISPLAY


# ══════════════════════════════════════════════
# URL 정규화와 id
# ══════════════════════════════════════════════


def test_트래킹_쿼리와_스킴이_달라도_같은_id_가_나온다():
    a = "http://Blog.Naver.com/user/1?utm_source=x&utm_medium=y#top"
    b = "https://blog.naver.com/user/1?ref=abc"
    c = "https://blog.naver.com/user/1?from=search"

    assert search_tool.make_item_id("naver", a) == search_tool.make_item_id("naver", b)
    assert search_tool.make_item_id("naver", b) == search_tool.make_item_id("naver", c)


def test_의미_있는_쿼리는_유지되어_다른_글은_다른_id_다():
    a = "https://cafe.naver.com/x?articleid=1"
    b = "https://cafe.naver.com/x?articleid=2"

    assert search_tool.make_item_id("naver", a) != search_tool.make_item_id("naver", b)


def test_같은_url_이라도_provider_가_다르면_id_가_다르다():
    url = "https://example.test/1"

    assert search_tool.make_item_id("naver", url) != search_tool.make_item_id("kakao", url)


@respx.mock
def test_다른_검색어로_같은_글이_걸려도_id_가_같다(monkeypatch):
    monkeypatch.setattr(search_tool, "ENDPOINTS", only_naver_blog())
    respx.get(NAVER_BLOG_URL).mock(
        side_effect=[
            httpx.Response(200, json=naver_body([
                blog_item(1, link="https://blog.naver.com/user/1?utm_source=a")])),
            httpx.Response(200, json=naver_body([
                blog_item(1, link="http://Blog.naver.com/user/1?ref=b")])),
        ]
    )

    first = search_tool.search("가계부 번거롭", SourceKind.BLOG, limit=5)[0]
    second = search_tool.search("가계부 매번", SourceKind.BLOG, limit=5)[0]

    assert first.id == second.id


@respx.mock
def test_한_응답_안의_중복_url_은_한_번만_담긴다(monkeypatch):
    monkeypatch.setattr(search_tool, "ENDPOINTS", only_naver_blog())
    respx.get(NAVER_BLOG_URL).mock(
        return_value=httpx.Response(200, json=naver_body([
            blog_item(1, link="https://blog.naver.com/user/1"),
            blog_item(2, link="https://blog.naver.com/user/1?utm_source=z"),
        ]))
    )

    assert len(search_tool.search("가계부", SourceKind.BLOG, limit=10)) == 1


# ══════════════════════════════════════════════
# limit · 페이지네이션
# ══════════════════════════════════════════════


@respx.mock
def test_limit_을_넘겨_돌려주지_않는다(monkeypatch):
    monkeypatch.setattr(search_tool, "ENDPOINTS", only_naver_blog())
    respx.get(NAVER_BLOG_URL).mock(
        return_value=httpx.Response(
            200, json=naver_body([blog_item(i) for i in range(50)])
        )
    )

    assert len(search_tool.search("가계부", SourceKind.BLOG, limit=7)) == 7


def _full_page(request: httpx.Request) -> httpx.Response:
    """요청한 display 만큼, 페이지마다 다른 글을 채워 돌려준다."""
    start = int(request.url.params["start"])
    display = int(request.url.params["display"])
    return httpx.Response(
        200, json=naver_body([blog_item(start + i) for i in range(display)])
    )


@respx.mock
def test_페이지를_넘기며_start_가_증가한다(monkeypatch, isolated_settings):
    monkeypatch.setattr(search_tool, "ENDPOINTS", only_naver_blog())
    monkeypatch.setattr(isolated_settings, "COLLECT_MAX_PAGES", 3)
    route = respx.get(NAVER_BLOG_URL).mock(side_effect=_full_page)

    # 한 페이지 상한(100)보다 많이 달라고 해야 페이지를 넘긴다
    items = search_tool.search("가계부", SourceKind.BLOG, limit=250)

    assert len(route.calls) == 3
    assert [c.request.url.params["start"] for c in route.calls] == ["1", "101", "201"]
    # 페이지마다 다른 글이므로 중복 없이 쌓이고, limit 에서 잘린다
    assert len(items) == 250


@respx.mock
def test_COLLECT_MAX_PAGES_를_넘겨_부르지_않는다(monkeypatch, isolated_settings):
    monkeypatch.setattr(search_tool, "ENDPOINTS", only_naver_blog())
    monkeypatch.setattr(isolated_settings, "COLLECT_MAX_PAGES", 2)
    route = respx.get(NAVER_BLOG_URL).mock(side_effect=_full_page)

    search_tool.search("가계부", SourceKind.BLOG, limit=1000)

    assert len(route.calls) == 2


@respx.mock
def test_결과가_페이지보다_적으면_다음_페이지를_부르지_않는다(monkeypatch):
    monkeypatch.setattr(search_tool, "ENDPOINTS", only_naver_blog())
    route = respx.get(NAVER_BLOG_URL).mock(
        return_value=httpx.Response(200, json=naver_body([blog_item(1)]))
    )

    search_tool.search("가계부", SourceKind.BLOG, limit=100)

    assert len(route.calls) == 1


@respx.mock
def test_카카오는_is_end_에서_멈춘다(monkeypatch, isolated_settings):
    monkeypatch.setattr(
        search_tool, "ENDPOINTS", {SourceKind.BLOG: (search_tool._KAKAO_BLOG,)}
    )
    monkeypatch.setattr(isolated_settings, "COLLECT_MAX_PAGES", 3)
    route = respx.get(KAKAO_BLOG_URL).mock(
        side_effect=[
            httpx.Response(200, json=kakao_body(
                [kakao_doc(i) for i in range(10)], is_end=False)),
            httpx.Response(200, json=kakao_body(
                [kakao_doc(i) for i in range(10, 20)], is_end=True)),
        ]
    )

    search_tool.search("가계부", SourceKind.BLOG, limit=100)

    assert len(route.calls) == 2
    assert [c.request.url.params["page"] for c in route.calls] == ["1", "2"]


@respx.mock
def test_블로그는_네이버와_카카오_양쪽에서_고르게_가져온다():
    respx.get(NAVER_BLOG_URL).mock(
        return_value=httpx.Response(200, json=naver_body(
            [blog_item(i) for i in range(10)]))
    )
    respx.get(KAKAO_BLOG_URL).mock(
        return_value=httpx.Response(200, json=kakao_body(
            [kakao_doc(100 + i) for i in range(10)]))
    )
    respx.get(KAKAO_WEB_URL).mock(
        return_value=httpx.Response(200, json=kakao_body(
            [kakao_doc(200 + i, url=f"https://web.example/{i}") for i in range(10)]))
    )

    items = search_tool.search("가계부", SourceKind.BLOG, limit=9)

    assert len(items) == 9
    # 한 곳에서만 나온 근거는 "세상의 문제"가 아니다 — 출처가 섞여야 한다
    assert len({i.source_name for i in items}) == 3


# ══════════════════════════════════════════════
# 재시도 · 실패 · 차단
# ══════════════════════════════════════════════


@respx.mock
def test_429_는_백오프하고_재시도한다(monkeypatch):
    monkeypatch.setattr(search_tool, "ENDPOINTS", only_naver_blog())
    waited: list[float] = []
    monkeypatch.setattr(search_tool, "_sleep", waited.append)
    route = respx.get(NAVER_BLOG_URL).mock(
        side_effect=[
            httpx.Response(429, json={"errorCode": "012"}),
            httpx.Response(429, json={"errorCode": "012"}),
            httpx.Response(200, json=naver_body([blog_item(1)])),
        ]
    )

    items = search_tool.search("가계부", SourceKind.BLOG, limit=5)

    assert len(items) == 1
    assert len(route.calls) == 3
    assert waited == [1.0, 2.0]  # 지수 백오프


@respx.mock
def test_5xx_도_재시도하고_끝내_실패하면_SearchError(monkeypatch):
    monkeypatch.setattr(search_tool, "ENDPOINTS", only_naver_blog())
    route = respx.get(NAVER_BLOG_URL).mock(return_value=httpx.Response(503))

    items = search_tool.search("가계부", SourceKind.BLOG, limit=5)

    # 엔드포인트가 하나뿐이라 결과는 비지만, 예외로 배치를 죽이지는 않는다
    assert items == []
    assert len(route.calls) == search_tool.MAX_ATTEMPTS


@respx.mock
def test_400_은_재시도하지_않는다(monkeypatch):
    monkeypatch.setattr(search_tool, "ENDPOINTS", only_naver_blog())
    route = respx.get(NAVER_BLOG_URL).mock(
        return_value=httpx.Response(400, json={"errorCode": "SE01"})
    )

    search_tool.search("가계부", SourceKind.BLOG, limit=5)

    assert len(route.calls) == 1


@respx.mock
def test_연속_3회_실패하면_그_provider_를_차단한다(monkeypatch):
    monkeypatch.setattr(search_tool, "ENDPOINTS", only_naver_blog())
    route = respx.get(NAVER_BLOG_URL).mock(
        return_value=httpx.Response(400, json={"errorCode": "SE01"})
    )

    for _ in range(3):
        search_tool.search("가계부", SourceKind.BLOG, limit=5)

    assert search_tool.is_blocked("naver")

    # 차단된 뒤에는 더 부르지 않는다 — 우회하지 않는다
    before = len(route.calls)
    assert search_tool.search("가계부", SourceKind.BLOG, limit=5) == []
    assert len(route.calls) == before


@respx.mock
def test_reset_run_state_가_차단을_푼다(monkeypatch):
    monkeypatch.setattr(search_tool, "ENDPOINTS", only_naver_blog())
    respx.get(NAVER_BLOG_URL).mock(return_value=httpx.Response(400))
    for _ in range(3):
        search_tool.search("가계부", SourceKind.BLOG, limit=5)
    assert search_tool.is_blocked("naver")

    search_tool.reset_run_state()

    assert not search_tool.is_blocked("naver")


@respx.mock
def test_한_provider_가_죽어도_다른_provider_는_계속_쓴다():
    respx.get(NAVER_BLOG_URL).mock(return_value=httpx.Response(500))
    respx.get(KAKAO_BLOG_URL).mock(
        return_value=httpx.Response(200, json=kakao_body([kakao_doc(1)]))
    )
    respx.get(KAKAO_WEB_URL).mock(
        return_value=httpx.Response(200, json=kakao_body(
            [kakao_doc(2, url="https://web.example/2")]))
    )

    items = search_tool.search("가계부", SourceKind.BLOG, limit=10)

    assert len(items) == 2
    assert all(i.id.startswith("kakao:") for i in items)


@respx.mock
def test_성공하면_실패_연속_카운터가_초기화된다(monkeypatch):
    monkeypatch.setattr(search_tool, "ENDPOINTS", only_naver_blog())
    respx.get(NAVER_BLOG_URL).mock(
        side_effect=[
            httpx.Response(400),
            httpx.Response(400),
            httpx.Response(200, json=naver_body([blog_item(1)])),
            httpx.Response(400),
        ]
    )

    for _ in range(4):
        search_tool.search("가계부", SourceKind.BLOG, limit=5)

    assert not search_tool.is_blocked("naver")


# ══════════════════════════════════════════════
# 쿼터
# ══════════════════════════════════════════════


@respx.mock
def test_호출할_때마다_쿼터_파일이_늘어난다(monkeypatch, corpus_dir):
    monkeypatch.setattr(search_tool, "ENDPOINTS", only_naver_blog())
    respx.get(NAVER_BLOG_URL).mock(
        return_value=httpx.Response(200, json=naver_body([blog_item(1)]))
    )

    search_tool.search("가계부", SourceKind.BLOG, limit=5)
    search_tool.search("이사", SourceKind.BLOG, limit=5)

    path = search_tool.quota_path()
    assert path.parent == corpus_dir
    assert json.loads(path.read_text(encoding="utf-8"))["naver"] == 2


@respx.mock
def test_한도를_넘기면_QuotaExceeded(monkeypatch, isolated_settings):
    monkeypatch.setattr(search_tool, "ENDPOINTS", only_naver_blog())
    monkeypatch.setattr(isolated_settings, "NAVER_DAILY_CAP", 2)
    respx.get(NAVER_BLOG_URL).mock(
        return_value=httpx.Response(200, json=naver_body([blog_item(1)]))
    )

    search_tool.search("가계부", SourceKind.BLOG, limit=5)
    search_tool.search("이사", SourceKind.BLOG, limit=5)

    with pytest.raises(QuotaExceeded):
        search_tool.search("청소", SourceKind.BLOG, limit=5)


def test_QuotaExceeded_는_SearchError_의_한_종류다():
    assert issubclass(QuotaExceeded, SearchError)


@respx.mock
def test_쿼터는_provider_별로_따로_센다(monkeypatch, isolated_settings):
    monkeypatch.setattr(isolated_settings, "NAVER_DAILY_CAP", 1)
    respx.get(NAVER_BLOG_URL).mock(
        return_value=httpx.Response(200, json=naver_body([blog_item(1)]))
    )
    respx.get(KAKAO_BLOG_URL).mock(
        return_value=httpx.Response(200, json=kakao_body([kakao_doc(1)]))
    )
    respx.get(KAKAO_WEB_URL).mock(
        return_value=httpx.Response(200, json=kakao_body(
            [kakao_doc(2, url="https://web.example/2")]))
    )

    search_tool.search("가계부", SourceKind.BLOG, limit=9)  # naver 1회 소진
    counts = search_tool.read_quota()

    assert counts["naver"] == 1
    assert counts["kakao"] == 2


@respx.mock
def test_재시도도_쿼터를_소모한다(monkeypatch):
    monkeypatch.setattr(search_tool, "ENDPOINTS", only_naver_blog())
    respx.get(NAVER_BLOG_URL).mock(return_value=httpx.Response(503))

    search_tool.search("가계부", SourceKind.BLOG, limit=5)

    assert search_tool.read_quota()["naver"] == search_tool.MAX_ATTEMPTS


# ══════════════════════════════════════════════
# 미지원 소스 · 키 없음
# ══════════════════════════════════════════════


@pytest.mark.parametrize("kind", [SourceKind.PUBLIC_DATA, SourceKind.SOCIAL])
def test_미지원_SourceKind_는_예외가_아니라_빈_목록이다(kind, caplog):
    with caplog.at_level("WARNING"):
        assert search_tool.search("가계부", kind, limit=10) == []
    assert caplog.records, "경고 로그를 남겨야 한다"


@pytest.mark.parametrize("kind", [SourceKind.PUBLIC_DATA, SourceKind.SOCIAL])
def test_미지원_SourceKind_는_쿼터를_쓰지_않는다(kind):
    search_tool.search("가계부", kind, limit=10)
    assert search_tool.read_quota() == {}


def test_키가_없으면_SearchError(monkeypatch, isolated_settings):
    monkeypatch.setattr(isolated_settings, "NAVER_CLIENT_ID", "")
    monkeypatch.setattr(isolated_settings, "NAVER_CLIENT_SECRET", "")
    monkeypatch.setattr(isolated_settings, "KAKAO_REST_API_KEY", "")

    with pytest.raises(SearchError) as exc:
        search_tool.search("가계부", SourceKind.BLOG, limit=10)

    assert "NAVER_CLIENT_ID" in str(exc.value)


def test_시크릿만_비어도_SearchError(monkeypatch, isolated_settings):
    monkeypatch.setattr(isolated_settings, "NAVER_CLIENT_SECRET", "")
    monkeypatch.setattr(isolated_settings, "KAKAO_REST_API_KEY", "")

    with pytest.raises(SearchError):
        search_tool.search("가계부", SourceKind.BLOG, limit=10)


@respx.mock
def test_키가_있는_provider_만_골라_쓴다(monkeypatch, isolated_settings):
    monkeypatch.setattr(isolated_settings, "KAKAO_REST_API_KEY", "")
    respx.get(NAVER_BLOG_URL).mock(
        return_value=httpx.Response(200, json=naver_body([blog_item(1)]))
    )

    items = search_tool.search("가계부", SourceKind.BLOG, limit=10)

    assert len(items) == 1  # 카카오는 조용히 빠지고 네이버만 돈다


def test_빈_검색어와_0_이하_limit_은_호출하지_않는다():
    assert search_tool.search("", SourceKind.BLOG, limit=10) == []
    assert search_tool.search("   ", SourceKind.BLOG, limit=10) == []
    assert search_tool.search("가계부", SourceKind.BLOG, limit=0) == []
    assert search_tool.read_quota() == {}


# ══════════════════════════════════════════════
# 방어
# ══════════════════════════════════════════════


@respx.mock
def test_url_이_없는_줄은_버린다(monkeypatch):
    monkeypatch.setattr(search_tool, "ENDPOINTS", only_naver_blog())
    respx.get(NAVER_BLOG_URL).mock(
        return_value=httpx.Response(200, json=naver_body([
            {"title": "제목만 있다", "link": "", "description": "본문"},
            blog_item(1),
        ]))
    )

    assert len(search_tool.search("가계부", SourceKind.BLOG, limit=10)) == 1


@respx.mock
def test_JSON_이_아니면_SearchError_이지만_배치는_살아_있다(monkeypatch):
    monkeypatch.setattr(search_tool, "ENDPOINTS", only_naver_blog())
    respx.get(NAVER_BLOG_URL).mock(
        return_value=httpx.Response(200, text="<html>점검 중</html>")
    )

    assert search_tool.search("가계부", SourceKind.BLOG, limit=10) == []


@respx.mock
def test_items_가_비면_빈_목록(monkeypatch):
    monkeypatch.setattr(search_tool, "ENDPOINTS", only_naver_blog())
    respx.get(NAVER_BLOG_URL).mock(
        return_value=httpx.Response(200, json=naver_body([]))
    )

    assert search_tool.search("가계부", SourceKind.BLOG, limit=10) == []
