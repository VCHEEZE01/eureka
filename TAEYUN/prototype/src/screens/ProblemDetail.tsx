'use client';

/**
 * 4. 문제 상세 / 근거 확인 (PRD F04) — ★유일한 분기 지점
 * [아이디어 보기](A) 와 [개인화하기](B) 로 갈린다.
 *
 * PRD 8절에 따라 실제 수집 근거와 AI 서술을 시각적으로 구분한다.
 * 단일 검증점수는 제공하지 않는다 — 근거 건수와 출처 수로 신뢰를 표현한다.
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
  EvidencePanel,
  PageTitle,
  buttonClass,
} from '@/components/ui';
import { getProblem, problems } from '@/data/problems';
import { NavLink } from '@/lib/nav';
import { sourceCount } from '@/lib/types';

export function ProblemDetailScreen({ problemId }: { problemId: string }) {
  const problem = getProblem(problemId);

  if (!problem) {
    return (
      <AppShell>
        <Page>
          <EmptyState
            title="문제를 찾을 수 없습니다"
            description="주소가 잘못되었거나 삭제된 문제일 수 있습니다."
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

  const sourceById = new Map(problem.sources.map((s) => [s.id, s]));
  const related = problem.relatedIds.map(getProblem).filter(Boolean);

  return (
    <AppShell>
      <Page>
        <div>
          <NavLink
            to="/problems"
            className="inline-flex items-center gap-1 text-[14px] text-text-secondary hover:text-text-primary mb-6"
          >
            <ChevronLeft size={16} aria-hidden />
            문제 탐색
          </NavLink>

          <div className="flex flex-col gap-5 prose-width">
            <Badge tone="blue">{problem.category}</Badge>
            <PageTitle>{problem.title}</PageTitle>
            <Body className="text-[17px]">{problem.oneLiner}</Body>

            <div className="flex flex-wrap items-center gap-6 pt-1">
              <Metric label="관련 사례" value={`${problem.caseCount}건`} />
              <Metric label="출처" value={`${sourceCount(problem)}곳`} />
              <Metric label="최근 갱신" value={problem.updatedAt} />
            </div>
          </div>
        </div>

        {/* ★분기 지점 — 여기서 A / B 로 갈린다 */}
        <div className="flex flex-wrap gap-3">
          <NavLink to={`/problems/${problem.id}/ideas`} className={buttonClass('primary')}>
            아이디어 보기
            <ArrowRight size={18} aria-hidden />
          </NavLink>
          <NavLink to={`/personalize/from/${problem.id}`} className={buttonClass('secondary')}>
            <SlidersHorizontal size={18} aria-hidden />
            내 조건에 맞게 개인화하기
          </NavLink>
          <SaveButton
            kind="problem"
            refId={problem.id}
            title={problem.title}
            subtitle={problem.oneLiner}
            path={`/problems/${problem.id}`}
          />
        </div>

        {/* 근거 영역 — 실제 수집 데이터 */}
        <EvidencePanel title={`사용자 불편 ${problem.evidence.length}건`}>
          <ul className="flex flex-col gap-5">
            {problem.evidence.map((e) => {
              const source = sourceById.get(e.sourceId);
              return (
                <li key={e.id} className="flex flex-col gap-2">
                  <p className="text-[16px] leading-[1.6] kr">{e.summary}</p>
                  {e.excerpt ? (
                    // PRD 8절: 원문 전체 복제 대신 허용된 짧은 발췌만
                    <p className="text-[15px] text-text-secondary kr border-l-2 border-blue pl-3 italic">
                      “{e.excerpt}”
                    </p>
                  ) : null}
                  <Caption>
                    {source?.name} · {source?.kind} · {e.postedAt}
                  </Caption>
                </li>
              );
            })}
          </ul>

          <div className="mt-6 pt-6 border-t border-blue-light">
            <p className="text-[13px] font-semibold text-blue mb-3">출처 분포</p>
            <ul className="flex flex-col gap-2.5">
              {problem.sources.map((s) => {
                const pct = Math.round((s.caseCount / problem.caseCount) * 100);
                return (
                  <li key={s.id} className="flex items-center gap-3">
                    <span className="text-[14px] w-32 shrink-0 truncate">{s.name}</span>
                    <span className="flex-1 h-1.5 rounded-full bg-blue-light overflow-hidden">
                      <span className="block h-full bg-blue rounded-full" style={{ width: `${pct}%` }} />
                    </span>
                    <span className="text-[13px] text-text-secondary w-16 text-right shrink-0">
                      {s.caseCount}건
                    </span>
                  </li>
                );
              })}
            </ul>
            <Caption className="mt-3">
              합계가 관련 사례 수와 다를 수 있습니다. 한 건이 여러 출처에서 중복 수집될 수 있기
              때문입니다.
            </Caption>
          </div>
        </EvidencePanel>

        {/* AI 서술 영역 */}
        <AiPanel title="이 문제를 이렇게 읽었습니다">
          <div className="flex flex-col gap-4 prose-width">
            <Body>{problem.description}</Body>
            <div>
              <p className="text-[15px] font-semibold mb-1.5">언제 주로 나타나나요</p>
              <Body>{problem.context}</Body>
            </div>
          </div>
        </AiPanel>

        {/* 비슷한 문제 */}
        {related.length > 0 ? (
          <section className="flex flex-col gap-5">
            <CardTitle>비슷한 문제</CardTitle>
            <ul className="grid gap-5 md:grid-cols-2">
              {related.map((p) => (
                <li key={p!.id}>
                  <NavLink to={`/problems/${p!.id}`}>
                    <Card interactive className="h-full flex flex-col gap-2">
                      <Caption>{p!.category}</Caption>
                      <p className="text-[17px] font-semibold kr">{p!.title}</p>
                      <Body>{p!.oneLiner}</Body>
                    </Card>
                  </NavLink>
                </li>
              ))}
            </ul>
          </section>
        ) : null}
      </Page>
    </AppShell>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[13px] text-text-muted mb-0.5">{label}</p>
      <p className="text-[18px] font-semibold">{value}</p>
    </div>
  );
}

/** 라우트에서 잘못된 id가 들어왔을 때를 위해 목록을 노출한다. */
export const allProblemIds = problems.map((p) => p.id);
