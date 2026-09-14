/**
 * 프론트엔드 내부에서만 쓰는 타입.
 *
 * ★ 백엔드와 주고받는 타입은 여기가 아니라 api/types.ts 에 있다. 섞지 말 것.
 *
 * 여기 둘 것 : 화면 상태, 필터 값, 저장 항목, 타겟 프로필 등 백엔드가 모르는 것.
 */
import type { Idea, Problem, Resource, ServiceForm, Target } from '@/api/types';

/* ── 문제 목록 정렬 ────────────────────────────────────────────── */

export const SORT_OPTIONS = ['cases', 'latest'] as const;
export type SortOption = (typeof SORT_OPTIONS)[number];

export const SORT_LABEL: Record<SortOption, string> = {
  cases: '관련 사례순',
  latest: '최신순',
};

/** ★ 새 계약엔 Source[] 가 없다. source_count 를 직접 쓴다. */
export function sourceCount(problem: Problem): number {
  return problem.source_count;
}

/* ── 화면에서 분포를 숨기는 최소 표본 기준 ────────────────────────
 * 백엔드 settings.MIN_LABELED_TO_SHOW(=3) 와 같은 값.
 * "1건 중 1건 = 100%" 는 분모를 붙여도 오해를 부르므로 아예 숨긴다.
 */
export const MIN_LABELED_TO_SHOW = 3;

/* ── F05 문제정의 조합 (현재 잠금 상태 — 타입만 유지) ─────────────── */

export const COMBINE_MAX = 3;

export interface CombinedProblem {
  id: string;
  title: string;
  description: string;
  sourceProblemIds: string[];
  sharedEvidence: string[];
  totalCaseCount: number;
}

/* ── F07 개인화 (현재 잠금 상태 — 타입만 유지) ────────────────────── */

export const EXTRA_MAX = 500;

export interface PersonalizeInput {
  problemId: string;
  serviceForm: ServiceForm;
  target: Target;
  resource: Resource;
  extra?: string;
}

export interface PersonalizedIdea extends Idea {
  fitReason: string;
  scopeNote: string;
  difficulty: '낮음' | '중간' | '높음';
  matchScore: number;
}

export interface PersonalizeRun {
  id: string;
  createdAt: string;
  input: PersonalizeInput;
  combined?: CombinedProblem;
  ideas: PersonalizedIdea[];
}

/* ── F09 즐겨찾기 / 보관함 ─────────────────────────────────────── */

export type SavedKind = 'problem' | 'idea' | 'personalized';

export interface SavedItem {
  key: string;
  kind: SavedKind;
  refId: string;
  savedAt: string;
  title: string;
  subtitle: string;
  path: string;
}

export function savedKey(kind: SavedKind, refId: string): string {
  return `${kind}:${refId}`;
}

/* ── 타겟 설정 (온보딩 교체, 2026-09-11) ───────────────────────────
 * ★ 관심분야·출처 선택 온보딩을 대체한다. 백엔드는 이 값을 모른다 —
 *   근거와의 대조는 프론트에서 evidence[].summary 부분 문자열 매칭으로만 한다.
 */

/** 드롭다운 표시용. 실제 저장값(AgeBand)은 '미선택'을 제외한다. */
export const AGE_BANDS = ['미선택', '10대', '20대', '30대', '40대', '50대 이상'] as const;
export type AgeBand = Exclude<(typeof AGE_BANDS)[number], '미선택'>;

export const GENDERS = ['미선택', '여성', '남성'] as const;
export type Gender = Exclude<(typeof GENDERS)[number], '미선택'>;

/** 연령·성별·직업·태그·장소 4개 중 최소 이 개수를 채워야 시작할 수 있다. */
export const TARGET_MIN_FILLED = 2;
/** 직업·장소 각각의 칩 개수 상한. */
export const TARGET_TOKEN_MAX = 5;

export interface TargetProfile {
  age: AgeBand | null;
  gender: Gender | null;
  jobs: string[];
  places: string[];
}

export const EMPTY_TARGET: TargetProfile = { age: null, gender: null, jobs: [], places: [] };

/** 4개 항목(연령·성별·직업·장소) 중 채워진 항목 수. */
export function filledCount(t: TargetProfile): number {
  let n = 0;
  if (t.age) n += 1;
  if (t.gender) n += 1;
  if (t.jobs.length > 0) n += 1;
  if (t.places.length > 0) n += 1;
  return n;
}
