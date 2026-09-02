'use client';

import { LOGIN_GATE, RunRow, SavedRow } from '@/components/mypage/items';
import {
  Breadcrumbs,
  ButtonLink,
  CardListSkeleton,
  EmptyState,
  PageHeader,
  SectionTitle,
  Skeleton,
} from '@/components/ui';
import { useStore } from '@/lib/store';

/**
 * F07 즐겨찾기 / 보관함. 마이페이지 하위 화면이다.
 * 저장한 문제 / 저장한 아이디어(기본·개인화) + 최근 개인화 실행 기록을 보여준다.
 * 저장·보관함 열람 자체가 로그인 필요 기능이므로 비로그인이면 로그인으로 유도한다.
 */
export default function LibraryPage() {
  const { user, saved, runs, toggleSave, hydrated } = useStore();

  // 저장 목록은 localStorage에서 온다. 빈 화면 대신 자리 표시자를 그린다.
  if (!hydrated) {
    return (
      <div className="space-y-8">
        <Skeleton className="h-9 w-40" />
        <CardListSkeleton count={4} />
      </div>
    );
  }

  if (!user) {
    return (
      <EmptyState
        title={LOGIN_GATE.title}
        description={LOGIN_GATE.description}
        action={
          <ButtonLink href="/login?next=/mypage/library">로그인하기</ButtonLink>
        }
      />
    );
  }

  const savedProblems = saved.filter((item) => item.kind === 'problem');
  const savedIdeas = saved.filter(
    (item) => item.kind === 'idea' || item.kind === 'personalized',
  );

  return (
    <div className="space-y-12">
      <div className="space-y-5">
        <Breadcrumbs
          items={[{ label: '마이페이지', href: '/mypage' }, { label: '보관함' }]}
        />
        <PageHeader
          title="보관함"
          description="저장한 문제와 아이디어를 모아봅니다."
        />
      </div>

      {saved.length === 0 && runs.length === 0 ? (
        <EmptyState
          title="아직 저장한 항목이 없습니다"
          description="문제 상세나 아이디어 카드의 저장 버튼을 누르면 여기서 다시 확인할 수 있습니다."
          action={<ButtonLink href="/problems">문제 둘러보기</ButtonLink>}
        />
      ) : (
        <>
          <section className="space-y-4">
            <SectionTitle
              title="저장한 문제"
              aside={
                savedProblems.length > 0 ? (
                  <span className="text-sm text-muted tabular-nums">
                    {savedProblems.length}건
                  </span>
                ) : undefined
              }
            />
            {savedProblems.length === 0 ? (
              <p className="kr-text text-sm text-muted">저장한 문제가 없습니다.</p>
            ) : (
              <div className="space-y-3">
                {savedProblems.map((item) => (
                  <SavedRow
                    key={item.key}
                    item={item}
                    onUnsave={() => toggleSave(item)}
                  />
                ))}
              </div>
            )}
          </section>

          <section className="space-y-4">
            <SectionTitle
              title="저장한 아이디어"
              aside={
                savedIdeas.length > 0 ? (
                  <span className="text-sm text-muted tabular-nums">
                    {savedIdeas.length}건
                  </span>
                ) : undefined
              }
            />
            {savedIdeas.length === 0 ? (
              <p className="kr-text text-sm text-muted">저장한 아이디어가 없습니다.</p>
            ) : (
              <div className="space-y-3">
                {savedIdeas.map((item) => (
                  <SavedRow
                    key={item.key}
                    item={item}
                    onUnsave={() => toggleSave(item)}
                  />
                ))}
              </div>
            )}
          </section>

          <section className="space-y-4">
            <SectionTitle
              title="최근 개인화 실행 기록"
              description="이전 조건으로 만든 개인화 결과를 다시 열어볼 수 있습니다."
            />
            {runs.length === 0 ? (
              <p className="kr-text text-sm text-muted">
                아직 초개인화를 실행하지 않았습니다.
              </p>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2">
                {runs.map((run) => (
                  <RunRow key={run.id} run={run} />
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
