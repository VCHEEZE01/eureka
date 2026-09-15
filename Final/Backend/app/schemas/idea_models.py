"""
v1 아이디어 생성 스키마.

★ 왜 app/schemas/models.py 에 안 두는가
  거기 있는 Idea(models.py:206)는 v0(문제→아이디어) 도메인이다
  (problem_id · why_linked · fit_reason). v1은 트렌드 키워드 +
  platform/type 에서 출발하고 ia · mvp_features · ai_tools 같은
  새 필드가 필요해서 계약이 다르다. models.py는 팀 전체가 공유하는
  파일이라 여기서 고치면 다른 담당자 작업과 충돌한다 — app/trends/가
  trend_models.py 를 따로 둔 것과 같은 이유로 별도 파일을 쓴다.

  v0 IdeaAgent 의 원래 계약(Problem 기반)은 git tag v0-pre-pivot 의
  app/agents/idea_agent.py 를 참고할 것.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field

Platform = Literal["web", "mobile", "desktop"]
IdeaType = Literal["utility", "fun", "business"]
Period = Literal["day", "week", "month"]
Source = Literal["llm", "cache", "fallback"]


class Depth2Node(BaseModel):
    title: str
    desc: str


class Depth1Node(BaseModel):
    depth1: str
    depth2: list[Depth2Node]


class AiTool(BaseModel):
    id: str
    name: str
    role: str


class IdeaSpec(BaseModel):
    """아이디어 하나. LLM 원시 출력과 완성본이 같은 형태를 쓴다."""

    id: str = ""
    name: str
    short_name: str
    approach: str
    slogan: str
    target: str
    problem: str
    solution: str
    architecture: str
    diff: str
    mvp_features: list[str] = Field(default_factory=list)
    future_features: list[str] = Field(default_factory=list)
    stack: str = ""
    ai_tools: list[AiTool] = Field(default_factory=list)
    ia: list[Depth1Node] = Field(default_factory=list)
    prompts: dict[str, str] = Field(default_factory=dict)
    prompt: str = ""


class SnapshotInfo(BaseModel):
    snapshot_id: str
    base_date: str
    is_dummy: bool = False
    note: Optional[str] = None


class KeywordRef(BaseModel):
    id: str
    name: str
    category: str = ""


class IdeaConfig(BaseModel):
    platform: Platform
    platform_label: str
    type: IdeaType
    type_label: str
    period: Period


class IdeaRequest(BaseModel):
    """POST /api/trends/{keyword_id}/ideas 요청 바디.

    platform/type/period 는 프론트 칩 라벨 그대로 받는다
    (예: "모바일 앱", "실용(편의)", "한 달 이상"). 정규화는
    app/ideas/axes.py 의 별칭 테이블이 한다.
    """

    platform: str
    type: str
    period: str = "하루"
    count: int = 3
    refresh: bool = False


class IdeaSet(BaseModel):
    snapshot: SnapshotInfo
    keyword: KeywordRef
    config: IdeaConfig
    source: Source
    generated_at: str
    prompt_version: int
    ideas: list[IdeaSpec]
    warnings: list[str] = Field(default_factory=list)
