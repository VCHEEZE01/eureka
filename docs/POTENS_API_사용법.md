# Potens API 사용법

이 문서는 현재 프로젝트에서 **Potens API를 Python 백엔드에서 호출하기 위한 최소 사용법**을 정리한 문서입니다.

현재 사용 범위는 **일반 응답 방식인 `/api/chat`** 입니다.

---

## 1. API Key 저장

실제 API Key는 Python 코드에 직접 작성하지 않고 `.env` 파일에 저장합니다.

```env
POTENS_API_KEY=실제_API_KEY
POTENS_BASE_URL=https://ai.potens.ai
```

예:

```env
POTENS_API_KEY=sk-xxxxxxxxxxxxxxxx
POTENS_BASE_URL=https://ai.potens.ai
```

`Bearer`라는 문자열은 `.env`에 넣지 않습니다.

잘못된 예:

```env
POTENS_API_KEY=Bearer sk-xxxxxxxx
```

올바른 예:

```env
POTENS_API_KEY=sk-xxxxxxxx
```

그리고 `.gitignore`에는 반드시 다음을 포함합니다.

```gitignore
.env
```

---

## 2. Potens API 기본 구조

사용할 Endpoint:

```text
POST https://ai.potens.ai/api/chat
```

Potens API는 요청 Header의 `Authorization`에 API Key를 넣어 인증합니다.

```text
Authorization: Bearer <API_KEY>
```

즉 Python 코드에서는 다음처럼 만들어집니다.

```python
headers = {
    "Authorization": f"Bearer {POTENS_API_KEY}",
    "Content-Type": "application/json",
}
```

---

## 3. 요청 데이터

기본 요청 Body:

```json
{
  "prompt": "안녕",
  "model": "claude-4-6-sonnet"
}
```

### prompt

AI 모델에게 전달할 실제 요청 내용입니다.

예:

```json
{
  "prompt": "이 데이터를 분석하고 핵심 문제를 3개 도출해줘.",
  "model": "claude-4-6-sonnet"
}
```

### model

Potens를 통해 사용할 모델 이름입니다. 요청 본문의 `model` 필드로 지정합니다.

| 포텐스닷 화면 이름 | API `model` 값 | 비고 |
| --- | --- | --- |
| Claude Sonnet 4.6 | `claude-4-6-sonnet` | 기본 모델. 이 프로젝트의 기본값(`POTENS_MODEL`) |
| Claude Sonnet 5 | `claude-5-sonnet` | |
| Claude Sonnet 4.5 | `claude-4-5-sonnet` | |
| Claude Haiku 4.5 | `claude-4-5-haiku` | 이번 확인에서 가장 빨랐음 |
| Claude Opus 4.8 | `claude-4-8-opus` | |
| Claude Opus 5 | `claude-5-opus` | |

6개 모두 2026-09-13에 실제 호출이 성공했습니다(자세한 기록은 11절).

> **주의: 모델 이름을 틀려도 오류가 나지 않습니다.** 없는 이름(`claude-9-9-notreal`, `totally-unknown-model`)이나 오타(`claude-4-6-sonet`)를 보내도 정상 응답(200)이 오고, 결과가 기본 모델 `claude-4-6-sonnet`과 글자까지 똑같았습니다. 오타가 나면 **조용히 기본 모델로 바뀌므로** 위 표의 이름을 그대로 복사해 쓰세요. 응답에는 실제로 사용된 모델 이름이 들어 있지 않습니다.

---

## 4. Python에서 호출

필요 패키지:

```bash
pip install requests python-dotenv
```

환경변수 불러오기:

```python
import os
from dotenv import load_dotenv

load_dotenv()

POTENS_API_KEY = os.getenv("POTENS_API_KEY")
POTENS_BASE_URL = os.getenv(
    "POTENS_BASE_URL",
    "https://ai.potens.ai"
)
```

기본 호출 함수:

```python
import requests

def call_potens(
    prompt: str,
    model: str = "claude-4-6-sonnet"
) -> dict:

    response = requests.post(
        f"{POTENS_BASE_URL}/api/chat",
        headers={
            "Authorization": f"Bearer {POTENS_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "prompt": prompt,
            "model": model,
        },
        timeout=120,
    )

    response.raise_for_status()

    return response.json()
```

사용 예시:

```python
result = call_potens(
    "현재 수집된 데이터를 바탕으로 핵심 문제를 분석해줘."
)

print(result)
```

---

## 5. 응답

제공받은 Potens 예시에 따르면 응답은 다음과 같은 JSON 형태입니다.

