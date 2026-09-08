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

/** models.py: Category */
export type Category = '생산성/업무' | '커리어/자기계발' | '라이프스타일';

/** models.py: SourceKind */
export type SourceKind = '커뮤니티' | '블로그' | '리뷰' | '뉴스' | '소셜';

/* ── 문제 ─────────────────────────────────────── */

/** models.py: Evidence — 근거 1건. 반드시 원문으로 역추적된다. */
export interface Evidence {
  raw_item_id: string;
  summary: string;
  /** 허용된 경우에만 채워지는 짧은 발췌 */
  excerpt?: string;
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
  /** 실제 수집된 근거 — 화면에서 AI 서술과 구분해 표시할 것 */
  evidence: Evidence[];
  case_count: number;
  source_count: number;
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
