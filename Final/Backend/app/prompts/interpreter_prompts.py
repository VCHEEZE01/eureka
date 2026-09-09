"""
interpreter_prompts — ② 해석기가 쓰는 프롬프트.

여기 있는 것: JUDGE_PAINS (긁어온 글이 '진짜 불편'인지 판별)

★ 치환은 str.replace("{items}", ...) 로 하라.
  프롬프트 안에 JSON 예시의 중괄호가 있어서 str.format() 을 쓰면 깨진다.
  아래 judge_pains_prompt() 를 쓰면 신경 쓸 필요 없다.

★ 판정 결과의 severity·has_need_signal 은 화면의 "불만도"·"필요도"의 재료다
  (docs/DATA_SPEC.md 4절). 숫자가 아니라 라벨을 받고, 점수는 ③이 이 라벨을
  세서 만든다. 그래서 여기서 모델에게 점수를 물어보지 않는다.
"""

from app.prompts.common_prompts import with_rules

JUDGE_PAINS = with_rules("""
너는 사람들이 인터넷에 쓴 글을 읽고, 그 글이 "글쓴이가 실제로 겪는 불편을
말하는 글"인지 판별하는 사람이다.

아래 JSON 배열의 각 항목(id·title·text·source)을 하나씩 판정하라.

## 불편이 아닌 것 (is_pain=false)
· 광고·홍보·협찬 글, 마케팅용 후기
· 사실만 전하는 정보 전달 글(뉴스 요약, 공지, 안내)
· 감상·잡담·후기 중 불편이 없는 것
· 반어법 — "짜증나게 재밌다", "미치도록 좋다" 처럼 부정 단어를 쓰지만
  실제로는 만족을 말하는 글
· 대상이 불분명한 막연한 불평 — "그냥 다 짜증난다", "요즘 세상 왜 이래"
  이때는 confidence 를 "낮음" 으로 하라
· 남의 불편을 전하기만 하고 글쓴이 자신은 겪지 않은 글

## 불편인 것 (is_pain=true)
· 무엇을 하려다 무엇 때문에 막혔는지가 읽히는 글
· 반복해서 손이 가거나, 시간·돈·감정을 쓰게 만드는 상황을 말하는 글
· 질문 형태여도 그 뒤에 실제 불편이 있으면 불편으로 본다

## 각 필드를 채우는 법
· pain_summary — 누가·언제·무엇 때문에 불편한지 한 문장.
  80자 이내. 원문 문장을 그대로 옮기지 말고 네 말로 다시 써라.
  is_pain 이 false 면 null.
· confidence — 이 판정이 얼마나 확실한가. "높음" | "중간" | "낮음" 중 하나.
· severity — 불편의 강도. "높음" | "중간" | "낮음" 중 하나.
  ★ confidence 와 다른 것이다. 확신도가 아니라 얼마나 괴로운가다.
    "높음"은 돈·시간을 크게 잃거나 일이 아예 막히는 경우,
    "낮음"은 조금 성가신 정도. is_pain 이 false 면 null.
· has_need_signal — 해결책을 원하는 표현이 있으면 true.
  예: "있었으면 좋겠다", "아쉽다", "없어서 불편하다", "개선됐으면",
      "왜 이런 기능이 없지", "대안 없나요"
  단순히 화만 내고 해결책을 바라는 표현이 없으면 false.

## 지킬 것
· 입력의 모든 id 에 대해 정확히 하나씩 판정하라.
· 입력에 없는 id 를 만들지 마라. 순서는 입력과 같게 하라.
· confidence 와 severity 는 "높음" | "중간" | "낮음" 이외의 값을 쓰지 마라.
· 설명·인사말·코드블록 표시 없이 JSON 배열만 출력하라.

## 출력 형식
[
  {"id": "...", "is_pain": true, "pain_summary": "...", "confidence": "높음",
   "severity": "중간", "has_need_signal": false},
  {"id": "...", "is_pain": false, "pain_summary": null, "confidence": "높음",
   "severity": null, "has_need_signal": false}
]

## 입력
{items}
""")


def judge_pains_prompt(items_json: str) -> str:
    """JUDGE_PAINS 의 {items} 자리에 입력 JSON 배열을 끼운다."""
    return JUDGE_PAINS.replace("{items}", items_json)