```json
{
  "message": "...",
  "token_usage": "..."
}
```

AI가 생성한 본문만 사용하려면:

```python
result = call_potens("안녕")

answer = result["message"]

print(answer)
```

---

## 6. 프로젝트에서의 동작 흐름

전체 흐름은 다음과 같습니다.

```text
.env
 │
 │ POTENS_API_KEY
 ▼
Python Backend
 │
 │ Authorization: Bearer <API_KEY>
 │ prompt
 │ model
 ▼
Potens API
https://ai.potens.ai/api/chat
 │
 ▼
선택한 AI Model
 │
 ▼
JSON 응답
{
  "message": "...",
  "token_usage": "..."
}
```

`.env`는 API Key를 **저장하는 장소**이고,

`potens_client.py` 같은 Python 코드는 그 API Key를 읽어 실제 Potens API에 요청을 보내는 역할을 합니다.

---

## 7. Agent에서 사용할 경우

예를 들어 문제정의 Agent가 있다면:

```python
def generate_problem_definition(
    collected_data: str,
    analysis_result: str
):

    prompt = f'''
    아래 수집 데이터와 분석 결과를 바탕으로
    사용자에게 제공할 문제정의를 작성해줘.

    [수집 데이터]
    {collected_data}

    [분석 결과]
    {analysis_result}
    '''

    result = call_potens(prompt)

    return result["message"]
```

흐름:

```text
데이터 수집 Agent
        ↓
데이터 분석 Agent
        ↓
문제정의 Agent
        ↓
call_potens()
        ↓
Potens API
        ↓
AI 응답
```

이렇게 하면 여러 Agent가 동일한 `call_potens()` 함수를 재사용할 수 있습니다.

---

## 8. `/api/chat`과 `/api/chat-stream`

Potens에는 두 가지 응답 방식이 있습니다.

### `/api/chat`

```text
요청
↓
AI 응답 생성 완료
↓
완성된 JSON 한 번에 반환
```

현재 프로젝트에서는 이 방식을 사용합니다.

Endpoint:

```text
POST /api/chat
```

### `/api/chat-stream`

```text
요청
↓
AI가 생성하는 내용을
조금씩 실시간으로 반환
```

ChatGPT처럼 답변이 실시간으로 나타나는 화면을 만들 때 사용할 수 있습니다.

현재 프로젝트에서는 사용하지 않습니다.

---

## 9. 권장 프로젝트 구조

예:

```text
backend/
├─ .env
├─ .env.example
├─ .gitignore
│
└─ app/
   ├─ core/
   │  └─ config.py
   │
   ├─ services/
   │  └─ potens_client.py
   │
   └─ agents/
      ├─ data_collection_agent.py
      ├─ data_analysis_agent.py
      └─ problem_definition_agent.py
```

예를 들어:

```text
problem_definition_agent.py
        ↓
potens_client.py
        ↓
Potens API
```

구조로 사용하는 것을 권장합니다.

기존 프로젝트에 이미 다른 폴더 구조가 있다면 현재 구조를 우선합니다.

---

## 10. 에러 처리

최소한 아래 처리를 권장합니다.

```python
import requests

try:
    response = requests.post(
        f"{POTENS_BASE_URL}/api/chat",
        headers={
            "Authorization": f"Bearer {POTENS_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "prompt": prompt,
            "model": model,
        },
        timeout=120,
    )

    response.raise_for_status()

except requests.Timeout:
    raise RuntimeError("Potens API 응답 시간이 초과되었습니다.")

except requests.RequestException as e:
    raise RuntimeError(
        f"Potens API 호출 중 오류가 발생했습니다: {e}"
    )
```

주의:

```python
print(POTENS_API_KEY)
```

처럼 API Key를 로그에 출력하면 안 됩니다.

---

## 11. 모델 호출 테스트 기록 (2026-09-13)

**방법:** 프로젝트의 `Backend/app/core/llm.py` `call_potens()`로 모델마다 같은 짧은 질문을 보냈습니다. 질문은 "연결 확인입니다. 한국어로 한 문장만 짧게 인사해 주세요."입니다. 코드와 `.env`는 바꾸지 않았습니다. (그 전에 조금 더 긴 질문으로도 6개 모두 1.5~3.7초에 성공했습니다.)

