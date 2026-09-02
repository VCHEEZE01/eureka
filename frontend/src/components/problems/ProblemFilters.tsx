'use client';

import { useEffect, useRef, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import type { Category, SortOption } from '@/lib/types';
import { SORT_OPTIONS, SORT_LABEL } from '@/lib/types';

/** F02 검색 정책: 선택 입력, 2~50자. */
const MIN_QUERY_LENGTH = 2;
const MAX_QUERY_LENGTH = 50;
const SEARCH_DEBOUNCE_MS = 250;

export interface CategoryFilterOption {
  value: Category;
  count: number;
}

export interface ProblemFiltersState {
  q: string;
  category?: Category;
  sort: SortOption;
}

interface ProblemFiltersProps {
  totalCount: number;
  categories: CategoryFilterOption[];
  current: ProblemFiltersState;
}

/**
 * 문제 탐색 필터 (검색·카테고리·정렬).
 * 상태는 URL 쿼리(`?q=&category=&sort=`)로 관리해 공유·뒤로가기가 가능하도록 한다.
 */
export function ProblemFilters({
  totalCount,
  categories,
  current,
}: ProblemFiltersProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [searchInput, setSearchInput] = useState(current.q);
  const [syncedQ, setSyncedQ] = useState(current.q);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // 뒤로/앞으로 가기 등 외부 URL 변경 시 입력값을 동기화한다.
  // 이펙트 대신 렌더 중 조정 패턴을 쓰면 추가 렌더 없이 반영된다.
  if (current.q !== syncedQ) {
    setSyncedQ(current.q);
    setSearchInput(current.q);
  }

  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  function pushParams(
    overrides: Partial<{ q: string; category: string; sort: SortOption }>,
  ) {
    const next = {
      q: overrides.q ?? current.q,
      category:
        overrides.category !== undefined
          ? overrides.category
          : (current.category ?? ''),
      sort: overrides.sort ?? current.sort,
    };

    const params = new URLSearchParams();
    if (next.q) params.set('q', next.q);
    if (next.category) params.set('category', next.category);
    if (next.sort) params.set('sort', next.sort);

    const qs = params.toString();
    router.replace(qs ? `${pathname}?${qs}` : pathname);
  }

  function handleSearchChange(value: string) {
    setSearchInput(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      const trimmed = value.trim().slice(0, MAX_QUERY_LENGTH);
      // 1자는 검색하지 않는다. 힌트만 보여주고 URL은 건드리지 않는다.
      if (trimmed.length === 1) return;
      pushParams({ q: trimmed });
    }, SEARCH_DEBOUNCE_MS);
  }

  const trimmedInput = searchInput.trim();
  const showTooShortHint =
    trimmedInput.length > 0 && trimmedInput.length < MIN_QUERY_LENGTH;

  return (
    <div className="space-y-5">
      <div>
        <label htmlFor="problem-search" className="sr-only">
          문제 검색
        </label>
        <input
          id="problem-search"
          type="search"
          value={searchInput}
          onChange={(event) => handleSearchChange(event.target.value)}
          placeholder="어떤 불편을 찾고 있나요? (2자 이상)"
          maxLength={MAX_QUERY_LENGTH}
          className="w-full rounded-full border border-border bg-surface px-5 py-3 text-sm outline-none placeholder:text-muted focus-visible:border-brand focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
          aria-describedby={showTooShortHint ? 'problem-search-hint' : undefined}
        />
        {showTooShortHint && (
          <p id="problem-search-hint" className="mt-2 text-xs text-muted">
            검색어는 2자 이상 입력해주세요.
          </p>
        )}
      </div>

      <div>
        <span className="mb-2 block text-xs font-semibold text-muted">
          카테고리
        </span>
        <div className="flex flex-wrap gap-2" role="group" aria-label="카테고리 선택">
          <CategoryChip
            label="전체"
            count={totalCount}
            active={!current.category}
            onClick={() => pushParams({ category: '' })}
          />
          {categories.map((item) => (
            <CategoryChip
              key={item.value}
              label={item.value}
              count={item.count}
              active={current.category === item.value}
              onClick={() => pushParams({ category: item.value })}
            />
          ))}
        </div>
      </div>

      <div>
        <span className="mb-2 block text-xs font-semibold text-muted">정렬</span>
        <div className="flex flex-wrap gap-2" role="group" aria-label="정렬 선택">
          {SORT_OPTIONS.map((option) => {
            const active = current.sort === option;
            return (
              <button
                key={option}
                type="button"
                aria-pressed={active}
                onClick={() => pushParams({ sort: option })}
                className={`rounded-full border px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand ${
                  active
                    ? 'border-brand bg-brand-soft text-brand-strong'
                    : 'border-border bg-surface text-muted hover:text-foreground'
                }`}
              >
                {SORT_LABEL[option]}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function CategoryChip({
  label,
  count,
  active,
  onClick,
}: {
  label: string;
  count: number;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      className={`inline-flex items-center gap-1.5 rounded-full border px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand ${
        active
          ? 'border-brand bg-brand-soft text-brand-strong'
          : 'border-border bg-surface text-muted hover:text-foreground'
      }`}
    >
      <span className="kr-text">{label}</span>
      <span className="text-xs tabular-nums opacity-70">{count}</span>
    </button>
  );
}
