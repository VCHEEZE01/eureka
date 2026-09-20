"""
FastAPI 진입점.

실행:  cd Backend && uvicorn main:app --reload
확인:  http://localhost:8000/health

※ 배치(수집 파이프라인)는 이 서버가 아니라
  scripts/run_pipeline.py 로 따로 돈다. 서버가 죽어도 배치는 무관하고,
  배치가 죽어도 서버는 멀쩡해야 한다.
"""

from pathlib import Path

from app.api.auth_routes import router as auth_router
from app.api.idea_routes import router as idea_router
from app.api.library_routes import router as library_router
from app.api.routes import router
from app.api.trend_routes import router as trend_router
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="유레카 API")
app.include_router(router)
app.include_router(trend_router)
app.include_router(idea_router)
app.include_router(auth_router)
app.include_router(library_router)

# 아이디어 화면의 "추천 AI" 로고 이미지 — 디자인 script가 상대경로
# 목욕중/*.png 로 직접 참조한다(app/api/routes.py처럼 파일 하나씩 라우트를
# 만들지 않은 이유: 이미지가 여러 장이라 폴더째 서빙하는 게 맞다).
# Frontend/ 전체를 마운트하지 않는 이유는 routes.py의 주석과 같다
# (.env.example 등 비공개 파일 노출) — 이 폴더만, 있을 때만 마운트한다.
_ASSETS_DIR = Path(__file__).resolve().parent.parent / "Frontend" / "목욕중"
if _ASSETS_DIR.is_dir():
    app.mount("/목욕중", StaticFiles(directory=_ASSETS_DIR), name="ai-tool-icons")
