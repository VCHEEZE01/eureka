"""
LLM 클라이언트 — 모델을 실제로 호출하는 유일한 곳.

Gemini는 Google 기본 generateContent API를 사용한다. 게이트웨이 설정과 키를 섞지 않는다.
  https://ai.google.dev/api/generate-content
  LLM_PROVIDER=gemini · GEMINI_API_KEY · GEMINI_MODEL

★ 왜 이렇게 복잡한가
  우리 LLM 제공자는 "포텐스닷" 게이트웨이인데, 요청/응답 형식을 아직 아무도
  확정하지 못했다. 그래서 형식을 코드에 박지 않고 .env 로 고른다.

      LLM_REQUEST_STYLE = openai_chat | anthropic_messages | raw_prompt
      LLM_RESPONSE_PATH = 응답에서 텍스트를 꺼낼 점 경로 (예: data.message)

  스펙이 확인되면 .env 만 고치면 되고, 세 형식 중 어디에도 안 맞으면
  _build_body() / _extract_text() 두 함수에 분기를 하나 더 넣으면 된다.

★ LLM_BASE_URL 은 "요청을 POST 할 전체 엔드포인트 URL"이다.
  경로를 코드가 추측해서 붙이지 않는다 (게이트웨이 경로를 모르기 때문).

사용:
    from app.core.llm import get_llm
    text = get_llm().complete("안녕").text
    data = get_llm().complete_json(prompt)   # JSON 배열/객체로 파싱해서 반환

테스트:
    from app.core.llm import set_llm, reset_llm, EchoLLM
    set_llm(EchoLLM())   # 네트워크 없이 결정적으로 동작
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from typing import Any, Optional, Protocol, runtime_checkable
from urllib.parse import quote

import httpx
from pydantic import BaseModel

from app.config.settings import settings

# ── 상수 ────────────────────────────────────────

#: complete_json 이 1차 파싱에 실패했을 때 덧붙이는 문장.
JSON_RETRY_SUFFIX = (
    "\n\n---\n"
    "앞선 응답이 JSON 으로 읽히지 않았다. 설명·인사말·코드블록 표시 없이 "
    "JSON 값 하나만 출력하라."
)

#: raw_prompt 응답에서 LLM_RESPONSE_PATH 가 비었을 때 순서대로 시도할 키.
_COMMON_TEXT_KEYS = ("text", "message", "content", "output")

_FENCE_RE = re.compile(r"```(?:json|JSON)?\s*(.*?)\s*```", re.DOTALL)


# ── 반환 타입 ───────────────────────────────────


class LLMResponse(BaseModel):
    """모델 호출 1회의 결과."""

    text: str
    usage: Optional[dict] = None
    raw: Optional[dict] = None


class LLMError(RuntimeError):
    """LLM 호출·파싱 실패. 호출하는 쪽은 이것만 잡으면 된다."""


@runtime_checkable
class LLMClient(Protocol):
    """에이전트들이 의존하는 계약. 구현체는 EchoLLM / HTTPLLMClient."""

    def complete(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.0,
    ) -> LLMResponse: ...

    def complete_json(self, prompt: str, **kw: Any) -> Any: ...


# ── 요청 본문 만들기 ────────────────────────────


def _clean(value: str) -> str:
    """
    설정 문자열을 정리한다.

    ★ .env 에 "LLM_MODEL=            # 설명" 처럼 값이 비고 주석만 있으면
      python-dotenv 가 주석을 값으로 읽어 온다. 그대로 두면 모델 이름이나
      응답 경로 자리에 "# 설명" 이 들어가서 원인을 찾기 어려운 실패가 난다.
      여기서 빈 값으로 되돌린다. (.env 자체는 다른 담당자 소유라 건드리지 않는다.)
    """
    v = (value or "").strip()
    return "" if v.startswith("#") else v


def _build_body(
    style: str,
    *,
    prompt: str,
    system: Optional[str],
    model: str,
    max_tokens: int,
    temperature: float,
) -> dict:
    """세 가지 요청 형식 중 하나로 본문을 만든다."""
    if style == "openai_chat":
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

    if style == "anthropic_messages":
        body: dict = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system:
            body["system"] = system
        return body

    if style == "raw_prompt":
        # 게이트웨이가 단순 프록시일 때. 모델·옵션을 받지 않으므로
        # system 은 프롬프트 앞에 붙여서 한 덩어리로 넘긴다.
        text = f"{system}\n\n---\n\n{prompt}" if system else prompt
        return {"prompt": text}

    raise LLMError(f"모르는 LLM_REQUEST_STYLE: {style!r}")


# ── 응답에서 텍스트 꺼내기 ──────────────────────


def _dot_get(data: Any, path: str) -> Any:
    """'data.message' 같은 점 경로를 따라간다. 없으면 None."""
    cur = data
    for part in path.split("."):
        if not part:
            continue
        if isinstance(cur, list):
            # 경로 중간에 리스트가 오면 숫자 인덱스로 해석한다.
            if not part.lstrip("-").isdigit():
                return None
            idx = int(part)
            if not -len(cur) <= idx < len(cur):
                return None
            cur = cur[idx]
            continue
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _extract_text(style: str, data: Any, response_path: str = "") -> str:
    """응답 JSON 에서 모델이 쓴 텍스트만 꺼낸다."""
    # 점 경로가 지정돼 있으면 형식과 무관하게 그게 우선이다.
    # (게이트웨이가 표준 응답을 한 번 더 감싸는 경우가 있다.)
    if response_path:
        found = _dot_get(data, response_path)
        if isinstance(found, str) and found:
            return found
        if style == "raw_prompt":
            raise LLMError(
                f"LLM_RESPONSE_PATH={response_path!r} 경로에서 텍스트를 찾지 못했다. "
                f"응답 키: {sorted(data) if isinstance(data, dict) else type(data).__name__}"
            )

    if style == "openai_chat":
        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise LLMError(f"openai_chat 응답 형식이 아니다: {e}. 원본={_head(data)}") from e
        if not isinstance(text, str):
            raise LLMError(f"openai_chat content 가 문자열이 아니다: {_head(data)}")
        return text

    if style == "anthropic_messages":
        try:
            text = data["content"][0]["text"]
        except (KeyError, IndexError, TypeError) as e:
            raise LLMError(
                f"anthropic_messages 응답 형식이 아니다: {e}. 원본={_head(data)}"
            ) from e
        if not isinstance(text, str):
            raise LLMError(f"anthropic_messages text 가 문자열이 아니다: {_head(data)}")
        return text

    if style == "raw_prompt":
        if isinstance(data, str):
            return data
        if isinstance(data, dict):
            for key in _COMMON_TEXT_KEYS:
                val = data.get(key)
                if isinstance(val, str) and val:
                    return val
        raise LLMError(
            "raw_prompt 응답에서 텍스트를 찾지 못했다. "
            f"LLM_RESPONSE_PATH 를 지정하라. 응답 키="
            f"{sorted(data) if isinstance(data, dict) else type(data).__name__}"
        )

    raise LLMError(f"모르는 LLM_REQUEST_STYLE: {style!r}")


def _head(data: Any, limit: int = 200) -> str:
    """에러 메시지에 붙일 응답 앞부분."""
    try:
        s = json.dumps(data, ensure_ascii=False)
    except (TypeError, ValueError):
        s = repr(data)
    return s[:limit]


# ── JSON 파싱 ───────────────────────────────────


def strip_code_fence(text: str) -> str:
    """```json ... ``` 코드펜스를 벗긴다. 없으면 그대로."""
    m = _FENCE_RE.search(text)
    return m.group(1) if m else text.strip()


def _loads_loose(text: str) -> Any:
    """코드펜스를 벗기고 JSON 으로 읽는다. 앞뒤 잡담이 붙어 있어도 건져낸다."""
    body = strip_code_fence(text)
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        pass
    # 앞뒤에 설명이 붙은 경우: 첫 여는 괄호 ~ 마지막 닫는 괄호만 잘라 본다.
    for opener, closer in (("[", "]"), ("{", "}")):
        start, end = body.find(opener), body.rfind(closer)
        if 0 <= start < end:
            try:
                return json.loads(body[start : end + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError("JSON 으로 읽을 수 없다")


# ── 공통 구현 ───────────────────────────────────


class _BaseLLM:
    """complete_json 처럼 구현체가 공유하는 부분."""

    def complete(  # pragma: no cover - 하위 클래스가 채운다
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.0,
    ) -> LLMResponse:
        raise NotImplementedError

    def complete_json(self, prompt: str, **kw: Any) -> Any:
        """
        JSON 을 기대하는 호출. 실패하면 "JSON 만 출력하라"를 붙여 1회만 재시도한다.

        두 번 다 실패하면 LLMError. 호출하는 쪽에서 반쪽짜리 문자열을
        파싱하려 애쓰지 않게 하려는 것이다.
        """
        first = self.complete(prompt, **kw)
        try:
            return _loads_loose(first.text)
        except ValueError:
            pass

        second = self.complete(prompt + JSON_RETRY_SUFFIX, **kw)
        try:
            return _loads_loose(second.text)
        except ValueError as e:
            raise LLMError(
                f"두 번 시도했지만 JSON 으로 읽지 못했다: {e}. "
                f"마지막 응답 앞부분={second.text[:200]!r}"
            ) from e


# ── 실제 호출 ───────────────────────────────────


class HTTPLLMClient(_BaseLLM):
    """
    포텐스닷 게이트웨이를 httpx 로 부른다.

    설정은 생성 시점에 스냅샷한다 — 테스트에서 인자로 직접 넣을 수 있게.
    """

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        request_style: Optional[str] = None,
        response_path: Optional[str] = None,
        auth_header: Optional[str] = None,
        auth_scheme: Optional[str] = None,
        timeout_sec: Optional[int] = None,
        max_retries: Optional[int] = None,
        client: Optional[httpx.Client] = None,
        sleep: Any = None,
    ) -> None:
        self.base_url = _clean(base_url if base_url is not None else settings.LLM_BASE_URL)
        self.api_key = _clean(api_key if api_key is not None else settings.LLM_API_KEY)
        self.model = _clean(model if model is not None else settings.LLM_MODEL)
        self.request_style = (
            request_style if request_style is not None else settings.LLM_REQUEST_STYLE
        )
        self.response_path = _clean(
            response_path if response_path is not None else settings.LLM_RESPONSE_PATH
        )
        self.auth_header = _clean(
            auth_header if auth_header is not None else settings.LLM_AUTH_HEADER
        ) or "Authorization"
        self.auth_scheme = _clean(
            auth_scheme if auth_scheme is not None else settings.LLM_AUTH_SCHEME
        )
        self.timeout_sec = (
            timeout_sec if timeout_sec is not None else settings.LLM_TIMEOUT_SEC
        )
        self.max_retries = (
            max_retries if max_retries is not None else settings.LLM_MAX_RETRIES
        )
        self._client = client
        self._sleep = sleep or time.sleep

        if not self.base_url:
            raise LLMError(
                "LLM_BASE_URL 이 비어 있다. .env 에 포텐스닷 엔드포인트 전체 URL을 넣거나, "
                "네트워크 없이 돌리려면 LLM_DRY_RUN=true 로 두어라."
            )

    # 헤더 ------------------------------------------------

    def headers(self) -> dict:
        """인증 헤더. LLM_AUTH_SCHEME 이 비면 키를 그대로 넣는다."""
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h[self.auth_header] = f"{self.auth_scheme} {self.api_key}".strip()
        return h

    # 호출 ------------------------------------------------

    def complete(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.0,
    ) -> LLMResponse:
        body = _build_body(
            self.request_style,
            prompt=prompt,
            system=system,
            model=model or self.model,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        data = self._post_with_retry(body)
        text = _extract_text(self.request_style, data, self.response_path)
        usage = data.get("usage") if isinstance(data, dict) else None
        return LLMResponse(
            text=text,
            usage=usage if isinstance(usage, dict) else None,
            raw=data if isinstance(data, dict) else {"_": data},
        )

    def _post_with_retry(self, body: dict) -> Any:
        """429·5xx·네트워크 오류는 지수 백오프로 재시도. 그 외 4xx 는 즉시 실패."""
        last = "이유 미상"
        for attempt in range(self.max_retries + 1):
            try:
                res = self._send(body)
            except httpx.RequestError as e:  # 타임아웃·연결 실패
                last = f"네트워크 오류: {e}"
            else:
                if res.status_code < 400:
                    try:
                        return res.json()
                    except ValueError as e:
                        raise LLMError(
                            f"응답이 JSON 이 아니다: {e}. 앞부분={res.text[:200]!r}"
                        ) from e
                if res.status_code != 429 and res.status_code < 500:
                    raise LLMError(
                        f"LLM 요청 거부 {res.status_code}: {res.text[:200]}"
                    )
                last = f"HTTP {res.status_code}: {res.text[:200]}"

            if attempt < self.max_retries:
                self._sleep(0.5 * (2**attempt))

        raise LLMError(f"{self.max_retries + 1}회 시도 모두 실패했다 — {last}")

    def _send(self, body: dict) -> httpx.Response:
        if self._client is not None:
            return self._client.post(
                self.base_url, json=body, headers=self.headers(), timeout=self.timeout_sec
            )
        with httpx.Client(timeout=self.timeout_sec) as client:
            return client.post(self.base_url, json=body, headers=self.headers())


class GeminiLLMClient(HTTPLLMClient):
    """Google의 고정 주소로만 전송. 포텐스닷 키·URL·응답 경로는 사용하지 않는다."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self) -> None:
        key = _clean(settings.GEMINI_API_KEY)
        model = _clean(settings.GEMINI_MODEL)
        if not key or not model:
            raise LLMError("GEMINI_API_KEY / GEMINI_MODEL 설정을 확인하라.")
        super().__init__(
            base_url=f"{self.BASE_URL}/{quote(model, safe='')}:generateContent",
            api_key=key,
            model=model,
            request_style="openai_chat",
            response_path="",
            auth_header="x-goog-api-key",
            auth_scheme="",
        )

    def complete(
        self, prompt: str, *, system: Optional[str] = None,
        model: Optional[str] = None, max_tokens: int = 2000,
        temperature: float = 0.0, json_mode: bool = False,
    ) -> LLMResponse:
        selected = _clean(model or self.model)
        config: dict = {"maxOutputTokens": max_tokens, "temperature": temperature}
        # 2.5 Flash/Lite에서는 단순 판별의 추가 추론 비용을 끈다.
        if selected.startswith("gemini-2.5-flash"):
            config["thinkingConfig"] = {"thinkingBudget": 0}
        if json_mode:
            config["responseMimeType"] = "application/json"
        body: dict = {
            "_model": selected,  # _send에서 경로로 옮긴다. 요청 본문에는 포함하지 않는다.
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": config,
        }
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        data = self._post_with_retry(body)
        try:
            candidate = data["candidates"][0]
            if candidate.get("finishReason") not in (None, "STOP"):
                raise LLMError("Gemini 응답이 정상 완료되지 않았다 (차단 또는 출력 한도 확인).")
            parts = candidate["content"]["parts"]
            text = "".join(
                part["text"] for part in parts
                if isinstance(part, dict) and isinstance(part.get("text"), str)
                and not part.get("thought", False)
            )
            if not text:
                raise LLMError("Gemini 텍스트 응답이 비어 있다.")
        except (KeyError, IndexError, TypeError, AttributeError) as exc:
            raise LLMError("Gemini 텍스트 응답이 없다. 안전 필터 또는 응답 형식을 확인하라.") from exc
        usage = data.get("usageMetadata")
        normalized = None
        if isinstance(usage, dict):
            normalized = {
                "prompt_tokens": usage.get("promptTokenCount", 0),
                "completion_tokens": usage.get("candidatesTokenCount", 0) + usage.get("thoughtsTokenCount", 0),
                "total_tokens": usage.get("totalTokenCount", 0),
            }
        return LLMResponse(text=text, usage=normalized, raw=data)

    def complete_json(self, prompt: str, **kw: Any) -> Any:
        kw["json_mode"] = True
        return super().complete_json(prompt, **kw)

    def _send(self, body: dict) -> httpx.Response:
        payload = dict(body)
        model = payload.pop("_model")
        url = f"{self.BASE_URL}/{quote(model, safe='')}:generateContent"
        if self._client is not None:
            return self._client.post(url, json=payload, headers=self.headers(), timeout=self.timeout_sec)
        with httpx.Client(timeout=self.timeout_sec) as client:
            return client.post(url, json=payload, headers=self.headers())


