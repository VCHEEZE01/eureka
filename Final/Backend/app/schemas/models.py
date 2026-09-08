"""
유레카 공용 데이터 모델 — 에이전트 사이의 계약.

★ 이 파일이 4명이 따로 개발할 수 있는 근거다.
  각자 자기 에이전트 안은 마음대로 짜되, 여기 정의된 입출력만 지키면 합쳐진다.

★ 이 파일을 바꾸려면 팀에 먼저 알릴 것.
  여기가 바뀌면 다른 사람 코드가 깨진다.

────────────────────────────────────────────────
지켜야 할 원칙 (PRD 8절)
────────────────────────────────────────────────
1. LLM이 채우는 모델에는 숫자 필드를 두지 않는다.
   → 사례 수·출처 수는 DB를 세서 만든다. 지어낼 자리를 아예 없앤다.
2. 실제 수집한 근거와 AI가 쓴 문장은 필드를 분리한다.
   → 화면에서 시각적으로 구분해 보여줘야 하기 때문.
3. 원문은 통째로 복제하지 않는다. 요약이 기본, 짧은 발췌만 허용.
"""

from datetime import date, datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field

# ══════════════════════════════════════════════
# 공통
# ══════════════════════════════════════════════


class Category(str, Enum):
    """PRD F03: MVP는 3개로 시작한다."""

    PRODUCTIVITY = "생산성/업무"
    CAREER = "커리어/자기계발"
    LIFESTYLE = "라이프스타일"


class SourceKind(str, Enum):
    """PRD F02: 온보딩에서 고르는 수집 범위."""

    COMMUNITY = "커뮤니티"
    BLOG = "블로그"
    REVIEW = "리뷰"
    NEWS = "뉴스"
    SOCIAL = "소셜"


# ══════════════════════════════════════════════
# ① 수집 에이전트의 산출물
# ══════════════════════════════════════════════


class SearchQuery(BaseModel):
    """수집 에이전트가 만들어내는 검색어 하나."""

    keyword: str = Field(description="실제로 API에 던질 검색어")
    category: Category
    source_kind: SourceKind
    reason: str = Field(description="이 검색어를 고른 이유. 나중에 튜닝할 때 본다")


class RawItem(BaseModel):
    """
    수집한 원문 1건. ★ 모든 숫자와 근거의 원천이다.

    절대 삭제하지 않는다. 이게 없으면 "사례 137건"을 증명할 수 없다.
    """

    id: str
    title: str
    snippet: str = Field(description="본문 전체가 아니라 스니펫. 원문 복제 금지")
    url: str
    source_name: str = Field(description="매체명. 예: 네이버 카페")
    source_kind: SourceKind
    posted_at: Optional[date] = None
    collected_at: datetime
    query_keyword: str = Field(description="어떤 검색어로 걸렸는지")


# ══════════════════════════════════════════════
# ② 해석기의 산출물
# ══════════════════════════════════════════════


class Judgement(BaseModel):
    """이 원문이 '진짜 불편'인지에 대한 판정. LLM이 채운다."""

    raw_item_id: str
    is_pain: bool = Field(description="실제 불편이면 True. 광고·잡담이면 False")
    pain_summary: Optional[str] = Field(
        default=None, description="불편을 한 문장으로. is_pain=False면 None"
    )
    confidence: Literal["높음", "중간", "낮음"]


class ProblemCandidate(BaseModel):
    """
    비슷한 불편끼리 묶은 결과. 아직 문제정의는 아니다.

    ※ 숫자 필드 없음. 몇 건인지는 raw_item_ids 길이를 세면 된다.
    """

    id: str
    raw_item_ids: list[str] = Field(description="이 묶음에 들어간 원문 id들")
    pain_summaries: list[str] = Field(description="묶인 불편 요약들")
    theme_hint: str = Field(description="이 묶음이 대충 무엇에 관한 것인지")
    category: Category


# ══════════════════════════════════════════════
# ③ 문제정의 생성기의 산출물
# ══════════════════════════════════════════════


