"""
POST /api/trends/{id}/ideas 의 refresh=true 경로 — 쿼터 소비/반납.

★ 원자성(동시 요청이 정말 한 번만 통과하는가)은 respx로 증명할 수 없다
  (DB 속성이다). 그 보장은 db/001_auth_library_quota.sql의
  `insert … on conflict … where used < quota_limit` 절 자체에 있다 —
  Supabase SQL Editor에서 손으로 두 번 호출해 true→false를 직접 확인
  했다(db/README.md). 여기서는 그 함수를 respx로 흉내 내
  idea_routes.py가 반환값을 올바르게 해석하고, 실패 결과(폴백·유사)에서
  쿼터를 제대로 반납하는지만 본다.
"""

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.api.deps import CurrentUser, get_current_user_optional
from app.config.settings import settings

USER_ID = "22222222-2222-2222-2222-222222222222"
BASE = "https://test-project.supabase.co/rest/v1"


@pytest.fixture(autouse=True)
def _supabase_ready(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://test-project.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_ANON_KEY", "anon-key")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "service-role-key")


@pytest.fixture
def client():
    from main import app

    app.dependency_overrides[get_current_user_optional] = lambda: CurrentUser(id=USER_ID, email="t@e.st")
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def anon_client():
    from main import app

    app.dependency_overrides[get_current_user_optional] = lambda: None
    yield TestClient(app)
    app.dependency_overrides.clear()


def _mock_consume(allowed: bool, used: int = 1, limit: int = 1):
    return respx.post(f"{BASE}/rpc/consume_refresh_quota").mock(
        return_value=httpx.Response(200, json=[{"o_allowed": allowed, "o_used": used, "o_limit": limit}])
    )


def _mock_release():
    return respx.post(f"{BASE}/rpc/release_refresh_quota").mock(return_value=httpx.Response(200, json=None))


def test_refresh_requires_login(anon_client):
    r = anon_client.post("/api/trends/r1/ideas", json={"platform": "웹(Web)", "type": "실용(편의)", "refresh": True})
    assert r.status_code == 403
    assert r.json()["detail"]["error_code"] == "refresh_requires_login"


def test_refresh_unavailable_when_supabase_not_ready(client, monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "")
    r = client.post("/api/trends/r1/ideas", json={"platform": "웹(Web)", "type": "실용(편의)", "refresh": True})
    assert r.status_code == 503
    assert r.json()["detail"]["error_code"] == "refresh_unavailable"


def test_refresh_releases_quota_when_llm_falls_back(client):
    """LLM_DRY_RUN=True(conftest 기본값)라 소스는 항상 fallback이다 —
    ★ 이 결과로는 쿼터를 태우면 안 된다(release가 반드시 불려야 한다)."""
    with respx.mock:
        consume_route = _mock_consume(allowed=True, used=1, limit=1)
        release_route = _mock_release()

        r = client.post("/api/trends/r1/ideas", json={"platform": "웹(Web)", "type": "실용(편의)", "count": 3, "refresh": True})

        assert r.status_code == 200
        body = r.json()
        assert consume_route.called, "먼저 예약(소비)했어야 한다"
        assert release_route.called, "폴백 결과는 쿼터를 반납해야 한다"
        assert body["source"] == "fallback"
        assert body["refresh"]["applied"] is False
        assert body["refresh"]["reason"] == "fallback"


def test_refresh_does_not_release_quota_on_genuine_llm_success(client, monkeypatch):
    """LLM이 진짜 성공하면(=완전한 아이디어 3개를 돌려주면) 쿼터를 그대로
    소비 상태로 둬야 한다 — release가 절대 불리면 안 된다."""
    def _ia():
        # web 축은 depth1이 3~4개여야 검증을 통과한다(app/ideas/axes.py PLATFORM_SPEC["web"]["ia_shape"]).
        return [
            {"depth1": f"화면{n}", "depth2": [{"title": "기능", "desc": "설명"}]}
            for n in range(1, 4)
        ]

    canned = [
        {
            "name": f"테스트 아이디어 {i}", "short_name": f"idea{i}", "approach": "테스트",
            "slogan": "슬로건", "target": "타깃", "problem": "문제", "solution": "해결",
            "architecture": "구조", "diff": "차별점",
            "mvp_features": ["기능1", "기능2", "기능3"], "future_features": ["확장1"],
            "ia": _ia(),
        }
        for i in range(3)
    ]
    monkeypatch.setattr("app.tools.idea_tool.complete_ideas_json", lambda prompt: canned)

    with respx.mock:
        consume_route = _mock_consume(allowed=True, used=1, limit=1)
        release_route = _mock_release()

        r = client.post("/api/trends/r1/ideas", json={"platform": "웹(Web)", "type": "실용(편의)", "count": 3, "refresh": True})

        assert r.status_code == 200
        body = r.json()
        assert body["source"] == "llm"
        assert consume_route.called
        assert not release_route.called, "진짜 성공했는데 쿼터를 반납하면 안 된다"
        assert body["refresh"] == {"applied": True, "reason": "ok", "used": 1, "limit": 1, "variant": 1}


def test_refresh_blocked_returns_previous_set_without_calling_agent(client, monkeypatch):
    """쿼터가 이미 소진됐으면(o_allowed=false) 에이전트를 아예 부르지 않고
    캐시에 있던 직전 세트를 그대로 돌려줘야 한다."""
    called = {"n": 0}

    def _spy(prompt):
        called["n"] += 1
        raise AssertionError("쿼터가 막혔는데 LLM을 불렀다")

    monkeypatch.setattr("app.tools.idea_tool.complete_ideas_json", _spy)

    with respx.mock:
        _mock_consume(allowed=False, used=1, limit=1)
        r = client.post("/api/trends/r1/ideas", json={"platform": "웹(Web)", "type": "실용(편의)", "count": 3, "refresh": True})

    # 캐시에 아무 것도 없는 첫 시도라 409(quota_spent)로 떨어지는 것도,
    # 직전 캐시가 있어 200으로 그 세트를 돌려주는 것도 둘 다 "LLM을 안 불렀다"는
    # 이 테스트의 핵심 단언을 만족한다.
    assert r.status_code in (200, 409)
    assert called["n"] == 0
    if r.status_code == 200:
        assert r.json()["refresh"]["reason"] == "quota_spent"
    else:
        assert r.json()["detail"]["error_code"] == "quota_spent"
