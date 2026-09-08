'use client';
/**
 * 기본 아이디어 (PRD F06) + 아이디어 상세 (PRD F08)
 *
 * 목적 : 별도 입력 없이 하나의 문제에서 여러 해결 방향을 보여준다
 * 입력 : 문제 ID
 * 출력 : 아이디어 3~5개 (이름·한줄·타깃·형태·연결 이유)
 * 정책 : 비로그인 열람 허용 · 개인화는 보조 경로로만 (강제 아님)
 *
 * ★ 표현 규칙 (PRD 8절)
 *   · "추천 후보"로 표현. 검증된 것처럼 쓰지 말 것
 *   · 시장 규모·성공 확률 같은 수치 표시 금지
 */

/** 기본 아이디어 목록 (F06) */
export function BasicIdeasScreen({ problemId }: { problemId: string }) {
  return null; // TODO: 프론트 담당자가 구현
}

/** 아이디어 상세 · Why This Idea (F08) */
export function IdeaDetailScreen({ ideaId }: { ideaId: string }) {
  return null; // TODO: 프론트 담당자가 구현
}
