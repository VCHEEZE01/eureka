"""
interpreter_prompts — ② 해석기가 쓰는 프롬프트.

여기 있는 것: JUDGE_PAINS (긁어온 글이 '진짜 불편'인지 판별)

★ 치환은 str.replace("{items}", ...) 로 하라.
  프롬프트 안에 JSON 예시의 중괄호가 있어서 str.format() 을 쓰면 깨진다.
  아래 judge_pains_prompt() 를 쓰면 신경 쓸 필요 없다.
  같은 이유로 sufferer_role 등의 고정 목록도 f-string 이 아니라 str.replace 로
  끼워 넣는다 (_ROLES_TOKEN 등 아래 상수 참고).

★ 판정 결과의 severity·has_need_signal 은 화면의 "불만도"·"필요도"의 재료다
  (docs/DATA_SPEC.md 4절). 숫자가 아니라 라벨을 받고, 점수는 ③이 이 라벨을
  세서 만든다. 그래서 여기서 모델에게 점수를 물어보지 않는다.

★ sufferer_role·sufferer_age_band·sufferer_gender·mentioned_service 는
  2026-09-11 계약 변경으로 추가된 근거 상세 페이지용 라벨이다. 모델이 준 값은
  llm_tool._clean_role 등이 규칙으로 한 번 더 검증한다(고정 목록 밖의 값·
  원문에 없는 서비스명·자기 서술 없는 성별은 여기서 프롬프트로 막아도
  llm_tool 이 규칙으로 다시 거른다 — 이중 방어).
"""

import json

from app.prompts.common_prompts import with_rules
from app.schemas.models import AGE_BANDS, GENDER_SELF_MENTION_WORDS, GENDERS, SUFFERER_ROLES

# 프롬프트 안의 고정 목록은 models.py 를 정본으로 삼아 여기서 조립한다.
# 손으로 다시 타이핑하면 SUFFERER_ROLES 등이 바뀔 때 프롬프트가 조용히 낡는다.
_roles_text = " | ".join(SUFFERER_ROLES)
_age_bands_text = " | ".join(AGE_BANDS)
_genders_text = " | ".join(GENDERS)
_gender_words_text = "·".join(GENDER_SELF_MENTION_WORDS)

