import Link from 'next/link';
import type { ComponentProps, ReactNode } from 'react';
import { ChevronRightIcon, EvidenceIcon, SparkIcon } from '@/components/icons';

/** 프로토타입 공용 UI 프리미티브. 화면별 컴포넌트는 이 위에 얹는다. */

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg';

const BUTTON_BASE =
  'focus-ring inline-flex items-center justify-center gap-2 rounded-full font-semibold whitespace-nowrap transition-[background-color,border-color,color,box-shadow,transform] duration-150 active:translate-y-px disabled:pointer-events-none disabled:opacity-45';

const BUTTON_SIZES: Record<ButtonSize, string> = {
  sm: 'px-3.5 py-1.5 text-xs',
  md: 'px-5 py-2.5 text-sm',
  lg: 'px-6 py-3 text-base',
};

const BUTTON_STYLES: Record<ButtonVariant, string> = {
  primary:
    'bg-brand text-white shadow-[var(--shadow-sm)] hover:bg-brand-strong hover:shadow-[var(--shadow-md)]',
  secondary:
    'border border-border-strong bg-surface text-foreground hover:border-brand hover:text-brand-strong',
  ghost: 'text-muted hover:bg-surface-muted hover:text-foreground',
  danger: 'border border-border bg-surface text-danger hover:border-danger',
};

function buttonClass(variant: ButtonVariant, size: ButtonSize, extra: string) {
  return `${BUTTON_BASE} ${BUTTON_SIZES[size]} ${BUTTON_STYLES[variant]} ${extra}`;
}

export function Button({
  variant = 'primary',
  size = 'md',
  className = '',
  ...props
}: ComponentProps<'button'> & { variant?: ButtonVariant; size?: ButtonSize }) {
  return <button {...props} className={buttonClass(variant, size, className)} />;
}

export function ButtonLink({
  variant = 'primary',
  size = 'md',
  className = '',
  ...props
}: ComponentProps<typeof Link> & { variant?: ButtonVariant; size?: ButtonSize }) {
  return <Link {...props} className={buttonClass(variant, size, className)} />;
}

type CardTone = 'default' | 'ai' | 'evidence' | 'muted';

const CARD_TONES: Record<CardTone, string> = {
  default: 'border-border bg-surface',
  ai: 'border-ai/25 bg-ai-soft/45',
  evidence: 'border-evidence/25 bg-evidence-soft/45',
  muted: 'border-border bg-surface-muted',
};

export function Card({
  className = '',
  tone = 'default',
  interactive = false,
  children,
}: {
  className?: string;
  tone?: CardTone;
  /** 카드 전체가 링크/버튼일 때 켠다. 호버 시 살짝 떠오르고 포커스 링이 카드에 걸린다. */
  interactive?: boolean;
  /** 스켈레톤처럼 내용 없이 형태만 쓰는 경우가 있어 선택값으로 둔다. */
  children?: ReactNode;
}) {
  return (
    <div
      className={`rounded-2xl border p-5 ${CARD_TONES[tone]} ${
        interactive
          ? 'focus-within-ring shadow-[var(--shadow-sm)] transition-[border-color,box-shadow,transform] duration-200 hover:-translate-y-0.5 hover:border-brand/60 hover:shadow-[var(--shadow-md)]'
          : ''
      } ${className}`}
    >
      {children}
    </div>
  );
}

export function Badge({
  tone = 'neutral',
  icon,
  children,
}: {
  tone?: 'neutral' | 'brand' | 'evidence' | 'ai' | 'outline';
  icon?: ReactNode;
  children: ReactNode;
}) {
  const tones = {
    neutral: 'bg-surface-muted text-muted',
    brand: 'bg-brand-soft text-brand-strong',
    evidence: 'bg-evidence-soft text-evidence',
    ai: 'bg-ai-soft text-ai',
    outline: 'border border-border text-muted',
  } as const;
  return (
    <span
      className={`kr-text inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${tones[tone]}`}
    >
      {icon}
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
    <Badge tone="evidence" icon={<EvidenceIcon />}>
      실제 수집 데이터
    </Badge>
  ) : (
    <Badge tone="ai" icon={<SparkIcon />}>
      AI 생성 설명
    </Badge>
  );
}

