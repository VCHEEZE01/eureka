"""
app/core/auth.py (토큰 검증) + app/api/deps.py (의존성) + /api/config, /api/me.

★ PyJWKClient는 내부적으로 urllib을 쓴다(httpx가 아니다) — 그래서
  respx로 못 잡는다. 진짜 EC 키쌍을 만들어 우리가 직접 서명하고,
  _get_jwks_client()만 가짜로 바꿔 그 공개키를 돌려주게 한다. 이러면
  네트워크 없이 verify_access_token()의 실제 검증 로직(서명·만료·
  audience·issuer)을 전부 통과시켜 본다.
"""

import time

import jwt
import pytest
from fastapi.testclient import TestClient
from jwt.algorithms import ECAlgorithm

from app.api.deps import CurrentUser, get_current_user
from app.config.settings import settings
from app.core import auth as auth_module

ISSUER = "https://test-project.supabase.co/auth/v1"
AUDIENCE = "authenticated"


@pytest.fixture
def keypair():
    from cryptography.hazmat.primitives.asymmetric import ec

    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    return private_key, public_key


@pytest.fixture
def signed_token(keypair):
    """(payload 오버라이드) -> 서명된 JWT 문자열."""
    private_key, _ = keypair

    def _make(**overrides):
        now = int(time.time())
        payload = {
            "sub": "user-123",
            "email": "person@example.com",
            "aud": AUDIENCE,
            "iss": ISSUER,
            "iat": now,
            "exp": now + 3600,
        }
        payload.update(overrides)
        return jwt.encode(payload, private_key, algorithm="ES256")

    return _make


@pytest.fixture(autouse=True)
def _enable_auth_with_fake_jwks(monkeypatch, keypair):
    """AUTH_ENABLED를 켜고, JWKS 조회를 네트워크 없이 우리 키로 대체한다."""
    _, public_key = keypair
    jwk_dict = ECAlgorithm(ECAlgorithm.SHA256).to_jwk(public_key, as_dict=True)
    signing_key = jwt.PyJWK.from_dict(jwk_dict, algorithm="ES256")

    class _FakeJWKClient:
        def get_signing_key_from_jwt(self, token):
            return signing_key

    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://test-project.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_ANON_KEY", "anon-key-value")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "service-role-value")
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", "")  # 비대칭 경로를 타게
    monkeypatch.setattr(auth_module, "_get_jwks_client", lambda: _FakeJWKClient())
    yield


# ── app/core/auth.py: verify_access_token ───────────────────────

def test_valid_token_returns_payload_with_sub(signed_token):
    payload = auth_module.verify_access_token(signed_token())
    assert payload["sub"] == "user-123"
    assert payload["email"] == "person@example.com"


def test_expired_token_is_invalid(signed_token):
    token = signed_token(exp=int(time.time()) - 10)
    with pytest.raises(auth_module.TokenInvalid):
        auth_module.verify_access_token(token)


def test_wrong_audience_is_invalid(signed_token):
    token = signed_token(aud="some-other-app")
    with pytest.raises(auth_module.TokenInvalid):
        auth_module.verify_access_token(token)


def test_wrong_issuer_is_invalid(signed_token):
    token = signed_token(iss="https://not-our-project.supabase.co/auth/v1")
    with pytest.raises(auth_module.TokenInvalid):
        auth_module.verify_access_token(token)


def test_missing_sub_is_invalid(signed_token):
    token = signed_token(sub="")
    with pytest.raises((auth_module.TokenInvalid, Exception)):
        # sub가 빈 문자열이면 require=["sub"]에 걸리거나, 통과해도
        # verify_access_token의 사후 체크(payload.get("sub"))에 걸려야 한다.
        auth_module.verify_access_token(token)


def test_empty_token_is_invalid():
    with pytest.raises(auth_module.TokenInvalid):
        auth_module.verify_access_token("")


def test_garbage_token_is_invalid():
    with pytest.raises(auth_module.TokenInvalid):
        auth_module.verify_access_token("not-a-jwt-at-all")


