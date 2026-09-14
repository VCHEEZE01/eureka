> 2026-09-14 수집량·노출 개선: 검색 120회×20건·판별 2,400건, 표현 없는 상황 탐색, 진행 중 불편 전체 보기, JSON 형식 재생성 1회. Backend 615 / Frontend 34 테스트 통과. 새 상한의 실제 전체 API 실행은 미실행. 최신 상세: ../../docs/PRODUCTION_COLLECTION_RUNBOOK.md

# ①수집 에이전트 · ②해석기 · ②′근거 조립기 — 진행 상황

## 2026-09-13 타겟 수집 연결 완료

사용자 결정에 따라 나이대·성별·직업·장소 입력 → POST 수집 실행 → 원문 문구 검사 → 판별 → 근거·검토 문제정의로 연결했다. 기존 배치 전용 설계를 대체하는 사용자 경로이며, 기준 reference HTML을 `http://localhost:8000`에서 제공한다. React는 기본 서비스로 사용하지 않는다.

실제 최종 실행 `col-21487dbac1b941b9a0320966`: 검색 5개 성공 → 원문 31건 → 타겟 문구 확인 3건 → Gemini 판별 2건 → 불편 후보·문제정의 0건. 미확인 28건은 보존하며 문제 생성에서 제외했다. 첫 연결 실행의 미검증 문제 세 개는 과거 이력으로만 보존하고 현재 타겟 결과에 노출하지 않는다. 문구 확인은 작성자의 속성 입증이 아니다.

백엔드 전체 **561개**, 프론트 **17개** 테스트 통과. 실제 브라우저 입력·상태 조회·빈 결과·새로고침 복원·이전 정책 결과 차단 확인. 실행법·상한·검증은 `docs/TARGET_COLLECTION_RUNBOOK.md`, 설계 지도는 `docs/eureka-agent-guide.html`과 바탕화면 `유레카_에이전트_설계지도.html`을 따른다.


**담당: 박민규** · 최종 갱신 2026-09-13

## 2026-09-13 문제정의 상세 연결 완료

- ③ ProblemAgent 구현: 실제 원문에서 제목·한 줄·설명·맥락·복잡성 서술 생성, 별도 Gemini 근거 대조 검수. 집계·근거는 코드가 결합하며 숫자·원문 링크를 LLM이 만들지 않는다.
- 게시 기준·AI 검수·사람 검수 승인 기록을 모두 통과한 문제만 JSON 공개 저장소에 저장한다. GET `/problems`, `/problems/{id}`는 읽기만 수행한다.
- `scripts/build_problems.py`가 저장 후보에서 상세 JSON·검수 보고서를 생성한다. `--review --include-pending`은 기준 미달 후보의 검토 전용이며 공개 저장하지 않는다.
- 실제 사례 하나로 생성·검수 실행 및 근거 1건의 메타데이터·집계 조립 확인. v1의 과대 추론을 발견해 방어를 보강했고 v2도 AI 검수 보류로 남겼다. 공개 문제 0개, 실제 검토용 상세 1개다.
- 기준 HTML에 실제 JSON·AI 검수 보고서 연결, React에 읽기 API 연결. 원문 링크·근거 필터·표본 부족·게시 보류·없는 ID·모바일 헤더를 브라우저에서 확인했다. 아이디어·조합·개인화는 잠금 유지.
- 백엔드 **521개**, 프론트 데이터 회귀 **6개** 통과. Next 타입·Webpack 빌드·단일 HTML 빌드 통과. 합성 20사례 통합 테스트로 생성→사람 승인→저장→공개 조회 계약도 검증했다(실데이터 정확도 측정 아님).
- 재개 명령·검증 한계: [문제 상세 실행 안내](../../docs/PROBLEM_DETAIL_RUNBOOK.md). 시각화: [에이전트 설계 지도](../../docs/eureka-agent-guide.html).

