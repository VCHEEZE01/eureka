/**
 * F05 문제정의 조합 + F07 개인화의 로컬 생성기.
 *
 * 프로토타입이므로 API·LLM 호출 없이 시드 데이터를 사용자 입력에 맞춰 재구성한다.
 * Math.random()은 쓰지 않는다 — 같은 입력이면 항상 같은 결과가 나와야
 * 보관함에서 다시 열었을 때 내용이 바뀌지 않는다.
 */

import { getIdeasFor } from '@/data/ideas';
import { getProblem } from '@/data/problems';
import {
  type CombinedProblem,
  type Idea,
  type PersonalizedIdea,
  type PersonalizeInput,
  type Problem,
} from './types';

/** djb2 변형. 결정론적 변주에만 쓴다. */
function hash(input: string): number {
  let h = 5381;
  for (let i = 0; i < input.length; i += 1) {
    h = ((h * 33) ^ input.charCodeAt(i)) >>> 0;
  }
  return h >>> 0;
}

/* ── F05 문제정의 조합 ─────────────────────────────────────────── */

export function combineId(problemIds: string[]): string {
  return `c-${hash([...problemIds].sort().join('|')).toString(36)}`;
}

/**
 * 선택한 문제 2~3개를 하나의 문제정의로 합친다.
 * PRD F05: 검증된 기존 문제끼리만 조합하며 임의 텍스트 입력은 받지 않는다.
 */
export function combineProblems(problemIds: string[]): CombinedProblem | null {
  const picked = problemIds.map(getProblem).filter((p): p is Problem => Boolean(p));
  if (picked.length < 2) return null;

  const categories = [...new Set(picked.map((p) => p.category))];
  const scopeLabel = categories.length === 1 ? categories[0] : '여러 영역';

  return {
    id: combineId(problemIds),
    title: `${picked.map((p) => shortLabel(p)).join(' + ')}이(가) 함께 겹치는 문제`,
    description:
      `${scopeLabel}에서 나온 ${picked.length}개 문제를 하나로 묶었습니다. ` +
      `각 문제는 따로 보면 별개지만, 근거를 겹쳐 보면 ` +
      `"${commonThread(picked)}"라는 공통 지점이 드러납니다. ` +
      `이 조합은 개별 문제보다 범위가 넓으므로 해결 방식도 달라집니다.`,
    sourceProblemIds: picked.map((p) => p.id),
    sharedEvidence: picked.map((p) => `${shortLabel(p)}: ${p.evidence[0].summary}`),
    totalCaseCount: picked.reduce((sum, p) => sum + p.caseCount, 0),
  };
}

/** 제목이 길어 조합 제목에 그대로 못 넣으므로 짧게 줄인다. */
function shortLabel(p: Problem): string {
  const head = p.title.split(/[을를이가은는]\s|\s/)[0];
  return head.length > 12 ? `${head.slice(0, 12)}…` : head;
}

/** 조합된 문제들의 공통 성격을 한 구절로 표현한다. */
function commonThread(picked: Problem[]): string {
  const threads = [
    '기록은 남는데 다시 꺼내 쓰는 단계가 빠져 있다',
    '개인이 노력해도 구조가 그대로라 반복된다',
    '입력 부담 때문에 도구가 유지되지 않는다',
    '선택지가 많아 결정 자체가 늦어진다',
  ];
  return threads[hash(picked.map((p) => p.id).join()) % threads.length];
}

/* ── F07 개인화 ────────────────────────────────────────────────── */

export function runId(input: PersonalizeInput): string {
  return `r-${hash(
    [input.problemId, input.serviceForm, input.target, input.resource, input.extra ?? ''].join('|'),
  ).toString(36)}`;
}

/**
 * 기술 난이도 참고값.
 * PRD 10절 TBD: 사용자에게 슬라이더로 입력받지 않고 시스템이 추론한다.
 * 서비스 형태와 아이디어 조합에서 파생한다.
 */
const FORM_WEIGHT: Record<string, number> = {
  '자동화 스크립트': 0,
  '챗봇': 1,
  '브라우저 확장': 1,
  '웹 서비스': 2,
  '모바일 앱': 3,
};

function difficultyOf(idea: Idea, input: PersonalizeInput): PersonalizedIdea['difficulty'] {
  const base = FORM_WEIGHT[input.serviceForm] ?? 2;
  const spread = hash(idea.id) % 2;
  const score = base + spread + (input.target === 'B2B' ? 1 : 0);
  if (score <= 1) return '낮음';
  if (score <= 3) return '중간';
  return '높음';
}

