"""온보딩 타겟과 명시적으로 시작한 수집 실행의 공개 계약."""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.models import Category, Problem, ReviewResult, SourceKind

AgeBand = Literal["10대", "20대", "30대", "40대", "50대 이상"]
Gender = Literal["여성", "남성"]


class TargetProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    age: Optional[AgeBand] = None
    gender: Optional[Gender] = None
    jobs: list[str] = Field(default_factory=list, max_length=5)
    places: list[str] = Field(default_factory=list, max_length=5)

    @field_validator("gender", mode="before")
    @classmethod
    def gender_alias(cls, value):
        return {"남자": "남성", "여자": "여성"}.get(value, value) if isinstance(value, str) else value

    @field_validator("jobs", "places", mode="before")
    @classmethod
    def keyword_tokens(cls, value):
        if not isinstance(value, list) or len(value) > 5:
            raise ValueError("키워드는 항목별 최대 다섯 개의 목록이어야 합니다")
        cleaned = []
        for token in value:
            if not isinstance(token, str):
                raise ValueError("키워드는 문자열이어야 합니다")
            token = unicodedata.normalize("NFKC", token)
            if any(unicodedata.category(char).startswith("C") for char in token):
                raise ValueError("키워드에 제어 문자를 사용할 수 없습니다")
            token = re.sub(r"\s+", " ", token).strip()
            # 검색 연산자/URL/제어문 삽입을 허용하지 않고 평범한 직업·장소 명사만 받는다.
            if not 1 <= len(token) <= 30 or not re.fullmatch(r"[가-힣ㄱ-ㅎㅏ-ㅣA-Za-z0-9][가-힣ㄱ-ㅎㅏ-ㅣA-Za-z0-9 .·&+()/-]*", token):
                raise ValueError("키워드는 한글·영문·숫자로 시작하는 서른 자 이하의 직업·장소여야 합니다")
            if re.search(r"\b(?:AND|OR|NOT)\b", token, re.IGNORECASE) or any(mark in token for mark in ["://", "&&", "++", "--"]):
                raise ValueError("검색 명령이나 URL은 키워드로 사용할 수 없습니다")
            if token.casefold() not in {t.casefold() for t in cleaned}:
                cleaned.append(token)
        return sorted(cleaned, key=str.casefold)

    @model_validator(mode="after")
    def minimum_fields(self):
        if sum(bool(value) for value in [self.age, self.gender, self.jobs, self.places]) < 2:
            raise ValueError("나이대·성별·직업·장소 중 최소 두 항목을 입력하세요")
        return self


class CollectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target: TargetProfile
    resume_from: Optional[str] = Field(default=None, pattern=r"^col-[0-9a-f]{24}$")


class TargetQuery(BaseModel):
    keyword: str
    category: Category
    source_kind: SourceKind
    provider: Literal["naver", "kakao"]
    endpoint: str
    source_name: str
    reason: str
    id: str = ""
    topic: str = ""
    topic_id: str = ""
    intent: str = ""
    anchor_mode: str = ""


class QueryResult(BaseModel):
    query_id: str
    keyword: str
    category: Category
    topic: str
    intent: str
    source_name: str
    status: Literal["succeeded", "failed"]
    result_count: int = 0
    new_count: int = 0
    error: Optional[str] = None


class CollectionCoverage(BaseModel):
    topics_total: int = 0
    topics_searched: int = 0
    intents_total: int = 9
    intents_searched: int = 0
    catalog_total: int = 0
    catalog_completed: int = 0
    catalog_remaining: int = 0


class ReviewCandidate(BaseModel):
    raw_item_id: str
    pain_summary: str
    target_status: str
    reason: str
    source_url: str
    source_name: str


class CollectionCounts(BaseModel):
    queries_total: int = 0
    queries_done: int = 0
    search_succeeded: int = 0
    search_failed: int = 0
    fetched: int = 0
    collected: int = 0
    target_matched: int = 0
    target_confirmed: int = 0
    pain_detected: int = 0
    target_unconfirmed: int = 0
    target_conflicts: int = 0
    selected: int = 0
    unselected: int = 0
    judged: int = 0
    judge_failed: int = 0
    pain_items: int = 0
    candidates: int = 0
    problems: int = 0
    generation_failed: int = 0
    generation_retries: int = 0
    held: int = 0
    llm_calls: int = 0


class CollectionLimits(BaseModel):
    search_queries: int
    search_http_attempts: int
    collected_items: int = 2400
    items_per_query: int = 20
    items_per_category: int = 1000
    judged_items: int = 2400
    problem_candidates: int = 20
    llm_logical_calls: int = 200
    llm_http_attempts: int = 1200
    timeout_seconds: int = 3600


class CollectionRun(BaseModel):
    id: str
    status: Literal["queued", "running", "completed", "failed"]
    stage: Literal["queued", "searching", "interpreting", "evidence", "generating", "completed", "failed"]
    message: str
    target: TargetProfile
    queries: list[TargetQuery]
    counts: CollectionCounts = Field(default_factory=CollectionCounts)
    problems: list[Problem] = Field(default_factory=list)
    reviews: dict[str, ReviewResult] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    error: Optional[str] = None
    limits: CollectionLimits
    created_at: datetime
    updated_at: datetime
    reused: bool = False
    target_match_policy: Literal["not_checked", "input_mentions_v1", "evidence_v2"] = "not_checked"
    plan_version: str = "legacy"
    current_plan_version: str = ""
    can_resume: bool = False
    series_id: str = ""
    resume_from: Optional[str] = None
    round_index: int = 1
    stop_reason: Optional[Literal["round_budget", "catalog_exhausted", "time_budget", "llm_budget", "failed"]] = None
    has_more: bool = False
    coverage: CollectionCoverage = Field(default_factory=CollectionCoverage)
    query_results: list[QueryResult] = Field(default_factory=list)
    cumulative_counts: CollectionCounts = Field(default_factory=CollectionCounts)
    exclusion_reasons: dict[str, int] = Field(default_factory=dict)
    review_candidates: list[ReviewCandidate] = Field(default_factory=list)
