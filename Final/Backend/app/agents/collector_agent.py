"""
① 수집 에이전트

역할  : 인터넷에서 사람들의 불평을 긁어온다
입력  : 카테고리 + 어떤 소스에서 찾을지
출력  : 원문(RawItem) 목록

흐름
  1. 검색어를 만든다   → 사전 조합 (도메인 키워드 × 불편 표현 × 소스)
  2. API를 호출한다    → tools/search_tool.py
  3. 중복을 제거하고 코퍼스에 쌓는다 → tools/corpus_tool.py

★ 검색어는 LLM이 만들지 않는다.
  app/config/dictionaries.py 를 전부 순회해 조합으로 만든다
  (docs/DATA_COLLECTION.md 4-1). 매주 같은 검색어가 나와야 주 단위 비교가 되고,
  모델이 흔들리면 수집량이 통째로 달라지기 때문이다.

★ 원문 URL을 따라가 본문을 긁지 않는다.
  검색 API가 준 스니펫만 쓴다. search_tool 이 그 경계를 지킨다.

규칙
  · 네이버·카카오 API를 여기서 직접 부르지 말 것 → tools 를 거칠 것
  · 쿼리 하나가 실패해도 배치가 죽으면 안 된다
  · 쿼터가 소진되면 그때까지 수집한 것으로 정상 종료한다
"""

from __future__ import annotations

import logging
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.agents.base import Agent
from app.config.dictionaries import (
    DICT_VERSION,
    DOMAIN_KEYWORDS,
    PAIN_SIGNALS_TIER1,
    PAIN_SIGNALS_TIER2,
)
from app.config.settings import settings
from app.schemas.models import (
    Category,
    CollectMode,
    LicensePolicy,
    RawItem,
    SearchQuery,
    SourceKind,
)
from app.tools import corpus_tool, search_tool
from app.tools.search_tool import QuotaExceeded, SearchError

logger = logging.getLogger(__name__)


class CollectInput(BaseModel):
    """
    ★ 새로 붙이는 필드는 전부 기본값을 가진다.
      pipeline.py 의 기존 호출 CollectInput(category=..., source_kinds=[...]) 이
      그대로 살아 있어야 한다.
    """

    category: Category
    source_kinds: list[SourceKind]
    limit: int = 50

    mode: CollectMode = CollectMode.BATCH
    per_query_limit: int = 100
    keyword_limit: Optional[int] = Field(
        default=None, description="도메인 키워드 상한. None 이면 사전 전체"
    )
    signal_tier: Literal["tier1", "all"] = Field(
        default="tier1", description="all 이면 Tier2 를 주차별로 돌려 가며 더한다"
    )
    week_rotation: int = Field(
        default=0, description="Tier2 로테이션 창 위치. 주차 번호를 넣으면 된다"
    )