| model 값 | 결과 | 응답 시간 | 입력 토큰 | 출력 토큰 | token_usage 모양 | 답변 |
| --- | --- | --- | --- | --- | --- | --- |
| `claude-4-6-sonnet` | 성공 | 1.8초 | 1,041 | 37 | `cacheWriteInputTokens` 있음 | 안녕하세요! Potens.AI입니다. 무엇이든 도와드릴게요 😊 |
| `claude-5-sonnet` | 성공 | 2.1초 | 1,044 | 21 | `cacheWriteInputTokens` 없음 | 안녕하세요! 잘 연결되었습니다. |
| `claude-4-5-sonnet` | 성공(2회 같음) | 2.3~2.5초 | 1,040 | 34 | `cacheWriteInputTokens` 있음 | 안녕하세요, Potens.AI입니다. 무엇을 도와드릴까요? |
| `claude-4-5-haiku` | 성공 | 1.3초 | 1,040 | 34 | `cacheWriteInputTokens` 없음 | 안녕하세요, Potens.AI입니다. 무엇을 도와드릴까요? |
| `claude-4-8-opus` | 성공 | 1.7초 | 1,044 | 33 | `cacheWriteInputTokens` 없음 | 안녕하세요, Potens.AI입니다. 무엇을 도와드릴까요? |
| `claude-5-opus` | 성공 | 1.9초 | 37 + 캐시 저장 1,007 (합 1,044) | 33 | `cacheDetails` 포함 | 안녕하세요, Potens.AI입니다. 무엇을 도와드릴까요? |
| 없는 이름 3종 (`claude-9-9-notreal`, `totally-unknown-model`, `claude-4-6-sonet`) | **오류 없이 성공** | 1.7~2.6초 | 1,041 | 37 | `claude-4-6-sonnet`과 같음 | `claude-4-6-sonnet`과 글자까지 같음 |

**어떻게 "그 모델이 실제로 쓰였다"고 판단했나**

- 응답에 모델 이름이 없고, 모델에게 물어봐도 "Potens.AI입니다"라고만 답합니다(한 번은 "Claude 3.7 Sonnet"이라고 틀리게 말함). 그래서 자기소개로는 확인할 수 없습니다.
- 대신 **없는 이름과 비교**했습니다. 없는 이름 3종은 입력 토큰·출력·token_usage 모양이 기본 모델 `claude-4-6-sonnet`과 전부 같았습니다. 즉 모르는 이름은 기본 모델로 처리됩니다.
- 나머지 5개 이름은 입력 토큰 수, 답변, token_usage 모양 중 하나 이상이 기본 모델과 달랐습니다. 그래서 **이름을 인식해 다른 모델로 보냈다**고 판단했습니다.
- 같은 질문인데 입력 토큰 수가 모델 세대별로 1,040(4.5) / 1,041(4.6) / 1,044(4.8·5)로 갈렸습니다. 세대마다 글자를 토큰으로 세는 방식이 달라서 생긴 차이로 보입니다.

**한계**

- 같은 세대끼리(Sonnet 4.5와 Haiku 4.5, Opus 4.8과 Sonnet 5)는 입력 토큰 수가 같습니다. 그래서 token_usage 모양·답변·속도로만 구분했습니다. 문서에 모델 목록 조회 API가 없어서, 이것이 지금 확인할 수 있는 최선입니다.
- 질문은 수십 토큰인데 입력 토큰이 약 1,040개로 잡힙니다. Potens가 질문 앞에 기본 안내문을 붙이는 것으로 보이며, **짧은 질문도 최소 약 1,000토큰**이 쓰입니다.
- 인사 한 문장으로 연결만 확인했습니다. 긴 분석 작업에서 모델별 품질·속도·60초 제한(Step 9에서 확인한 504) 차이는 따로 비교해야 합니다.

---

## 핵심 요약

`.env`

```env
POTENS_API_KEY=실제키
```

Python:

```python
api_key = os.getenv("POTENS_API_KEY")
```

요청 Header:

```python
"Authorization": f"Bearer {api_key}"
```

요청 URL:

```text
https://ai.potens.ai/api/chat
```

요청 Body:

```json
{
  "prompt": "...",
  "model": "claude-4-6-sonnet"
}
```

사용 가능한 `model` 값(2026-09-13 호출 확인):

```text
claude-4-6-sonnet (기본), claude-5-sonnet, claude-4-5-sonnet,
claude-4-5-haiku, claude-4-8-opus, claude-5-opus
```

이름을 틀려도 오류 없이 기본 모델로 답하므로 오타에 주의합니다.

응답:

```json
{
  "message": "...",
  "token_usage": "..."
}
```

현재 프로젝트에서는 `/api/chat` 방식만 사용합니다.
