/**
 * 개발용 가상 데이터.
 *
 * 용도
 *   1. 백엔드가 준비되기 전에 화면을 만들 때
 *   2. 서버 없이 열리는 공유용 단일 HTML  ← 이건 영원히 이 데이터를 쓴다
 *
 * ★ 여기 숫자는 전부 가짜다. 화면에 표시할 때 "예시 데이터" 임을 밝힐 것.
 *
 * 채울 것 : 문제 몇 개 + 문제별 아이디어 3~5개
 * 타입은 api/types.ts 를 따른다.
 */
import type { Idea, Problem } from '@/api/types';

export const problems: Problem[] = [];  // TODO
export const ideas: Idea[] = [];        // TODO
