"""
LLM 없이 축 테이블만으로 아이디어를 만드는 결정적 폴백.

★ 프론트 v1-trend-incubator.html:5124-5253 에 하드코딩돼 있던 3가지
  접근(데이터 큐레이션·레이더 / 게이미피케이션·도감 / 의사결정 보조·
  룰렛)을 그대로 가져오되, target·problem·solution·mvp·stack·ai_tools·
  ia를 axes.py 테이블에서 뽑아 채운다 — 그래서 폴백조차 9조합이
  서로 달라지고, LLM 없이 조합 차이를 테스트할 수 있다.

  이 파일은 app.core.llm 을 모른다. generate 쪽에서 LLM 실패·오프라인
  일 때만 부른다.
"""

from app.ideas.axes import ResolvedAxis, build_stack, pick_ai_tools
from app.schemas.idea_models import AiTool, Depth1Node, Depth2Node, IdeaSpec

_APPROACHES = ["radar", "collector", "roulette"]

# 같은 접근(approach)이라도 유형(type)에 따라 problem/solution/mvp가
# 실제로 달라지게 하는 짧은 문구. type_spec의 긴 directive 문장을
# 그대로 여러 필드에 반복해서 넣으면(예: target과 diff에 같은 문장이
# 겹쳐) 유형이 달라도 단어가 겹쳐버리는 문제가 있었다(테스트로 발견).
# 여기는 독립된 짧은 문장을 쓴다.
_TYPE_FLAVOR: dict[str, dict[str, str]] = {
    "utility": {
        "problem_suffix": " 매번 손으로 반복하다 보니 번거롭습니다.",
        "solution_suffix": " 반복 단계를 자동화해 눈에 보이게 줄입니다.",
        "mvp_extra": "설정 없이 기본값으로 바로 동작",
    },
    "fun": {
        "problem_suffix": " 심심할 때 가볍게 즐길 거리가 마땅치 않습니다.",
        "solution_suffix": " 캡처해서 자랑하고 싶은 결과로 만들어 줍니다.",
        "mvp_extra": "회원가입 없이 30초 안에 결과 확인",
    },
    "business": {
        "problem_suffix": " 이 수요를 실제 매출로 연결할 창구가 마땅치 않습니다.",
        "solution_suffix": " 무료·유료 사용자를 나눠 거래로 이어지게 합니다.",
        "mvp_extra": "유료로 넘어가는 지점 1곳 포함",
    },
}


def _ia_for(axis: ResolvedAxis, approach: str, kw: str) -> list[Depth1Node]:
    lo = axis.platform_spec["ia_shape"]["depth1_min"]
    hi = axis.platform_spec["ia_shape"]["depth1_max"]
    count = min(hi, max(lo, 3))  # 기본 3개, 플랫폼 상한이 더 낮으면 맞춘다

    if approach == "radar":
        pool = [
            Depth1Node(depth1="메인 홈", depth2=[
                Depth2Node(title="핵심 목록/지도", desc=f"{kw} 관련 항목을 한눈에 모아 보여준다"),
                Depth2Node(title="빠른 필터", desc="지금 조건에 맞는 것만 골라 보는 토글"),
            ]),
            Depth1Node(depth1="상세 정보", depth2=[
                Depth2Node(title="상태 현황판", desc="지금 상황을 배지로 한눈에 보여준다"),
                Depth2Node(title="한줄 검증 피드", desc="실사용자가 남긴 짧은 코멘트 목록"),
            ]),
            Depth1Node(depth1="저장 & 다시 쓰기", depth2=[
                Depth2Node(title="관심 항목 저장", desc="다시 방문했을 때 바로 이어보는 보관함"),
            ]),
            Depth1Node(depth1="공유 & 연동", depth2=[
                Depth2Node(title="외부 링크 연동", desc="관련 서비스로 한 번에 이동"),
            ]),
        ]
    elif approach == "collector":
        pool = [
            Depth1Node(depth1="도감 홈", depth2=[
                Depth2Node(title="퀘스트 그리드", desc=f"{kw} 관련 미션 카드와 달성 스탬프 표시"),
                Depth2Node(title="진행률 게이지", desc="지금까지 모은 정도를 한눈에 보여준다"),
            ]),
            Depth1Node(depth1="인증소", depth2=[
                Depth2Node(title="경험 기록", desc="사진이나 메모로 방금 한 일을 남긴다"),
                Depth2Node(title="스탬프 인터랙션", desc="손맛 있는 애니메이션으로 완료를 표시"),
            ]),
            Depth1Node(depth1="컬렉션 & 공유", depth2=[
                Depth2Node(title="완성 카드 뷰어", desc="모은 것을 한 화면에 모아보는 카드"),
                Depth2Node(title="결과 이미지 카드", desc="공유용 이미지로 저장·전송"),
            ]),
        ]
    else:  # roulette
        pool = [
            Depth1Node(depth1="취향 진단", depth2=[
                Depth2Node(title="빠른 설문", desc=f"{kw} 취향을 파악하는 3문 3답"),
            ]),
            Depth1Node(depth1="추천 뽑기", depth2=[
                Depth2Node(title="추첨 애니메이션", desc="결과가 나올 때까지의 재미있는 연출"),
                Depth2Node(title="재추첨", desc="마음에 들 때까지 다시 돌리는 기능"),
            ]),
            Depth1Node(depth1="결과 & 공유", depth2=[
                Depth2Node(title="추천 카드", desc="선택된 조합의 요약 정보를 보여준다"),
                Depth2Node(title="공유하기", desc="친구에게 결과를 보내는 버튼"),
            ]),
        ]

    return pool[:count]


