# 새 디자인 HTML 을 받았을 때

팀원이 피그마에서 뽑은 새 `v1-trend-incubator.html` 을 주면 이 순서대로 한다.
V1.3 때는 이 절차가 없어서 백엔드 연동을 통째로 손으로 다시 이식해야 했다.

**소요: 10분 내외.** 마지막 6번만 사람이 판단해야 하고 나머지는 기계적이다.

---

## 왜 이렇게 되어 있나

디자인 HTML 의 `<script>` 블록은 **하나뿐이고 클래식 스크립트**다(모듈도, IIFE 도 아님).
그래서 두 가지가 가능하다:

| | 이유 |
|---|---|
| `window.foo = 내함수` 로 디자인 함수를 갈아끼울 수 있다 | 최상위 `function foo(){}` 는 `window` 의 **쓰기 가능한** 속성이 된다. `onclick="foo()"` 속성까지 전부 새 함수를 탄다 |
| `savedIdeas` 같은 전역을 맨이름으로 읽고 쓸 수 있다 | 최상위 `let`/`const` 는 전역 렉시컬 환경에 들어가고 **클래식 스크립트끼리 공유**한다 |

`eureka-app.js` 는 이 두 성질에만 의존한다. **디자인 script 블록은 한 글자도 안 고친다.**
이게 성립하지 않으면(모듈이거나 IIFE 로 감싸져 있으면) 전략 자체를 다시 짜야 한다 — 2번에서 거른다.

---

## 절차

### 1. 덮어쓰고, 먼저 **디자인만** 도는지 본다

```bash
cp ~/Downloads/새파일.html Final/Frontend/v1-trend-incubator.html
```

서버를 재시작하고 <http://localhost:8000/> 을 연다.
아직 연동 script 두 줄이 없으니 **디자인 자체의 목업 흐름**이 도는지만 본다.
여기서 안 되면 연동 문제가 아니라 디자인 파일 문제다 — 팀원에게 돌려보낸다.

### 2. ⚠️ 이 전략이 아직 성립하는지 확인 — **여기서 걸리면 멈춘다**

```bash
grep -n '<script' Final/Frontend/v1-trend-incubator.html
```

확인할 것:

- `<script>` 가 **하나**이고 `type="module"` 이 **없어야** 한다
- 그 블록이 `(function(){` 나 `(()=>{` 로 시작하지 **않아야** 한다

```bash
# 블록 시작 줄 번호를 얻어 그 다음 몇 줄을 본다
sed -n "$(grep -n '<script>' Final/Frontend/v1-trend-incubator.html | head -1 | cut -d: -f1),+4p" \
  Final/Frontend/v1-trend-incubator.html
```

**둘 중 하나라도 걸리면 3번 이후로 가지 말고 상의할 것.** 덮어쓰기가 조용히 안 먹는다.

### 3. `<head>` 에 두 줄 추가

`</head>` 바로 앞(보통 `</style>` 다음):

```html
<script defer src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.116.0/dist/umd/supabase.js" crossorigin="anonymous"></script>
<script defer src="/eureka-app.js"></script>
```

- **버전을 `@2` 로 바꾸지 마라.** 어느 날 조용히 올라가서 깨진다.
- **`type="module"` 로 바꾸지 마라.** 위의 "왜 이렇게 되어 있나" 참고.
- Supabase SDK 가 필요 없는 단계라도 두 줄 다 넣어두면 된다(전역 이름은 `supabase`).

### 4. 계약 식별자가 남아 있는지 확인

`eureka-app.js` 가 **부팅할 때 스스로 확인하고 콘솔에 경고를 찍는다.** 브라우저 콘솔을 열고:

```
[eureka] 통합 계약 누락 3건 — ...
[eureka]   없는 함수(덮어쓸 대상): toggleSaveIdea
```

이런 게 안 뜨면 통과다. `?debug=1` 을 붙이면 성공 시에도 로그가 찍히고,
누락이 있으면 화면 하단에 빨간 배너가 뜬다.

```
http://localhost:8000/?debug=1
```

콘솔에서 상태를 직접 볼 수도 있다:

```js
EUREKA.describe()
// { version: "...", served: true, contractOk: true, tabsHooked: true, hooks: 1 }
```

터미널에서 미리 세어보고 싶으면:

