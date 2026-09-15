"""
③ 계산 — 코드가 한다. AI는 이 파일을 절대 거치지 않는다.

docs/트렌드_백엔드_설계.md 4절 "트렌드 강도 규칙"을 그대로 구현한다.
전주 대비 변화율(weekly_change_rate)만으로 강함/보통/약함을 정한다.

★ 지금 단계의 한계 (README 성격의 주석) ─────────────────────────
설계 문서 4절의 "작은 숫자 착시 막기"(capped)는 그 전 7일의 실제
검색·게시물 원본 수치가 있어야 계산된다. 지금 입력 데이터
(fixtures/rising_keywords_36.json)는 6개월치 월별 집계값과 이미
계산된 weekly_change_rate만 갖고 있고, 일 단위 원본 수치가 없다.
그래서 capped는 항상 False로 둔다 — 없는 데이터를 지어내 "작은
숫자였다"고 판정하지 않기 위해서다. 실제 일별 수집이 붙으면 이
함수에 prev_7d_* 인자를 추가해 채운다.
"""

from app.schemas.trend_models import TrendStrength

STRENGTH_STRONG_RATE = 300   # +300% 이상 = 지난주의 4배 이상 → 강함
STRENGTH_MEDIUM_RATE = 100   # +100% 이상 = 지난주의 2배 이상 → 보통
STRENGTH_LABELS = {"strong": "강함", "medium": "보통", "weak": "약함"}


def trend_strength(weekly_change_rate: float) -> TrendStrength:
    """전주 대비 변화율 하나로 트렌드 강도를 정한다. trend/surge 두 탭 모두 같은 기준."""
    if weekly_change_rate >= STRENGTH_STRONG_RATE:
        level = "strong"
    elif weekly_change_rate >= STRENGTH_MEDIUM_RATE:
        level = "medium"
    else:
        level = "weak"

    return TrendStrength(level=level, label=STRENGTH_LABELS[level], capped=False)


def parse_int(value: str) -> int:
    """'58,000' 같은 쉼표 포함 숫자 문자열을 정수로. AI가 아니라 원본 수집값을 그대로 옮기는 것뿐."""
    return int(str(value).replace(",", "").strip())


def parse_rate(value: str) -> float:
    """'+420%' / '-25%' 를 420.0 / -25.0 으로."""
    text = str(value).strip().replace("%", "")
    return float(text)
