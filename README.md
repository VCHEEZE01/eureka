# 유레카

트렌드 키워드를 골라 AI로 서비스 아이디어를 만들고, 바로 바이브코딩에 쓸 프롬프트까지 받는 서비스 · 팀 **목욕중**

> 🌐 **지금 바로 써보기:** https://eureka-five-beta.vercel.app
> (모바일 화면은 아직 최적화 전입니다 — PC로 접속해주세요)

---

## 🔄 v0 → v1 전환 (2026-09-15)

실시간 대량 수집 + 건별 LLM 판별 방식(v0)을 폐기하고,
**트렌드·검색 키워드 사전 확보 → 아이디어 생성 → 바이브코딩 실행** 방향으로 전환했습니다.

판단 근거와 실측 데이터는 [`docs/PIVOT.md`](docs/PIVOT.md)에 정리돼 있습니다.
v0 코드 전체는 `v0-pre-pivot` 태그로 보존돼 있습니다 (`git checkout v0-pre-pivot`).

---

## 지금 상태

| | |
| :-- | :-- |
| 기획 (PRD · 플로우 · 디자인) | ✅ 완료 — [`TAEYUN/`](TAEYUN/) |
| 백엔드 (FastAPI + Gemini) | ✅ 실제 배포, 테스트 114개 통과 |
| 로그인·보관함·새로고침 제한 (Supabase) | ✅ 실사용 검증 완료 |
| 실제 배포 (Vercel) | ✅ `deploy` 브랜치 push → 자동 재배포 |
| 실제 트렌드 데이터 수집 (네이버·유튜브·스레드) | ❌ 미착수 — 지금은 고정 데이터 28개 |

실제로 동작하는 코드는 [`Final/`](Final/) 폴더에 있습니다. 구조·주의사항은
[`Final/README.md`](Final/README.md)를 먼저 읽어주세요.

---

## 📂 기획 자료 — 태윤이 정리한 것

| | 파일 | 내용 |
| :-- | :-- | :-- |
| **①** | [`Eureka_PRD_v2.md`](TAEYUN/Eureka_PRD_v2.md) | 기능 정의서 — F00~F10, IA, KPI |
| **②** | [`flow_diagram_abstract.png`](TAEYUN/flow_diagram_abstract.png) | 화면 흐름 한 장 |
| **③** | [`유레카_임시_DESIGN.md`](TAEYUN/유레카_임시_DESIGN.md) | 디자인 가이드 — 색·폰트·여백 |
| **④** | [`에이전트_흐름도.html`](TAEYUN/에이전트_흐름도.html) | 에이전트 설계 그림 |
| **⑤** | [`아키텍처_설계.md`](TAEYUN/아키텍처_설계.md) | 시스템 설계 초안 (당시 기준, 실제 구조는 [`Final/README.md`](Final/README.md) 참고) |
| **⑥** | [`팀원과공유.md`](TAEYUN/팀원과공유.md) | 초기 논의 기록 |

**보조 문서** — [`공유가이드.md`](TAEYUN/공유가이드.md) · [`논의_01_에이전트와_스택.md`](TAEYUN/논의_01_에이전트와_스택.md) ·
[`프롬프트_유레카.md`](TAEYUN/프롬프트_유레카.md)

> ⚠️ 예전엔 여기에 `TAEYUN/prototype/`(Next.js 프로토타입)과 `TAEYUN/eureka-공유용.html`(그 결과물)이
> 있었습니다. 실제 서비스(`Final/`)가 이를 완전히 대체해서 **2026-09-20에 정리하며 삭제했습니다.**
> 지금 눌러볼 수 있는 실물은 맨 위 배포 링크입니다. 경위는 [`docs/저장소_정리_2026-09-20.md`](docs/저장소_정리_2026-09-20.md) 참고.

---

## 🛠 로컬에서 돌려보기

실제 서비스 코드는 `Final/Backend`(서버) + `Final/Frontend`(화면 1개 HTML + JS)입니다.

```bash
cd Final/Backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
python -m app.trends.build_snapshot
uvicorn main:app --reload          # http://localhost:8000
```

자세한 건 [`Final/README.md`](Final/README.md)에 있습니다 (Supabase 연동 포함).

---

## 🤖 AI에게 맡기려면

```
Final/README.md 읽고 docs/ 훑어본 다음 지금 상태 요약해줘
```