## 2026-09-13 Gemini 호출 복구

- 기존 `gemini-2.5-flash-lite` 실호출에서 HTTP 404 재현: Google이 신규 사용자에게 해당 모델을 제공하지 않는다고 응답했다.
- Google 오류 안내에 따라 `.env`, `.env.example`, Settings 기본 모델을 `gemini-3.5-flash-lite`로 변경했다.
- 실제 텍스트 응답 `OK`와 `complete_json` 응답 `{"ok": true}` 확인 완료. 관련 테스트 `tests/test_gemini_llm.py tests/test_llm.py`는 56개 통과했다.
- `.env`의 `LLM_DRY_RUN=true`는 유지했다. 실제 호출 확인: `LLM_DRY_RUN=false .venv/bin/python -m app.core.llm --ping` (Backend 디렉터리에서 실행).
- 아래 기존 진행 기록은 당시 상태다. 현재 Gemini 키는 설정되어 있으며, 이번 복구에서는 전체 수집·판별 배치를 실행하지 않았다.

## 2026-09-13 실데이터 파일럿

- IT/생산성 `회의록` 소규모 수집 46건 → 규칙 통과 26건 → Gemini 최초 불편 판정 12건.
- 가이드·홍보 문구를 실제 경험으로 인정하는 오탐을 발견해 판별 프롬프트를 보강했다. 같은 26건을 두 번 재판별한 결과 양성은 각각 2건이며 불편 여부는 26/26 일치했다. 남은 양성 1건은 요약에 근거 없는 추론이 있어 검토 보류다.
- 보강 결과에서 최소 묶음 5건을 충족한 후보는 0개. 근거 조립기까지 실행했으나 실제 근거 묶음은 없으므로 화면 연결 검증은 미완료다.
- 관련 회귀 테스트 150개 통과. 최초 판정과 비교 판정은 별도 저장했다. `data/corpus`의 최초 판정에는 오탐이 남아 있으므로 게시용으로 쓰지 않는다.
- 상세 결과·한계·이어서 실행할 위치: [Gemini 파일럿 보고서](../../docs/GEMINI_PILOT_2026-09-13.md).

근거 계획: `~/.claude/plans/vivid-launching-naur.md` · 사양: [`docs/DATA_SPEC.md`](../../docs/DATA_SPEC.md) · [`docs/DATA_COLLECTION.md`](../../docs/DATA_COLLECTION.md)

> 이 파일이 한동안 뒤처져 있었다 — 아래 체크박스는 실제 `pytest tests/ -q` 결과(461 passed)와
> `git status`(코드 반영분)를 보고 다시 맞췄다. 지금부터는 진행하면서 바로 체크한다.

---

## 준비

- [x] 뼈대 파악 · 계약(`schemas/models.py`) 확인
- [x] `docs/DATA_COLLECTION.md` · `DATA_SOURCES.md` 사양 추출
- [x] 팀 회의 결과 반영 → `docs/DATA_SPEC.md` 작성
- [x] 구현 계획 승인
- [x] `docs/DATA_SPEC.md` 커밋 + 팀 공지 (계약 변경 1차 4건 — `Category`·`SourceKind`·`RawItem`·`Judgement`)
- [x] Python 3.11 venv · `app/config/settings.py` (pydantic-settings)
- [x] `app/tools/corpus_tool.py` 구현 완료 (JSONL append-only 저장소)
- [x] 네이버·카카오·Gemini 키 설정 및 소규모 실제 수집·판별 완료 (2026-09-13). 전체 배치는 아직 실행하지 않았다.

## ① 수집 에이전트 — 완료

