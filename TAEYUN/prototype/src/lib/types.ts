/**
 * 유레카 도메인 타입.
 * 근거: Eureka_PRD_v2.md 6절 Functional Requirements (F02~F09).
 * Next.js 앱과 공유용 단일 HTML이 같은 타입을 쓴다.
 */

/* ── F03 문제 탐색 ─────────────────────────────────────────────── */

/** PRD 6절 F03: MVP는 3개로 시작한다. 확장은 9절 Out of Scope. */
export const CATEGORIES = ['생산성/업무', '커리어/자기계발', '라이프스타일'] as const;
export type Category = (typeof CATEGORIES)[number];

export const SORT_OPTIONS = ['cases', 'latest'] as const;
export type SortOption = (typeof SORT_OPTIONS)[number];

export const SORT_LABEL: Record<SortOption, string> = {
  cases: '관련 사례순',
  latest: '최신순',
};

/** F02 온보딩에서 고르는 수집 범위. */
export const SOURCE_KINDS = ['커뮤니티', '블로그', '리뷰', '뉴스', '소셜'] as const;
export type SourceKind = (typeof SOURCE_KINDS)[number];

export interface Source {
  id: string;
  /** 매체명 */
  name: string;
  kind: SourceKind;
  /** 이 출처에서 수집된 관련 사례 수 */
  caseCount: number;
}

/**
 * 실제 사용자 불편 1건.
 * PRD 8절: 원문 전체 복제 대신 요약이 기본이고,
 * `excerpt`(짧은 발췌)는 허용된 경우에만 채운다.
 */
export interface Evidence {
  id: string;
  /** 서비스가 정리한 불편 요약 */
  summary: string;
  /** 허용된 경우에만 제공하는 짧은 발췌 */
  excerpt?: string;
  sourceId: string;
  /** ISO 8601 (YYYY-MM-DD) */
  postedAt: string;
}

export interface Problem {
  id: string;
  title: string;
  /** 카드에 노출되는 한 줄 요약 */
  oneLiner: string;
  category: Category;
  /** 서비스가 작성한 설명 — AI 서술 영역 */
  description: string;
  /** 문제가 발생하는 맥락 — AI 서술 영역 */
  context: string;
  /** 실제 수집된 불편 3~5건 — 근거 영역 */
  evidence: Evidence[];
  sources: Source[];
  /** 수집 전체 기준 관련 사례 수. evidence 길이와 다르다. */
  caseCount: number;
  /** 비슷한 문제 2~3개 */
  relatedIds: string[];
  updatedAt: string;
}

/** 출처 수는 sources에서 파생되므로 별도 필드를 두지 않는다. */
export function sourceCount(problem: Problem): number {
  return problem.sources.length;
}

/* ── F05 문제정의 조합 ─────────────────────────────────────────── */

/** PRD F05: 검증된 기존 문제끼리만, 최대 3개. */
export const COMBINE_MAX = 3;

export interface CombinedProblem {
  id: string;
  title: string;
  description: string;
  /** 조합에 쓰인 원본 문제 */
  sourceProblemIds: string[];
  /** 원본들에서 모은 공통 근거 요약 */
  sharedEvidence: string[];
  totalCaseCount: number;
}

/* ── F06~F08 아이디어 ──────────────────────────────────────────── */

export const SERVICE_FORMS = [
  '웹 서비스',
  '모바일 앱',
  '챗봇',
  '브라우저 확장',
  '자동화 스크립트',
] as const;
export type ServiceForm = (typeof SERVICE_FORMS)[number];

export const TARGETS = ['B2C', 'B2B', '1인 사업자/프리랜서'] as const;
export type Target = (typeof TARGETS)[number];

export const RESOURCES = ['1인', '2~5인', '전업/충분한 리소스'] as const;
export type Resource = (typeof RESOURCES)[number];

/** PRD F08: 기본 아이디어와 개인화 아이디어가 같은 상세 구조를 공유한다. */
export interface Idea {
  id: string;
  problemId: string;
  name: string;
  oneLiner: string;
  target: string;
  serviceForm: string;
  /** 이 문제와 연결되는 이유 — Why This Idea */
  whyLinked: string;
  howItWorks: string;
  coreFeatures: string[];
  differentiator: string;
}

/* ── F07 개인화 ────────────────────────────────────────────────── */

/**
 * PRD F07 + 10절 TBD: "기술 난이도" 슬라이더는 입력받지 않는다.
 * 리소스를 바탕으로 시스템이 참고값을 추론한다.
 */
export interface PersonalizeInput {
  /** 기준 문제 (조합 문제정의면 combined id) */
  problemId: string;
  serviceForm: ServiceForm;
  target: Target;
  resource: Resource;
  /** 추가 조건. 선택, 최대 500자. */
  extra?: string;
}

export const EXTRA_MAX = 500;

export interface PersonalizedIdea extends Idea {
  /** 사용자 조건에 적합한 이유 */
  fitReason: string;
  /** 리소스 대비 권장 범위 — 시스템 추론값 */
  scopeNote: string;
  /** 시스템이 추론한 기술 난이도 참고값 */
  difficulty: '낮음' | '중간' | '높음';
  /** 조건 일치도 (정렬용, 0~100) */
  matchScore: number;
}

export interface PersonalizeRun {
  id: string;
  createdAt: string;
  input: PersonalizeInput;
  /** 조합 문제정의 기반이면 그 스냅샷을 함께 보관한다 */
  combined?: CombinedProblem;
  ideas: PersonalizedIdea[];
}

/* ── F09 즐겨찾기 / 보관함 ─────────────────────────────────────── */

export type SavedKind = 'problem' | 'idea' | 'personalized';

export interface SavedItem {
  /** `${kind}:${refId}` — 중복 저장 방지 키 */
  key: string;
  kind: SavedKind;
  refId: string;
  savedAt: string;
  /** 목록 렌더링용 스냅샷 */
  title: string;
  subtitle: string;
  /** 돌아갈 경로 */
  path: string;
}

export function savedKey(kind: SavedKind, refId: string): string {
  return `${kind}:${refId}`;
}
