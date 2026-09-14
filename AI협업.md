> 2026-09-14 수집량·노출 개선: 검색 120회×20건·판별 2,400건, 표현 없는 상황 탐색, 진행 중 불편 전체 보기, JSON 형식 재생성 1회. Backend 615 / Frontend 34 테스트 통과. 새 상한의 실제 전체 API 실행은 미실행. 최신 상세: docs/PRODUCTION_COLLECTION_RUNBOOK.md

# AI협업.md — Codex 인계 문서

> **2026-09-13 타겟 수집 변경:** 사용자는 온보딩 나이대·성별·직업·장소에 맞게 수집하도록 변경했다. 이전의 “사용자 클릭은 수집하지 않음/전체 문제 풀만 조회”는 이 경로에 적용하지 않는다. 기준 공유용 디자인을 사용하고, 변경 사항은 `docs/eureka-agent-guide.html`과 바탕화면 `유레카_에이전트_설계지도.html`에 동기화한다. 구현·검증 최신 기록은 `docs/TARGET_COLLECTION_RUNBOOK.md`를 따른다.

> **웹 열기 기준 (2026-09-13 사용자 재확인):** 사용자는 기존 React/Next 화면을 사용하지 않기로 했다. “유레카 웹 열어줘” 요청에는 `reference-pages/` 기반 공유용 HTML을 연다. 현재 타겟 수집 웹은 백엔드 `http://localhost:8000`이 제공하는 `Final/Frontend/eureka-공유용.html` live 모드다. `Final/Backend/data/problem-preview/eureka-problem-review.html`은 과거 고정 검토 표본으로만 사용한다. Next 서버(`localhost:3000`)를 기본 서비스 화면으로 열지 않는다.


> **2026-09-13 후속 갱신:** 아래 본문은 이전 인계 기록이다. 현재는 Gemini 연결과 ③ 문제정의 생성·검수, JSON 저장·목록/상세 API, 기준 HTML 실제 데이터·검토 보고서 및 React API 연결을 구현했다. 아이디어·조합·개인화는 잠금이다. 공개 저장에는 게시 기준·AI 검수·명시적 사람 승인 기록이 필요하다. 실제 생성 자료는 1건의 검토 보류 예시이며 공개 문제는 0개다. 최신 상태는 `Final/Backend/PROGRESS.md`, 실행법은 `docs/PROBLEM_DETAIL_RUNBOOK.md`, 시각화는 `docs/eureka-agent-guide.html`을 읽는다. 기존 본문의 ‘③ 스텁·API 키 공란’은 현재 상태가 아니다.

**작성**: Claude (Opus 5) · 2026-09-12 · 브랜치 `박민규` · 커밋 안 됨(전부 워킹 트리 변경)
**받는 사람**: Codex — 이 문서 하나로 이어서 작업할 수 있게 썼다. 다른 문서를 먼저 찾아 읽을 필요 없다.

---

## 0. 이 문서를 읽는 법

1. **1절(핵심 원칙)을 가장 먼저 읽어라.** 이 프로젝트의 모든 설계가 여기서 나온다. 어기면 기존 테스트(`test_no_numbers.py`)가 실패한다.
2. **2절(지금 상태)**로 뭐가 이미 되어 있는지 확인해라. 다시 만들지 마라.
3. **3절(바로 할 일)**이 진짜 다음 작업이다 — 사람이 직접 코드를 대조해서 찾은 미완성 항목 2개다.
4. 그 외 배경·세부 규칙이 필요하면 4절 이후를 참고해라.

---

## 1. 핵심 원칙 (절대 위반 금지)

프로젝트 이름 "유레카" — 실제 수집 데이터에서 문제를 발굴해 보여주는 서비스. 근거 없는 수치를 지어내면 안 된다는 것이 전체 설계의 축이다.

> **AI(LLM)는 라벨만 붙인다. 숫자는 DB(집계 코드)가 센다.**
> "불만도 73점"처럼 LLM이 숫자를 직접 산출하는 필드는 **모델 설계 단계에서 아예 만들지 않는다.**
> 대신 LLM은 `높음/중간/낮음` 같은 라벨만 달고, 그 라벨이 몇 건인지는 순수 함수가 센다.

