'use client';

/**
 * 게시 기준 체크리스트 (docs/DATA_COLLECTION.md 6절).
 *
 * ★ 기준 수치는 gate.min_* 로 백엔드에서 함께 받는다. 프론트는 수치를
 *   하드코딩하지 않고 실제 집계값과 실제 판정 기준을 나란히 보여준다.
 */
import { AlertCircle, CheckCircle2 } from 'lucide-react';
import type { PublishGate } from '@/api/types';

export function GateChecklist({
  gate,
  caseCount,
  sourceCount,
  evidenceCount,
}: {
  gate: PublishGate;
  caseCount: number;
  sourceCount: number;
  evidenceCount: number;
}) {
  const rows: { label: string; ok: boolean; minimum: string }[] = [
    { label: `관련 사례 ${caseCount}건`, ok: gate.case_count_ok, minimum: `기준 ${gate.min_cases}건` },
    { label: `서로 다른 출처 ${sourceCount}곳`, ok: gate.source_count_ok, minimum: `기준 ${gate.min_sources}곳` },
    { label: `근거 요약 ${evidenceCount}건`, ok: gate.evidence_count_ok, minimum: `기준 ${gate.min_evidence}건` },
  ];

  return (
    <div className="flex flex-col gap-2.5">
      {rows.map((r) => (
        <div key={r.label} className="flex items-center gap-2">
          {r.ok ? (
            <CheckCircle2 size={18} className="text-blue shrink-0" aria-hidden />
          ) : (
            <AlertCircle size={18} className="text-danger shrink-0" aria-hidden />
          )}
          <span className={`text-[15px] ${r.ok ? 'text-text-primary' : 'text-danger'}`}>{r.label}</span>
          <span className="text-[13px] text-text-muted">({r.minimum})</span>
          <span className="sr-only">{r.ok ? '기준 통과' : '기준 미달'}</span>
        </div>
      ))}
      {gate.passed ? (
        <p className="text-[13px] font-semibold text-blue kr">게시 기준을 통과했습니다.</p>
      ) : gate.reason ? (
        <p className="text-[13px] text-danger kr">{gate.reason}</p>
      ) : null}
    </div>
  );
}
