import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { BasicIdeas } from '@/components/ideas/BasicIdeas';
import { Badge, Breadcrumbs, PageHeader } from '@/components/ui';
import { getAllProblems, getProblem } from '@/lib/data';

/** F04 문제 기반 기본 아이디어. 비로그인으로 열람 가능하다. */

type Props = { params: Promise<{ id: string }> };

export function generateStaticParams() {
  return getAllProblems().map((problem) => ({ id: problem.id }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const problem = getProblem(id);
  return { title: problem ? `${problem.title} — 기본 아이디어` : '기본 아이디어' };
}

export default async function BasicIdeasPage({ params }: Props) {
  const { id } = await params;
  const problem = getProblem(id);
  if (!problem) notFound();

  return (
    <div className="space-y-8">
      <Breadcrumbs
        items={[
          { label: '문제 탐색', href: '/problems' },
          { label: '문제 상세', href: `/problems/${problem.id}` },
          { label: '기본 아이디어' },
        ]}
      />

      <PageHeader
        eyebrow={<Badge tone="brand">{problem.category}</Badge>}
        title={problem.title}
        description="이 문제에서 나올 수 있는 서로 다른 해결 방향입니다. 별도 입력 없이 바로 확인할 수 있습니다."
      />

      <BasicIdeas problem={problem} />
    </div>
  );
}