/** PRD F07: 리소스가 적을수록 기능 범위를 축소해 제안한다. */
function scopeNoteFor(idea: Idea, input: PersonalizeInput): string {
  const total = idea.coreFeatures.length;
  if (input.resource === '1인') {
    return `혼자 만든다면 핵심 기능 ${Math.min(2, total)}개(${idea.coreFeatures
      .slice(0, 2)
      .join(', ')})까지만 먼저 구현하고 나머지는 반응을 본 뒤 붙이는 것을 권합니다.`;
  }
  if (input.resource === '2~5인') {
    return `2~5인이면 기능 ${Math.min(3, total)}개까지 한 번에 가져가고, 나머지 ${Math.max(
      0,
      total - 3,
    )}개는 다음 회차로 미루는 구성이 무난합니다.`;
  }
  return `리소스가 충분하다면 ${total}개 기능을 모두 포함해도 됩니다. 다만 첫 배포는 ${idea.coreFeatures[0]}만으로 내보내 반응을 먼저 확인하는 편이 안전합니다.`;
}

/** 사용자 조건에 맞춘 이유. 어떤 입력이 어떻게 반영됐는지 드러나게 쓴다. */
function fitReasonFor(idea: Idea, input: PersonalizeInput): string {
  const formPart =
    idea.serviceForm === input.serviceForm
      ? `원래 제안 형태가 ${idea.serviceForm}라 요청하신 형태와 그대로 맞습니다.`
      : `${idea.serviceForm}로 제안됐던 아이디어를 ${input.serviceForm} 형태로 옮겨 구성했습니다.`;

  const targetPart =
    input.target === 'B2B'
      ? '조직 단위로 도입한다면 관리자 화면과 구성원 초대가 초기부터 필요합니다.'
      : input.target === '1인 사업자/프리랜서'
        ? '혼자 쓰는 상황이라 협업 기능을 빼고 개인 사용 흐름만 남겼습니다.'
        : '개인 사용자를 대상으로 첫 사용까지의 단계를 최소화하는 방향으로 봤습니다.';

  const extraPart = input.extra?.trim()
    ? ` 추가로 적어주신 "${truncate(input.extra.trim(), 40)}" 조건은 ${idea.coreFeatures[0]} 쪽에 반영해 볼 여지가 있습니다.`
    : '';

  return `${formPart} ${targetPart}${extraPart}`;
}

function truncate(text: string, max: number): string {
  return text.length > max ? `${text.slice(0, max)}…` : text;
}

/**
 * 개인화 아이디어 생성.
 * PRD F07: 결과는 3~5개. 원본 문제와의 연결을 유지한다.
 */
export function personalize(
  input: PersonalizeInput,
  combined?: CombinedProblem,
): PersonalizedIdea[] {
  // 조합 문제정의면 원본 문제들의 아이디어를 모두 후보로 삼는다.
  const pool: Idea[] = combined
    ? combined.sourceProblemIds.flatMap(getIdeasFor)
    : getIdeasFor(input.problemId);

  if (pool.length === 0) return [];

  const seed = hash(runId(input));
  const count = Math.min(pool.length, 3 + (seed % 3)); // 3~5개

  return pool
    .map((idea) => {
      // 요청한 형태와 원래 형태가 같으면 일치도를 높게 잡는다.
      const formMatch = idea.serviceForm === input.serviceForm ? 28 : 0;
      const targetMatch = idea.target.includes('1인') && input.target === '1인 사업자/프리랜서' ? 12 : 0;
      const base = 58 + (hash(`${idea.id}:${seed}`) % 14);
      return { idea, score: Math.min(97, base + formMatch + targetMatch) };
    })
    .sort((a, b) => b.score - a.score || a.idea.id.localeCompare(b.idea.id))
    .slice(0, count)
    .map(({ idea, score }) => ({
      ...idea,
      id: `${runId(input)}-${idea.id}`,
      serviceForm: input.serviceForm,
      target: input.target === 'B2C' ? idea.target : input.target,
      fitReason: fitReasonFor(idea, input),
      scopeNote: scopeNoteFor(idea, input),
      difficulty: difficultyOf(idea, input),
      matchScore: score,
    }));
}
