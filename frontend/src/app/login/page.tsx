'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useState, type FormEvent } from 'react';
import { Button, Card } from '@/components/ui';
import { useStore } from '@/lib/store';

/**
 * F08 로그인. 프로토타입 목업 인증 — 실제 인증 서버 없이 브라우저(localStorage)에만
 * 저장한다. PRD 9-TBD: 로그인 방식(이메일/소셜)은 아직 결정되지 않았다.
 */

const DEFAULT_NEXT = '/problems';
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/** same-origin 단일 경로만 허용한다. `//evil.com`, `http...` 등은 기본값으로 되돌린다. */
function sanitizeNext(raw: string | null): string {
  if (!raw) return DEFAULT_NEXT;
  if (!raw.startsWith('/') || raw.startsWith('//')) return DEFAULT_NEXT;
  try {
    // 상대 경로를 절대 URL로 해석해 스킴이 섞여 들어오는 경우까지 막는다.
    const resolved = new URL(raw, 'http://localhost');
    if (resolved.origin !== 'http://localhost') return DEFAULT_NEXT;
    return `${resolved.pathname}${resolved.search}${resolved.hash}`;
  } catch {
    return DEFAULT_NEXT;
  }
}

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginPageInner />
    </Suspense>
  );
}

function LoginPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, login, logout, hydrated } = useStore();

  const [email, setEmail] = useState('');
  const [nickname, setNickname] = useState('');
  const [error, setError] = useState('');

  const next = sanitizeNext(searchParams.get('next'));

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      setError('이메일을 입력해주세요.');
      return;
    }
    if (!EMAIL_PATTERN.test(trimmedEmail)) {
      setError('이메일 형식을 확인해주세요. 예: name@example.com');
      return;
    }
    setError('');
    login(trimmedEmail, nickname.trim() || undefined);
    router.replace(next);
  }

  if (!hydrated) {
    return <div className="mx-auto max-w-md" />;
  }

  return (
    <div className="mx-auto max-w-md space-y-8">
      <section>
        <h1 className="text-2xl font-extrabold">로그인</h1>
        <p className="kr-text mt-2 text-sm text-muted">
          로그인하면 즐겨찾기·보관함과 초개인화 아이디어를 계정 단위로
          유지할 수 있습니다.
        </p>
      </section>

      <Card className="border-dashed bg-surface-muted">
        <p className="kr-text text-sm text-muted">
          이 로그인은 프로토타입용 임시 화면입니다. 실제 인증 서버 없이
          입력한 정보가 브라우저에만 저장되며, 로그인 방식(이메일/소셜 등)은
          PRD상 아직 결정되지 않았습니다(TBD).
        </p>
      </Card>

      {user ? (
        <Card>
          <p className="text-sm text-muted">현재 로그인된 계정</p>
          <p className="mt-1 text-lg font-bold">{user.nickname}</p>
          <p className="mt-0.5 text-sm text-muted">{user.email}</p>
          <div className="mt-5 flex gap-2">
            <Button variant="secondary" onClick={logout}>
              로그아웃
            </Button>
          </div>
        </Card>
      ) : (
        <Card>
          <form className="space-y-5" onSubmit={handleSubmit} noValidate>
            <div>
              <label htmlFor="login-email" className="text-sm font-medium">
                이메일
              </label>
              <input
                id="login-email"
                type="email"
                value={email}
                onChange={(event) => {
                  setEmail(event.target.value);
                  if (error) setError('');
                }}
                placeholder="name@example.com"
                className="mt-1.5 w-full rounded-xl border border-border bg-surface px-3.5 py-2.5 text-sm outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
                aria-invalid={Boolean(error)}
                aria-describedby={error ? 'login-email-error' : undefined}
              />
              {error && (
                <p id="login-email-error" className="kr-text mt-1.5 text-xs text-red-600">
                  {error}
                </p>
              )}
            </div>

            <div>
              <label htmlFor="login-nickname" className="text-sm font-medium">
                닉네임 <span className="text-muted">(선택)</span>
              </label>
              <input
                id="login-nickname"
                type="text"
                value={nickname}
                onChange={(event) => setNickname(event.target.value)}
                placeholder="입력하지 않으면 이메일 앞부분을 사용합니다"
                className="mt-1.5 w-full rounded-xl border border-border bg-surface px-3.5 py-2.5 text-sm outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
              />
            </div>

            <Button type="submit" className="w-full">
              시작하기
            </Button>
          </form>
        </Card>
      )}

      <section className="space-y-2">
        <p className="text-sm font-semibold">로그인하면 이런 걸 할 수 있어요</p>
        <ul className="kr-text list-inside list-disc space-y-1 text-sm text-muted">
          <li>관심 있는 문제·아이디어 즐겨찾기</li>
          <li>저장한 항목을 보관함에서 다시 확인</li>
          <li>내 조건에 맞춘 초개인화 아이디어 받기</li>
        </ul>
        <p className="kr-text mt-3 text-xs text-muted">
          랜딩, 문제 탐색, 문제 상세, 기본 아이디어 확인은 로그인 없이도
          이용할 수 있습니다.
        </p>
      </section>
    </div>
  );
}
