"""
IA·아이디어 필드 검증과 자동 보정.

★ LLM 없이 단독으로 테스트할 수 있어야 한다 — app.core.llm 을 모른다.
  docs/IDEA_GENERATION_HANDOFF.md 의 IA 작성 규칙(depth1 2~4개, depth2
  1~3개, depth1끼리 depth2 개수 차이 2개 이상 금지, title/desc 길이,
  근거 없는 수치 금지)을 코드로 강제한다.
"""

import re

from app.ideas.axes import ResolvedAxis
from app.schemas.idea_models import Depth1Node, IdeaSpec

# "월 10만명이 이용" 같은 근거 없는 집계 수치를 잡는다. "반경 5km",
# "12단계"처럼 단위·개수 표현은 허용한다 — 막을 것은 만·억·명·%·원 같은
# 통계성 단위가 붙은 숫자다.
_NUM_CLAIM = re.compile(r"\d[\d,\.]*\s*(만|억|천|명|건|%|퍼센트|원|배)")

_TIME_ROADMAP = re.compile(r"(Day\s*\d|day\s*\d|\d+\s*주차|1주차|2주차|3주차|4주차)", re.IGNORECASE)


def check_ia(ia: list[Depth1Node], axis: ResolvedAxis) -> list[str]:
    """규칙 위반 메시지 목록을 돌려준다. 빈 리스트면 통과."""
    errors: list[str] = []

    lo = axis.platform_spec["ia_shape"]["depth1_min"]
    hi = axis.platform_spec["ia_shape"]["depth1_max"]
    if not (2 <= len(ia) <= 4):
        errors.append(f"depth1이 {len(ia)}개다 (2~4개여야 함)")
    elif not (lo <= len(ia) <= hi):
        errors.append(f"{axis.platform_spec['label']}은 depth1 {lo}~{hi}개여야 하는데 {len(ia)}개다")

    counts = [len(node.depth2) for node in ia]
    if any(not (1 <= c <= 3) for c in counts):
        errors.append(f"depth2 개수 {counts} (각 1~3개여야 함)")
    if counts and max(counts) - min(counts) >= 2:
        errors.append(f"depth2 개수가 불균형하다 {counts} (차이 2개 이상 금지)")

    for node in ia:
        if len(node.depth1) > 14:
            errors.append(f"depth1 이름이 길다: {node.depth1!r}")
        for leaf in node.depth2:
            if len(leaf.title) > 12:
                errors.append(f"depth2 title이 길다: {leaf.title!r}")
            if len(leaf.desc) > 40:
                errors.append(f"depth2 desc가 길다: {leaf.desc!r}")
            if _NUM_CLAIM.search(leaf.desc):
                errors.append(f"근거 없는 수치가 섞여 있다: {leaf.desc!r}")

    return errors


def check_idea(idea: IdeaSpec, axis: ResolvedAxis) -> list[str]:
    errors = check_ia(idea.ia, axis)

    if not (3 <= len(idea.mvp_features) <= 5):
        errors.append(f"mvp_features가 {len(idea.mvp_features)}개다 (3~5개여야 함)")
    if not (1 <= len(idea.future_features) <= 3):
        errors.append(f"future_features가 {len(idea.future_features)}개다 (1~3개여야 함)")
    if len(idea.short_name) > 20:
        errors.append(f"short_name이 길다(탭 제목이 깨진다): {idea.short_name!r}")

    catalog_ids = {t.id for t in idea.ai_tools}
    from app.ideas.axes import AI_TOOL_CATALOG

    unknown = catalog_ids - set(AI_TOOL_CATALOG.keys())
    if unknown:
        errors.append(f"카탈로그에 없는 AI 툴 id: {unknown}")

    haystack = " ".join(
        [idea.name, idea.slogan, idea.problem, idea.solution, idea.architecture]
        + idea.mvp_features
        + idea.future_features
    )
    if _TIME_ROADMAP.search(haystack):
        errors.append("시간 진행 표현(Day 1 / N주차 등)이 섞여 있다 — 기간은 로드맵이 아니다")

    return errors


def is_valid(idea: IdeaSpec, axis: ResolvedAxis) -> bool:
    return len(check_idea(idea, axis)) == 0


def repair(idea: IdeaSpec, axis: ResolvedAxis) -> tuple[IdeaSpec, list[str]]:
    """고칠 수 있는 건 고치고, 무엇을 고쳤는지 warnings로 돌려준다.
    IdeaSpec은 불변으로 다루지 않으므로 그대로 수정해 반환한다."""
    warnings: list[str] = []

    # depth1 5개 이상이면 앞에서부터 최대치만 남긴다.
    hi = axis.platform_spec["ia_shape"]["depth1_max"]
    if len(idea.ia) > hi:
        warnings.append(f"IA depth1이 {len(idea.ia)}개라 {hi}개로 줄였습니다")
        idea.ia = idea.ia[:hi]

    for node in idea.ia:
        if len(node.depth2) > 3:
            warnings.append(f"'{node.depth1}'의 depth2가 {len(node.depth2)}개라 3개로 줄였습니다")
            node.depth2 = node.depth2[:3]
        for leaf in node.depth2:
            if len(leaf.desc) > 40:
                leaf.desc = leaf.desc[:40].rstrip() + "…"

    if len(idea.mvp_features) > 5:
        idea.mvp_features = idea.mvp_features[:5]
    if len(idea.future_features) > 3:
        idea.future_features = idea.future_features[:3]

    return idea, warnings
