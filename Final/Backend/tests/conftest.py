"""
pytest 공통 설정.

★ v0 conftest.py는 그대로 못 쓴다 — CollectMode·LicensePolicy를
  import하는데 현재 app/schemas/models.py에 없다. 새로 짧게 쓴다.
"""

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import pytest

from app.config.settings import settings
from app.core.llm import reset_llm


@pytest.fixture(autouse=True)
def _offline_and_isolated(tmp_path, monkeypatch):
    """실호출을 막고, 아이디어 캐시가 진짜 data/ideas/를 건드리지 않게 한다.

    ★ .env에 실제 Supabase 키가 들어간 뒤로 이게 더 중요해졌다 —
      AUTH_ENABLED/SUPABASE_URL이 진짜 값이면 테스트가 실수로 진짜
      프로젝트에 네트워크를 낼 수 있다. 여기서 강제로 꺼서 "테스트는
      기본적으로 인증이 없다"를 보장한다. 인증을 실제로 테스트하는
      파일(test_auth.py)만 monkeypatch로 개별 켠다."""
    monkeypatch.setattr(settings, "LLM_DRY_RUN", True)
    monkeypatch.setattr(settings, "IDEAS_DIR", tmp_path / "ideas")
    monkeypatch.setattr(settings, "AUTH_ENABLED", False)
    monkeypatch.setattr(settings, "SUPABASE_URL", "")
    monkeypatch.setattr(settings, "SUPABASE_ANON_KEY", "")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "")
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", "")
    reset_llm()
    from app.core.auth import reset_jwks_cache
    reset_jwks_cache()
    yield
    reset_llm()
    reset_jwks_cache()
