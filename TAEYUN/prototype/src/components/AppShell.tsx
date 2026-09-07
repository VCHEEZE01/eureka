'use client';

/**
 * 전체 화면을 감싸는 껍데기. 헤더 + 본문 + 푸터.
 * Next.js와 공유용 단일 HTML이 같이 쓴다.
 */

import { Bookmark, User as UserIcon } from 'lucide-react';
import type { ReactNode } from 'react';
import { LOGO_SRC } from '@/lib/assets';
import { NavLink, useNav } from '@/lib/nav';
import { useStore } from '@/lib/store';

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col bg-bg">
      <Header />
      <main className="flex-1">{children}</main>
      <Footer />
    </div>
  );
}

function Header() {
  const { user, saved } = useStore();
  const { path } = useNav();

  return (
    <header className="sticky top-0 z-10 bg-bg/95 backdrop-blur border-b border-border">
      <div className="shell h-16 flex items-center justify-between gap-4">
        <NavLink to="/" className="flex items-center" ariaLabel="유레카 홈">
          {/* 로고는 지급된 파일을 그대로 쓴다. */}
          <img src={LOGO_SRC} alt="유레카" className="h-8 w-auto" />
        </NavLink>

        <nav className="flex items-center gap-1">
          <HeaderLink to="/problems" active={path.startsWith('/problems')}>
            문제 탐색
          </HeaderLink>

          <NavLink
            to="/mypage"
            className="inline-flex items-center gap-1.5 h-10 px-3 rounded-[10px] text-[15px] text-text-secondary hover:bg-bg-subtle"
          >
            <Bookmark size={17} aria-hidden />
            <span className="hidden sm:inline">보관함</span>
            {saved.length > 0 ? (
              <span className="inline-flex items-center justify-center min-w-5 h-5 px-1 rounded-full bg-blue text-white text-[12px] font-semibold">
                {saved.length}
              </span>
            ) : null}
          </NavLink>

          {user ? (
            <NavLink
              to="/mypage"
              className="inline-flex items-center gap-1.5 h-10 px-3 rounded-[10px] text-[15px] font-medium text-control-text hover:bg-bg-subtle"
            >
              <UserIcon size={17} aria-hidden />
              <span className="hidden sm:inline">{user.nickname}</span>
            </NavLink>
          ) : (
            <NavLink
              to="/login"
              className="inline-flex items-center h-10 px-4 rounded-[10px] text-[15px] font-semibold text-blue hover:bg-blue-light"
            >
              로그인
            </NavLink>
          )}
        </nav>
      </div>
    </header>
  );
}

function HeaderLink({ to, active, children }: { to: string; active: boolean; children: ReactNode }) {
  return (
    <NavLink
      to={to}
      className={`inline-flex items-center h-10 px-3 rounded-[10px] text-[15px] font-medium ${
        active ? 'text-blue bg-blue-light' : 'text-text-secondary hover:bg-bg-subtle'
      }`}
    >
      {children}
    </NavLink>
  );
}

function Footer() {
  return (
    <footer className="border-t border-border mt-24">
      <div className="shell py-10 flex flex-col gap-2">
        <p className="text-[15px] font-semibold">유레카 — 문제를 발견하고, 아이디어로 바꾸다</p>
        <p className="text-[13px] text-text-muted kr">
          팀 목욕중 · MVP 프로토타입. 화면과 흐름 검토용이며 표시되는 데이터는 전부 가상입니다.
        </p>
      </div>
    </footer>
  );
}

/** 본문 여백 규칙. DESIGN.md 11절 섹션 간 64~96px. */
export function Page({ children }: { children: ReactNode }) {
  return <div className="shell py-14 flex flex-col gap-12">{children}</div>;
}
