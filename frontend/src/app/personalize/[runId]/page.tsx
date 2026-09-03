'use client';

/**
 * F05 개인화 결과 목록.
 * 스토어에 저장된 실행(run)을 불러와 조건 칩과 함께 결과를 보여준다.
 */

import { useParams } from 'next/navigation';
import { Badge, ButtonLink, EmptyState, SectionTitle } from '@/components/ui';
import { IdeaCard } from '@/components/IdeaCard';
import { getProblem } from '@/lib/data';
import { useStore } from '@/lib/store';

export default function PersonalizationRunPage() {
  const { runId } = useParams<{ runId: string }>();
  const { getRun, hydrated } = useStore();

  const run = getRun(runId);

  if (!hydrated) {
    return (
      <div className="space-y-6">
        <SectionTitle title="맞춤 아이디어" description="불러오는 중입니다…" />
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
      <SectionTitle
        title="맞춤 아이디어"
        description={
          problem
            ? `"${problem.title}" 문제를 기준으로 조건에 맞게 다시 구성한 아이디어입니다.`
            : '입력한 조건에 맞게 다시 구성한 아이디어입니다.'
        }
        aside={
          <div className="flex flex-wrap gap-2">
            {problem && (
              <ButtonLink href={`/problems/${problem.id}`} variant="ghost">
                원본 문제 보기
              </ButtonLink>
            )}
            <ButtonLink
              href={`/personalize?${retryParams.toString()}`}
              variant="secondary"
            >
              조건 바꿔 다시 받기
            </ButtonLink>
          </div>
        }
      />

      <div className="flex flex-wrap gap-2">
        <Badge tone="brand">{input.serviceForm}</Badge>
        <Badge tone="brand">{input.target}</Badge>
        <Badge tone="brand">{input.resource}</Badge>
        {input.extra && <Badge>추가 조건 반영됨</Badge>}
      </div>

      {ideas.length === 0 ? (
        <EmptyState
          title="이 문제에는 아직 아이디어가 없습니다"
          description="다른 문제를 기준으로 다시 시도해 주세요."
          action={<ButtonLink href="/personalize">다시 시도하기</ButtonLink>}
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {ideas.map((idea) => (
            <IdeaCard
              key={idea.id}
              idea={idea}
              saveKind="personalized"
              href={`/personalize/${run.id}/${idea.id}`}
            />
          ))}
        </div>
      )}
    </div>
  );
}
