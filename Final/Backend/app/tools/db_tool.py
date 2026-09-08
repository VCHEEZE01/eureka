"""
DB 도구 — 저장과 조회를 담당하는 유일한 곳.

쓰는 사람: ③ 문제정의 생성기

★ 숫자는 여기서 센다. LLM이 만들지 않는다.
  publish_problem() 이 raw_items 를 세서 case_count 를 채운다.

TODO
  · DB를 정한 뒤 core/db.py 에 연결을 만들 것
    후보: SQLite / PostgreSQL+pgvector / Supabase
  · 묶기를 임베딩으로 한다면 벡터 검색이 필요하므로 pgvector 쪽이 유리
"""

from app.schemas.models import Category, Problem, ProblemDraft, RawItem


def save_raw_items(items: list[RawItem]) -> None:
    """수집한 원문을 저장한다. 절대 삭제하지 않는다."""
    raise NotImplementedError


def find_similar_problems(title: str) -> list[Problem]:
    """비슷한 기존 문제를 찾는다. 검수의 중복 판단에 쓴다."""
    raise NotImplementedError


def publish_problem(
    draft: ProblemDraft, problem_id: str, category: Category
) -> Problem:
    """
    초안을 게시한다.

    ★ 이때 숫자를 센다 — LLM이 준 값을 쓰지 않는다.
      case_count   = 연결된 raw_items 개수
      source_count = 서로 다른 출처 개수
    """
    raise NotImplementedError


def list_problems() -> list[Problem]:
    """게시된 문제 목록."""
    raise NotImplementedError
