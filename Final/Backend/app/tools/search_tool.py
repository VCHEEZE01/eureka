"""
검색 도구 — 네이버·카카오·공공데이터 API를 부르는 유일한 곳.

쓰는 사람: ① 수집 에이전트

★ 에이전트는 여기를 거쳐서만 바깥과 대화한다.
  이유: 테스트할 때 이 파일만 가짜로 바꾸면 되고, API 키가 한 곳에만 있다.

TODO
  · 네이버 검색 오픈API 연동  (일 25,000회 무료)
  · 카카오 다음 검색 API 연동 (무료)
  · 키는 .env 에서 읽을 것. 코드에 직접 쓰지 말 것
"""

from app.schemas.models import RawItem, SourceKind


def search(keyword: str, source_kind: SourceKind, limit: int = 50) -> list[RawItem]:
    """검색어 하나로 원문을 긁어온다."""
    raise NotImplementedError