class Evidence(BaseModel):
    """근거 1건. 반드시 raw_item으로 역추적되어야 한다."""

    raw_item_id: str
    summary: str = Field(description="서비스가 정리한 불편 요약")
    excerpt: Optional[str] = Field(default=None, description="허용된 경우에만 짧은 발췌")


class ProblemDraft(BaseModel):
    """
    LLM이 쓰는 문제정의. ★ 숫자 필드가 하나도 없다 — 의도된 것이다.

    사례 수·출처 수는 아래 Problem에서 DB가 세서 채운다.
    """

    title: str
    one_liner: str = Field(description="카드에 보일 한 줄")
    description: str = Field(description="AI 서술 영역")
    context: str = Field(description="언제 주로 나타나는가. AI 서술 영역")
    evidence: list[Evidence] = Field(description="근거 3~5건")


class ReviewResult(BaseModel):
    """검수 결과. PRD F00: 게시 / 보류 / 병합 세 갈래."""

    decision: Literal["publish", "hold", "merge"]
    reason: str
    merge_into_problem_id: Optional[str] = Field(
        default=None, description="decision이 merge일 때만 채운다"
    )


class Problem(BaseModel):
    """
    게시된 문제정의. 화면에 나가는 최종 형태.

    ★ case_count / source_count 는 LLM이 아니라 DB 집계가 채운다.
    """

    id: str
    title: str
    one_liner: str
    category: Category
    description: str
    context: str
    evidence: list[Evidence]
    # ↓ 여기부터는 집계값. 절대 LLM이 채우지 않는다.
    case_count: int = Field(description="raw_items 개수를 센 값")
    source_count: int = Field(description="서로 다른 출처 개수를 센 값")
    updated_at: datetime


# ══════════════════════════════════════════════
# ④ 아이디어 생성기의 산출물
# ══════════════════════════════════════════════


class ServiceForm(str, Enum):
    WEB = "웹 서비스"
    MOBILE = "모바일 앱"
    CHATBOT = "챗봇"
    EXTENSION = "브라우저 확장"
    SCRIPT = "자동화 스크립트"


class Target(str, Enum):
    B2C = "B2C"
    B2B = "B2B"
    SOLO = "1인 사업자/프리랜서"


class Resource(str, Enum):
    ONE = "1인"
    SMALL = "2~5인"
    FULL = "전업/충분한 리소스"


class UserCondition(BaseModel):
    """
    PRD F07 개인화 조건. ★ 선택 입력이다 — 없으면 기본 아이디어가 나온다.

    "기술 난이도"는 받지 않는다(PRD 10절). 시스템이 추론한다.
    """

    service_form: ServiceForm
    target: Target
    resource: Resource
    extra: Optional[str] = Field(default=None, max_length=500)


class Idea(BaseModel):
    """
    아이디어. 기본과 개인화가 같은 구조를 공유한다(PRD F08).

    ※ 시장 규모·성공 확률 같은 필드는 두지 않는다. 지어낼 자리를 없앤다.
    """

    id: str
    problem_id: str
    name: str
    one_liner: str
    target: str
    service_form: str
    why_linked: str = Field(description="이 문제와 연결되는 이유")
    how_it_works: str
    core_features: list[str]
    differentiator: str
    # ↓ 조건을 넣었을 때만 채워진다
    fit_reason: Optional[str] = Field(default=None, description="사용자 조건에 맞는 이유")
    scope_note: Optional[str] = Field(default=None, description="리소스 대비 권장 범위")


# ══════════════════════════════════════════════
# 진행 상태 (PRD F02·F05·F07)
# ══════════════════════════════════════════════


class ProgressEvent(BaseModel):
    """
    실시간 생성 중 프론트로 흘려보내는 단계 알림.

    화면의 "에이전틱 진행 상태 UI"가 이걸 받아서 그린다.
    """

    step: str = Field(description="단계 이름. 예: 후보 수집")
    index: int = Field(description="0부터")
    total: int
    done: bool = False
