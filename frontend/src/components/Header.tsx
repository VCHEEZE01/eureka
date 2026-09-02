'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import {
  CloseIcon,
  CompassIcon,
  MenuIcon,
  SlidersIcon,
  UserIcon,
} from '@/components/icons';
import { useStore } from '@/lib/store';
import { VARIANTS, VARIANT_SPECS } from '@/lib/types';

const NAV = [
  { href: '/problems', label: '문제 탐색', icon: CompassIcon },
  { href: '/mypage', label: '마이페이지', icon: UserIcon },
];

/**
 * 상단 헤더.
 *
 * 기본 아이디어 화면(F04)의 A/B/C 변형은 실험 조작 장치라 항상 노출은 하되,
 * 헤더 본줄을 차지하지 않도록 "실험" 팝오버 안으로 접었다. 이전에는 이 스위처가
 * 로고·내비와 같은 줄에 놓여 모바일에서 헤더가 세 줄로 접혔다.
 */
export function Header() {
  const pathname = usePathname();
  const { user, logout, hydrated } = useStore();
  const [menuOpen, setMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  // 경로가 바뀌면 모바일 메뉴를 닫는다. 열린 채로 다음 화면에 남지 않게 한다.
  // 이펙트로 닫으면 열린 메뉴가 한 프레임 보였다 사라지므로 렌더 중에 조정한다.
  const [syncedPath, setSyncedPath] = useState(pathname);
  if (pathname !== syncedPath) {
    setSyncedPath(pathname);
    if (menuOpen) setMenuOpen(false);
  }

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 4);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <header
      className={`sticky top-0 z-40 bg-background/85 backdrop-blur transition-shadow ${
        scrolled ? 'border-b border-border shadow-[var(--shadow-sm)]' : 'border-b border-transparent'
      }`}
    >
      <div className="mx-auto flex h-14 w-full max-w-5xl items-center gap-3 px-4 sm:px-6">
        <Link
          href="/"
          className="focus-ring -mx-1 flex items-baseline gap-1.5 rounded-lg px-1 py-1"
        >
          <span className="text-lg font-extrabold tracking-tight">유레카</span>
          <span className="display hidden text-xs text-brand sm:inline">Eureka</span>
        </Link>

        <nav aria-label="주요" className="ml-2 hidden items-center gap-1 text-sm sm:flex">
          {NAV.map((item) => (
            <NavLink key={item.href} {...item} active={isActive(pathname, item.href)} />
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-1.5">
          <VariantMenu disabled={!hydrated} />

          {hydrated && user ? (
            <div className="hidden items-center gap-1 sm:flex">
              <Link
                href="/mypage"
                title={user.email}
                className="focus-ring max-w-[10rem] truncate rounded-full px-3 py-1.5 text-sm font-medium transition-colors hover:bg-surface-muted"
              >
                {user.nickname}
              </Link>
              <button
                onClick={logout}
                className="focus-ring rounded-full px-2.5 py-1.5 text-sm text-muted transition-colors hover:text-foreground"
              >
                로그아웃
              </button>
            </div>
          ) : (
            <Link
              href="/login"
              className="focus-ring hidden rounded-full border border-border-strong px-4 py-1.5 text-sm font-semibold transition-colors hover:border-brand hover:text-brand-strong sm:inline-flex"
            >
              로그인
            </Link>
          )}

          <button
            type="button"
            aria-expanded={menuOpen}
            aria-controls="mobile-nav"
            aria-label={menuOpen ? '메뉴 닫기' : '메뉴 열기'}
            onClick={() => setMenuOpen((open) => !open)}
            className="focus-ring rounded-full p-2 text-foreground transition-colors hover:bg-surface-muted sm:hidden"
          >
            {menuOpen ? <CloseIcon className="size-5" /> : <MenuIcon className="size-5" />}
          </button>
        </div>
      </div>

      {menuOpen && (
        <div id="mobile-nav" className="border-t border-border bg-background sm:hidden">
          <nav aria-label="주요 (모바일)" className="mx-auto max-w-5xl px-4 py-3">
            <ul className="space-y-1">
              {NAV.map((item) => {
                const active = isActive(pathname, item.href);
                const Icon = item.icon;
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      aria-current={active ? 'page' : undefined}
                      className={`focus-ring flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm font-medium ${
                        active ? 'bg-brand-soft text-brand-strong' : 'hover:bg-surface-muted'
                      }`}
                    >
                      <Icon className="size-4.5" />
                      {item.label}
                    </Link>
                  </li>
                );
              })}
            </ul>

            <div className="mt-3 border-t border-border pt-3">
              {hydrated && user ? (
                <div className="flex items-center justify-between gap-3 px-3">
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-semibold">{user.nickname}</span>
                    <span className="block truncate text-xs text-muted">{user.email}</span>
                  </span>
                  <button
                    onClick={logout}
                    className="focus-ring shrink-0 rounded-full border border-border px-3 py-1.5 text-xs font-medium text-muted"
                  >
                    로그아웃
                  </button>
                </div>
              ) : (
                <Link
                  href="/login"
                  className="focus-ring flex items-center justify-center rounded-xl bg-brand px-4 py-2.5 text-sm font-semibold text-white"
                >
                  로그인
                </Link>
              )}
            </div>
          </nav>
        </div>
      )}
    </header>
  );
}

/** `/mypage`와 `/mypage/library`가 같은 항목으로 묶이도록 경로 접두사로 판단한다. */
function isActive(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(`${href}/`);
}

function NavLink({
  href,
  label,
  icon: Icon,
  active,
}: {
  href: string;
  label: string;
  icon: typeof CompassIcon;
  active: boolean;
}) {
  return (
    <Link
      href={href}
      aria-current={active ? 'page' : undefined}
      className={`focus-ring flex items-center gap-1.5 rounded-full px-3 py-1.5 font-medium transition-colors ${
        active
          ? 'bg-brand-soft text-brand-strong'
          : 'text-muted hover:bg-surface-muted hover:text-foreground'
      }`}
    >
      <Icon className="size-4" />
      {label}
    </Link>
  );
}

/**
 * 기본 아이디어 화면(F04) 버전 전환.
 * 평소에는 아이콘 버튼 하나로 접어 두고, 열었을 때만 각 버전의 설명을 보여준다.
 */
function VariantMenu({ disabled }: { disabled: boolean }) {
  const { variant, setVariant } = useStore();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function onPointerDown(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') setOpen(false);
    }
    document.addEventListener('mousedown', onPointerDown);
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('mousedown', onPointerDown);
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [open]);

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        disabled={disabled}
        aria-expanded={open}
        aria-haspopup="dialog"
        onClick={() => setOpen((v) => !v)}
        className="focus-ring flex items-center gap-1.5 rounded-full border border-border px-3 py-1.5 text-xs font-semibold text-muted transition-colors hover:border-border-strong hover:text-foreground disabled:opacity-45"
      >
        <SlidersIcon className="size-3.5" />
        <span className="hidden sm:inline">아이디어 화면</span>
        <span className="text-brand-strong">{disabled ? '—' : variant}</span>
      </button>

      {open && (
        <div
          role="dialog"
          aria-label="기본 아이디어 화면 버전 선택"
          className="absolute right-0 z-50 mt-2 w-72 rounded-2xl border border-border bg-surface p-2 shadow-[var(--shadow-lg)]"
        >
          <p className="kr-text px-2 pt-1 pb-2 text-xs text-muted">
            F04 기본 아이디어 화면의 A/B 실험 버전입니다.
          </p>
          <ul className="space-y-1">
            {VARIANTS.map((v) => {
              const spec = VARIANT_SPECS[v];
              const active = variant === v;
              return (
                <li key={v}>
                  <button
                    type="button"
                    aria-pressed={active}
                    onClick={() => {
                      setVariant(v);
                      setOpen(false);
                    }}
                    className={`focus-ring flex w-full items-start gap-2.5 rounded-xl px-2.5 py-2 text-left transition-colors ${
                      active ? 'bg-brand-soft' : 'hover:bg-surface-muted'
                    }`}
                  >
                    <span
                      className={`mt-px flex size-5 shrink-0 items-center justify-center rounded-full text-[11px] font-bold ${
                        active ? 'bg-brand text-white' : 'bg-surface-muted text-muted'
                      }`}
                    >
                      {v}
                    </span>
                    <span className="min-w-0">
                      <span
                        className={`kr-text block text-sm font-semibold ${
                          active ? 'text-brand-strong' : ''
                        }`}
                      >
                        {spec.label}
                      </span>
                      <span className="kr-text mt-0.5 block text-xs text-muted">
                        {spec.description}
                      </span>
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
