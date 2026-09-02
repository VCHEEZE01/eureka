/**
 * 데이터 접근 계층. 화면은 `src/data/*`를 직접 import하지 않고 이 모듈만 사용한다.
 * 실제 수집 파이프라인(F00)이 붙으면 이 파일의 구현만 교체하면 된다.
 */

import { ideas } from '@/data/ideas';
import { problems } from '@/data/problems';
import type { Category, Idea, Problem, SortOption } from './types';

export interface ProblemQuery {
  /** 검색어. 2~50자. 제목·요약·설명에서 부분 일치. */
  q?: string;
  /** 카테고리 단일 선택. 미지정이면 전체. */
  category?: Category;
  sort?: SortOption;
}

export function listProblems({
  q,
  category,
  sort = 'cases',
}: ProblemQuery = {}): Problem[] {
  const keyword = q?.trim().toLowerCase() ?? '';
  const filtered = problems.filter((problem) => {
    if (category && problem.category !== category) return false;
    if (!keyword) return true;
    return [problem.title, problem.oneLiner, problem.description, problem.context]
      .join(' ')
      .toLowerCase()
      .includes(keyword);
  });

  return [...filtered].sort((a, b) =>
    sort === 'latest'
      ? b.updatedAt.localeCompare(a.updatedAt)
      : b.caseCount - a.caseCount,
  );
}

export function getProblem(id: string): Problem | undefined {
  return problems.find((problem) => problem.id === id);
}

export function getAllProblems(): Problem[] {
  return problems;
}

/** 비슷한 문제 2~3개 (F03) */
export function getRelatedProblems(problem: Problem): Problem[] {
  return problem.relatedProblemIds
    .map(getProblem)
    .filter((p): p is Problem => Boolean(p));
}

/** 카테고리별 문제 수. 탐색 화면 필터 칩에 표시한다. */
export function countByCategory(category: Category): number {
  return problems.filter((problem) => problem.category === category).length;
}

/**
 * 문제별 기본 아이디어 풀 전체.
 * 변형 B(새로고침)에서 서로 다른 묶음을 돌려 보여주기 위해 풀은 3~5개보다 크다.
 */
export function getIdeaPool(problemId: string): Idea[] {
  return ideas.filter((idea) => idea.problemId === problemId);
}

/** 기본 아이디어 노출 개수. PRD F04: 문제당 3~5개. */
export const IDEAS_PER_VIEW = 3;

/**
 * 풀에서 `round`번째 묶음을 잘라 낸다.
 * 라운드가 늘어날수록 다음 묶음으로 순환하므로 새로고침해도 항상 결과가 있다.
 */
export function getIdeaBatch(problemId: string, round: number): Idea[] {
  const pool = getIdeaPool(problemId);
  if (pool.length === 0) return [];
  const size = Math.min(IDEAS_PER_VIEW, pool.length);
  const start = (round * size) % pool.length;
  return Array.from({ length: size }, (_, i) => pool[(start + i) % pool.length]);
}

/** 풀을 몇 번 돌면 처음으로 되돌아오는지. "새 아이디어 없음" 안내에 쓴다. */
export function ideaRoundCount(problemId: string): number {
  const pool = getIdeaPool(problemId);
  if (pool.length === 0) return 0;
  return Math.ceil(pool.length / Math.min(IDEAS_PER_VIEW, pool.length));
}

export function getIdea(id: string): Idea | undefined {
  return ideas.find((idea) => idea.id === id);
}

/** 정적 경로 생성 등에서 쓰는 전체 아이디어 목록. */
export function getAllIdeas(): Idea[] {
  return ideas;
}
