import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { ArrowRightIcon } from '@/components/icons';
import { EvidenceList } from '@/components/problem-detail/EvidenceList';
import { SourceBreakdown } from '@/components/problem-detail/SourceBreakdown';
import { ProblemCardLink } from '@/components/ProblemCard';
import { SaveButton } from '@/components/SaveButton';
import {
  Badge,
  Breadcrumbs,
  ButtonLink,
  Card,
  OriginLabel,
  PageHeader,
  SectionTitle,
  Stat,
} from '@/components/ui';
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
    title: problem.title,
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
    <div className="space-y-14">
      <div className="space-y-5">
        <Breadcrumbs
          items={[
            { label: '문제 탐색', href: '/problems' },
            { label: problem.category, href: `/problems?category=${encodeURIComponent(problem.category)}` },
            { label: '문제 상세' },
          ]}
        />

        <PageHeader
          eyebrow={<Badge tone="brand">{problem.category}</Badge>}
          title={problem.title}
          description={problem.oneLiner}
          aside={
            <SaveButton
              kind="problem"
              refId={problem.id}
              title={problem.title}
              subtitle={problem.oneLiner}
              href={`/problems/${problem.id}`}
            />
          }
        >
          <div className="mt-7 grid gap-3 sm:grid-cols-3">
            <Stat
              label="관련 사례"
              value={problem.caseCount}
              unit="건"
              hint="수집 데이터 기준"
            />
            <Stat label="발견된 출처" value={sourceCount(problem)} unit="곳" />
            <Stat
              label="근거 항목"
              value={problem.evidence.length}
              unit="건"
              hint="원문 요약"
            />
          </div>
        </PageHeader>
      </div>

      {/* AI가 쓴 해석. 문제 설명과 발생 맥락을 하나의 보라 영역으로 묶어
          "여기부터 여기까지가 AI 서술"이라는 경계가 한눈에 보이게 한다. */}
      <section className="space-y-3">
        <SectionTitle title="AI가 정리한 문제" aside={<OriginLabel origin="ai" />} />
        <Card tone="ai" className="space-y-6 sm:p-6">
          <div>
            <h3 className="text-sm font-bold text-ai">문제 설명</h3>
            <p className="kr-text mt-2 leading-relaxed text-foreground/90">
              {problem.description}
            </p>
          </div>
          <div className="border-t border-ai/20 pt-6">
            <h3 className="text-sm font-bold text-ai">문제가 발생하는 맥락</h3>
            <p className="kr-text mt-2 leading-relaxed text-foreground/90">
              {problem.context}
            </p>
          </div>
        </Card>
      </section>

      <section className="space-y-3">
        <SectionTitle
          title="실제 사용자 불편"
          description="수집된 원문을 요약했으며, 허용된 경우에만 짧은 발췌와 원문 링크를 함께 표시합니다."
          aside={<OriginLabel origin="evidence" />}
        />
        <EvidenceList evidence={problem.evidence} sources={problem.sources} />
      </section>

      <section className="space-y-3">
        <SectionTitle
          title="출처 및 플랫폼별 분포"
          description="근거가 수집된 출처와, 관련 사례 수 기준 플랫폼별 비중입니다."
          aside={<OriginLabel origin="evidence" />}
        />
        <SourceBreakdown sources={problem.sources} />
      </section>

      <section className="aurora overflow-hidden rounded-2xl border border-brand/30 bg-brand-soft/50 px-6 py-8 sm:px-8">
        <p className="display text-xs tracking-[0.18em] text-brand uppercase">Next step</p>
        <h2 className="kr-text mt-2 text-xl font-extrabold tracking-tight text-balance sm:text-2xl">
          이 문제에서 바로 시작할 수 있는 아이디어
        </h2>
        <p className="kr-text mt-2 max-w-xl text-sm text-muted">
          같은 문제에서 나올 수 있는 서로 다른 해결 방향을 확인해보세요. 로그인 없이 볼 수
          있습니다.
        </p>
        <ButtonLink href={`/problems/${problem.id}/ideas`} size="lg" className="mt-6">
          이 문제로 아이디어 얻기
          <ArrowRightIcon />
        </ButtonLink>
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
    </div>
  );
}
