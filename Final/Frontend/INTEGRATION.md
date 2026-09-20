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
for n in savedKeywords savedIdeas configSettings selectedKeyword generatedIdeas; do
  printf "%-18s %s\n" "$n" "$(grep -cE "^\s*(let|const|var) $n\b" v1-trend-incubator.html)"
done
for n in toggleSaveKeyword toggleSaveIdea removeSavedKeyword removeSavedIdea \
         updateSavedCounts executeIdeaGeneration handleFigmaLogin handleFigmaSignup \
         renderIdeasTabs renderSavedScreen showToast navigateTo \
         findKeywordById renderBestKeywordsGrid renderWeeklySlider; do
  printf "%-24s %s\n" "$n" "$(grep -cE "^\s*(async )?function $n\b" v1-trend-incubator.html)"
done
```

위 목록(`CONTRACT.globals`/`overrides`/`uses`)은 `eureka-app.js`가 필수로 요구하는 것만 담았다.
전부 `1` 이어야 한다. `0` 이면 이름이 바뀐 것이니 `eureka-app.js` 의 `CONTRACT` 를 고친다.

`finishIdeaGeneration`(오프라인 폴백)은 `CONTRACT.optionalUses`에 있다 — 없어도 부팅 계약
점검에서 경고가 안 뜬다(`executeIdeaGeneration`의 catch 경로가 `typeof === 'function'`으로
조용히 건너뛴다). 디자인이 자체 오프라인 목업 생성기(`finishIdeaGeneration` 같은)를 갖고
있으면 서버 실패 시 폴백으로 재사용되니 이름이 다르면 `eureka-app.js`의 `executeIdeaGeneration`
안 `window.finishIdeaGeneration` 호출부를 맞춰 고친다.

(MVP 핵심기능 수정 기능은 2026-09-20에 제거했다 — `syncSavedIdea` 오버라이드와 `PATCH
/api/library/ideas/{idea_key}` 동기화 경로는 그 기능 전용이었다. 이후 저장된 아이디어를
편집하는 기능이 다시 생기면 그때 다시 만든다.)

⚠️ **디자인이 자체 아이디어 필드 이름을 쓰면(`mvpFeatures`처럼) 백엔드 응답
(`app/schemas/idea_models.py`의 스네이크케이스 `mvp_features` 등)과 안 맞을 수 있다.**
`eureka-app.js`의 `mapBackendIdea()`가 그 변환을 전담한다 — 디자인이 카드에서 쓰는 필드 이름이
바뀌었으면(예: `idea.mvpFeatures` → `idea.features`) 이 함수의 반환 객체 키를 그에 맞게 고친다.
이 변환은 순수 로직이라 디자인 script는 안 건드린다.

⚠️ **디자인이 자체 로그인/회원가입 화면(`view-login`/`view-signup`류)과 그걸 처리하는
제출 핸들러(`handleFigmaLogin`/`handleFigmaSignup`)를 갖고 있을 수 있다** — Supabase와
무관하게 `localStorage`만 건드리는 순수 목업인 경우, 그대로 두면 사용자가 그 화면에서
"로그인"해도 실제 세션이 안 생겨 보관함·새로고침이 조용히 계속 깨진 채로 남는다.

2026-09-20에 처음엔 `navigateTo`를 감싸 `'login'`/`'signup'`을 우리가 직접 만든 모달로
가로채는 방식을 썼는데, **"화면이 팀원이 만든 화면이 아니다"라는 피드백을 받고 되돌렸다** —
사용자 입장에선 당연히 이상해 보인다(디자인이 다른 화면으로 바뀌었으니까). 그래서
지금은 화면은 디자인 것 그대로 두고, `eureka-app.js`의 `installLoginOverrides()`가
`handleFigmaLogin`/`handleFigmaSignup` 자체를 실제 `window.sb.auth.signInWithPassword`/
`signUp` 호출로 갈아끼운다(`toggleSaveIdea`를 덮어쓰는 것과 같은 패턴 — 마크업은 안
건드리고 제출 핸들러만 바꾼다). `installLogoutOverride()`/`syncDesignAuthFlag()`가
디자인의 로그아웃 링크와 GNB 로그인/마이페이지 버튼 표시를 실제 인증 상태와 맞춘다.
**우리가 따로 헤더 칩이나 모달을 주입하지 않는다** — 디자인 자신의 GNB 버튼과
로그인/회원가입 화면이 유일한 진입점이다.

다음 디자인의 로그인/회원가입 제출 함수 이름이 다르면 `installLoginOverrides()` 안의
`window.handleFigmaLogin`/`window.handleFigmaSignup` 참조와 `CONTRACT.overrides`를 그
이름으로 맞춰 고친다. **디자인에 자체 로그인 화면이 아예 없으면**(원래 가정했던 경우)
`installLoginOverrides()`는 `typeof === 'function'` 검사에서 조용히 아무것도 못 찾고
넘어간다 — 이 경우엔 로그인 진입점 자체가 없다는 뜻이니, 그때 가서 최소한의 모달을 다시
만든다(지금 없는 디자인을 미리 대비해 두지 않는다).

### 5. DOM id 확인

```bash
for i in ideas-tabs-container result-main-screen active-idea-card-container toast-popup; do
  printf "%-32s %s\n" "$i" "$(grep -c "id=\"$i\"" Final/Frontend/v1-trend-incubator.html)"
