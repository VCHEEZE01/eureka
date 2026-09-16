"""
⑥ 검수·게시 — fixtures/rising_keywords_28.json(고정 키워드 데이터)을
KeywordReport 스키마의 스냅샷으로 굳혀 data/trends/latest_snapshot.json에 쓴다.

실행:
    python -m app.trends.build_snapshot

지금은 "① 후보 모으기 ② 숫자 모으기"가 없다 — fixtures 파일 자체가
그 결과물(실사용자 조사로 만든 28개 키워드, 프론트 V1.3 디자인의
RISING_KEYWORDS와 동일)이라고 보고, 이 스크립트는 ③ 계산 ④ 나누기
⑤(글쓰기 생략, 이미 써 있음) ⑥ 게시만 한다.
실제 배치(매일 06:00, app/trends/collect.py)가 붙으면 이 스크립트는
그 배치의 마지막 단계로 흡수된다.

★ 2026-09-17: 이전 rising_keywords_36.json(36개)에서 프론트 V1.3
  디자인의 RISING_KEYWORDS(28개)로 교체했다 — 프론트 키워드 id와
  백엔드 스냅샷 id가 어긋나면 같은 id로 다른 키워드가 응답되는
  문제가 있었다. 두 raw 필드명이 우연히 동일해서(_to_report 참고)
  변환 없이 그대로 옮겨졌다.
"""

import json
from datetime import date, timedelta
from pathlib import Path

from app.trends.classify import rank_key, tab_for_status
from app.trends.metrics import parse_int, parse_rate, trend_strength

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES_PATH = _BACKEND_ROOT / "app" / "trends" / "fixtures" / "rising_keywords_28.json"
SNAPSHOT_DIR = _BACKEND_ROOT / "data" / "trends"
LATEST_PATH = SNAPSHOT_DIR / "latest_snapshot.json"


def _months_back(base: date, count: int = 6) -> list[str]:
    months = []
    y, m = base.year, base.month
    for _ in range(count):
        months.append(f"{y:04d}-{m:02d}")
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return list(reversed(months))


def _to_report(raw: dict) -> dict:
    status_type = raw["statusType"]
    tab = tab_for_status(status_type)
    rate = parse_rate(raw["weeklyRate"])

    return {
        "id": raw["id"],
        "tab": tab,
        "name": raw["name"],
        "category": raw["category"],
        "summary": raw["aiSummary"],
        "status": raw["status"],
        "status_type": status_type,
        "metrics": {
            "monthly_search_volume": parse_int(raw["searchVol"]),
            "monthly_mention_volume": parse_int(raw["mentionVol"]),
            "weekly_change_rate": rate,
            "trend_strength": trend_strength(rate).model_dump(),
        },
        "platform_share": raw["platforms"],
        "analysis": {
            "why_trending": raw["whyTrending"],
            "target": raw["target"],
            "sustainability": raw["sustainability"],
            "evidence_ids": [],
        },
        "related_keywords": raw["relatedKeywords"],
        "platform_trend": {
            "naver": {"metric": "search_volume", "values": raw["platformTrend"]["naver"]},
            "youtube": {"metric": "mention_count", "values": raw["platformTrend"]["youtube"]},
            "threads": {"metric": "mention_count", "values": raw["platformTrend"]["threads"]},
        },
        "evidence": [],
        "limitations": ["예시 데이터이며 실제 수집 결과가 아닙니다."],
    }


def build_snapshot(base_date: date | None = None) -> dict:
    base_date = base_date or date.today()
    raw_items = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    reports = [_to_report(r) for r in raw_items]

    for tab in ("trend", "surge"):
        tab_items = [r for r in reports if r["tab"] == tab]
        tab_items.sort(key=lambda r: rank_key(tab, r["metrics"]["weekly_change_rate"],
                                               r["metrics"]["monthly_search_volume"],
                                               r["metrics"]["monthly_mention_volume"]))
        for i, item in enumerate(tab_items, start=1):
            item["rank"] = i

    snapshot_info = {
        "snapshot_id": base_date.isoformat(),
        "base_date": base_date.isoformat(),
        "months": _months_back(base_date),
        "is_dummy": True,
        "note": "예시 데이터입니다 (실제 네이버·유튜브·스레드 수집 연동 전)",
    }

    by_tab = {
        "trend": sorted([r for r in reports if r["tab"] == "trend"], key=lambda r: r["rank"]),
        "surge": sorted([r for r in reports if r["tab"] == "surge"], key=lambda r: r["rank"]),
    }

    criteria = {
        "trend": "최근 실사용자 조사에서 지속 성장(sustained)으로 판단된 키워드",
        "surge": "최근 실사용자 조사에서 급상승·일시적 유행(rising/viral)으로 판단된 키워드",
    }

    return {"snapshot": snapshot_info, "by_tab": by_tab, "criteria": criteria}


def main() -> None:
    snapshot = build_snapshot()
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    dated_path = SNAPSHOT_DIR / f"{snapshot['snapshot']['snapshot_id']}.json"
    text = json.dumps(snapshot, ensure_ascii=False, indent=2)
    dated_path.write_text(text, encoding="utf-8")
    LATEST_PATH.write_text(text, encoding="utf-8")
    print(f"스냅샷 저장: {dated_path}")
    print(f"트렌드 {len(snapshot['by_tab']['trend'])}개 · 급상승 {len(snapshot['by_tab']['surge'])}개")


if __name__ == "__main__":
    main()
