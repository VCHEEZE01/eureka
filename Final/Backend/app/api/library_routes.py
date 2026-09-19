"""
보관함(관심 키워드·관심 아이디어) 서버 저장 — 계정별.

★ 전부 로그인 필수(get_current_user, strict). 로그아웃 상태의 보관함은
  여전히 브라우저 localStorage에만 있다(Final/Frontend/eureka-app.js) —
  "로그아웃 상태에서도 아이디어 생성은 된다"는 원칙과 대칭으로,
  "보관함은 로그인해야 계정에 남는다"는 이 기능의 존재 이유 자체다.

★ payload는 정규화하지 않고 JSONB 그대로 둔다(db/001_auth_library_quota.sql
  주석 참고) — 프론트 camelCase 뷰 모양을 그대로 저장하고 그대로
  돌려준다. 이 라우트는 그 모양을 들여다보지 않는다(name 하나만 예외).
"""

import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, get_current_user
from app.tools import supabase_tool
from app.tools.supabase_tool import SupabaseError, SupabaseUnavailable, idea_key_for

router = APIRouter(prefix="/api/library", tags=["library"])

_MAX_PAYLOAD_BYTES = 64_000  # 폭주한 붙여넣기 하나가 행 하나를 못 부풀리게


def _service_unavailable() -> HTTPException:
    return HTTPException(
        status_code=503,
        detail={"error_code": "library_unavailable", "message": "보관함 기능을 지금 쓸 수 없습니다."},
    )


def _bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=400, detail={"error_code": "invalid_input", "message": message})


def _run(fn, *args, **kwargs):
    """supabase_tool 호출 공통 오류 변환. 매 엔드포인트에서 try/except를
    반복하지 않기 위함 — idea_routes.py의 _resolve_axis_or_400과 같은 자리."""
    try:
        return fn(*args, **kwargs)
    except SupabaseUnavailable:
        raise _service_unavailable()
    except SupabaseError as e:
        raise HTTPException(
            status_code=502,
            detail={"error_code": "library_upstream_error", "message": f"저장소 오류: {e.status_code}"},
        )


def _check_payload(payload: dict) -> None:
    if not isinstance(payload, dict) or not payload.get("name"):
        raise _bad_request("payload는 name을 포함한 객체여야 합니다.")
    size = len(json.dumps(payload, ensure_ascii=False))
    if size > _MAX_PAYLOAD_BYTES:
        raise _bad_request(f"payload가 너무 큽니다({size}자, 최대 {_MAX_PAYLOAD_BYTES}자).")


# ── 요청/응답 모델 ────────────────────────────────────────────────

class SavedKeywordIn(BaseModel):
    keyword_id: str
    name: str
    category: str = ""
    payload: dict = Field(default_factory=dict)


class SavedIdeaIn(BaseModel):
    keyword_id: str = ""
    keyword_name: str = ""
    name: str
    platform: str = ""
    type: str = ""
    period: str = "day"
    payload: dict


class SavedIdeaPatch(BaseModel):
    payload: dict | None = None
    period: str | None = None


class MigrateIn(BaseModel):
    keywords: list[dict] = Field(default_factory=list)
    ideas: list[dict] = Field(default_factory=list)


# ── 관심 키워드 ───────────────────────────────────────────────────

@router.get("/keywords")
def list_keywords(user: CurrentUser = Depends(get_current_user)) -> dict:
    items = _run(supabase_tool.list_saved_keywords, user.id)
    return {"items": items, "count": len(items)}


@router.post("/keywords")
def save_keyword(body: SavedKeywordIn, user: CurrentUser = Depends(get_current_user)) -> dict:
    row = _run(
        supabase_tool.upsert_saved_keyword,
        user.id, body.keyword_id, body.name, body.category, body.payload,
    )
    return row


@router.delete("/keywords/{keyword_id}", status_code=204)
def delete_keyword(keyword_id: str, user: CurrentUser = Depends(get_current_user)) -> None:
    _run(supabase_tool.delete_saved_keyword, user.id, keyword_id)


