# 아이디어 상세 — IA · 바이브코딩 프롬프트 사양

**담당: 박민규** · 대상 파일: `Final/Frontend/v1-trend-incubator.html` · 관련: [PIVOT.md](PIVOT.md)

아이디어 상세 화면(결과 화면 우측 패널)에서 박민규가 맡은 두 블록의 데이터 소스와 렌더 규칙을 고정한다. **이 문서에 나열된 필드·클래스명이 바뀌면 이 문서도 같이 고친다.**

## 0. 한 장 요약

| 블록 | 함수 | 입력 | 성격 |
|---|---|---|---|
| 서비스 정보구조도 (IA) | ~~`renderIAFlow(idea.ia, idea.shortName)`~~ (화면 렌더 없음 — 2026-09 개편으로 폐기) | `idea.ia` | **프롬프트 내부 전용.** 화면에는 안 뜨지만 `idea.ia`는 삭제되지 않았고 아래 3절 프롬프트가 계속 소비한다 |
| 바이브코딩 프롬프트 | `buildPromptForPeriod(idea, ctx, period)` (프론트) / `build_period_prompt()` (백엔드, 1:1 이식) | `idea.*` 전체 + `configSettings` | LLM에 그대로 붙여넣는 완성 텍스트 |
| MVP 편집 · 재생성 | `renderMvpSection()` / `POST /api/trends/{id}/ideas/prompt` | 사용자가 고친 `idea.mvpFeatures` | 5절 참고 |

이제 `generatedIdeas`는 실제 백엔드 아이디어 생성 에이전트(`app/agents/idea_agent.py`)의 출력이다(2026-09-15, 커밋 `0e681dc5`) — "현재는 하드코딩 목업"이라는 예전 서술은 낡았다. 다만 서버 미기동·`file://`로 열었을 때의 오프라인 폴백은 여전히 프론트 내장 목업(`buildFallbackIdeaDrafts`)을 쓴다.

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

## 2. (폐기) IA 화면 렌더 — `renderIAFlow`

> **2026-09-15 개편으로 아이디어 상세 화면에서 IA 블록을 제거했다.** `idea.ia`는
> 삭제된 것이 아니라 **프롬프트 전용 내부 데이터로 남는다** — 프론트
> `formatIAOutline()` / 백엔드 `_format_ia_outline()`이 계속 소비해서
> 프롬프트 본문의 "# 2. 시스템 아키텍처 및 서비스 정보구조(IA)" 절을 채운다
> (3절 참고). 아래 DOM·CSS 명세는 이력 보존용이며, 현재 코드에 `.ia-flow-grid`
> 등 해당 요소는 전혀 없다(`renderIAFlow()` 함수 자체도 삭제됨).

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

## 4. UI — 기간 표시

> 이 절은 낡았다. 실제 코드에는 `activePromptTab`/`switchPromptTab`/탭 3개
> UI가 없다 — 커밋 `aaff7b75`("가로형 IA · 기간별 단일 프롬프트")가 탭
> 방식을 걷어내고, 설정 화면에서 고른 기간(`configSettings.period`) 하나만
> `.figma-prompt-period-tag`로 표시하는 방식으로 이미 바뀌었다(문서 미반영
> 상태로 남아 있었음). 응답에는 `prompts.day`/`week`/`month`가 전부 담기지만
> 화면에는 그중 현재 선택된 기간 하나만 보여준다.

## 5. MVP 편집 · 프롬프트 재생성

2026-09-16 개편(가장 최근). "MVP 핵심 기능" 섹션 제목 옆에 [수정] 버튼을 추가해
사용자가 항목을 직접 고칠 수 있게 했고, IA 화면 블록을 없애면서 생긴 자리에
프롬프트가 바로 오도록 했다.

**편집 상태 모델** (`v1-trend-incubator.html`):
- `mvpEditState = { index, draft: string[] } | null` — 편집 중인 아이디어의
  임시 값. `showIdeaDetail()`이 카드를 `innerHTML`로 통째로 다시 그리는
  구조라, 입력값의 원본을 DOM이 아니라 이 전역에 둔다(재렌더돼도 안전).
- `idea.promptStale` — MVP를 고쳤지만 프롬프트는 아직 재생성 전이라는 표시.
  섹션 제목 옆과 프롬프트 헤더 양쪽에 배지로 뜬다.

**개수 규칙이 백엔드 생성 규칙(3~5개)과 다른 이유**: `app/ideas/validate.py`의
3~5개 강제는 *LLM 출력 품질 가드*다. 사람이 일부러 고친 값에 같은 규칙을
걸면 "화면엔 이미 떠 있는데 저장이 안 되는" 모순이 생긴다. 그래서 편집
UI는 1~8개만 허용하고, 3~5 범위를 벗어나면 차단 대신 힌트 문구만 보여준다.

**`POST /api/trends/{keyword_id}/ideas/prompt`** — 프롬프트만 재조립한다
(`Final/Backend/app/api/idea_routes.py`). `IdeaSpec`을 요청 바디로 그대로
재사용하고, `build_period_prompt()`를 다시 호출할 뿐 **LLM을 부르지 않는다**
(순수 문자열 조립이라 비용이 0). `idea.ia`는 편집 대상이 아니지만 요청에
그대로 실려가야 한다 — 빠지면 프롬프트의 "# 2" 섹션이 비어버린다
(`toIdeaSpec()`이 이 값을 채운다). **서버 캐시(`data/ideas/`)는 갱신하지
않는다** — 캐시는 "LLM이 만든 원본"을 보관하는 자리이고, 여기서 만드는 건
사용자의 개인 편집본이라 섞으면 같은 조합을 연 다른 사람이 남의 편집을
받게 된다.

프론트 호출도 서버 우선 + 오프라인 폴백이다. 서버가 안 되면(`file://`로
열었을 때 등) `buildPromptForPeriod()`로 그대로 로컬 조립한다 — 아이디어
생성 자체의 폴백 패턴(`executeIdeaGeneration()`)과 동일.

## 6. 보관함 저장 형식

```ts
savedIdeas[i] = { name, slogan, keyword, mvpFeatures: string[], prompt, duration, date }
```

`mvpFeatures`는 2026-09-16에 추가됐다. **하위 호환**: 그 이전에 저장된
localStorage 항목에는 `mvpFeatures`가 없다 — 보관함 카드 렌더는
`Array.isArray(item.mvpFeatures) && item.mvpFeatures.length`로 가드하고,
없으면 MVP 요약 없이 이름·슬로건만 보여준다.

아이디어를 편집·재생성한 뒤에는 `syncSavedIdea(idea)`가 같은 name으로
매칭되는 보관함 항목을 제자리에서 갱신한다 — 저장 후 편집하면 보관함에
옛날 MVP·옛날 프롬프트가 남는 문제를 막는다. 보관함에 아직 없는
아이디어를 편집만 해서는 저장되지 않는다(별표를 눌러야 저장된다).

> `prompts`(3종 dict) 형식과 `getSavedPrompts()`/`switchSavedPromptTab`
> 언급은 4절과 같은 이유로 낡았다 — 현재 코드는 단일 `prompt` 필드만
> 저장한다.

## 7. 검증 방법

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
