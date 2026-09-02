'use client';

import Link from 'next/link';
import { LOGIN_GATE, RunRow, SavedRow } from '@/components/mypage/items';
import { ButtonLink, EmptyState, SectionTitle } from '@/components/ui';
import { useStore } from '@/lib/store';

/**
 * F07 즐겨찾기 / 보관함. 마이페이지 하위 화면이다.
 * 저장한 문제 / 저장한 아이디어(기본·개인화) + 최근 개인화 실행 기록을 보여준다.
 * 저장·보관함 열람 자체가 로그인 필요 기능이므로 비로그인이면 로그인으로 유도한다.
 */
export default function LibraryPage() {
  const { user, saved, runs, toggleSave, hydrated } = useStore();

  if (!hydrated) {
    return <div className="min-h-[40vh]" />;
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
      <div>
        <nav className="mb-3 text-sm text-muted">
          <Link href="/mypage" className="hover:text-foreground">
            마이페이지
          </Link>
          <span className="mx-2" aria-hidden>
            ›
          </span>
          <span className="text-foreground">보관함</span>
        </nav>
        <SectionTitle
          title="보관함"
          description="저장한 문제와 아이디어를 모아봅니다."
        />
      </div>

      {saved.length === 0 && runs.length === 0 ? (
        <EmptyState
          title="아직 저장한 항목이 없습니다"
          description="문제 상세나 아이디어 카드의 저장 버튼(☆)을 누르면 여기서 다시 확인할 수 있습니다."
          action={<ButtonLink href="/problems">문제 둘러보기</ButtonLink>}
        />
      ) : (
        <>
          <section className="space-y-4">
            <SectionTitle title="저장한 문제" />
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
            <SectionTitle title="저장한 아이디어" />
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
