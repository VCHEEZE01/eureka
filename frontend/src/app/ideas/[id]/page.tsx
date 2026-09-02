import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { ArrowRightIcon, SparkIcon } from '@/components/icons';
import { SaveButton } from '@/components/SaveButton';
import { Badge, Breadcrumbs, Card, OriginLabel, PageHeader } from '@/components/ui';
import { getAllIdeas, getIdea, getProblem } from '@/lib/data';

/** F06 아이디어 상세 / Why This Idea (기본 아이디어용). */

type Props = { params: Promise<{ id: string }> };

export function generateStaticParams() {
  return getAllIdeas().map((idea) => ({ id: idea.id }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const idea = getIdea(id);
  return { title: idea ? `${idea.name} — 왜 이 아이디어인가?` : '아이디어 상세' };
}

export default async function IdeaDetailPage({ params }: Props) {
  const { id } = await params;
  const idea = getIdea(id);
  if (!idea) notFound();
  const problem = getProblem(idea.problemId);

  return (
    <article className="space-y-12">
      <div className="space-y-5">
        <Breadcrumbs
          items={[
            { label: '문제 탐색', href: '/problems' },
            ...(problem
              ? [{ label: '기본 아이디어', href: `/problems/${problem.id}/ideas` }]
              : []),
            { label: '아이디어 상세' },
          ]}
        />

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
              kind="idea"
              refId={idea.id}
              title={idea.name}
              subtitle={idea.oneLiner}
              href={`/ideas/${idea.id}`}
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
              <span
                className="mt-2 size-1.5 shrink-0 rounded-full bg-brand"
                aria-hidden
              />
              {feature}
            </li>
          ))}
        </ul>
      </section>

      <section className="rounded-2xl border border-ai/25 bg-ai-soft/60 p-5 sm:p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="kr-text flex items-center gap-2 text-lg font-bold tracking-tight text-ai">
            <SparkIcon />왜 이 아이디어인가?
          </h2>
          <OriginLabel origin="ai" />
        </div>
        <div className="mt-5 space-y-5">
          <div>
            <h3 className="text-sm font-bold text-ai">문제와 연결되는 이유</h3>
            <p className="kr-text mt-1.5 leading-relaxed text-foreground/85">{idea.whyLinked}</p>
          </div>
          <div className="border-t border-ai/20 pt-5">
            <h3 className="text-sm font-bold text-ai">차별점</h3>
            <p className="kr-text mt-1.5 leading-relaxed text-foreground/85">
              {idea.differentiator}
            </p>
          </div>
        </div>
        <p className="kr-text mt-6 text-xs text-muted">
          이 설명은 AI가 생성한 추천 근거입니다. 시장 규모나 성공 확률을 보장하지 않습니다.
        </p>
      </section>

      {problem && (
        <Card interactive className="group">
          <p className="text-xs font-semibold text-muted">이 아이디어가 출발한 문제</p>
          <Link
            href={`/problems/${problem.id}`}
            className="focus-ring kr-text mt-1.5 flex items-center gap-2 rounded font-bold transition-colors group-hover:text-brand-strong"
          >
            {problem.title}
            <ArrowRightIcon className="size-4 shrink-0" />
          </Link>
          <p className="kr-text mt-2 text-sm text-muted">{problem.oneLiner}</p>
        </Card>
      )}
    </article>
  );
}
