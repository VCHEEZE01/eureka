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
    <div className="space-y-5">
      <div className="space-y-3">
        {platforms.map(([platform, bucket]) => {
          const share = totalCases > 0 ? Math.round((bucket.caseCount / totalCases) * 100) : 0;
          return (
            <div key={platform}>
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">{platform}</span>
                <span className="text-muted tabular-nums">
                  {bucket.caseCount}건 · {share}%
                </span>
              </div>
              <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-surface-muted">
                <div
                  className="h-full rounded-full bg-evidence"
                  style={{ width: `${share}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <ul className="grid gap-2 sm:grid-cols-2">
        {sources.map((source) => (
          <li
            key={source.id}
            className="kr-text flex items-center justify-between gap-2 rounded-xl border border-border bg-surface px-3 py-2 text-sm"
          >
            <span className="flex min-w-0 flex-col">
              {source.url ? (
                <a
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="truncate font-medium hover:text-brand"
                >
                  {source.name}
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
