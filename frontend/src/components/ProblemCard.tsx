import Link from 'next/link';
import { Badge, Card } from '@/components/ui';
import type { Problem } from '@/lib/types';

/** 문제 카드 (F02). 제목·요약·카테고리·대표 근거·대표 출처·관련 사례 수. */
export function ProblemCard({ problem }: { problem: Problem }) {
  const leadEvidence = problem.evidence[0];
  const leadSource = problem.sources[0];

  return (
    <Card className="flex h-full flex-col transition-colors hover:border-brand">
      <div className="flex items-start justify-between gap-3">
        <Badge tone="brand">{problem.category}</Badge>
        <span className="shrink-0 text-xs text-muted tabular-nums">
          관련 사례 {problem.caseCount}건
        </span>
      </div>

      <h3 className="kr-text mt-3 text-base font-bold leading-snug">
        <Link href={`/problems/${problem.id}`} className="hover:text-brand">
          <span className="absolute inset-0" aria-hidden />
          {problem.title}
        </Link>
      </h3>
      <p className="kr-text mt-2 text-sm text-muted">{problem.oneLiner}</p>

      {leadEvidence && (
        <p className="kr-text mt-4 border-l-2 border-evidence pl-3 text-sm text-foreground/80">
          {leadEvidence.summary}
        </p>
      )}

      <p className="mt-auto pt-4 text-xs text-muted">
        대표 출처 {leadSource?.name ?? '—'} 외 {Math.max(problem.sources.length - 1, 0)}곳
      </p>
    </Card>
  );
}

/** 카드 전체를 클릭 영역으로 쓰기 위한 relative 래퍼. */
export function ProblemCardLink({ problem }: { problem: Problem }) {
  return (
    <li className="relative">
      <ProblemCard problem={problem} />
    </li>
  );
}
