'use client';

/**
 * Next.js용 NavProvider.
 * 화면(screens/)은 이 파일을 몰라도 되고 useNav()만 쓴다.
 * 공유용 단일 HTML에서는 이 대신 useHashNav()가 들어간다.
 */

import { usePathname, useRouter } from 'next/navigation';
import { useMemo, type ReactNode } from 'react';
import { NavProvider, type NavApi } from './nav';

export function NextNavProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();

  const api = useMemo<NavApi>(
    () => ({
      path: pathname || '/',
      go: (next) => router.push(next),
      back: () => router.back(),
      hrefFor: (next) => next,
    }),
    [pathname, router],
  );

  return <NavProvider value={api}>{children}</NavProvider>;
}
