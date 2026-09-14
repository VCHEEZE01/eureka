"""Gemini generateContent 계약. 모든 요청은 mock이며 실제 키를 쓰지 않는다."""

import json

import httpx
import pytest
import respx

from app.config.settings import settings
from app.core.llm import EchoLLM, GeminiLLMClient, LLMError, get_llm, reset_llm

URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent"


def response_body(text):
    return {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": text}]}}]}


@pytest.fixture(autouse=True)
def gemini_settings(monkeypatch):
    for name, value in {
        "LLM_PROVIDER": "gemini",
        "LLM_DRY_RUN": False,
        "GEMINI_API_KEY": "test-gemini-key",
        "GEMINI_MODEL": "gemini-3.5-flash-lite",
        "LLM_API_KEY": "test-potens-key",
        "LLM_BASE_URL": "https://unrelated.example.test/chat",
        "LLM_MODEL": "potens-model",
        "LLM_MODEL_JUDGE": "potens-judge",
        "LLM_AUTH_HEADER": "X-Potens-Key",
        "LLM_AUTH_SCHEME": "Potens",
        "LLM_REQUEST_STYLE": "raw_prompt",
        "LLM_RESPONSE_PATH": "data.result",
    }.items():
        monkeypatch.setattr(settings, name, value)
    reset_llm()
    yield
    reset_llm()


@respx.mock
def test_gemini_request_and_json_response_are_isolated_from_potens():
    usage = {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120}
    route = respx.post(URL).mock(return_value=httpx.Response(
        200, json={**response_body('[{"ok":true}]'),
                   "usageMetadata": {"promptTokenCount": 100, "candidatesTokenCount": 20, "totalTokenCount": 120}},
    ))
    client = get_llm()
    assert isinstance(client, GeminiLLMClient)
    assert client is get_llm()
    assert client.complete_json("JSON 배열로 답하라", max_tokens=200) == [{"ok": True}]
    request = route.calls.last.request
    assert request.headers["x-goog-api-key"] == "test-gemini-key"
    assert "Authorization" not in request.headers
    assert "X-Potens-Key" not in request.headers
    assert "test-potens-key" not in request.content.decode()
    body = json.loads(request.content)
    assert "_model" not in body
    assert body["generationConfig"]["maxOutputTokens"] == 200
    assert body["generationConfig"]["responseMimeType"] == "application/json"
    assert "thinkingConfig" not in body["generationConfig"]
    assert body["contents"] == [{"role": "user", "parts": [{"text": "JSON 배열로 답하라"}]}]
    assert client.complete("안녕").usage == usage


def test_gemini_dry_run_does_not_require_key(monkeypatch):
    monkeypatch.setattr(settings, "LLM_DRY_RUN", True)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    assert isinstance(get_llm(), EchoLLM)


@pytest.mark.parametrize("field", ["GEMINI_API_KEY", "GEMINI_MODEL"])
def test_gemini_missing_configuration_fails_without_falling_back(field, monkeypatch):
    monkeypatch.setattr(settings, field, "")
    with pytest.raises(LLMError, match="GEMINI_API_KEY / GEMINI_MODEL"):
        get_llm()


def test_gemini_judge_uses_only_gemini_model():
    assert settings.judge_model == "gemini-3.5-flash-lite"


def test_gemini_missing_keys_does_not_require_potens_configuration(monkeypatch):
    for name in ["LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL"]:
        monkeypatch.setattr(settings, name, "")
    assert not any(name.startswith("LLM_") for name in settings.missing_keys())
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    assert "GEMINI_API_KEY" in settings.missing_keys()


@respx.mock
def test_gemini_authentication_failure_is_not_retried():
    route = respx.post(URL).mock(return_value=httpx.Response(
        401, json={"error": {"message": "Invalid credentials"}},
    ))
    with pytest.raises(LLMError, match="401"):
        get_llm().complete("안녕")
    assert route.call_count == 1


@respx.mock
def test_gemini_invalid_json_is_retried_once():
    route = respx.post(URL).mock(side_effect=[
        httpx.Response(200, json=response_body("invalid")),
        httpx.Response(200, json=response_body("[]")),
    ])
    assert get_llm().complete_json("JSON 배열") == []
    assert route.call_count == 2


@pytest.mark.parametrize("body", [
    {}, {"candidates": []},
    {"candidates": [{"finishReason": "SAFETY"}]},
    {"candidates": [{"finishReason": "MAX_TOKENS"}]},
    response_body(""),
])
@respx.mock
def test_gemini_empty_or_incomplete_response_fails(body):
    respx.post(URL).mock(return_value=httpx.Response(200, json=body))
    with pytest.raises(LLMError):
        get_llm().complete("안녕")


@respx.mock
def test_gemini_system_instruction_and_model_override():
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    route = respx.post(url).mock(return_value=httpx.Response(200, json=response_body("안녕")))
    assert get_llm().complete("안녕", system="한국어로 답하라", model="gemini-2.5-flash").text == "안녕"
    body = json.loads(route.calls.last.request.content)
    assert body["systemInstruction"] == {"parts": [{"text": "한국어로 답하라"}]}
    assert body["generationConfig"]["thinkingConfig"] == {"thinkingBudget": 0}
