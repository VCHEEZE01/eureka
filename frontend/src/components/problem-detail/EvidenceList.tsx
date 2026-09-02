import { ExternalIcon } from '@/components/icons';
import type { EvidenceItem, Source } from '@/lib/types';

/**
 * 실제 사용자 불편 요약 3~5건 (F03 근거 영역).
 * 각 항목의 출처명·게시일을 표시하고, excerpt가 있으면 짧은 발췌 인용으로,
 * 출처에 url이 있으면 원문 링크를 함께 보여준다. 링크는 원문 데이터에 있을 때만 노출한다.
 */
export function EvidenceList({
  evidence,
  sources,
}: {
  evidence: EvidenceItem[];
  sources: Source[];
}) {
  const sourceById = new Map(sources.map((s) => [s.id, s]));

  return (
    <ol className="space-y-3">
      {evidence.map((item, index) => {
        const source = sourceById.get(item.sourceId);
        return (
          <li
            key={item.id}
            className="rounded-2xl border border-evidence/25 bg-evidence-soft/40 p-4 sm:p-5"
          >
            <div className="flex gap-3.5">
              <span
                aria-hidden
                className="display mt-px w-5 shrink-0 text-sm text-evidence tabular-nums"
              >
                {String(index + 1).padStart(2, '0')}
              </span>
              <div className="min-w-0 flex-1">
                <p className="kr-text leading-relaxed text-foreground">{item.summary}</p>

                {item.excerpt && (
                  <blockquote className="kr-text mt-3 border-l-2 border-evidence pl-3 text-sm leading-relaxed text-foreground/75 italic">
                    {item.excerpt}
                  </blockquote>
                )}

                <div className="mt-3.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted">
                  {source?.platform && (
                    <span className="rounded-full bg-evidence/10 px-2 py-0.5 font-medium text-evidence">
                      {source.platform}
                    </span>
                  )}
                  {source?.url ? (
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="focus-ring inline-flex items-center gap-1 rounded font-medium text-evidence hover:underline"
                    >
                      {source.name}
                      <ExternalIcon className="size-3" />
                      <span className="sr-only">(새 창)</span>
                    </a>
                  ) : (
                    <span className="font-medium">{source?.name ?? '출처 미상'}</span>
                  )}
                  <span aria-hidden>·</span>
                  <time>{item.postedAt}</time>
                </div>
              </div>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
