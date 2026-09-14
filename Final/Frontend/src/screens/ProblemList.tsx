'use client';

/**
 * 문제 탐색 (PRD F03)
 * 검색 / 카테고리 / 정렬로 좁히고, 카드를 눌러 상세로 간다.
 * 2개 이상 선택하면 F05 문제정의 조합으로 넘어갈 수 있다(현재 잠금 — 라우트는 notFound).
 *
 * ★ 온보딩이 타겟 설정으로 바뀌면서, 목록은 타겟과의 매칭 건수 내림차순으로
 *   "정렬"만 한다. 필터링은 하지 않는다 — 0건인 문제도 남고
 *   "타겟과 겹치는 근거 없음"으로 표시한다. 카테고리 필터 칩은 그대로 유지한다.
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
import type { Category, Problem } from '@/api/types';
import { DATA_MODE } from '@/api/client';
import { useProblems } from '@/hooks/useProblems';
import { matchTarget } from '@/lib/targetMatch';
import { NavLink, useNav } from '@/lib/nav';
import { useStore } from '@/lib/store';
import { COMBINE_MAX, SORT_LABEL, SORT_OPTIONS, sourceCount, type SortOption } from '@/lib/types';

const CATEGORIES: Category[] = ['금융', '헬스케어', '라이프스타일', 'IT/생산성', '교육/커리어'];

export function ProblemListScreen() {
  const { target, selectedProblemIds, toggleProblemSelect, clearProblemSelect } = useStore();
  const { go } = useNav();

  const { problems, loading, error } = useProblems();
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState<Category | null>(null);
  const [sort, setSort] = useState<SortOption>('cases');

  const targetLabel = useMemo(() => {
    if (!target) return null;
    const parts = [target.age, target.gender, ...target.jobs, ...target.places].filter(Boolean);
    return parts.length > 0 ? parts.join(' · ') : null;
  }, [target]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const list = problems.filter((p) => {
      if (category && p.category !== category) return false;
      if (!q) return true;
      return (
        p.title.toLowerCase().includes(q) ||
        p.one_liner.toLowerCase().includes(q) ||
        p.description.toLowerCase().includes(q)
      );
    });

    const matchCountOf = (p: Problem) => (target ? matchTarget(p, target).matchedEvidenceIds.length : 0);

    return [...list].sort((a, b) => {
      if (target) {
        const diff = matchCountOf(b) - matchCountOf(a);
        if (diff !== 0) return diff;
      }
      return sort === 'cases'
        ? b.case_count - a.case_count
        : b.updated_at.localeCompare(a.updated_at);
    });
  }, [problems, query, category, sort, target]);

  const selectedCount = selectedProblemIds.length;
  const canCombine = selectedCount >= 2;

  return (
    <AppShell>
      <Page>
        <div className="flex flex-col gap-4 prose-width">
          <PageTitle>문제 탐색</PageTitle>
          <Caption>{DATA_MODE === 'demo' ? '디자인 데모 · 예시 데이터' : '실제 수집 데이터 · 게시 기준 통과'}</Caption>
          <Body>
            실제 불편에서 뽑아낸 문제입니다. 마음이 가는 문제를 눌러 근거를 확인해 보세요.
          </Body>
          {targetLabel ? (
            <Cap>
              현재 타겟: {targetLabel}{' '}
              <NavLink to="/onboarding" className="text-blue font-semibold">
                변경
              </NavLink>
            </Cap>
          ) : (
            <Cap>
              타겟을 입력하면 근거와 얼마나 관련 있는지 함께 보여드립니다.{' '}
              <NavLink to="/onboarding" className="text-blue font-semibold">
                타겟 설정하기
              </NavLink>
            </Cap>
          )}
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
        {loading || error ? <EmptyState title={loading ? '문제를 불러오는 중입니다' : '데이터 연결 오류'} description={error || '저장된 게시 문제를 확인하고 있습니다.'} /> : filtered.length === 0 ? (
          <EmptyState
            title={problems.length ? '조건에 맞는 문제가 없습니다' : '아직 게시된 문제가 없습니다'}
            description={problems.length ? '검색어를 지우거나 카테고리를 전체로 바꿔보세요.' : '충분한 실제 근거와 게시 기준을 갖춘 문제부터 표시됩니다.'}
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
              const match = target ? matchTarget(p, target) : null;
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
                      <Body>{p.one_liner}</Body>
                    </NavLink>

                    {/* 대표 근거 1건 — PRD F03의 카드 필수 항목 */}
                    <p className="text-[14px] text-text-secondary kr border-l-2 border-blue pl-3">
                      {p.evidence[0]?.summary}
                    </p>

                    <div className="flex items-center gap-4 pt-1">
                      <Cap>
                        관련 사례 <b className="text-text-primary">{p.case_count}</b>건
                      </Cap>
                      <Cap>
                        출처 <b className="text-text-primary">{sourceCount(p)}</b>곳
                      </Cap>
                    </div>

                    {target ? (
                      <Cap>
                        {match && match.matchedEvidenceIds.length > 0
                          ? `타겟과 겹치는 근거 ${match.matchedEvidenceIds.length}건`
                          : '타겟과 겹치는 근거 없음'}
                      </Cap>
                    ) : null}
                  </Card>
                </li>
              );
            })}
          </ul>
        )}
      </Page>

      {/* 선택 바 — 2개 이상일 때만 조합으로 넘어갈 수 있다 (현재 잠금 기능) */}
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
