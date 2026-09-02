import { ExternalIcon } from '@/components/icons';
import type { Source, SourcePlatform } from '@/lib/types';

/**
 * 출처 목록 + 플랫폼별 분포 (F03).
 * `sources`를 platform 기준으로 묶어 caseCount 합계 대비 비중을 CSS 바로 보여준다.
 * 차트 라이브러리 없이 순수 CSS 폭으로만 표현하며, 근거 없는 수치는 만들지 않는다.
 */
export function SourceBreakdown({ sources }: { sources: Source[] }) {
  const totalCases = sources.reduce((sum, s) => sum + s.caseCount, 0);

  const byPlatform = new Map<SourcePlatform, { caseCount: number; sources: Source[] }>();
  for (const source of sources) {
    const bucket = byPlatform.get(source.platform) ?? { caseCount: 0, sources: [] };
    bucket.caseCount += source.caseCount;
    bucket.sources.push(source);
    byPlatform.set(source.platform, bucket);
  }

  const platforms = [...byPlatform.entries()].sort((a, b) => b[1].caseCount - a[1].caseCount);

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-border bg-surface p-5">
        {/* 전체 비중을 한 줄로 먼저 보여주고, 아래에서 플랫폼별로 나눈다. */}
        <div
          className="flex h-2.5 overflow-hidden rounded-full bg-surface-muted"
          role="img"
          aria-label={`플랫폼별 사례 비중: ${platforms
            .map(([platform, bucket]) => `${platform} ${bucket.caseCount}건`)
            .join(', ')}`}
        >
          {platforms.map(([platform, bucket], index) => (
            <span
              key={platform}
              className="h-full bg-evidence"
              style={{
                width: `${totalCases > 0 ? (bucket.caseCount / totalCases) * 100 : 0}%`,
                opacity: 1 - index * 0.18,
              }}
            />
          ))}
        </div>

        <dl className="mt-4 space-y-3">
          {platforms.map(([platform, bucket], index) => {
            const share = totalCases > 0 ? Math.round((bucket.caseCount / totalCases) * 100) : 0;
            return (
              <div key={platform} className="flex items-center gap-3 text-sm">
                <span
                  aria-hidden
                  className="size-2.5 shrink-0 rounded-full bg-evidence"
                  style={{ opacity: 1 - index * 0.18 }}
                />
                <dt className="kr-text font-medium">{platform}</dt>
                <dd className="ml-auto text-muted tabular-nums">
                  {bucket.caseCount}건
                  <span className="ml-2 font-semibold text-foreground">{share}%</span>
                </dd>
              </div>
            );
          })}
        </dl>
      </div>

      <ul className="grid gap-2 sm:grid-cols-2">
        {sources.map((source) => (
          <li
            key={source.id}
            className="kr-text flex items-center justify-between gap-2 rounded-xl border border-border bg-surface px-3.5 py-2.5 text-sm transition-colors hover:border-border-strong"
          >
            <span className="flex min-w-0 flex-col">
              {source.url ? (
                <a
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="focus-ring inline-flex items-center gap-1 truncate rounded font-medium hover:text-brand-strong"
                >
                  <span className="truncate">{source.name}</span>
                  <ExternalIcon className="size-3 shrink-0" />
                  <span className="sr-only">(새 창)</span>
                </a>
              ) : (
                <span className="truncate font-medium">{source.name}</span>
              )}
              <span className="text-xs text-muted">{source.platform}</span>
            </span>
            <span className="shrink-0 text-xs text-muted tabular-nums">{source.caseCount}건</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
