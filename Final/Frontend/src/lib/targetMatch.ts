/**
 * 타겟 프로필을 실제 근거와 대조한다.
 *
 * ★ AI 서술(description·context)은 매칭 대상이 아니다 — 우리가 쓴 문장이라
 *   "간호사"라는 단어가 있어도 "간호사가 겪는 문제"라고 주장할 근거가 못 된다.
 *   매칭은 evidence[].summary 에만, 부분 문자열 포함(includes)으로 한다.
 *   형태소 분석은 하지 않는다.
 */
import type { Problem } from '@/api/types';
import type { TargetProfile } from './types';

const MIN_KEYWORD_LEN = 2;

function normalize(v: string): string {
  return v.trim();
}

function isUsableKeyword(v: string | null | undefined): v is string {
  return Boolean(v && normalize(v).length >= MIN_KEYWORD_LEN);
}

function keywordsOf(target: TargetProfile): string[] {
  const raw = [target.age, target.gender, ...target.jobs, ...target.places]
    .filter(isUsableKeyword)
    .map(normalize);
  return [...new Set(raw)];
}

export interface TargetMatch {
  keyword: string;
  evidenceCount: number;
}

export interface TargetMatchResult {
  /** 매칭된 키워드만 (0건 키워드는 빠진다) */
  matches: TargetMatch[];
  matchedEvidenceIds: string[];
  /** ★ 분모 */
  totalEvidence: number;
}

export function matchTarget(problem: Problem, target: TargetProfile): TargetMatchResult {
  const keywords = keywordsOf(target);
  const totalEvidence = problem.evidence.length;
  const matches: TargetMatch[] = [];
  const matchedIds = new Set<string>();

  for (const keyword of keywords) {
    let count = 0;
    for (const e of problem.evidence) {
      if (e.summary.includes(keyword)) {
        count += 1;
        matchedIds.add(e.raw_item_id);
      }
    }
    if (count > 0) matches.push({ keyword, evidenceCount: count });
  }

  return {
    matches: matches.sort((a, b) => b.evidenceCount - a.evidenceCount),
    matchedEvidenceIds: [...matchedIds],
    totalEvidence,
  };
}

/**
 * 주어진 키워드들(여러 개면 OR) 중 하나라도 포함된 근거 건수.
 * ProblemDetail의 "당신의 타겟과 대조" 줄 단위 표시에 쓴다
 * (예: 연령·성별을 한 줄로 묶어 보여줄 때).
 */
export function countMatchesFor(problem: Problem, keywords: (string | null | undefined)[]): number {
  const valid = keywords.filter(isUsableKeyword).map(normalize);
  if (valid.length === 0) return 0;
  return problem.evidence.filter((e) => valid.some((k) => e.summary.includes(k))).length;
}
