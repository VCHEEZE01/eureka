"""
④ 아이디어 생성기 — v1 (트렌드 키워드 → 아이디어 3개)

역할  : 트렌드 키워드 + 플랫폼 + 아이디어 유형에서 서로 다른 아이디어를 뽑는다
입력  : 키워드 id, 플랫폼(웹/모바일 앱/데스크탑 웹), 유형(실용/재미/수익)
출력  : 아이디어 N개 (설명 / 추천 AI 툴 / 서비스 타겟 / MVP / IA / 기간별 프롬프트)

★ v0 계약과 다르다 (docs/PIVOT.md 참고)
  v0의 IdeaInput은 Problem + UserCondition(git tag v0-pre-pivot의 이
  파일)에서 출발했지만, v1은 실시간 수집 파이프라인을 접고 트렌드
  키워드에서 바로 아이디어로 간다 — problem_id·why_linked·fit_reason
  같은 필드가 없다. 그래서 app/schemas/models.py의 Idea는 그대로 두고
  app/schemas/idea_models.py에 새 스키마를 뒀다.

할 일
  1. 스냅샷에서 키워드를 읽는다 (계산은 app/trends/가 이미 끝냄)
  2. 플랫폼×유형 축을 정규화한다 (app/ideas/axes.py)
  3. LLM으로 아이디어 N개를 뽑는다. 실패·오프라인이면 결정적 폴백으로
  4. IA·필드 제약을 검증하고 고칠 수 있는 건 고친다
  5. stack·AI 툴은 코드가 축 테이블에서 조립한다 (LLM이 정하지 않음)
  6. 기간별(하루/일주일/한달) 바이브코딩 프롬프트 3종을 전부 만든다

규칙
  · 시장 규모·성공 확률 같은 근거 없는 수치를 만들지 말 것
  · "검증된 아이디어"처럼 표현하지 말 것 → 어디까지나 "추천 후보"
    (app/prompts/common_prompts.py COMMON_RULES 로 강제)
"""

from datetime import datetime, timezone

from pydantic import BaseModel

from app.agents.base import Agent
from app.core.llm import LLMError
from app.ideas import axes, fallback, validate
from app.prompts.idea_prompts import PROMPT_VERSION, build_idea_prompt, build_period_prompt
from app.schemas.idea_models import (
    AiTool,
    Depth1Node,
    IdeaConfig,
    IdeaSet,
    IdeaSpec,
    KeywordRef,
    SnapshotInfo,
)
from app.tools import idea_tool
from app.tools.idea_tool import LLMOffline


class IdeaAgentInput(BaseModel):
    keyword_id: str
    platform: str  # 프론트 칩 라벨 그대로 (예: "모바일 앱")
    type: str      # 프론트 칩 라벨 그대로 (예: "재미")
    count: int = 3


def _raw_to_spec(raw: dict) -> IdeaSpec:
    """LLM이 낸 dict를 IdeaSpec으로 느슨하게 채운다. 키가 빠져 있어도
    죽지 않게 기본값을 둔다 — 부족한 필드는 검증 단계에서 걸러진다."""
    ia = [
        Depth1Node(
            depth1=node.get("depth1", ""),
            depth2=[{"title": leaf.get("title", ""), "desc": leaf.get("desc", "")}
                    for leaf in node.get("depth2", [])],
        )
        for node in raw.get("ia", [])
    ]
    return IdeaSpec(
        name=raw.get("name", ""),
        short_name=raw.get("short_name", raw.get("name", ""))[:20],
        approach=raw.get("approach", ""),
        slogan=raw.get("slogan", ""),
        target=raw.get("target", ""),
        problem=raw.get("problem", ""),
        solution=raw.get("solution", ""),
        architecture=raw.get("architecture", ""),
        diff=raw.get("diff", ""),
        mvp_features=list(raw.get("mvp_features", [])),
        future_features=list(raw.get("future_features", [])),
        ia=ia,
    )


class IdeaAgent(Agent[IdeaAgentInput, IdeaSet]):
    name = "아이디어 생성기"
    steps = ["키워드 읽기", "아이디어 뽑기", "IA 검증", "프롬프트 작성"]

    def run(self, data: IdeaAgentInput) -> IdeaSet:
        self.report(0)
        kw = idea_tool.load_keyword(data.keyword_id)
        snapshot_info = idea_tool.load_snapshot_info()
        axis = axes.resolve(data.platform, data.type)
        count = max(1, min(data.count, 5))
        self.report(0, done=True)

        self.report(1)
        try:
            raw_list = idea_tool.complete_ideas_json(
                build_idea_prompt(kw, axis, count)
            )
            source = "llm"
        except (LLMOffline, LLMError, ValueError):
            raw_list = []
            source = "fallback"

        ideas = [_raw_to_spec(x) for x in raw_list] if source == "llm" else []
        self.report(1, done=True)

        self.report(2)
        warnings: list[str] = []
        checked: list[IdeaSpec] = []
        for idea in ideas:
            idea, repair_warnings = validate.repair(idea, axis)
            warnings.extend(repair_warnings)
            if validate.is_valid(idea, axis):
                checked.append(idea)
            else:
                warnings.append(f"'{idea.name}'이(가) 검증을 통과하지 못해 제외했습니다: {validate.check_idea(idea, axis)}")

        if len(checked) < count:
            missing = count - len(checked)
            fallback_ideas = fallback.build(kw["name"], axis, count=missing)
            if source == "llm" and checked:
                warnings.append(f"LLM이 {missing}개를 채우지 못해 예시 아이디어로 보충했습니다")
            elif source == "llm":
                source = "fallback"
            checked.extend(fallback_ideas)
        self.report(2, done=True)

        self.report(3)
        for i, idea in enumerate(checked, start=1):
            idea.id = idea.id or f"{data.keyword_id}-{axis.platform_key}-{axis.type_key}-{i}"
            if not idea.stack:
                idea.stack = axes.build_stack(axis)
            if not idea.ai_tools:
                idea.ai_tools = [AiTool(**t) for t in axes.pick_ai_tools(axis)]
            idea.prompts = {
                period: build_period_prompt(idea, kw["name"], axis, period)
                for period in ("day", "week", "month")
            }
            idea.prompt = idea.prompts["day"]
        self.report(3, done=True)

        return IdeaSet(
            snapshot=SnapshotInfo(**snapshot_info),
            keyword=KeywordRef(id=kw["id"], name=kw["name"], category=kw.get("category", "")),
            config=IdeaConfig(
                platform=axis.platform_key, platform_label=axis.platform_spec["label"],
                type=axis.type_key, type_label=axis.type_spec["label"],
                period="day",
            ),
            source=source,
            generated_at=datetime.now(timezone.utc).astimezone().isoformat(),
            prompt_version=PROMPT_VERSION,
            ideas=checked,
            warnings=warnings,
        )


__all__ = ["IdeaAgent", "IdeaAgentInput"]
