'use client';

/**
 * 공용 UI 조각.
 * 수치·색은 전부 유레카_임시_DESIGN.md에서 왔다. 여기서 임의로 만들지 않는다.
 *
 * DESIGN.md 15절 Don't를 지킨다:
 * - 카드는 꼭 필요한 경우에만
 * - 색상은 Blue 하나로, 보라색 AI 스타일 금지
 * - 과한 그림자·애니메이션 금지
 */

import type { ReactNode } from 'react';

/* ── Button (DESIGN.md 9절) ────────────────────────────────────── */

type ButtonVariant = 'primary' | 'secondary' | 'ghost';

const BUTTON_BASE =
  'inline-flex items-center justify-center gap-2 h-12 px-5 rounded-[12px] font-semibold text-[15px] transition-colors disabled:opacity-40 disabled:cursor-not-allowed';

const BUTTON_VARIANT: Record<ButtonVariant, string> = {
  primary: 'bg-blue text-white hover:bg-blue-hover',
  secondary: 'bg-bg text-control-text border border-control-border hover:bg-bg-subtle',
  ghost: 'bg-transparent text-text-secondary hover:bg-bg-subtle',
};

export function Button({
  children,
  variant = 'primary',
  onClick,
  disabled,
  type = 'button',
  full,
}: {
  children: ReactNode;
  variant?: ButtonVariant;
  onClick?: () => void;
  disabled?: boolean;
  type?: 'button' | 'submit';
  full?: boolean;
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${BUTTON_BASE} ${BUTTON_VARIANT[variant]} ${full ? 'w-full' : ''}`}
    >
      {children}
    </button>
  );
}

/** 링크를 버튼처럼 보이게 할 때 쓰는 클래스. NavLink에 넘긴다. */
export function buttonClass(variant: ButtonVariant = 'primary', full = false): string {
  return `${BUTTON_BASE} ${BUTTON_VARIANT[variant]} ${full ? 'w-full' : ''}`;
}

/* ── Card (DESIGN.md 8절) ──────────────────────────────────────── */

export function Card({
  children,
  className = '',
  interactive,
}: {
  children: ReactNode;
  className?: string;
  interactive?: boolean;
}) {
  return (
    <div
      className={`bg-bg border border-border rounded-[16px] p-6 shadow-[0_2px_8px_rgba(0,0,0,0.04)] ${
        interactive ? 'transition-colors hover:border-blue' : ''
      } ${className}`}
    >
      {children}
    </div>
  );
}

/* ── 타이포 (DESIGN.md 3절) ────────────────────────────────────── */

export function PageTitle({ children }: { children: ReactNode }) {
  return <h1 className="text-[36px] leading-[1.3] font-bold kr">{children}</h1>;
}

export function SectionTitle({ children }: { children: ReactNode }) {
  return <h2 className="text-[24px] leading-[1.35] font-bold kr">{children}</h2>;
}

export function CardTitle({ children }: { children: ReactNode }) {
  return <h3 className="text-[20px] leading-[1.45] font-semibold kr">{children}</h3>;
}

export function Caption({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <p className={`text-[13px] text-text-muted kr ${className}`}>{children}</p>;
}

export function Body({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <p className={`text-[16px] leading-[1.6] text-text-secondary kr ${className}`}>{children}</p>;
}

/* ── Badge / Chip ──────────────────────────────────────────────── */

export function Badge({ children, tone = 'neutral' }: { children: ReactNode; tone?: 'neutral' | 'blue' }) {
  const cls =
    tone === 'blue'
      ? 'bg-blue-light text-blue'
      : 'bg-bg-subtle text-text-secondary border border-border';
  return (
    <span className={`inline-flex items-center h-7 px-2.5 rounded-lg text-[13px] font-medium ${cls}`}>
      {children}
    </span>
  );
}

export function Chip({
  children,
  selected,
  onClick,
}: {
  children: ReactNode;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={`h-11 px-4 rounded-[12px] text-[15px] font-medium transition-colors border ${
        selected
          ? 'bg-blue-light border-blue text-blue'
          : 'bg-bg border-control-border text-control-text hover:bg-bg-subtle'
      }`}
    >
      {children}
    </button>
  );
}

/* ── Input (DESIGN.md 10절) ────────────────────────────────────── */

const FIELD =
  'w-full h-12 px-4 rounded-[12px] border border-control-border bg-bg text-[15px] outline-none focus:border-blue';

export function TextInput({
  value,
  onChange,
  placeholder,
  type = 'text',
  id,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
  id?: string;
}) {
  return (
    <input
      id={id}
      type={type}
      value={value}
      placeholder={placeholder}
      onChange={(e) => onChange(e.target.value)}
      className={FIELD}
    />
  );
}

export function TextArea({
  value,
  onChange,
  placeholder,
  maxLength,
  id,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  maxLength?: number;
  id?: string;
}) {
  return (
    <textarea
      id={id}
      value={value}
      placeholder={placeholder}
      maxLength={maxLength}
      rows={4}
      onChange={(e) => onChange(e.target.value)}
      className={`${FIELD} h-auto py-3 leading-[1.6] resize-y`}
    />
  );
}

export function Field({
  label,
  hint,
  htmlFor,
  children,
}: {
  label: string;
  hint?: string;
  htmlFor?: string;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={htmlFor} className="text-[15px] font-semibold">
        {label}
      </label>
      {hint ? <Caption>{hint}</Caption> : null}
      {children}
    </div>
  );
}

/* ── 근거 / AI 구분 (PRD 8절) ──────────────────────────────────── */

/**
 * PRD 8절: "실제로 수집된 근거"와 "AI가 생성한 설명"을 시각적으로 구분한다.
 * DESIGN.md가 보라색 AI 스타일을 금지하므로, 색을 늘리지 않고
 * 근거는 Blue 계열 / AI 서술은 회색 계열로 나눈다.
 */
export function EvidencePanel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-[16px] border border-blue-light bg-blue-soft p-6">
      <div className="flex items-center gap-2 mb-4">
        <span className="inline-block w-1.5 h-1.5 rounded-full bg-blue" aria-hidden />
        <span className="text-[13px] font-semibold text-blue">실제 수집된 근거</span>
      </div>
      <h3 className="text-[20px] font-semibold mb-4 kr">{title}</h3>
      {children}
    </section>
  );
}

export function AiPanel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-[16px] border border-border bg-bg-subtle p-6">
      <div className="flex items-center gap-2 mb-4">
        <span className="inline-block w-1.5 h-1.5 rounded-full bg-text-muted" aria-hidden />
        <span className="text-[13px] font-semibold text-text-muted">AI가 생성한 설명</span>
      </div>
      <h3 className="text-[20px] font-semibold mb-4 kr">{title}</h3>
      {children}
    </section>
  );
}

/* ── 기타 ──────────────────────────────────────────────────────── */

export function EmptyState({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return (
    <div className="py-20 text-center">
      <p className="text-[18px] font-semibold mb-2 kr">{title}</p>
      <Body className="mb-6">{description}</Body>
      {action}
    </div>
  );
}

export function Divider() {
  return <hr className="border-0 border-t border-border" />;
}

/** 프로토타입임을 밝히는 고지. PRD 8절의 "근거 없는 수치 생성 금지"와 짝을 이룬다. */
export function PrototypeNotice() {
  return (
    <p className="text-[13px] text-text-muted kr">
      이 화면의 문제·아이디어·수치는 흐름 확인용 가상 데이터입니다. 실제 수집 결과가 아닙니다.
    </p>
  );
}
