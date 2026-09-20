"""
GET/POST/PATCH/DELETE /api/library/* — respx로 Supabase PostgREST를
가짜로 대신하고, get_current_user는 dependency_overrides로 갈아끼운다
(계획 B-9: JWT를 흉내 내지 말고 의존성 자체를 바꾼다).
"""

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.api.deps import CurrentUser, get_current_user
from app.config.settings import settings

USER_ID = "11111111-1111-1111-1111-111111111111"
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

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=USER_ID, email="t@e.st")
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_list_keywords_scopes_by_user_id(client):
    with respx.mock:
        route = respx.get(f"{BASE}/saved_keywords").mock(
            return_value=httpx.Response(200, json=[{"keyword_id": "r1", "name": "두잇"}])
        )
        r = client.get("/api/library/keywords")
        assert r.status_code == 200
        assert r.json() == {"items": [{"keyword_id": "r1", "name": "두잇"}], "count": 1}
        sent = route.calls.last.request.url
        assert f"user_id=eq.{USER_ID}" in str(sent)
        # service_role 키가 실제로 실려 나가는지(그래야 RLS를 우회해 조회된다)
        assert route.calls.last.request.headers["apikey"] == "service-role-key"


def test_save_keyword_upserts_with_on_conflict(client):
    with respx.mock:
        route = respx.post(f"{BASE}/saved_keywords").mock(
            return_value=httpx.Response(201, json=[{"keyword_id": "r1", "name": "두잇"}])
        )
        r = client.post("/api/library/keywords", json={"keyword_id": "r1", "name": "두잇", "category": "생산성"})
        assert r.status_code == 200
        assert r.json()["keyword_id"] == "r1"
        req = route.calls.last.request
        assert "on_conflict=user_id%2Ckeyword_id" in str(req.url) or "on_conflict=user_id,keyword_id" in str(req.url)
        assert req.headers["prefer"] == "resolution=merge-duplicates,return=representation"


def test_delete_keyword(client):
    with respx.mock:
        route = respx.delete(f"{BASE}/saved_keywords").mock(return_value=httpx.Response(204))
        r = client.delete("/api/library/keywords/r1")
        assert r.status_code == 204
        sent = str(route.calls.last.request.url)
        assert f"user_id=eq.{USER_ID}" in sent and "keyword_id=eq.r1" in sent


def test_save_idea_computes_idea_key_and_persists_payload(client):
    with respx.mock:
        route = respx.post(f"{BASE}/saved_ideas").mock(
            return_value=httpx.Response(201, json=[{"idea_key": "abc123", "name": "두잇 파인더"}])
        )
        body = {
            "keyword_id": "r1", "keyword_name": "두잇", "name": "두잇 파인더",
            "platform": "web", "type": "utility", "period": "week",
            "payload": {"name": "두잇 파인더", "mvpFeatures": ["a", "b"]},
        }
        r = client.post("/api/library/ideas", json=body)
        assert r.status_code == 200
        sent_body = route.calls.last.request.content
        assert b"week" in sent_body
        assert b"\xeb\x91\x90\xec\x9e\x87" in sent_body or "두잇" in sent_body.decode()


def test_save_idea_rejects_payload_without_name(client):
    r = client.post("/api/library/ideas", json={
        "name": "두잇", "payload": {"mvpFeatures": []},  # payload에 name 없음
    })
    assert r.status_code == 400
    assert r.json()["detail"]["error_code"] == "invalid_input"


def test_save_idea_rejects_oversized_payload(client):
    huge = {"name": "x", "blob": "a" * 100_000}
    r = client.post("/api/library/ideas", json={"name": "x", "payload": huge})
    assert r.status_code == 400


def test_patch_idea_merges_period(client):
    with respx.mock:
        route = respx.patch(f"{BASE}/saved_ideas").mock(
            return_value=httpx.Response(200, json=[{"idea_key": "abc123", "period": "month"}])
        )
        r = client.patch("/api/library/ideas/abc123", json={"period": "month"})
        assert r.status_code == 200
        assert r.json()["period"] == "month"
        sent = str(route.calls.last.request.url)
        assert "idea_key=eq.abc123" in sent


