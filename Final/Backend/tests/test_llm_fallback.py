"""Gemini 1차 → 실패 시 포텐스닷 2차 자동 전환. 모든 요청은 mock이며 실제 키를 쓰지 않는다."""

import json

import httpx
import pytest
import respx

from app.config.settings import settings
from app.core.llm import FallbackLLMClient, GeminiLLMClient, LLMError, get_llm, reset_llm

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent"
POTENS_URL = "https://ai.potens.ai/api/chat"


def gemini_body(text):
    return {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": text}]}}]}


@pytest.fixture(autouse=True)
def llm_settings(monkeypatch):
    for name, value in {
        "LLM_PROVIDER": "gemini",
        "LLM_DRY_RUN": False,
        "GEMINI_API_KEY": "test-gemini-key",
        "GEMINI_MODEL": "gemini-3.5-flash-lite",
        "LLM_MAX_RETRIES": 0,
        "POTENS_API_KEY": "test-potens-key",
        "POTENS_BASE_URL": "https://ai.potens.ai",
        "POTENS_MODEL": "claude-4-6-sonnet",
    }.items():
        monkeypatch.setattr(settings, name, value)
    reset_llm()
    yield
    reset_llm()


@respx.mock
def test_gemini_success_never_touches_potens():
    respx.post(GEMINI_URL).mock(return_value=httpx.Response(200, json=gemini_body("안녕")))
    potens_route = respx.post(POTENS_URL).mock(return_value=httpx.Response(200, json={"message": "백업 응답"}))

    client = get_llm()
    assert isinstance(client, FallbackLLMClient)
    assert client.complete("안녕").text == "안녕"
    assert potens_route.call_count == 0


@respx.mock
def test_gemini_failure_falls_back_to_potens():
    respx.post(GEMINI_URL).mock(return_value=httpx.Response(500, json={"error": "quota exceeded"}))
    respx.post(POTENS_URL).mock(return_value=httpx.Response(200, json={"message": "백업 응답", "token_usage": {}}))

    result = get_llm().complete("안녕")
    assert result.text == "백업 응답"


@respx.mock
def test_potens_request_shape_matches_docs():
    respx.post(GEMINI_URL).mock(return_value=httpx.Response(429, json={"error": "quota exceeded"}))
    route = respx.post(POTENS_URL).mock(return_value=httpx.Response(200, json={"message": "ok"}))

    get_llm().complete("프롬프트", system="시스템")

    request = route.calls.last.request
    assert request.headers["Authorization"] == "Bearer test-potens-key"
    body = json.loads(request.content)
    assert body["model"] == "claude-4-6-sonnet"
    assert "프롬프트" in body["prompt"]
    assert "시스템" in body["prompt"]


@respx.mock
def test_both_providers_failing_raises():
    respx.post(GEMINI_URL).mock(return_value=httpx.Response(500, json={"error": "down"}))
    respx.post(POTENS_URL).mock(return_value=httpx.Response(500, json={"error": "down"}))

    with pytest.raises(LLMError):
        get_llm().complete("안녕")


@respx.mock
def test_complete_json_falls_back_after_gemini_exhausts_retries():
    respx.post(GEMINI_URL).mock(return_value=httpx.Response(200, json=gemini_body("이건 JSON이 아니다")))
    respx.post(POTENS_URL).mock(return_value=httpx.Response(200, json={"message": "[1, 2, 3]"}))

    assert get_llm().complete_json("JSON 배열로 답하라") == [1, 2, 3]


def test_no_potens_key_means_no_fallback_wrapper(monkeypatch):
    monkeypatch.setattr(settings, "POTENS_API_KEY", "")
    client = get_llm()
    assert isinstance(client, GeminiLLMClient)
    assert not isinstance(client, FallbackLLMClient)