def test_auth_disabled_raises_not_configured(monkeypatch, signed_token):
    monkeypatch.setattr(settings, "AUTH_ENABLED", False)
    with pytest.raises(auth_module.AuthNotConfigured):
        auth_module.verify_access_token(signed_token())


def test_missing_supabase_url_raises_not_configured(monkeypatch, signed_token):
    monkeypatch.setattr(settings, "SUPABASE_URL", "")
    with pytest.raises(auth_module.AuthNotConfigured):
        auth_module.verify_access_token(signed_token())


def test_legacy_hs256_path_works(monkeypatch):
    """SUPABASE_JWT_SECRET이 있으면 대칭 키 경로를 탄다 — 레거시 프로젝트 지원."""
    secret = "shared-secret-value-that-is-long-enough-for-hs256-32bytes"
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", secret)
    now = int(time.time())
    token = jwt.encode(
        {"sub": "legacy-user", "aud": AUDIENCE, "iss": ISSUER, "iat": now, "exp": now + 3600},
        secret,
        algorithm="HS256",
    )
    payload = auth_module.verify_access_token(token)
    assert payload["sub"] == "legacy-user"


# ── app/api/deps.py ───────────────────────────────────────────────

def test_get_current_user_optional_returns_none_without_token():
    from app.api.deps import get_current_user_optional

    assert get_current_user_optional(None) is None


def test_get_current_user_optional_returns_user_with_valid_token(signed_token):
    from fastapi.security import HTTPAuthorizationCredentials

    from app.api.deps import get_current_user_optional

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=signed_token())
    user = get_current_user_optional(creds)
    assert user is not None
    assert user.id == "user-123"


def test_get_current_user_optional_returns_none_on_invalid_token():
    from fastapi.security import HTTPAuthorizationCredentials

    from app.api.deps import get_current_user_optional

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="garbage")
    assert get_current_user_optional(creds) is None


def test_get_current_user_raises_401_without_token():
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(None)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["error_code"] == "unauthorized"


def test_get_current_user_raises_503_when_auth_disabled(monkeypatch):
    from fastapi import HTTPException

    monkeypatch.setattr(settings, "AUTH_ENABLED", False)
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(None)
    assert exc_info.value.status_code == 503
    assert exc_info.value.detail["error_code"] == "auth_disabled"


# ── /api/config, /api/me (실제 라우트) ──────────────────────────

@pytest.fixture
def client():
    from main import app

    return TestClient(app)


def test_config_endpoint_reports_ready_when_supabase_configured(client):
    r = client.get("/api/config")
    assert r.status_code == 200
    body = r.json()
    assert body["auth_enabled"] is True
    assert body["supabase_url"] == "https://test-project.supabase.co"
    assert body["supabase_anon_key"] == "anon-key-value"
    # service_role 키는 응답에 아예 없어야 한다
    assert "service" not in str(body).lower()


def test_config_endpoint_hides_everything_when_not_ready(client, monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "")  # ready 조건 하나만 깨도
    r = client.get("/api/config")
    body = r.json()
    assert body["auth_enabled"] is False
    assert body["supabase_url"] == ""
    assert body["supabase_anon_key"] == ""


def test_me_endpoint_401_without_token(client):
    r = client.get("/api/me")
    assert r.status_code == 401
    assert r.json()["detail"]["error_code"] == "unauthorized"


def test_me_endpoint_returns_user_with_valid_token(client, signed_token):
    r = client.get("/api/me", headers={"Authorization": f"Bearer {signed_token()}"})
    assert r.status_code == 200
    body = r.json()
    assert body["user_id"] == "user-123"
    assert body["email"] == "person@example.com"


def test_me_endpoint_401_with_expired_token(client, signed_token):
    token = signed_token(exp=int(time.time()) - 10)
    r = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_dependency_override_for_route_tests(client):
    """다른 라우트 테스트가 쓸 패턴 — 가짜 JWT를 만들지 않고 의존성 자체를
    갈아끼운다. 이게 계획(B-9)에서 명시한 권장 방식이다."""
    from main import app

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id="override-id", email="o@e.st")
    try:
        r = client.get("/api/me")
        assert r.status_code == 200
        assert r.json()["user_id"] == "override-id"
    finally:
        app.dependency_overrides.clear()