이 원칙은 `Final/Backend/tests/test_no_numbers.py`가 **테스트로 강제**한다:
- `LLM_FILLED_MODELS`에 속한 모델(`Judgement`, `ProblemDraft`, `Evidence` 등)은 `int`/`float` 필드를 가지면 즉시 실패한다.
- 중첩된 pydantic 모델(예: `ProblemSignals`)을 실수로 LLM 모델에 붙여도 재귀적으로 잡아낸다.
- 새 필드를 추가할 때마다 **먼저 이 테스트가 통과하는지 확인해라.** `pytest tests/test_no_numbers.py -v`.

부가 원칙:
- **분모 없는 건수는 화면에 못 쓴다.** "강한 불만 12건"은 반드시 "판정된 40건 중"과 함께 나와야 한다 (`*_labeled_count` 필드들).
- **표본이 적으면(3건 미만) 그 분포를 아예 숨긴다.** `settings.MIN_LABELED_TO_SHOW`.
- **연령·성별은 추론 금지, 명시적 자기 서술만.** "간호사인데" → 성별 추측 금지(편견). `llm_tool._clean_gender`가 규칙으로 방어한다.
- **`PAIN_SIGNALS`(판별용 사전)와 `PAYMENT_SIGNALS`(집계용 사전)를 절대 합치지 마라.** `dictionaries.py`의 `PAYMENT_SIGNALS` 주석에 4가지 부작용이 적혀 있다.
- **`app/tools/aggregate_tool.py`는 `llm_tool`을 절대 import하지 않는다.** 숫자를 만드는 곳과 LLM을 부르는 곳을 파일 경계로 분리해뒀다.

---

## 2. 지금 상태 — 이미 완료된 것 (다시 만들지 말 것)

### 파이프라인 지도

```
①CollectorAgent   (완성) → list[RawItem]
②InterpreterAgent (완성) → list[ProblemCandidate]  ─┐
                                                      │ corpus_tool.save_candidates 로 영속화됨
②′EvidenceAgent   (완성, 신규) → list[EvidenceBundle] = Evidence[] + ProblemSignals + PublishGate
       ↑ llm_tool 을 import하지 않는다. 그래서 ③이 없어도 여기까지는 완주된다.
③ProblemAgent     (스텁, NotImplementedError) — 담당자 미배정. 손대지 않았다
④IdeaAgent        (스텁) — 이번 작업에서 의도적으로 잠금
```

### 백엔드 (`Final/Backend/`) — `pytest tests/ -q` → **461 passed**

| 파일 | 상태 |
| :-- | :-- |
| `app/schemas/models.py` | `ProblemSignals`·`PublishGate`·`EvidenceBundle`·`WeekCount`·`ServiceMention` 신규. `Judgement`에 `has_payment_signal`·`sufferer_role`·`sufferer_age_band`·`sufferer_gender`·`mentioned_service` 5개 라벨. `Problem`에 `complexity_note`·`signals`·`gate` 추가 |
| `app/config/settings.py` | `PUBLISH_MIN_CASES`(20)·`PUBLISH_MIN_SOURCES`(3)·`PUBLISH_MIN_EVIDENCE`(3)·`EVIDENCE_SHOW_MAX`(5)·`EVIDENCE_LOOKBACK_WEEKS`(8)·`MIN_LABELED_TO_SHOW`(3) |
| `app/config/dictionaries.py` | `PAYMENT_SIGNALS`(15표현) 신규, `PAIN_SIGNALS`와 분리 |
| `app/tools/text_tool.py` | `has_payment_signal`·`payment_signal_hits`·`item_text`(공개 별칭) 추가 |
| `app/tools/aggregate_tool.py` | **신규 파일.** `signals_for()`·`publish_gate()` — 근거 상세 페이지의 모든 집계를 순수 함수로 |
| `app/agents/evidence_agent.py` | **신규 파일.** ②′ 근거 조립기. 출처 라운드로빈으로 근거 3~5건 선별, 게시 기준 판정 |
| `app/tools/corpus_tool.py` | `save_candidates`/`load_candidates`/`load_raw_items_by_ids`/`load_judgements_by_ids` 추가 |
| `app/agents/interpreter_agent.py` | 승격 후보를 디스크에 저장하도록 1줄 추가(예전엔 반환값으로만 존재해 즉시 소멸했다) |
| `app/graph/pipeline.py` | `run_collect_pipeline`이 ①→②→②′까지 연결됨(③은 기다리지 않는다). 반환 타입이 `list[Problem]`→`list[EvidenceBundle]`로 바뀜(의도된 것) |
| `app/prompts/interpreter_prompts.py` | `JUDGE_PAINS`에 신규 라벨 4종 지침 추가. "직업으로 성별 추측 금지" 명시 |
| `scripts/build_evidence_preview.py` | **신규.** 읽기 전용 미리보기. 코퍼스가 비어 있어도(`.env` 키 없음) 예외 없이 빈 결과 출력 |
| `scripts/run_pipeline.py` | `Category.PRODUCTIVITY`(존재 안 함) → `Category.IT_PRODUCTIVITY` 버그 수정 |

