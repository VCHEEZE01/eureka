"""
프론트엔드가 부르는 입구.

TODO(담당자): Phase 2에서 채운다. 지금은 뼈대만.

★ 주의: 실시간 생성(F05·F07)은 단발 응답이 아니라
  진행 상태를 흘려보내는 스트리밍이어야 한다.
  나중에 붙이려면 API를 다시 짜야 하므로 처음부터 이렇게 설계한다.
"""

import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.config.settings import settings
from app.schemas.collections import CollectionRequest, CollectionRun
from app.tools import collection_tool

from app.schemas.models import Category, Problem
from app.tools import db_tool

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/problems", response_model=list[Problem])
def problems(category: Category | None = None) -> list[Problem]:
    """게시된 문제만 읽는다. 화면 조회는 수집이나 LLM을 호출하지 않는다."""
    try:
        return [p for p in db_tool.list_problems() if category is None or p.category == category]
    except db_tool.ProblemStoreError as exc:
        raise HTTPException(status_code=503, detail="문제 저장소를 확인할 수 없습니다") from exc


@router.get("/problems/{problem_id}", response_model=Problem)
def problem_detail(problem_id: str) -> Problem:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,199}", problem_id):
        raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다")
    try:
        problem = db_tool.get_problem(problem_id)
    except db_tool.ProblemStoreError as exc:
        raise HTTPException(status_code=503, detail="문제 저장소를 확인할 수 없습니다") from exc
    if problem is None:
        raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다")
    return problem


# TODO: GET  /problems/{id}/ideas 기본 아이디어 (F06)
# TODO: POST /combine            문제 조합 (F05) — 스트리밍
# TODO: POST /personalize        개인화 (F07) — 스트리밍



@router.get("/", include_in_schema=False)
def reference_app():
    """승인된 reference HTML을 그대로 제공한다. 화면 열기는 수집을 시작하지 않는다."""
    if not settings.REFERENCE_HTML_PATH.is_file():
        raise HTTPException(status_code=503, detail="공유용 화면 파일을 찾을 수 없습니다")
    return FileResponse(settings.REFERENCE_HTML_PATH, media_type="text/html",
                        headers={"Cache-Control": "no-store"})


@router.post("/collections", status_code=202, response_model=CollectionRun)
def start_collection(request: CollectionRequest) -> CollectionRun:
    """명시적인 탐색 요청만 실제 수집을 시작한다. 같은 최근 요청은 재사용한다."""
    try:
        return collection_tool.create_run(request.target, resume_from=request.resume_from)
    except collection_tool.CollectionBusyError as exc:
        raise HTTPException(status_code=409, detail={"message": str(exc), "run_id": exc.run_id}) from exc
    except collection_tool.CollectionRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except collection_tool.CollectionStoreError as exc:
        raise HTTPException(status_code=503, detail="수집 실행 기록을 확인할 수 없습니다") from exc


@router.get("/collections/{run_id}", response_model=CollectionRun)
def collection_status(run_id: str) -> CollectionRun:
    if not re.fullmatch(r"col-[0-9a-f]{24}", run_id):
        raise HTTPException(status_code=404, detail="수집 실행을 찾을 수 없습니다")
    try:
        run = collection_tool.get_run(run_id)
    except collection_tool.CollectionStoreError as exc:
        raise HTTPException(status_code=503, detail="수집 실행 기록을 확인할 수 없습니다") from exc
    if run is None:
        raise HTTPException(status_code=404, detail="수집 실행을 찾을 수 없습니다")
    return run
