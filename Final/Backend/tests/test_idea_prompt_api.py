import warnings

import pytest
from fastapi.testclient import TestClient

warnings.filterwarnings("ignore", category=DeprecationWarning)


@pytest.fixture
def client():
    from main import app

    return TestClient(app)


@pytest.fixture
def sample_idea(client):
    r = client.post("/api/trends/r1/ideas", json={"platform": "웹(Web MVP)", "type": "재미"})
    assert r.status_code == 200
    return r.json()["ideas"][0]


def test_rebuild_prompt_reflects_edited_mvp(client, sample_idea):
    sample_idea["mvp_features"] = ["내가 직접 고친 기능 A", "기능 B"]
    r = client.post(
        "/api/trends/r1/ideas/prompt",
        json={"platform": "웹(Web MVP)", "type": "재미", "period": "일주일", "idea": sample_idea},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["period"] == "week"
    assert "[핵심 기능 1]: 내가 직접 고친 기능 A" in body["prompt"]
    assert "[핵심 기능 2]: 기능 B" in body["prompt"]
    assert set(body["prompts"]) == {"day", "week", "month"}
    assert body["prompt"] == body["prompts"]["week"]


def test_rebuild_prompt_keeps_ia_outline(client, sample_idea):
    """IA는 화면에서만 숨겼고 프롬프트 본문에는 그대로 남는다 — 회귀 가드."""
    r = client.post(
        "/api/trends/r1/ideas/prompt",
        json={"platform": "웹(Web MVP)", "type": "재미", "idea": sample_idea},
    )
    assert r.status_code == 200
    prompt = r.json()["prompt"]
    assert "# 2. 시스템 아키텍처 및 서비스 정보구조(IA)" in prompt
    assert sample_idea["ia"][0]["depth1"] in prompt


def test_rebuild_prompt_allows_two_mvp_items(client, sample_idea):
    """사람이 고친 MVP에는 validate의 3~5개 규칙을 강제하지 않는다."""
    sample_idea["mvp_features"] = ["하나", "둘"]
    r = client.post(
        "/api/trends/r1/ideas/prompt",
        json={"platform": "웹(Web MVP)", "type": "재미", "idea": sample_idea},
    )
    assert r.status_code == 200


def test_rebuild_prompt_empty_mvp_is_400(client, sample_idea):
    sample_idea["mvp_features"] = ["  ", ""]
    r = client.post(
        "/api/trends/r1/ideas/prompt",
        json={"platform": "웹(Web MVP)", "type": "재미", "idea": sample_idea},
    )
    assert r.status_code == 400
    assert r.json()["detail"]["error_code"] == "invalid_input"


def test_rebuild_prompt_too_many_mvp_is_400(client, sample_idea):
    sample_idea["mvp_features"] = [f"기능{i}" for i in range(9)]
    r = client.post(
        "/api/trends/r1/ideas/prompt",
        json={"platform": "웹(Web MVP)", "type": "재미", "idea": sample_idea},
    )
    assert r.status_code == 400
    assert r.json()["detail"]["error_code"] == "invalid_input"


def test_rebuild_prompt_invalid_platform_is_400(client, sample_idea):
    r = client.post(
        "/api/trends/r1/ideas/prompt",
        json={"platform": "홀로그램", "type": "재미", "idea": sample_idea},
    )
    assert r.status_code == 400
    assert r.json()["detail"]["error_code"] == "invalid_input"


def test_rebuild_prompt_unknown_keyword_is_404(client, sample_idea):
    r = client.post(
        "/api/trends/no-such-id/ideas/prompt",
        json={"platform": "웹(Web MVP)", "type": "재미", "idea": sample_idea},
    )
    assert r.status_code == 404
    assert r.json()["detail"]["error_code"] == "keyword_not_found"


def test_rebuild_prompt_does_not_touch_cache(client, sample_idea):
    """재생성 후에도 GET /ideas 캐시는 LLM 원본 MVP를 유지한다."""
    original_mvp = list(sample_idea["mvp_features"])

    edited = dict(sample_idea)
    edited["mvp_features"] = ["완전히 다른 기능"]
    r = client.post(
        "/api/trends/r1/ideas/prompt",
        json={"platform": "웹(Web MVP)", "type": "재미", "idea": edited},
    )
    assert r.status_code == 200

    cached = client.get("/api/trends/r1/ideas", params={"platform": "웹(Web MVP)", "type": "재미"})
    assert cached.status_code == 200
    assert cached.json()["ideas"][0]["mvp_features"] == original_mvp
