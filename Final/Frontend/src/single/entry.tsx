/**
 * 공유용 단일 HTML 의 진입점.
 *
 * Next.js 앱과 화면(screens/)을 그대로 공유하고 라우팅만 해시로 바꾼다.
 * 덕분에 UI 를 두 벌 관리하지 않아도 된다.
 *
 * 하는 일
 *   1. 해시 경로(#/problems/p1)를 읽어 어떤 화면을 그릴지 정한다
 *   2. 그 화면을 렌더링한다
 *   3. 데이터는 항상 data/mock.ts 를 쓴다 (서버가 없으므로)
 *
 * 빌드 : npm run build:single → 단일 HTML 파일 생성
 */
export {};  // TODO: 프론트 담당자가 구현
