'use client';

/**
 * F06 아이디어 상세 / Why This Idea — 개인화 결과 버전.
 * 기본 아이디어 상세와 같은 구조를 공유하되, "사용자 조건에 적합한 이유"와
 * scopeNote(리소스 기준 범위 · 참고용 기술 난이도)가 추가된다.
 */

import { useParams } from 'next/navigation';
import { ArrowLeftIcon, SparkIcon } from '@/components/icons';
import {
  Badge,
  ButtonLink,
  Card,
  EmptyState,
  OriginLabel,
  PageHeader,
  Skeleton,
} from '@/components/ui';
import { SaveButton } from '@/components/SaveButton';
import { useStore } from '@/lib/store';

export default function PersonalizedIdeaPage() {
  const { runId, ideaId } = useParams<{ runId: string; ideaId: string }>();
  const { getRun, hydrated } = useStore();

  const run = getRun(runId);
  const idea = run?.ideas.find((i) => i.id === ideaId);

  if (!hydrated) {
    return (
      <div className="space-y-8">
        <PageHeader title="왜 이 아이디어인가" description="불러오는 중입니다…" />
        <Skeleton className="h-40" />
        <Skeleton className="h-64" />
      </div>
    );
  }

  if (!run || !idea) {
    return (
      <EmptyState
        title="아이디어를 찾을 수 없습니다"
        description="브라우저를 새로고침했거나 다른 기기에서 접속하면 이전 개인화 결과가 보이지 않을 수 있습니다."
        action={<ButtonLink href="/personalize">초개인화 다시 시작하기</ButtonLink>}
      />
    );
  }

  return (
    <article className="space-y-12">
      <div className="space-y-5">
        <ButtonLink href={`/personalize/${run.id}`} variant="ghost" size="sm" className="-ml-3">
          <ArrowLeftIcon className="size-3.5" />
          맞춤 아이디어 목록으로
        </ButtonLink>

        <PageHeader
          eyebrow={
            <>
              <OriginLabel origin="ai" />
              <Badge tone="outline">{idea.serviceForm}</Badge>
            </>
          }
          title={idea.name}
          description={idea.oneLiner}
          aside={
            <SaveButton
              kind="personalized"
              refId={idea.id}
              title={idea.name}
              subtitle={idea.oneLiner}
              href={`/personalize/${run.id}/${idea.id}`}
            />
          }
        >
          <dl className="mt-7 grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl border border-border bg-surface px-4 py-3">
              <dt className="text-xs font-semibold text-muted">주요 타깃</dt>
              <dd className="kr-text mt-1 font-medium">{idea.target}</dd>
            </div>
            <div className="rounded-xl border border-border bg-surface px-4 py-3">
              <dt className="text-xs font-semibold text-muted">서비스 형태</dt>
              <dd className="kr-text mt-1 font-medium">{idea.serviceForm}</dd>
            </div>
          </dl>
        </PageHeader>
      </div>

      <section>
        <h2 className="kr-text text-lg font-bold tracking-tight">해결 방식</h2>
        <p className="kr-text mt-3 leading-relaxed text-foreground/85">{idea.howItWorks}</p>
      </section>

      <section>
        <h2 className="kr-text text-lg font-bold tracking-tight">핵심 기능</h2>
        <ul className="mt-4 grid gap-2.5 sm:grid-cols-2">
          {idea.coreFeatures.map((feature) => (
            <li
              key={feature}
              className="kr-text flex gap-2.5 rounded-xl border border-border bg-surface px-4 py-3 text-sm leading-relaxed text-foreground/85"
            >
              <span className="mt-2 size-1.5 shrink-0 rounded-full bg-brand" aria-hidden />
              {feature}
            </li>
          ))}
        </ul>
      </section>

      {/* AI 서술 3종(차별점·연결 이유·적합 이유)을 하나의 보라 영역으로 묶는다. */}
      <section className="rounded-2xl border border-ai/25 bg-ai-soft/60 p-5 sm:p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="kr-text flex items-center gap-2 text-lg font-bold tracking-tight text-ai">
            <SparkIcon />왜 이 아이디어인가?
          </h2>
          <OriginLabel origin="ai" />
        </div>
        <div className="mt-5 space-y-5">
          <div>
            <h3 className="text-sm font-bold text-ai">차별점</h3>
            <p className="kr-text mt-1.5 leading-relaxed text-foreground/85">
              {idea.differentiator}
            </p>
          </div>
          <div className="border-t border-ai/20 pt-5">
            <h3 className="text-sm font-bold text-ai">문제와 연결되는 이유</h3>
            <p className="kr-text mt-1.5 leading-relaxed text-foreground/85">{idea.whyLinked}</p>
          </div>
          <div className="border-t border-ai/20 pt-5">
            <h3 className="text-sm font-bold text-ai">내 조건에 적합한 이유</h3>
            <p className="kr-text mt-1 text-xs text-muted">
              입력한 형태·타깃·리소스·추가 조건을 반영해 이 아이디어를 골라 다시 구성한
              이유입니다.
            </p>
            <p className="kr-text mt-2 leading-relaxed text-foreground/85">{idea.fitReason}</p>
          </div>
        </div>
      </section>

      <section>
        <h2 className="kr-text text-lg font-bold tracking-tight">리소스 기준 범위 안내</h2>
        <Card className="mt-3" tone="muted">
          <p className="kr-text leading-relaxed text-foreground/85">{idea.scopeNote}</p>
        </Card>
      </section>
    </article>
  );
}