_judge_pains_raw = """
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

## 먼저 확인할 것: 실제 경험인가, 설명을 위한 예시인가
· 제목과 text를 함께 읽고 글의 목적을 먼저 구분하라. 불편한 상황을 묘사했다는
  사실만으로 is_pain=true가 되지는 않는다. 광고·홍보·사용법 안내가 독자의
  공감을 얻으려고 제시한 불편 예시는 실제 사례로 세지 않는다.
· "이런 적 없으신가요?", "누구나 겪어봤을", "~한다면" 같은 독자 대상 질문,
  가정, 일반론만 있고 글쓴이의 실제 사건이 없으면 is_pain=false다.
· 제목이 가이드·추천·사용법인 것만으로 무조건 제외하지는 마라. 다만 제목과
  스니펫 안에 글쓴이가 직접 겪은 구체적 상황과 막힌 지점이 확인되어야 한다.
  한국어에서 '저는'이 생략되어도 실제 경험이 읽히면 인정한다.
· "나도 써봤다" 같은 일인칭 표현이 있어도 상품 구매·강의 신청을 권하는
  마케팅용 후기라면 위의 광고·홍보 제외 기준을 우선한다.
· 잘린 스니펫의 뒷부분을 상상하거나, 제목의 대상 독자를 글쓴이의 신분으로
  바꾸지 마라. 실제 경험 여부를 판단할 정보가 부족하면 is_pain=false,
  confidence="낮음", pain_summary=null로 남긴다.
· 요약에 원문에 없는 감정·직업·실패 결과를 보태지 마라. 양식을 물어봤다는
  사실이 곧 '당황했다'거나 '작성법을 몰랐다'는 뜻은 아니다.

예시 (표현을 외우지 말고 실제 경험과 가정의 차이를 적용하라):
· "매달 영수증 정리가 막막하신가요? 이 앱을 구매하세요" → false (상품 홍보)
· "파일 검색이 힘들다면 폴더 이름을 바꿔보세요" → false (일반적인 안내)
· "어제 정산하다 영수증 파일을 못 찾아서 한 시간 동안 폴더를 뒤졌다"
  → true (글쓴이의 구체적인 사건과 불편)
· "자료를 찾으려고 폴더를 여러 겹 만들었다. 그런데..."
  → false, confidence="낮음" (잘린 뒤의 불편은 확인할 수 없음)

## 판단 결과와 경험자 분리
· pain_status = "pain"(구체적 자기 불편), "not_pain"(충분한 문맥에서 불편 없음),
  "insufficient"(잘린 근거·질문/답변 혼합·경험자 불명) 중 하나다.
  광고·정보·타인 사례는 not_pain이며, 정보 부족을 불편 없음으로 부르지 마라.
· 불편/짜증 같은 단어가 없어도 구체적인 행동, 막힘, 반복 수작업, 시간·비용 손실을 판별하라.
· experience_type = self | other | mixed | unknown. 지식iN 검색 요약은 질문과 답변을
  섞어 보여줄 수 있다. 분리된 원문이 없고 화자가 바뀌면 mixed, pain_status=insufficient.
  답변자의 공감·조언·예시를 질문자가 직접 말했다고 옮기지 마라.
· experience_evidence: 동일한 글쓴이의 경험을 확인할 원문 구절 그대로, 최대 300자.
  근거가 없으면 null. assessment_reason에는 판정 이유를 짧게 쓴다.
· 의료 증상 자체·진단 질문은 서비스 불편과 구분하고 not_pain으로 두되 사유에
  증상/진단 질문이라고 명시한다. 예약 실패·서류 재제출·정보 전달 장애가 실제로
  읽힐 때만 해당 서비스 불편으로 판단한다. 질환으로부터 서비스 불편을 상상하지 마라.

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

## 근거 상세 페이지용 라벨 (전부 확실하지 않으면 null — 지어내지 마라)
· sufferer_role — 글쓴이가 스스로 밝힌 역할. 다음 중 하나만 써라:
    {sufferer_roles}
  원문에 역할을 알 만한 표현이 없으면 null.
· sufferer_age_band — 글쓴이가 나이대를 직접 밝힌 경우에만("30대인데",
  "20대 후반이라" 등). 다음 중 하나: {age_bands}
  ★ 문체·관심사로 나이를 짐작하지 마라. 직접 밝히지 않았으면 null.
· sufferer_gender — 글쓴이가 성별을 직접 밝힌 경우에만 채워라.
  다음 중 하나: {genders}
  자기 서술로 볼 수 있는 표현의 예: {gender_words}
  ★★ 직업·말투·문체로 성별을 추측하지 마라. 그것은 편견이다.
    예: "간호사인데 매번 번거로워요" 는 직업만 밝혔을 뿐 성별을 밝히지
    않았다 — 이 글의 sufferer_gender 는 반드시 null 이다.
    "간호사 = 여자", "군인 = 남자" 처럼 직업으로 성별을 넘겨짚지 마라.
  원문에 위 같은 자기 서술 표현이 전혀 없으면 무조건 null.
· mentioned_service — 원문에 함께 언급된 기존 서비스·앱·브랜드 이름.
  ★ 원문에 글자 그대로(verbatim) 등장하는 이름만 써라.
    지어내거나 "아마 이런 서비스일 것"이라고 짐작한 이름을 쓰면 안 된다.
  언급이 없으면 null.

## 타겟 확인 (target_profile이 주어질 때)
{target_profile}
· 검색어에 들어 있다는 사실은 타겟 근거가 아니다. 입력된 각 필드를 같은 경험자에 대해
  확인하라. 나이·성별은 명시적 자기 서술만 인정하며 문체·직업·남자친구·오빠로 추정 금지.
· jobs/places의 복수 값은 같은 필드 안에서 OR, 입력한 서로 다른 필드끼리는 AND다.
  직업은 경험자의 실제 역할, 장소는 그 불편을 겪는 활동 장소다. 집=거주지 추정 금지.
· target_field_status: 입력된 age/gender/jobs/places별 confirmed | unconfirmed | conflict.
  target_values: 원문에서 확인한 값. target_evidence: 그 값이 동일 경험자를 설명하는
  원문 구절 그대로. 모든 target_evidence는 experience_evidence 안에 실제로 있어야 한다.
  나이 값은 명시된 23살→20대, 60대→50대 이상처럼 범주로 정규화하고 근거 구절은 원문 그대로 둔다.
  단어만 떼어 적지 말고 '저는 20대 남자이고...'처럼 누구의 말인지 알 수 있게 적어라.
· 다른 사람의 나이·성별, 뉴스 통계, 답변 속 가정은 unconfirmed다.
  '저는 20대'가 확인되고 입력은 30대일 때만 age=conflict다. 직업·장소가 안 보이면
  conflict가 아니라 unconfirmed다. 새 동의어/연관 직무를 임의로 동일 직업으로 확정하지 마라.
· 불편이 맞아도 타겟을 확인하지 못하면 is_pain=true를 유지하고 target은 unconfirmed로
  남겨라. 타겟 미확인은 '불편 없음'이 아니다. Q&A 혼합은 경험부터 insufficient로 보류한다.

## 지킬 것
· 입력의 모든 id 에 대해 정확히 하나씩 판정하라.
· 입력에 없는 id 를 만들지 마라. 순서는 입력과 같게 하라.
· confidence 와 severity 는 "높음" | "중간" | "낮음" 이외의 값을 쓰지 마라.
· sufferer_role·sufferer_age_band·sufferer_gender 는 위에 제시한 고정 목록
  밖의 값을 쓰지 마라. 확실하지 않으면 반드시 null 이다.
· 설명·인사말·코드블록 표시 없이 JSON 배열만 출력하라.

## 출력 형식
[
  {"id": "...", "is_pain": true, "pain_summary": "...", "confidence": "높음",
   "severity": "중간", "has_need_signal": false,
   "sufferer_role": null, "sufferer_age_band": null, "sufferer_gender": null,
   "mentioned_service": null, "pain_status": "pain", "assessment_reason": "판정 이유",
   "experience_type": "self", "experience_evidence": "입력에서 가져온 동일 경험자의 구절",
   "target_field_status": {}, "target_values": {}, "target_evidence": {}},
  {"id": "...", "is_pain": false, "pain_summary": null, "confidence": "높음",
   "severity": null, "has_need_signal": false,
   "sufferer_role": null, "sufferer_age_band": null, "sufferer_gender": null,
   "mentioned_service": null, "pain_status": "insufficient", "assessment_reason": "근거 확인 필요",
   "experience_type": "unknown", "experience_evidence": null,
   "target_field_status": {}, "target_values": {}, "target_evidence": {}}
]

## 입력
{items}
"""

JUDGE_PAINS = with_rules(
    _judge_pains_raw.replace("{sufferer_roles}", _roles_text)
    .replace("{age_bands}", _age_bands_text)
    .replace("{genders}", _genders_text)
    .replace("{gender_words}", _gender_words_text)
)


def judge_pains_prompt(items_json: str, target_profile=None) -> str:
    """JUDGE_PAINS 의 {items} 자리에 입력 JSON 배열을 끼운다."""
    target = target_profile.model_dump() if target_profile is not None else None
    return JUDGE_PAINS.replace("{items}", items_json).replace("{target_profile}", json.dumps(target, ensure_ascii=False))
