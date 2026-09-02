'use client';

import { useEffect, useRef, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { CloseIcon, SearchIcon } from '@/components/icons';
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
  resultCount: number;
  categories: CategoryFilterOption[];
  current: ProblemFiltersState;
}

/**
 * 문제 탐색 필터 (검색·카테고리·정렬).
 * 상태는 URL 쿼리(`?q=&category=&sort=`)로 관리해 공유·뒤로가기가 가능하도록 한다.
 *
 * 이전에는 검색/카테고리/정렬이 각각 제목을 단 세 개의 블록으로 쌓여 첫 화면의
 * 세로 공간을 대부분 차지했다. 지금은 검색 한 줄 + (카테고리 · 정렬) 한 줄로 접고,
 * 결과 수와 초기화를 같은 도구 모음 안에서 보여준다.
 */
export function ProblemFilters({
  totalCount,
  resultCount,
  categories,
  current,
}: ProblemFiltersProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [searchInput, setSearchInput] = useState(current.q);
  const [syncedQ, setSyncedQ] = useState(current.q);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

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

  function clearSearch() {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    setSearchInput('');
    pushParams({ q: '' });
    inputRef.current?.focus();
  }

  const trimmedInput = searchInput.trim();
  const showTooShortHint =
    trimmedInput.length > 0 && trimmedInput.length < MIN_QUERY_LENGTH;
  const hasFilters = Boolean(current.q || current.category);

  return (
    <div className="space-y-3">
      <div className="relative">
        <label htmlFor="problem-search" className="sr-only">
          문제 검색
        </label>
        <SearchIcon className="pointer-events-none absolute top-1/2 left-4 size-4.5 -translate-y-1/2 text-muted" />
        <input
          id="problem-search"
          ref={inputRef}
          type="search"
          value={searchInput}
          onChange={(event) => handleSearchChange(event.target.value)}
          placeholder="어떤 불편을 찾고 있나요? (2자 이상)"
          maxLength={MAX_QUERY_LENGTH}
          className="focus-ring w-full rounded-full border border-border bg-surface py-3 pr-12 pl-11 text-sm shadow-[var(--shadow-sm)] transition-colors placeholder:text-muted/80 hover:border-border-strong focus-visible:border-brand [&::-webkit-search-cancel-button]:hidden"
          aria-describedby={showTooShortHint ? 'problem-search-hint' : undefined}
        />
        {searchInput && (
          <button
            type="button"
            onClick={clearSearch}
            aria-label="검색어 지우기"
            className="focus-ring absolute top-1/2 right-3 -translate-y-1/2 rounded-full p-1.5 text-muted transition-colors hover:bg-surface-muted hover:text-foreground"
          >
            <CloseIcon className="size-4" />
          </button>
        )}
      </div>

      {showTooShortHint && (
        <p id="problem-search-hint" className="px-1 text-xs text-brand-strong">
          검색어는 2자 이상 입력해주세요.
        </p>
      )}

      <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
        <div
          className="no-scrollbar -mx-1 flex flex-1 basis-full items-center gap-2 overflow-x-auto px-1 py-0.5 sm:basis-0"
          role="group"
          aria-label="카테고리 선택"
        >
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

        <div
          role="group"
          aria-label="정렬 선택"
          className="flex shrink-0 items-center gap-0.5 rounded-full border border-border bg-surface p-0.5"
        >
          {SORT_OPTIONS.map((option) => {
            const active = current.sort === option;
            return (
              <button
                key={option}
                type="button"
                aria-pressed={active}
                onClick={() => pushParams({ sort: option })}
                className={`focus-ring rounded-full px-3 py-1.5 text-xs font-semibold transition-colors ${
                  active
                    ? 'bg-brand text-white'
                    : 'text-muted hover:text-foreground'
                }`}
              >
                {SORT_LABEL[option]}
              </button>
            );
          })}
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2 border-t border-border pt-3 text-sm">
        <p className="text-muted" role="status" aria-live="polite">
          총 <span className="font-semibold text-foreground tabular-nums">{resultCount}</span>건
          {hasFilters && <span className="text-muted"> / 전체 {totalCount}건</span>}
        </p>
        {hasFilters && (
          <button
            type="button"
            onClick={() => {
              setSearchInput('');
              pushParams({ q: '', category: '' });
            }}
            className="focus-ring rounded-full px-2 py-1 text-xs font-medium text-muted underline-offset-2 transition-colors hover:text-foreground hover:underline"
          >
            필터 초기화
          </button>
        )}
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
      className={`focus-ring inline-flex shrink-0 items-center gap-1.5 rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors ${
        active
          ? 'border-brand bg-brand-soft text-brand-strong'
          : 'border-border bg-surface text-muted hover:border-border-strong hover:text-foreground'
      }`}
    >
      <span className="kr-text whitespace-nowrap">{label}</span>
      <span className="text-xs tabular-nums opacity-70">{count}</span>
    </button>
  );
}
