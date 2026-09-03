'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { useStore } from '@/lib/store';
import type { SavedKind } from '@/lib/types';

/**
 * 즐겨찾기 토글 (F07).
 * 저장은 로그인 필요이므로 비로그인 상태에서는 로그인 화면으로 보낸다.
 * 동일 항목 중복 저장은 스토어의 key 규칙으로 막는다.
 */
export function SaveButton({
  kind,
  refId,
  title,
  subtitle,
  href,
  size = 'md',
}: {
  kind: SavedKind;
  refId: string;
  title: string;
  subtitle: string;
  href: string;
  size?: 'sm' | 'md';
}) {
  const router = useRouter();
  const { isSaved, toggleSave, user, hydrated } = useStore();
  const [justChanged, setJustChanged] = useState(false);

  const saved = hydrated && isSaved(kind, refId);

  function handleClick() {
    if (!user) {
      router.push(`/login?next=${encodeURIComponent(href)}`);
      return;
    }
    toggleSave({ kind, refId, title, subtitle, href });
    setJustChanged(true);
    window.setTimeout(() => setJustChanged(false), 1200);
  }

  const label = saved ? '저장됨' : '저장';

  return (
    <button
      onClick={handleClick}
      aria-pressed={saved}
      className={`inline-flex shrink-0 items-center gap-1.5 rounded-full border font-medium transition-colors ${
        size === 'sm' ? 'px-3 py-1 text-xs' : 'px-4 py-1.5 text-sm'
      } ${
        saved
          ? 'border-brand bg-brand-soft text-brand-strong'
          : 'border-border bg-surface text-muted hover:text-foreground'
      }`}
    >
      <span aria-hidden>{saved ? '★' : '☆'}</span>
      {justChanged && saved ? '보관함에 담김' : label}
    </button>
  );
}
