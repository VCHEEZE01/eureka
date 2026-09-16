"""
.env 를 읽는 유일한 곳.

★ 다른 파일에서 os.environ 을 직접 읽지 말 것. 여기서 가져다 쓸 것.
  이유: 기본값이 흩어지지 않고, 테스트에서 한 곳만 바꾸면 된다.

사용:
    from app.config.settings import settings
    settings.NAVER_DAILY_CAP
"""

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── 외부 검색 API ────────────────────────────
    NAVER_CLIENT_ID: str = ""
    NAVER_CLIENT_SECRET: str = ""
    KAKAO_REST_API_KEY: str = ""
    PUBLIC_DATA_KEY: str = ""

    # ── LLM (포텐스닷 / Gemini) ─────────────────
    LLM_PROVIDER: Literal["potens", "gemini", "echo"] = "potens"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"
    LLM_BASE_URL: str = ""
    LLM_API_KEY: str = ""
    LLM_MODEL: str = ""
    LLM_MODEL_JUDGE: str = ""  # 비우면 LLM_MODEL 을 쓴다
    LLM_AUTH_HEADER: str = "Authorization"
    LLM_AUTH_SCHEME: str = "Bearer"
    LLM_REQUEST_STYLE: Literal[
        "openai_chat", "anthropic_messages", "raw_prompt"
    ] = "openai_chat"
    LLM_RESPONSE_PATH: str = ""
    LLM_TIMEOUT_SEC: int = 60
    LLM_MAX_RETRIES: int = 2
    LLM_DRY_RUN: bool = True  # 기본은 네트워크 호출 없음. 실호출은 명시적으로 켠다

    # ── 수집 (① 수집 에이전트) ──────────────────
    # 주 1회 배치만 돌므로 배치일 하루치 한도를 다 써도 된다 (DATA_SPEC 0절).
    NAVER_DAILY_CAP: int = 20_000
    KAKAO_DAILY_CAP: int = 25_000
    COLLECT_PER_QUERY_LIMIT: int = 100
    COLLECT_MAX_PAGES: int = 3  # DATA_COLLECTION 4-1: 쿼리당 3페이지

    # ── 판별·묶기 (② 해석기) ───────────────────
    JUDGE_BATCH_SIZE: int = 20
    MAX_LLM_ITEMS: int = 20_000  # 주간 총량 하드 상한 (카테고리 5개 합산)
    CLUSTER_BACKEND: Literal["tfidf", "embedding", "hash"] = "tfidf"
    CLUSTER_THRESHOLD_TFIDF: float = 0.45
    CLUSTER_THRESHOLD_EMBED: float = 0.80
    MIN_GROUP_SIZE: int = 5  # DATA_COLLECTION 6절: 유사한 글 5건 이상이면 후보

    # ── 근거 조립 (②′ EvidenceAgent) ────────────
    # ★ 문서 11절이 "데이터를 보고 조정"이라고 남긴 값이다. 코드에 박지 말 것.
    # docs/DATA_COLLECTION.md 6절 게시 기준.
    PUBLISH_MIN_CASES: int = 20  # 관련 사례
    PUBLISH_MIN_SOURCES: int = 3  # 서로 다른 출처 — 문서가 "핵심"이라고 한 조건
    PUBLISH_MIN_EVIDENCE: int = 3  # 근거로 쓸 요약
    EVIDENCE_SHOW_MAX: int = 5  # 화면에 보일 근거 상한
    EVIDENCE_LOOKBACK_WEEKS: int = 8  # 원문을 되짚을 주차 창

    # ★ 라벨 분포를 화면에 그릴 최소 표본. 미만이면 "표본이 부족합니다"로 대체한다.
    #   "1건 중 1건 = 100%" 는 분모를 붙여도 오해를 부른다.
    MIN_LABELED_TO_SHOW: int = 3

    # ── 저장 ────────────────────────────────────
    CORPUS_DIR: Path = _BACKEND_ROOT / "data" / "corpus"
    CORPUS_KEEP_SNIPPET: bool = True

    DATABASE_URL: str = "sqlite:///./eureka.db"
    PROBLEMS_DIR: Path = _BACKEND_ROOT / "data" / "problems"
    COLLECTIONS_DIR: Path = _BACKEND_ROOT / "data" / "collections"
    # None preserves the original batch quota path. Target workers explicitly share the parent corpus quota.
    SEARCH_QUOTA_DIR: Optional[Path] = None
    COLLECTION_TIMEOUT_SEC: int = 3600
    COLLECTION_QUERY_BUDGET: int = 120
    COLLECTION_ITEMS_PER_QUERY: int = 20
    COLLECTION_JUDGE_PER_CATEGORY: int = 1000
    COLLECTION_JUDGE_BUDGET: int = 2400
    COLLECTION_PROBLEM_BUDGET: int = 20
    COLLECTION_LLM_CALL_BUDGET: int = 200
    COLLECTION_REUSE_SEC: int = 3600
    REFERENCE_HTML_PATH: Path = _BACKEND_ROOT.parent / "Frontend" / "v1-trend-incubator.html"
    API_ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # ── 아이디어 생성 (④ 아이디어 생성기, v1) ─────
    IDEAS_DIR: Path = _BACKEND_ROOT / "data" / "ideas"
    IDEA_COUNT_DEFAULT: int = 3
    # 실측(실제 Gemini 호출, usageMetadata.candidatesTokenCount 기준):
    #   count=3 → 1800~1950 토큰,  count=5 → 2900~3000 토큰
    # ★ 한때 3000으로 낮췄다가 count=5에서 간헐적으로 MAX_TOKENS 잘림
    #   (finishReason != STOP → LLMError → 폴백)이 재현되어 되돌렸다.
    #   candidatesTokenCount가 딱 3000 근처에서 끊기는 게 직접 확인됨.
    #   여유를 넉넉히 둬서 6000으로 — count=5의 실측치(~3000)에 2배
    #   마진, 예전 8000보다는 25% 작다.
    IDEA_LLM_MAX_TOKENS: int = 6000
    # 판별용 LLM_TEMPERATURE 기본값(0.0)과 달리 아이디어 생성은 매번 다른
    # 결과가 나와야 하므로 온도를 높게 둔다.
    IDEA_LLM_TEMPERATURE: float = 0.9

    # ── 방어 ────────────────────────────────────

    @field_validator("*", mode="before")
    @classmethod
    def _drop_inline_comment(cls, v: Any) -> Any:
        """
        `KEY=   # 설명` 처럼 값이 비고 주석만 있는 줄을 python-dotenv 가
        주석 문자열을 값으로 읽어버린다. 실호출을 켜는 순간 모델명 자리에
        주석이 들어가므로 여기서 빈 값으로 되돌린다.
        """
        if isinstance(v, str) and v.lstrip().startswith("#"):
            return ""
        return v

    @field_validator("COLLECTION_QUERY_BUDGET", "COLLECTION_ITEMS_PER_QUERY", "COLLECTION_JUDGE_PER_CATEGORY",
                     "COLLECTION_JUDGE_BUDGET", "COLLECTION_PROBLEM_BUDGET", "COLLECTION_LLM_CALL_BUDGET",
                     "COLLECTION_TIMEOUT_SEC", mode="after")
    @classmethod
    def _collection_budgets(cls, value: int, info):
        ceilings = {"COLLECTION_QUERY_BUDGET": 1000, "COLLECTION_ITEMS_PER_QUERY": 100,
                    "COLLECTION_JUDGE_PER_CATEGORY": 1000, "COLLECTION_JUDGE_BUDGET": 5000,
                    "COLLECTION_PROBLEM_BUDGET": 50, "COLLECTION_LLM_CALL_BUDGET": 500,
                    "COLLECTION_TIMEOUT_SEC": 7200}
        if not 1 <= value <= ceilings[info.field_name]:
            raise ValueError(f"{info.field_name}은 1부터 {ceilings[info.field_name]} 사이여야 합니다")
        return value

    # ── 파생 ────────────────────────────────────

    @property
    def judge_model(self) -> str:
        """판별용 모델. 따로 안 정했으면 기본 모델을 쓴다."""
        if self.LLM_PROVIDER == "gemini":
            return self.GEMINI_MODEL
        return self.LLM_MODEL_JUDGE or self.LLM_MODEL

    def cluster_threshold(self) -> float:
        """묶기 임계값. 백엔드마다 스케일이 다르므로 분리해 둔다."""
        return (
            self.CLUSTER_THRESHOLD_EMBED
            if self.CLUSTER_BACKEND == "embedding"
            else self.CLUSTER_THRESHOLD_TFIDF
        )

    def missing_keys(self) -> list[str]:
        """비어 있어서 실호출이 안 되는 항목. 실행 전 안내용."""
        need = {
            "NAVER_CLIENT_ID": self.NAVER_CLIENT_ID,
            "NAVER_CLIENT_SECRET": self.NAVER_CLIENT_SECRET,
            "KAKAO_REST_API_KEY": self.KAKAO_REST_API_KEY,
        }
        if not self.LLM_DRY_RUN and self.LLM_PROVIDER == "gemini":
            need["GEMINI_API_KEY"] = self.GEMINI_API_KEY
            need["GEMINI_MODEL"] = self.GEMINI_MODEL
        elif not self.LLM_DRY_RUN and self.LLM_PROVIDER != "echo":
            need["LLM_BASE_URL"] = self.LLM_BASE_URL
            need["LLM_API_KEY"] = self.LLM_API_KEY
            need["LLM_MODEL"] = self.LLM_MODEL
        return [k for k, v in need.items() if not v]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()



def child_process_environment() -> dict[str, str]:
    """독립 수집 worker에 현재 설정을 전달한다. 비밀값은 로그·응답에 출력하지 않는다."""
    env = os.environ.copy()
    for name, value in settings.model_dump(mode="json").items():
        if value is None:
            env.pop(name, None)
        elif isinstance(value, (list, dict, bool)):
            env[name] = json.dumps(value, ensure_ascii=False)
        else:
            env[name] = str(value)
    return env
