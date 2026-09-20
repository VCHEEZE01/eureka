"""
프론트엔드가 부르는 입구.

TODO(담당자): Phase 2에서 채운다. 지금은 뼈대만.

★ 주의: 실시간 생성(F05·F07)은 단발 응답이 아니라
  진행 상태를 흘려보내는 스트리밍이어야 한다.
  나중에 붙이려면 API를 다시 짜야 하므로 처음부터 이렇게 설계한다.
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()

# v0의 "GET / 이 reference html을 그대로 서빙" 패턴을 그대로 가져온다.
# 이 경로로 열어야(http://localhost:8000/) 화면의 fetch('/api/trends')가
# 같은 오리진으로 붙는다 — file://로 이중클릭해서 열면 API 없이 폴백
# 데이터로 동작한다(그것도 의도된 동작).
_TREND_HTML_PATH = Path(__file__).resolve().parent.parent.parent.parent / "Frontend" / "v1-trend-incubator.html"

# 디자인과 분리한 연동 계층. 팀원이 새 디자인 HTML 을 줘도 이 파일은
# 그대로 살아남는다(자세한 건 Final/Frontend/INTEGRATION.md).
#
# ★ StaticFiles 로 Frontend/ 를 통째로 마운트하지 않는다 — 그 폴더엔
#   .env.example, package.json, src/, node_modules/, .next/ 가 같이 있어서
#   전부 공개돼 버린다. 파일 하나면 라우트 하나로 충분하다.
_APP_JS_PATH = _TREND_HTML_PATH.parent / "eureka-app.js"

# 카카오톡·슬랙 등 링크 공유 미리보기(Open Graph og:image)가 쓴다.
# HTML <head>의 og:image가 절대주소로 이 경로를 가리킨다.
_OG_IMAGE_PATH = _TREND_HTML_PATH.parent / "public" / "eureka.png"


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/", include_in_schema=False)
def trend_incubator_app():
    if not _TREND_HTML_PATH.is_file():
        raise HTTPException(status_code=503, detail="트렌드 인큐베이터 화면 파일을 찾을 수 없습니다")
    return FileResponse(_TREND_HTML_PATH, media_type="text/html", headers={"Cache-Control": "no-store"})


@router.get("/eureka-app.js", include_in_schema=False)
def eureka_app_js():
    # no-store 는 HTML 과 같은 이유다 — 디자인을 다시 이식한 직후 브라우저가
    # 옛 JS 를 캐시에서 꺼내 쓰면 "분명 고쳤는데 안 바뀐다"가 된다.
    if not _APP_JS_PATH.is_file():
        raise HTTPException(status_code=503, detail="eureka-app.js 를 찾을 수 없습니다")
    return FileResponse(
        _APP_JS_PATH,
        media_type="application/javascript",
        headers={"Cache-Control": "no-store"},
    )


@router.get("/og-image.png", include_in_schema=False)
def og_image():
    # 로고 이미지라 HTML·JS와 달리 자주 안 바뀐다 — 공유 미리보기가
    # 매번 새로 받아가지 않도록 짧게라도 캐싱을 허용한다.
    if not _OG_IMAGE_PATH.is_file():
        raise HTTPException(status_code=503, detail="og-image.png를 찾을 수 없습니다")
    return FileResponse(
        _OG_IMAGE_PATH,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=3600"},
    )


# TODO: GET  /problems           문제 목록 (F03)
# TODO: GET  /problems/{id}      문제 상세 (F04)
# TODO: GET  /problems/{id}/ideas 기본 아이디어 (F06)
# TODO: POST /combine            문제 조합 (F05) — 스트리밍
# TODO: POST /personalize        개인화 (F07) — 스트리밍