done
```

바뀌었으면 `eureka-app.js` 의 `SELECTORS` 를 고친다.

### 6. 🖐 사람이 확인·판단해야 하는 것

디자인마다 4번(계약 점검) 결과가 다르게 나온다 — 어떤 디자인은 이전 디자인이 갖고
있던 헬퍼(`esc`, `aiToolsFor`, `toIdeaView` 같은)를 그대로 이어받고, 어떤 디자인은
(2026-09-20 `new1.3.html`이 그랬듯) 훨씬 이른 단계로 되돌아가 그런 헬퍼가 아예 없다.
**후자라도 당황할 것 없다** — 그런 매핑은 마크업과 무관한 순수 로직이니 디자인을 안
건드리고 `eureka-app.js` 안에서 자체적으로 처리하면 된다(`mapBackendIdea()`가 예시).
아래는 실제로 마크업과 섞여 분리가 안 돼서 사람이 확인해야 하는 항목들이다:

| 확인할 것 | 이번(2026-09-20 `new1.3.html`)엔 어땠나 | 다음에 다르면 |
|---|---|---|
| 추천 AI pill이 기간별(하루/일주일/한달)로 다른가 | 디자인 자체 `getRecommendedAiList()`가 이미 백엔드 `AI_TOOL_BY_PERIOD`와 동일한 기간별 고정 목록을 그림 — 손댈 것 없었음 | 카드 마크업 안에서 `getRecommendedAiList` 호출부를 찾아 백엔드 `ai_tools_by_period` 값을 쓰도록 바꿔야 할 수 있다 |
| 프롬프트 박스 제목이 선택한 아이디어 이름을 따라가는가 | 디자인이 이미 `${idea.name} 개발 프롬프트`로 그림 — 손댈 것 없었음 | 제목이 고정 문구면 `showIdeaDetail()`/`renderSavedScreen()` 템플릿에서 직접 고쳐야 한다 |
| `toggleSaveIdea()`가 저장 객체에 기간을 남기는가 | 안 남겨서(`...idea`만 폄) `eureka-app.js`의 override 안에서 `newEntry.period`/`periodKey`를 직접 채워 넣음(디자인 안 건드림) | 이미 남긴다면 그 필드 이름을 확인해 `eureka-app.js`의 `EUREKA_PERIOD_KEY` 매핑·`rowToIdeaItem()`과 맞춘다 |
| 아이디어 카드가 기대하는 필드 이름 | `mvpFeatures`(카멜) — 백엔드는 `mvp_features`(스네이크) | `mapBackendIdea()`의 반환 객체 키를 디자인이 실제로 읽는 이름에 맞춘다 |
| 디자인 자체 로그인 UI가 있는가 | 있었음(`view-login`/`view-signup`, `handleFigmaLogin`/`handleFigmaSignup`, Supabase 무관 로컬 목업) — 화면은 그대로 두고 `installLoginOverrides()`가 제출 핸들러만 실제 Supabase 호출로 갈아끼움(디자인 안 건드림) | 함수 이름이 다르면 `installLoginOverrides()`와 `CONTRACT.overrides`를 맞춘다. 자체 로그인 화면이 아예 없으면 그때 최소 모달을 다시 만든다 |
| 새로고침 버튼이 카드를 가리지 않는가 | `mountRefreshButton()`이 `#ideas-tabs-container`(카드 grid) 자신이 아니라 그 바깥 padded 박스(`.figma-result-tabs-box`)에 얹혀서 안 가림 | grid 바깥에 padding 있는 wrapper가 없으면 카드를 가릴 수 있다 — `mountRefreshButton()`의 `closest('.figma-result-tabs-box')` 선택자를 그 디자인의 wrapper 클래스로 바꾼다 |
| "추천 AI" 로고 이미지가 실제로 뜨는가 | 디자인이 `목욕중/*.png` 상대경로를 참조 — `Final/Backend/main.py`가 `Final/Frontend/목욕중/`을 `/목욕중`에 정적 마운트한다. 파일이 없으면 `onerror`로 조용히 숨겨져 "로고가 비어있다"처럼 보인다 | 이미지 폴더 이름/경로가 바뀌면 `main.py`의 `_ASSETS_DIR` 마운트 경로를 맞춘다 |

> 작업 전 이전 버전에서 그대로 떠올 수 있다:
> `git show HEAD:Final/Frontend/v1-trend-incubator.html > /tmp/이전.html`
> 후 `diff` 로 비교하면 뭐가 새로 생기거나 사라졌는지 바로 보인다.

### 7. 연기 테스트

- [ ] 키워드 선택 → 설정 → 아이디어 생성 (서버 응답이 오는지)
- [ ] 기간 칩 하루/일주일/한 달 → **추천 AI** pill 이 4개/2개/2개로 바뀌는지
- [ ] 아이디어 탭 전환 → 프롬프트 제목이 그 아이디어 이름으로 바뀌는지
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
