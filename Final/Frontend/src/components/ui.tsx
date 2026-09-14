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

import { AlertCircle, ChevronDown, X } from 'lucide-react';
import { useState, type KeyboardEvent, type ReactNode } from 'react';

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

const FIELD_INVALID = 'border-danger focus:border-danger';

export function TextInput({
  value,
  onChange,
  placeholder,
  type = 'text',
  id,
  invalid,
  describedBy,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
  id?: string;
  invalid?: boolean;
  describedBy?: string;
}) {
  return (
    <input
      id={id}
      type={type}
      value={value}
      placeholder={placeholder}
      onChange={(e) => onChange(e.target.value)}
      aria-invalid={invalid || undefined}
      aria-describedby={describedBy}
      className={`${FIELD} ${invalid ? FIELD_INVALID : ''}`}
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

/**
 * 드롭다운. ui.tsx에 없던 것을 신규로 만든다(타겟 설정 온보딩용).
 * 네이티브 <select> + appearance-none + ChevronDown 아이콘.
 */
export function Select({
  value,
  onChange,
  options,
  id,
  invalid,
  describedBy,
  ariaLabel,
}: {
  value: string;
  onChange: (v: string) => void;
  options: readonly string[];
  id?: string;
  invalid?: boolean;
  describedBy?: string;
  ariaLabel?: string;
}) {
  return (
    <div className="relative">
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-invalid={invalid || undefined}
        aria-describedby={describedBy}
        aria-label={ariaLabel}
        className={`${FIELD} appearance-none pr-10 ${invalid ? FIELD_INVALID : ''}`}
      >
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
      <ChevronDown
        size={18}
        className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-text-muted"
        aria-hidden
      />
    </div>
  );
}

/** Badge 기반 삭제 가능 칩. 삭제 버튼은 마우스 전용이 아니라 focus 가능한 <button>이다. */
export function TokenChip({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <span className="inline-flex items-center gap-1 h-8 pl-3 pr-1.5 rounded-lg bg-bg-subtle border border-border text-text-secondary text-[13px] font-medium">
      {label}
      <button
        type="button"
        onClick={onRemove}
        aria-label={`${label} 삭제`}
        className="inline-flex items-center justify-center w-5 h-5 rounded-full text-text-muted hover:bg-border hover:text-text-primary"
      >
        <X size={12} aria-hidden />
      </button>
    </span>
  );
}

/**
 * 엔터로 칩을 등록하는 입력. 키보드만으로 등록·삭제가 모두 가능해야 한다.
 * trim + 빈 문자열 무시, 대소문자·공백 정규화 후 중복 무시, 개수 상한.
 */
export function TokenInput({
  id,
  value,
  onChange,
  placeholder,
  max,
  invalid,
  describedBy,
  onDraftChange,
}: {
  id?: string;
  value: string[];
  onChange: (next: string[]) => void;
  placeholder?: string;
  max: number;
  invalid?: boolean;
  describedBy?: string;
  /** 사용자가 뭔가 입력을 시작했음을 상위에 알린다 (invalid 즉시 해제용). */
  onDraftChange?: () => void;
}) {
  const [draft, setDraft] = useState('');
  const atMax = value.length >= max;

  const commit = () => {
    const trimmed = draft.trim().slice(0, 20);
    if (!trimmed || atMax) {
      setDraft('');
      return;
    }
    const exists = value.some((v) => v.toLowerCase() === trimmed.toLowerCase());
    if (!exists) onChange([...value, trimmed]);
    setDraft('');
  };

  const handleDraftChange = (v: string) => {
    setDraft(v);
    if (v.trim().length > 0) onDraftChange?.();
  };

  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    // 한글 IME 조합 중 Enter는 마지막 글자 확정용이다. 이때 commit하면
    // 마지막 글자가 별도 토큰으로 남을 수 있으므로 조합 완료 뒤 Enter만 처리한다.
    if (e.nativeEvent.isComposing || e.keyCode === 229) return;

    if (e.key === 'Enter') {
      e.preventDefault();
      commit();
    }
  };

  const remove = (idx: number) => onChange(value.filter((_, i) => i !== idx));

  return (
    <div className="flex flex-col gap-2.5">
      <input
        id={id}
        type="text"
        value={draft}
        onChange={(e) => handleDraftChange(e.target.value)}
        onKeyDown={onKeyDown}
        onBlur={commit}
        placeholder={atMax ? `최대 ${max}개까지 등록할 수 있습니다` : placeholder}
        disabled={atMax}
        aria-invalid={invalid || undefined}
        aria-describedby={describedBy}
        className={`${FIELD} ${invalid ? FIELD_INVALID : ''}`}
      />
      {value.length > 0 ? (
        <ul className="flex flex-wrap gap-2" aria-label="등록된 항목">
          {value.map((v, i) => (
            <li key={v}>
              <TokenChip label={v} onRemove={() => remove(i)} />
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

export function Field({
  label,
  hint,
  htmlFor,
  children,
  error,
}: {
  label: string;
  hint?: string;
  htmlFor?: string;
  children: ReactNode;
  error?: string;
}) {
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={htmlFor} className="text-[15px] font-semibold">
        {label}
      </label>
      {hint ? <Caption>{hint}</Caption> : null}
      {children}
      {error ? (
        <p
          id={htmlFor ? `${htmlFor}-error` : undefined}
          role="alert"
          className="flex items-center gap-1.5 text-[13px] text-danger"
        >
          <AlertCircle size={14} aria-hidden />
          {error}
        </p>
      ) : null}
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
      이 화면의 문제·수치는 흐름 확인용 예시 데이터입니다. 실제 수집 결과가 아닙니다.
    </p>
  );
}
