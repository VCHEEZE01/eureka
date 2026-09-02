import type { Metadata, Viewport } from 'next';
import { Instrument_Serif } from 'next/font/google';
import { Header } from '@/components/Header';
import { StoreProvider } from '@/lib/store';
import './globals.css';

/** 라틴 악센트(통계 숫자·아이브로우) 전용 서체. 한글은 Pretendard로 폴백된다. */
const displaySerif = Instrument_Serif({
  subsets: ['latin'],
  weight: '400',
  display: 'swap',
  variable: '--font-display-serif',
});

export const metadata: Metadata = {
  title: {
    default: '유레카 — 문제에서 아이디어까지',
    template: '%s — 유레카',
  },
  description:
    '실제 사용자 불편 데이터에서 문제를 발견하고, 근거를 확인한 뒤 만들 수 있는 아이디어로 연결합니다.',
};

/** 라이트/다크 양쪽에서 주소창 색이 배경과 이어지도록 한다. */
export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#faf8f4' },
    { media: '(prefers-color-scheme: dark)', color: '#131210' },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko" className={displaySerif.variable}>
      <head>
        {/* 본문 한글용 Pretendard.
            이전에는 --font-pretendard가 정의된 적이 없어 폰트가 실제로는 적용되지 않았다. */}
        <link rel="preconnect" href="https://cdn.jsdelivr.net" />
        <link
          rel="stylesheet"
          href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css"
        />
      </head>
      <body className="flex min-h-dvh flex-col">
        <a
          href="#main"
          className="focus-ring sr-only rounded-full bg-brand px-4 py-2 text-sm font-semibold text-white focus:not-sr-only focus:absolute focus:top-3 focus:left-3 focus:z-50"
        >
          본문으로 건너뛰기
        </a>
        <StoreProvider>
          <Header />
          <main id="main" className="mx-auto w-full max-w-5xl flex-1 px-4 py-8 sm:px-6 sm:py-12">
            {children}
          </main>
          <footer className="mt-16 border-t border-border">
            <div className="mx-auto flex w-full max-w-5xl flex-wrap items-center justify-between gap-3 px-4 py-8 text-xs text-muted sm:px-6">
              <p className="kr-text">
                <span className="font-semibold text-foreground">유레카</span> 프로토타입 · 팀 목욕중
              </p>
              <p className="kr-text">표시되는 문제와 근거는 시연용 샘플 데이터입니다.</p>
            </div>
          </footer>
        </StoreProvider>
      </body>
    </html>
  );
}
