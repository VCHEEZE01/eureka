"""
묶기 도구 — 비슷한 불편끼리 뭉친다.

쓰는 사람: ② 해석기

방식은 담당자가 정한다. 후보 세 가지.
  a) 임베딩 + 클러스터링 — 수천 건 가능 · 재현성 있음 · 라이브러리 필요
  b) LLM에게 통째로      — 코드 적음 · 수백 건 한계 · 결과가 매번 다름
  c) a 로 묶고 b 로 검수 — 실무에서 흔한 방식

무엇을 고르든 아래 함수 모양은 유지할 것. 그래야 나중에 갈아끼울 수 있다.
"""

from app.schemas.models import Judgement


def group(judgements: list[Judgement]) -> list[list[Judgement]]:
    """비슷한 불편끼리 묶는다. 반환: 묶음들의 목록."""
    raise NotImplementedError


def name_group(group_items: list[Judgement]) -> str:
    """이 묶음이 무엇에 관한 것인지 한 구절로."""
    raise NotImplementedError
