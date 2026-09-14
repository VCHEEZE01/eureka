"""Public reads never invoke generation and do not expose review-only drafts."""
from datetime import datetime

from fastapi.testclient import TestClient

from app.schemas.models import Category, Problem
from app.tools import db_tool
from main import app


def example():
    return Problem(id="p-test", title="테스트 문제", one_liner="테스트 한 줄",
                   category=Category.IT_PRODUCTIVITY, description="테스트 설명",
                   context="테스트 맥락", complexity_note="확인할 제약", evidence=[],
                   case_count=20, source_count=3, updated_at=datetime.now())


def test_empty_published_pool_and_unknown_problem(monkeypatch):
    monkeypatch.setattr(db_tool, "list_problems", lambda: [])
    monkeypatch.setattr(db_tool, "get_problem", lambda _: None)
    with TestClient(app) as client:
        assert client.get("/problems").json() == []
        assert client.get("/problems/missing").status_code == 404
        assert client.post("/combine").status_code == 404
        assert client.post("/personalize").status_code == 404
        assert client.get("/problems/missing/ideas").status_code == 404


def test_read_contract_and_category_filter(monkeypatch):
    p = example()
    monkeypatch.setattr(db_tool, "list_problems", lambda: [p])
    monkeypatch.setattr(db_tool, "get_problem", lambda id: p if id == p.id else None)
    with TestClient(app) as client:
        detail = client.get("/problems/p-test")
        assert detail.status_code == 200
        assert detail.json() == p.model_dump(mode="json")
        assert client.get("/problems", params={"category": "금융"}).json() == []
        assert len(client.get("/problems", params={"category": "IT/생산성"}).json()) == 1
        assert client.get("/problems", params={"category": "invalid"}).status_code == 422


def test_cors_allows_configured_frontend_only(monkeypatch):
    monkeypatch.setattr(db_tool, "list_problems", lambda: [])
    with TestClient(app) as client:
        allowed = client.get("/problems", headers={"Origin": "http://localhost:3000"})
        assert allowed.headers["access-control-allow-origin"] == "http://localhost:3000"
        other = client.get("/problems", headers={"Origin": "https://unrelated.example"})
        assert "access-control-allow-origin" not in other.headers


def test_corrupt_store_is_an_error_not_an_empty_success(monkeypatch):
    def fail(*args):
        raise db_tool.ProblemStoreError("synthetic corrupt file")
    monkeypatch.setattr(db_tool, "list_problems", fail)
    monkeypatch.setattr(db_tool, "get_problem", fail)
    with TestClient(app) as client:
        assert client.get("/problems").status_code == 503
        assert client.get("/problems/p-test").status_code == 503
        assert client.get("/problems/bad!id").status_code == 404
