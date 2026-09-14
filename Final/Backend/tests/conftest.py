"""
테스트 공통 준비 — 모든 테스트가 이 파일에 의존한다.

여기서 보장하는 것 (전부 autouse, 테스트가 따로 안 불러도 걸린다)
  1. `import app` 이 되게 Final/Backend 를 sys.path 에 넣는다
  2. settings.CORPUS_DIR 을 pytest tmp_path 로 갈아끼운다 — 진짜 data/ 를 안 건드린다
  3. settings.LLM_DRY_RUN=True — 실수로 LLM 실호출이 나가지 않게
  4. 네트워크를 끊는다 — 진짜 API를 부르면 테스트가 그 자리에서 실패한다
     단 respx 를 쓰는 테스트는 정상 동작한다(아래 _no_network 설명 참고)

쓸 수 있는 fixture
    make_raw_item(...)   RawItem 하나 만들기
    make_judgement(...)  Judgement 하나 만들기
    corpus_dir           이번 테스트의 CORPUS_DIR (Path)
    assert_no_fabricated_numbers(text)  집계성 수치 표현이 없는지 검사
"""

from __future__ import annotations

import importlib
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import pytest

# ── 1. import app 이 되게 한다 ────────────────────────────────
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.schemas.models import (  # noqa: E402
    CollectMode,
    Judgement,
    LicensePolicy,
    RawItem,
    SourceKind,
)


# ══════════════════════════════════════════════
# 2·3. 설정 격리
# ══════════════════════════════════════════════
#
# settings 는 모듈 임포트 시점에 만들어지는 싱글턴이고, 다른 모듈들은
#     from app.config.settings import settings
# 로 그 객체를 이름에 묶어 둔다. 그래서 lru_cache 만 비우면 이미 임포트된
# 모듈들은 옛 객체를 계속 본다. → 살아 있는 객체의 필드를 제자리에서 바꾼다.


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path, monkeypatch):
    """CORPUS_DIR 은 tmp_path, LLM_DRY_RUN 은 True 로 강제한다."""
    settings_module = importlib.import_module("app.config.settings")
    live = settings_module.settings

    corpus_dir = tmp_path / "corpus"
    monkeypatch.setenv("CORPUS_DIR", str(corpus_dir))
    monkeypatch.setenv("LLM_DRY_RUN", "true")

    overrides = {"CORPUS_DIR": corpus_dir, "PROBLEMS_DIR": tmp_path / "problems", "COLLECTIONS_DIR": tmp_path / "collections", "SEARCH_QUOTA_DIR": None, "LLM_DRY_RUN": True}
    before = {k: getattr(live, k) for k in overrides}
    for k, v in overrides.items():
        setattr(live, k, v)

    # get_settings() 를 새로 부르는 코드도 같은 값을 보게 캐시를 비운다.
    settings_module.get_settings.cache_clear()

    yield live

    for k, v in before.items():
        setattr(live, k, v)
    settings_module.get_settings.cache_clear()


@pytest.fixture
def corpus_dir(isolated_settings) -> Path:
    """이번 테스트의 CORPUS_DIR."""
    return Path(isolated_settings.CORPUS_DIR)


# ══════════════════════════════════════════════
# 4. 네트워크 차단
# ══════════════════════════════════════════════
#
# httpx 가 아니라 그 아래 httpcore 를 막는다. 이유:
# respx 는 기본적으로 httpcore 의 handle_request / handle_async_request 를
# 갈아끼운다. 우리가 먼저 그 자리를 막아 두면, respx 가 활성화될 때
# respx 것이 위에 덮이고(= respx 가 이긴다) 끝나면 우리 차단이 되돌아온다.
# 반대로 httpx.HTTPTransport 를 막으면 respx 까지 같이 죽는다.
#
# ★ 함수 이름을 handle_request / handle_async_request 로 유지해야 한다.
#   respx 가 이름과 인자 이름을 보고 mock 을 만든다.

_HTTPCORE_TARGETS = [
    ("httpcore._sync.connection", "HTTPConnection", "handle_request"),
    ("httpcore._sync.connection_pool", "ConnectionPool", "handle_request"),
    ("httpcore._sync.http_proxy", "HTTPProxy", "handle_request"),
    ("httpcore._async.connection", "AsyncHTTPConnection", "handle_async_request"),
    ("httpcore._async.connection_pool", "AsyncConnectionPool", "handle_async_request"),
    ("httpcore._async.http_proxy", "AsyncHTTPProxy", "handle_async_request"),
]