# ── 관심 아이디어 ─────────────────────────────────────────────────

@router.get("/ideas")
def list_ideas(user: CurrentUser = Depends(get_current_user)) -> dict:
    items = _run(supabase_tool.list_saved_ideas, user.id)
    return {"items": items, "count": len(items)}


@router.post("/ideas")
def save_idea(body: SavedIdeaIn, user: CurrentUser = Depends(get_current_user)) -> dict:
    _check_payload(body.payload)
    key = idea_key_for(body.keyword_id, body.platform, body.type, body.name)
    row = _run(
        supabase_tool.upsert_saved_idea,
        user.id, key, body.keyword_id, body.keyword_name,
        body.name, body.platform, body.type, body.period, body.payload,
    )
    return row


@router.patch("/ideas/{idea_key}")
def patch_idea(idea_key: str, body: SavedIdeaPatch, user: CurrentUser = Depends(get_current_user)) -> dict:
    patch: dict = {}
    if body.payload is not None:
        _check_payload(body.payload)
        patch["payload"] = body.payload
    if body.period is not None:
        patch["period"] = body.period
    if not patch:
        raise _bad_request("payload 또는 period 중 하나는 있어야 합니다.")
    row = _run(supabase_tool.patch_saved_idea, user.id, idea_key, patch)
    if row is None:
        raise HTTPException(status_code=404, detail={"error_code": "idea_not_found", "message": "저장된 아이디어를 찾을 수 없습니다."})
    return row


@router.delete("/ideas/{idea_key}", status_code=204)
def delete_idea(idea_key: str, user: CurrentUser = Depends(get_current_user)) -> None:
    _run(supabase_tool.delete_saved_idea, user.id, idea_key)


# ── 최초 로그인 이관 ──────────────────────────────────────────────

@router.post("/migrate")
def migrate(body: MigrateIn, user: CurrentUser = Depends(get_current_user)) -> dict:
    """localStorage에 있던 로그아웃 시절 보관함을 계정에 옮긴다.
    DB의 unique 제약(merge-duplicates)이 실제 방어선이라 이 엔드포인트
    자체는 멱등하다 — 몇 번을 다시 불러도 중복이 안 생긴다."""
    imported_keywords = 0
    for kw in body.keywords:
        kw_id = str(kw.get("id") or kw.get("keyword_id") or "")
        name = str(kw.get("name") or "")
        if not kw_id or not name:
            continue
        _run(
            supabase_tool.upsert_saved_keyword,
            user.id, kw_id, name, str(kw.get("category") or ""), kw,
        )
        imported_keywords += 1

    imported_ideas = 0
    for idea in body.ideas:
        name = str(idea.get("name") or "")
        if not name:
            continue
        keyword_id = str(idea.get("keywordId") or "")  # 옛 데이터엔 보통 없다
        platform = str(idea.get("platform") or "")
        type_ = str(idea.get("type") or "")
        # 옛 저장 항목(로그인 기능 붙기 전)엔 periodKey가 없다 — day로
        # 채우되 payload.periodLegacy로 "이건 실제 기록이 아니다"를 남겨,
        # 화면이 "기간 미기록"처럼 정직하게 보여줄 수 있게 한다.
        period_key = idea.get("periodKey") or "day"
        if period_key not in ("day", "week", "month"):
            period_key = "day"
        payload = dict(idea)
        payload["periodLegacy"] = not bool(idea.get("periodKey"))
        key = idea_key_for(keyword_id, platform, type_, name)
        _run(
            supabase_tool.upsert_saved_idea,
            user.id, key, keyword_id, str(idea.get("keyword") or ""),
            name, platform, type_, period_key, payload,
        )
        imported_ideas += 1

    return {
        "imported_keywords": imported_keywords,
        "imported_ideas": imported_ideas,
        "skipped_keywords": len(body.keywords) - imported_keywords,
        "skipped_ideas": len(body.ideas) - imported_ideas,
    }
