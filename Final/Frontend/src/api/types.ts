/**
 * 백엔드와 주고받는 데이터 타입.
 *
 * ★★ Backend/app/schemas/models.py 와 1:1로 맞춘다.
 *    한쪽만 바꾸면 런타임에 조용히 깨진다. 바꿀 때는 반드시 양쪽 같이.
 *
 * ★ 프론트와 백엔드가 서로 안 기다리게 해주는 파일이다.
 *   이 계약만 고정돼 있으면, 백엔드가 아직 없어도 mock으로 개발할 수 있다.
 */

/* ── 공통 ─────────────────────────────────────── */

/** models.py: Category — 팀 회의(2026-09-09)로 5개 확정 */
export type Category =
  | '금융'
  | '헬스케어'
  | '라이프스타일'
  | 'IT/생산성'
  | '교육/커리어';

/**
 * models.py: SourceKind
 * 온보딩에서 고르는 것은 수집 범위가 아니라 표시 필터다 (docs/DATA_SPEC.md 0절).
 * '커뮤니티'는 화면에 노출하지 않는다 — 지식iN·카페용.
 */
export type SourceKind = '뉴스' | '소셜' | '블로그' | '공공데이터' | '커뮤니티';

/* ── 문제 ─────────────────────────────────────── */

/** models.py: Evidence — 근거 1건. 반드시 원문으로 역추적된다. */
export interface Evidence {
  raw_item_id: string;
  source_url?: string | null;
  source_name?: string | null;
  source_kind?: SourceKind | null;
  posted_at?: string | null;
  summary: string;
  /** 허용된 경우에만 채워지는 짧은 발췌 */
  excerpt?: string;
  /** 근거 목록 필터용 Judgement 라벨. 과거 응답에는 없을 수 있다. */
  severity?: '높음' | '중간' | '낮음' | null;
  has_payment_signal?: boolean;
  has_need_signal?: boolean;
}

/* ── 근거 상세 페이지 신호 (2026-09-11 계약 변경) ─────── */

/**
 * models.py: WeekCount
 * ★ "언급량 추세"가 아니다. "수집된 근거의 작성일 분포"다.
 *   검색 API를 최신순(sort=date)으로 조회하므로 이 값은 실제 언급 증감이
 *   아니라 수집 창 안에서 발견된 글의 작성일 분포다 (docs/DATA_SPEC.md 8절 위험3).
 *   화면에 "추세"라고 쓰지 말 것.
 */
export interface WeekCount {
  week: string;
  count: number;
  /** 관측 창이 이 주를 온전히 덮지 못했다. 화면에서 흐리게 표시할 것 */
  partial: boolean;
}

/** models.py: ServiceMention — ★ name 은 원문에 글자 그대로 있는 것만 */
export interface ServiceMention {
  name: string;
  count: number;
}

/**
 * models.py: ProblemSignals — 근거 상세 페이지의 집계값.
 *
 * ★★ 전부 백엔드가 센 값이다. LLM 산출물이 아니다.
 * ★ 단 severity_* / role_* / age_* / gender_* / mentioned_services 는
 *   "AI 라벨을 센 것"이므로 화면에서 case_count(순수 DB 집계)와 구분
 *   표기해야 한다 (DATA_SPEC 4절). [AI 판정] 배지를 붙일 것.
 * ★ *_labeled_count 는 분모다. 분모 없이 건수만 보여주면 오해된다.
 *   *_labeled_count 가 작으면(백엔드 settings.MIN_LABELED_TO_SHOW 미만)
 *   그 분포는 화면에서 아예 숨긴다.
 */
export interface ProblemSignals {
  // ⑧ 이 문제를 믿어도 되는가 — 표본의 폭
  source_kind_counts: Record<string, number>;
  /** ★ source_count = Object.keys(source_name_counts).length 와 같다 */
  source_name_counts: Record<string, number>;

  // ④ 얼마나 꾸준히 나타나나 — 시간 분포. '화제성'이라 부르지 말 것
  first_posted_at: string | null;
  last_posted_at: string | null;
  observed_weeks: number;
  weekly_counts: WeekCount[];
  /** posted_at 이 없어 시간 분포에서 빠진 건수. 지식iN·카페는 작성일이 없다 */
  undated_count: number;

  // ⑦ 얼마나 불편해하나 — AI 라벨의 합
  severity_counts: Record<string, number>;
  severity_labeled_count: number;
  need_signal_count: number;
  signal_type_counts: Record<string, number>;

