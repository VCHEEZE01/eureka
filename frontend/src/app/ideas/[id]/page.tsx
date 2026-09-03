import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { SaveButton } from '@/components/SaveButton';
import { Badge, Card, OriginLabel } from '@/components/ui';
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
    <article className="space-y-8">
      <nav className="text-sm text-muted">
        {problem && (
          <>
            <Link
              href={`/problems/${problem.id}/ideas`}
              className="hover:text-foreground"
            >
              기본 아이디어
            </Link>
            <span className="mx-2" aria-hidden>
              ›
            </span>
          </>
        )}
        <span className="text-foreground">아이디어 상세</span>
      </nav>

      <header>
        <div className="flex flex-wrap items-center gap-2">
          <OriginLabel origin="ai" />
          <Badge>{idea.serviceForm}</Badge>
        </div>
        <div className="mt-3 flex flex-wrap items-start justify-between gap-4">
          <h1 className="kr-text text-2xl font-extrabold sm:text-3xl">
            {idea.name}
          </h1>
          <SaveButton
            kind="idea"
            refId={idea.id}
            title={idea.name}
            subtitle={idea.oneLiner}
            href={`/ideas/${idea.id}`}
          />
        </div>
        <p className="kr-text mt-3 max-w-2xl text-lg text-muted">
          {idea.oneLiner}
        </p>
      </header>

      <section className="grid gap-4 sm:grid-cols-2">
        <Card>
          <h2 className="text-sm font-semibold text-muted">주요 타깃</h2>
          <p className="kr-text mt-1">{idea.target}</p>
        </Card>
        <Card>
          <h2 className="text-sm font-semibold text-muted">서비스 형태</h2>
          <p className="kr-text mt-1">{idea.serviceForm}</p>
        </Card>
      </section>

      <section>
        <h2 className="text-lg font-bold">해결 방식</h2>
        <p className="kr-text mt-2 text-foreground/85">{idea.howItWorks}</p>
      </section>

      <section>
        <h2 className="text-lg font-bold">핵심 기능</h2>
        <ul className="mt-3 space-y-2">
          {idea.coreFeatures.map((feature) => (
            <li key={feature} className="kr-text flex gap-2.5 text-foreground/85">
              <span className="mt-2 size-1.5 shrink-0 rounded-full bg-brand" aria-hidden />
              {feature}
            </li>
          ))}
        </ul>
      </section>

      <section className="rounded-2xl bg-ai-soft p-5">
        <h2 className="text-lg font-bold text-ai">왜 이 아이디어인가?</h2>
        <div className="mt-3 space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-muted">
              문제와 연결되는 이유
            </h3>
            <p className="kr-text mt-1 text-foreground/85">{idea.whyLinked}</p>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-muted">차별점</h3>
            <p className="kr-text mt-1 text-foreground/85">
              {idea.differentiator}
            </p>
          </div>
        </div>
        <p className="kr-text mt-5 text-xs text-muted">
          이 설명은 AI가 생성한 추천 근거입니다. 시장 규모나 성공 확률을
          보장하지 않습니다.
        </p>
      </section>

      {problem && (
        <section className="rounded-2xl border border-border bg-surface p-5">
          <h2 className="text-sm font-semibold text-muted">
            이 아이디어가 출발한 문제
          </h2>
          <Link
            href={`/problems/${problem.id}`}
            className="kr-text mt-1 block font-bold hover:text-brand"
          >
            {problem.title}
          </Link>
          <p className="kr-text mt-2 text-sm text-muted">{problem.oneLiner}</p>
        </section>
      )}
    </article>
  );
}
