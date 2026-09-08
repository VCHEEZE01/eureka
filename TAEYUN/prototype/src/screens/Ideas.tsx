'use client';

/**
 * 5. 문제 기반 기본 아이디어 (PRD F06) + 아이디어 상세 (F08)
 *
 * 별도 입력 없이 하나의 문제에서 여러 해결 방향을 보여준다.
 * 비로그인 열람이 가능하고, 보조 경로로 개인화에 넘어갈 수 있다(강제 아님).
 * PRD 8절: 추천 후보로만 표현하고 시장성·성공 확률은 표시하지 않는다.
 */

import { ArrowRight, ChevronLeft, SlidersHorizontal } from 'lucide-react';
import { AppShell, Page } from '@/components/AppShell';
import { SaveButton } from '@/components/SaveButton';
import {
  AiPanel,
  Badge,
  Body,
  Caption,
  Card,
  CardTitle,
  EmptyState,
  PageTitle,
  buttonClass,
} from '@/components/ui';
import { getIdea, getIdeasFor } from '@/data/ideas';
import { getProblem } from '@/data/problems';
import { NavLink } from '@/lib/nav';

/* ── 5. 기본 아이디어 목록 ─────────────────────────────────────── */

export function BasicIdeasScreen({ problemId }: { problemId: string }) {
  const problem = getProblem(problemId);
  const list = getIdeasFor(problemId);

  if (!problem) {
    return (
      <AppShell>
        <Page>
          <EmptyState
            title="문제를 찾을 수 없습니다"
            description="주소가 잘못되었을 수 있습니다."
            action={
              <NavLink to="/problems" className={buttonClass('primary')}>
                문제 목록으로
              </NavLink>
            }
          />
        </Page>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <Page>
        <div>
          <NavLink
            to={`/problems/${problem.id}`}
            className="inline-flex items-center gap-1 text-[14px] text-text-secondary hover:text-text-primary mb-6"
          >
            <ChevronLeft size={16} aria-hidden />
            문제 상세
          </NavLink>

          <div className="prose-width flex flex-col gap-4">
            <Caption>{problem.title}</Caption>
            <PageTitle>이 문제에서 나온 아이디어 {list.length}개</PageTitle>
            <Body>
              같은 문제라도 접근이 다르면 결과가 달라집니다. 서로 다른 방향으로 구성했습니다.
            </Body>
            <p className="text-[13px] text-text-muted kr">
              AI가 제시한 추천 후보입니다. 시장성이나 성공 가능성이 검증된 것은 아닙니다.
            </p>
          </div>
        </div>

        <ul className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {list.map((idea) => (
            <li key={idea.id}>
              <Card interactive className="h-full flex flex-col gap-3">
                <NavLink to={`/ideas/${idea.id}`} className="flex flex-col gap-3 flex-1">
                  <CardTitle>{idea.name}</CardTitle>
                  <Body>{idea.oneLiner}</Body>
                  <div className="flex flex-wrap gap-2 mt-1">
                    <Badge>{idea.serviceForm}</Badge>
                    <Badge>{idea.target}</Badge>
                  </div>
                </NavLink>
                <NavLink
                  to={`/ideas/${idea.id}`}
                  className="text-[14px] font-semibold text-blue inline-flex items-center gap-1"
                >
                  왜 이 아이디어인가
                  <ArrowRight size={15} aria-hidden />
                </NavLink>
              </Card>
            </li>
          ))}
        </ul>

        {/* 보조 경로 — 개인화는 강제하지 않는다 */}
        <div className="rounded-[16px] border border-border bg-bg-subtle p-8 flex flex-wrap items-center justify-between gap-5">
          <div className="prose-width">
            <p className="text-[18px] font-semibold mb-1.5 kr">
              여기까지로 충분하지 않다면
            </p>
            <Body>
              만들 형태와 타깃, 쓸 수 있는 리소스를 넣으면 그 조건에 맞게 아이디어를 다시
              좁혀드립니다.
            </Body>
          </div>
          <NavLink to={`/personalize/from/${problem.id}`} className={buttonClass('primary')}>
            <SlidersHorizontal size={18} aria-hidden />
            내 상황에 맞게 구체화
          </NavLink>
        </div>
      </Page>
    </AppShell>
  );
}

/* ── 아이디어 상세 (기본 아이디어용) ───────────────────────────── */

export function IdeaDetailScreen({ ideaId }: { ideaId: string }) {
  const idea = getIdea(ideaId);
  const problem = idea ? getProblem(idea.problemId) : undefined;

  if (!idea || !problem) {
    return (
      <AppShell>
        <Page>
          <EmptyState
            title="아이디어를 찾을 수 없습니다"
            description="주소가 잘못되었을 수 있습니다."
            action={
              <NavLink to="/problems" className={buttonClass('primary')}>
                문제 목록으로
              </NavLink>
            }
          />
        </Page>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <Page>
        <div>
          <NavLink
            to={`/problems/${problem.id}/ideas`}
            className="inline-flex items-center gap-1 text-[14px] text-text-secondary hover:text-text-primary mb-6"
          >
            <ChevronLeft size={16} aria-hidden />
            아이디어 목록
          </NavLink>

          <div className="prose-width flex flex-col gap-5">
            <Caption>{problem.title}</Caption>
            <PageTitle>{idea.name}</PageTitle>
            <Body className="text-[17px]">{idea.oneLiner}</Body>
            <div className="flex flex-wrap gap-2">
              <Badge tone="blue">{idea.serviceForm}</Badge>
              <Badge>{idea.target}</Badge>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap gap-3">
          <SaveButton
            kind="idea"
            refId={idea.id}
            title={idea.name}
            subtitle={idea.oneLiner}
            path={`/ideas/${idea.id}`}
          />
          <NavLink to={`/personalize/from/${problem.id}`} className={buttonClass('secondary')}>
            <SlidersHorizontal size={18} aria-hidden />
            내 조건으로 다시 받기
          </NavLink>
        </div>

        <IdeaBody idea={idea} />

        <section className="flex flex-col gap-4">
          <p className="text-[20px] font-semibold">이 아이디어가 나온 문제</p>
          <NavLink to={`/problems/${problem.id}`}>
            <Card interactive className="flex flex-col gap-2 max-w-[760px]">
              <Caption>{problem.category}</Caption>
              <p className="text-[17px] font-semibold kr">{problem.title}</p>
              <Body>{problem.oneLiner}</Body>
              <Caption className="mt-1">
                관련 사례 {problem.caseCount}건 · 출처 {problem.sources.length}곳
              </Caption>
            </Card>
          </NavLink>
        </section>
      </Page>
    </AppShell>
  );
}

/** 기본/개인화 아이디어가 공유하는 상세 본문 (PRD F08). */
export function IdeaBody({
  idea,
}: {
  idea: {
    whyLinked: string;
    howItWorks: string;
    coreFeatures: string[];
    differentiator: string;
  };
}) {
  return (
    <AiPanel title="Why This Idea">
      <div className="flex flex-col gap-6 prose-width">
        <Section title="이 문제와 연결되는 이유" body={idea.whyLinked} />
        <Section title="어떻게 해결하나" body={idea.howItWorks} />
        <div>
          <p className="text-[15px] font-semibold mb-2">핵심 기능</p>
          <ul className="flex flex-col gap-1.5">
            {idea.coreFeatures.map((f) => (
              <li key={f} className="text-[16px] leading-[1.6] text-text-secondary kr flex gap-2">
                <span className="text-blue shrink-0" aria-hidden>
                  ·
                </span>
                {f}
              </li>
            ))}
          </ul>
        </div>
        <Section title="차별점" body={idea.differentiator} />
      </div>
    </AiPanel>
  );
}

function Section({ title, body }: { title: string; body: string }) {
  return (
    <div>
      <p className="text-[15px] font-semibold mb-1.5">{title}</p>
      <Body>{body}</Body>
    </div>
  );
}
