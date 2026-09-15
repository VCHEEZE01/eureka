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


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/", include_in_schema=False)
def trend_incubator_app():
    if not _TREND_HTML_PATH.is_file():
        raise HTTPException(status_code=503, detail="트렌드 인큐베이터 화면 파일을 찾을 수 없습니다")
    return FileResponse(_TREND_HTML_PATH, media_type="text/html", headers={"Cache-Control": "no-store"})


# TODO: GET  /problems           문제 목록 (F03)
# TODO: GET  /problems/{id}      문제 상세 (F04)
# TODO: GET  /problems/{id}/ideas 기본 아이디어 (F06)
# TODO: POST /combine            문제 조합 (F05) — 스트리밍
# TODO: POST /personalize        개인화 (F07) — 스트리밍
