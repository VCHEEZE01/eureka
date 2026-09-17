"""
트렌드 키워드 서비스 API — docs/트렌드_백엔드_설계.md 7절.

GET /api/trends?tab=trend|surge   목록 (탭 전체, 최대 36개)
GET /api/trends/{keyword_id}      키워드 하나의 분석 리포트

가장 최근 게시된 스냅샷(app/trends/build_snapshot.py가 만든
data/trends/latest_snapshot.json)을 읽기만 한다 — 여기서 계산하지
않는다. 스냅샷이 없으면 503(snapshot_not_ready)을 낸다.
(읽기는 app/trends/snapshot_store.py — Vercel 예외도 거기 있다)
"""

from fastapi import APIRouter, HTTPException

from app.trends import snapshot_store

router = APIRouter(prefix="/api/trends", tags=["trends"])


def _load_snapshot() -> dict:
    snapshot = snapshot_store.load_latest()
    if snapshot is None:
        raise HTTPException(
            status_code=503,
            detail={"error_code": "snapshot_not_ready", "message": "아직 게시된 트렌드 스냅샷이 없습니다. 배치를 먼저 실행해 주세요."},
        )
    return snapshot


@router.get("")
def list_trends(tab: str) -> dict:
    if tab not in ("trend", "surge"):
        raise HTTPException(
            status_code=400,
            detail={"error_code": "invalid_input", "message": "tab은 trend 또는 surge여야 합니다."},
        )
    snapshot = _load_snapshot()
    items = snapshot["by_tab"][tab]
    return {
        "snapshot": snapshot["snapshot"],
        "tab": tab,
        "criteria": snapshot["criteria"][tab],
        "items": items,
    }


@router.get("/{keyword_id}")
def get_trend_report(keyword_id: str) -> dict:
    snapshot = _load_snapshot()
    for tab_items in snapshot["by_tab"].values():
        for item in tab_items:
            if item["id"] == keyword_id:
                return {"snapshot": snapshot["snapshot"], "report": item}
    raise HTTPException(
        status_code=404,
        detail={"error_code": "keyword_not_found", "message": "해당 키워드를 찾을 수 없습니다."},
    )
