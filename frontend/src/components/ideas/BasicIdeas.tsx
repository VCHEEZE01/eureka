'use client';

import Link from 'next/link';
import { useState } from 'react';
import { ArrowRightIcon, SparkIcon } from '@/components/icons';
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
    <div className="space-y-8">
      {totalRounds > 1 && (
        <p className="text-xs text-muted tabular-nums">
          묶음 {(round % totalRounds) + 1} / {totalRounds}
        </p>
      )}

      <ul className="grid gap-4 sm:grid-cols-2">
        {ideas.map((idea) => (
          <li key={idea.id}>
            <IdeaCard idea={idea} href={`/ideas/${idea.id}`} />
          </li>
        ))}
      </ul>

      {/*
        변형별 행동 유도. hydration 전에는 어느 쪽도 그리지 않아 깜빡임을 막는다.
        대신 같은 높이를 미리 잡아 두어 나중에 콘텐츠가 밀려 내려가지 않게 한다.
      */}
      <div className="min-h-[7.5rem]">
        {hydrated && (
          <>
            {variantSpec.showPersonalizeCta && (
              <CtaPanel
                title="이 중에 만들고 싶은 게 없다면"
                body="만들려는 형태와 보유 리소스에 맞춰 아이디어를 다시 좁혀 받아볼 수 있습니다."
                action={
                  <ButtonLink href={`/personalize?problem=${problem.id}`}>
                    내 상황에 맞게 구체화
                    <ArrowRightIcon />
                  </ButtonLink>
                }
              />
            )}

            {variantSpec.showRefresh && (
              <CtaPanel
                title={wrapped ? '준비된 아이디어를 모두 보여드렸습니다' : '다른 방향도 있습니다'}
                body={
                  wrapped
                    ? '계속 누르면 처음 묶음부터 다시 보여집니다.'
                    : '마음에 드는 방향이 없다면 같은 문제에서 다른 해결 방향을 더 볼 수 있습니다.'
                }
                action={
                  <Button variant="secondary" onClick={() => setRound((r) => r + 1)}>
                    다른 아이디어 보기
                  </Button>
                }
              />
            )}

            {!variantSpec.showPersonalizeCta && !variantSpec.showRefresh && (
              <p className="kr-text rounded-2xl border border-dashed border-border px-5 py-6 text-sm text-muted">
                이 문제에서 발견된 기본 아이디어입니다. 마음에 드는 아이디어는 저장해 두고
                보관함에서 다시 확인할 수 있습니다.
              </p>
            )}
          </>
        )}
      </div>

      <footer className="space-y-2 border-t border-border pt-6 text-xs text-muted">
        <p className="kr-text flex items-start gap-1.5">
          <SparkIcon className="mt-0.5 size-3.5 shrink-0 text-ai" />
          <span>
            아이디어는 AI가 만든 추천 후보이며 시장성이나 성공 가능성이 검증된 결과가
            아닙니다.{' '}
            <Link
              href={`/problems/${problem.id}`}
              className="focus-ring rounded font-medium text-foreground underline underline-offset-2"
            >
              이 아이디어들이 근거로 삼은 문제 보기
            </Link>
          </span>
        </p>
        {hydrated && (
          <p className="kr-text">
            현재 <strong className="font-semibold text-foreground">버전 {variant}</strong> ·{' '}
            {variantSpec.label} — {variantSpec.description} 상단 &ldquo;아이디어 화면&rdquo;에서
            다른 버전으로 전환할 수 있습니다.
          </p>
        )}
      </footer>
    </div>
  );
}

function CtaPanel({
  title,
  body,
  action,
}: {
  title: string;
  body: string;
  action: React.ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-brand/25 bg-brand-soft/45 px-5 py-5">
      <div className="min-w-0 max-w-md">
        <p className="kr-text font-bold">{title}</p>
        <p className="kr-text mt-1 text-sm text-muted">{body}</p>
      </div>
      {action}
    </div>
  );
}
