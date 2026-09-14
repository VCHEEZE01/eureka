# 문제정의·상세 근거 데이터 실행 안내

> **최신 사용자 경로:** 2026-09-13 타겟 입력에 따른 실제 수집으로 변경했다. 웹 실행과 새 검증은 [타겟 수집 실행 안내](TARGET_COLLECTION_RUNBOOK.md)를 따른다. 아래 내용은 이전 고정 검토 표본·생성 경로 기록이며 React 실행은 기본 서비스가 아니다.

2026-09-13. 이번 구현 범위는 수집 → 판별 → 근거 조립 → 문제정의·검수 → 저장·조회 → 상세 화면이다. 아이디어·조합·개인화는 잠금 상태다.

## 현재 결과와 파일

- 원본 파일럿: 수집 46건, 판별 26건. 수정 판별은 양성 2건이며 그중 직접 경험이 확인된 하나를 검토 예시로 선택했다. 전체 표본의 정확도를 검증한 것은 아니다.
- 실제 생성 데이터: `Final/Backend/data/problem-preview/problems-v2.json`.
- 생성·AI 검수 보고서: 같은 폴더의 `problems-v2.report.json`.
- 실제 상세 화면: 같은 폴더의 `eureka-problem-review.html`. 더블클릭한 후 문제 탐색에서 실제 항목을 선택하거나 `#detail.html?id=pc-2a556828d8243c97`로 연다.
- 시각화 원본: `docs/eureka-agent-guide.html`. 외부 리소스 없이 작동하는 단일 파일이다.

생성물에는 제목·한 줄·설명·맥락·복잡성 서술과 실제 근거·원문 링크·출처·작성일·라벨·분포·게시 기준이 들어 있다. 빈 속성과 부족한 표본은 추정해서 채우지 않는다. 최종 예시는 사례 1건·출처 1곳·대표 근거 1건이다. 게시 기준 20/3/3에 미달하며, 별도 AI 검수도 서술 범위를 이유로 보류했다. AI 검수 사유 자체도 사람의 정답은 아니다. 공개 목록에는 아무 문제도 게시하지 않았다.

첫 초안의 업무 복귀·음성·피로감 추론을 발견해 작성·검수 프롬프트와 관측된 표현 유형의 코드 방어를 보강했다. v2는 더 좁은 서술이지만 원문의 비유를 실제 텍스트 추출 작업으로 단정할 여지가 있어 검토용으로만 남긴다. 링크와 집계가 연결된다는 검증이 서술의 정확도를 보장하지 않는다.

## 저장된 자료로 다시 생성

수집을 반복할 필요는 없다. 최초 판정에는 오탐이 남아 있으므로 아래처럼 수정 판정이 있는 별도 평가 코퍼스를 사용한다. 기존 결과를 덮어쓰지 않도록 새 출력 파일명을 쓴다.

```bash
cd Final/Backend
LLM_DRY_RUN=false LLM_MAX_RETRIES=0 LLM_TIMEOUT_SEC=45 \
.venv/bin/python scripts/build_problems.py \
  --category 'IT/생산성' \
  --corpus-dir data/pilots/2026-09-13-gemini/revised-corpus \
  --review --include-pending --candidate-id pc-2a556828d8243c97 \
  --max-candidates 1 --output data/problem-preview/problems-next.json --execute
```

`--execute`를 빼면 계획만 표시한다. 기본은 승격된 후보만 읽으며 `--review --include-pending`을 지정할 때만 기준 미달 후보의 초안을 만든다. 모델의 실제 호출·JSON 형식·근거 검수 결과는 `.report.json`을 확인한다. 보류는 정상적인 검토 결과일 수 있으므로 종료 코드만으로 통과 여부를 판단하지 않는다. 생성·검수는 각각 모델 호출이며 JSON 오류·HTTP 오류에 대한 재시도는 별도다.

```bash
cd Final/Frontend
npm run build:single -- \
  --data ../Backend/data/problem-preview/problems-v2.json \
  --report ../Backend/data/problem-preview/problems-v2.report.json \
  --mode review \
  --out ../Backend/data/problem-preview/eureka-problem-review.html
```

기준 9개 화면의 디자인을 유지한다. 검토 배너와 AI 검수 사유를 표시하며 존재하지 않는 ID를 예시로 대체하지 않는다. 인자 없는 `build:single`은 명시적 디자인 데모다. `--mode published`에는 공개 저장소에서 읽은 결과만 사용해야 한다. 자동 기준을 통과한 초안이 곧 사람 검수까지 승인된 문제는 아니다.

## 공개 저장·조회 경계

③은 원문으로 서술 다섯 필드만 생성하고 별도 LLM 호출로 원문과 대조한다. 근거 배열과 메타데이터는 수집·판정에서 복사하며, 집계 코드는 원자료를 다시 세어 검증한다. 공개 저장은 게시 기준·AI 검수·명시적 사람 검수 승인 모두 필요하다. 기본 생성 경로에는 사람 승인이 없어 공개 저장하지 않는다. 승인 UI와 주간 스케줄러 운영은 이번 구현에 포함하지 않는다.

저장소는 `settings.PROBLEMS_DIR`의 문제별 JSON이고, 원문 스냅샷·승인 기록·AI 검수 결과를 함께 남긴다. 같은 ID를 자동 덮어쓰지 않으며 손상된 파일을 빈 목록으로 숨기지 않는다. GET `/problems`, GET `/problems/{id}`는 공개 저장소만 읽고 수집·LLM을 호출하지 않는다. 없는 ID는 404, 저장소 오류는 503이다. 원문 스니펫 전체는 API에 노출하지 않고 허용된 요약·출처 메타데이터만 전달한다.

```bash
# 터미널 1
cd Final/Backend
.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000

# 터미널 2
cd Final/Frontend
NEXT_PUBLIC_API_BASE=http://localhost:8000 npm run dev
```

Next 프로덕션은 같은 환경변수를 **빌드 시점**에 넣어야 한다. 실제 공개 목록은 현재 빈 배열이며 화면은 ‘아직 게시된 문제가 없습니다’를 표시한다. 미설정 API 주소로 `/problems`를 같은 프론트 origin에 요청하면 페이지 HTML과 충돌하므로 이 분리 실행에서는 주소를 반드시 지정한다.

## 검증과 남은 데이터 과제

- 백엔드 521개 테스트 통과. 합성 20사례의 집계·생성·사람 승인·공개 API 조회, 승인 없음 차단, 미달 보류, 원문 URL 위조·손상 파일·숫자·과대 추론 방어 포함. 합성 테스트는 실제 서비스 표본이 아니다.
- 프론트 6개 회귀 테스트·TypeScript·Next Webpack 빌드·기준 HTML 빌드 통과.
- 브라우저에서 실제 JSON 상세·검수 사유·원문 링크·네 가지 필터·표본 부족·404·아이디어 잠금·모바일 헤더 확인. Next와 FastAPI의 실제 로컬 HTTP 연결·빈 목록·404도 확인했다.
- 시각화의 다섯 탭, 단계 선택, 24개 판단의 분류·검색·Markdown 내보내기, 모바일 레이아웃을 확인했다.

후속 데이터 작업은 새 질문형 표본·사람 정답 검토·재판정 버전 선택이다. 검색 경로와 실제 원문 플랫폼의 분류도 별도로 다듬어야 한다. 현재 다음 웹문서로 찾은 커뮤니티 글의 `source_kind`는 요청 경로인 블로그이며, 독립 출처 수의 정의도 미결정 상태다. 게시 기준을 낮춰 빈 결과를 숨기거나 이 검토 자료를 승인된 문제로 바꾸지 않는다.