def _one(axis: ResolvedAxis, approach: str, kw: str, idx: int) -> IdeaSpec:
    p, t = axis.platform_spec, axis.type_spec

    if approach == "radar":
        name = f"{kw} 파인더 (Finder & Radar)"
        slogan = f"내 주변 {kw} 관련 정보를 한눈에 실시간 확인"
        problem = f"{kw} 관련 정보가 여러 곳에 흩어져 있어 진짜 쓸만한 걸 찾기까지 서칭 피로가 발생합니다."
        solution = f"{kw} 관련 항목을 한 화면에서 실시간으로 큐레이션합니다."
        mvp = [
            "핵심 목록/지도 보기",
            "빠른 필터 및 검색",
            "관심 항목 저장",
            "결과 공유 링크",
        ]
        future = ["실시간 상태 업데이트", "알림 구독"]
    elif approach == "collector":
        name = f"{kw} 도감 챌린지 (Collector's Log)"
        slogan = f"미션을 깨며 나만의 {kw} 스탬프 도감을 완성하는 재미"
        problem = f"{kw} 경험이 일회성으로 끝나고, 무엇을 해봤는지 재미있게 기록할 공간이 없습니다."
        solution = f"{kw} 관련 수집 퀘스트를 제공해 나만의 디지털 스크랩북을 완성하게 합니다."
        mvp = [
            "퀘스트 카드 목록",
            "경험 기록 및 스탬프",
            "수집 진행률 표시",
            "결과 이미지 카드 저장",
        ]
        future = ["친구와 진행률 비교", "한정판 디지털 배지"]
    else:
        name = f"오늘의 {kw} 룰렛 & 추천 봇"
        slogan = f"선택 장애 끝! 지금 내 기분에 딱 맞는 {kw} 조합 추천"
        problem = f"{kw}의 종류·조합이 너무 많아 무엇을 고를지 망설이다 시간을 씁니다."
        solution = f"짧은 질문에 답하면 {kw} 조합을 몇 초 만에 추천합니다."
        mvp = [
            "빠른 취향 설문",
            "추첨 애니메이션",
            "추천 결과 요약",
            "결과 공유하기",
        ]
        future = ["장바구니 딥링크", "유저 랭킹전"]

    ai_tools = [AiTool(**tool) for tool in pick_ai_tools(axis)]
    flavor = _TYPE_FLAVOR[axis.type_key]
    mvp = mvp + [flavor["mvp_extra"]]

    return IdeaSpec(
        id=f"{approach}-{axis.platform_key}-{axis.type_key}",
        name=name,
        short_name=name.split(" (")[0][:20],
        approach={"radar": "데이터 큐레이션 & 실시간 레이더",
                  "collector": "게이미피케이션 & 수집 도감",
                  "roulette": "의사결정 보조 & 랜덤 추천"}[approach],
        slogan=slogan,
        target=t["target_directive"][:100],
        problem=f"{problem}{flavor['problem_suffix']}",
        solution=f"{solution}{flavor['solution_suffix']}",
        architecture=f"{axis.combo_note} {p['target_directive'][:40]}",
        diff=f"{t['angle_directive'][:60]}",
        mvp_features=mvp,
        future_features=future,
        stack=build_stack(axis),
        ai_tools=ai_tools,
        ia=_ia_for(axis, approach, kw),
    )


def build(kw: str, axis: ResolvedAxis, count: int = 3) -> list[IdeaSpec]:
    """count개의 아이디어를 결정적으로 만든다. count > 3이면 접근을
    반복하되 id를 구분한다(폴백은 3가지 원형만 가지고 있다)."""
    out: list[IdeaSpec] = []
    for i in range(count):
        approach = _APPROACHES[i % len(_APPROACHES)]
        idea = _one(axis, approach, kw, i)
        if i >= len(_APPROACHES):
            idea.id = f"{idea.id}-{i}"
        out.append(idea)
    return out
