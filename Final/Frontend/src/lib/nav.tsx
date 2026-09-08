'use client';
/**
 * 라우팅 추상화.
 *
 * 화면(screens/)이 next/navigation 을 직접 부르지 않게 한다.
 * 화면은 useNav() 와 <NavLink> 만 쓴다.
 *
 * 왜 필요한가
 *   · Next.js  → 실제 경로  (/problems/p1)
 *   · 공유용 단일 HTML → 해시 경로 (#/problems/p1)
 *   같은 화면 코드를 양쪽에서 쓰려면 이 층이 있어야 한다.
 *
 * 만들 것
 *   useNav()   { path, go(), back(), hrefFor() }
 *   NavLink    화면 이동 링크
 */
export {};  // TODO: 프론트 담당자가 구현
