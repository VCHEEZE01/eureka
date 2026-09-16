import pytest

from app.ideas import axes


def test_normalize_accepts_frontend_labels():
    assert axes.normalize_platform("모바일 앱") == "mobile"
    assert axes.normalize_platform("모바일 앱(App)") == "mobile"
    assert axes.normalize_platform("웹(Web MVP)") == "web"
    assert axes.normalize_platform("웹(Web)") == "web"
    assert axes.normalize_type("실용(편의)") == "utility"
    assert axes.normalize_type("재미") == "fun"
    assert axes.normalize_type("수익(비즈니스)") == "business"


def test_normalize_period_absorbs_doc_code_label_mismatch():
    # 코드: 하루/일주일/한 달 이상  vs  문서: 1일/일주일/한달
    assert axes.normalize_period("하루") == "day"
    assert axes.normalize_period("1일") == "day"
    assert axes.normalize_period("한 달 이상") == "month"
    assert axes.normalize_period("한달") == "month"


def test_normalize_rejects_unknown_value():
    with pytest.raises(ValueError):
        axes.normalize_platform("VR 헤드셋")


ALL_COMBOS = [(p, t) for p in ("web", "mobile") for t in ("utility", "fun", "business")]


def test_nine_combos_have_unique_stack():
    stacks = set()
    for p, t in ALL_COMBOS:
        axis = axes.resolve(axes.PLATFORM_SPEC[p]["label"], axes.TYPE_SPEC[t]["label"])
        stacks.add(axes.build_stack(axis))
    assert len(stacks) == 6


def test_nine_combos_have_unique_ai_tool_sets():
    tool_sets = set()
    for p, t in ALL_COMBOS:
        axis = axes.resolve(axes.PLATFORM_SPEC[p]["label"], axes.TYPE_SPEC[t]["label"])
        tool_sets.add(tuple(sorted(x["id"] for x in axes.pick_ai_tools(axis))))
    assert len(tool_sets) == 6


def test_ai_tools_are_all_in_catalog():
    for p, t in ALL_COMBOS:
        axis = axes.resolve(axes.PLATFORM_SPEC[p]["label"], axes.TYPE_SPEC[t]["label"])
        for tool in axes.pick_ai_tools(axis):
            assert tool["id"] in axes.AI_TOOL_CATALOG
