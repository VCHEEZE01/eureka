"""
LLM 어댑터 테스트.

★ 절대 네트워크를 부르지 않는다. httpx 는 respx 로 막고, 나머지는 EchoLLM 을 쓴다.
★ 포텐스닷 스펙이 아직 확정되지 않았으므로, 여기서 검증하는 것은
  "세 가지 요청/응답 형식을 .env 로 갈아끼울 수 있는가" 다.
"""

import importlib
import json
import pkgutil

import httpx
import pytest
import respx

import app.prompts
from app.config.settings import settings
from app.core.llm import (
    EchoLLM,
    HTTPLLMClient,
    LLMError,
    LLMResponse,
    _BaseLLM,
    _build_body,
    _extract_text,
    get_llm,
    reset_llm,
    set_llm,
    strip_code_fence,
)
from app.prompts.collector_prompts import SUGGEST_DOMAIN_KEYWORDS
from app.prompts.common_prompts import COMMON_RULES
from app.prompts.interpreter_prompts import JUDGE_PAINS

URL = "https://gateway.example.test/v1/chat"


def make_client(**kw) -> HTTPLLMClient:
    """설정 파일과 무관하게, 인자로 못 박은 클라이언트."""
    kw.setdefault("base_url", URL)
    kw.setdefault("api_key", "KEY123")
    kw.setdefault("model", "test-model")
    kw.setdefault("request_style", "openai_chat")
    kw.setdefault("response_path", "")
    kw.setdefault("auth_header", "Authorization")
    kw.setdefault("auth_scheme", "Bearer")
    kw.setdefault("max_retries", 2)
    kw.setdefault("sleep", lambda _sec: None)  # 테스트가 기다리지 않게
    return HTTPLLMClient(**kw)


@pytest.fixture(autouse=True)
def _clean_singleton():
    reset_llm()
    yield
    reset_llm()


# ── 요청 본문 ───────────────────────────────────


def test_body_openai_chat():
    body = _build_body(
        "openai_chat",
        prompt="안녕",
        system="너는 판별기다",
        model="m1",
        max_tokens=100,
        temperature=0.0,
    )
    assert body == {
        "model": "m1",
        "messages": [
            {"role": "system", "content": "너는 판별기다"},
            {"role": "user", "content": "안녕"},
        ],
        "max_tokens": 100,
        "temperature": 0.0,
    }


def test_body_openai_chat_without_system():
    body = _build_body(
        "openai_chat", prompt="안녕", system=None, model="m1", max_tokens=10, temperature=0.2
    )
    assert body["messages"] == [{"role": "user", "content": "안녕"}]


def test_body_anthropic_messages():
    body = _build_body(
        "anthropic_messages",
        prompt="안녕",
        system="너는 판별기다",
        model="m1",
        max_tokens=100,
        temperature=0.0,
    )
    assert body == {
        "model": "m1",
        "system": "너는 판별기다",
        "messages": [{"role": "user", "content": "안녕"}],
        "max_tokens": 100,
        "temperature": 0.0,
    }


def test_body_raw_prompt_merges_system():
    body = _build_body(
        "raw_prompt",
        prompt="안녕",
        system="너는 판별기다",
        model="m1",
        max_tokens=100,
        temperature=0.0,
    )
    assert list(body) == ["prompt"]
    assert body["prompt"].startswith("너는 판별기다")
    assert body["prompt"].endswith("안녕")


def test_body_unknown_style():
    with pytest.raises(LLMError):
        _build_body(
            "grpc", prompt="x", system=None, model="m", max_tokens=1, temperature=0.0
        )


# ── 응답 파싱 ───────────────────────────────────


def test_extract_openai():
    data = {"choices": [{"message": {"content": "결과"}}]}
    assert _extract_text("openai_chat", data) == "결과"


def test_extract_anthropic():
    data = {"content": [{"text": "결과"}]}
    assert _extract_text("anthropic_messages", data) == "결과"


def test_extract_raw_common_keys():
    assert _extract_text("raw_prompt", {"message": "결과"}) == "결과"
    assert _extract_text("raw_prompt", {"output": "결과"}) == "결과"


def test_extract_raw_dot_path():
    data = {"data": {"message": "결과"}}
    assert _extract_text("raw_prompt", data, "data.message") == "결과"


def test_extract_dot_path_with_list_index():
    data = {"result": [{"text": "결과"}]}
    assert _extract_text("raw_prompt", data, "result.0.text") == "결과"


def test_extract_dot_path_wrong_path_raises():
    with pytest.raises(LLMError) as e:
        _extract_text("raw_prompt", {"data": {"message": "결과"}}, "data.nope")
    assert "data.nope" in str(e.value)


def test_extract_raw_without_known_key_raises():
    with pytest.raises(LLMError):
        _extract_text("raw_prompt", {"이상한키": "결과"})


def test_extract_openai_malformed_raises():
    with pytest.raises(LLMError):
        _extract_text("openai_chat", {"choices": []})


