/**
 * 백엔드를 부르는 유일한 곳.
 *
 * ★ 화면(screens/)에서 fetch 를 직접 쓰지 말 것. 여기 함수만 쓸 것.
 *   백엔드 주소가 바뀌거나 인증이 붙어도 이 파일만 고치면 된다.
 *
 * 백엔드 주소는 .env.local 의 NEXT_PUBLIC_API_BASE 에서 읽는다.
 */

import type { Idea, Problem, ProgressEvent, UserCondition } from './types';

const BASE = (process.env.NEXT_PUBLIC_API_BASE ?? '').replace(/\/$/, '');
export const DATA_MODE = process.env.NEXT_PUBLIC_DATA_MODE === 'demo' ? 'demo' : 'live';
export class ApiError extends Error {
  constructor(public status: number) { super(status === 404 ? '문제를 찾을 수 없습니다.' : `데이터를 불러오지 못했습니다. (${status})`); }
}
async function read<T>(route: string): Promise<T> {
  const response = await fetch(`${BASE}${route}`, { cache: 'no-store' });
  if (!response.ok) throw new ApiError(response.status);
  return response.json() as Promise<T>;
}

/* ── 읽기 (빠름 · 미리 만들어둔 것) ─────────────── */

/** F03 문제 목록 */
export async function fetchProblems(category?: string): Promise<Problem[]> {
  return read<Problem[]>(`/problems${category ? `?category=${encodeURIComponent(category)}` : ''}`);
}

/** F04 문제 상세 */
export async function fetchProblem(id: string): Promise<Problem> {
  return read<Problem>(`/problems/${encodeURIComponent(id)}`);
}

/** F06 기본 아이디어 */
export async function fetchIdeas(problemId: string): Promise<Idea[]> {
  throw new Error('미구현: GET /problems/{id}/ideas');
}

/* ── 실시간 생성 (느림 · 진행 상태를 흘려보냄) ──── */

/**
 * F05 문제정의 조합.
 *
 * ★ 보통 API처럼 답이 한 번에 오지 않는다.
 *   단계가 끝날 때마다 onProgress 가 불린다.
 */
export async function combine(
  problemIds: string[],
  onProgress?: (e: ProgressEvent) => void,
): Promise<Problem> {
  throw new Error('미구현: POST /combine (스트리밍)');
}

/** F07 개인화. combine 과 같은 방식으로 진행 상태가 온다. */
export async function personalize(
  problemId: string,
  condition: UserCondition,
  onProgress?: (e: ProgressEvent) => void,
): Promise<Idea[]> {
  throw new Error('미구현: POST /personalize (스트리밍)');
}
