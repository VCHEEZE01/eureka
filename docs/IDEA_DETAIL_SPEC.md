# 아이디어 상세 — IA · 바이브코딩 프롬프트 사양

**담당: 박민규** · 대상 파일: `Final/Frontend/v1-trend-incubator.html` · 관련: [PIVOT.md](PIVOT.md)

아이디어 상세 화면(결과 화면 우측 패널)에서 박민규가 맡은 두 블록의 데이터 소스와 렌더 규칙을 고정한다. **이 문서에 나열된 필드·클래스명이 바뀌면 이 문서도 같이 고친다.**

## 0. 한 장 요약

| 블록 | 함수 | 입력 | 성격 |
|---|---|---|---|
| 서비스 정보구조도 (IA) | `renderIAFlow(idea.ia, idea.shortName)` | `idea.ia` (목업 고정값) | 화면 구조 명세 — 좌→우 계층 |
| 바이브코딩 프롬프트 3종 | `buildPrompts(idea, ctx)` | `idea.*` 전체 + `configSettings` | LLM에 그대로 붙여넣는 완성 텍스트 |

현재는 `generatedIdeas`가 하드코딩된 목업이다. 실제 아이디어 생성 LLM이 붙으면, 그 출력이 아래 `idea.*` 스키마를 그대로 채워야 이 두 블록이 수정 없이 동작한다.

## 1. `idea.ia` 스키마

```ts
idea.ia: Array<{
  depth1: string;               // 1Depth 화면/섹션명
  depth2: Array<{
    title: string;               // 2Depth 기능명
    desc: string;                // 2Depth 설명 (한 줄)
  }>;
}>
```

**가변 규칙**: `depth1` 개수, 각 `depth2` 개수 모두 자유롭게 늘거나 준다. 렌더러와 프롬프트 생성기 어느 쪽도 개수를 하드코딩하지 않는다 — `.map()`으로 순회한다. 현재 5개 아이디어 전부 `depth1` 3개 · 각 `depth2` 2개로 맞춰져 있지만 이는 데이터의 우연한 형태지 강제 규칙이 아니다.

## 2. IA 렌더 — `renderIAFlow`

**형태: 좌(서비스) → 우(2Depth) 가로 플로우.** 세로 카드 3장이 나란히 있던 이전 버전(`grid-template-columns: repeat(3,1fr)`)은 계층이 안 보인다는 문제가 있어 폐기했다.

### DOM 구조 (중첩 flex, grid-row 계산 없음)

```
.ia-flow-grid (flex row)
├─ .ia-node.ia-depth0                    ← 서비스명, 전체 높이 stretch
└─ .ia-groups (flex column)
   └─ .ia-group (flex row) × depth1 개수
      ├─ .ia-node.ia-depth1              ← 자기 depth2 그룹과 높이 stretch
      └─ .ia-depth2-col (flex column)
         └─ .ia-node.ia-depth2 × depth2 개수
```

depth1 카드의 높이가 자기 depth2 자식들 높이에 자동으로 맞춰지는 이유는 `.ia-group`이 `align-items: stretch`이기 때문이다 — grid-row 범위를 수동 계산하지 않는다. **이 구조를 유지해야 개수가 바뀌어도 안 무너진다.**

### 커넥터 선

`.has-children`(오른쪽 끝 세로 트렁크) / `.has-parent`(왼쪽 끝 가로 스텁)를 CSS `::before`/`::after`로 그린다. 트렁크는 `right:-14px`, 스텁은 `left:-14px` — 두 값이 만나려면 **column-gap이 반드시 28px**이어야 한다(`.ia-flow-grid`·`.ia-group` 둘 다). gap을 바꾸면 오프셋도 같이 바꾼다.

### 모바일 폴백 (`max-width: 900px`)

`.ia-flow-grid`·`.ia-group`·`.ia-groups`·`.ia-depth2-col`을 전부 `flex-direction: column`으로 바꾸고 커넥터를 숨긴다. DOM 순서가 이미 depth0 → (depth1 → 그 depth2들) 순서라서 폴백 시에도 계층이 그대로 읽힌다 — 순서를 depth1 전부 나열 후 depth2 전부 나열하는 식으로 바꾸면 이 폴백이 깨진다.

## 3. 바이브코딩 프롬프트 3종 — `buildPrompts(idea, ctx)`

설정 화면의 `구현 난이도`(초급·중급·도전)를 없애고 **`작업 기간`**(1일·일주일·한달)으로 통합했다. 난이도와 기간이 사실상 같은 축이라 함께 두면 "초급+한달" 같은 모순 조합이 생겼기 때문이다.

### 입력

```ts
buildPrompts(idea: {
  shortName, slogan, target, problem, solution, diff,
  mvpFeatures: string[], futureFeatures: string[], stack, architecture,
  ia: (위 1절 스키마)
}, ctx: { keyword, platform, type, ai })
→ { '1일': string, '일주일': string, '한달': string }
```

### 핵심 — `idea.ia`를 실제 화면 구조로 주입한다

이전 버전의 결함: `generateVibePrompt()`가 "주요 페이지 1) 메인 랜딩 2) 핵심 기능 3) 결과 요약 4) 보관함"을 **하드코딩**해서, 5개 아이디어가 전부 똑같은 페이지 구성을 프롬프트에 받았다. `formatIAOutline(idea.ia)`가 그 아이디어의 실제 IA를 텍스트 개요로 펼쳐 `# 2. 시스템 아키텍처 및 서비스 정보구조(IA)` 섹션에 그대로 넣는다. **이 지점을 다시 하드코딩하면 회귀다.**

