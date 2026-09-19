"""
아이디어 생성 API — docs/트렌드_백엔드_설계.md 7절의
"POST /api/trends/{keyword_id}/ideas (나중) 아이디어 5개 만들기"를 채운다.

POST /api/trends/{keyword_id}/ideas          아이디어 생성 (캐시 히트 시 즉시 반환)
GET  /api/trends/{keyword_id}/ideas          캐시만 조회 (없으면 404)
POST /api/trends/{keyword_id}/ideas/prompt   사용자가 편집한 MVP로 프롬프트만 재조립

trend_routes.py와 같은 prefix("/api/trends")를 쓰지만 경로가 겹치지
않는다 (거기는 "", "/{keyword_id}"만 정의).

★ 새로고침(refresh=true, 로그인 필수, 키워드당 REFRESH_QUOTA_PER_KEYWORD회)
  은 이 파일에서 처리한다. 핵심 규칙 셋:
  1. 캐시 variant를 그 사용자의 쿼터 사용량으로 정한다 — variant=0(최초
     생성)은 절대 덮어쓰지 않는다. 한 사용자의 새로고침이 다른 사용자가
     보는 결과를 바꾸는 예전 버그(app/ideas/cache.py 주석 참고)를 여기서
     막는다.
  2. 쿼터는 LLM 호출 "전"에 예약하고, 결과가 폴백이거나 이전과 너무
     비슷하면 반납한다 — "새 AI 아이디어 3개"가 아닌 결과로 1회뿐인
     권리를 태우지 않는다.
  3. Supabase 실패가 아이디어 생성 자체를 막지 않는다 — 쿼터 조회가
     실패해도 화면에 보여줄 상태값만 보수적으로 채우고 생성은 계속한다.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ValidationError

from app.agents.idea_agent import IdeaAgent, IdeaAgentInput
from app.api.deps import CurrentUser, get_current_user_optional
from app.config.settings import settings
from app.ideas import axes, cache, dedupe
from app.ideas.axes import ResolvedAxis
from app.prompts.idea_prompts import build_period_prompt
from app.schemas.idea_models import IdeaSpec
from app.tools import idea_tool, supabase_tool
from app.tools.idea_tool import KeywordNotFound, SnapshotNotReady
from app.tools.supabase_tool import SupabaseError, SupabaseUnavailable

router = APIRouter(prefix="/api/trends", tags=["ideas"])

# 쿼터가 아무리 커져도(설정 실수 등) variant 키가 무한히 늘어나지 않게
# 막는 안전판. REFRESH_QUOTA_PER_KEYWORD 기본값(1)보다 넉넉히 크다.
MAX_VARIANT = 5


class IdeaGenerateRequest(BaseModel):
    platform: str
    type: str
    period: str = "하루"
    count: int = 3
    refresh: bool = False


def _bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=400, detail={"error_code": "invalid_input", "message": message})


def _resolve_axis_or_400(platform: str, type_: str) -> ResolvedAxis:
    try:
        return axes.resolve(platform, type_)
    except ValueError as e:
        raise _bad_request(str(e)) from e


def _load_snapshot_info_or_404() -> dict:
    return idea_tool.load_snapshot_info()


def _stamp(cached: dict, period_key: str, source: str | None = None) -> dict:
    """캐시에서 읽은(또는 방금 만든) 아이디어셋에 요청한 기간의 프롬프트를
    골라 얹는다. 세 갈래(POST 캐시히트/GET/새로고침 되돌리기)가 전부 같은
    모양을 만들어야 해서 한 곳으로 모았다."""
    out = dict(cached)
    if source:
        out["source"] = source
    out["config"] = dict(out["config"])
    out["config"]["period"] = period_key
    out["ideas"] = [dict(idea) for idea in out.get("ideas", [])]
    for idea in out["ideas"]:
        idea["prompt"] = idea.get("prompts", {}).get(period_key, idea.get("prompt", ""))
    return out


def _refresh_block(applied: bool, reason: str, used: int = 0, limit: int = 0, variant: int = 0) -> dict:
    return {"applied": applied, "reason": reason, "used": used, "limit": limit, "variant": variant}


def _quota_snapshot(user: CurrentUser | None, keyword_id: str) -> dict:
    """새로고침 버튼을 그릴 수 있게 현재 쿼터 상태를 알려준다(소비는 안 함).
    Supabase가 흔들려도 이 조회 실패가 아이디어 생성 자체를 막지 않는다
    — 그냥 "지금은 모른다"로 보수적으로 채운다."""
    limit = settings.REFRESH_QUOTA_PER_KEYWORD
    if user is None:
        return _refresh_block(False, "anonymous", 0, limit, 0)
    if not settings.supabase_ready:
        return _refresh_block(False, "unavailable", 0, limit, 0)
    try:
        q = supabase_tool.get_refresh_quota(user.id, keyword_id, limit)
    except (SupabaseError, SupabaseUnavailable):
        return _refresh_block(False, "unavailable", 0, limit, 0)
    used, lim = q["used"], q["limit"]
    return _refresh_block(used < lim, "ok" if used < lim else "quota_spent", used, lim, min(used, MAX_VARIANT))


def _serve_previous_or_regenerate(
    keyword_id: str, axis: ResolvedAxis, count: int, variant: int, period_key: str,
    reason: str, quota_used: int, quota_limit: int,
) -> dict:
    """새로고침을 거절해야 할 때(쿼터 소진·폴백·유사도 가드) 직전에
    성공했던 세트를 그대로 돌려준다. 그 세트조차 캐시에 없는 아주 드문
    경우에만(방어적으로) variant=0으로 떨어진다."""
    snapshot_info = _load_snapshot_info_or_404()
    key = cache.cache_key(snapshot_info["snapshot_id"], keyword_id, axis.platform_key, axis.type_key, count, variant=variant)
    cached = cache.read(keyword_id, axis.platform_key, axis.type_key, key)
    if cached is None and variant != 0:
        key0 = cache.cache_key(snapshot_info["snapshot_id"], keyword_id, axis.platform_key, axis.type_key, count, variant=0)
        cached = cache.read(keyword_id, axis.platform_key, axis.type_key, key0)
        variant = 0
    if cached is None:
        # 정말 아무 캐시도 없다 — 이 경로까지 왔다는 건 쿼터가 이미 소비된
        # 적이 있다는 뜻이라 이론상 거의 안 생기지만, 생기면 그냥 새로 만든다.
        return None
    out = _stamp(cached, period_key, source="cache")
    out["refresh"] = _refresh_block(False, reason, quota_used, quota_limit, variant)
    return out


@router.post("/{keyword_id}/ideas")
def generate_ideas(
    keyword_id: str, body: IdeaGenerateRequest,
    user: CurrentUser | None = Depends(get_current_user_optional),
) -> dict:
    if not (1 <= body.count <= 5):
        raise _bad_request("count는 1~5여야 합니다.")

    axis = _resolve_axis_or_400(body.platform, body.type)
    try:
        period_key = axes.normalize_period(body.period)
    except ValueError as e:
        raise _bad_request(str(e)) from e

    if body.refresh and user is None:
        raise HTTPException(
            status_code=403,
            detail={"error_code": "refresh_requires_login", "message": "로그인 후 새로고침할 수 있습니다."},
        )
    if body.refresh and not settings.supabase_ready:
        raise HTTPException(
            status_code=503,
            detail={"error_code": "refresh_unavailable", "message": "지금은 새로고침을 쓸 수 없습니다."},
        )

    try:
        snapshot_info = _load_snapshot_info_or_404()
    except SnapshotNotReady as e:
        raise HTTPException(status_code=503, detail={"error_code": "snapshot_not_ready", "message": str(e)}) from e

    # ── 새로고침이 아니면 오늘까지의 동작과 완전히 동일 ──────────────
    if not body.refresh:
        key = cache.cache_key(snapshot_info["snapshot_id"], keyword_id, axis.platform_key, axis.type_key, body.count)
        cached = cache.read(keyword_id, axis.platform_key, axis.type_key, key)
        if cached is not None:
            out = _stamp(cached, period_key, source="cache")
            out["refresh"] = _quota_snapshot(user, keyword_id)
            return out
        result, source = _run_agent_or_404_503_400(keyword_id, body, axis, exclude=[], variation=0)
        data = result.model_dump()
        cache.write(keyword_id, axis.platform_key, axis.type_key, key, data)
        out = _stamp(data, period_key)
        out["refresh"] = _quota_snapshot(user, keyword_id)
        return out

    # ── 여기부터 새로고침 경로 ────────────────────────────────────────
    # 먼저 예약한다 — 동시에 두 번 눌러도 DB의 원자적 함수가 한 번만
    # 허용한다(app/tools/supabase_tool.consume_refresh_quota).
    try:
        quota = supabase_tool.consume_refresh_quota(user.id, keyword_id, settings.REFRESH_QUOTA_PER_KEYWORD)
    except (SupabaseError, SupabaseUnavailable) as e:
        raise HTTPException(
            status_code=503,
            detail={"error_code": "refresh_unavailable", "message": f"쿼터 확인에 실패했습니다: {e}"},
        ) from e

    used, limit = quota.get("o_used", 0), quota.get("o_limit", settings.REFRESH_QUOTA_PER_KEYWORD)
    if not quota.get("o_allowed"):
        served = _serve_previous_or_regenerate(
            keyword_id, axis, body.count, min(used, MAX_VARIANT), period_key, "quota_spent", used, limit,
        )
        if served is not None:
            return served
        # 캐시가 없다 — 방어적으로 쿼터 소진 상태만 알리고 새로 만들지는 않는다.
        raise HTTPException(
            status_code=409,
            detail={"error_code": "quota_spent", "message": "이 키워드는 새로고침을 모두 사용했습니다."},
        )

    variant = min(used, MAX_VARIANT)

    # 직전(variant-1) 세트를 "이미 보여준 아이디어"로 프롬프트에 못박는다.
    exclude: list[dict] = []
    if variant > 0:
        prev_key = cache.cache_key(
            snapshot_info["snapshot_id"], keyword_id, axis.platform_key, axis.type_key, body.count,
            variant=variant - 1,
        )
        prev = cache.read(keyword_id, axis.platform_key, axis.type_key, prev_key)
        if prev:
            exclude = [
                {"name": i.get("name", ""), "approach": i.get("approach", ""), "slogan": i.get("slogan", "")}
                for i in prev.get("ideas", [])
            ]

    try:
        result, source = _run_agent_or_404_503_400(keyword_id, body, axis, exclude=exclude, variation=variant)
    except HTTPException:
        supabase_tool.release_refresh_quota(user.id, keyword_id)
        raise

    if source == "fallback":
        supabase_tool.release_refresh_quota(user.id, keyword_id)
        served = _serve_previous_or_regenerate(
            keyword_id, axis, body.count, variant - 1 if variant > 0 else 0, period_key, "fallback", used - 1, limit,
        )
        if served is not None:
            return served
        # 직전 세트도 없다(최초 시도부터 LLM이 죽어 있던 경우) — 방금 만든
        # 폴백이라도 보여준다. "새 AI 아이디어"는 아니라고 이유는 남긴다.
        data = result.model_dump()
        out = _stamp(data, period_key, source="fallback")
        out["refresh"] = _refresh_block(False, "fallback", used - 1, limit, variant - 1 if variant > 0 else 0)
        return out

    if exclude and dedupe.is_too_similar(result.ideas, exclude):
        supabase_tool.release_refresh_quota(user.id, keyword_id)
        served = _serve_previous_or_regenerate(
            keyword_id, axis, body.count, variant - 1, period_key, "too_similar", used - 1, limit,
        )
        if served is not None:
            return served
        # 이 경우도 극히 드물다 — 그냥 이번 결과를 보여준다(쿼터는 이미 반납했다).

    key = cache.cache_key(
        snapshot_info["snapshot_id"], keyword_id, axis.platform_key, axis.type_key, body.count, variant=variant,
    )
    data = result.model_dump()
    cache.write(keyword_id, axis.platform_key, axis.type_key, key, data)
    out = _stamp(data, period_key)
    out["refresh"] = _refresh_block(True, "ok", used, limit, variant)
    return out


def _run_agent_or_404_503_400(keyword_id: str, body: IdeaGenerateRequest, axis: ResolvedAxis, exclude: list[dict], variation: int):
    try:
        result = IdeaAgent().run(IdeaAgentInput(
            keyword_id=keyword_id, platform=body.platform, type=body.type, count=body.count,
            exclude=exclude, variation=variation,
        ))
        return result, result.source
    except KeywordNotFound as e:
        raise HTTPException(status_code=404, detail={"error_code": "keyword_not_found", "message": str(e)}) from e
    except SnapshotNotReady as e:
        raise HTTPException(status_code=503, detail={"error_code": "snapshot_not_ready", "message": str(e)}) from e
    except ValidationError as e:
        raise _bad_request(str(e)) from e


@router.get("/{keyword_id}/ideas")
def get_cached_ideas(
    keyword_id: str, platform: str, type: str, period: str = "하루", count: int = 3,
    user: CurrentUser | None = Depends(get_current_user_optional),
) -> dict:
    axis = _resolve_axis_or_400(platform, type)
    try:
        period_key = axes.normalize_period(period)
    except ValueError as e:
        raise _bad_request(str(e)) from e

    snapshot_info = _load_snapshot_info_or_404()

    # 이 사용자가 새로고침을 썼다면 그 variant를 읽어야 최신 세트가 보인다
    # (그렇지 않으면 새로고침 후 화면을 벗어났다 들어왔을 때 옛 세트가 보인다).
    variant = 0
    if user is not None and settings.supabase_ready:
        try:
            q = supabase_tool.get_refresh_quota(user.id, keyword_id, settings.REFRESH_QUOTA_PER_KEYWORD)
            variant = min(q["used"], MAX_VARIANT)
        except (SupabaseError, SupabaseUnavailable):
            variant = 0

    key = cache.cache_key(snapshot_info["snapshot_id"], keyword_id, axis.platform_key, axis.type_key, count, variant=variant)
    cached = cache.read(keyword_id, axis.platform_key, axis.type_key, key)
    if cached is None and variant != 0:
        key0 = cache.cache_key(snapshot_info["snapshot_id"], keyword_id, axis.platform_key, axis.type_key, count)
        cached = cache.read(keyword_id, axis.platform_key, axis.type_key, key0)
    if cached is None:
        raise HTTPException(
            status_code=404,
            detail={"error_code": "keyword_not_found", "message": "캐시된 아이디어가 없습니다. POST로 먼저 생성하세요."},
        )
    out = _stamp(cached, period_key, source="cache")
    out["refresh"] = _quota_snapshot(user, keyword_id)
    return out


class PromptRebuildRequest(BaseModel):
    platform: str
    type: str
    period: str = "하루"
    idea: IdeaSpec


@router.post("/{keyword_id}/ideas/prompt")
def rebuild_idea_prompt(keyword_id: str, body: PromptRebuildRequest) -> dict:
    """사용자가 손으로 고친 MVP를 반영해 프롬프트만 다시 조립한다.

    LLM을 부르지 않는다 — build_period_prompt()는 순수 문자열 조립이라
    아이디어 생성(POST /ideas)과 달리 캐시도 건드리지 않는다. 캐시는
    "LLM이 만든 원본"을 보관하는 자리이고, 여기서 만드는 건 사용자의
    개인 편집본이라 섞으면 다른 사용자가 남의 편집을 받게 된다.

    IA(idea.ia)는 화면에서는 안 보여도 그대로 왕복한다 — 프롬프트
    "# 2. 시스템 아키텍처 및 서비스 정보구조(IA)" 절이 이걸 그대로 쓴다.
    validate.check_idea()는 부르지 않는다: 그건 LLM 출력 품질 가드라서
    (depth1 개수·mvp_features 3~5개 등) 사람이 일부러 고친 값에 적용하면
    "화면엔 이미 떠 있는데 저장이 안 되는" 모순이 생긴다.
    """
    axis = _resolve_axis_or_400(body.platform, body.type)
    try:
        period_key = axes.normalize_period(body.period)
    except ValueError as e:
        raise _bad_request(str(e)) from e

    mvp = [f.strip() for f in body.idea.mvp_features if f and f.strip()]
    if not mvp:
        raise _bad_request("mvp_features는 최소 1개가 필요합니다.")
    if len(mvp) > 8:
        raise _bad_request("mvp_features는 최대 8개까지입니다.")
    idea = body.idea.model_copy(update={"mvp_features": mvp})

    try:
        kw = idea_tool.load_keyword(keyword_id)
    except KeywordNotFound as e:
        raise HTTPException(
            status_code=404,
            detail={"error_code": "keyword_not_found", "message": str(e)},
        ) from e
    except SnapshotNotReady as e:
        raise HTTPException(
            status_code=503,
            detail={"error_code": "snapshot_not_ready", "message": str(e)},
        ) from e

    prompts = {
        period: build_period_prompt(idea, kw["name"], axis, period)
        for period in ("day", "week", "month")
    }
    return {"period": period_key, "prompt": prompts[period_key], "prompts": prompts}
