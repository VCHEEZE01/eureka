"""
검색 도구 — 네이버·카카오 검색 API를 부르는 유일한 곳.

쓰는 사람: ① 수집 에이전트

★ 에이전트는 여기를 거쳐서만 바깥과 대화한다.
  이유: 테스트할 때 이 파일만 가짜로 바꾸면 되고, API 키가 한 곳에만 있다.

★ 원문 URL을 따라가 본문을 긁지 않는다.
  검색 API가 준 스니펫만 쓴다. 이것이 "원문 전문 저장 금지"
  (docs/DATA_COLLECTION.md 3-2)의 구조적 보장이다.

────────────────────────────────────────────────
엔드포인트 근거 (전부 공식 문서 확인 완료)
────────────────────────────────────────────────
· 네이버 검색 오픈API  https://developers.naver.com/docs/serviceapi/search/blog/blog.md
  - GET https://openapi.naver.com/v1/search/{blog|news|kin|cafearticle}.json
  - 헤더 X-Naver-Client-Id / X-Naver-Client-Secret
  - query(필수) · display(기본 10, 최대 100) · start(기본 1, 최대 1000)
    · sort(sim=정확도 기본 / date=날짜순)
  - 응답 items[]: title · link · description (+ blog: bloggername·postdate,
    news: originallink·pubDate, cafearticle: cafename·cafeurl, kin: 날짜 없음)
  - 하루 호출 한도 25,000회. 429 = 하루 허용량 초과 또는 초당 호출량 초과
    (https://developers.naver.com/docs/common/openapiguide/errorcode.md)

· 카카오 다음 검색 REST API  https://developers.kakao.com/docs/ko/daum-search/dev-guide
  - GET https://dapi.kakao.com/v2/search/{web|blog}
  - 헤더 Authorization: KakaoAK {REST_API_KEY}
  - query(필수) · sort(accuracy 기본 / recency=최신순) · page(1~50) · size(1~50, 기본 10)
  - 응답 meta{total_count,pageable_count,is_end} · documents[]{title,contents,url,datetime}
    (blog 는 blogname·thumbnail 추가). datetime 은 ISO 8601.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from hashlib import sha1
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx

from app.config.settings import settings
from app.schemas.models import RawItem, SourceKind
from app.tools.text_tool import clean_text, content_hash, strip_pii

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════
# 예외
# ══════════════════════════════════════════════


class SearchError(Exception):
    """검색 한 건이 실패했다. 배치는 이걸 잡고 다음 쿼리로 넘어간다."""


class QuotaExceeded(SearchError):
    """일일 호출 한도를 다 썼다. 잡으면 그때까지 수집분으로 마무리해야 한다."""


# ══════════════════════════════════════════════
# 상수 — 공식 문서에서 확인한 값만 둔다
# ══════════════════════════════════════════════

NAVER_BASE_URL = "https://openapi.naver.com/v1/search"
NAVER_MAX_DISPLAY = 100  # 확인: display 최대 100
NAVER_MAX_START = 1000  # 확인: start 최대 1000
NAVER_SORT_DATE = "date"  # 확인: 날짜순 내림차순

KAKAO_BASE_URL = "https://dapi.kakao.com/v2/search"
KAKAO_MAX_SIZE = 50  # 확인: web·blog 는 size 1~50
KAKAO_MAX_PAGE = 50  # 확인: web·blog 는 page 1~50
KAKAO_SORT_RECENT = "recency"  # 확인: 최신순
KAKAO_AUTH_SCHEME = "KakaoAK"  # 확인: Authorization: KakaoAK {키}

PROVIDER_NAVER = "naver"
PROVIDER_KAKAO = "kakao"

HTTP_TIMEOUT_SEC = 10.0
MAX_ATTEMPTS = 3  # 429·5xx 재시도 횟수
BACKOFF_BASE_SEC = 1.0  # 지수 백오프 기준. 1 → 2 → 4초
MAX_CONSECUTIVE_FAILURES = 3  # 연속 이만큼 실패하면 그 provider 를 차단한다

# 정체를 밝힌다 (docs/DATA_COLLECTION.md 4-6 수집 규칙).
USER_AGENT = "EurekaBot/0.1"

# TODO(공식문서 확인): 카카오 일일 쿼터 수치는 개발자 콘솔의 "쿼터" 페이지에만
#   있고 REST API 문서 본문에는 없다. settings.KAKAO_DAILY_CAP 이 유일한 근거다.
#   키가 발급되면 콘솔 값과 맞춰라.


# ══════════════════════════════════════════════
# SourceKind → 엔드포인트 매핑
# ══════════════════════════════════════════════


@dataclass(frozen=True)
class _Endpoint:
    provider: str
    path: str  # 네이버는 "blog.json", 카카오는 "blog"
    source_name: str  # RawItem.source_name 에 그대로 들어간다
    date_field: str = ""  # 빈 문자열이면 그 API 는 날짜를 주지 않는다


_NAVER_BLOG = _Endpoint(PROVIDER_NAVER, "blog.json", "네이버 블로그", "postdate")
_NAVER_NEWS = _Endpoint(PROVIDER_NAVER, "news.json", "네이버 뉴스", "pubDate")
_NAVER_KIN = _Endpoint(PROVIDER_NAVER, "kin.json", "네이버 지식iN")
_NAVER_CAFE = _Endpoint(PROVIDER_NAVER, "cafearticle.json", "네이버 카페")
_KAKAO_BLOG = _Endpoint(PROVIDER_KAKAO, "blog", "다음 블로그", "datetime")
_KAKAO_WEB = _Endpoint(PROVIDER_KAKAO, "web", "다음 웹문서", "datetime")

# ★ 블로그가 최우선이다. 네이버를 먼저 두어 이쪽부터 채워지게 한다.
ENDPOINTS: dict[SourceKind, tuple[_Endpoint, ...]] = {
    SourceKind.BLOG: (_NAVER_BLOG, _KAKAO_BLOG, _KAKAO_WEB),
    SourceKind.NEWS: (_NAVER_NEWS,),
    # 화면에 노출하지 않는다. 수집 여부는 미결정이나 코드는 준비해 둔다.
    SourceKind.COMMUNITY: (_NAVER_KIN, _NAVER_CAFE),
    # 아래 둘은 의도적으로 비워 둔다. 아래 _UNSUPPORTED 의 사유를 본다.
    SourceKind.PUBLIC_DATA: (),
    SourceKind.SOCIAL: (),
}

_UNSUPPORTED: dict[SourceKind, str] = {
    SourceKind.PUBLIC_DATA: "공공데이터 API 키 승인 대기 중이라 아직 미구현이다",
    SourceKind.SOCIAL: "Threads 키워드 검색 권한 승인 대기 중이라 아직 미구현이다",
}


# ══════════════════════════════════════════════
# HTTP 클라이언트 — 모듈 레벨에서 재사용한다
# ══════════════════════════════════════════════

_client: Optional[httpx.Client] = None


def _get_client() -> httpx.Client:
    """연결을 재사용한다. 쿼리 수백 개를 도는 배치에서 이게 크다."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.Client(
            timeout=HTTP_TIMEOUT_SEC, headers={"User-Agent": USER_AGENT}
        )
    return _client


