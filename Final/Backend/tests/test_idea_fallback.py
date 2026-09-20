import itertools
import re

from app.ideas import axes, fallback, validate

ALL_COMBOS = [(p, t) for p in ("web", "mobile") for t in ("utility", "fun", "business")]


def _build(p: str, t: str):
    axis = axes.resolve(axes.PLATFORM_SPEC[p]["label"], axes.TYPE_SPEC[t]["label"])
    return axis, fallback.build("테스트키워드", axis, count=3)


def test_fallback_passes_validation_for_all_nine_combos():
    for p, t in ALL_COMBOS:
        axis, ideas = _build(p, t)
        for idea in ideas:
            errors = validate.check_idea(idea, axis)
            assert not errors, f"{p}/{t} {idea.id}: {errors}"


def test_nine_combos_produce_distinct_stack():
    stacks = {(p, t): _build(p, t)[1][0].stack for p, t in ALL_COMBOS}
    assert len(set(stacks.values())) == 6, stacks


def test_fallback_carries_period_fixed_ai_tools():
    """폴백도 LLM 경로와 같은 기간별 고정 목록을 달고 나와야 한다."""
    for p, t in ALL_COMBOS:
        _, ideas = _build(p, t)
        for idea in ideas:
            assert set(idea.ai_tools_by_period) == {"day", "week", "month"}
            assert [x.id for x in idea.ai_tools_by_period["week"]] == ["antigravity", "cursor"]
            # ai_tools는 하위 호환용 'day' 사본이다
            assert [x.id for x in idea.ai_tools] == [x.id for x in idea.ai_tools_by_period["day"]]


def test_ia_depth1_count_respects_platform_shape():
    for p, t in ALL_COMBOS:
        axis, ideas = _build(p, t)
        lo = axis.platform_spec["ia_shape"]["depth1_min"]
        hi = axis.platform_spec["ia_shape"]["depth1_max"]
        for idea in ideas:
            assert lo <= len(idea.ia) <= hi, (p, t, idea.id, len(idea.ia))


def _words(idea) -> set[str]:
    text = " ".join(
        [idea.problem, idea.solution, idea.target] + idea.mvp_features
    )
    return set(re.findall(r"[가-힣A-Za-z0-9]+", text))


def test_mvp_and_problem_text_differ_across_combos_within_same_platform():
    """같은 플랫폼 안에서 유형만 바뀌어도 텍스트가 과도하게 겹치지 않는지."""
    for platform in ("web", "mobile"):
        combos = [(platform, t) for t in ("utility", "fun", "business")]
        idea_sets = {t: _build(platform, t)[1][0] for _, t in combos}
        for (t1, i1), (t2, i2) in itertools.combinations(idea_sets.items(), 2):
            w1, w2 = _words(i1), _words(i2)
            jaccard = len(w1 & w2) / len(w1 | w2) if (w1 | w2) else 0
            assert jaccard < 0.6, (platform, t1, t2, jaccard)


def test_no_time_roadmap_wording_in_any_combo():
    banned = re.compile(r"(Day\s*\d|\d+\s*주차)", re.IGNORECASE)
    for p, t in ALL_COMBOS:
        _, ideas = _build(p, t)
        for idea in ideas:
            haystack = " ".join([idea.name, idea.slogan, idea.problem, idea.solution] + idea.mvp_features)
            assert not banned.search(haystack), (p, t, idea.id)


# ── 2026-09-19: 새로고침용 variation ────────────────────────────

def test_fallback_variation_default_matches_no_variation():
    """variation을 아예 안 주는 것과 variation=0은 완전히 같아야 한다
    (기존 호출부·캐시가 바뀌지 않는다는 보장)."""
    axis = axes.resolve(axes.PLATFORM_SPEC["web"]["label"], axes.TYPE_SPEC["utility"]["label"])
    default = fallback.build("테스트키워드", axis, count=3)
    explicit0 = fallback.build("테스트키워드", axis, count=3, variation=0)
    assert [i.model_dump() for i in default] == [i.model_dump() for i in explicit0]


def test_fallback_variation_changes_output_across_all_combos():
    """새로고침(variation=1)은 접근 순서·슬로건·id가 원래(variation=0)와 달라야
    한다 — 이게 없으면 폴백으로 떨어진 새로고침이 매번 같은 3개를 반복한다."""
    for p, t in ALL_COMBOS:
        axis = axes.resolve(axes.PLATFORM_SPEC[p]["label"], axes.TYPE_SPEC[t]["label"])
        base = fallback.build("테스트키워드", axis, count=3, variation=0)
        varied = fallback.build("테스트키워드", axis, count=3, variation=1)
        assert [i.id for i in base] != [i.id for i in varied], (p, t)
        assert [i.slogan for i in base] != [i.slogan for i in varied], (p, t)
        # 그래도 여전히 검증은 통과해야 한다 — 변형이 형식을 깨면 안 된다
        for idea in varied:
            assert not validate.check_idea(idea, axis), (p, t, idea.id)


def test_fallback_variation_ids_stay_unique_within_one_call():
    axis = axes.resolve(axes.PLATFORM_SPEC["mobile"]["label"], axes.TYPE_SPEC["fun"]["label"])
    ideas = fallback.build("테스트키워드", axis, count=3, variation=2)
    ids = [i.id for i in ideas]
    assert len(ids) == len(set(ids)), ids
