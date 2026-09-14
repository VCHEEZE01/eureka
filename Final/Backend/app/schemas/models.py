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
    """팀 회의(2026-09-09)로 5개 확정. docs/DATA_SPEC.md 1절."""

    FINANCE = "금융"
    HEALTHCARE = "헬스케어"
    LIFESTYLE = "라이프스타일"
    IT_PRODUCTIVITY = "IT/생산성"
    EDUCATION_CAREER = "교육/커리어"


class SourceKind(str, Enum):
    """
    온보딩에서 고르는 것은 수집 범위가 아니라 표시 필터다 (docs/DATA_SPEC.md 0절).
    배치는 항상 전체 출처를 수집한다.
    """

    NEWS = "뉴스"
    SOCIAL = "소셜"
    BLOG = "블로그"
    PUBLIC_DATA = "공공데이터"
    # 화면에 노출하지 않는다. 지식iN·카페용 — 수집 여부는 미결정(DATA_SPEC 6절)
    COMMUNITY = "커뮤니티"


class CollectMode(str, Enum):
    """어느 경로로 수집됐는가 (DATA_COLLECTION 3-1)."""

    BATCH = "batch"
    REALTIME = "realtime"


class LicensePolicy(str, Enum):
    """발췌 허용 여부 (DATA_COLLECTION 3-1·3-2)."""

    SUMMARY_ONLY = "summary-only"
    EXCERPT_OK = "excerpt-ok"


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
    # ↓ DATA_COLLECTION 3-1의 공통 필드. 전부 기본값이라 기존 코드가 깨지지 않는다.
    content_hash: str = Field(
        default="", description="정제된 title+snippet의 해시. 중복 판정 전용"
    )
    collected_by: CollectMode = CollectMode.BATCH
    license: LicensePolicy = LicensePolicy.SUMMARY_ONLY


# ══════════════════════════════════════════════
# ② 해석기의 산출물
# ══════════════════════════════════════════════

# ↓ 근거 상세 페이지 "⑤ 누가 겪고 있나"의 고정 라벨 목록.
#   ★ dictionaries.py 가 아니라 여기 둔다 — dictionaries.py:13이
#     `from app.schemas.models import Category` 를 하므로 반대 방향으로
#     두면 순환 import 가 된다.
SUFFERER_ROLES: tuple[str, ...] = (
    "직장인", "학생", "1인 사업자·프리랜서", "부모·보호자", "환자·간병인", "기타",
)
AGE_BANDS: tuple[str, ...] = ("10대", "20대", "30대", "40대", "50대 이상")
GENDERS: tuple[str, ...] = ("남자", "여자")

# ★ sufferer_gender 를 채우기 전에 원문에 이 표현이 하나라도 있어야 한다.
#   직업·문체로 성별을 추론하는 것을 막는 규칙 방어다 (llm_tool._clean_gender).
GENDER_SELF_MENTION_WORDS: tuple[str, ...] = (
    "남자", "여자", "남성", "여성", "아빠", "엄마", "아버지", "어머니",
    "남편", "아내", "형", "누나", "오빠", "언니",
)