def _sleep(seconds: float) -> None:
    """백오프 대기. 테스트가 여기만 갈아끼우면 즉시 끝난다."""
    time.sleep(seconds)


# ══════════════════════════════════════════════
# 실행 단위 상태 — 연속 실패한 provider 차단
# ══════════════════════════════════════════════
#
# "4xx/5xx가 연속 3회면 그 사이트 수집을 중단한다 (우회 금지)"
#   — docs/DATA_COLLECTION.md 4-6

_failure_streak: dict[str, int] = {}
_blocked_providers: set[str] = set()


def reset_run_state() -> None:
    """배치 1회를 시작할 때 부른다. 차단 기록은 실행 단위로만 유지된다."""
    _failure_streak.clear()
    _blocked_providers.clear()


def _note_success(provider: str) -> None:
    _failure_streak[provider] = 0


def _note_failure(provider: str) -> None:
    n = _failure_streak.get(provider, 0) + 1
    _failure_streak[provider] = n
    if n >= MAX_CONSECUTIVE_FAILURES and provider not in _blocked_providers:
        _blocked_providers.add(provider)
        logger.warning(
            "%s 연속 %d회 실패 — 이번 실행 동안 이 provider 를 차단한다. 우회하지 않는다.",
            provider,
            n,
        )


def is_blocked(provider: str) -> bool:
    return provider in _blocked_providers


