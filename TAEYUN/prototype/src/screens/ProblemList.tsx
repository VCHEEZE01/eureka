'use client';

/**
 * 3. 문제 탐색 (PRD F03)
 * 검색 / 카테고리 / 정렬로 좁히고, 카드를 눌러 상세로 간다.
 * 2개 이상 선택하면 F05 문제정의 조합으로 넘어갈 수 있다.
 */

import { Combine, Search, X } from 'lucide-react';
import { useMemo, useState } from 'react';
import { AppShell, Page } from '@/components/AppShell';
import {
  Badge,
  Body,
  Button,
  Caption,
  Card,
  CardTitle,
  Caption as Cap,
  EmptyState,
  PageTitle,
} from '@/components/ui';
import { problems } from '@/data/problems';
import { NavLink, useNav } from '@/lib/nav';
import { useStore } from '@/lib/store';
import {
  CATEGORIES,
  COMBINE_MAX,
  SORT_LABEL,
  SORT_OPTIONS,
  sourceCount,
  type Category,
  type SortOption,
} from '@/lib/types';

export function ProblemListScreen() {
  const { scope, selectedProblemIds, toggleProblemSelect, clearProblemSelect } = useStore();
  const { go } = useNav();

  const [query, setQuery] = useState('');
  const [category, setCategory] = useState<Category | null>(null);
  const [sort, setSort] = useState<SortOption>('cases');

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const list = problems.filter((p) => {
      if (category && p.category !== category) return false;
      if (!q) return true;
      return (
        p.title.toLowerCase().includes(q) ||
        p.oneLiner.toLowerCase().includes(q) ||
        p.description.toLowerCase().includes(q)
      );
    });
    return [...list].sort((a, b) =>
      sort === 'cases' ? b.caseCount - a.caseCount : b.updatedAt.localeCompare(a.updatedAt),
    );
  }, [query, category, sort]);

  const selectedCount = selectedProblemIds.length;
  const canCombine = selectedCount >= 2;

  return (
    <AppShell>
      <Page>
        <div className="flex flex-col gap-4 prose-width">
          <PageTitle>문제 탐색</PageTitle>
          <Body>
            실제 불편에서 뽑아낸 문제입니다. 마음이 가는 문제를 눌러 근거를 확인하거나, 두 개 이상
            골라 하나의 문제정의로 묶어보세요.
          </Body>
          {scope ? (
            <Cap>
              현재 리서치 범위: {scope.join(' · ')}{' '}
              <NavLink to="/onboarding" className="text-blue font-semibold">
                변경
              </NavLink>
            </Cap>
          ) : null}
        </div>

        {/* 필터 */}
        <div className="flex flex-col gap-4">
          <div className="relative max-w-[520px]">
            <Search
              size={18}
              className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none"
              aria-hidden
            />
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="어떤 불편을 찾고 있나요?"
              aria-label="문제 검색"
              className="w-full h-12 pl-11 pr-4 rounded-[12px] border border-control-border bg-bg text-[15px] outline-none focus:border-blue"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <FilterChip active={category === null} onClick={() => setCategory(null)}>
              전체
            </FilterChip>
            {CATEGORIES.map((c) => (
              <FilterChip key={c} active={category === c} onClick={() => setCategory(c)}>
                {c}
              </FilterChip>
            ))}

            <span className="ml-auto flex items-center gap-1">
              {SORT_OPTIONS.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setSort(s)}
                  className={`h-9 px-3 rounded-lg text-[14px] font-medium ${
                    sort === s ? 'text-blue bg-blue-light' : 'text-text-secondary hover:bg-bg-subtle'
                  }`}
                >
                  {SORT_LABEL[s]}
                </button>
              ))}
            </span>
          </div>
        </div>

        {/* 목록 */}
        {filtered.length === 0 ? (
          <EmptyState
            title="조건에 맞는 문제가 없습니다"
            description="검색어를 지우거나 카테고리를 전체로 바꿔보세요."
            action={
              <Button
                variant="secondary"
                onClick={() => {
                  setQuery('');
                  setCategory(null);
                }}
              >
                전체 보기
              </Button>
            }
          />
        ) : (
          <ul className="grid gap-5 md:grid-cols-2">
            {filtered.map((p) => {
              const checked = selectedProblemIds.includes(p.id);
              const blocked = !checked && selectedCount >= COMBINE_MAX;
              return (
                <li key={p.id}>
                  <Card interactive className="h-full flex flex-col gap-4">
                    <div className="flex items-start justify-between gap-3">
                      <Badge tone="blue">{p.category}</Badge>
                      <label
                        className={`flex items-center gap-2 text-[13px] shrink-0 ${
                          blocked ? 'text-text-muted cursor-not-allowed' : 'text-text-secondary cursor-pointer'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={checked}
                          disabled={blocked}
                          onChange={() => toggleProblemSelect(p.id)}
                          className="w-4 h-4 accent-blue"
                        />
                        조합에 담기
                      </label>
                    </div>

                    <NavLink to={`/problems/${p.id}`} className="flex flex-col gap-2 flex-1">
                      <CardTitle>{p.title}</CardTitle>
                      <Body>{p.oneLiner}</Body>
                    </NavLink>

                    {/* 대표 근거 1건 — PRD F03의 카드 필수 항목 */}
                    <p className="text-[14px] text-text-secondary kr border-l-2 border-blue pl-3">
                      {p.evidence[0].summary}
                    </p>

                    <div className="flex items-center gap-4 pt-1">
                      <Cap>
                        관련 사례 <b className="text-text-primary">{p.caseCount}</b>건
                      </Cap>
                      <Cap>
                        출처 <b className="text-text-primary">{sourceCount(p)}</b>곳
                      </Cap>
                    </div>
                  </Card>
                </li>
              );
            })}
          </ul>
        )}
      </Page>

      {/* 선택 바 — 2개 이상일 때만 조합으로 넘어갈 수 있다 */}
      {selectedCount > 0 ? (
        <div className="sticky bottom-0 border-t border-border bg-bg/95 backdrop-blur">
          <div className="shell py-4 flex flex-wrap items-center gap-3">
            <span className="text-[15px] font-semibold">
              {selectedCount}개 선택됨
              <span className="text-text-muted font-normal"> · 최대 {COMBINE_MAX}개</span>
            </span>
            <button
              type="button"
              onClick={clearProblemSelect}
              className="inline-flex items-center gap-1 text-[14px] text-text-secondary hover:text-text-primary"
            >
              <X size={15} aria-hidden />
              선택 해제
            </button>
            <span className="ml-auto flex items-center gap-3">
              {!canCombine ? (
                <Cap>조합하려면 1개 더 선택하세요</Cap>
              ) : null}
              <Button disabled={!canCombine} onClick={() => go('/problems/combine')}>
                <Combine size={18} aria-hidden />
                문제정의 조합하기
              </Button>
            </span>
          </div>
        </div>
      ) : null}
    </AppShell>
  );
}

function FilterChip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`h-10 px-4 rounded-[10px] text-[15px] font-medium border transition-colors ${
        active
          ? 'bg-blue-light border-blue text-blue'
          : 'bg-bg border-control-border text-control-text hover:bg-bg-subtle'
      }`}
    >
      {children}
    </button>
  );
}
