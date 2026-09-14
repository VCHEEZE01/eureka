'use client';

/**
 * 근거 페이지의 막대 그래프 — 라이브러리 없이 순수 CSS(flex + width/height %)로 그린다.
 * 가로 막대(⑧ 출처 분포) / 세로 막대(④ 주별 분포) 겸용.
 *
 * 색은 Blue 계열만 쓴다 (globals.css --color-blue 계열).
 */

export interface StatBarItem {
  label: string;
  value: number;
  /** ★ 분모. 항목마다 다를 수 있다(세로 막대는 보통 전체 중 최댓값을 공유). */
  total: number;
  /** 관측 창이 온전하지 않은 항목(예: partial 주차) — 흐리게 표시 */
  dim?: boolean;
}

function pct(value: number, total: number): number {
  if (total <= 0) return 0;
  return Math.max(0, Math.min(100, Math.round((value / total) * 100)));
}

export function StatBar({
  items,
  orientation = 'horizontal',
  unit = '건',
}: {
  items: StatBarItem[];
  orientation?: 'horizontal' | 'vertical';
  unit?: string;
}) {
  if (items.length === 0) return null;

  if (orientation === 'vertical') {
    return (
      <div className="flex items-end gap-3 h-36">
        {items.map((it) => (
          <div key={it.label} className={`flex flex-col items-center justify-end gap-2 flex-1 h-full ${it.dim ? 'opacity-50' : ''}`}>
            <span className="text-[12px] font-semibold text-text-primary">{it.value}</span>
            <div className="w-full flex-1 rounded-t-md bg-blue-light flex flex-col justify-end overflow-hidden">
              <div className="w-full rounded-t-md bg-blue" style={{ height: `${pct(it.value, it.total)}%` }} />
            </div>
            <span className="text-[11px] text-text-muted whitespace-nowrap">{it.label}</span>
          </div>
        ))}
      </div>
    );
  }

  return (
    <ul className="flex flex-col gap-2.5">
      {items.map((it) => (
        <li key={it.label} className={`flex items-center gap-3 ${it.dim ? 'opacity-50' : ''}`}>
          <span className="text-[14px] w-28 shrink-0 truncate">{it.label}</span>
          <span className="flex-1 h-2 rounded-full bg-blue-light overflow-hidden">
            <span className="block h-full rounded-full bg-blue" style={{ width: `${pct(it.value, it.total)}%` }} />
          </span>
          <span className="text-[13px] text-text-secondary w-16 text-right shrink-0">
            {it.value}
            {unit}
          </span>
        </li>
      ))}
    </ul>
  );
}

export interface StackedBarSegment {
  key: string;
  label: string;
  value: number;
  /** Blue 명도 단계를 나타내는 배경 클래스 (bg-blue-hover / bg-blue / bg-blue-light 등) */
  className: string;
}

/** 누적 막대 1줄. ⑦ 불편 강도 분포에 쓴다. 색만이 아니라 라벨·건수를 함께 표기한다. */
export function StackedBar({ segments }: { segments: StackedBarSegment[] }) {
  const total = segments.reduce((sum, s) => sum + s.value, 0);
  if (total === 0) return null;

  return (
    <div className="flex flex-col gap-2.5">
      <div className="flex h-3 w-full rounded-full overflow-hidden bg-bg-subtle" role="img" aria-label="불편 강도 분포">
        {segments
          .filter((s) => s.value > 0)
          .map((s) => (
            <div
              key={s.key}
              className={s.className}
              style={{ width: `${(s.value / total) * 100}%` }}
              title={`${s.label} ${s.value}건`}
            />
          ))}
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-1">
        {segments.map((s) => (
          <span key={s.key} className="inline-flex items-center gap-1.5 text-[13px] text-text-secondary">
            <span className={`inline-block w-2.5 h-2.5 rounded-sm ${s.className}`} aria-hidden />
            {s.label} {s.value}건
          </span>
        ))}
      </div>
    </div>
  );
}

/** 관측 기간 타임라인 바 — 단일 바 + 양 끝 날짜 라벨. */
export function TimelineBar({ first, last }: { first: string | null; last: string | null }) {
  if (!first || !last) {
    return <p className="text-[13px] text-text-muted kr">관측 기간을 계산할 근거가 부족합니다.</p>;
  }
  return (
    <div className="flex flex-col gap-1.5">
      <div className="h-2 w-full rounded-full bg-blue" aria-hidden />
      <div className="flex justify-between text-[12px] text-text-muted">
        <span>{first}</span>
        <span>{last}</span>
      </div>
    </div>
  );
}
