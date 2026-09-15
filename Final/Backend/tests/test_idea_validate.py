from app.ideas import axes, validate
from app.schemas.idea_models import AiTool, Depth1Node, Depth2Node, IdeaSpec


def _mobile_axis():
    return axes.resolve("모바일 앱", "실용(편의)")


def _base_idea(**overrides) -> IdeaSpec:
    defaults = dict(
        name="테스트 아이디어",
        short_name="테스트",
        approach="테스트 접근",
        slogan="슬로건",
        target="타겟",
        problem="문제",
        solution="해결",
        architecture="구조",
        diff="차별점",
        mvp_features=["기능1", "기능2", "기능3"],
        future_features=["확장1"],
        stack="React Native",
        ai_tools=[AiTool(id="cursor", name="Cursor", role="편집")],
        ia=[
            Depth1Node(depth1="홈", depth2=[Depth2Node(title="목록", desc="항목을 보여준다")]),
            Depth1Node(depth1="상세", depth2=[Depth2Node(title="정보", desc="상세 정보를 보여준다")]),
            Depth1Node(depth1="저장", depth2=[Depth2Node(title="북마크", desc="저장한다")]),
        ],
    )
    defaults.update(overrides)
    return IdeaSpec(**defaults)


def test_valid_idea_passes():
    idea = _base_idea()
    assert validate.is_valid(idea, _mobile_axis())


def test_depth1_too_many_is_rejected():
    idea = _base_idea(ia=[
        Depth1Node(depth1=f"화면{i}", depth2=[Depth2Node(title="a", desc="b")]) for i in range(6)
    ])
    errors = validate.check_ia(idea.ia, _mobile_axis())
    assert any("depth1" in e for e in errors)


def test_depth2_imbalance_is_rejected():
    idea = _base_idea(ia=[
        Depth1Node(depth1="A", depth2=[Depth2Node(title="a", desc="b")]),
        Depth1Node(depth1="B", depth2=[Depth2Node(title=f"t{i}", desc="d") for i in range(3)]),
        Depth1Node(depth1="C", depth2=[Depth2Node(title="a", desc="b")]),
    ])
    errors = validate.check_ia(idea.ia, _mobile_axis())
    assert any("불균형" in e for e in errors)


def test_numeric_claim_in_desc_is_rejected():
    idea = _base_idea(ia=[
        Depth1Node(depth1="A", depth2=[Depth2Node(title="a", desc="월 10만명이 이용합니다")]),
        Depth1Node(depth1="B", depth2=[Depth2Node(title="b", desc="정상 설명")]),
        Depth1Node(depth1="C", depth2=[Depth2Node(title="c", desc="정상 설명")]),
    ])
    errors = validate.check_ia(idea.ia, _mobile_axis())
    assert any("근거 없는 수치" in e for e in errors)


def test_unit_or_count_numbers_are_allowed():
    idea = _base_idea(ia=[
        Depth1Node(depth1="A", depth2=[Depth2Node(title="a", desc="반경 5km 내 표시")]),
        Depth1Node(depth1="B", depth2=[Depth2Node(title="b", desc="12단계로 구성됨")]),
        Depth1Node(depth1="C", depth2=[Depth2Node(title="c", desc="3문 3답 설문")]),
    ])
    errors = validate.check_ia(idea.ia, _mobile_axis())
    assert not any("근거 없는 수치" in e for e in errors)


def test_time_roadmap_wording_is_rejected():
    idea = _base_idea(solution="Day 1에 핵심 기능부터 만듭니다")
    errors = validate.check_idea(idea, _mobile_axis())
    assert any("시간 진행 표현" in e for e in errors)


def test_unknown_ai_tool_id_is_rejected():
    idea = _base_idea(ai_tools=[AiTool(id="does-not-exist", name="???", role="???")])
    errors = validate.check_idea(idea, _mobile_axis())
    assert any("카탈로그에 없는" in e for e in errors)


def test_repair_truncates_excess_depth1():
    idea = _base_idea(ia=[
        Depth1Node(depth1=f"화면{i}", depth2=[Depth2Node(title="a", desc="b")]) for i in range(6)
    ])
    repaired, warnings = validate.repair(idea, _mobile_axis())
    assert len(repaired.ia) <= 4
    assert warnings