def test_dot_path_wins_over_style_shape():
    """게이트웨이가 표준 응답을 한 번 더 감쌌을 때."""
    data = {"data": {"choices": [{"message": {"content": "결과"}}]}}
    assert _extract_text("openai_chat", data, "data.choices.0.message.content") == "결과"


# ── 인증 헤더 ───────────────────────────────────


def test_auth_header_with_scheme():
    h = make_client().headers()
    assert h["Authorization"] == "Bearer KEY123"


def test_auth_header_empty_scheme_uses_bare_key():
    h = make_client(auth_scheme="").headers()
    assert h["Authorization"] == "KEY123"


def test_auth_header_custom_name():
    h = make_client(auth_header="X-API-KEY", auth_scheme="").headers()
    assert h["X-API-KEY"] == "KEY123"
    assert "Authorization" not in h


def test_env_comment_only_value_is_treated_as_empty():
    """.env 에 값 없이 주석만 있으면 python-dotenv 가 주석을 값으로 읽어 온다."""
    client = make_client(
        model="# Claude Opus 계열 모델 식별자",
        response_path="# raw_prompt일 때 응답 본문 경로",
        auth_scheme="# 빈 문자열이면 키를 그대로",
    )
    assert client.model == ""
    assert client.response_path == ""
    assert client.headers()["Authorization"] == "KEY123"


def test_auth_header_omitted_without_key():
    h = make_client(api_key="").headers()
    assert "Authorization" not in h


# ── 실제 호출 (respx 로 막는다) ─────────────────


@respx.mock
def test_complete_openai_roundtrip():
    route = respx.post(URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "안녕하세요"}}],
                "usage": {"total_tokens": 7},
            },
        )
    )
    res = make_client().complete("안녕", system="시스템")
    assert isinstance(res, LLMResponse)
    assert res.text == "안녕하세요"
    assert res.usage == {"total_tokens": 7}
    sent = json.loads(route.calls.last.request.content)
    assert sent["model"] == "test-model"
    assert sent["messages"][0]["role"] == "system"
    assert route.calls.last.request.headers["authorization"] == "Bearer KEY123"


@respx.mock
def test_complete_raw_prompt_with_response_path():
    respx.post(URL).mock(
        return_value=httpx.Response(200, json={"data": {"message": "결과"}})
    )
    client = make_client(request_style="raw_prompt", response_path="data.message")
    assert client.complete("안녕").text == "결과"


@respx.mock
def test_retry_on_429_then_success():
    route = respx.post(URL).mock(
        side_effect=[
            httpx.Response(429, text="rate limited"),
            httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]}),
        ]
    )
    assert make_client().complete("안녕").text == "ok"
    assert route.call_count == 2


@respx.mock
def test_retry_exhausted_raises():
    route = respx.post(URL).mock(return_value=httpx.Response(503, text="down"))
    with pytest.raises(LLMError):
        make_client(max_retries=1).complete("안녕")
    assert route.call_count == 2  # 최초 1회 + 재시도 1회


@respx.mock
def test_4xx_fails_immediately():
    route = respx.post(URL).mock(return_value=httpx.Response(401, text="no auth"))
    with pytest.raises(LLMError) as e:
        make_client().complete("안녕")
    assert "401" in str(e.value)
    assert route.call_count == 1  # 재시도하지 않는다


@respx.mock
def test_network_error_is_retried():
    route = respx.post(URL).mock(
        side_effect=[
            httpx.ConnectTimeout("timeout"),
            httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]}),
        ]
    )
    assert make_client().complete("안녕").text == "ok"
    assert route.call_count == 2


@respx.mock
def test_non_json_response_raises():
    respx.post(URL).mock(return_value=httpx.Response(200, text="<html>웹페이지</html>"))
    with pytest.raises(LLMError):
        make_client().complete("안녕")


# ── JSON 파싱 ───────────────────────────────────


class FakeLLM(_BaseLLM):
    """정해진 텍스트를 순서대로 뱉는 가짜. 프롬프트를 기록한다."""

    def __init__(self, texts: list[str]):
        self.texts = list(texts)
        self.prompts: list[str] = []

    def complete(self, prompt, **kw) -> LLMResponse:
        self.prompts.append(prompt)
        return LLMResponse(text=self.texts.pop(0) if self.texts else "")


def test_strip_code_fence():
    assert strip_code_fence('```json\n[{"a": 1}]\n```') == '[{"a": 1}]'
    assert strip_code_fence('```\n{"a": 1}\n```') == '{"a": 1}'
    assert strip_code_fence('  {"a": 1}  ') == '{"a": 1}'


def test_complete_json_strips_fence():
    llm = FakeLLM(['```json\n[{"id": "a"}]\n```'])
    assert llm.complete_json("아무거나") == [{"id": "a"}]
    assert len(llm.prompts) == 1


def test_complete_json_ignores_surrounding_chatter():
    llm = FakeLLM(['알겠습니다. 결과는 다음과 같습니다:\n[{"id": "a"}]\n감사합니다.'])
    assert llm.complete_json("아무거나") == [{"id": "a"}]


