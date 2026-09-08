'use client';

/**
 * 9. 마이페이지 / 보관함 (PRD F09, F10)
 * 즐겨찾기한 문제·아이디어를 탭으로 나눠 다시 확인한다. 로그인이 필요하다.
 */

import { Bookmark, Lock } from 'lucide-react';
import { useState } from 'react';
import { AppShell, Page } from '@/components/AppShell';
import {
  Badge,
  Body,
  Button,
  Caption,
  Card,
  EmptyState,
  PageTitle,
  buttonClass,
} from '@/components/ui';
import { NavLink } from '@/lib/nav';
import { useStore } from '@/lib/store';
import type { SavedKind } from '@/lib/types';

const TABS: { id: SavedKind | 'all'; label: string }[] = [
  { id: 'all', label: '전체' },
  { id: 'problem', label: '문제' },
  { id: 'idea', label: '아이디어' },
  { id: 'personalized', label: '개인화 결과' },
];

export function MyPageScreen() {
  const { user, saved, runs, logout } = useStore();
  const [tab, setTab] = useState<SavedKind | 'all'>('all');

  if (!user) {
    return (
      <AppShell>
        <Page>
          <div className="max-w-[560px] flex flex-col gap-6">
            <span className="inline-flex w-11 h-11 items-center justify-center rounded-[12px] bg-blue-light text-blue">
              <Lock size={20} aria-hidden />
            </span>
            <PageTitle>보관함은 로그인이 필요합니다</PageTitle>
            <Body>
              저장한 문제와 아이디어를 계정에 묶어두기 때문입니다. 문제 탐색과 기본 아이디어는
              로그인 없이 계속 보실 수 있습니다.
            </Body>
            <div className="flex flex-wrap gap-3">
              <NavLink to="/login" className={buttonClass('primary')}>
                로그인
              </NavLink>
              <NavLink to="/problems" className={buttonClass('ghost')}>
                문제 탐색으로
              </NavLink>
            </div>
          </div>
        </Page>
      </AppShell>
    );
  }

  const list = tab === 'all' ? saved : saved.filter((s) => s.kind === tab);

  return (
    <AppShell>
      <Page>
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div className="flex flex-col gap-3">
            <PageTitle>{user.nickname}님의 보관함</PageTitle>
            <Caption>
              {user.email} · 저장 {saved.length}건 · 개인화 실행 {runs.length}회
            </Caption>
          </div>
          <Button variant="ghost" onClick={logout}>
            로그아웃
          </Button>
        </div>

        <div className="flex flex-wrap gap-2">
          {TABS.map((t) => {
            const count = t.id === 'all' ? saved.length : saved.filter((s) => s.kind === t.id).length;
            return (
              <button
                key={t.id}
                type="button"
                onClick={() => setTab(t.id)}
                className={`h-10 px-4 rounded-[10px] text-[15px] font-medium border transition-colors ${
                  tab === t.id
                    ? 'bg-blue-light border-blue text-blue'
                    : 'bg-bg border-control-border text-control-text hover:bg-bg-subtle'
                }`}
              >
                {t.label} {count > 0 ? <span className="opacity-70">{count}</span> : null}
              </button>
            );
          })}
        </div>

        {list.length === 0 ? (
          <EmptyState
            title="아직 저장한 항목이 없습니다"
            description="문제나 아이디어 화면에서 저장을 누르면 여기에 모입니다."
            action={
              <NavLink to="/problems" className={buttonClass('primary')}>
                문제 탐색하러 가기
              </NavLink>
            }
          />
        ) : (
          <ul className="grid gap-5 md:grid-cols-2">
            {list.map((item) => (
              <li key={item.key}>
                <NavLink to={item.path}>
                  <Card interactive className="h-full flex flex-col gap-3">
                    <div className="flex items-start justify-between gap-3">
                      <Badge tone="blue">{kindLabel(item.kind)}</Badge>
                      <Bookmark size={17} className="text-blue shrink-0" aria-hidden />
                    </div>
                    <p className="text-[18px] font-semibold kr">{item.title}</p>
                    <Body>{item.subtitle}</Body>
                    <Caption className="mt-auto pt-2">
                      {new Date(item.savedAt).toLocaleDateString('ko-KR')} 저장
                    </Caption>
                  </Card>
                </NavLink>
              </li>
            ))}
          </ul>
        )}

        {/* 개인화 실행 이력 — 결과를 다시 열기 위한 경로 */}
        {runs.length > 0 ? (
          <section className="flex flex-col gap-5">
            <p className="text-[20px] font-semibold">개인화 실행 이력</p>
            <ul className="flex flex-col">
              {runs.map((run) => (
                <li key={run.id} className="border-t border-border last:border-b">
                  <NavLink to={`/personalize/${run.id}`} className="flex items-center gap-4 py-5">
                    <div className="flex-1 min-w-0">
                      <p className="text-[16px] font-medium kr mb-1">
                        {run.combined?.title ?? '문제 기반 개인화'}
                      </p>
                      <Caption>
                        {run.input.serviceForm} · {run.input.target} · {run.input.resource} ·
                        아이디어 {run.ideas.length}개
                      </Caption>
                    </div>
                    <Caption>{new Date(run.createdAt).toLocaleDateString('ko-KR')}</Caption>
                  </NavLink>
                </li>
              ))}
            </ul>
          </section>
        ) : null}
      </Page>
    </AppShell>
  );
}

function kindLabel(kind: SavedKind): string {
  if (kind === 'problem') return '문제';
  if (kind === 'idea') return '아이디어';
  return '개인화 결과';
}
