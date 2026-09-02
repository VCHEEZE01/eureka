/**
 * F05 초개인화 — 결정론적 로컬 생성기.
 *
 * 프로토타입이므로 API/LLM 호출 없이, 기존 시드 아이디어 풀(`getIdeaPool`)을
 * 사용자 입력에 맞춰 재구성한다. 네트워크·API 호출 금지, `Math.random()` 금지.
 * 같은 입력은 항상 같은 결과를 내야 하므로 모든 변주는 입력 문자열의 해시에서
 * 유도한다.
 */

import { getIdeaPool } from './data';
import type { Idea, PersonalizationInput, PersonalizedIdea } from './types';

/** 결과 개수. PRD F05: 3~5개. */
const MIN_RESULTS = 3;
const MAX_RESULTS = 5;

/** 문자열 → 32bit 정수 해시 (djb2 변형). 결정론적 변주에만 사용한다. */
function hashString(input: string): number {
  let hash = 5381;
  for (let i = 0; i < input.length; i += 1) {
    hash = ((hash * 33) ^ input.charCodeAt(i)) >>> 0;
  }
  return hash >>> 0;
}

/** 입력 전체를 하나의 해시로. 같은 조건이면 항상 같은 값이 나온다. */
function hashInput(input: PersonalizationInput): number {
  return hashString(
    [input.problemId, input.serviceForm, input.target, input.resource, input.extra ?? '']
      .join('|'),
  );
}

export function newRunId(input: PersonalizationInput): string {
  return `run-${hashInput(input).toString(36)}`;
}

/**
 * 기술 난이도 참고값. PRD: 사용자가 입력하는 값이 아니라 시스템이 제시하는
 * 참고값이어야 하므로, 사용자 리소스 선택이 아니라 아이디어·서비스 형태
 * 조합에서 파생한다.
 */
const DIFFICULTY_LABELS = ['낮음', '중간', '높음'] as const;

function difficultyHint(idea: Idea, serviceForm: string): (typeof DIFFICULTY_LABELS)[number] {
  return DIFFICULTY_LABELS[hashString(`${idea.id}:${serviceForm}`) % DIFFICULTY_LABELS.length];
}

/** PRD: 리소스가 적을수록 기능 범위를 축소해 제안한다. */
function buildScope(
  idea: Idea,
  input: PersonalizationInput,
): { coreFeatures: string[]; scopeNote: string } {
  const hint = difficultyHint(idea, input.serviceForm);
  const original = idea.coreFeatures.length;

  if (input.resource === '1인') {
    const coreFeatures = idea.coreFeatures.slice(0, 2);
    return {
      coreFeatures,
      scopeNote: `1인이 혼자 운영할 수 있도록 핵심 기능을 ${original}개에서 ${coreFeatures.length}개로 줄여 제안했습니다. 나머지는 이후 단계로 미룰 수 있습니다. (참고용 기술 난이도: ${hint})`,
    };
  }

  if (input.resource === '2~5인') {
    const coreFeatures = idea.coreFeatures.slice(0, 3);
    return {
      coreFeatures,
      scopeNote: `2~5인 팀이 나눠 맡을 수 있는 범위로 핵심 기능을 ${coreFeatures.length}개로 좁혀 제안했습니다. (참고용 기술 난이도: ${hint})`,
    };
  }

  return {
    coreFeatures: idea.coreFeatures,
    scopeNote: `전업 수준의 리소스를 갖췄다고 밝혀 원래 기능 구성(${original}개)을 그대로 유지했습니다. 여유가 있다면 범위를 더 넓혀 볼 수 있습니다. (참고용 기술 난이도: ${hint})`,
  };
}

function buildOneLiner(idea: Idea): string {
  // 조건은 결과 상단 칩과 카드 배지에 이미 드러나므로 한 줄 설명에 덧붙이지 않는다.
  return idea.oneLiner;
}

function buildWhyLinked(idea: Idea): string {
  // 원본 문제와의 연결은 유지하되, 카드마다 같은 문장이 반복되지 않도록
  // 출처가 되는 기본 아이디어만 한 문장으로 덧붙인다.
  return `${idea.whyLinked} 기본 아이디어 "${idea.name}"을 이번 조건에 맞게 다시 구성했습니다.`;
}

function buildHowItWorks(idea: Idea, input: PersonalizationInput): string {
  return `${idea.howItWorks} ${input.serviceForm} 형태로 만든다고 가정해도 핵심 동작 흐름은 위와 같이 유지됩니다.`;
}

function buildDifferentiator(idea: Idea, input: PersonalizationInput): string {
  if (idea.serviceForm === input.serviceForm) return idea.differentiator;
  return `${idea.differentiator} 원래는 ${idea.serviceForm}로 그려졌지만, 이번 조건에서는 ${input.serviceForm} 형태로 다시 짰습니다.`;
}

function buildFitReason(idea: Idea, input: PersonalizationInput): string {
  const parts = [
    `${input.target} 대상으로 ${input.serviceForm} 형태를 원했고, 보유 리소스로 ${input.resource}을(를) 밝혀 이 아이디어를 그 조건에 맞춰 조정했습니다.`,
  ];
  const extra = input.extra?.trim();
  if (extra) {
    parts.push(`추가로 남긴 조건("${extra}")도 방향에 반영했습니다.`);
  }
  return parts.join(' ');
}

function buildPersonalizedIdea(
  idea: Idea,
  input: PersonalizationInput,
  runHash: number,
  index: number,
): PersonalizedIdea {
  const { coreFeatures, scopeNote } = buildScope(idea, input);
  return {
    ...idea,
    id: `pi-${runHash.toString(36)}-${index}`,
    target: input.target,
    serviceForm: input.serviceForm,
    oneLiner: buildOneLiner(idea),
    whyLinked: buildWhyLinked(idea),
    howItWorks: buildHowItWorks(idea, input),
    differentiator: buildDifferentiator(idea, input),
    coreFeatures,
    fitReason: buildFitReason(idea, input),
    scopeNote,
    input,
  };
}

function resultCount(poolSize: number): number {
  if (poolSize <= MIN_RESULTS) return poolSize;
  return Math.min(MAX_RESULTS, poolSize);
}

/**
 * 문제 아이디어 풀에서 3~5개를 뽑아 사용자 조건에 맞게 재구성한다.
 * 같은 입력은 항상 같은 결과(같은 개수·같은 순서·같은 id)를 낸다.
 */
export function generatePersonalizedIdeas(input: PersonalizationInput): PersonalizedIdea[] {
  const pool = getIdeaPool(input.problemId);
  if (pool.length === 0) return [];

  const runHash = hashInput(input);
  const size = resultCount(pool.length);
  const start = runHash % pool.length;
  const picked = Array.from({ length: size }, (_, i) => pool[(start + i) % pool.length]);

  return picked.map((idea, index) => buildPersonalizedIdea(idea, input, runHash, index));
}
