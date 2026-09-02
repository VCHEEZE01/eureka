import Link from 'next/link';
import { ArrowRightIcon } from '@/components/icons';
import { Badge, Card } from '@/components/ui';
import type { Problem } from '@/lib/types';

/** 문제 카드 (F02). 제목·요약·카테고리·대표 근거·대표 출처·관련 사례 수. */
export function ProblemCard({ problem }: { problem: Problem }) {
  const leadEvidence = problem.evidence[0];
  const leadSource = problem.sources[0];
  const otherSources = Math.max(problem.sources.length - 1, 0);

  return (
    <Card interactive className="group flex h-full flex-col">
      <div className="flex items-start justify-between gap-3">
        <Badge tone="brand">{problem.category}</Badge>
        <span className="shrink-0 text-xs text-muted tabular-nums">
          사례 <span className="font-semibold text-foreground">{problem.caseCount}</span>건
        </span>
      </div>

      <h3 className="kr-text mt-3 text-base leading-snug font-bold">
        <Link
          href={`/problems/${problem.id}`}
          className="transition-colors group-hover:text-brand-strong"
        >
          {/* 카드 전체를 클릭 영역으로 만든다. 부모 li가 relative. */}
          <span className="absolute inset-0 rounded-2xl" aria-hidden />
          {problem.title}
        </Link>
      </h3>
      <p className="kr-text mt-2 text-sm leading-relaxed text-muted">{problem.oneLiner}</p>

      {leadEvidence && (
        <p className="kr-text mt-4 border-l-2 border-evidence bg-evidence-soft/40 py-2 pr-2 pl-3 text-sm text-foreground/85">
          {leadEvidence.summary}
        </p>
      )}

      <div className="mt-auto flex items-end justify-between gap-3 pt-5">
        <p className="kr-text text-xs text-muted">
          {leadSource?.name ?? '출처 미상'}
          {otherSources > 0 && ` 외 ${otherSources}곳`}
        </p>
        <span className="flex items-center gap-1 text-xs font-semibold text-brand opacity-0 transition-opacity group-hover:opacity-100">
          근거 보기
          <ArrowRightIcon className="size-3.5" />
        </span>
      </div>
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