### 프론트엔드 (`Final/Frontend/`) — `tsc` 0에러 · `next build` 성공 · `build:single` 성공

> **2026-09-12 후속 결정:** 사용자가 제공한 `/Users/minkyu/Downloads/공유용 (2).html`의
> 9개 화면이 기준 프론트 디자인이다. 이를 `reference-pages/`에 페이지별 원본으로 보존했고,
> 기본 `npm run build:single`은 이 화면들을 묶어 `eureka-공유용.html`을 생성한다.
> 기존 React 화면은 삭제하지 않았으며 `npm run build:react-single`로 별도 생성할 수 있다.
> 기준 디자인의 `detail.html`에는 게시 기준, 집계 분모, AI 판정 표시, 근거 필터 4종을
> 같은 시각 언어로 이식했다. 두 단일 HTML 빌드는 같은 출력 경로를 사용하므로 최종 공유 전에는
> 반드시 `npm run build:single`을 마지막에 실행한다.
> 사용자의 최종 정정에 따라 기준 디자인의 `config.html`은 카테고리·플랫폼 선택을 제거하고,
> 나이대·성별·직업·장소 중 최소 2개를 입력하는 타겟 온보딩으로 확정했다.
> 직업·장소는 Enter로 키워드 칩을 등록하며 선택값은 로딩 화면과 결과 요약까지 이어진다.

| 파일 | 상태 |
| :-- | :-- |
| `reference-pages/*.html` | 사용자 제공 공유용 HTML에서 추출한 기준 프론트 9개 화면 |
| `scripts/import-reference-single.mjs` | 사용자 제공 단일 HTML을 페이지별 소스로 가져오는 도구 |
| `scripts/build-reference-single.mjs` | 기준 프론트 9개 화면을 다시 단일 공유용 HTML로 묶는 기본 빌더 |
| `reference-pages/config.html` | 나이대·성별·직업·장소 중 최소 2개 입력. Enter 키워드 칩과 탐색 잠금 검증 포함 |
| `src/api/types.ts` | 백엔드 계약과 1:1 동기화 완료(`ProblemSignals`·`PublishGate` 등) |
| `src/screens/*.tsx` | `TAEYUN/prototype/src`에서 이식 완료. `Combine.tsx`/`Ideas.tsx`/`Personalize.tsx`는 **의도적으로 스텁 유지**(잠금 대상이라 새 계약으로 재작성 안 함) |
| `app/ideas/`, `app/personalize/`, `app/problems/combine/`, `app/combined/` 라우트 | `notFound()`로 잠금 |
| `src/screens/ProblemDetail.tsx` | 근거 상세 페이지 8블록 + 근거 필터 4종 구현 |
| `src/screens/Onboarding.tsx` | 같은 계약의 React 타겟 설정 화면(나이대·성별·직업·장소, 최소 2개) |
| `src/lib/targetMatch.ts` | 신규. `Evidence.summary`에만 부분 매칭 |
| `src/components/evidence/{StatBar,CountWithDenominator,JudgedBadge,GateChecklist}.tsx` | 신규 공통 컴포넌트 |
| `src/data/mock.ts` | 손으로 쓴 문제 8개(실데이터 없어서). ③이 완성되면 교체 대상 |

### 문서

`docs/DATA_SPEC.md`·`docs/DATA_COLLECTION.md`·`docs/DATA_SOURCES.md`·`Final/Backend/PROGRESS.md` 전부 이번 작업 반영해서 갱신됨. **이게 최신이다** — 오래된 계획 문서를 찾지 마라.

### 검증 명령어

