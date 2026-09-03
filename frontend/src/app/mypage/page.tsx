'use client';

import Link from 'next/link';
import {
  LOGIN_GATE,
  RunRow,
  SavedRow,
  formatDate,
} from '@/components/mypage/items';
import { Button, ButtonLink, Card, EmptyState, SectionTitle } from '@/components/ui';
import { useStore } from '@/lib/store';

/**
 * 마이페이지. 계정 정보와 저장 현황을 모아 보여주고,
 * 전체 목록(F07 보관함)은 /mypage/library로 연결한다.
 */

const PREVIEW_COUNT = 3;

export default function MyPage() {
  const { user, saved, runs, logout, hydrated } = useStore();

  if (!hydrated) {
    return <div className="min-h-[40vh]" />;
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
    <div className="space-y-12">
      <section>
        <SectionTitle title="마이페이지" />
        <Card className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-lg font-bold">{user.nickname}</p>
            <p className="mt-0.5 text-sm text-muted">{user.email}</p>
          </div>
          <Button variant="secondary" onClick={logout}>
            로그아웃
          </Button>
        </Card>
      </section>

      <section>
        <SectionTitle
          title="보관함"
          description="저장한 문제와 아이디어를 모아봅니다."
          aside={
            <ButtonLink href="/mypage/library" variant="secondary">
              보관함 열기
            </ButtonLink>
          }
        />
        <div className="grid gap-4 sm:grid-cols-3">
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
            description="문제 상세나 아이디어 카드의 저장 버튼(☆)을 누르면 여기에 쌓입니다."
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
                className="inline-block text-sm font-semibold text-brand hover:underline"
              >
                저장한 항목 {saved.length}개 전체 보기 →
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
    <Card>
      <p className="text-sm text-muted">{label}</p>
      <p className="mt-1 text-3xl font-extrabold tabular-nums">{count}</p>
    </Card>
  );
}