_BLOCKED_MESSAGE = (
    "테스트가 실제 네트워크를 호출했다. respx 로 목킹하거나 "
    "LLM_DRY_RUN 경로를 타게 하라."
)


class NetworkBlockedError(RuntimeError):
    """테스트 중 실제 네트워크 호출. 그 자리에서 실패시킨다."""


def handle_request(self, request):  # noqa: D103 - 이름이 계약이다
    raise NetworkBlockedError(f"{_BLOCKED_MESSAGE} ({request.method} {request.url})")


async def handle_async_request(self, request):  # noqa: D103
    raise NetworkBlockedError(f"{_BLOCKED_MESSAGE} ({request.method} {request.url})")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """실제 네트워크를 끊는다. respx 가 활성인 동안은 respx 가 이긴다."""
    blockers = {
        "handle_request": handle_request,
        "handle_async_request": handle_async_request,
    }
    for module_path, class_name, method in _HTTPCORE_TARGETS:
        try:
            module = importlib.import_module(module_path)
        except ImportError:  # httpcore 가 없으면 막을 것도 없다
            continue
        monkeypatch.setattr(
            getattr(module, class_name), method, blockers[method], raising=False
        )
    yield


# ══════════════════════════════════════════════
# 모델 팩토리
# ══════════════════════════════════════════════


@pytest.fixture
def make_raw_item():
    """
    RawItem 하나. 인자는 전부 선택이다.

        item = make_raw_item(id="r1", query_keyword="가계부 번거롭")
    """
    counter = {"n": 0}

    def _make(
        id: Optional[str] = None,
        title: str = "가계부 정리가 너무 번거롭습니다",
        snippet: str = "매번 카드 명세서를 손으로 옮겨 적는 게 번거롭네요",
        url: Optional[str] = None,
        source_name: str = "네이버 카페",
        source_kind: SourceKind = SourceKind.COMMUNITY,
        posted_at: Optional[date] = None,
        collected_at: Optional[datetime] = None,
        query_keyword: str = "가계부 번거롭",
        content_hash: str = "",
        collected_by: CollectMode = CollectMode.BATCH,
        license: LicensePolicy = LicensePolicy.SUMMARY_ONLY,
        **extra,
    ) -> RawItem:
        counter["n"] += 1
        n = counter["n"]
        return RawItem(
            id=id or f"raw-{n:04d}",
            title=title,
            snippet=snippet,
            url=url or f"https://example.test/post/{n}",
            source_name=source_name,
            source_kind=source_kind,
            posted_at=posted_at,
            collected_at=collected_at or datetime(2026, 9, 9, 3, 0, 0),
            query_keyword=query_keyword,
            content_hash=content_hash or f"hash-{n:04d}",
            collected_by=collected_by,
            license=license,
            **extra,
        )

    return _make


@pytest.fixture
def make_judgement():
    """Judgement 하나. 기본은 '진짜 불편'."""
    counter = {"n": 0}

    def _make(
        raw_item_id: Optional[str] = None,
        is_pain: bool = True,
        pain_summary: Optional[str] = "가계부를 손으로 옮겨 적어야 한다",
        confidence: str = "높음",
        severity: Optional[str] = "중간",
        has_need_signal: bool = False,
        **extra,
    ) -> Judgement:
        counter["n"] += 1
        return Judgement(
            raw_item_id=raw_item_id or f"raw-{counter['n']:04d}",
            is_pain=is_pain,
            pain_summary=pain_summary if is_pain else None,
            confidence=confidence,
            severity=severity,
            has_need_signal=has_need_signal,
            **extra,
        )

    return _make


# ══════════════════════════════════════════════
# 제1규칙 도우미 — 숫자는 LLM이 만들지 않는다
# ══════════════════════════════════════════════

# 단위가 붙은 수량만 잡는다. "3일에 한 번" 같은 서술은 정당하므로 통과시킨다.
AGGREGATE_NUMBER_RE = re.compile(r"\d+\s*(건|명|개|%|퍼센트|배|위|만|억|천|백)")


def find_aggregate_numbers(text: str) -> list[str]:
    """집계성 수량 표현을 전부 찾아 준다. 없으면 빈 목록."""
    return [m.group(0) for m in AGGREGATE_NUMBER_RE.finditer(text or "")]


@pytest.fixture
def assert_no_fabricated_numbers():
    """LLM 산출물 문자열에 지어낸 집계 수치가 없는지 검사한다."""

    def _assert(text: str, where: str = "") -> None:
        hits = find_aggregate_numbers(text)
        assert not hits, f"지어낸 집계 수치 {hits} — {where or text!r}"

    return _assert
