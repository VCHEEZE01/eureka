'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useStore } from '@/lib/store';
import { VARIANTS, VARIANT_SPECS } from '@/lib/types';

const NAV = [
  { href: '/problems', label: '문제 탐색' },
  { href: '/mypage', label: '마이페이지' },
];

/**
 * 상단 헤더. 기본 아이디어 화면(F04)의 A/B/C 변형을 여기서 전환한다.
 * 실험 대상 화면이 아닌 곳에서도 항상 노출해 언제든 버전을 바꿀 수 있게 한다.
 */
export function Header() {
  const pathname = usePathname();
  const { user, logout, variant, setVariant, hydrated } = useStore();

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/85 backdrop-blur">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-x-6 gap-y-3 px-5 py-3">
        <Link href="/" className="text-lg font-extrabold tracking-tight">
          유레카
        </Link>

        <nav className="flex items-center gap-1 text-sm">
          {NAV.map((item) => {
            const active = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`rounded-full px-3 py-1.5 font-medium transition-colors ${
                  active
                    ? 'bg-surface-muted text-foreground'
                    : 'text-muted hover:text-foreground'
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="ml-auto flex items-center gap-4">
          <VariantSwitcher
            value={variant}
            onChange={setVariant}
            disabled={!hydrated}
          />
          {hydrated && user ? (
            <button
              onClick={logout}
              className="text-sm text-muted hover:text-foreground"
              title={user.email}
            >
              {user.nickname} · 로그아웃
            </button>
          ) : (
            <Link
              href="/login"
              className="text-sm font-medium text-muted hover:text-foreground"
            >
              로그인
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}

function VariantSwitcher({
  value,
  onChange,
  disabled,
}: {
  value: string;
  onChange: (v: (typeof VARIANTS)[number]) => void;
  disabled: boolean;
}) {
  return (
    <div className="flex items-center gap-2">
      <span className="hidden text-xs text-muted sm:inline">
        아이디어 화면 버전
      </span>
      <div
        role="group"
        aria-label="기본 아이디어 화면 버전 선택"
        className="flex items-center rounded-full border border-border bg-surface p-0.5"
      >
        {VARIANTS.map((v) => {
          const spec = VARIANT_SPECS[v];
          const active = value === v;
          return (
            <button
              key={v}
              onClick={() => onChange(v)}
              disabled={disabled}
              aria-pressed={active}
              title={`${v}. ${spec.label} — ${spec.description}`}
              className={`rounded-full px-3 py-1 text-xs font-semibold transition-colors disabled:opacity-50 ${
                active
                  ? 'bg-brand text-white'
                  : 'text-muted hover:text-foreground'
              }`}
            >
              {v}
            </button>
          );
        })}
      </div>
    </div>
  );
}
