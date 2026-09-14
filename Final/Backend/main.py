"""
FastAPI 진입점. uvicorn main:app --reload 로 실행한다.

/ 는 공유용 reference HTML을 제공한다. POST /collections만 타겟 수집 worker를
시작하고 GET /collections/{id}는 실행 상태·검토용 결과를 읽는다.
주간 배치는 scripts/run_pipeline.py로 별도로 실행한다.
"""

from app.api.routes import router
from app.config.settings import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="유레카 API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.API_ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Accept", "Content-Type"],
)
app.include_router(router)