def test_patch_idea_404_when_not_found(client):
    with respx.mock:
        respx.patch(f"{BASE}/saved_ideas").mock(return_value=httpx.Response(200, json=[]))
        r = client.patch("/api/library/ideas/nope", json={"period": "day"})
        assert r.status_code == 404
        assert r.json()["detail"]["error_code"] == "idea_not_found"


def test_patch_idea_requires_at_least_one_field(client):
    r = client.patch("/api/library/ideas/abc123", json={})
    assert r.status_code == 400


def test_delete_idea(client):
    with respx.mock:
        route = respx.delete(f"{BASE}/saved_ideas").mock(return_value=httpx.Response(204))
        r = client.delete("/api/library/ideas/abc123")
        assert r.status_code == 204
        assert f"user_id=eq.{USER_ID}" in str(route.calls.last.request.url)


def test_migrate_imports_keywords_and_ideas(client):
    with respx.mock:
        respx.post(f"{BASE}/saved_keywords").mock(return_value=httpx.Response(201, json=[{"keyword_id": "r1"}]))
        respx.post(f"{BASE}/saved_ideas").mock(return_value=httpx.Response(201, json=[{"idea_key": "k1"}]))
        r = client.post("/api/library/migrate", json={
            "keywords": [{"id": "r1", "name": "두잇", "category": "생산성"}],
            "ideas": [{"name": "두잇 파인더", "keyword": "두잇", "mvpFeatures": ["a"]}],
        })
        assert r.status_code == 200
        body = r.json()
        assert body["imported_keywords"] == 1
        assert body["imported_ideas"] == 1
        assert body["skipped_keywords"] == 0
        assert body["skipped_ideas"] == 0


def test_migrate_skips_malformed_entries(client):
    with respx.mock:
        respx.post(f"{BASE}/saved_keywords").mock(return_value=httpx.Response(201, json=[{"keyword_id": "r1"}]))
        r = client.post("/api/library/migrate", json={
            "keywords": [{"id": "r1", "name": "두잇"}, {"name": "id 없음"}],  # 두번째는 id 없어 스킵
            "ideas": [],
        })
        body = r.json()
        assert body["imported_keywords"] == 1
        assert body["skipped_keywords"] == 1


def test_migrate_marks_legacy_ideas_without_period_key(client):
    """periodKey가 없는 옛 저장 항목은 day로 채우되 payload.periodLegacy=true를
    남긴다 — 화면이 틀린 값을 자신 있게 보여주지 않게."""
    with respx.mock:
        route = respx.post(f"{BASE}/saved_ideas").mock(return_value=httpx.Response(201, json=[{"idea_key": "k1"}]))
        client.post("/api/library/migrate", json={
            "keywords": [], "ideas": [{"name": "옛날 아이디어"}],  # periodKey 없음
        })
        sent = route.calls.last.request.content.decode()
        assert "periodLegacy" in sent
        assert '"period": "day"' in sent or '"period":"day"' in sent


def test_library_requires_login(monkeypatch):
    """dependency_override 없이(=진짜 get_current_user 경로) 호출하면
    AUTH_ENABLED=False(conftest 기본값)라 503이 나야 한다."""
    from main import app
    app.dependency_overrides.pop(get_current_user, None)
    monkeypatch.setattr(settings, "AUTH_ENABLED", False)
    c = TestClient(app)
    r = c.get("/api/library/keywords")
    assert r.status_code == 503
    assert r.json()["detail"]["error_code"] == "auth_disabled"


def test_supabase_upstream_error_becomes_502(client):
    with respx.mock:
        respx.get(f"{BASE}/saved_keywords").mock(return_value=httpx.Response(500, text="db down"))
        r = client.get("/api/library/keywords")
        assert r.status_code == 502
        assert r.json()["detail"]["error_code"] == "library_upstream_error"


def test_library_unavailable_when_supabase_not_ready(client, monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "")  # ready 조건 하나만 깨도
    r = client.get("/api/library/keywords")
    assert r.status_code == 503
    assert r.json()["detail"]["error_code"] == "library_unavailable"
