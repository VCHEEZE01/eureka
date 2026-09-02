import Link from 'next/link';
import { ArrowRightIcon, SparkIcon } from '@/components/icons';
import { SaveButton } from '@/components/SaveButton';
import { Badge, Card } from '@/components/ui';
import type { Idea, PersonalizedIdea } from '@/lib/types';

function isPersonalized(idea: Idea | PersonalizedIdea): idea is PersonalizedIdea {
  return 'fitReason' in idea;
}

/**
 * 아이디어 카드 (F04 기본 아이디어 / F05 개인화 결과 공용).
 * 개인화 결과에는 "내 조건에 맞는 이유"가 추가로 붙는다.
 *
 * 저장 버튼이 카드 안에 있어 카드 전체를 링크로 덮지 않는다. 대신 제목 링크를
 * group hover로 강조해 어디를 눌러야 하는지 드러낸다.
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
    <Card interactive className="group flex h-full flex-col">
      <div className="flex flex-wrap items-center gap-1.5">
        <Badge tone="ai" icon={<SparkIcon />}>
          AI 추천 후보
        </Badge>
        <Badge tone="outline">{idea.serviceForm}</Badge>
      </div>

      <h3 className="kr-text mt-3 text-lg leading-snug font-bold tracking-tight">
        <Link href={href} className="focus-ring rounded transition-colors group-hover:text-brand-strong">
          {idea.name}
        </Link>
      </h3>
      <p className="kr-text mt-1.5 text-sm leading-relaxed text-muted">{idea.oneLiner}</p>

      <dl className="mt-4 space-y-3 text-sm">
        <div className="flex gap-2">
          <dt className="w-20 shrink-0 text-xs font-semibold text-muted">주요 타깃</dt>
          <dd className="kr-text min-w-0 flex-1 text-sm">{idea.target}</dd>
        </div>
        <div className="flex gap-2">
          <dt className="w-20 shrink-0 text-xs font-semibold text-muted">연결 이유</dt>
          <dd className="kr-text min-w-0 flex-1 text-sm text-foreground/80">{idea.whyLinked}</dd>
        </div>
      </dl>

      {isPersonalized(idea) && (
        <div className="mt-4 rounded-xl border border-ai/20 bg-ai-soft/70 px-3.5 py-3">
          <p className="flex items-center gap-1.5 text-xs font-bold text-ai">
            <SparkIcon className="size-3.5" />내 조건에 맞는 이유
          </p>
          <p className="kr-text mt-1.5 text-sm leading-relaxed text-foreground/85">
            {idea.fitReason}
          </p>
        </div>
      )}

      <div className="mt-auto flex items-center justify-between gap-3 border-t border-border pt-4 sm:pt-5">
        <Link
          href={href}
          className="focus-ring inline-flex items-center gap-1 rounded text-sm font-semibold text-brand hover:underline"
        >
          왜 이 아이디어인가?
          <ArrowRightIcon className="size-3.5" />
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