# ── 오프라인용 ──────────────────────────────────


class EchoLLM(_BaseLLM):
    """
    네트워크를 부르지 않는 가짜 모델 (LLM_DRY_RUN=true).

    ★ 결정적이다 — 같은 프롬프트면 항상 같은 응답. 테스트가 흔들리지 않는다.
    ★ 프롬프트에 id 가 들어 있는 JSON 배열이 보이면 그 id들로 판정 배열을
      만들어 돌려준다. judge_pains 배선을 오프라인에서 검증하기 위한 것이다.
      ※ 내용은 해시로 만든 가짜다. 판정 품질을 여기서 보지 마라.
    """

    _ID_RE = re.compile(r'"id"\s*:\s*"([^"]+)"')
    # 프롬프트 안의 출력 예시("id": "...")까지 주워 담지 않기 위한 거름망.
    _PLACEHOLDER_ID = re.compile(r"^[.\u2026\s_-]*$")
    _LABELS = ("높음", "중간", "낮음")

    def complete(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.0,
    ) -> LLMResponse:
        ids = self._real_ids(prompt)
        if ids:
            text = json.dumps(
                [self._fake_judgement(i) for i in ids], ensure_ascii=False
            )
        elif self._wants_json(prompt):
            text = "[]"
        else:
            digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]
            text = f"[echo:{digest}] 실제 모델을 부르지 않았다 (LLM_DRY_RUN)."
        return LLMResponse(text=text, usage=None, raw={"echo": True})

    @classmethod
    def _real_ids(cls, prompt: str) -> list[str]:
        """프롬프트에서 판정 대상 id 만 뽑는다. 예시용 자리표시자와 중복은 뺀다."""
        out: list[str] = []
        for found in cls._ID_RE.findall(prompt):
            if cls._PLACEHOLDER_ID.match(found) or found in out:
                continue
            out.append(found)
        return out

    @staticmethod
    def _wants_json(prompt: str) -> bool:
        return "JSON" in prompt or "json" in prompt

    @classmethod
    def _fake_judgement(cls, item_id: str) -> dict:
        h = int(hashlib.sha256(item_id.encode("utf-8")).hexdigest()[:8], 16)
        is_pain = h % 3 != 0  # 셋 중 둘은 불편으로 본다
        return {
            "id": item_id,
            "is_pain": is_pain,
            "pain_summary": f"에코 요약: {item_id} 글에서 겪는 불편" if is_pain else None,
            "confidence": cls._LABELS[h % 3],
            "severity": cls._LABELS[(h >> 4) % 3] if is_pain else None,
            "has_need_signal": bool((h >> 8) % 2),
        }


