"""
트렌드 키워드 서비스 API가 주고받는 데이터 모양.

docs/트렌드_백엔드_설계.md 8절을 그대로 코드로 옮긴 것 — 필드 하나를
고치면 그 문서도 같이 고친다. 화면(Final/Frontend/v1-trend-incubator.html)의
toCardView()가 이 스키마를 camelCase로 변환해서 쓴다.
"""

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field

# ═══════════════════════ 공통 이름표 ═══════════════════════

Category = Literal["디저트/푸드", "패션/뷰티", "라이프/취미", "챌린지/놀이", "테크/생산성", "콘텐츠/밈"]
Platform = Literal["naver", "youtube", "threads"]
TabType = Literal["trend", "surge"]
StatusType = Literal["sustained", "rising", "viral"]


# ═══════════════════════ 기준 정보 ═══════════════════════

class SnapshotInfo(BaseModel):
    """이 응답의 숫자가 '언제 만든 결과'인지 알려주는 꼬리표."""

    snapshot_id: str
    base_date: date
    months: list[str]
    is_dummy: bool
    note: Optional[str] = None


# ═══════════════════════ 카드(첫 페이지) ═══════════════════════

class TrendStrength(BaseModel):
    """트렌드 강도. 전주 대비 변화율로 코드가 정한다(트렌드_백엔드_설계.md 4절)."""

    level: Literal["strong", "medium", "weak"]
    label: str
    capped: bool = False


class KeywordMetrics(BaseModel):
    monthly_search_volume: int = Field(ge=0)
    monthly_mention_volume: int = Field(ge=0)
    weekly_change_rate: float
    trend_strength: TrendStrength


class PlatformShare(BaseModel):
    naver: int = Field(ge=0, le=100)
    youtube: int = Field(ge=0, le=100)
    threads: int = Field(ge=0, le=100)


class KeywordCard(BaseModel):
    id: str
    rank: int
    tab: TabType
    name: str
    category: Category
    summary: str
    status: str
    status_type: StatusType
    metrics: KeywordMetrics
    platform_share: PlatformShare


# ═══════════════════════ 리포트(상세 화면) ═══════════════════════

class PlatformSeries(BaseModel):
    metric: Literal["search_volume", "mention_count"]
    values: list[int]


class PlatformTrend(BaseModel):
    naver: PlatformSeries
    youtube: PlatformSeries
    threads: PlatformSeries


class EvidenceItem(BaseModel):
    id: str
    platform: Platform
    title: str
    url: str
    published_at: Optional[date] = None
    snippet: str = ""


class ReportAnalysis(BaseModel):
    why_trending: str
    target: str
    sustainability: str
    evidence_ids: list[str]


class KeywordReport(KeywordCard):
    analysis: ReportAnalysis
    related_keywords: list[str] = Field(min_length=1, max_length=5)
    platform_trend: PlatformTrend
    evidence: list[EvidenceItem] = []
    limitations: list[str] = []


# ═══════════════════════ API 응답 ═══════════════════════

class TrendListResponse(BaseModel):
    """GET /api/trends?tab=... 의 응답.

    ※ 설계 문서는 items를 KeywordCard(가벼운 목록용)로 정의하지만,
      지금 규모(수십 개)에서는 상세 필드까지 통째로 내려줘도 payload가
      작아서(수십 KB) 화면이 상세 화면 진입 시 추가 요청을 안 해도 된다.
      그래서 items를 KeywordReport로 채운다 — 카드가 필요로 하는 필드는
      전부 KeywordCard의 상위集합이라 프론트 호환에는 문제가 없다.
      카탈로그가 커지면(수백~수천) 그때 KeywordCard로 되돌린다.
    """

    snapshot: SnapshotInfo
    tab: TabType
    criteria: str
    items: list[KeywordReport]


class KeywordReportResponse(BaseModel):
    snapshot: SnapshotInfo
    report: KeywordReport


class ErrorResponse(BaseModel):
    error_code: Literal["invalid_input", "keyword_not_found", "snapshot_not_ready", "internal_error"]
    message: str
