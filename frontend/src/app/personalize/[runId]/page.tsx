'use client';

/**
 * F05 개인화 결과 목록.
 * 스토어에 저장된 실행(run)을 불러와 조건 칩과 함께 결과를 보여준다.
 */

import { useParams } from 'next/navigation';
import { ArrowRightIcon } from '@/components/icons';
import {
  Badge,
  ButtonLink,
  CardListSkeleton,
  EmptyState,
  PageHeader,
  Skeleton,
} from '@/components/ui';
import { IdeaCard } from '@/components/IdeaCard';
import { getProblem } from '@/lib/data';
import { useStore } from '@/lib/store';

export default function PersonalizationRunPage() {
  const { runId } = useParams<{ runId: string }>();
  const { getRun, hydrated } = useStore();

  const run = getRun(runId);

  // 결과는 로컬 스토어에만 있어 hydration 전에는 알 수 없다.
  // 빈 화면 대신 최종 레이아웃과 같은 형태의 자리 표시자를 둔다.
  if (!hydrated) {
    return (
      <div className="space-y-8">
        <PageHeader title="맞춤 아이디어" description="불러오는 중입니다…" />
        <Skeleton className="h-8 w-64" />
        <CardListSkeleton count={3} />
      </div>
    );
  }

  if (!run) {
    return (
      <EmptyState
        title="개인화 결과를 찾을 수 없습니다"
        description="브라우저를 새로고침했거나 다른 기기에서 접속하면 이전에 만든 개인화 결과가 보이지 않을 수 있습니다. 조건을 다시 입력해 새로 받아보세요."
        action={<ButtonLink href="/personalize">초개인화 시작하기</ButtonLink>}
      />
    );
  }

  const { input, ideas } = run;
  const problem = getProblem(input.problemId);

  const retryParams = new URLSearchParams({
    problem: input.problemId,
    serviceForm: input.serviceForm,
    target: input.target,
    resource: input.resource,
    ...(input.extra ? { extra: input.extra } : {}),
  });

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow={
          <span className="display text-sm tracking-[0.18em] text-ai uppercase">
            Personalized
          </span>
        }
        title="맞춤 아이디어"
        description={
          problem
            ? `"${problem.title}" 문제를 기준으로 조건에 맞게 다시 구성한 아이디어입니다.`
            : '입력한 조건에 맞게 다시 구성한 아이디어입니다.'
        }
      >
        <div className="mt-6 flex flex-wrap items-center gap-x-4 gap-y-3 rounded-2xl border border-border bg-surface px-4 py-3.5">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-xs font-semibold text-muted">적용된 조건</span>
            <Badge tone="brand">{input.serviceForm}</Badge>
            <Badge tone="brand">{input.target}</Badge>
            <Badge tone="brand">{input.resource}</Badge>
            {input.extra && <Badge tone="outline">추가 조건 반영됨</Badge>}
          </div>
          <div className="ml-auto flex flex-wrap gap-2">
            {problem && (
              <ButtonLink href={`/problems/${problem.id}`} variant="ghost" size="sm">
                원본 문제 보기
              </ButtonLink>
            )}
            <ButtonLink
              href={`/personalize?${retryParams.toString()}`}
              variant="secondary"
              size="sm"
            >
              조건 바꿔 다시 받기
              <ArrowRightIcon className="size-3.5" />
            </ButtonLink>
          </div>
        </div>
      </PageHeader>

      {ideas.length === 0 ? (
        <EmptyState
          title="이 문제에는 아직 아이디어가 없습니다"
          description="다른 문제를 기준으로 다시 시도해 주세요."
          action={<ButtonLink href="/personalize">다시 시도하기</ButtonLink>}
        />
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {ideas.map((idea) => (
            <li key={idea.id}>
              <IdeaCard
                idea={idea}
                saveKind="personalized"
                href={`/personalize/${run.id}/${idea.id}`}
              />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
