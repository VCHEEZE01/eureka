'use client';

/**
 * F06 아이디어 상세 / Why This Idea — 개인화 결과 버전.
 * 기본 아이디어 상세와 같은 구조를 공유하되, "사용자 조건에 적합한 이유"와
 * scopeNote(리소스 기준 범위 · 참고용 기술 난이도)가 추가된다.
 */

import { useParams } from 'next/navigation';
import { Badge, ButtonLink, Card, EmptyState, OriginLabel, SectionTitle } from '@/components/ui';
import { SaveButton } from '@/components/SaveButton';
import { useStore } from '@/lib/store';

export default function PersonalizedIdeaPage() {
  const { runId, ideaId } = useParams<{ runId: string; ideaId: string }>();
  const { getRun, hydrated } = useStore();

  const run = getRun(runId);
  const idea = run?.ideas.find((i) => i.id === ideaId);

  if (!hydrated) {
    return (
      <div className="space-y-6">
        <SectionTitle title="왜 이 아이디어인가" description="불러오는 중입니다…" />
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
    <div className="space-y-8">
      <div>
        <ButtonLink href={`/personalize/${run.id}`} variant="ghost">
          ← 맞춤 아이디어 목록으로
        </ButtonLink>
      </div>

      <div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="ai">AI 추천 후보</Badge>
          <Badge>{idea.serviceForm}</Badge>
        </div>
        <h1 className="kr-text mt-3 text-2xl font-extrabold">{idea.name}</h1>
        <p className="kr-text mt-2 text-muted">{idea.oneLiner}</p>
        <div className="mt-4">
          <SaveButton
            kind="personalized"
            refId={idea.id}
            title={idea.name}
            subtitle={idea.oneLiner}
            href={`/personalize/${run.id}/${idea.id}`}
          />
        </div>
      </div>

      <Card>
        <dl className="grid gap-5 sm:grid-cols-2">
          <div>
            <dt className="text-xs font-semibold text-muted">주요 타깃</dt>
            <dd className="kr-text mt-1 text-sm">{idea.target}</dd>
          </div>
          <div>
            <dt className="text-xs font-semibold text-muted">서비스 형태</dt>
            <dd className="kr-text mt-1 text-sm">{idea.serviceForm}</dd>
          </div>
        </dl>
      </Card>

      <section>
        <SectionTitle title="해결 방식" />
        <Card>
          <p className="kr-text text-sm text-foreground/90">{idea.howItWorks}</p>
        </Card>
      </section>

      <section>
        <SectionTitle title="핵심 기능" />
        <Card>
          <ul className="kr-text list-disc space-y-1.5 pl-5 text-sm text-foreground/90">
            {idea.coreFeatures.map((feature) => (
              <li key={feature}>{feature}</li>
            ))}
          </ul>
        </Card>
      </section>

      <section>
        <SectionTitle title="차별점" />
        <Card>
          <p className="kr-text text-sm text-foreground/90">{idea.differentiator}</p>
        </Card>
      </section>

      <section>
        <SectionTitle
          title="문제와 연결되는 이유"
          aside={<OriginLabel origin="ai" />}
        />
        <Card>
          <p className="kr-text text-sm text-foreground/90">{idea.whyLinked}</p>
        </Card>
      </section>

      <section>
        <SectionTitle
          title="사용자 조건에 적합한 이유"
          description="입력한 형태·타깃·리소스·추가 조건을 반영해 이 아이디어를 골라 다시 구성한 이유입니다."
          aside={<OriginLabel origin="ai" />}
        />
        <Card className="bg-ai-soft">
          <p className="kr-text text-sm text-foreground/90">{idea.fitReason}</p>
        </Card>
      </section>

      <section>
        <SectionTitle title="리소스 기준 범위 안내" />
        <Card>
          <p className="kr-text text-sm text-foreground/90">{idea.scopeNote}</p>
        </Card>
      </section>
    </div>
  );
}