def test_complete_json_retries_once_then_succeeds():
    llm = FakeLLM(["JSON 이 아닌 잡담", '[{"id": "a"}]'])
    assert llm.complete_json("판정해라") == [{"id": "a"}]
    assert len(llm.prompts) == 2
    assert "JSON" in llm.prompts[1] and llm.prompts[1].startswith("판정해라")


def test_complete_json_raises_after_retry():
    llm = FakeLLM(["잡담", "또 잡담"])
    with pytest.raises(LLMError):
        llm.complete_json("판정해라")
    assert len(llm.prompts) == 2  # 재시도는 딱 1회


# ── EchoLLM ─────────────────────────────────────


def test_echo_is_deterministic():
    a, b = EchoLLM(), EchoLLM()
    assert a.complete("같은 프롬프트").text == b.complete("같은 프롬프트").text
    assert a.complete("다른 프롬프트").text != a.complete("같은 프롬프트").text


def test_echo_builds_judgements_for_ids():
    items = json.dumps(
        [
            {"id": "r1", "title": "t1", "text": "본문1", "source": "블로그"},
            {"id": "r2", "title": "t2", "text": "본문2", "source": "뉴스"},
        ],
        ensure_ascii=False,
    )
    out = EchoLLM().complete_json(JUDGE_PAINS.replace("{items}", items))
    assert [j["id"] for j in out] == ["r1", "r2"]
    for j in out:
        assert isinstance(j["is_pain"], bool)
        assert j["confidence"] in ("높음", "중간", "낮음")
        assert j["severity"] in ("높음", "중간", "낮음", None)
        assert isinstance(j["has_need_signal"], bool)
        assert (j["pain_summary"] is None) is (not j["is_pain"])


def test_echo_returns_empty_array_when_no_ids():
    assert EchoLLM().complete_json("JSON 배열로만 답하라") == []


# ── get_llm ─────────────────────────────────────


def test_get_llm_returns_echo_on_dry_run(monkeypatch):
    monkeypatch.setattr(settings, "LLM_DRY_RUN", True)
    assert isinstance(get_llm(), EchoLLM)
    assert get_llm() is get_llm()  # 싱글턴


def test_get_llm_returns_echo_for_echo_provider(monkeypatch):
    monkeypatch.setattr(settings, "LLM_DRY_RUN", False)
    monkeypatch.setattr(settings, "LLM_PROVIDER", "echo")
    assert isinstance(get_llm(), EchoLLM)


def test_get_llm_without_base_url_raises(monkeypatch):
    monkeypatch.setattr(settings, "LLM_DRY_RUN", False)
    monkeypatch.setattr(settings, "LLM_PROVIDER", "potens")
    monkeypatch.setattr(settings, "LLM_BASE_URL", "")
    with pytest.raises(LLMError) as e:
        get_llm()
    assert "LLM_BASE_URL" in str(e.value)


def test_get_llm_builds_http_client(monkeypatch):
    monkeypatch.setattr(settings, "LLM_DRY_RUN", False)
    monkeypatch.setattr(settings, "LLM_PROVIDER", "potens")
    monkeypatch.setattr(settings, "LLM_BASE_URL", URL)
    assert isinstance(get_llm(), HTTPLLMClient)


def test_set_and_reset_llm(monkeypatch):
    monkeypatch.setattr(settings, "LLM_DRY_RUN", True)
    fake = FakeLLM(["x"])
    set_llm(fake)
    assert get_llm() is fake
    reset_llm()
    assert isinstance(get_llm(), EchoLLM)


# ── 프롬프트 ────────────────────────────────────


def _prompt_constants():
    """app/prompts 의 모든 모듈에서 대문자 문자열 상수를 모은다."""
    found = []
    for mod_info in pkgutil.iter_modules(app.prompts.__path__):
        if mod_info.name == "common_prompts":
            continue
        mod = importlib.import_module(f"app.prompts.{mod_info.name}")
        for name, value in vars(mod).items():
            if name.isupper() and isinstance(value, str):
                found.append((mod_info.name, name, value))
    return found


def test_every_prompt_constant_inherits_common_rules():
    for mod_name, name, value in _prompt_constants():
        assert COMMON_RULES in value, (
            f"{mod_name}.{name} 이 with_rules() 로 감싸이지 않았다"
        )


def test_judge_pains_prompt_has_required_instructions():
    for must in (
        "{items}",
        "is_pain",
        "pain_summary",
        "confidence",
        "severity",
        "has_need_signal",
        "80자",
        "광고",
        "반어",
    ):
        assert must in JUDGE_PAINS, f"JUDGE_PAINS 에 {must} 가 없다"


def test_suggest_keywords_prompt_has_placeholders():
    assert "{category}" in SUGGEST_DOMAIN_KEYWORDS
    assert "{existing}" in SUGGEST_DOMAIN_KEYWORDS
    assert "keyword" in SUGGEST_DOMAIN_KEYWORDS