class Judgement(BaseModel):
    """이 원문이 '진짜 불편'인지에 대한 판정. LLM이 채운다."""

    raw_item_id: str
    pain_status: Literal["pain", "not_pain", "insufficient"] = "insufficient"
    assessment_reason: Optional[str] = None
    experience_type: Literal["self", "other", "mixed", "unknown"] = "unknown"
    experience_evidence: Optional[str] = None
    target_status: Literal["confirmed", "unconfirmed", "conflict"] = "unconfirmed"
    target_field_status: dict[str, Literal["confirmed", "unconfirmed", "conflict"]] = Field(default_factory=dict)
    target_evidence: dict[str, str] = Field(default_factory=dict)
    target_values: dict[str, str] = Field(default_factory=dict)
    target_profile_key: Optional[str] = None
    target_policy: Optional[Literal["evidence_v2"]] = None
    is_pain: bool = Field(description="실제 불편이면 True. 광고·잡담이면 False")
    pain_summary: Optional[str] = Field(
        default=None, description="불편을 한 문장으로. is_pain=False면 None"
    )
    confidence: Literal["높음", "중간", "낮음"]
    # ↓ 화면의 불만도·필요도 재료 (docs/DATA_SPEC.md 4절).
    #   ★ 숫자가 아니라 라벨이다. 점수는 ③이 이 라벨을 세서 만든다.
    severity: Optional[Literal["높음", "중간", "낮음"]] = Field(
        default=None, description="불편 강도. 불만도 집계의 재료. 판정 못 했으면 None"
    )
    has_need_signal: bool = Field(
        default=False,
        description="결핍 신호(있었으면·아쉽·없어서·개선됐으면) 등장 여부. 필요도 집계의 재료",
    )
    # ↓ 2026-09-11 계약 변경. 근거 상세 페이지용 라벨 5개. 전부 기본값 —
    #   과거에 쓰인 JSONL 이 이 필드 없이도 그대로 파싱된다.
    has_payment_signal: bool = Field(
        default=False,
        description="지불 신호(돈 아깝·구독료·환불 등) 등장 여부. ① '돈이 걸린 문제인가' 재료. "
        "규칙으로만 채운다 — PAIN_SIGNALS 와 섞지 않는다",
    )
    sufferer_role: Optional[Literal[SUFFERER_ROLES]] = Field(
        default=None, description="글쓴이가 밝힌 역할. SUFFERER_ROLES 중 하나. 모르면 None",
    )
    sufferer_age_band: Optional[Literal[AGE_BANDS]] = Field(
        default=None,
        description="★ 글쓴이가 직접 밝힌 경우에만("
        "'30대인데' 등). 추론 금지. 모르면 None",
    )
    sufferer_gender: Optional[Literal[GENDERS]] = Field(
        default=None,
        description="★★ 원문에 성별 자기 서술이 있는 경우에만. 직업·문체로 "
        "추론하지 않는다(편견). 모르면 None",
    )
    mentioned_service: Optional[str] = Field(
        default=None,
        description="원문에 함께 언급된 기존 서비스명. ★ 원문에 글자 그대로 "
        "있는 것만 — 환각 브랜드명은 llm_tool 이 규칙으로 버린다",
    )


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
    # 수집 원문에서 복사하는 메타데이터. LLM이 링크·출처·날짜를 작성하지 않는다.
    source_name: str = ""
    source_url: Optional[str] = None
    source_kind: Optional[SourceKind] = None
    posted_at: Optional[date] = None
    # ↓ 근거 목록 필터용 라벨. 집계값을 복제하지 않고 이 근거를 만든
    #   Judgement의 값을 그대로 옮긴다. 전부 기본값이라 과거 데이터도 읽힌다.
    severity: Optional[Literal["높음", "중간", "낮음"]] = Field(
        default=None, description="불편 강도 라벨. 판정 못 했으면 None"
    )
    has_payment_signal: bool = Field(
        default=False, description="이 근거에 지불 신호가 있었는지"
    )
    has_need_signal: bool = Field(
        default=False, description="이 근거에 결핍·해결책 탐색 신호가 있었는지"
    )


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
    # ↓ 2026-09-11 계약 변경. 근거 상세 페이지 "③ 만들기에 얼마나 복잡한가".
    #   ★ 서술만 담는다. complexity_score·complexity_level 같은 점수·등급
    #   필드를 만들지 않는다 — tests/test_no_numbers.py 가 이름으로도 막는다.
    complexity_note: str = Field(
        default="", description="문제의 복잡도를 서술로만. 점수·등급 금지"
    )


class ReviewResult(BaseModel):
    """검수 결과. PRD F00: 게시 / 보류 / 병합 세 갈래."""

    decision: Literal["publish", "hold", "merge"]
    reason: str
    merge_into_problem_id: Optional[str] = Field(
        default=None, description="decision이 merge일 때만 채운다"
    )


class WeekCount(BaseModel):
    """
    주차별 근거 건수.

    ★ "언급량"이 아니다. "수집된 근거의 작성일 분포"다.
      검색 API를 최신순(sort=date)으로 조회하므로 이 값은 실제 언급 증감이
      아니라 수집 창 안에서 발견된 글의 작성일 분포다 (docs/DATA_SPEC.md 8절 위험3).
      화면에 "추세"라고 쓰지 말 것.
    """

    week: str = Field(description="ISO 주차. corpus_tool.week_key() 형식")
    count: int
    partial: bool = Field(
        default=False, description="관측 창이 이 주를 온전히 덮지 못했다. 화면에서 흐리게"
    )


