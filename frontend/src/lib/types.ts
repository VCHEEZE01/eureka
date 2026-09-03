/**
 * 유레카 도메인 타입.
 * PRD 6. Functional Requirements (F02~F07) 기준.
 * 모든 화면/에이전트가 공유하는 단일 계약이므로 임의 변경 금지.
 */

/* ── 문제 (F02, F03) ───────────────────────────────────────────── */

/**
 * 활성 카테고리.
 * 앞의 3개는 PRD가 정한 MVP 카테고리이고,
 * 뒤의 5개는 PRD 6절 F02가 "향후 데이터 확보 시 확장 가능"으로 든 임시 카테고리다.
 */
export const CATEGORIES = [
  '생산성/업무',
  '커리어/자기계발',
  '라이프스타일',
  '재테크/금융',
  '건강',
  '반려동물',
  '육아',
  '주거/생활',
] as const;
export type Category = (typeof CATEGORIES)[number];

export const SORT_OPTIONS = ['latest', 'cases'] as const;
export type SortOption = (typeof SORT_OPTIONS)[number];

export const SORT_LABEL: Record<SortOption, string> = {
  latest: '최신순',
  cases: '관련 사례순',
};

/** 근거가 수집된 플랫폼 종류. 출처 분포 표시에 사용. */
export type SourcePlatform = '커뮤니티' | '리뷰' | '뉴스' | '소셜';

export interface Source {
  id: string;
  /** 출처 매체명 (예: "OO 개발자 커뮤니티") */
  name: string;
  platform: SourcePlatform;
  /** 원문 링크. 재배포가 허용된 경우에만 존재한다. */
  url?: string;
  /** 이 출처에서 수집된 관련 사례 수 */
  caseCount: number;
}

/**
 * 실제 사용자 불편 1건. PRD F03: 원문 전체 복제 대신 요약이 기본이며
 * `excerpt`(짧은 발췌)는 허용된 경우에만 채운다.
 */
export interface EvidenceItem {
  id: string;
  /** 서비스가 정리한 불편 요약 */
  summary: string;
  /** 허용된 경우에만 제공되는 짧은 원문 발췌 */
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
  /** 서비스가 작성한 문제 설명 (AI/서비스 서술 영역) */
  description: string;
  /** 문제가 발생하는 맥락 */
  context: string;
  /** 실제 사용자 불편 요약 3~5건 (근거 영역) */
  evidence: EvidenceItem[];
  sources: Source[];
  /** 수집 데이터 내 관련 사례 수. evidence 길이가 아니라 수집 전체 기준. */
  caseCount: number;
  /** 비슷한 문제 2~3개 */
  relatedProblemIds: string[];
  /** 최신순 정렬 기준 (ISO 8601) */
  updatedAt: string;
}

/** 발견된 출처 수. sources 배열에서 파생되므로 별도 필드를 두지 않는다. */
export function sourceCount(problem: Problem): number {
  return problem.sources.length;
}

/* ── 아이디어 (F04, F05, F06) ──────────────────────────────────── */

export const SERVICE_FORMS = [
  '웹 서비스',
  '모바일 앱',
  '챗봇',
  '브라우저 확장 프로그램',
  '자동화 스크립트',
] as const;
export type ServiceForm = (typeof SERVICE_FORMS)[number];

export const TARGETS = ['B2C', 'B2B', '1인 사업자/프리랜서'] as const;
export type Target = (typeof TARGETS)[number];

export const RESOURCES = ['1인', '2~5인', '전업/충분한 리소스'] as const;
export type Resource = (typeof RESOURCES)[number];

/**
 * 아이디어. PRD F04/F06 기준으로 기본 아이디어와 개인화 아이디어가
 * 동일한 상세 구조(Why This Idea)를 공유한다.
 */
export interface Idea {
  id: string;
  problemId: string;
  name: string;
  oneLiner: string;
  target: string;
  serviceForm: string;
  /** 문제와 연결되는 이유 (F04 카드 + F06 상세 공통) */
  whyLinked: string;
  /** 해결 방식 */
  howItWorks: string;
  coreFeatures: string[];
  /** 차별점 */
  differentiator: string;
}

export interface PersonalizationInput {
  problemId: string;
  serviceForm: ServiceForm;
  target: Target;
  resource: Resource;
  /** 추가 조건. 선택, 최대 500자. */
  extra?: string;
}

export const EXTRA_MAX_LENGTH = 500;

/** 개인화 결과. F06의 "사용자 조건에 적합한 이유"가 추가된다. */
export interface PersonalizedIdea extends Idea {
  /** 사용자 조건에 적합한 이유 */
  fitReason: string;
  /** 리소스 대비 권장 범위 등 시스템 참고값 */
  scopeNote: string;
  input: PersonalizationInput;
}

/** 개인화 실행 1건. 보관함에서 결과를 다시 열기 위해 보관한다. */
export interface PersonalizationRun {
  id: string;
  createdAt: string;
  input: PersonalizationInput;
  ideas: PersonalizedIdea[];
}

/* ── 저장 / 보관함 (F07) ───────────────────────────────────────── */

export type SavedKind = 'problem' | 'idea' | 'personalized';

export interface SavedItem {
  /** `${kind}:${refId}` — 동일 항목 중복 저장 방지용 키 */
  key: string;
  kind: SavedKind;
  refId: string;
  savedAt: string;
  /** 보관함 목록 렌더링용 스냅샷 (원본 삭제와 무관하게 표시) */
  title: string;
  subtitle: string;
  /** 상세로 돌아가기 위한 경로 */
  href: string;
}

export function savedKey(kind: SavedKind, refId: string): string {
  return `${kind}:${refId}`;
}

/* ── A/B/C 실험 변형 (사용자 요구사항) ─────────────────────────── */

/**
 * 기본 아이디어 화면(F04)의 CTA 구성 실험.
 * KPI "개인화 이용률" 검증을 위해 상단 헤더에서 전환한다.
 *
 * - A: 개인화 전환 버튼만 노출 (PRD 기본 동작)
 * - B: 다른 아이디어 보기(새로고침) 버튼만 노출
 * - C: 두 버튼 모두 없음 (대조군)
 */
export const VARIANTS = ['A', 'B', 'C'] as const;
export type Variant = (typeof VARIANTS)[number];

export interface VariantSpec {
  id: Variant;
  label: string;
  description: string;
  /** "내 상황에 맞게 구체화" CTA 노출 여부 */
  showPersonalizeCta: boolean;
  /** "다른 아이디어 보기" 새로고침 버튼 노출 여부 */
  showRefresh: boolean;
}

export const VARIANT_SPECS: Record<Variant, VariantSpec> = {
  A: {
    id: 'A',
    label: '개인화 전환',
    description: '기본 아이디어에서 초개인화로 넘어가는 버튼을 제공합니다.',
    showPersonalizeCta: true,
    showRefresh: false,
  },
  B: {
    id: 'B',
    label: '아이디어 새로고침',
    description: '같은 문제에서 새로운 기본 아이디어를 다시 받아봅니다.',
    showPersonalizeCta: false,
    showRefresh: true,
  },
  C: {
    id: 'C',
    label: '버튼 없음',
    description: '추가 행동 유도 없이 기본 아이디어만 보여주는 대조군입니다.',
    showPersonalizeCta: false,
    showRefresh: false,
  },
};
