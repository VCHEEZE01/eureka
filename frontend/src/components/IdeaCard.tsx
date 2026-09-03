import Link from 'next/link';
import { SaveButton } from '@/components/SaveButton';
import { Badge, Card } from '@/components/ui';
import type { Idea, PersonalizedIdea } from '@/lib/types';

function isPersonalized(idea: Idea | PersonalizedIdea): idea is PersonalizedIdea {
  return 'fitReason' in idea;
}

/**
 * 아이디어 카드 (F04 기본 아이디어 / F05 개인화 결과 공용).
 * 개인화 결과에는 "내 조건에 맞는 이유"가 추가로 붙는다.
 */
export function IdeaCard({
  idea,
  href,
  saveKind = 'idea',
}: {
  idea: Idea | PersonalizedIdea;
  /** 상세로 가는 경로. 개인화 결과는 실행 id가 포함된 경로를 넘긴다. */
  href: string;
  saveKind?: 'idea' | 'personalized';
}) {
  return (
    <Card className="flex h-full flex-col">
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone="ai">AI 추천 후보</Badge>
        <Badge>{idea.serviceForm}</Badge>
      </div>

      <h3 className="kr-text mt-3 text-base font-bold">
        <Link href={href} className="hover:text-brand">
          {idea.name}
        </Link>
      </h3>
      <p className="kr-text mt-2 text-sm text-muted">{idea.oneLiner}</p>

      <dl className="mt-4 space-y-3 text-sm">
        <div>
          <dt className="text-xs font-semibold text-muted">주요 타깃</dt>
          <dd className="kr-text mt-0.5">{idea.target}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold text-muted">문제와 연결되는 이유</dt>
          <dd className="kr-text mt-0.5 text-foreground/80">{idea.whyLinked}</dd>
        </div>
        {isPersonalized(idea) && (
          <div className="rounded-xl bg-ai-soft px-3 py-2.5">
            <dt className="text-xs font-semibold text-ai">내 조건에 맞는 이유</dt>
            <dd className="kr-text mt-0.5 text-foreground/80">{idea.fitReason}</dd>
          </div>
        )}
      </dl>

      <div className="mt-auto flex items-center justify-between gap-3 pt-5">
        <Link href={href} className="text-sm font-semibold text-brand hover:underline">
          왜 이 아이디어인가? →
        </Link>
        <SaveButton
          kind={saveKind}
          refId={idea.id}
          title={idea.name}
          subtitle={idea.oneLiner}
          href={href}
          size="sm"
        />
      </div>
    </Card>
  );
}
