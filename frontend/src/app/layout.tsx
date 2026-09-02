import type { Metadata } from 'next';
import { Header } from '@/components/Header';
import { StoreProvider } from '@/lib/store';
import './globals.css';

export const metadata: Metadata = {
  title: '유레카 — 문제에서 아이디어까지',
  description:
    '실제 사용자 불편 데이터에서 문제를 발견하고, 근거를 확인한 뒤 만들 수 있는 아이디어로 연결합니다.',
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body className="min-h-dvh">
        <StoreProvider>
          <Header />
          <main className="mx-auto max-w-5xl px-5 py-8">{children}</main>
          <footer className="mx-auto max-w-5xl px-5 py-10 text-xs text-muted">
            유레카 프로토타입 · 팀 목욕중 · 표시되는 문제와 근거는 시연용 샘플
            데이터입니다.
          </footer>
        </StoreProvider>
      </body>
    </html>
  );
}
