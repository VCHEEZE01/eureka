'use client';
/**
 * 문제정의 조합 (PRD F05) — ★개인화 포인트 1
 *
 * 목적 : 여러 문제를 조합해 새로운 문제정의를 만든다
 * 입력 : 선택한 문제 2~3개 (기존 검증된 문제 중에서만)
 * 출력 : 새로 생성된 문제정의 + 근거 요약
 * 예외 : 1개만 선택하면 조합 비활성화
 * 정책 : 임의 텍스트 입력 불가 · 분기 없음(개인화로만 이어짐) · 로그인 필요
 *
 * ★ 진행 상태 UI 필요 — api/client.ts 의 combine() 이 onProgress 를 준다
 */

/** 3-1. 선택한 문제 확인 */
export function CombineConfirmScreen() {
  return null; // TODO: 프론트 담당자가 구현
}

/** 3-2. 조합된 문제정의 */
export function CombinedDetailScreen({ combinedId }: { combinedId: string }) {
  return null; // TODO: 프론트 담당자가 구현
}