```bash
cd Final/Frontend
for n in savedKeywords savedIdeas configSettings selectedKeyword generatedIdeas isGenerating PERIOD_KEY; do
  printf "%-18s %s\n" "$n" "$(grep -cE "^\s*(let|const|var) $n\b" v1-trend-incubator.html)"
done
for n in toggleSaveKeyword toggleSaveIdea removeSavedKeyword removeSavedIdea \
         syncSavedIdea updateSavedCounts executeIdeaGeneration \
         renderIdeasTabs renderSavedScreen showIdeaDetail showToast navigateTo esc aiToolsFor; do
  printf "%-24s %s\n" "$n" "$(grep -cE "^\s*(async )?function $n\b" v1-trend-incubator.html)"
done
```

전부 `1` 이어야 한다. `0` 이면 이름이 바뀐 것이니 `eureka-app.js` 의 `CONTRACT` 를 고친다.

### 5. DOM id 확인

```bash
for i in ideas-tabs-container result-main-screen active-idea-card-container toast-popup; do
  printf "%-32s %s\n" "$i" "$(grep -c "id=\"$i\"" Final/Frontend/v1-trend-incubator.html)"
done
```

바뀌었으면 `eureka-app.js` 의 `SELECTORS` 를 고친다.

### 6. 🖐 손으로 다시 넣어야 하는 것

**여기만 사람이 한다.** 마크업과 섞여 있어 분리할 수 없는 부분이다.
디자인 파일이 새로 오면 아래는 매번 사라지므로 직접 다시 적용한다.

| 위치 | 넣을 것 | 왜 분리 못 하나 |
|---|---|---|
| `showIdeaDetail()` | 추천 AI pill → `aiToolsFor(idea)` | 카드 마크업 안에 박힌 템플릿 |
| `showIdeaDetail()` | 프롬프트 박스 제목 → `${esc(idea.shortName \|\| idea.name)} 개발 프롬프트` | 〃 |
| `renderSavedScreen()` | 추천 AI pill → `aiToolsFor(item)` · 제목 → `${esc(item.shortName \|\| item.name)} 개발 프롬프트` | 보관함 카드 마크업 |
| `toggleSaveIdea()` | 저장 객체에 `period` · `periodKey` 추가 | 저장 로직이 렌더 호출과 붙어 있음 |
| `toIdeaView()` / `toIdeaSpec()` | `aiToolsByPeriod` · `periodKey` 매핑 | 디자인이 자체 목업용으로 다시 쓸 수 있음 |
| `aiToolsFor()` + `AI_TOOL_TOOLS_BY_PERIOD_FALLBACK` | 함수 자체가 사라졌으면 다시 넣기 | 오프라인 폴백용 상수 |

> 작업 전 이전 버전에서 그대로 떠올 수 있다:
> `git show HEAD:Final/Frontend/v1-trend-incubator.html > /tmp/이전.html`
> 후 `diff` 로 비교하면 뭘 넣어야 하는지 바로 보인다.

### 7. 연기 테스트

- [ ] 키워드 선택 → 설정 → 아이디어 생성 (서버 응답이 오는지)
- [ ] 기간 칩 하루/일주일/한 달 → **추천 AI** pill 이 4개/2개/2개로 바뀌는지
- [ ] 아이디어 탭 전환 → 프롬프트 제목이 그 아이디어 이름으로 바뀌는지
- [ ] MVP 수정 → 저장 → [프롬프트 재생성하기] 버튼이 나타나는지
- [ ] 아이디어 저장 → 보관함에서 펼쳤을 때 저장 당시 기간의 AI 목록이 나오는지
- [ ] 서버를 내리고 새로고침 → 폴백 아이디어 3개가 뜨는지
- [ ] 콘솔에 `[eureka] 통합 계약 누락` 이 없는지

*(로그인·보관함 서버 저장·새로고침 제한이 붙은 뒤에는 그 항목도 여기 추가된다)*

---

## 파일 나눔 기준

| 어디에 | 무엇이 | 규칙 |
|---|---|---|
| `eureka-app.js` | 마크업 문자열이 **없는** 순수 로직 | 새 디자인이 와도 그대로 산다 |
| `v1-trend-incubator.html` | 화면을 그리는 모든 것 + CSS | 디자이너 소유. 매번 새로 온다 |

새 로직을 추가할 때 **HTML 안에 쓰고 싶어지면 한 번 멈추고** 생각할 것 —
마크업이 꼭 필요한 게 아니라면 `eureka-app.js` 로 간다. 그게 이 구조의 전부다.
