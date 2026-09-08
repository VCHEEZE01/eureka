# 유레카 — 공용 뼈대 구조

**팀 목욕중** · 개발 착수 전 공통 인식용

> **이 폴더에는 실제 동작 코드가 없습니다.**
> "우리가 이렇게 나눠서 만들기로 했다"는 **구조와 약속**만 들어 있습니다.
> 각자 자기 파일을 채우면 이 구조 안에서 합쳐집니다.

---

## 1. 기술 스택

| 영역 | 결정 |
| :-- | :-- |
| **Frontend** | Next.js 16 · React 19 · TypeScript · Tailwind 4 |
| **Backend** | Python 3.11 · FastAPI · Pydantic 2 |
| **에이전트** | LangGraph |
| **공유용 배포** | esbuild 단일 HTML (서버 없이 열림) |

**프론트와 백엔드는 완전히 분리된 두 프로그램입니다.** HTTP로만 대화합니다.

```
Frontend :3000  ─── HTTP ───▶  Backend :8000
(화면)                          (데이터 · AI 판단)
```

---

## 2. 이 구조가 의미하는 것 — 경계선 3개

**뼈대는 경계선 3개로 이루어져 있습니다.** 각 경계선은
**"이쪽이 바뀌어도 저쪽은 안 바뀌게"** 하려고 그은 것입니다.
그래야 여러 명이 동시에 작업할 수 있습니다.

### ① 화면 ↔ 데이터

```
screens/          화면. 데이터가 어디서 오는지 모른다
   ↓
api/client.ts     ★ 경계선 — 백엔드와 대화하는 유일한 곳
   ↓ HTTP
Backend/app/api/
```

**의미:** 화면은 `client.ts` 하나만 보고 일합니다.
백엔드 주소가 바뀌든 인증이 붙든 **화면 코드는 안 바뀝니다.**

### ② 판단 ↔ 바깥세상

```
agents/           AI가 판단하는 곳. 바깥을 모른다
   ↓
tools/            ★ 경계선 — 바깥과 대화하는 유일한 곳
   ↓
네이버 API · 카카오 API · DB · LLM
```

**의미:** 에이전트는 "네이버를 어떻게 부르는지" 모릅니다. `search_tool.search()` 만 압니다.
→ 테스트할 때 진짜 API를 안 부릅니다. API 키가 한 곳에만 있습니다.

### ③ 미리 만드는 것 ↔ 지금 만드는 것

```
[배치]    scripts/run_pipeline.py   스케줄러가 돌림 · 사용자와 무관
             ↓ 문제 풀을 채움
[실시간]  main.py (FastAPI)         사용자가 누를 때 반응
```

**의미:** 서로 다른 프로그램입니다. 같이 안 죽습니다.
→ 밤새 수집이 실패해도 **사용자는 문제없이 서비스를 씁니다.**

---

## 3. 에이전트 4개

```
   ① 수집 에이전트          인터넷에서 사람들 불평 긁어오기
          ↓
   ② 해석기                 비슷한 것끼리 묶어서 "문제 후보"로
          ↓
   ③ 문제정의 생성기   ←──  기존 문제 2~3개   (선택 입력)
          ↓
   ④ 아이디어 생성기   ←──  사용자 조건       (선택 입력)
          ↓
        결과
```

**기능은 8개(F00~F07)인데 에이전트는 4개입니다.**
오른쪽 화살표 두 개가 그 이유입니다.

| 옆에서 넣는 것 | 그러면 | 새 에이전트? |
| :-- | :-- | :-- |
| 아무것도 안 넣음 | 기본 문제 · 기본 아이디어 | — |
| **기존 문제 2~3개** | **문제 조합** (F05) | ❌ ③ 재사용 |
| **사용자 조건** | **개인화** (F07) | ❌ ④ 재사용 |

조합과 개인화는 새로 만드는 게 아니라 **입력을 하나 더 끼우는 것**입니다.

**앞 둘과 뒤 둘의 성격도 다릅니다.**

```
①② = 재료 만들기 → 미리 돌려둠 (배치)
③④ = 결과 만들기 → 사용자가 누를 때도 돎 (실시간)
```

---

## 4. 폴더 구조

```
Final/
│
├─ Backend/                        Python · FastAPI
│  ├─ main.py                      FastAPI 서버 진입점
│  ├─ requirements.txt             설치할 패키지
│  ├─ .env.example                 API 키 양식 (.env 로 복사해서 채울 것)
│  ├─ scripts/run_pipeline.py      전체 흐름 실행 · 확인용
│  ├─ tests/                       테스트
│  │
│  └─ app/
│     ├─ schemas/models.py         ★★ 계약 — 모든 데이터의 모양
│     │
│     ├─ agents/                   AI가 "판단"하는 곳
│     │  ├─ base.py                   공통 인터페이스. run() 만 구현
│     │  ├─ collector_agent.py      ① 수집
│     │  ├─ interpreter_agent.py    ② 해석기
│     │  ├─ problem_agent.py        ③ 문제정의 생성기
│     │  └─ idea_agent.py           ④ 아이디어 생성기
│     │
│     ├─ tools/                    ★ 바깥과 대화하는 곳
│     │  ├─ search_tool.py            네이버·카카오 API
│     │  ├─ cluster_tool.py           묶기 계산
│     │  ├─ llm_tool.py               LLM 호출
│     │  └─ db_tool.py                저장·조회·숫자 집계
│     │
│     ├─ prompts/                  AI에게 줄 "말"
│     │  └─ common_prompts.py         모두가 상속하는 금지 규칙
│     │
│     ├─ graph/pipeline.py         에이전트를 잇는 "순서"
│     ├─ api/routes.py             프론트가 부르는 입구
│     ├─ core/                     LLM·DB 연결
│     └─ config/                   설정 읽기
│
└─ Frontend/                       Next.js · React · TypeScript
   ├─ package.json                 npm 스크립트 (dev · build · build:single)
   ├─ .env.example                 백엔드 주소 양식
   ├─ scripts/build-single.mjs     단일 HTML 생성
   │
   └─ src/
      ├─ api/
      │  ├─ types.ts               ★★ 계약 — 백엔드 models.py 와 1:1
      │  └─ client.ts              ★ 백엔드 호출. 화면은 여기만 씀
      │
      ├─ hooks/useAgentStream.ts   진행 상태 받아 화면에 그리기
      │
      ├─ screens/                  화면 9개 (PRD 기능과 1:1)
      ├─ components/               공용 UI · 진행 상태 표시
      ├─ app/                      Next.js 라우트 13개 (screens 를 감싸는 껍데기)
      ├─ data/mock.ts              가상 데이터
      ├─ single/entry.tsx          공유용 단일 HTML 진입점
      └─ lib/                      라우팅 · 저장 상태 · 내부 타입
```

