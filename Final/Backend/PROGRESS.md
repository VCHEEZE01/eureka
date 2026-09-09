# ①수집 에이전트 · ②해석기 — 진행 상황

**담당: 박민규** · 최종 갱신 2026-09-09

근거 계획: `~/.claude/plans/dapper-tumbling-fairy.md` · 사양: [`docs/DATA_SPEC.md`](../../docs/DATA_SPEC.md)

---

## 준비

- [x] 뼈대 파악 · 계약(`schemas/models.py`) 확인
- [x] `docs/DATA_COLLECTION.md` · `DATA_SOURCES.md` 사양 추출
- [x] 팀 회의 결과 반영 → `docs/DATA_SPEC.md` 작성
- [x] 구현 계획 승인
- [ ] **`docs/DATA_SPEC.md` 커밋 + 팀 공지** (계약 변경 4건 · 미결정 5건)
- [ ] Python 3.11 venv · `.env` 채우기
- [ ] `app/config/settings.py` (pydantic-settings)
- [ ] `app/tools/corpus_tool.py` 스텁 → `import app` 통과

## ① 수집 에이전트

- [ ] `app/config/dictionaries.py` — 불편 신호 사전(문서 5절 그대로) + `DOMAIN_KEYWORDS` **5개 카테고리** + `DICT_VERSION`
- [ ] `collector_agent._build_queries()` — 도메인 키워드 × 불편 표현 조합
- [ ] **`search_tool` — 네이버 블로그 하나** ← 첫 실데이터
- [ ] `app/tools/text_tool.py` — 정제 · PII 제거 · `content_hash` · **완결 문장 추출기**
- [ ] `collector_agent.run()` 완성 + JSONL 적재
- [ ] **① 완료** — 실데이터가 `RawItem`으로 쌓인다
- [ ] 공공데이터 수집기 추가 (헬스케어·금융의 안전한 출발점)
- [ ] 네이버 뉴스 + 카카오 추가 → 출처 3곳 충족
- [ ] (결정 시) 지식iN · 카페 추가

## ② 해석기

- [ ] `text_tool.rule_judge()` — 30자 / 신호 / 광고 / 중복 (문서 3-3)
- [ ] `interpreter_agent` 규칙 판별 경로 (`use_llm=False`) — LLM 비용 0으로 통과율 확인
- [ ] **결핍 신호 집계** = 필요도 재료
- [ ] `app/core/llm.py` — 포텐스닷 어댑터 + `EchoLLM`
- [ ] `app/prompts/interpreter_prompts.py` — `JUDGE_PAINS`
- [ ] `llm_tool.judge_pains()` + 방어 로직 4개 (환각 id · 누락 보정 · 숫자 차단 · 복제 차단)
- [ ] **불편 강도 라벨** = 불만도 재료
- [ ] 포텐스닷 실연결 → 50건 실호출 · 라벨 재현성 확인
- [ ] `cluster_tool` — TF-IDF char n-gram + Agglomerative + 폴백
- [ ] `interpreter_agent.run()` 완성 — 5건 기준 · 출처 편중 상한 · `pending` 적재
- [ ] **② 완료** — `ProblemCandidate`가 나온다
- [ ] θ 튜닝 (라벨 200쌍 → precision 0.85 기준)
- [ ] `pending` 자동 승격 + 주간 배치 스크립트

## 검증

- [ ] `scripts/run_collect_only.py` — ①→② 단독 실행
- [ ] pytest + `conftest.py` (실API 차단)
- [ ] `tests/test_no_numbers.py` — 규칙 ⑤ 자동 강제
- [ ] `.github/workflows/backend.yml`

---

## 막고 있는 것

| # | 항목 | 누가 |
| --: | :-- | :-- |
| 1 | `models.py` 계약 변경 4건 공지 (Category 5개 · SourceKind · RawItem · Judgement) | 팀 |
| 2 | 지식iN·카페를 수집에 넣는가 — 발췌 재료가 여기 몰려 있다 | 팀 |
| 3 | "서로 다른 출처 3곳"의 정의 | 팀 |
| 4 | 포텐스닷 엔드포인트 · 요청 형식 · 임베딩 지원 여부 | 박민규 |
| 5 | 헬스케어·금융 민감정보 취급 범위 | 팀·법률 |
