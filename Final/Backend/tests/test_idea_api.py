import warnings

import pytest
from fastapi.testclient import TestClient

warnings.filterwarnings("ignore", category=DeprecationWarning)


@pytest.fixture
def client():
    from main import app

    return TestClient(app)


def test_generate_ideas_offline_returns_fallback(client):
    r = client.post("/api/trends/r1/ideas", json={"platform": "모바일 앱", "type": "재미", "count": 3})
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "fallback"
    assert len(body["ideas"]) == 3
    assert body["config"]["platform"] == "mobile"
    assert body["config"]["type"] == "fun"


def test_second_request_same_combo_hits_cache(client):
    client.post("/api/trends/r1/ideas", json={"platform": "웹(Web MVP)", "type": "실용(편의)"})
    r2 = client.post("/api/trends/r1/ideas", json={"platform": "웹(Web MVP)", "type": "실용(편의)"})
    assert r2.status_code == 200
    assert r2.json()["source"] == "cache"


def test_period_switch_reuses_cache_without_regenerating(client):
    client.post("/api/trends/r1/ideas", json={"platform": "웹(Web MVP)", "type": "실용(편의)", "period": "하루"})
    r2 = client.post("/api/trends/r1/ideas", json={"platform": "웹(Web MVP)", "type": "실용(편의)", "period": "한 달 이상"})
    assert r2.json()["source"] == "cache"
    idea = r2.json()["ideas"][0]
    assert idea["prompt"] == idea["prompts"]["month"]


def test_invalid_platform_is_400(client):
    r = client.post("/api/trends/r1/ideas", json={"platform": "홀로그램", "type": "재미"})
    assert r.status_code == 400
    assert r.json()["detail"]["error_code"] == "invalid_input"


def test_unknown_keyword_is_404(client):
    r = client.post("/api/trends/no-such-id/ideas", json={"platform": "웹(Web MVP)", "type": "재미"})
    assert r.status_code == 404
    assert r.json()["detail"]["error_code"] == "keyword_not_found"


def test_count_out_of_range_is_400(client):
    r = client.post("/api/trends/r1/ideas", json={"platform": "웹(Web MVP)", "type": "재미", "count": 20})
    assert r.status_code == 400


def test_get_cached_ideas_without_prior_post_is_404(client):
    r = client.get("/api/trends/r1/ideas", params={"platform": "데스크탑 웹", "type": "수익(비즈니스)"})
    assert r.status_code == 404


def test_get_cached_ideas_after_post_returns_200(client):
    client.post("/api/trends/r1/ideas", json={"platform": "데스크탑 웹", "type": "수익(비즈니스)"})
    r = client.get("/api/trends/r1/ideas", params={"platform": "데스크탑 웹", "type": "수익(비즈니스)"})
    assert r.status_code == 200
    assert r.json()["source"] == "cache"
