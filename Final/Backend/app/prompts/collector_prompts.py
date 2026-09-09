"""
collector_prompts — ① 수집 에이전트가 쓰는 프롬프트.

여기 있는 것: SUGGEST_DOMAIN_KEYWORDS (도메인 키워드 후보 제안)

★ 배치가 실제로 던지는 검색어는 LLM 이 만들지 않는다.
  app/config/dictionaries.py 의 사전을 전부 순회해서 조합으로 만든다
  (docs/DATA_COLLECTION.md). 매주 같은 검색어가 나와야 주 단위 비교가
  되고, 모델이 흔들리면 수집량이 통째로 달라지기 때문이다.

  이 프롬프트는 사람이 사전을 넓힐 때 참고하는 용도다.
  결과를 그대로 검색에 쓰지 말고, 사람이 골라서 dictionaries.py 에 넣어라.

★ 치환은 str.replace("{category}", ...) / str.replace("{existing}", ...) 로 하라.
  프롬프트 안에 JSON 예시의 중괄호가 있어서 str.format() 을 쓰면 깨진다.
  아래 suggest_keywords_prompt() 를 쓰면 신경 쓸 필요 없다.
"""

from app.prompts.common_prompts import with_rules

SUGGEST_DOMAIN_KEYWORDS = with_rules("""
너는 "{category}" 분야에서 사람들이 불편을 털어놓을 만한 글을 찾으려 한다.
그 글을 검색으로 건지기 위한 도메인 키워드 후보를 제안하라.

## 조건
· 명사 또는 짧은 명사구로 하라. 문장·질문 형태로 쓰지 마라.
· 검색창에 그대로 넣어 쓸 수 있어야 한다.
· 브랜드명·회사명·제품명은 넣지 마라. 특정 회사 글만 걸리면 편향된다.
· 아래 "이미 쓰는 키워드"와 같거나 사실상 같은 말은 내지 마라.
· 서로 다른 상황을 덮도록 하라. 비슷한 말을 여러 개 내지 마라.
· 너무 넓은 말(예: "생활", "서비스")은 쓸모가 없다. 무엇에 관한 것인지
  알아볼 수 있을 만큼 좁혀라.
· reason 에는 이 분야의 어떤 상황을 건지려는 것인지 한 문장으로 써라.

## 이미 쓰는 키워드
{existing}

## 출력 형식
설명·코드블록 표시 없이 JSON 배열만 출력하라. 최대 10개.
[
  {"keyword": "...", "reason": "..."}
]
""")


def suggest_keywords_prompt(category: str, existing: list[str] | str) -> str:
    """SUGGEST_DOMAIN_KEYWORDS 의 자리표시자를 채운다."""
    joined = existing if isinstance(existing, str) else ", ".join(existing)
    return SUGGEST_DOMAIN_KEYWORDS.replace("{category}", category).replace(
        "{existing}", joined or "(없음)"
    )