```bash
cd Final/Backend && .venv/bin/python -m pytest tests/ -q                 # 461 passed 기대
cd Final/Backend && .venv/bin/python scripts/build_evidence_preview.py   # [] 출력 (코퍼스 비어있음)
cd Final/Frontend && npx tsc --noEmit && npm run build && npm run build:single
```

---

## 3. 완료 — 코드 대조로 확인했던 미완성 2건 (Codex, 2026-09-12)

아래 두 항목은 Codex가 계약·백엔드·프론트·목데이터까지 반영했다.
`pytest tests/ -q` 461개, `npx tsc --noEmit`, Webpack 프로덕션 빌드,
`npm run build:single`로 검증했다. 기본 Turbopack 빌드는 실행환경의 로컬 포트
바인딩 제한으로 실패했으며 같은 소스를 Webpack 빌드로 검증했다.

### 3-1. 근거 목록 필터 칩 — 완료

**계획**: 문제 상세 페이지 근거 목록(⑨ 블록) 위에 `[전체] [강한 불만] [돈 언급] [해결책 탐색]` 필터 칩.
**현재**: `[전체] [강한 불만] [돈 언급] [해결책 탐색]` 칩이 있고,
`Evidence`에 복사된 건별 판정 라벨로 클라이언트에서 필터링한다.
**원인**: `Evidence`(`models.py`/`api/types.ts`)에 `raw_item_id`·`summary`·`excerpt`만 있고, 근거 **건별** 라벨(강한 불만인지, 돈 언급이 있는지, 결핍 신호가 있는지)이 없다. `ProblemSignals`엔 집계값만 있어서 개별 근거를 걸러낼 수 없다.

**고치는 법**:
1. `Final/Backend/app/schemas/models.py`의 `Evidence`에 필드 3개 추가 (전부 라벨, 숫자 아님 — `test_no_numbers.py` 통과 확인할 것):
   ```python
   class Evidence(BaseModel):
       raw_item_id: str
       summary: str
       excerpt: Optional[str] = None
       # ↓ 신규. 근거 목록 필터용. 이 근거를 만든 Judgement에서 그대로 복사한다.
       severity: Optional[Literal["높음", "중간", "낮음"]] = None
       has_payment_signal: bool = False
       has_need_signal: bool = False
   ```
2. `app/agents/evidence_agent.py`의 `_select_evidence()`에서 `Evidence(...)` 생성할 때 위 3개 필드를 `j.severity`/`j.has_payment_signal`/`j.has_need_signal`에서 채운다(이미 그 자리에 `j`가 있다).
3. `Final/Frontend/src/api/types.ts`의 `Evidence`에 동일 필드 3개 추가.
4. `ProblemDetail.tsx`의 근거 목록 위에 필터 칩 4개(전체/강한 불만/돈 언급/해결책 탐색) 추가 — 클라이언트에서 `evidence.filter(e => ...)`로 거르면 된다. 백엔드 재계산 불필요.
5. `tests/test_evidence_agent.py`에 "선별된 Evidence의 severity가 원본 Judgement와 일치하는지" 테스트 추가.

### 3-2. 게시 기준 체크리스트의 실제 기준 숫자 — 완료

**계획**: "관련 사례 47건 ✓ **(기준 20건)**"처럼 기준 수치를 사용자에게 그대로 보여준다.
**현재**: `PublishGate.min_cases`·`min_sources`·`min_evidence`를 백엔드가
판정 당시 설정값으로 채우고, 화면이 각 실제 집계값 옆에 기준을 함께 표시한다.
**원인**: `PublishGate` 모델에 `case_count_ok`(불리언)만 있고, 기준 숫자 자체(`min_cases` 등)가 없다. 프론트가 하드코딩 없이는 보여줄 방법이 없다.

**고치는 법**:
1. `models.py`의 `PublishGate`에 필드 3개 추가:
   ```python
   class PublishGate(BaseModel):
       case_count_ok: bool
       source_count_ok: bool
       evidence_count_ok: bool
       passed: bool
       reason: str = ""
       # ↓ 신규. 화면이 기준 숫자를 하드코딩하지 않고 그대로 보여주기 위해.
       min_cases: int = 0
       min_sources: int = 0
       min_evidence: int = 0
   ```