export function SectionTitle({
  title,
  description,
  aside,
  eyebrow,
}: {
  title: string;
  description?: string;
  aside?: ReactNode;
  eyebrow?: ReactNode;
}) {
  return (
    <div className="mb-4 flex flex-wrap items-end justify-between gap-x-4 gap-y-3">
      <div className="min-w-0">
        {eyebrow && (
          <p className="mb-1.5 text-xs font-semibold tracking-wide text-brand uppercase">
            {eyebrow}
          </p>
        )}
        <h2 className="kr-text text-lg font-bold tracking-tight">{title}</h2>
        {description && (
          <p className="kr-text mt-1 max-w-2xl text-sm text-muted">{description}</p>
        )}
      </div>
      {aside}
    </div>
  );
}

/**
 * 화면 최상단 제목 블록. 이전에는 화면마다 h1 마크업을 따로 짜서
 * 크기·간격이 조금씩 달랐다.
 */
export function PageHeader({
  eyebrow,
  title,
  description,
  aside,
  children,
}: {
  eyebrow?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  aside?: ReactNode;
  children?: ReactNode;
}) {
  return (
    <header className="rise">
      {eyebrow && <div className="mb-3 flex flex-wrap items-center gap-2">{eyebrow}</div>}
      <div className="flex flex-wrap items-start justify-between gap-x-6 gap-y-4">
        <h1 className="kr-text max-w-3xl text-2xl font-extrabold tracking-tight text-balance sm:text-3xl">
          {title}
        </h1>
        {aside && <div className="shrink-0">{aside}</div>}
      </div>
      {description && (
        <p className="kr-text mt-3 max-w-2xl text-base text-muted">{description}</p>
      )}
      {children}
    </header>
  );
}

/** 화면 경로 표시. 여러 화면에 흩어져 있던 `›` 마크업을 하나로 합쳤다. */
export function Breadcrumbs({
  items,
}: {
  items: { label: string; href?: string }[];
}) {
  return (
    <nav aria-label="현재 위치">
      <ol className="flex flex-wrap items-center gap-1 text-sm text-muted">
        {items.map((item, index) => (
          <li key={item.label} className="flex items-center gap-1">
            {index > 0 && <ChevronRightIcon className="size-3.5 opacity-50" />}
            {item.href ? (
              <Link
                href={item.href}
                className="focus-ring kr-text rounded px-1 py-0.5 transition-colors hover:text-foreground"
              >
                {item.label}
              </Link>
            ) : (
              <span className="kr-text px-1 py-0.5 font-medium text-foreground">
                {item.label}
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
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
    <div className="aurora rounded-2xl border border-dashed border-border-strong bg-surface/60 px-6 py-14 text-center">
      <p className="kr-text text-lg font-bold">{title}</p>
      <p className="kr-text mx-auto mt-2 max-w-md text-sm text-muted">{description}</p>
      {action && <div className="mt-6 flex justify-center">{action}</div>}
    </div>
  );
}

/**
 * 숫자 하나를 크게 보여주는 지표 블록.
 * 단위(건/곳)는 한글이라 display 서체에 글리프가 없다. 숫자만 display로 두고
 * 단위는 본문 서체로 분리해 두 서체가 한 줄에서 어긋나지 않게 한다.
 */
export function Stat({
  label,
  value,
  unit,
  hint,
}: {
  label: string;
  value: ReactNode;
  unit?: string;
  hint?: string;
}) {
  return (
    <div className="rounded-xl border border-border bg-surface px-4 py-3">
      <p className="kr-text text-xs text-muted">{label}</p>
      <p className="mt-1 flex items-baseline gap-1">
        <span className="display text-2xl tabular-nums">{value}</span>
        {unit && <span className="text-sm font-medium text-muted">{unit}</span>}
      </p>
      {hint && <p className="kr-text mt-0.5 text-xs text-muted">{hint}</p>}
    </div>
  );
}

/** hydration 대기 중 빈 화면 대신 쓰는 자리 표시자. */
export function Skeleton({ className = '' }: { className?: string }) {
  return (
    <div className={`skeleton rounded-xl ${className}`}>
      <span className="sr-only">불러오는 중</span>
    </div>
  );
}

/** 카드 목록을 기다리는 동안 실제 레이아웃과 같은 형태를 유지한다. */
export function CardListSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2" aria-hidden>
      {Array.from({ length: count }, (_, index) => (
        <Skeleton key={index} className="h-44" />
      ))}
    </div>
  );
}

/** 폼 입력 공통 스타일. 로그인·개인화 폼이 같은 높이/반경/포커스를 쓰도록 한다. */
export const FIELD_CLASS =
  'focus-ring w-full rounded-xl border border-border bg-surface px-3.5 py-2.5 text-sm text-foreground transition-colors placeholder:text-muted/70 hover:border-border-strong focus-visible:border-brand';
