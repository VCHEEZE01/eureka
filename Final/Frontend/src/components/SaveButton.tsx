'use client';

/**
 * 즐겨찾기 토글 (PRD F09).
 * 로그인 필요 기능이므로 비로그인 상태에서는 로그인으로 유도한다.
 * 같은 항목 중복 저장은 불가하고 토글로만 해제된다.
 */

import { Bookmark, BookmarkCheck } from 'lucide-react';
import { useNav } from '@/lib/nav';
import { useStore } from '@/lib/store';
import type { SavedKind } from '@/lib/types';

export function SaveButton({
  kind,
  refId,
  title,
  subtitle,
  path,
  full,
}: {
  kind: SavedKind;
  refId: string;
  title: string;
  subtitle: string;
  path: string;
  full?: boolean;
}) {
  const { user, isSaved, toggleSave } = useStore();
  const { go } = useNav();
  const saved = isSaved(kind, refId);

  const onClick = () => {
    if (!user) {
      go('/login');
      return;
    }
    toggleSave({ kind, refId, title, subtitle, path });
  };

  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={saved}
      className={`inline-flex items-center justify-center gap-2 h-12 px-5 rounded-[12px] font-semibold text-[15px] border transition-colors ${
        saved
          ? 'bg-blue-light border-blue text-blue'
          : 'bg-bg border-control-border text-control-text hover:bg-bg-subtle'
      } ${full ? 'w-full' : ''}`}
    >
      {saved ? <BookmarkCheck size={18} aria-hidden /> : <Bookmark size={18} aria-hidden />}
      {saved ? '저장됨' : '저장'}
    </button>
  );
}
