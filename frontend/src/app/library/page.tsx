'use client';

import Link from 'next/link';
import { Badge, ButtonLink, Card, EmptyState, SectionTitle } from '@/components/ui';
import { useStore } from '@/lib/store';
import type { PersonalizationRun, SavedItem } from '@/lib/types';

/**
 * F07 즐겨찾기 / 보관함.
 * 저장한 문제 / 저장한 아이디어(기본·개인화) + 최근 개인화 실행 기록을 보여준다.
 * 저장·보관함 열람 자체가 로그인 필요 기능이므로 비로그인이면 로그인으로 유도한다.
 */

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    });
  } catch {
    return iso;
  }
}

function SavedRow({ item, onUnsave }: { item: SavedItem; onUnsave: () => void }) {
  return (
    <Card className="flex flex-wrap items-start justify-between gap-3">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone={item.kind === 'personalized' ? 'ai' : 'brand'}>
            {item.kind === 'problem'
              ? '문제'
              : item.kind === 'personalized'
                ? '개인화 아이디어'
                : '기본 아이디어'}
          </Badge>
          <span className="text-xs text-muted">{formatDate(item.savedAt)} 저장</span>
        </div>
        <Link href={item.href} className="mt-2 block font-semibold hover:underline">
          {item.title}
        </Link>
        <p className="kr-text mt-1 text-sm text-muted">{item.subtitle}</p>
      </div>
      <button
        onClick={onUnsave}
        className="shrink-0 rounded-full border border-border px-3 py-1.5 text-xs font-medium text-muted transition-colors hover:text-foreground"
      >
        저장 해제
      </button>
    </Card>
  );
}

function summarizeRun(run: PersonalizationRun): string {
  const { serviceForm, target, resource, extra } = run.input;
  const base = [serviceForm, target, resource].join(' · ');
  return extra ? `${base} · ${extra}` : base;
}

function RunRow({ run }: { run: PersonalizationRun }) {
  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-xs text-muted">{formatDate(run.createdAt)} 실행</span>
        <span className="text-xs text-muted">아이디어 {run.ideas.length}개</span>
      </div>
      <p className="kr-text mt-2 text-sm font-medium">{summarizeRun(run)}</p>
      <Link
        href={`/personalize/${run.id}`}
        className="mt-3 inline-block text-sm font-semibold text-brand hover:underline"
      >
        결과 다시 보기 →
      </Link>
    </Card>
  );
}

export default function LibraryPage() {
  const { user, saved, runs, toggleSave, hydrated } = useStore();

  if (!hydrated) {
    return <div className="min-h-[40vh]" />;
  }

  if (!user) {
    return (
      <EmptyState
        title="보관함은 로그인이 필요합니다"
        description="저장한 문제와 아이디어, 개인화 실행 기록은 계정 단위로 보관됩니다. 로그인 후 다시 확인해주세요."
        action={<ButtonLink href="/login?next=/library">로그인하기</ButtonLink>}
      />
    );
  }

  const savedProblems = saved.filter((item) => item.kind === 'problem');
  const savedIdeas = saved.filter(
    (item) => item.kind === 'idea' || item.kind === 'personalized',
  );
  const isEmpty = saved.length === 0 && runs.length === 0;

  if (isEmpty) {
    return (
      <div className="space-y-8">
        <SectionTitle title="보관함" description="저장한 문제와 아이디어를 모아봅니다." />
        <EmptyState
          title="아직 저장한 항목이 없습니다"
          description="문제 상세나 아이디어 카드의 저장 버튼(☆)을 누르면 여기서 다시 확인할 수 있습니다."
          action={<ButtonLink href="/problems">문제 둘러보기</ButtonLink>}
        />
      </div>
    );
  }

  return (
    <div className="space-y-12">
      <SectionTitle title="보관함" description="저장한 문제와 아이디어를 모아봅니다." />

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
          <p className="kr-text text-sm text-muted">아직 초개인화를 실행하지 않았습니다.</p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {runs.map((run) => (
              <RunRow key={run.id} run={run} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
