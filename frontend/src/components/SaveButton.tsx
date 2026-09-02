'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import { BookmarkIcon } from '@/components/icons';
import { useStore } from '@/lib/store';
import type { SavedKind } from '@/lib/types';

/**
 * 즐겨찾기 토글 (F07).
 * 저장은 로그인 필요이므로 비로그인 상태에서는 로그인 화면으로 보낸다.
 * 동일 항목 중복 저장은 스토어의 key 규칙으로 막는다.
 *
 * 라벨은 "저장 / 저장됨" 두 가지로 고정한다. 이전에는 누른 직후 "보관함에 담김"으로
 * 길어지면서 버튼 폭이 변해 옆 요소가 밀렸다. 확인 메시지는 레이아웃을 차지하지 않는
 * live region으로만 알린다.
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
  const [announcement, setAnnouncement] = useState('');
  const [pulse, setPulse] = useState(false);
  const timers = useRef<number[]>([]);

  useEffect(() => {
    const pending = timers.current;
    return () => pending.forEach(clearTimeout);
  }, []);

  const saved = hydrated && isSaved(kind, refId);

  function handleClick() {
    if (!user) {
      router.push(`/login?next=${encodeURIComponent(href)}`);
      return;
    }
    toggleSave({ kind, refId, title, subtitle, href });
    setAnnouncement(saved ? '보관함에서 제외했습니다.' : '보관함에 담았습니다.');
    setPulse(true);
    timers.current.push(
      window.setTimeout(() => setPulse(false), 400),
      window.setTimeout(() => setAnnouncement(''), 2000),
    );
  }

  return (
    <>
      <button
        onClick={handleClick}
        aria-pressed={saved}
        title={saved ? '보관함에서 빼기' : '보관함에 담기'}
        className={`focus-ring inline-flex shrink-0 items-center gap-1.5 rounded-full border font-medium transition-[background-color,border-color,color] active:translate-y-px ${
          size === 'sm' ? 'px-3 py-1.5 text-xs' : 'px-4 py-2 text-sm'
        } ${
          saved
            ? 'border-brand bg-brand-soft text-brand-strong'
            : 'border-border-strong bg-surface text-muted hover:border-brand hover:text-brand-strong'
        }`}
      >
        <BookmarkIcon
          filled={saved}
          className={`transition-transform duration-300 ${pulse ? 'scale-125' : 'scale-100'}`}
        />
        {saved ? '저장됨' : '저장'}
      </button>
      <span role="status" aria-live="polite" className="sr-only">
        {announcement}
      </span>
    </>
  );
}
