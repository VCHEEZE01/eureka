'use client';

import Link from 'next/link';
import { ArrowRightIcon, UserIcon } from '@/components/icons';
import {
  LOGIN_GATE,
  RunRow,
  SavedRow,
  formatDate,
} from '@/components/mypage/items';
import {
  Button,
  ButtonLink,
  Card,
  CardListSkeleton,
  EmptyState,
  PageHeader,
  SectionTitle,
  Skeleton,
} from '@/components/ui';
import { useStore } from '@/lib/store';

/**
 * 마이페이지. 계정 정보와 저장 현황을 모아 보여주고,
 * 전체 목록(F07 보관함)은 /mypage/library로 연결한다.
 */

const PREVIEW_COUNT = 3;

export default function MyPage() {
  const { user, saved, runs, logout, hydrated } = useStore();

  // localStorage를 읽기 전에는 로그인 여부를 알 수 없다.
  // 이전에는 빈 div를 그려 화면이 한 번 깜빡였다.
  if (!hydrated) {
    return (
      <div className="space-y-8">
        <Skeleton className="h-9 w-40" />
        <Skeleton className="h-24" />
        <CardListSkeleton count={2} />
      </div>
    );
  }

  if (!user) {
    return (
      <EmptyState
        title={LOGIN_GATE.title}
        description={LOGIN_GATE.description}
        action={<ButtonLink href="/login?next=/mypage">로그인하기</ButtonLink>}
      />
    );
  }

  const savedProblems = saved.filter((item) => item.kind === 'problem');
  const savedIdeas = saved.filter(
    (item) => item.kind === 'idea' || item.kind === 'personalized',
  );
  const recent = saved.slice(0, PREVIEW_COUNT);

  return (
    <div className="space-y-14">
      <section className="space-y-5">
        <PageHeader title="마이페이지" />
        <Card className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex min-w-0 items-center gap-3.5">
            <span
              aria-hidden
              className="flex size-11 shrink-0 items-center justify-center rounded-full bg-brand-soft text-brand-strong"
            >
              <UserIcon className="size-5" />
            </span>
            <div className="min-w-0">
              <p className="truncate text-lg font-bold">{user.nickname}</p>
              <p className="mt-0.5 truncate text-sm text-muted">{user.email}</p>
            </div>
          </div>
          <Button variant="secondary" size="sm" onClick={logout}>
            로그아웃
          </Button>
        </Card>
      </section>

      <section>
        <SectionTitle
          title="보관함"
          description="저장한 문제와 아이디어를 모아봅니다."
          aside={
            <ButtonLink href="/mypage/library" variant="secondary" size="sm">
              보관함 열기
              <ArrowRightIcon className="size-3.5" />
            </ButtonLink>
          }
        />
        <div className="grid grid-cols-3 gap-px overflow-hidden rounded-2xl border border-border bg-border">
          <CountCard label="저장한 문제" count={savedProblems.length} />
          <CountCard label="저장한 아이디어" count={savedIdeas.length} />
          <CountCard label="개인화 실행" count={runs.length} />
        </div>
      </section>

      <section className="space-y-4">
        <SectionTitle title="최근 저장한 항목" />
        {recent.length === 0 ? (
          <EmptyState
            title="아직 저장한 항목이 없습니다"
            description="문제 상세나 아이디어 카드의 저장 버튼을 누르면 여기에 쌓입니다."
            action={<ButtonLink href="/problems">문제 둘러보기</ButtonLink>}
          />
        ) : (
          <>
            <div className="space-y-3">
              {recent.map((item) => (
                <SavedRow key={item.key} item={item} />
              ))}
            </div>
            {saved.length > recent.length && (
              <Link
                href="/mypage/library"
                className="focus-ring inline-flex items-center gap-1 rounded text-sm font-semibold text-brand hover:underline"
              >
                저장한 항목 {saved.length}개 전체 보기
                <ArrowRightIcon className="size-3.5" />
              </Link>
            )}
          </>
        )}
      </section>

      {runs.length > 0 && (
        <section className="space-y-4">
          <SectionTitle
            title="최근 개인화 실행"
            description={`마지막 실행 ${formatDate(runs[0].createdAt)}`}
          />
          <div className="grid gap-4 sm:grid-cols-2">
            {runs.slice(0, 2).map((run) => (
              <RunRow key={run.id} run={run} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function CountCard({ label, count }: { label: string; count: number }) {
  return (
    <div className="bg-surface px-4 py-4">
      <p className="kr-text text-xs text-muted sm:text-sm">{label}</p>
      <p className="display mt-1 text-3xl tabular-nums">{count}</p>
    </div>
  );
}