- [x] `app/config/dictionaries.py` — 불편 신호 사전 6유형 36표현 + `DOMAIN_KEYWORDS` 5개 카테고리 × 24 + `DICT_VERSION`
- [x] `collector_agent._build_queries()` — 도메인 키워드 × 불편 표현 × 소스 조합
- [x] `search_tool` — 네이버(블로그·뉴스·지식iN·카페) + 카카오(블로그·웹문서)
- [x] `app/tools/text_tool.py` — 정제 · PII 제거 · `content_hash` · 완결 문장 추출기(`extract_sentences`)
- [x] `collector_agent.run()` 완성 + JSONL 적재
- [x] **① 완료** — 코드는 실데이터를 `RawItem`으로 쌓을 준비가 됐다 (실행은 `.env` 채운 뒤)
- [ ] 공공데이터 수집기 추가 (헬스케어·금융의 안전한 출발점) — API 키 승인 대기
- [x] 네이버 뉴스 + 카카오 추가
- [ ] 지식iN·카페를 표시에도 쓸지 — 수집엔 이미 들어감, 표시 여부는 팀 미결정 (`DATA_SPEC.md` 6절 #1)

## ② 해석기 — 완료

- [x] `text_tool.rule_judge()` — 30자 / 신호 / 광고 / 중복
- [x] `interpreter_agent` 규칙 판별 경로 (`use_llm=False`)
- [x] 결핍 신호 집계 = 필요도 재료 (`has_need_signal`)
- [x] `app/core/llm.py` — LLM 어댑터 + dry-run
- [x] `app/prompts/interpreter_prompts.py` — `JUDGE_PAINS` (2026-09-12: 근거 페이지용 라벨 4종 지침 추가)
- [x] `llm_tool.judge_pains()` + 방어 로직 5개 (환각 id · 누락 보정 · 숫자 차단 · 복제 차단 · 라벨 정규화)
- [x] 불편 강도 라벨(`severity`) = 불만도 재료
- [x] 실LLM 연결 및 50건 상한 파일럿 — 실제 수집 46건 중 26건 판별, 프롬프트 보강 후 같은 26건 2회 재현성 확인 (2026-09-13)
- [ ] 새 표본·사람 정답 기반 판별 품질 검증 — 잘린 스니펫 추론·역할 라벨 문제 잔존
- [x] `cluster_tool` — TF-IDF char n-gram + 폴백
- [x] `interpreter_agent.run()` 완성 — 5건 기준 · 출처 편중 상한 · `pending` 적재
- [x] **② 완료** — `ProblemCandidate`가 나온다
- [x] **승격된 후보를 디스크에 남긴다** (2026-09-12) — 예전엔 반환값으로만 존재해 파이프라인이 즉시 버렸다. `corpus_tool.save_candidates`로 고침
- [ ] θ 튜닝 (라벨 200쌍 → precision 0.85 기준) — 실데이터 없어서 보류
- [ ] `pending` 자동 승격 + 주간 배치 스크립트

## ②′ 근거 조립기 — 신설, 완료 (2026-09-11~12)

문제 상세 근거 페이지(8블록) 작업 중 파이프라인의 "5 구성" 단계가 통째로 비어 있는 것을
발견해 신설했다. ②(해석기)와 ③(문제정의 생성기) 사이에 낀다 — 문장은 ③이 쓰고,
근거 선별·신호 집계·게시 기준 판정은 여기가 한다. `llm_tool`을 import하지 않아서
③이 스텁인 채로도 근거 페이지 데이터가 완성된다.

- [x] `app/tools/aggregate_tool.py` — `ProblemSignals` 집계 (순수 함수 5개), `PublishGate` 판정
- [x] `app/agents/evidence_agent.py` — 근거 모으기 → 신호 세기 → 게시 기준 확인 (3단계)
- [x] 근거 선별 = 출처 라운드로빈 (`DATA_COLLECTION.md` 6절 구현)
- [x] `corpus_tool` — `save_candidates`/`load_candidates`/`load_raw_items_by_ids`/`load_judgements_by_ids`
- [x] `app/graph/pipeline.run_collect_pipeline` — ①→②→②′ 연결 (③은 기다리지 않는다)
- [x] `scripts/build_evidence_preview.py` — 읽기 전용 미리보기 (빈 코퍼스에서도 통과)
- [x] `scripts/run_pipeline.py`의 `Category.PRODUCTIVITY` 버그 수정 (`IT_PRODUCTIVITY`)
- [x] `models.py` 계약 변경 2차 5건 (`ProblemSignals`·`PublishGate`·`EvidenceBundle`·`Judgement` 라벨 5개·`complexity_note`) — `Final/Frontend/src/api/types.ts`와 동기화 완료
- [x] `PAYMENT_SIGNALS` 사전 신설 (`PAIN_SIGNALS`와 분리 — 섞으면 4곳 깨짐, `dictionaries.py` 주석 참고)
- [x] 연령·성별 라벨은 명시적 자기 서술만 (직업으로 성별 추측 금지, `llm_tool._clean_gender` 규칙 방어 + 테스트로 고정)
- [x] `Evidence`에 근거별 강도·지불·결핍 라벨 보존 — 프론트 근거 필터 4종 연결
- [x] `PublishGate`에 판정 당시 기준값 3개 보존 — 체크리스트가 실제 기준 숫자를 표시

## 검증

- [x] `scripts/run_collect_only.py` — ①→② 단독 실행 (안내 후 정상 종료 포함)
- [x] pytest + `conftest.py` (실API 차단) — **461 passed** (2026-09-09 393 → +68)
- [x] `tests/test_no_numbers.py` — 규칙 자동 강제. **2026-09-12: 테스트 구멍 2개 보강**(LLM 모델 목록에 `ProblemDraft`등 4개 추가, 중첩 pydantic 모델 검사 추가)
- [ ] `.github/workflows/backend.yml`

---

## 프론트 연동 (2026-09-12 신규 항목)

- [x] `TAEYUN/prototype/src` → `Final/Frontend/src` 이식 (타입을 `api/types.ts` 계약으로 전환)
- [x] 아이디어 라우트 잠금 (`app/ideas/`·`app/personalize/`·`app/problems/combine/`·`app/combined/` → `notFound()`)
- [x] 근거 상세 페이지 8블록 구현 (`ProblemDetail.tsx`)
- [x] 근거 목록 필터 칩 4종(전체·강한 불만·돈 언급·해결책 탐색)
- [x] 게시 기준 체크리스트에 실제 기준값 병기(프론트 하드코딩 없음)
- [x] 공유용 기준 온보딩 — 카테고리·플랫폼 제거, 나이대·성별·직업·장소 중 최소 2개 입력
- [x] `npx tsc --noEmit` 0 에러 · `npm run build` · `npm run build:single` 전부 통과
- [x] 실제 모드의 목록·상세는 API/내장 JSON을 읽도록 연결. 목데이터는 명시적 디자인 데모 모드에만 사용.

---

## 막고 있는 것

| # | 항목 | 누가 |
| --: | :-- | :-- |
| 1 | ③·저장·조회·상세 연결은 구현. 공개 가능한 표본 확보와 사람 내용 검수는 진행 필요 | 팀 |
| 2 | API 연결·소규모 배치는 완료. 실제 경험 판별의 잔여 오탐과 새 표본 검증 필요 | 박민규 |
| 3 | 지식iN·카페를 화면에도 노출할지 | 팀 |
| 4 | "서로 다른 출처 3곳"의 정의 (지식iN/카페/블로그를 따로 셀지) | 팀 |
| 5 | 게시 기준 수치(20건/3곳/3건)가 적절한지 — 실데이터 보고 조정 | 팀 |
| 6 | 헬스케어·금융 민감정보 취급 범위 | 팀·법률 |
| 7 | 발췌(`Evidence.excerpt`) 인용 범위 — 지금은 `license` 하드코딩으로 항상 `null` | 팀·법률 |
