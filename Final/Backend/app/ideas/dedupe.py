"""
새로고침 결과가 "이름만 바뀐 재탕"인지 판정하는 유사도 가드.

exclude 프롬프트(app/prompts/idea_prompts.py 의 EXCLUDE_TEMPLATE)를 넣어도
LLM이 지침을 무시하고 사실상 같은 아이디어를 낼 수 있다. 여기서 이름을
정규화해 겹침을 세고, 너무 겹치면 idea_routes.py 가 새로고침을 "실패"로
처리해 쿼터를 반납하고 이전 세트를 돌려주게 한다.

★ 이 파일은 순수 함수만 담는다. LLM도, DB도, 설정도 모른다.
"""

import re

_STRIP = re.compile(r"[^\w가-힣]+")


def _normalize(name: str) -> str:
    """대소문자·공백·괄호·기호 차이로 "다른 이름"처럼 보이는 걸 줄인다.
    예: "두잇 (Do-it)" 과 "두잇(Doit)" 을 같은 걸로 본다."""
    return _STRIP.sub("", name.strip().lower())


def _name_of(idea) -> str:
    """IdeaSpec(속성)과 dict(캐시에서 막 읽은 raw JSON) 둘 다 받는다."""
    if isinstance(idea, dict):
        return idea.get("name", "") or ""
    return getattr(idea, "name", "") or ""


def is_too_similar(new_ideas: list, previous_ideas: list, threshold: float = 0.5) -> bool:
    """새 세트의 이름 중 threshold 이상 비율이 이전 세트와 겹치면 True.

    개수가 다르거나(count 변경) 어느 한쪽이 비어 있으면 비교할 수 없으므로
    False(유사하지 않음 취급 — 통과시킨다). 3개 중 2개 이상 겹치면
    막는다는 게 기본값의 의미(threshold=0.5, 2/3 ≈ 0.67 > 0.5)."""
    if not new_ideas or not previous_ideas:
        return False

    prev_names = {_normalize(_name_of(i)) for i in previous_ideas}
    prev_names.discard("")
    if not prev_names:
        return False

    new_names = [_normalize(_name_of(i)) for i in new_ideas]
    new_names = [n for n in new_names if n]
    if not new_names:
        return False

    overlap = sum(1 for n in new_names if n in prev_names)
    return (overlap / len(new_names)) >= threshold