# ══════════════════════════════════════════════
# 쿼터 가드 — {CORPUS_DIR}/quota-{YYYY-MM-DD}.json
# ══════════════════════════════════════════════


def quota_path(day: Optional[date] = None) -> Path:
    """오늘의 카운터 파일. ★ settings 를 호출 시점에 읽는다(테스트가 갈아끼운다)."""
    day = day or date.today()
    return Path(settings.CORPUS_DIR) / f"quota-{day.isoformat()}.json"


def _daily_cap(provider: str) -> int:
    """provider 별 하루 한도. 모듈 로드 시점이 아니라 지금 읽는다."""
    if provider == PROVIDER_NAVER:
        return int(settings.NAVER_DAILY_CAP)
    if provider == PROVIDER_KAKAO:
        return int(settings.KAKAO_DAILY_CAP)
    return 0


def read_quota(day: Optional[date] = None) -> dict[str, int]:
    """오늘까지 쓴 호출 수. 파일이 없거나 깨졌으면 빈 dict."""
    path = quota_path(day)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): int(v) for k, v in data.items() if isinstance(v, int)}


def _write_quota(counts: dict[str, int], day: Optional[date] = None) -> None:
    path = quota_path(day)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(counts, ensure_ascii=False), encoding="utf-8")


def _consume_quota(provider: str) -> None:
    """
    호출 1건을 미리 적어 둔다. 한도를 넘으면 QuotaExceeded.

    ★ 재시도도 실제로 API를 때리므로 시도마다 센다.
      먼저 적고 나중에 부르는 순서인 이유: 프로세스가 죽어도 과소 집계가 안 난다.
    """
    cap = _daily_cap(provider)
    counts = read_quota()
    used = counts.get(provider, 0)
    if cap and used >= cap:
        raise QuotaExceeded(
            f"{provider} 일일 호출 한도 {cap}회를 다 썼다 (사용 {used}회). "
            f"오늘은 여기까지다."
        )
    counts[provider] = used + 1
    _write_quota(counts)


# ══════════════════════════════════════════════
# URL 정규화 · id
# ══════════════════════════════════════════════

# 붙어 있어도 같은 글인 파라미터들. 이것 때문에 id 가 갈리면 중복 제거가 안 된다.
TRACKING_PARAM_PREFIXES = ("utm_",)
TRACKING_PARAMS = frozenset({"ref", "from"})


def normalize_url(url: str) -> str:
    """
    같은 글이 다른 쿼리로 걸려도 같은 문자열이 나오게 만든다.

    스킴 통일(https) · 소문자 호스트 · 기본 포트 제거 ·
    트래킹 쿼리(utm_*, ref, from) 제거 · 남은 쿼리 정렬 · 프래그먼트 제거.
    """
    if not url:
        return ""
    parts = urlsplit(url.strip())
    host = (parts.hostname or "").lower()
    if parts.port and parts.port not in (80, 443):
        host = f"{host}:{parts.port}"
    query = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k.lower() not in TRACKING_PARAMS
        and not k.lower().startswith(TRACKING_PARAM_PREFIXES)
    ]
    query.sort()
    return urlunsplit(("https", host, parts.path, urlencode(query), ""))


def make_item_id(provider: str, url: str) -> str:
    """`{provider}:{정규화 URL 의 sha1 앞 16자}`."""
    digest = sha1(normalize_url(url).encode("utf-8")).hexdigest()[:16]
    return f"{provider}:{digest}"


# ══════════════════════════════════════════════
# 날짜 파싱 — 실패하면 예외가 아니라 None
# ══════════════════════════════════════════════


def _parse_posted_at(field: str, value: Any) -> Optional[date]:
    if not field or not value or not isinstance(value, str):
        return None
    raw = value.strip()
    try:
        if field == "postdate":  # 네이버 블로그: "20260909"
            return datetime.strptime(raw, "%Y%m%d").date()
        if field == "pubDate":  # 네이버 뉴스: RFC 1123
            return parsedate_to_datetime(raw).date()
        if field == "datetime":  # 카카오: ISO 8601
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
    except (ValueError, TypeError, IndexError):
        logger.debug("날짜 파싱 실패 — None 으로 둔다: %s=%r", field, value)
    return None


# ══════════════════════════════════════════════
# 요청
# ══════════════════════════════════════════════


