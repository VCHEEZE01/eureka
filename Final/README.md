# 유레카 — Final

**팀 목욕중** · 실제 배포 중인 서비스입니다.

> 🌐 **배포 주소:** https://eureka-five-beta.vercel.app
> 📄 이 폴더의 지난 정리 작업 기록은 [`docs/저장소_정리_2026-09-20.md`](../docs/저장소_정리_2026-09-20.md) 참고.

이 README는 이전에 "개발 착수 전 공통 인식용 뼈대 구조" 문서였습니다.
지금은 코드가 실제로 다 채워지고 배포까지 끝난 상태라, **지금 구조를 그대로** 다시 썼습니다.

---

## 1. 실제로 이렇게 돌아갑니다

**프론트와 백엔드가 분리된 두 프로그램이 아닙니다.** 파이썬 서버 하나가 전부 합니다.

```
브라우저 ──GET /──▶ FastAPI(main.py) ──▶ v1-trend-incubator.html 그대로 서빙
                                          (화면 안의 <script>가 /api/* 를 호출)
```

애초에 계획은 "Next.js 프론트 + FastAPI 백엔드, 서로 HTTP로만 대화"였지만,
실제로 만들면서 **화면 하나를 HTML 파일 하나로 통째로 서빙하는 쪽으로 바뀌었습니다.**
그래서 `Frontend/`엔 더 이상 Next.js 프로젝트가 없습니다 — 삭제 경위는 정리 기록 문서 참고.

| 영역 | 실제 |
| :-- | :-- |
| **Frontend** | 순수 HTML + 바닐라 JS 1개 파일 (Figma 익스포트 + 연동 레이어) |
| **Backend** | Python 3.12(배포)/3.11(로컬 확인) · FastAPI · Pydantic 2 |
| **LLM** | Google Gemini (`app/core/llm.py`) — 실제 호출, mock 아님 |
| **인증·DB** | Supabase (Auth + Postgres, PostgREST를 httpx로 직접 호출) |
| **배포** | Vercel — `deploy` 브랜치를 Production으로 추적, push하면 자동 재배포 |

---

## 2. 폴더 구조 (지금 실제로 있는 것만)

```text
Final/
├─ Backend/
│  ├─ main.py                  FastAPI 진입점. 라우터 5개 등록
│  ├─ requirements.txt         로컬 개발용 전체 의존성 (테스트 포함)
│  ├─ app/
│  │  ├─ agents/
│  │  │  ├─ base.py            Agent 추상 클래스
│  │  │  └─ idea_agent.py      ★ 유일하게 살아있는 에이전트 — 키워드→아이디어 3개
│  │  ├─ api/
│  │  │  ├─ routes.py          GET / · /eureka-app.js · /og-image.png · /health
│  │  │  ├─ idea_routes.py     아이디어 생성·조회·새로고침
│  │  │  ├─ auth_routes.py     GET /api/config · /api/me
│  │  │  ├─ library_routes.py  보관함 CRUD (로그인 필수)
│  │  │  ├─ trend_routes.py    GET /api/trends — ⚠ 프론트가 안 부름(아래 3절 참고)
│  │  │  └─ deps.py            get_current_user 등 인증 의존성
│  │  ├─ config/settings.py    .env 읽는 유일한 곳
│  │  ├─ core/
│  │  │  ├─ llm.py             ★ 실제 Gemini 호출
│  │  │  └─ auth.py            Supabase JWT 검증 (JWKS/HS256)
│  │  ├─ ideas/                축(axes)·캐시·중복판정·폴백·검증
│  │  ├─ prompts/               idea_prompts.py · common_prompts.py
│  │  ├─ schemas/                pydantic 모델
│  │  ├─ tools/
│  │  │  ├─ idea_tool.py       스냅샷에서 키워드 조회
│  │  │  └─ supabase_tool.py   PostgREST 직접 호출 (보관함·쿼터)
│  │  └─ trends/                 build_snapshot.py · classify.py · metrics.py
│  ├─ db/001_auth_library_quota.sql   Supabase 대시보드에서 수동 실행
│  └─ tests/                    114개, 전부 pytest
│
├─ Frontend/
│  ├─ v1-trend-incubator.html  ★ 실제 배포되는 화면 전체 (Figma 익스포트)
│  ├─ eureka-app.js            ★ Supabase 로그인·보관함·새로고침 연동 레이어
│  ├─ assets/eureka.png        og:image (링크 공유 미리보기 썸네일)
│  ├─ 목욕중/                  "추천 AI" 로고 이미지들
│  └─ INTEGRATION.md           팀원이 새 디자인 HTML을 줄 때 지킬 체크리스트
│
└─ README.md                   이 파일
```

---

## 3. 알아두면 사고를 막는 것 3가지

### ① 키워드 데이터가 두 군데 따로 있습니다

화면에 뜨는 트렌드 키워드 28개는 **`v1-trend-incubator.html` 안에 자바스크립트 배열로 통째로 박혀있습니다**
(`RISING_KEYWORDS`). 백엔드도 **똑같은 내용을 JSON으로 따로 가지고 있습니다**
(`app/trends/fixtures/rising_keywords_28.json`) — 아이디어 생성 시 키워드 정보를 조회할 때만 씁니다.

**이 둘은 사람이 직접 동기화해야 합니다.** 한쪽만 고치면, 그 키워드로 아이디어 생성을 눌렀을 때
`KeywordNotFound`가 납니다. 나중에 실제 네이버·유튜브·스레드 수집을 붙일 때
이 이중 구조부터 정리하는 게 먼저입니다.

### ② `GET /api/trends`는 아무도 안 부릅니다

서버 코드는 멀쩡히 동작하지만, 프론트가 이 API를 **한 번도 fetch하지 않습니다.**
화면은 위 ①의 프론트 내장 배열만 봅니다. 죽은 코드는 아니고(호출하면 응답함),
**연결이 끊긴 채로 방치된 상태**입니다.

### ③ Supabase 없이도 앱은 돌아갑니다

`.env`의 `AUTH_ENABLED=false`(기본값)면 로그인·보관함·새로고침 제한 기능만 안 보이고,
아이디어 생성 자체는 익명으로 정상 동작합니다. 로컬에서 빨리 확인하고 싶을 때 유용합니다.

---

## 4. 로컬에서 돌려보기

```bash
cd Final/Backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt     # PyJWT[crypto] 포함, 반드시 재설치

python -m app.trends.build_snapshot               # fixtures → data/trends/latest_snapshot.json
                                                    # (없으면 /api/trends가 503)

uvicorn main:app --reload                          # http://localhost:8000
```

Supabase까지 켜려면 `.env.example`을 `.env`로 복사해 Supabase 키 3개를 채우고
`AUTH_ENABLED=true`로 바꾼 뒤, `db/001_auth_library_quota.sql`을 Supabase SQL Editor에서 한 번 실행합니다.

---

## 5. 배포

`deploy` 브랜치에 push하면 Vercel이 자동으로 재배포합니다. 진입점은 저장소 최상위 `index.py`
(→ 이 폴더의 `Backend/main.py`를 불러옴)이고, 루트 `requirements.txt`(Vercel 전용, 이 폴더의
`requirements.txt`와 별개)를 따로 관리해야 합니다 — 잊으면 로컬은 되는데 배포에서만 터집니다.
