"""
④ 나누기 — 트렌드/급상승 탭과 순위. AI 없음, 전부 코드.

★ 지금 단계의 한계 ─────────────────────────────────────────────
docs/트렌드_백엔드_설계.md 5절의 classify()는 jump_ratio·
days_since_first_over_min·months_over_min_in_a_row 같은, 여러 주에
걸친 일별 원본 수집 이력이 있어야 계산되는 값을 기준으로 삼는다.
지금 입력 데이터(fixtures/rising_keywords_36.json)는 이런 이력이
없는 정적 스냅샷 36개뿐이라, 그 판정 자체를 코드로 다시 계산할 수
없다.

대신 이 36개는 만들어질 때 이미 tab에 해당하는 판단(statusType:
sustained=지속 성장, rising/viral=급상승)이 사람이 검토해 붙어
있으므로, 그 라벨을 그대로 신뢰해서 tab을 정한다:
  statusType == "sustained"        → tab = "trend"
  statusType in ("rising","viral") → tab = "surge"

실제 일별 수집이 붙으면 이 함수를 5절의 원래 classify()로 교체하고,
여기 있는 라벨 기반 매핑은 지운다.
"""

from app.schemas.trend_models import StatusType, TabType


def tab_for_status(status_type: StatusType) -> TabType:
    if status_type == "sustained":
        return "trend"
    if status_type in ("rising", "viral"):
        return "surge"
    raise ValueError(f"알 수 없는 status_type: {status_type}")


def rank_key(tab: TabType, weekly_change_rate: float, monthly_search_volume: int, monthly_mention_volume: int):
    """탭 안 정렬 기준.

    surge(급상승) = 변화율이 큰 순.
    trend(지속 성장) = 규모(검색+언급)가 큰 순.
    (설계 문서의 '최근성'·'꾸준함' 가중치는 위와 같은 이유로 지금은 반영하지 않는다.)
    """
    if tab == "surge":
        return -weekly_change_rate
    return -(monthly_search_volume + monthly_mention_volume)
