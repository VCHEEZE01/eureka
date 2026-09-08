"""
FastAPI 진입점.

실행:  cd Backend && uvicorn main:app --reload
확인:  http://localhost:8000/health

※ 배치(수집 파이프라인)는 이 서버가 아니라
  scripts/run_pipeline.py 로 따로 돈다. 서버가 죽어도 배치는 무관하고,
  배치가 죽어도 서버는 멀쩡해야 한다.
"""

from app.api.routes import router
from fastapi import FastAPI

app = FastAPI(title="유레카 API")
app.include_router(router)
