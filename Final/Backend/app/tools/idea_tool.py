"""
④ 아이디어 생성기 전용 도구 — LLM 호출과 스냅샷 읽기를 여기서만 한다.

★ app/tools/llm_tool.py 를 건드리지 않는 이유: 그 파일은 ②③ 담당자와
  공유하는 파일이고 v0 Idea/Problem 스키마를 쓴다. v1 아이디어 생성은
  입출력이 다르므로 여기 새 파일에 둔다 (app/trends/ 가 기존 tools/를
  건드리지 않은 것과 같은 이유).

  app/agents/base.py:8 규칙 — "에이전트 안에서 외부 API·DB를 직접
  부르지 않는다. tools/ 를 거친다." IdeaAgent는 이 파일만 통해
  app.core.llm 과 data/trends 스냅샷을 만난다.
"""

import json
import logging
import time
from pathlib import Path

from app.config.settings import settings
from app.core.llm import LLMError, get_llm

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
LATEST_SNAPSHOT_PATH = _BACKEND_ROOT / "data" / "trends" / "latest_snapshot.json"

logger = logging.getLogger(__name__)


class LLMOffline(RuntimeError):
    """LLM_DRY_RUN 이거나 LLM_PROVIDER=echo 일 때 — 호출 자체를 하지 않는다.

    app.core.llm.EchoLLM 은 "JSON"이 프롬프트에 있고 id가 없으면
    "[]" 를 돌려주므로, 여기서 EchoLLM 을 아예 호출하지 않고
    이 예외를 던져 폴백 경로로 곧장 보낸다.
    """


class SnapshotNotReady(RuntimeError):
    """data/trends/latest_snapshot.json 이 아직 없다."""


class KeywordNotFound(RuntimeError):
    """스냅샷에 해당 keyword_id가 없다."""


def load_keyword(keyword_id: str) -> dict:
    """app/trends/build_snapshot.py 가 만든 최신 스냅샷에서 키워드 리포트
    하나를 읽는다. trend_routes.get_trend_report() 와 같은 읽기 방식이다
    — 여기서 계산하지 않는다."""
    if not LATEST_SNAPSHOT_PATH.is_file():
        raise SnapshotNotReady("아직 게시된 트렌드 스냅샷이 없습니다.")
    snapshot = json.loads(LATEST_SNAPSHOT_PATH.read_text(encoding="utf-8"))
    for tab_items in snapshot["by_tab"].values():
        for item in tab_items:
            if item["id"] == keyword_id:
                return item
    raise KeywordNotFound(f"키워드를 찾을 수 없습니다: {keyword_id}")


def load_snapshot_info() -> dict:
    if not LATEST_SNAPSHOT_PATH.is_file():
        raise SnapshotNotReady("아직 게시된 트렌드 스냅샷이 없습니다.")
    snapshot = json.loads(LATEST_SNAPSHOT_PATH.read_text(encoding="utf-8"))
    return snapshot["snapshot"]


def complete_ideas_json(prompt: str) -> list[dict]:
    """아이디어 생성 프롬프트를 LLM에 보내고 JSON 배열을 받는다.

    오프라인(LLM_DRY_RUN=true 또는 LLM_PROVIDER=echo)이면 호출하지
    않고 LLMOffline 을 던진다 — 호출하는 쪽(app.agents.idea_agent)이
    app.ideas.fallback 으로 흘려보낸다.

    ★ 소요 시간을 로그로 남긴다. "아이디어 생성이 느리다" 문제를 다시
      조사할 때 병목이 (a) LLM 응답 자체인지 (b) complete_json의
      JSON 재시도(1회 더 왕복) 때문인지 서버 로그만 보고 바로
      구분하기 위함이다.
    """
    if settings.LLM_DRY_RUN or settings.LLM_PROVIDER == "echo":
        raise LLMOffline("LLM_DRY_RUN 이거나 LLM_PROVIDER=echo 라 호출하지 않습니다.")

    started = time.monotonic()
    try:
        raw = get_llm().complete_json(
            prompt,
            max_tokens=settings.IDEA_LLM_MAX_TOKENS,
            temperature=settings.IDEA_LLM_TEMPERATURE,
        )
    except Exception as e:
        elapsed = time.monotonic() - started
        logger.warning("아이디어 LLM 호출 실패 (%.1f초 만에) — provider=%s model=%s max_tokens=%d — %s: %s",
                        elapsed, settings.LLM_PROVIDER, settings.GEMINI_MODEL,
                        settings.IDEA_LLM_MAX_TOKENS, type(e).__name__, e)
        raise
    elapsed = time.monotonic() - started
    logger.info("아이디어 LLM 호출 완료: %.1f초 (provider=%s model=%s max_tokens=%d)",
                elapsed, settings.LLM_PROVIDER, settings.GEMINI_MODEL, settings.IDEA_LLM_MAX_TOKENS)

    if not isinstance(raw, list):
        raise LLMError(f"LLM이 배열이 아닌 값을 반환했습니다: {type(raw)}")
    return raw
