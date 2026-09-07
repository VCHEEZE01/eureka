'use client';

/**
 * 3-1. 문제정의 조합 확인 / 3-2. 조합된 문제정의 (PRD F05) — ★개인화 포인트 1
 *
 * 검증된 기존 문제끼리만 조합한다(임의 텍스트 입력 불가).
 * PRD: 이 경로는 분기가 없다 — 개인화로만 이어진다.
 * 생성 중에는 에이전틱 진행 상태 UI를 노출한다.
 */

import { ArrowRight, ChevronLeft, X } from 'lucide-react';
import { useState } from 'react';
import { AgentProgress } from '@/components/AgentProgress';
import { AppShell, Page } from '@/components/AppShell';
import { SaveButton } from '@/components/SaveButton';
import {
  Body,
  Button,
  Caption,
  Card,
  EmptyState,
  EvidencePanel,
  PageTitle,
  buttonClass,
} from '@/components/ui';
import { getProblem } from '@/data/problems';
import { combineProblems } from '@/lib/personalize';
import { NavLink, useNav } from '@/lib/nav';
import { getCombined, useStore } from '@/lib/store';

/* ── 3-1. 조합 확인 ────────────────────────────────────────────── */

export function CombineConfirmScreen() {
  const { selectedProblemIds, toggleProblemSelect, addCombined } = useStore();
  const { go } = useNav();
  const [generating, setGenerating] = useState(false);

  const picked = selectedProblemIds.map(getProblem).filter(Boolean);

  if (picked.length < 2) {
    return (
      <AppShell>
        <Page>
          <EmptyState
            title="조합하려면 문제를 2개 이상 골라야 합니다"
            description="문제 탐색에서 카드의 '조합에 담기'를 눌러 2~3개를 선택해 주세요."
            action={
              <NavLink to="/problems" className={buttonClass('primary')}>
                문제 탐색으로
              </NavLink>
            }
          />
        </Page>
      </AppShell>
    );
  }

  const start = () => setGenerating(true);

  const finish = () => {
    const combined = combineProblems(selectedProblemIds);
    if (!combined) return;
    addCombined(combined);
    go(`/combined/${combined.id}`);
  };

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
          <div className="prose-width flex flex-col gap-4">
            <PageTitle>이 문제들을 묶습니다</PageTitle>
            <Body>
              선택한 문제의 근거를 겹쳐 하나의 새로운 문제정의를 만듭니다. 개별 문제보다 범위가
              넓어지고, 이어지는 아이디어도 달라집니다.
            </Body>
          </div>
        </div>

        {generating ? (
          <AgentProgress label="문제정의를 만들고 있습니다" onDone={finish} />
        ) : (
          <>
            <ul className="flex flex-col gap-4 max-w-[760px]">
              {picked.map((p) => (
                <li key={p!.id}>
                  <Card className="flex items-start gap-4">
                    <div className="flex-1 min-w-0 flex flex-col gap-1.5">
                      <Caption>{p!.category}</Caption>
                      <p className="text-[18px] font-semibold kr">{p!.title}</p>
                      <Body>{p!.oneLiner}</Body>
                      <Caption className="mt-1">
                        관련 사례 {p!.caseCount}건 · 출처 {p!.sources.length}곳
                      </Caption>
                    </div>
                    <button
                      type="button"
                      onClick={() => toggleProblemSelect(p!.id)}
                      aria-label={`${p!.title} 조합에서 빼기`}
                      className="shrink-0 w-9 h-9 inline-flex items-center justify-center rounded-lg text-text-muted hover:bg-bg-subtle hover:text-text-primary"
                    >
                      <X size={17} aria-hidden />
                    </button>
                  </Card>
                </li>
              ))}
            </ul>

            <div className="flex flex-wrap items-center gap-3">
              <Button onClick={start}>
                조합된 문제정의 만들기
                <ArrowRight size={18} aria-hidden />
              </Button>
              <Caption>선택한 {picked.length}개를 하나로 묶습니다.</Caption>
            </div>
          </>
        )}
      </Page>
    </AppShell>
  );
}

/* ── 3-2. 조합된 문제정의 ──────────────────────────────────────── */

export function CombinedDetailScreen({ combinedId }: { combinedId: string }) {
  // 조합 결과는 사용자별 생성물이라 localStorage에 보관된다.
  const { combined: all } = useStore();
  const combined = all.find((c) => c.id === combinedId) ?? getCombined(combinedId);

  if (!combined) {
    return (
      <AppShell>
        <Page>
          <EmptyState
            title="조합된 문제정의를 찾을 수 없습니다"
            description="이 결과는 브라우저에 보관됩니다. 저장 기록이 지워졌거나 다른 기기에서 만든 것일 수 있습니다."
            action={
              <NavLink to="/problems" className={buttonClass('primary')}>
                문제 탐색으로
              </NavLink>
            }
          />
        </Page>
      </AppShell>
    );
  }

  const origins = combined.sourceProblemIds.map(getProblem).filter(Boolean);

  return (
    <AppShell>
      <Page>
        <div className="prose-width flex flex-col gap-5">
          <span className="inline-flex w-fit items-center h-7 px-2.5 rounded-lg bg-blue-light text-blue text-[13px] font-semibold">
            조합된 문제정의
          </span>
          <PageTitle>{combined.title}</PageTitle>
          <Body className="text-[17px]">{combined.description}</Body>
          <Caption>
            원본 {origins.length}개 문제의 관련 사례를 합치면 {combined.totalCaseCount}건입니다.
          </Caption>
        </div>

        {/* 분기 없음 — 개인화로만 이어진다 (PRD F05) */}
        <div className="flex flex-wrap gap-3">
          <NavLink to={`/personalize/from/${combined.id}`} className={buttonClass('primary')}>
            이 문제정의로 개인화하기
            <ArrowRight size={18} aria-hidden />
          </NavLink>
          <SaveButton
            kind="problem"
            refId={combined.id}
            title={combined.title}
            subtitle="조합된 문제정의"
            path={`/combined/${combined.id}`}
          />
        </div>

        <EvidencePanel title="어떤 근거가 겹쳤나">
          <ul className="flex flex-col gap-4">
            {combined.sharedEvidence.map((line, i) => (
              <li key={i} className="text-[16px] leading-[1.6] kr border-l-2 border-blue pl-3">
                {line}
              </li>
            ))}
          </ul>
        </EvidencePanel>

        <section className="flex flex-col gap-5">
          <p className="text-[20px] font-semibold">원본 문제</p>
          <ul className="grid gap-5 md:grid-cols-2">
            {origins.map((p) => (
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
      </Page>
    </AppShell>
  );
}
