"""
① 수집 에이전트

역할  : 인터넷에서 사람들의 불평을 긁어온다
입력  : 카테고리 + 어떤 소스에서 찾을지
출력  : 원문(RawItem) 목록

할 일
  1. 카테고리에 맞는 검색어를 만든다        → LLM
  2. 그 검색어로 API를 호출한다             → tools/search_tool.py
  3. 중복 제거 등 정리한다

규칙
  · 네이버·카카오 API를 여기서 직접 부르지 말 것 → tools 를 거칠 것
  · 검색어 생성 프롬프트는 prompts/collector_prompts.py 에 둘 것
"""

from app.agents.base import Agent
from app.schemas.models import Category, RawItem, SourceKind
from pydantic import BaseModel


class CollectInput(BaseModel):
    category: Category
    source_kinds: list[SourceKind]
    limit: int = 50


class CollectorAgent(Agent[CollectInput, list[RawItem]]):
    name = "수집 에이전트"
    steps = ["검색어 만들기", "원문 긁어오기", "정리"]

    def run(self, data: CollectInput) -> list[RawItem]:
        raise NotImplementedError("① 담당자가 구현합니다")
