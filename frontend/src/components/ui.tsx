import Link from 'next/link';
import type { ComponentProps, ReactNode } from 'react';

/** 프로토타입 공용 UI 프리미티브. 화면별 컴포넌트는 이 위에 얹는다. */

type ButtonVariant = 'primary' | 'secondary' | 'ghost';

const BUTTON_BASE =
  'inline-flex items-center justify-center gap-2 rounded-full px-5 py-2.5 text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand';

const BUTTON_STYLES: Record<ButtonVariant, string> = {
  primary: 'bg-brand text-white hover:bg-brand-strong',
  secondary:
    'border border-border bg-surface text-foreground hover:bg-surface-muted',
  ghost: 'text-muted hover:bg-surface-muted hover:text-foreground',
};

export function Button({
  variant = 'primary',
  className = '',
  ...props
}: ComponentProps<'button'> & { variant?: ButtonVariant }) {
  return (
    <button
      {...props}
      className={`${BUTTON_BASE} ${BUTTON_STYLES[variant]} ${className}`}
    />
  );
}

export function ButtonLink({
  variant = 'primary',
  className = '',
  ...props
}: ComponentProps<typeof Link> & { variant?: ButtonVariant }) {
  return (
    <Link
      {...props}
      className={`${BUTTON_BASE} ${BUTTON_STYLES[variant]} ${className}`}
    />
  );
}

export function Card({
  className = '',
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return (
    <div
      className={`rounded-2xl border border-border bg-surface p-5 ${className}`}
    >
      {children}
    </div>
  );
}

export function Badge({
  tone = 'neutral',
  children,
}: {
  tone?: 'neutral' | 'brand' | 'evidence' | 'ai';
  children: ReactNode;
}) {
  const tones = {
    neutral: 'bg-surface-muted text-muted',
    brand: 'bg-brand-soft text-brand-strong',
    evidence: 'bg-evidence-soft text-evidence',
    ai: 'bg-ai-soft text-ai',
  } as const;
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${tones[tone]}`}
    >
      {children}
    </span>
  );
}

/**
 * PRD F03/F06: 실제 수집 근거와 AI 서술을 시각적으로 구분해야 한다.
 * 두 영역 모두 이 라벨을 상단에 달아 출처 성격을 명시한다.
 */
export function OriginLabel({ origin }: { origin: 'evidence' | 'ai' }) {
  return origin === 'evidence' ? (
    <Badge tone="evidence">실제 수집 데이터</Badge>
  ) : (
    <Badge tone="ai">AI 생성 설명</Badge>
  );
}

export function SectionTitle({
  title,
  description,
  aside,
}: {
  title: string;
  description?: string;
  aside?: ReactNode;
}) {
  return (
    <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h2 className="text-lg font-bold">{title}</h2>
        {description && (
          <p className="kr-text mt-1 text-sm text-muted">{description}</p>
        )}
      </div>
      {aside}
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-dashed border-border bg-surface px-6 py-12 text-center">
      <p className="font-semibold">{title}</p>
      <p className="kr-text mx-auto mt-2 max-w-md text-sm text-muted">
        {description}
      </p>
      {action && <div className="mt-5 flex justify-center">{action}</div>}
    </div>
  );
}

export function Stat({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="rounded-xl bg-surface-muted px-4 py-3">
      <p className="text-xs text-muted">{label}</p>
      <p className="mt-1 text-xl font-bold tabular-nums">{value}</p>
    </div>
  );
}
