'use client';

/**
 * 에이전틱 진행 상태 UI.
 * PRD F05·F07의 [잠정] 항목 — 조합·개인화는 실시간 생성이라
 * 대기 시간에 무엇을 하고 있는지 단계로 보여준다.
 *
 * 프로토타입에서는 실제 에이전트가 없으므로 단계만 재현한다.
 * 화면 흐름 검토가 목적이므로 총 대기 시간은 짧게 잡았다.
 */

import { Check, Loader2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Caption } from './ui';

/**
 * F05 조합 · F07 개인화의 기본 단계.
 * 이미 만들어진 문제에서 아이디어를 합성하는 흐름이다.
 */
export const SYNTHESIS_STEPS = ['탐색 조건 해석', '후보 수집', '중복 정리', '근거 정리'] as const;

/**
 * F02 온보딩의 단계.
 * 처음 요청하는 소스 조합은 캐시 미스라 그 자리에서 수집해야 하므로(PRD F00),
 * 아이디어 합성이 아니라 수집 파이프라인의 단계를 보여준다.
 */
export const RESEARCH_STEPS = [
  '선택 범위 확인',
  '소스별 수집',
  '신호 해석',
  '중복 정리',
  '문제 목록 구성',
] as const;

/** 단계당 대기 시간(ms). 실제 처리 시간 목표는 PRD 10절 TBD. */
const STEP_MS = 550;

export function AgentProgress({
  onDone,
  label,
  steps = SYNTHESIS_STEPS,
}: {
  onDone: () => void;
  label: string;
  steps?: readonly string[];
}) {
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (step >= steps.length) {
      onDone();
      return;
    }
    const timer = setTimeout(() => setStep((s) => s + 1), STEP_MS);
    return () => clearTimeout(timer);
    // onDone은 호출부에서 안정적으로 넘긴다.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step]);

  return (
    <div className="rounded-[16px] border border-border bg-bg-subtle p-8 max-w-[560px]">
      <p className="text-[18px] font-semibold mb-1 kr">{label}</p>
      <Caption className="mb-6">
        조건에 맞춰 그 자리에서 만들고 있습니다. 잠시만 기다려 주세요.
      </Caption>

      <ol className="flex flex-col gap-3">
        {steps.map((name, i) => {
          const done = i < step;
          const active = i === step;
          return (
            <li key={name} className="flex items-center gap-3">
              <span
                className={`inline-flex items-center justify-center w-6 h-6 rounded-full shrink-0 ${
                  done ? 'bg-blue text-white' : active ? 'bg-blue-light text-blue' : 'bg-border text-text-muted'
                }`}
                aria-hidden
              >
                {done ? (
                  <Check size={14} />
                ) : active ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <span className="text-[12px]">{i + 1}</span>
                )}
              </span>
              <span
                className={`text-[15px] ${
                  done ? 'text-text-secondary' : active ? 'text-text-primary font-medium' : 'text-text-muted'
                }`}
              >
                {name}
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