def _auth_headers(provider: str) -> dict[str, str]:
    """키가 비어 있으면 여기서 명확하게 실패시킨다."""
    if provider == PROVIDER_NAVER:
        cid, secret = settings.NAVER_CLIENT_ID, settings.NAVER_CLIENT_SECRET
        if not cid or not secret:
            raise SearchError(
                "네이버 검색 API 키가 없다. .env 의 NAVER_CLIENT_ID / "
                "NAVER_CLIENT_SECRET 을 채워라."
            )
        return {"X-Naver-Client-Id": cid, "X-Naver-Client-Secret": secret}
    if provider == PROVIDER_KAKAO:
        key = settings.KAKAO_REST_API_KEY
        if not key:
            raise SearchError(
                "카카오 검색 API 키가 없다. .env 의 KAKAO_REST_API_KEY 를 채워라."
            )
        return {"Authorization": f"{KAKAO_AUTH_SCHEME} {key}"}
    raise SearchError(f"모르는 provider: {provider}")


def _has_keys(provider: str) -> bool:
    try:
        _auth_headers(provider)
    except SearchError:
        return False
    return True


def _get_json(provider: str, url: str, params: dict[str, Any]) -> dict:
    """
    GET 한 번. 429·5xx 는 지수 백오프로 최대 MAX_ATTEMPTS 번 시도한다.

    QuotaExceeded 는 재시도하지 않고 바로 올린다 — 기다려도 안 풀린다.
    """
    headers = _auth_headers(provider)
    client = _get_client()
    last: Optional[SearchError] = None

    for attempt in range(MAX_ATTEMPTS):
        _consume_quota(provider)
        try:
            resp = client.get(url, params=params, headers=headers)
        except httpx.HTTPError as exc:
            last = SearchError(f"{provider} 요청 실패: {exc}")
        else:
            status = resp.status_code
            if status == 200:
                _note_success(provider)
                try:
                    return resp.json()
                except ValueError as exc:
                    _note_failure(provider)
                    raise SearchError(f"{provider} 응답이 JSON 이 아니다: {exc}") from exc
            if status == 429 or status >= 500:
                last = SearchError(f"{provider} HTTP {status}")
            else:
                # 400·401·403 은 다시 불러도 같다. 재시도하지 않는다.
                _note_failure(provider)
                raise SearchError(
                    f"{provider} 검색 실패: HTTP {status} {resp.text[:200]}"
                )
        if attempt < MAX_ATTEMPTS - 1:
            _sleep(BACKOFF_BASE_SEC * (2**attempt))

    _note_failure(provider)
    raise last or SearchError(f"{provider} 검색 실패")


# ══════════════════════════════════════════════
# 응답 → RawItem
# ══════════════════════════════════════════════


def _to_item(
    row: dict,
    endpoint: _Endpoint,
    source_kind: SourceKind,
    keyword: str,
    collected_at: datetime,
) -> Optional[RawItem]:
    """검색 결과 한 줄을 RawItem 으로. 쓸 수 없는 줄이면 None."""
    if endpoint.provider == PROVIDER_NAVER:
        url = row.get("originallink") or row.get("link") or ""
        raw_snippet = row.get("description") or ""
    else:
        url = row.get("url") or ""
        raw_snippet = row.get("contents") or ""

    url = clean_text(url, -1)
    if not url:
        return None

    # ★ 정제 순서: 태그 제거(clean_text) → PII 제거(strip_pii).
    #   순서를 뒤집으면 태그 안에 숨은 이메일·멘션을 놓친다.
    title = strip_pii(clean_text(row.get("title") or ""))
    snippet = strip_pii(clean_text(raw_snippet))
    if not title and not snippet:
        return None

    return RawItem(
        id=make_item_id(endpoint.provider, url),
        title=title,
        snippet=snippet,
        url=url,
        source_name=endpoint.source_name,
        source_kind=source_kind,
        posted_at=_parse_posted_at(endpoint.date_field, row.get(endpoint.date_field)),
        collected_at=collected_at,
        query_keyword=keyword,
        content_hash=content_hash(title, snippet),
    )


# ══════════════════════════════════════════════
# 페이지 순회
# ══════════════════════════════════════════════