### 기간별 차이 — 일정이 아니라 완성도·요구 스킬

**세 프롬프트는 하나의 프로젝트가 시간을 두고 진행되는 단계가 아니다.** 예전 `구현 난이도`(초급·중급·도전)를 그대로 기간 이름으로 바꿔 부른 것뿐이고, 각각 독립된 완성본이다. 그래서 "Day 1~5 로드맵", "1주차~4주차 마일스톤"처럼 시간 진행을 서술하는 문구는 넣지 않는다 — 그건 세 프롬프트를 한 프로젝트의 체크포인트처럼 보이게 만들어, 사용자가 실제로 원하는 "완성도·난이도 선택"이라는 의미를 흐린다.

| | 1일 | 일주일 | 한달 |
|---|---|---|---|
| AI 행동 | 질문 없이 즉시 전체 코드 | **먼저 질문 → 답 받고 착수** | 아키텍처 설계 → 검토 후 구현 |
| IA 반영 범위 | 1Depth 핵심 1~2개만 | 1·2Depth 전체 | 1·2Depth 전체 + `futureFeatures` |
| 데이터 | 인라인 목업 + localStorage | 경량 BaaS, 실제 저장·조회 | DB 스키마·인증·배포·테스트 |
| 요구 스킬 | 프롬프트 그대로 실행만 하면 됨 | BaaS 연동 이해 | 프론트·백엔드·배포 전반 |

일주일 프롬프트가 AI에게 **먼저 되묻게** 만드는 것은 유지한다(타깃 사용 맥락 / 우선 화면 / 데이터 출처 / 디자인 톤) — 사용자가 답하면서 아이디어가 자기 상황에 맞게 구체화되는 게 이 등급의 가치이기 때문이다. 이 질문 유도 문구를 지우면 1일 프롬프트와 차별점이 없어진다. 하지만 질문 이후의 구현 지시는 "Day 단위 진행"이 아니라 "이 완성도로 만들어라"는 스펙으로 준다.

## 4. UI — 프롬프트 탭

`activePromptTab`(모듈 전역, 기본값 = 설정 화면에서 고른 기간)으로 표시 중인 프롬프트를 추적한다. `switchPromptTab(index, duration)`이 값을 바꾸고 `showIdeaDetail(index)`를 다시 그린다. 복사 버튼(`copyPromptToClipboard`)은 항상 `idea.prompts[activePromptTab]`을 복사한다 — 탭과 복사 내용이 어긋나면 버그다.

## 5. 보관함 저장 형식

```ts
savedIdeas[i] = { name, slogan, keyword, prompts: {…3종…}, duration, date }
```

**하위 호환**: 피보팅 전 형식(`{ prompt: string }`, `prompts` 없음)이 localStorage에 남아 있을 수 있다. `getSavedPrompts(item)`이 `item.prompts ?? (item.prompt ? {'1일': item.prompt} : {})`로 흡수한다 — 보관함 렌더·복사 로직 어디서든 `item.prompt`를 직접 읽지 말고 반드시 `getSavedPrompts()`를 거친다. 기간 탭은 `.saved-entry-card`마다 `savedPromptTabs[i]`로 독립적으로 추적된다.

## 6. 검증 방법

`Final/Frontend/v1-trend-incubator.html`은 서버 없이 더블클릭으로 열리는 단일 HTML이다(팀의 "서버 없이 열리는 단일 HTML 유지" 제약). Playwright로 headless 검증한 항목:

- 설정 화면 `작업 기간` 3칩 존재, `구현 난이도` 그룹 부재
- 기간 선택 → 결과 화면 프롬프트 탭이 그 기간으로 활성화
- 5개 아이디어 전부 depth0/1/2 노드 수와 커넥터 클래스(`has-children`/`has-parent`) 일치
- 탭 3개의 프롬프트 본문 길이가 서로 다르고, 각각 그 아이디어의 실제 `depth1` 이름을 포함 (하드코딩 회귀 방지)
- 복사 버튼이 활성 탭 내용과 정확히 일치하는 텍스트를 클립보드에 씀
- 아이디어 저장 → 보관함에 기간 탭 3개 노출
- 레거시(`prompt`만 있는) localStorage 항목 삽입 후에도 보관함이 깨지지 않고 렌더됨
- 뷰포트 900px 이하에서 `.ia-flow-grid`가 `flex-direction: column`으로 전환

콘솔 에러 0건 확인.

## 범위 밖

- 키워드 상세 화면(검색 볼륨·차트·연관어) — 이미 구현돼 있고 이 문서의 대상 아님
- 아이디어 5개 생성 로직 자체(현재 하드코딩 목업) — 실제 LLM 연동은 별도 작업. 연동 시 출력이 위 1절 `idea.ia` 스키마를 지켜야 한다. IA·프롬프트 3종 생성 규칙을 아이디어 생성 담당자에게 넘기는 문서는 [IDEA_GENERATION_HANDOFF.md](IDEA_GENERATION_HANDOFF.md)
- 백엔드 연동(`Final/Backend/`) — 이번 작업은 프로토타입 HTML 범위만