---

## 5. 누가 어디를 채우나

**서로 다른 파일을 만지므로 충돌이 안 납니다.**

| 담당 | 채울 파일 |
| :-- | :-- |
| **프론트엔드** | `Frontend/src/api/client.ts` · `hooks/useAgentStream.ts` |
| **① 수집** | `agents/collector_agent.py` · `tools/search_tool.py` |
| **② 해석기** | `agents/interpreter_agent.py` · `tools/cluster_tool.py` |
| **③ 문제정의** | `agents/problem_agent.py` · `tools/db_tool.py` |
| **④ 아이디어** | `agents/idea_agent.py` |

**공유 파일은 셋뿐입니다.**

| 파일 | 규칙 |
| :-- | :-- |
| `Backend/app/schemas/models.py` | 바꾸려면 팀에 알릴 것 |
| `Frontend/src/api/types.ts` | 위와 **항상 같이** 바꿀 것 |
| `Backend/app/tools/llm_tool.py` | 각자 **자기 함수만** 채울 것 |

---

## 6. 모두가 지킬 규칙 5개

| # | 규칙 | 안 지키면 |
| :-- | :-- | :-- |
| ① | 화면은 `api/client.ts` 만 쓴다 | 주소 바뀔 때 화면을 다 고쳐야 함 |
| ② | 에이전트는 `tools/` 만 쓴다 | 테스트마다 진짜 API를 부름 · 키가 흩어짐 |
| ③ | 프롬프트는 `prompts/` 에 둔다 | 문구 고치려고 파일 여러 개를 뒤짐 |
| ④ | `models.py` 와 `types.ts` 는 같이 바꾼다 | 런타임에 조용히 깨짐 |
| ⑤ | **숫자는 LLM이 만들지 않는다** | **서비스 존재 이유가 무너짐** |

### ⑤번이 제일 중요합니다

"사례 137건"이 가짜면 유레카가 성립하지 않습니다.
그래서 **LLM이 채우는 모델에는 숫자 필드를 아예 두지 않았습니다.**

```python
class ProblemDraft(BaseModel):   # LLM이 채움
    title: str
    evidence: list[Evidence]
    # 숫자 필드 없음 ← 의도된 것

class Problem(BaseModel):        # DB가 채움
    case_count: int              # raw_items 를 센 값
    source_count: int            # 서로 다른 출처를 센 값
```

**지어낼 자리를 없애는 방식입니다.** 이 구조를 깨지 마세요.

---

## 7. 에이전트 구현하는 법

`base.py` 를 상속하고 `run()` 하나만 채우면 됩니다.

```python
class CollectorAgent(Agent[CollectInput, list[RawItem]]):
    name = "수집 에이전트"
    steps = ["검색어 만들기", "원문 긁어오기", "정리"]   # 화면에 뜨는 단계

    def run(self, data: CollectInput) -> list[RawItem]:
        self.report(0)              # 1단계 시작 알림
        ...
        self.report(0, done=True)   # 1단계 완료 알림
        return items
```

`steps` 와 `report()` 가 **화면의 진행 상태 UI로 그대로 연결됩니다.**

```
Backend   agent.report(0)
   ↓  ProgressEvent (HTTP)
Frontend  useAgentStream()
   ↓
화면      [1/3] 검색어 만들기 … 완료
```

---

## 8. 실행

```bash
# 백엔드
cd Final/Backend
pip install -r requirements.txt
python scripts/run_pipeline.py      # 지금은 "미구현" 이 정상입니다
uvicorn main:app --reload

# 프론트엔드
cd Final/Frontend
npm install
npm run dev                         # 지금은 빈 화면이 정상입니다
```

**둘 다 지금은 아무것도 안 나옵니다.** 뼈대만 있고 내용이 없으니까요.
각자 자기 파일을 채우면 그 부분부터 살아납니다.

---

## 9. 참고

기획과 설계 배경은 `TAEYUN/` 폴더에 있습니다.

| 파일 | 내용 |
| :-- | :-- |
| `TAEYUN/eureka-공유용.html` | 화면 프로토타입 — **더블클릭** |
| `TAEYUN/에이전트_흐름도.html` | 이 구조가 나온 배경 — **더블클릭** |
| `TAEYUN/Eureka_PRD_v2.md` | 기능 정의서 (F00~F10) |
