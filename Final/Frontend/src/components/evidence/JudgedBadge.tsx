'use client';

/**
 * [AI 판정] 배지. DATA_SPEC 4절: AI가 라벨을 붙인 수치에는 반드시 이 배지를 붙인다.
 * 순수 DB 집계(case_count, source_count, source_kind_counts 등)에는 붙이지 않는다.
 */
export function JudgedBadge() {
  return (
    <span className="inline-flex items-center h-6 px-2 rounded-md bg-bg-subtle text-text-secondary border border-border text-[12px] font-semibold whitespace-nowrap">
      AI 판정
    </span>
  );
}
