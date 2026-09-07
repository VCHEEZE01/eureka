import type { Metadata } from 'next';
import { NextNavProvider } from '@/lib/next-nav';
import './globals.css';

export const metadata: Metadata = {
  title: '유레카 — 문제를 발견하고, 아이디어로 바꾸다',
  description:
    '실제 사용자 불편에서 문제를 발견하고, 근거와 함께 실행 가능한 아이디어로 연결하는 서비스. 팀 목욕중 MVP 프로토타입.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <head>
        {/* DESIGN.md 2절: 한국어 기본 폰트는 Pretendard */}
        <link
          rel="stylesheet"
          href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css"
        />
      </head>
      <body>
        <NextNavProvider>{children}</NextNavProvider>
      </body>
    </html>
  );
}
