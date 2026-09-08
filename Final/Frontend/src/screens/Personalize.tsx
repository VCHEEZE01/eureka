'use client';
/**
 * 개인화 (PRD F07) — ★개인화 포인트 3
 *
 * 목적 : 기본 아이디어로 부족한 사용자가 조건에 맞게 좁히게 한다
 * 입력 : 기준 문제(자동) · 형태 · 타깃 · 리소스 · 추가 조건(500자, 선택)
 * 출력 : 개인화 아이디어 3~5개 + 조건 적합 이유 + 권장 범위
 * 예외 : 필수 입력 누락 시 제출 차단 / 실패·시간초과 시 재시도 안내
 * 정책 : 로그인 필요 · 원본 문제와의 연결 유지
 *
 * ★ "기술 난이도" 슬라이더는 입력받지 않는다 (PRD 10절)
 *   리소스를 바탕으로 시스템이 추론해 결과에만 표시한다
 *
 * ★ 진행 상태 UI 필요 — api/client.ts 의 personalize() 가 onProgress 를 준다
 */

/** 조건 입력 폼 */
export function PersonalizeFormScreen({ baseId }: { baseId: string }) {
  return null; // TODO: 프론트 담당자가 구현
}

/** 결과 목록 */
export function PersonalizeResultScreen({ id }: { id: string }) {
  return null; // TODO: 프론트 담당자가 구현
}

/** 결과 상세 */
export function PersonalizedIdeaDetailScreen({ id, ideaId }: { id: string; ideaId: string }) {
  return null; // TODO: 프론트 담당자가 구현
}
