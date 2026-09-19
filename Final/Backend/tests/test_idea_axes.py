import re

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


def test_ai_tools_are_fixed_per_period():
    """추천 AI는 축이 아니라 기간으로 정해진다 — 표에 적힌 그대로 나와야 한다."""
    assert [t["id"] for t in axes.tools_for_period("day")] == ["chatgpt", "gemini", "claude", "ai_studio"]
    assert [t["id"] for t in axes.tools_for_period("week")] == ["antigravity", "cursor"]
    assert [t["id"] for t in axes.tools_for_period("month")] == ["claude_code", "codex"]


def test_ai_tools_differ_across_periods():
    sets = {p: tuple(t["id"] for t in axes.tools_for_period(p)) for p in ("day", "week", "month")}
    assert len(set(sets.values())) == 3, sets


def test_ai_tools_are_all_in_catalog():
    for period, tools in axes.tools_by_period().items():
        assert tools, f"{period} 기간의 추천 AI가 비어 있다"
        for tool in tools:
            assert tool["id"] in axes.AI_TOOL_CATALOG
            assert tool["name"] and tool["role"]


def test_unknown_period_falls_back_to_day():
    """화면 pill이 빈 채로 남는 것보다 하루 목록이라도 보여주는 쪽."""
    assert axes.tools_for_period("decade") == axes.tools_for_period("day")


def test_ai_tool_names_carry_no_version_or_model_number():
    """'Claude 3.5 Sonnet'처럼 금방 낡는 이름이 사용자에게 나가면 안 된다."""
    for tool in axes.AI_TOOL_CATALOG.values():
        assert not re.search(r"\d", tool["name"]), tool["name"]
