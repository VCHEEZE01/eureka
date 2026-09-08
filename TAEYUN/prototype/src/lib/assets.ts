/**
 * 로고 경로.
 * Next.js에서는 public/ 경로를, 공유용 단일 HTML에서는 번들이 로드되기 전
 * 주입해 둔 data URI를 쓴다. 화면 코드는 이 값만 참조한다.
 */
declare global {
  interface Window {
    __EUREKA_LOGO__?: string;
  }
}

export const LOGO_SRC =
  (typeof window !== 'undefined' && window.__EUREKA_LOGO__) || '/eureka.png';
