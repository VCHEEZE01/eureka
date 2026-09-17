"""Vercel 배포 환경 대응 — settings.VERCEL · snapshot_store · cache.write."""

import warnings
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config.settings import Settings, settings
from app.trends import build_snapshot, snapshot_store

warnings.filterwarnings("ignore", category=DeprecationWarning)


@pytest.fixture
def client():
    from main import app

    return TestClient(app)


@pytest.fixture
def no_snapshot_file(tmp_path, monkeypatch):
    """배포 환경처럼 data/trends/latest_snapshot.json 이 없는 상태."""
    monkeypatch.setattr(build_snapshot, "LATEST_PATH", tmp_path / "missing.json")
    snapshot_store._build_in_memory.cache_clear()
    yield
    snapshot_store._build_in_memory.cache_clear()


def test_vercel_moves_idea_cache_to_tmp(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    assert Settings().IDEAS_DIR == Path("/tmp/eureka/ideas")


def test_explicit_ideas_dir_is_kept_on_vercel(monkeypatch, tmp_path):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("IDEAS_DIR", str(tmp_path))
    assert Settings().IDEAS_DIR == tmp_path


def test_missing_snapshot_is_503_outside_vercel(no_snapshot_file, client):
    r = client.get("/api/trends", params={"tab": "trend"})
    assert r.status_code == 503
    assert r.json()["detail"]["error_code"] == "snapshot_not_ready"


def test_missing_snapshot_is_built_in_memory_on_vercel(no_snapshot_file, monkeypatch, client):
    monkeypatch.setattr(settings, "VERCEL", True)
    r = client.get("/api/trends", params={"tab": "trend"})
    assert r.status_code == 200
    assert r.json()["items"]

    r2 = client.post("/api/trends/r1/ideas", json={"platform": "웹(Web)", "type": "재미"})
    assert r2.status_code == 200
    assert len(r2.json()["ideas"]) == 3


def test_cache_write_failure_still_returns_ideas(no_snapshot_file, monkeypatch, tmp_path, client):
    monkeypatch.setattr(settings, "VERCEL", True)
    not_a_dir = tmp_path / "not-a-dir"
    not_a_dir.write_text("읽기 전용 파일시스템 흉내", encoding="utf-8")
    monkeypatch.setattr(settings, "IDEAS_DIR", not_a_dir)

    r = client.post("/api/trends/r1/ideas", json={"platform": "웹(Web)", "type": "재미"})
    assert r.status_code == 200
    assert len(r.json()["ideas"]) == 3