  // ① 돈이 걸린 문제인가
  payment_signal_count: number;

  // ⑤ 누가 겪고 있나 — 주력은 source_kind_counts. 이건 보조
  role_counts: Record<string, number>;
  role_labeled_count: number;
  age_counts: Record<string, number>;
  age_labeled_count: number;
  gender_counts: Record<string, number>;
  gender_labeled_count: number;

  // ② 이미 나와 있는 것들 — '리뷰 불만'은 담지 않는다 (리뷰는 출처에 없음)
  mentioned_services: ServiceMention[];
}

/**
 * models.py: PublishGate — docs/DATA_COLLECTION.md 6절 게시 기준.
 * ★ 근거 페이지 ⑧ 블록이 그대로 보여준다. 기준 수치도 함께 노출할 것 —
 *   기준을 숨기고 ✓만 보여주면 그것도 근거 없는 신뢰 표시가 된다.
 */
export interface PublishGate {
  case_count_ok: boolean;
  source_count_ok: boolean;
  evidence_count_ok: boolean;
  passed: boolean;
  /** 미달 사유. 통과면 빈 문자열 */
  reason: string;
  /** 백엔드가 실제 판정에 사용한 기준. 프론트에서 따로 하드코딩하지 않는다. */
  min_cases: number;
  min_sources: number;
  min_evidence: number;
}

/**
 * models.py: Problem — 게시된 문제정의.
 *
 * ★ case_count / source_count 는 백엔드 DB가 센 값이다.
 *   LLM이 만든 값이 아니므로 화면에 그대로 표시해도 된다.
 */
export interface Problem {
  id: string;
  title: string;
  one_liner: string;
  category: Category;
  /** AI가 쓴 서술 — 화면에서 근거와 구분해 표시할 것 */
  description: string;
  /** AI가 쓴 서술 */
  context: string;
  /** AI가 쓴 서술 — "③ 만들기에 얼마나 복잡한가". 서술형만, 점수·등급 없음 */
  complexity_note: string;
  /** 실제 수집된 근거 — 화면에서 AI 서술과 구분해 표시할 것 */
  evidence: Evidence[];
  case_count: number;
  source_count: number;
  /** 근거 상세 페이지의 집계값 전부 */
  signals: ProblemSignals;
  /**
   * 게시된 문제는 정의상 이미 기준을 통과했다(passed는 항상 true).
   * 그래도 실제 기준 수치를 들고 다니는 이유: ⑧ 체크리스트가
   * "관련 사례 47건 ✓ (기준 20건)"처럼 보여주려면 그 수치가 필요하다.
   */
  gate: PublishGate;
  updated_at: string;
}

/* ── 아이디어 ──────────────────────────────────── */

/** models.py: ServiceForm */
export type ServiceForm =
  | '웹 서비스'
  | '모바일 앱'
  | '챗봇'
  | '브라우저 확장'
  | '자동화 스크립트';

/** models.py: Target */
export type Target = 'B2C' | 'B2B' | '1인 사업자/프리랜서';

/** models.py: Resource */
export type Resource = '1인' | '2~5인' | '전업/충분한 리소스';

/**
 * models.py: UserCondition — 개인화 조건.
 * PRD 10절: "기술 난이도"는 받지 않는다. 시스템이 추론한다.
 */
export interface UserCondition {
  service_form: ServiceForm;
  target: Target;
  resource: Resource;
  /** 최대 500자 */
  extra?: string;
}

/**
 * models.py: Idea — 아이디어.
 * 기본 아이디어와 개인화 아이디어가 같은 구조를 공유한다.
 */
export interface Idea {
  id: string;
  problem_id: string;
  name: string;
  one_liner: string;
  target: string;
  service_form: string;
  why_linked: string;
  how_it_works: string;
  core_features: string[];
  differentiator: string;
  /** 조건을 넣었을 때만 채워진다 (F07) */
  fit_reason?: string;
  /** 조건을 넣었을 때만 채워진다 (F07) */
  scope_note?: string;
}

/* ── 진행 상태 ─────────────────────────────────── */

/**
 * models.py: ProgressEvent — 실시간 생성 중 단계 알림.
 *
 * 에이전트가 한 단계 끝낼 때마다 하나씩 날아온다.
 * 화면의 진행 상태 UI가 이걸 받아 그린다.
 */
export interface ProgressEvent {
  step: string;
  index: number;
  total: number;
  done: boolean;
}
