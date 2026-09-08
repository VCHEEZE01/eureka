'use client';

/**
 * 로그인 (PRD F10)
 * 로그인 방식은 PRD 10절 TBD 상태다.
 * 프로토타입에서는 인증 없이 이메일만 받아 로그인 상태를 흉내 낸다.
 */

import { useState } from 'react';
import { AppShell, Page } from '@/components/AppShell';
import { Body, Button, Caption, Field, PageTitle, TextInput } from '@/components/ui';
import { useNav } from '@/lib/nav';
import { useStore } from '@/lib/store';

export function LoginScreen() {
  const { login } = useStore();
  const { go, back } = useNav();
  const [email, setEmail] = useState('');
  const [nickname, setNickname] = useState('');

  const valid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) && nickname.trim().length > 0;

  const submit = () => {
    if (!valid) return;
    login(email.trim(), nickname.trim());
    back();
  };

  return (
    <AppShell>
      <Page>
        <div className="max-w-[440px] flex flex-col gap-8">
          <div className="flex flex-col gap-4">
            <PageTitle>로그인</PageTitle>
            <Body>
              저장한 문제와 개인화 결과를 계정에 묶어둡니다. 탐색과 기본 아이디어는 로그인 없이도
              볼 수 있습니다.
            </Body>
          </div>

          <div className="flex flex-col gap-5">
            <Field label="이메일" htmlFor="email">
              <TextInput
                id="email"
                type="email"
                value={email}
                onChange={setEmail}
                placeholder="you@example.com"
              />
            </Field>

            <Field label="닉네임" htmlFor="nickname">
              <TextInput
                id="nickname"
                value={nickname}
                onChange={setNickname}
                placeholder="보관함에 표시될 이름"
              />
            </Field>

            <Button onClick={submit} disabled={!valid} full>
              로그인
            </Button>

            <Button variant="ghost" onClick={() => go('/problems')} full>
              로그인 없이 둘러보기
            </Button>
          </div>

          <div className="rounded-[12px] bg-bg-subtle border border-border p-4">
            <Caption>
              프로토타입이라 실제 인증은 하지 않습니다. 입력한 값은 이 브라우저에만 저장되고 서버로
              전송되지 않습니다. 실제 로그인 방식(이메일·소셜 등)은 아직 정해지지 않았습니다.
            </Caption>
          </div>
        </div>
      </Page>
    </AppShell>
  );
}
