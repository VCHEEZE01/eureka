'use client';

/**
 * 라우팅 추상화.
 *
 * 화면(screens/)을 Next.js와 공유용 단일 HTML이 함께 쓰기 위한 장치다.
 * 화면은 next/navigation을 직접 부르지 않고 여기의 useNav()만 쓴다.
 *
 * - Next.js  → 실제 경로 (/problems/p1)
 * - 단일 HTML → 해시 경로 (#/problems/p1)
 *
 * 덕분에 화면 코드를 두 벌 관리하지 않아도 된다.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

export interface NavApi {
  /** 현재 경로. 항상 '/'로 시작한다. */
  path: string;
  go: (path: string) => void;
  back: () => void;
  /** <a href>에 넣을 실제 값 (단일 HTML에서는 '#'가 붙는다) */
  hrefFor: (path: string) => string;
}

const NavContext = createContext<NavApi | null>(null);

export function NavProvider({ value, children }: { value: NavApi; children: ReactNode }) {
  return <NavContext.Provider value={value}>{children}</NavContext.Provider>;
}

export function useNav(): NavApi {
  const api = useContext(NavContext);
  if (!api) throw new Error('useNav는 NavProvider 안에서만 쓸 수 있습니다.');
  return api;
}

/**
 * 해시 기반 구현. 공유용 단일 HTML 전용.
 * 파일을 더블클릭해 file://로 열어도 화면 이동이 동작한다.
 */
export function useHashNav(): NavApi {
  const read = () => {
    const raw = typeof window === 'undefined' ? '' : window.location.hash.replace(/^#/, '');
    return raw.startsWith('/') ? raw : '/';
  };
  const [path, setPath] = useState(read);

  useEffect(() => {
    const sync = () => setPath(read());
    window.addEventListener('hashchange', sync);
    sync();
    return () => window.removeEventListener('hashchange', sync);
  }, []);

  return useMemo(
    () => ({
      path,
      go: (next) => {
        window.location.hash = next;
        window.scrollTo(0, 0);
      },
      back: () => window.history.back(),
      hrefFor: (next) => `#${next}`,
    }),
    [path],
  );
}

/**
 * 화면 이동 링크. 화면에서는 next/link 대신 이걸 쓴다.
 * 마우스 오른쪽 클릭·새 탭 열기가 되도록 실제 href를 유지한다.
 */
export function NavLink({
  to,
  children,
  className,
  ariaLabel,
}: {
  to: string;
  children: ReactNode;
  className?: string;
  ariaLabel?: string;
}) {
  const { go, hrefFor } = useNav();
  const onClick = useCallback(
    (event: React.MouseEvent<HTMLAnchorElement>) => {
      // 새 탭/새 창 의도는 브라우저에 맡긴다.
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.button !== 0) return;
      event.preventDefault();
      go(to);
    },
    [go, to],
  );

  return (
    <a href={hrefFor(to)} onClick={onClick} className={className} aria-label={ariaLabel}>
      {children}
    </a>
  );
}
