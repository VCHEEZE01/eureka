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
    <ul className="space-y-3">
      {evidence.map((item) => {
        const source = sourceById.get(item.sourceId);
        return (
          <li
            key={item.id}
            className="rounded-xl border border-evidence/30 bg-evidence-soft/40 p-4"
          >
            <p className="kr-text text-sm text-foreground">{item.summary}</p>
            {item.excerpt && (
              <p className="kr-text mt-2 border-l-2 border-evidence pl-3 text-sm italic text-foreground/80">
                {item.excerpt}
              </p>
            )}
            <div className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted">
              {source?.url ? (
                <a
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-medium text-evidence hover:underline"
                >
                  {source?.name ?? '출처 미상'}
                </a>
              ) : (
                <span className="font-medium">{source?.name ?? '출처 미상'}</span>
              )}
              <span aria-hidden>·</span>
              <span>{item.postedAt}</span>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
