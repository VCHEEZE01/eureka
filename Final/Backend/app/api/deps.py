"""
"지금 요청을 보낸 사람이 누구인가" — 라우트가 공통으로 쓰는 의존성.

두 가지를 제공한다.
  get_current_user           로그인 필수. 없거나 무효하면 401(또는
                              AUTH_ENABLED=False면 503).
  get_current_user_optional   로그인 선택. 없거나 무효하면 조용히 None
                              — 아이디어 생성처럼 "로그아웃 상태에서도
                              돼야 하는" 엔드포인트가 쓴다.

★ 실제 검증은 app/core/auth.py 가 한다. 여기는 HTTP 계층(헤더 파싱,
  상태 코드 변환)만 맡는다 — idea_routes.py 의 axes.resolve() /
  _bad_request() 와 같은 역할 분담이다.
"""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.auth import AuthNotConfigured, TokenInvalid, verify_access_token

# auto_error=False — 헤더가 없어도 여기서 바로 401을 던지지 않는다.
# get_current_user_optional 이 "없으면 None"을 표현해야 하기 때문이다.
_bearer = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    id: str
    email: str = ""


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(status_code=401, detail={"error_code": "unauthorized", "message": message})


def _auth_disabled() -> HTTPException:
    return HTTPException(
        status_code=503,
        detail={"error_code": "auth_disabled", "message": "로그인 기능이 꺼져 있습니다."},
    )


def _resolve(creds: HTTPAuthorizationCredentials | None) -> CurrentUser | None:
    # 토큰이 없어도 verify_access_token()을 통과시킨다 — 그래야
    # AUTH_ENABLED=False일 때 "토큰이 없으니 401"이 아니라 "애초에 로그인
    # 기능이 꺼져 있으니 503"이 나온다. 빈 문자열을 바로 반환해 버리면
    # 이 판정 자체가 스킵된다(실제로 있었던 버그 — 토큰 없이 호출하면
    # AUTH_ENABLED 여부와 무관하게 항상 401이 났었다).
    token = creds.credentials if creds is not None else ""
    try:
        payload = verify_access_token(token)
    except AuthNotConfigured:
        # 설정 문제는 "로그인 안 함"과 다르다 — 호출부가 갈라서 처리한다.
        raise
    except TokenInvalid:
        return None
    return CurrentUser(id=payload["sub"], email=payload.get("email", ""))


def get_current_user_optional(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> CurrentUser | None:
    """로그인 여부를 몰라도 되는 엔드포인트용. AUTH_ENABLED=False 이거나
    토큰이 없거나 무효하면 예외 없이 None을 돌려준다 — 호출부가 이걸로
    분기해서 "익명"과 "로그인"을 구분한다."""
    try:
        return _resolve(creds)
    except AuthNotConfigured:
        return None


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> CurrentUser:
    """로그인이 반드시 필요한 엔드포인트용(보관함 등). 토큰이 없거나
    무효하면 401, AUTH_ENABLED=False면 503 — 이 구분 덕분에 클라이언트가
    "로그인하세요"와 "지금은 로그인 기능이 없어요"를 다르게 안내할 수 있다."""
    try:
        user = _resolve(creds)
    except AuthNotConfigured:
        raise _auth_disabled()
    if user is None:
        raise _unauthorized("로그인이 필요합니다.")
    return user
