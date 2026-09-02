import { ButtonLink, EmptyState, PageHeader } from '@/components/ui';
import { ProblemCardLink } from '@/components/ProblemCard';
import {
  ProblemFilters,
  type CategoryFilterOption,
} from '@/components/problems/ProblemFilters';
import { countByCategory, getAllProblems, listProblems } from '@/lib/data';
import {
  CATEGORIES,
  SORT_OPTIONS,
  type Category,
  type SortOption,
} from '@/lib/types';

/** F02 검색 정책: 선택 입력, 2~50자. 1자 검색어는 무시한다. */
const MIN_QUERY_LENGTH = 2;
const MAX_QUERY_LENGTH = 50;

type RawSearchParams = Record<string, string | string[] | undefined>;

function firstValue(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

/** 신뢰할 수 없는 원본 문자열을 검증된 검색어로 정규화한다. */
function normalizeQuery(raw: string | undefined): string {
  const trimmed = (raw ?? '').trim().slice(0, MAX_QUERY_LENGTH);
  return trimmed.length >= MIN_QUERY_LENGTH ? trimmed : '';
}

/** 알 수 없는 카테고리 값은 전체(미지정)로 되돌린다. */
function normalizeCategory(raw: string | undefined): Category | undefined {
  return (CATEGORIES as readonly string[]).includes(raw ?? '')
    ? (raw as Category)
    : undefined;
}

/** 알 수 없는 정렬 값은 데이터 계층 기본값(관련 사례순)으로 되돌린다. */
function normalizeSort(raw: string | undefined): SortOption {
  return (SORT_OPTIONS as readonly string[]).includes(raw ?? '')
    ? (raw as SortOption)
    : 'cases';
}

export default async function ProblemsPage({
  searchParams,
}: {
  searchParams: Promise<RawSearchParams>;
}) {
  const rawParams = await searchParams;
  const q = normalizeQuery(firstValue(rawParams.q));
  const category = normalizeCategory(firstValue(rawParams.category));
  const sort = normalizeSort(firstValue(rawParams.sort));

  const results = listProblems({ q: q || undefined, category, sort });
  const totalCount = getAllProblems().length;
  const categoryOptions: CategoryFilterOption[] = CATEGORIES.map((value) => ({
    value,
    count: countByCategory(value),
  }));

  const hasQuery = q.length > 0;
  const hasCategoryFilter = Boolean(category);
  const isEmpty = results.length === 0;

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow={<span className="display text-sm tracking-[0.18em] text-brand uppercase">Explore</span>}
        title="문제 탐색"
        description="커뮤니티·리뷰·뉴스·소셜에서 모은 실제 불편 중 관심 있는 문제를 찾아보세요."
      />

      <ProblemFilters
        totalCount={totalCount}
        resultCount={results.length}
        categories={categoryOptions}
        current={{ q, category, sort }}
      />

      {isEmpty ? (
        hasQuery ? (
          <EmptyState
            title="검색 결과가 없습니다"
            description={`"${q}"에 해당하는 문제를 찾지 못했습니다. 검색어를 바꾸거나 전체 문제를 확인해보세요.`}
            action={<ButtonLink href="/problems">전체 문제 보기</ButtonLink>}
          />
        ) : hasCategoryFilter ? (
          <EmptyState
            title="이 카테고리에는 아직 데이터가 없습니다"
            description="다른 카테고리에서 문제를 탐색해보세요."
            action={
              <div className="flex flex-wrap justify-center gap-2">
                {categoryOptions
                  .filter((item) => item.value !== category && item.count > 0)
                  .map((item) => (
                    <ButtonLink
                      key={item.value}
                      href={`/problems?category=${encodeURIComponent(item.value)}`}
                      variant="secondary"
                    >
                      {item.value}
                    </ButtonLink>
                  ))}
                <ButtonLink href="/problems">전체 문제 보기</ButtonLink>
              </div>
            }
          />
        ) : (
          <EmptyState
            title="표시할 문제가 없습니다"
            description="현재 수집된 문제 데이터가 없습니다. 잠시 후 다시 시도해주세요."
            action={<ButtonLink href="/problems">전체 문제 보기</ButtonLink>}
          />
        )
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2">
          {results.map((problem) => (
            <ProblemCardLink key={problem.id} problem={problem} />
          ))}
        </ul>
      )}
    </div>
  );
}
