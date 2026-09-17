"""
Vercel 배포 진입점 — 로컬 실행에는 쓰지 않는다 (로컬은 Final/Backend 에서 uvicorn main:app).

Vercel은 저장소 최상위의 index.py 에서 `app` 이라는 FastAPI 인스턴스를 찾는다.
실제 앱은 Final/Backend/main.py 이고, 그 안의 `from app...` import 가 동작하도록
Final/Backend 를 import 경로 맨 앞에 넣은 뒤 가져온다.

저장소 최상위를 프로젝트 루트로 두는 이유: 화면 파일(Final/Frontend/v1-trend-incubator.html)이
Final/Backend 밖에 있어서, 루트를 Final/Backend 로 잡으면 함수 번들에 화면이 빠진다.

관련 파일: requirements.txt(런타임 의존성) · .python-version
"""

import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent / "Final" / "Backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

import main as _backend_main  # noqa: E402

app = _backend_main.app
