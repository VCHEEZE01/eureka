"""
Supabase 액세스 토큰 검증 — "이 요청이 로그인된 사용자의 것인가"를
판정하는 유일한 곳.

★ 로컬 검증(JWKS)을 쓴다. 매 요청마다 Supabase에 GET /auth/v1/user 로
  물어보면 익명 사용자까지 왕복 지연을 물고, 무료 티어가 일시정지되는
  순간 아이디어 생성까지 멎는다. 토큰이 exp까지 유효한 비용은 감수한다
  — 위조에 민감한 값(새로고침 쿼터)은 어차피 Postgres RLS가 권위를
  갖고 클라이언트는 건드릴 수 없다(db/001_auth_library_quota.sql).

지원하는 서명 방식 두 가지, 설정만으로 자동 판별:
  - SUPABASE_JWT_SECRET 이 있으면 → 레거시 HS256(공유 시크릿)
  - 없으면 → 새 프로젝트 기본값인 비대칭(ES256/RS256) + JWKS

★ PyJWT[crypto] 는 팀 공유 requirements.txt 에 새로 추가한 의존성이다.
  받은 뒤 pip install 을 안 돌린 팀원의 서버가 통째로 죽지 않도록,
  import 자체가 실패하면 여기서 잡아서 AuthNotConfigured 로만 새게
  한다 — 서버는 계속 뜨고, 로그인 기능만 꺼진다.
"""

import logging

from app.config.settings import settings

logger = logging.getLogger(__name__)

try:
    import jwt
    from jwt import PyJWKClient

    _JWT_AVAILABLE = True
    _IMPORT_ERROR = ""
except ImportError as e:  # pragma: no cover — 정상 설치 시 이 분기를 안 탄다
    _JWT_AVAILABLE = False
    _IMPORT_ERROR = str(e)
    logger.warning(
        "PyJWT를 불러올 수 없습니다(%s) — 로그인 기능이 꺼진 채로 서버를 계속 띄웁니다. "
        "pip install -r requirements.txt 를 다시 돌리세요.", e,
    )


class TokenInvalid(Exception):
    """토큰이 없거나, 형식이 깨졌거나, 서명·만료·발급자·대상이 안 맞는다."""


class AuthNotConfigured(Exception):
    """AUTH_ENABLED=False 이거나, 켜졌는데 필요한 설정/의존성이 없다."""


_ASYMMETRIC_ALGS = ["ES256", "RS256"]
_SYMMETRIC_ALG = "HS256"

# JWKS는 네트워크 호출이라 매 요청마다 부르지 않는다. PyJWKClient가
# 내부적으로 lifespan(초) 동안 캐시한다 — URL이 바뀌면(설정 재로드 등)
# 새로 만든다.
_jwks_client: "PyJWKClient | None" = None
_jwks_client_url: str | None = None


def _get_jwks_client() -> "PyJWKClient":
    global _jwks_client, _jwks_client_url
    url = settings.supabase_jwks_url
    if _jwks_client is None or _jwks_client_url != url:
        _jwks_client = PyJWKClient(
            url,
            cache_keys=True,
            lifespan=settings.SUPABASE_JWKS_CACHE_SEC,
            timeout=settings.SUPABASE_TIMEOUT_SEC,
        )
        _jwks_client_url = url
    return _jwks_client


def reset_jwks_cache() -> None:
    """테스트 전용 — 이전 테스트가 만든 JWKS 클라이언트/캐시를 지운다."""
    global _jwks_client, _jwks_client_url
    _jwks_client = None
    _jwks_client_url = None


def verify_access_token(token: str) -> dict:
    """검증에 성공하면 토큰 payload(dict)를 돌려준다. 최소 'sub'(user id)가
    있다고 보장한다. 실패하면 TokenInvalid, 애초에 설정이 안 됐으면
    AuthNotConfigured — 둘을 구분하는 이유는 API 응답 코드가 다르기
    때문이다(전자는 401, 후자는 503)."""
    if not settings.AUTH_ENABLED:
        raise AuthNotConfigured("AUTH_ENABLED=False")
    if not _JWT_AVAILABLE:
        raise AuthNotConfigured(f"PyJWT 미설치: {_IMPORT_ERROR}")
    if not settings.SUPABASE_URL:
        raise AuthNotConfigured("SUPABASE_URL이 비어 있습니다")
    if not token:
        raise TokenInvalid("토큰이 없습니다")

    common_kwargs = dict(
        audience=settings.SUPABASE_JWT_AUDIENCE,
        issuer=settings.supabase_jwt_issuer,
        options={"require": ["exp", "sub"]},
    )

    try:
        if settings.SUPABASE_JWT_SECRET:
            payload = jwt.decode(
                token, settings.SUPABASE_JWT_SECRET, algorithms=[_SYMMETRIC_ALG], **common_kwargs
            )
        else:
            signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token, signing_key.key, algorithms=_ASYMMETRIC_ALGS, **common_kwargs
            )
    except jwt.PyJWTError as e:
        raise TokenInvalid(str(e)) from e
    except Exception as e:  # JWKS 네트워크 실패 등 jwt 라이브러리 밖의 오류
        raise TokenInvalid(f"토큰 검증 중 오류: {e}") from e

    if not payload.get("sub"):
        raise TokenInvalid("토큰에 sub(사용자 id)가 없습니다")

    return payload
