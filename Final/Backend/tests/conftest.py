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
    """실호출을 막고, 아이디어 캐시가 진짜 data/ideas/를 건드리지 않게 한다."""
    monkeypatch.setattr(settings, "LLM_DRY_RUN", True)
    monkeypatch.setattr(settings, "IDEAS_DIR", tmp_path / "ideas")
    reset_llm()
    yield
    reset_llm()