2. `app/tools/aggregate_tool.py`의 `publish_gate()`에서 이미 지역변수로 갖고 있는 `min_cases`/`min_sources`/`min_evidence`를 그대로 반환값에 넣는다(로직 변경 없음, 필드만 채우면 됨).
3. `api/types.ts`의 `PublishGate`에 동일 필드 3개 추가.
4. `Final/Frontend/src/components/evidence/GateChecklist.tsx`에서 각 행에 `(기준 ${gate.min_cases}건)` 형태로 병기.
5. `tests/test_aggregate_tool.py`에 `min_cases == settings.PUBLISH_MIN_CASES` 같은 회귀 테스트 추가.

두 작업은 **기존 테스트를 무회귀로 통과**했고, 회귀 테스트 1개가 추가돼 총 461개가 됐다.

---

## 4. 그다음 우선순위 (3절보다 크고, 다른 담당 영역과 겹침)

| # | 항목 | 비고 |
| --: | :-- | :-- |
| 1 | **③ ProblemAgent 구현** — `Problem` 객체를 만드는 유일한 경로가 아직 스텁이다 | 원래 다른 담당자 몫. 이 세션에서 의도적으로 손대지 않았다. `app/agents/evidence_agent.py`가 만든 `EvidenceBundle`을 입력으로 문장(`title`·`description`·`context`·`complexity_note`)만 쓰면 된다 — 숫자·근거 선별은 이미 끝나 있다 |
| 2 | **`.env` API 키 채우기** — `NAVER_CLIENT_ID`/`SECRET`·`KAKAO_REST_API_KEY`·`LLM_*` 전부 공란. 배치가 한 번도 안 돌았다 | 실행하면 `scripts/run_pipeline.py` 그대로 쓰면 된다 |
| 3 | `db_tool.py` 구현 — 전부 `NotImplementedError` 스텁. ③이 만든 `ProblemDraft` + `EvidenceBundle`을 합쳐 `Problem`을 완성하고 DB에 쓰는 자리 | ③과 함께 진행 |
| 4 | 발췌(`Evidence.excerpt`) 부활 — `collector_agent.py`가 `license=SUMMARY_ONLY`를 하드코딩해서 발췌가 영구히 `None`이다 | **법률·약관 확인 후.** `docs/DATA_SPEC.md` 8절 위험 2 참고. 지금은 보류가 맞다 |
| 5 | `ProblemList`의 "조합에 담기" 체크박스 — `/problems/combine`이 잠겨 있는데 UI는 남아 있다 | 사소함. 지우거나 그대로 둬도 무방(클릭해도 404로 안전하게 막힘) |

---

## 5. 담당 경계 (팀 공유 파일 주의)

- **박민규 담당**: ①수집·②해석·②′근거조립 (`Final/Backend/app/agents/collector_agent.py`, `interpreter_agent.py`, `evidence_agent.py`, 관련 tools). 이 문서를 쓴 세션이 전부 이 사람 대신 진행한 것이다.
- **태윤 담당**: 프론트엔드(`Final/Frontend/`). **이번에 Claude가 프론트까지 전부 대신 만들었다** — 아직 태윤과 조율 전이다. Codex가 프론트를 더 건드리기 전에 사용자에게 태윤과의 조율 여부를 확인하는 게 안전하다.
- **③④ 담당자 미상**: `problem_agent.py`·`idea_agent.py`. 건드리려면 먼저 팀에 확인해라.
- **`Final/Backend/app/schemas/models.py`**: 파일 머리말에 "이 파일을 바꾸려면 팀에 먼저 알릴 것"이라고 적혀 있다. 3절의 계약 확장도 팀 공지 대상이다.

---

## 6. 참고 문서 (자세한 배경이 필요할 때만)

- `docs/DATA_SPEC.md` — 근거 상세 페이지 8블록 사양, 계약 변경 이력, 미결정 항목
- `docs/DATA_COLLECTION.md` — 수집·판별·묶기·게시 기준의 전체 파이프라인 설계
- `docs/DATA_SOURCES.md` — 플랫폼별 API/크롤링 조사, 구현 상태
- `Final/Backend/PROGRESS.md` — 체크박스 형태 진행 현황(더 세분화된 버전)

이 문서(`AI협업.md`)와 위 문서가 어긋나면 **위 문서 쪽 날짜가 더 최신인지 먼저 확인해라** — 둘 다 2026-09-12에 함께 갱신됐지만, 이후 누군가 `docs/`만 고칠 수 있다.