# ── 싱글턴 ──────────────────────────────────────

_client: Optional[LLMClient] = None


def get_llm() -> LLMClient:
    """
    설정에 맞는 클라이언트를 돌려준다. 한 번 만들면 재사용한다.

    LLM_DRY_RUN=true 이거나 LLM_PROVIDER=echo 면 EchoLLM (네트워크 없음).
    """
    global _client
    if _client is None:
        if settings.LLM_DRY_RUN or settings.LLM_PROVIDER == "echo":
            _client = EchoLLM()
        elif settings.LLM_PROVIDER == "gemini":
            _client = GeminiLLMClient()
        else:
            _client = HTTPLLMClient()
    return _client


def set_llm(client: LLMClient) -> None:
    """테스트 주입점. 가짜 클라이언트를 끼운다."""
    global _client
    _client = client


def reset_llm() -> None:
    """다음 get_llm() 이 설정을 다시 읽게 한다."""
    global _client
    _client = None


# ── 손으로 한 번 찔러보기 ───────────────────────


def _ping(prompt: str) -> int:
    """왕복 1회. 설정이 맞는지 눈으로 확인하는 용도."""
    gemini = settings.LLM_PROVIDER == "gemini"
    key = _clean(settings.GEMINI_API_KEY if gemini else settings.LLM_API_KEY)
    print(
        f"provider={settings.LLM_PROVIDER} dry_run={settings.LLM_DRY_RUN} "
        f"model={settings.judge_model or '(없음)'} "
        f"key_configured={bool(key)}"
    )
    reset_llm()
    try:
        res = get_llm().complete(prompt, max_tokens=200)
    except LLMError as e:
        print(f"실패: {e}")
        return 1
    print(f"--- 응답 ---\n{res.text}")
    if res.usage:
        print(f"usage={res.usage}")
    return 0


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="LLM 설정 확인용 왕복 1회")
    parser.add_argument("--ping", action="store_true", help="한 번 호출해 본다")
    parser.add_argument("--prompt", default="한 문장으로 자기소개를 해라.")
    args = parser.parse_args()
    if not args.ping:
        parser.print_help()
        sys.exit(0)
    sys.exit(_ping(args.prompt))
