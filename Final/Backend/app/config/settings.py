"""
.env 를 읽는 유일한 곳.

★ 다른 파일에서 os.environ 을 직접 읽지 말 것. 여기서 가져다 쓸 것.
  이유: 기본값이 흩어지지 않고, 테스트에서 한 곳만 바꾸면 된다.

사용:
    from app.config.settings import settings
    settings.NAVER_DAILY_CAP
"""

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

    # ── LLM (포텐스닷 게이트웨이) ────────────────
    LLM_PROVIDER: Literal["potens", "echo"] = "potens"
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

    # ── 저장 ────────────────────────────────────
    CORPUS_DIR: Path = _BACKEND_ROOT / "data" / "corpus"
    CORPUS_KEEP_SNIPPET: bool = True

    DATABASE_URL: str = "sqlite:///./eureka.db"

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

    # ── 파생 ────────────────────────────────────

    @property
    def judge_model(self) -> str:
        """판별용 모델. 따로 안 정했으면 기본 모델을 쓴다."""
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
        if not self.LLM_DRY_RUN:
            need["LLM_BASE_URL"] = self.LLM_BASE_URL
            need["LLM_API_KEY"] = self.LLM_API_KEY
            need["LLM_MODEL"] = self.LLM_MODEL
        return [k for k, v in need.items() if not v]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