class ServiceMention(BaseModel):
    """원문에 함께 언급된 기존 서비스. ★ name 은 원문에 글자 그대로 있는 것만."""

    name: str
    count: int = Field(description="이 이름이 등장한 근거 건수")


class ProblemSignals(BaseModel):
    """
    문제 1건의 근거를 센 값. 근거 상세 페이지의 재료다.

    ★★ 전부 집계값이다. LLM은 이 모델을 절대 채우지 않는다.
      LLM이 만드는 것은 Judgement의 라벨(severity·sufferer_role 등)까지이고,
      그 라벨을 '세는' 것은 aggregate_tool이다. 원칙: docs/DATA_SPEC.md 4절.

    ★ 이 모델을 ProblemDraft·Idea 에 붙이지 말 것.
      tests/test_no_numbers.py 가 막고 있다 (test_signals_live_only_on_problem).

    ★ 건수마다 분모를 같이 둔 이유
      "강한 불만 12건"은 case_count 가 아니라 severity 라벨이 붙은 건수를 분모로
      해야 정직하다. role_counts 도 같다. 분모 없는 건수는 화면에서 반드시 오해된다.
      *_labeled_count 가 settings.MIN_LABELED_TO_SHOW 미만이면 화면은 그 분포를
      아예 숨긴다 — "1건 중 1건 = 100%"는 분모를 붙여도 오해를 부른다.
    """

    # ── ⑧ 이 문제를 믿어도 되는가 — 표본의 폭 ──────────────
    source_kind_counts: dict[str, int] = Field(
        default_factory=dict, description="SourceKind 값 → 근거 건수"
    )
    source_name_counts: dict[str, int] = Field(
        default_factory=dict,
        description="매체명 → 근거 건수. ★ Problem.source_count 는 이 dict 의 길이다",
    )

    # ── ④ 얼마나 꾸준히 나타나나 — 시간 분포 ───────────────
    #    ★ '화제성'이라고 부를 수 없다. 위 WeekCount 주석 참고.
    first_posted_at: Optional[date] = None
    last_posted_at: Optional[date] = None
    observed_weeks: int = Field(default=0, description="작성일이 있는 근거가 걸친 주차 수")
    weekly_counts: list[WeekCount] = Field(default_factory=list)
    undated_count: int = Field(
        default=0,
        description="posted_at 이 없어 시간 분포에서 빠진 건수. "
        "★ 지식iN·카페는 작성일을 주지 않는다. 화면에 반드시 함께 표시",
    )

    # ── ⑦ 얼마나 불편해하나 — ② 라벨의 합 ─────────────────
    #    ★ 이건 DB 집계가 아니라 "AI 가 판정한 건수"다. 화면에서 구분 표기할 것
    #      (docs/DATA_SPEC.md 4절 경고).
    severity_counts: dict[str, int] = Field(
        default_factory=dict, description='"높음"/"중간"/"낮음" → 건수'
    )
    severity_labeled_count: int = Field(
        default=0, description="severity 라벨이 붙은 건수 = 위 분포의 분모"
    )
    need_signal_count: int = Field(
        default=0, description="결핍 신호가 걸린 건수. 규칙으로 세므로 전건 판정된다"
    )
    signal_type_counts: dict[str, int] = Field(
        default_factory=dict,
        description="PAIN_SIGNALS 유형 → 걸린 근거 건수. ★ RawItem 에서 재계산한다",
    )

    # ── ① 돈이 걸린 문제인가 ───────────────────────────────
    payment_signal_count: int = Field(
        default=0,
        description="PAYMENT_SIGNALS 표현이 하나 이상 걸린 근거 건수. "
        "★ 표현 개수가 아니라 건수다",
    )

    # ── ⑤ 누가 겪는가 — 주력은 source_kind_counts. 이건 보조 ──
    #    ★ *_labeled_count < settings.MIN_LABELED_TO_SHOW(3) 이면 화면이 분포를 숨긴다
    role_counts: dict[str, int] = Field(default_factory=dict)
    role_labeled_count: int = Field(
        default=0,
        description="역할이 드러난 건수 = role_counts 의 분모. "
        "스니펫 200자 안에 자기 서술이 없는 글이 많아 이 값은 작다",
    )
    age_counts: dict[str, int] = Field(default_factory=dict)
    age_labeled_count: int = Field(default=0, description="연령이 드러난 건수 = 분모")
    gender_counts: dict[str, int] = Field(default_factory=dict)
    gender_labeled_count: int = Field(
        default=0,
        description="성별 자기 서술이 드러난 건수 = 분모. 추론값이 아니다",
    )

    # ── ② 유사 서비스 ─────────────────────────────────────
    #    ★ '리뷰 불만'은 담지 않는다. 리뷰는 출처에 없다 (docs/DATA_SPEC.md 1절).
    mentioned_services: list[ServiceMention] = Field(default_factory=list)


