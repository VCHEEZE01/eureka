# 유레카 프론트엔드 (프로토타입)

PRD.md 기준 MVP 화면을 구현한 Next.js 프로토타입입니다.

## 실행

```bash
cd frontend
npm install
npm run dev      # http://localhost:3000
```

## 프로토타입 범위

- 백엔드/AI 호출이 없습니다. 문제·근거·기본 아이디어·개인화 결과는 모두
  `src/data/*`의 시연용 가상 데이터와 규칙 기반 조합으로 만들어집니다.
- 로그인은 실제 인증 없이 브라우저 `localStorage`에만 저장되는 목업입니다.
- 즐겨찾기·보관함·개인화 실행 기록도 동일하게 브라우저에만 남습니다.

## 화면 구성

| 경로 | PRD |
| :-- | :-- |
| `/` | F01 랜딩 |
| `/problems` | F02 문제 탐색 |
| `/problems/[id]` | F03 문제 상세 / 근거 확인 |
| `/problems/[id]/ideas` | F04 문제 기반 기본 아이디어 |
| `/ideas/[id]` | F06 아이디어 상세 / Why This Idea |
| `/personalize` | F05 초개인화 요청 |
| `/personalize/[runId]` | F05 개인화 결과 |
| `/personalize/[runId]/[ideaId]` | F06 개인화 아이디어 상세 |
| `/mypage` | 마이페이지 (계정·저장 현황) |
| `/mypage/library` | F07 보관함 |
| `/login` | F08 로그인 |

`/library`는 이전 경로라 `/mypage/library`로 리다이렉트됩니다.

## 기본 아이디어 화면 A/B/C 버전

`/problems/[id]/ideas`의 하단 행동 유도만 다른 세 버전을 두고,
**상단 헤더의 A · B · C 버튼**으로 즉시 전환합니다.
KPI "개인화 이용률"을 비교하기 위한 구성이라 아이디어 카드 내용은 세 버전이 동일합니다.

| 버전 | 하단 버튼 | 의도 |
| :-- | :-- | :-- |
| A | 내 상황에 맞게 구체화 | PRD 기본 흐름. 개인화로 전환 |
| B | 다른 아이디어 보기 | 같은 문제에서 다른 아이디어 묶음을 다시 제공 |
| C | 없음 | 대조군 |

선택한 버전은 브라우저에 저장되며, `?v=A` `?v=B` `?v=C` 쿼리로 링크를 공유해
특정 버전으로 바로 열 수도 있습니다.

## 구조

```text
src/
├── app/           # App Router 화면
├── components/    # 공용 UI 및 화면별 컴포넌트
├── data/          # 시연용 가상 데이터 (문제/아이디어)
└── lib/
    ├── types.ts       # 도메인 타입 (전 화면 공통 계약)
    ├── data.ts        # 데이터 접근 계층
    ├── personalize.ts # 규칙 기반 개인화 아이디어 생성
    └── store.tsx      # 로그인/저장/버전 전역 상태
```

실제 수집 파이프라인(F00)이 붙으면 `src/lib/data.ts` 구현만 교체하면 됩니다.
