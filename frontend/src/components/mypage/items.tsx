'use client';

import Link from 'next/link';
import { ArrowRightIcon, CloseIcon } from '@/components/icons';
import { Badge, Card } from '@/components/ui';
import type { PersonalizationRun, SavedItem } from '@/lib/types';

/** 마이페이지와 보관함이 함께 쓰는 목록 조각. */

export function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    });
  } catch {
    return iso;
  }
}

export function kindLabel(kind: SavedItem['kind']): string {
  if (kind === 'problem') return '문제';
  return kind === 'personalized' ? '개인화 아이디어' : '기본 아이디어';
}

export function SavedRow({
  item,
  onUnsave,
}: {
  item: SavedItem;
  /** 없으면 저장 해제 버튼을 숨긴다. 마이페이지 미리보기에서 쓴다. */
  onUnsave?: () => void;
}) {
  return (
    <Card interactive className="group flex flex-wrap items-start justify-between gap-3">
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone={item.kind === 'personalized' ? 'ai' : 'brand'}>
            {kindLabel(item.kind)}
          </Badge>
          <span className="text-xs text-muted">{formatDate(item.savedAt)} 저장</span>
        </div>
        <Link
          href={item.href}
          className="focus-ring kr-text mt-2 flex items-center gap-1.5 rounded font-semibold transition-colors group-hover:text-brand-strong"
        >
          {item.title}
          <ArrowRightIcon className="size-3.5 shrink-0 opacity-0 transition-opacity group-hover:opacity-100" />
        </Link>
        <p className="kr-text mt-1 text-sm text-muted">{item.subtitle}</p>
      </div>
      {onUnsave && (
        <button
          onClick={onUnsave}
          title={`"${item.title}" 저장 해제`}
          className="focus-ring inline-flex shrink-0 items-center gap-1 rounded-full border border-border px-3 py-1.5 text-xs font-medium text-muted transition-colors hover:border-danger hover:text-danger"
        >
          <CloseIcon className="size-3" />
          저장 해제
        </button>
      )}
    </Card>
  );
}

export function summarizeRun(run: PersonalizationRun): string {
  const { serviceForm, target, resource, extra } = run.input;
  const base = [serviceForm, target, resource].join(' · ');
  return extra ? `${base} · ${extra}` : base;
}

export function RunRow({ run }: { run: PersonalizationRun }) {
  return (
    <Card interactive className="group flex h-full flex-col">
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-muted">
        <span>{formatDate(run.createdAt)} 실행</span>
        <span className="tabular-nums">아이디어 {run.ideas.length}개</span>
      </div>
      <p className="kr-text mt-2.5 text-sm leading-relaxed font-medium">{summarizeRun(run)}</p>
      <Link
        href={`/personalize/${run.id}`}
        className="focus-ring mt-auto inline-flex items-center gap-1 rounded pt-4 text-sm font-semibold text-brand hover:underline"
      >
        결과 다시 보기
        <ArrowRightIcon className="size-3.5" />
      </Link>
    </Card>
  );
}

/** 로그인이 필요한 마이페이지 계열 화면의 공통 안내. */
export const LOGIN_GATE = {
  title: '마이페이지는 로그인이 필요합니다',
  description:
    '저장한 문제와 아이디어, 개인화 실행 기록은 계정 단위로 보관됩니다. 로그인 후 다시 확인해주세요.',
} as const;
