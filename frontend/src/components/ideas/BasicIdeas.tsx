'use client';

import Link from 'next/link';
import { useState } from 'react';
import { IdeaCard } from '@/components/IdeaCard';
import { Button, ButtonLink, EmptyState } from '@/components/ui';
import { getIdeaBatch, ideaRoundCount } from '@/lib/data';
import { useStore } from '@/lib/store';
import type { Problem } from '@/lib/types';

/**
 * 기본 아이디어 목록 (F04) — A/B/C 변형의 실제 분기 지점.
 *
 * 세 버전은 아이디어 카드 자체는 동일하게 보여주고 하단 행동 유도만 달라진다.
 * KPI "개인화 이용률"을 비교하는 것이 목적이므로 카드 내용을 바꾸면 안 된다.
 *
 * - A: "내 상황에 맞게 구체화" 만 노출
 * - B: "다른 아이디어 보기" 만 노출
 * - C: 둘 다 없음 (대조군)
 */
export function BasicIdeas({ problem }: { problem: Problem }) {
  const { variant, variantSpec, hydrated } = useStore();
  const [round, setRound] = useState(0);

  const ideas = getIdeaBatch(problem.id, round);
  const totalRounds = ideaRoundCount(problem.id);
  // 풀을 한 바퀴 다 돌면 처음 묶음으로 되돌아온다.
  const wrapped = totalRounds > 0 && round >= totalRounds;

  if (ideas.length === 0) {
    return (
      <EmptyState
        title="아직 이 문제의 아이디어가 준비되지 않았습니다"
        description="문제는 수집됐지만 아이디어 생성이 끝나지 않았습니다. 다른 문제를 먼저 둘러봐 주세요."
        action={<ButtonLink href="/problems">문제 탐색으로</ButtonLink>}
      />
    );
  }

  return (
    <div className="space-y-6">
      <ul className="grid gap-4 sm:grid-cols-2">
        {ideas.map((idea) => (
          <li key={idea.id}>
            <IdeaCard idea={idea} href={`/ideas/${idea.id}`} />
          </li>
        ))}
      </ul>

      {/* 변형별 행동 유도. hydration 전에는 어느 쪽도 그리지 않아 깜빡임을 막는다. */}
      {hydrated && (
        <div className="border-t border-border pt-6">
          {variantSpec.showPersonalizeCta && (
            <div className="flex flex-wrap items-center justify-between gap-4">
              <p className="kr-text max-w-md text-sm text-muted">
                만들고 싶은 아이디어가 없다면, 만들려는 형태와 리소스에 맞게
                좁혀서 다시 받아볼 수 있습니다.
              </p>
              <ButtonLink href={`/personalize?problem=${problem.id}`}>
                내 상황에 맞게 구체화
              </ButtonLink>
            </div>
          )}

          {variantSpec.showRefresh && (
            <div className="flex flex-wrap items-center justify-between gap-4">
              <p className="kr-text max-w-md text-sm text-muted">
                {wrapped
                  ? '준비된 아이디어를 모두 보여드렸습니다. 계속 누르면 처음 묶음부터 다시 보여집니다.'
                  : '마음에 드는 방향이 없다면 같은 문제에서 다른 해결 방향을 더 볼 수 있습니다.'}
              </p>
              <Button onClick={() => setRound((r) => r + 1)}>
                다른 아이디어 보기
              </Button>
            </div>
          )}

          {!variantSpec.showPersonalizeCta && !variantSpec.showRefresh && (
            <p className="kr-text text-sm text-muted">
              이 문제에서 발견된 기본 아이디어입니다. 마음에 드는 아이디어는
              저장해 두고 보관함에서 다시 확인할 수 있습니다.
            </p>
          )}
        </div>
      )}

      <p className="text-xs text-muted">
        현재 <strong className="font-semibold text-foreground">버전 {variant}</strong>
        {' · '}
        {variantSpec.label} — {variantSpec.description} 상단에서 다른 버전으로
        전환할 수 있습니다.
      </p>

      <p className="kr-text text-xs text-muted">
        아이디어는 AI가 만든 추천 후보이며 시장성이나 성공 가능성이 검증된
        결과가 아닙니다.{' '}
        <Link href={`/problems/${problem.id}`} className="underline">
          이 아이디어들이 근거로 삼은 문제 보기
        </Link>
      </p>
    </div>
  );
}