def _fetch_endpoint(
    keyword: str, source_kind: SourceKind, endpoint: _Endpoint, want: int
) -> list[RawItem]:
    """엔드포인트 하나에서 최대 want 건. 정렬은 최신순으로 고정한다."""
    max_pages = max(int(settings.COLLECT_MAX_PAGES), 1)
    collected_at = datetime.now()
    out: list[RawItem] = []
    seen: set[str] = set()

    # ★ 페이지 크기는 처음에 정하고 끝까지 고정한다.
    #   남은 개수에 맞춰 줄이면 start 오프셋이 어긋나 같은 글을 다시 받는다.
    is_naver = endpoint.provider == PROVIDER_NAVER
    page_size = min(want, NAVER_MAX_DISPLAY if is_naver else KAKAO_MAX_SIZE)

    for page in range(max_pages):
        if len(out) >= want:
            break

        if is_naver:
            start = 1 + page * page_size
            if start > NAVER_MAX_START:
                break
            url = f"{NAVER_BASE_URL}/{endpoint.path}"
            params = {
                "query": keyword,
                "display": page_size,
                "start": start,
                "sort": NAVER_SORT_DATE,
            }
        else:
            page_no = page + 1
            if page_no > KAKAO_MAX_PAGE:
                break
            url = f"{KAKAO_BASE_URL}/{endpoint.path}"
            params = {
                "query": keyword,
                "size": page_size,
                "page": page_no,
                "sort": KAKAO_SORT_RECENT,
            }

        payload = _get_json(endpoint.provider, url, params)
        rows = payload.get("items" if is_naver else "documents")
        if not isinstance(rows, list) or not rows:
            break

        for row in rows:
            if not isinstance(row, dict):
                continue
            item = _to_item(row, endpoint, source_kind, keyword, collected_at)
            if item is None or item.id in seen:
                continue
            seen.add(item.id)
            out.append(item)
            if len(out) >= want:
                break

        if is_naver:
            if len(rows) < page_size:
                break  # 더 줄 게 없다
        else:
            meta = payload.get("meta")
            if isinstance(meta, dict) and meta.get("is_end"):
                break

    return out


# ══════════════════════════════════════════════
# 공개 API
# ══════════════════════════════════════════════


def search(keyword: str, source_kind: SourceKind, limit: int = 50) -> list[RawItem]:
    """
    검색어 하나로 원문을 긁어온다.

    · 미지원 SourceKind 는 예외가 아니라 빈 목록 + 경고 로그다.
      배치가 소스 하나 때문에 멈추면 안 된다.
    · 키가 없거나 provider 가 전부 막혔으면 SearchError.
    · 일일 한도를 넘기면 QuotaExceeded — 호출자가 잡아서 마무리해야 한다.
    """
    if limit <= 0 or not keyword.strip():
        return []

    endpoints = ENDPOINTS.get(source_kind, ())
    if not endpoints:
        logger.warning(
            "%s 는 아직 수집하지 않는다: %s",
            source_kind.value,
            _UNSUPPORTED.get(source_kind, "매핑된 엔드포인트가 없다"),
        )
        return []

    usable = [e for e in endpoints if _has_keys(e.provider)]
    if not usable:
        # 키가 하나도 없다. 여기서 분명하게 알려 준다.
        _auth_headers(endpoints[0].provider)  # 항상 SearchError 를 던진다
        raise SearchError(f"{source_kind.value} 를 부를 수 있는 키가 없다")

    live = [e for e in usable if not is_blocked(e.provider)]
    if not live:
        logger.warning(
            "%s 의 provider 가 전부 차단됐다 — 이번 실행에서는 건너뛴다.",
            source_kind.value,
        )
        return []

    # 출처를 고르게 섞는다. 한 곳에서만 나온 근거는 "세상의 문제"가 아니다
    # (docs/DATA_COLLECTION.md 6절 출처 3곳 조건).
    per_endpoint = -(-limit // len(live))

    out: list[RawItem] = []
    seen: set[str] = set()
    for endpoint in live:
        room = limit - len(out)
        if room <= 0:
            break
        if is_blocked(endpoint.provider):
            continue
        try:
            rows = _fetch_endpoint(
                keyword, source_kind, endpoint, min(per_endpoint, room)
            )
        except QuotaExceeded:
            raise
        except SearchError as exc:
            logger.warning("%s 검색 실패 — 건너뛴다: %s", endpoint.source_name, exc)
            continue
        for item in rows:
            if item.id in seen:
                continue
            seen.add(item.id)
            out.append(item)
            if len(out) >= limit:
                break

    return out[:limit]
