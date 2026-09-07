# 유레카 프로토타입

`TAEYUN/` 폴더의 기획 문서를 화면으로 옮긴 MVP 프로토타입입니다.

- 기능 정의: [Eureka_PRD_v2.md](../Eureka_PRD_v2.md)
- 화면 흐름: [flow_diagram_abstract.png](../flow_diagram_abstract.png)
- 디자인 규칙: [유레카_임시_DESIGN.md](../유레카_임시_DESIGN.md)

**표시되는 문제·아이디어·수치는 전부 흐름 확인용 가상 데이터입니다.** 실제 수집 결과가 아닙니다.

## 실행

```bash
npm install     # 처음 한 번만
npm run dev     # http://localhost:3000
```

## 공유용 단일 HTML 만들기

```bash
npm run build:single
```

`TAEYUN/eureka-공유용.html` 파일 하나가 만들어집니다. 더블클릭하면 브라우저에서 바로 열리고,
카톡·메일로 그 파일만 보내도 상대방이 똑같이 볼 수 있습니다. 설치도 서버도 필요 없습니다.

## 구조

화면 코드는 **한 벌만** 있습니다. Next.js 앱과 공유용 HTML이 같은 코드를 씁니다.

```
src/
├── screens/     ← 실제 화면 9종. 여기만 고치면 양쪽 다 반영된다
├── components/  ← 공용 UI 조각 (버튼·카드·근거 패널 등)
├── data/        ← 가상 데이터 (문제 9개, 아이디어 27개)
├── lib/
│   ├── types.ts       도메인 타입 (PRD 6절 기준)
│   ├── nav.tsx        라우팅 추상화 ★
│   ├── next-nav.tsx   Next.js용 구현
│   ├── store.tsx      로그인·저장·개인화 결과 (localStorage)
│   └── personalize.ts 조합·개인화 생성기
├── app/         ← Next.js 라우트 (screens를 감싸기만 하는 얇은 껍데기)
└── single/      ← 공유용 HTML 진입점 (해시 라우팅)
```

**★ 핵심은 `lib/nav.tsx`입니다.** 화면은 `next/link`나 `useRouter`를 직접 쓰지 않고
`useNav()` / `<NavLink>`만 씁니다. 그래서 Next.js에서는 `/problems/p1`로,
공유용 HTML에서는 `#/problems/p1`로 같은 화면이 동작합니다.

새 화면을 만들 때도 `next/navigation`을 직접 import하지 마세요. 그 순간 공유용 빌드가 깨집니다.

## 화면과 PRD 대응

| 경로 | 화면 | PRD |
| :-- | :-- | :-- |
| `/` | 랜딩 | F01 |
| `/onboarding` | 리서치 범위 선택 | F02 ★개인화 2 |
| `/problems` | 문제 탐색 | F03 |
| `/problems/combine` | 문제정의 조합 확인 | F05 ★개인화 1 |
| `/combined/[id]` | 조합된 문제정의 | F05 |
| `/problems/[id]` | 문제 상세 — **유일한 분기 지점** | F04 |
| `/problems/[id]/ideas` | 기본 아이디어 | F06 |
| `/ideas/[id]` | 아이디어 상세 | F08 |
| `/personalize/from/[baseId]` | 개인화 설정 | F07 ★개인화 3 |
| `/personalize/[runId]` | 개인화 결과 목록 | F07 |
| `/personalize/[runId]/[ideaId]` | 개인화 결과 상세 | F08 |
| `/mypage` | 보관함 | F09 |
| `/login` | 로그인 | F10 |

## 구현하면서 PRD를 따른 지점

- **단일 검증점수를 만들지 않았습니다.** PRD 6절 F04 결정에 따라 근거 건수와 출처 수로만 신뢰를 표현합니다.
- **근거와 AI 서술을 시각적으로 분리했습니다.** PRD 8절 요구사항입니다.
  DESIGN.md가 "보라색 AI 스타일 남발"을 금지해서, 색을 늘리지 않고
  근거는 Blue 계열 패널 / AI 서술은 회색 패널로 나눴습니다.
- **기술 난이도 슬라이더를 넣지 않았습니다.** PRD 10절 TBD의 권고대로 입력받지 않고,
  서비스 형태와 타깃에서 시스템이 참고값을 추론해 결과에만 표시합니다.
- **에이전틱 진행 상태 UI를 3곳에 넣었습니다.** 실시간 생성이라 대기가 생기는 지점 전부입니다 —
  3가지 개인화 포인트와 정확히 일치합니다.
  - **F02 온보딩** — 처음 고른 소스 조합은 캐시 미스라 그 자리에서 수집해야 합니다(F00).
    단계: 선택 범위 확인 → 소스별 수집 → 신호 해석 → 중복 정리 → 문제 목록 구성
  - **F05 조합 / F07 개인화** — 이미 있는 문제에서 합성합니다.
    단계: 탐색 조건 해석 → 후보 수집 → 중복 정리 → 근거 정리

  단계 이름이 두 벌인 이유는 하는 일이 다르기 때문입니다(수집 vs 합성).
  둘 다 `components/AgentProgress.tsx` 한 컴포넌트가 `steps` 값만 바꿔 씁니다.
- **같은 조건이면 항상 같은 결과가 나옵니다.** `Math.random()`을 쓰지 않고 입력 해시로만
  변주를 만듭니다. 보관함에서 다시 열었을 때 내용이 바뀌면 안 되기 때문입니다.

## 아직 안 된 것

- 백엔드가 없습니다. 로그인은 인증 없이 흉내만 내고, 저장·개인화 결과는 브라우저(localStorage)에만 남습니다.
- 실제 데이터 수집 파이프라인(F00)은 없습니다. 데이터 소스 자체가 PRD 10절 TBD 상태입니다.
- Pretendard 폰트는 CDN에서 받아옵니다. 인터넷이 없으면 시스템 기본 폰트로 표시됩니다.
