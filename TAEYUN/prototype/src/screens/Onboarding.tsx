'use client';

/**
 * 2. 리서치 범위 선택 (PRD F02) — ★개인화 포인트 2
 * 문제를 어떤 소스에서 찾아올지 사용자가 정한다.
 * 아무것도 고르지 않고 진행하면 기본값(전체 범위)이 적용된다.
 * 언제든 건너뛸 수 있다.
 *
 * PRD F00: 처음 요청하는 소스 조합은 캐시 미스라 그 자리에서 수집해야 한다.
 * 그래서 여기서도 대기가 생기고, 에이전틱 진행 상태 UI를 노출한다.
 * 단계 이름은 아이디어 합성(F05·F07)이 아니라 수집 파이프라인을 따른다.
 */

import { ArrowRight } from 'lucide-react';
import { useState } from 'react';
import { AgentProgress, RESEARCH_STEPS } from '@/components/AgentProgress';
import { AppShell, Page } from '@/components/AppShell';
import { Body, Button, Caption, PageTitle } from '@/components/ui';
import { useNav } from '@/lib/nav';
import { useStore } from '@/lib/store';
import { SOURCE_KINDS, type SourceKind } from '@/lib/types';

const HINTS: Record<SourceKind, string> = {
  커뮤니티: '"이거 불편한데 방법 없나요" 형태의 원문이 가장 많이 쌓이는 곳',
  블로그: '경험을 길게 정리한 글. 맥락을 파악하기 좋음',
  리뷰: '앱·서비스 사용 중 겪은 구체적 불만',
  뉴스: '사회적으로 다뤄지기 시작한 문제',
  소셜: '짧고 즉각적인 반응. 최신 흐름 파악에 유리',
};

export function OnboardingScreen() {
  const { scope, setScope } = useStore();
  const { go } = useNav();
  const [picked, setPicked] = useState<SourceKind[]>(scope ?? []);
  /** 수집 중에 어떤 범위를 채우는지 보여주기 위해 확정된 범위를 담아둔다. */
  const [collecting, setCollecting] = useState<SourceKind[] | null>(null);

  const toggle = (kind: SourceKind) =>
    setPicked((prev) => (prev.includes(kind) ? prev.filter((k) => k !== kind) : [...prev, kind]));

  // 아무것도 선택하지 않으면 전체 범위를 기본값으로 적용한다.
  const start = (range: SourceKind[]) => setCollecting(range.length > 0 ? range : [...SOURCE_KINDS]);

  const finish = () => {
    if (collecting) setScope(collecting);
    go('/problems');
  };

  // 수집 중에는 선택 UI 대신 진행 상태만 보여준다.
  if (collecting) {
    return (
      <AppShell>
        <Page>
          <div className="prose-width flex flex-col gap-4">
            <Caption>{collecting.join(' · ')}</Caption>
            <PageTitle>범위에 맞는 문제를 모으고 있습니다</PageTitle>
          </div>
          <AgentProgress
            label={`${collecting.length}개 범위에서 수집 중`}
            steps={RESEARCH_STEPS}
            onDone={finish}
          />
        </Page>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <Page>
        <div className="prose-width flex flex-col gap-4">
          <Caption>1 / 1 단계</Caption>
          <PageTitle>어디에서 문제를 찾아올까요?</PageTitle>
          <Body>
            고른 소스에서 모은 불편을 우선해 보여줍니다. 지금 정하지 않아도 되고, 나중에 바꿀 수
            있습니다.
          </Body>
        </div>

        <div className="flex flex-col gap-3 max-w-[720px]">
          {SOURCE_KINDS.map((kind) => {
            const selected = picked.includes(kind);
            return (
              <button
                key={kind}
                type="button"
                onClick={() => toggle(kind)}
                aria-pressed={selected}
                className={`flex items-center gap-4 text-left p-5 rounded-[16px] border transition-colors ${
                  selected
                    ? 'border-blue bg-blue-soft'
                    : 'border-border bg-bg hover:bg-bg-subtle'
                }`}
              >
                <span
                  className={`inline-flex items-center justify-center w-5 h-5 rounded-md border-2 shrink-0 ${
                    selected ? 'border-blue bg-blue' : 'border-control-border'
                  }`}
                  aria-hidden
                >
                  {selected ? (
                    <svg width="11" height="11" viewBox="0 0 12 12" fill="none">
                      <path
                        d="M2.5 6.2L4.8 8.5L9.5 3.8"
                        stroke="white"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  ) : null}
                </span>
                <span className="flex-1 min-w-0">
                  <span className="block text-[17px] font-semibold mb-1">{kind}</span>
                  <span className="block text-[14px] text-text-secondary kr">{HINTS[kind]}</span>
                </span>
              </button>
            );
          })}
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Button onClick={() => start(picked)}>
            {picked.length > 0 ? `${picked.length}개 범위로 시작하기` : '전체 범위로 시작하기'}
            <ArrowRight size={18} aria-hidden />
          </Button>
          <Button variant="ghost" onClick={() => start([])}>
            건너뛰기
          </Button>
        </div>
      </Page>
    </AppShell>
  );
}