class PublishGate(BaseModel):
    """
    docs/DATA_COLLECTION.md 6절 게시 기준.

    ★ 근거 페이지 ⑧ 블록이 이걸 그대로 보여준다. 기준 수치도 함께 노출한다 —
      기준을 숨기고 ✓만 보여주면 그건 또 하나의 '근거 없는 신뢰 표시'다.
    """

    case_count_ok: bool = Field(description="관련 사례 >= settings.PUBLISH_MIN_CASES")
    source_count_ok: bool = Field(description="서로 다른 출처 >= settings.PUBLISH_MIN_SOURCES")
    evidence_count_ok: bool = Field(
        description="근거 요약 >= settings.PUBLISH_MIN_EVIDENCE"
    )
    passed: bool
    reason: str = Field(default="", description="미달 사유. 통과면 빈 문자열")
    # 화면이 설정값을 따로 하드코딩하지 않고 실제 판정 기준을 그대로 보여준다.
    # 기본값은 과거에 저장된 Problem JSON과의 하위 호환을 위한 것이다.
    min_cases: int = Field(default=0, description="게시에 필요한 최소 관련 사례 수")
    min_sources: int = Field(default=0, description="게시에 필요한 최소 출처 수")
    min_evidence: int = Field(default=0, description="게시에 필요한 최소 근거 요약 수")


class EvidenceBundle(BaseModel):
    """
    ②′ 근거 조립기(EvidenceAgent)의 산출물. ③ 문제정의 생성기에게 넘긴다.

    ★ LLM이 채우는 필드가 하나도 없다. candidate_id 로 ProblemCandidate 를
      역추적할 수 있다.
    """

    candidate_id: str
    category: Category
    evidence: list[Evidence] = Field(description="3~5건. 서로 다른 출처 우선(라운드로빈)")
    signals: ProblemSignals
    gate: PublishGate


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
    # ↓ 2026-09-11 계약 변경. AI 서술 — "③ 만들기에 얼마나 복잡한가"
    complexity_note: str = Field(default="", description="문제의 복잡도를 서술로만")
    # ↓ 여기부터는 집계값. 절대 LLM이 채우지 않는다.
    case_count: int = Field(description="raw_items 개수를 센 값")
    source_count: int = Field(description="서로 다른 출처 개수를 센 값")
    # ↓ 2026-09-11 계약 변경. 근거 상세 페이지의 집계값 전부.
    signals: ProblemSignals = Field(
        default_factory=ProblemSignals,
        description="근거 상세 페이지의 집계값. db_tool.publish_problem 이 채운다",
    )
    # ↓ 게시된 문제는 정의상 이미 게시 기준을 통과했다(passed=True 고정).
    #   그래도 값을 들고 다니는 이유: ⑧ 블록이 "관련 사례 47건 ✓ (기준 20건)"처럼
    #   실제 기준 수치를 보여주려면 그 수치가 필요하다. 프론트가 PUBLISH_MIN_*
    #   상수를 따로 하드코딩하면 백엔드 settings 가 바뀔 때 어긋난다.
    gate: PublishGate = Field(
        default_factory=lambda: PublishGate(
            case_count_ok=True, source_count_ok=True, evidence_count_ok=True,
            passed=True, reason="",
        ),
        description="게시 기준 통과 근거. ⑧ 체크리스트가 그대로 표시한다",
    )
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
