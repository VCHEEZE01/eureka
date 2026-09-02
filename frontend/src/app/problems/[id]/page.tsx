import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { EvidenceList } from '@/components/problem-detail/EvidenceList';
import { SourceBreakdown } from '@/components/problem-detail/SourceBreakdown';
import { ProblemCardLink } from '@/components/ProblemCard';
import { SaveButton } from '@/components/SaveButton';
import { Badge, ButtonLink, Card, OriginLabel, SectionTitle, Stat } from '@/components/ui';
import { getAllProblems, getProblem, getRelatedProblems } from '@/lib/data';
import { sourceCount } from '@/lib/types';

/** F03 문제 상세 / 근거 확인. 서비스 서술(AI)과 실제 수집 근거(evidence) 영역을 시각적으로 구분한다. */

export function generateStaticParams() {
  return getAllProblems().map((problem) => ({ id: problem.id }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const problem = getProblem(id);
  if (!problem) return {};
  return {
    title: `${problem.title} — 유레카`,
    description: problem.oneLiner,
  };
}

export default async function ProblemDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const problem = getProblem(id);
  if (!problem) notFound();

  const related = getRelatedProblems(problem);

  return (
    <div className="space-y-10">
      <section>
        <div className="flex items-start justify-between gap-3">
          <Badge tone="brand">{problem.category}</Badge>
          <SaveButton
            kind="problem"
            refId={problem.id}
            title={problem.title}
            subtitle={problem.oneLiner}
            href={`/problems/${problem.id}`}
          />
        </div>
        <h1 className="kr-text mt-3 text-2xl font-extrabold leading-tight sm:text-3xl">
          {problem.title}
        </h1>
        <p className="kr-text mt-3 text-base text-muted">{problem.oneLiner}</p>
      </section>

      <section className="grid gap-4 sm:grid-cols-2">
        <Stat label="수집 데이터 내 관련 사례 수" value={`${problem.caseCount}건`} />
        <Stat label="발견된 출처 수" value={`${sourceCount(problem)}곳`} />
      </section>

      <section className="space-y-3">
        <OriginLabel origin="ai" />
        <Card className="bg-ai-soft/40 border-ai/30">
          <h2 className="text-lg font-bold">문제 설명</h2>
          <p className="kr-text mt-2 text-sm leading-relaxed text-foreground/90">
            {problem.description}
          </p>
        </Card>
      </section>

      <section className="space-y-3">
        <OriginLabel origin="ai" />
        <Card className="bg-ai-soft/40 border-ai/30">
          <h2 className="text-lg font-bold">문제가 발생하는 맥락</h2>
          <p className="kr-text mt-2 text-sm leading-relaxed text-foreground/90">
            {problem.context}
          </p>
        </Card>
      </section>

      <section className="space-y-3">
        <OriginLabel origin="evidence" />
        <SectionTitle
          title="실제 사용자 불편"
          description="수집된 원문을 요약했으며, 허용된 경우에만 짧은 발췌와 원문 링크를 함께 표시합니다."
        />
        <EvidenceList evidence={problem.evidence} sources={problem.sources} />
      </section>

      <section className="space-y-3">
        <OriginLabel origin="evidence" />
        <SectionTitle
          title="출처 및 플랫폼별 분포"
          description="근거가 수집된 출처와, 관련 사례 수 기준 플랫폼별 비중입니다."
        />
        <SourceBreakdown sources={problem.sources} />
      </section>

      {related.length > 0 && (
        <section>
          <SectionTitle title="비슷한 문제" />
          <ul className="grid gap-4 sm:grid-cols-2">
            {related.map((relatedProblem) => (
              <ProblemCardLink key={relatedProblem.id} problem={relatedProblem} />
            ))}
          </ul>
        </section>
      )}

      <section className="flex flex-col items-start gap-3 border-t border-border pt-8 sm:flex-row sm:items-center sm:justify-between">
        <p className="kr-text text-sm text-muted">
          이 문제에서 바로 시작할 수 있는 아이디어를 확인해보세요.
        </p>
        <ButtonLink href={`/problems/${problem.id}/ideas`}>
          이 문제로 아이디어 얻기
        </ButtonLink>
      </section>
    </div>
  );
}
