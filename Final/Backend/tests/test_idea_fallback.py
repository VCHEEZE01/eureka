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


def test_nine_combos_produce_distinct_ai_tools():
    tools = {(p, t): tuple(x.id for x in _build(p, t)[1][0].ai_tools) for p, t in ALL_COMBOS}
    assert len(set(tools.values())) == 6, tools


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
