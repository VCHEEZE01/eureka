"""
인증 관련 최소 API — 회원가입·로그인·로그아웃은 여기 없다.

★ 그 셋은 브라우저에서 supabase-js가 직접 한다(Final/Frontend/
  eureka-app.js). FastAPI는 비밀번호를 보지도, 토큰을 발급하지도
  않는다 — 검증만 한다(app/core/auth.py). 프록시하지 않는 이유는
  계획 문서(B-3) 참고: supabase-js가 무음 토큰 갱신과 다중 탭 동기화를
  이미 하므로, 그걸 다시 만들 이유가 없다.

GET /api/config   브라우저가 Supabase SDK를 초기화하는 데 필요한 값.
                   anon key는 공개해도 되는 값이다(RLS가 실제 방어선).
GET /api/me       지금 토큰이 가리키는 사용자. 로그인 여부 확인용.
"""

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, get_current_user
from app.config.settings import settings

router = APIRouter(prefix="/api", tags=["auth"])


@router.get("/config")
def get_config() -> dict:
    return {
        "auth_enabled": settings.supabase_ready,
        "supabase_url": settings.SUPABASE_URL if settings.supabase_ready else "",
        "supabase_anon_key": settings.SUPABASE_ANON_KEY if settings.supabase_ready else "",
    }


@router.get("/me")
def get_me(user: CurrentUser = Depends(get_current_user)) -> dict:
    return {"user_id": user.id, "email": user.email}