class CollectorAgent(Agent[CollectInput, list[RawItem]]):
    name = "수집 에이전트"
    steps = ["검색어 만들기", "원문 긁어오기", "정리"]

    # ── 1단계 ─────────────────────────────────

    def _pain_expressions(self, data: CollectInput) -> list[str]:
        """
        불편 표현 목록.

        tier1 만 쓰면 쿼리 수가 고정된다. all 이면 Tier2 를 Tier1 크기만큼
        잘라 주차별로 돌려 쓴다 — 쿼리 수를 늘리지 않고 사전 전체를 커버한다.
        """
        exprs = list(PAIN_SIGNALS_TIER1)
        if data.signal_tier != "all" or not PAIN_SIGNALS_TIER2:
            return exprs

        window = max(len(PAIN_SIGNALS_TIER1), 1)
        total = len(PAIN_SIGNALS_TIER2)
        start = (data.week_rotation * window) % total
        rotated = PAIN_SIGNALS_TIER2[start:] + PAIN_SIGNALS_TIER2[:start]
        return exprs + rotated[:window]

    def _build_queries(self, data: CollectInput) -> list[SearchQuery]:
        """도메인 키워드 × 불편 표현 × 소스. 조합이 곧 쿼리 수다."""
        keywords = list(DOMAIN_KEYWORDS.get(data.category, []))
        if data.keyword_limit is not None:
            keywords = keywords[: max(data.keyword_limit, 0)]
        exprs = self._pain_expressions(data)

        queries = [
            SearchQuery(
                keyword=f"{kw} {ex}",
                category=data.category,
                source_kind=sk,
                reason=f"도메인 '{kw}' × 불편표현 '{ex}' · 사전 v{DICT_VERSION}",
            )
            for kw in keywords
            for ex in exprs
            for sk in data.source_kinds
        ]

        # ★ settings 는 여기서 읽는다. 모듈 레벨에 캡처하면 테스트가 못 갈아끼운다.
        max_pages = max(int(settings.COLLECT_MAX_PAGES), 1)
        logger.info(
            "%s: 검색어 %d개 (키워드 %d × 표현 %d × 소스 %d) · "
            "예상 API 호출 최대 %d회 (쿼리당 %d페이지) · 사전 v%s",
            data.category.value,
            len(queries),
            len(keywords),
            len(exprs),
            len(data.source_kinds),
            len(queries) * max_pages,
            max_pages,
            DICT_VERSION,
        )
        return queries

    # ── 2단계 ─────────────────────────────────

    def _collect(self, data: CollectInput, queries: list[SearchQuery]) -> list[RawItem]:
        """쿼리를 순회한다. 하나가 실패해도 멈추지 않는다."""
        per_query = max(
            min(data.per_query_limit, int(settings.COLLECT_PER_QUERY_LIMIT)), 1
        )
        out: list[RawItem] = []
        failed = 0

        for query in queries:
            try:
                out.extend(
                    search_tool.search(query.keyword, query.source_kind, per_query)
                )
            except QuotaExceeded as exc:
                # 한도를 넘겼다. 예외를 올리지 않고 여기까지로 마무리한다.
                logger.warning(
                    "쿼터 소진 — 여기까지 수집한 %d건으로 마무리한다: %s", len(out), exc
                )
                break
            except SearchError as exc:
                failed += 1
                logger.warning("검색 실패 — 다음 쿼리로 넘어간다 (%s): %s", query.keyword, exc)
                continue

        if failed:
            logger.info("실패한 쿼리 %d/%d개. 나머지는 정상 수집했다.", failed, len(queries))
        return out

    # ── 3단계 ─────────────────────────────────

    def _dedupe(self, data: CollectInput, items: list[RawItem]) -> list[RawItem]:
        """지난 배치까지의 id·해시와 대조해 새것만 남긴다."""
        seen_ids, seen_hashes = corpus_tool.load_seen()
        out: list[RawItem] = []

        for item in items:
            if item.id in seen_ids:
                continue
            if item.content_hash and item.content_hash in seen_hashes:
                continue
            seen_ids.add(item.id)
            if item.content_hash:
                seen_hashes.add(item.content_hash)
            out.append(
                item.model_copy(
                    update={
                        "collected_by": data.mode,
                        # 발췌 허용은 출처별로 따로 판단한다. 기본은 요약만.
                        "license": LicensePolicy.SUMMARY_ONLY,
                    }
                )
            )
        return out

    # ── 실행 ──────────────────────────────────

    def run(self, data: CollectInput) -> list[RawItem]:
        # provider 차단 기록은 실행 단위다. 매 배치 시작에 지운다.
        search_tool.reset_run_state()

        self.report(0)
        queries = self._build_queries(data)
        self.report(0, done=True)

        self.report(1)
        collected = self._collect(data, queries)
        self.report(1, done=True)

        self.report(2)
        fresh = self._dedupe(data, collected)
        # ★ 수집한 것은 전부 남긴다. limit 은 이번 호출이 돌려줄 개수일 뿐이다.
        corpus_tool.save_raw_items(fresh, category=data.category)
        logger.info(
            "%s: 수집 %d건 → 중복 제거 후 %d건 저장, %d건 반환",
            data.category.value,
            len(collected),
            len(fresh),
            min(len(fresh), max(data.limit, 0)),
        )
        self.report(2, done=True)

        return fresh[: max(data.limit, 0)]
