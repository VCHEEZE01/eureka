"""
아이디어 생성 API — docs/트렌드_백엔드_설계.md 7절의
"POST /api/trends/{keyword_id}/ideas (나중) 아이디어 5개 만들기"를 채운다.

POST /api/trends/{keyword_id}/ideas          아이디어 생성 (캐시 히트 시 즉시 반환)
GET  /api/trends/{keyword_id}/ideas          캐시만 조회 (없으면 404)
POST /api/trends/{keyword_id}/ideas/prompt   사용자가 편집한 MVP로 프롬프트만 재조립

trend_routes.py와 같은 prefix("/api/trends")를 쓰지만 경로가 겹치지
않는다 (거기는 "", "/{keyword_id}"만 정의).
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ValidationError

from app.agents.idea_agent import IdeaAgent, IdeaAgentInput
from app.ideas import axes, cache
from app.ideas.axes import ResolvedAxis
from app.prompts.idea_prompts import build_period_prompt
from app.schemas.idea_models import IdeaSpec
from app.tools import idea_tool
from app.tools.idea_tool import KeywordNotFound, SnapshotNotReady

router = APIRouter(prefix="/api/trends", tags=["ideas"])


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


@router.post("/{keyword_id}/ideas")
def generate_ideas(keyword_id: str, body: IdeaGenerateRequest) -> dict:
    if not (1 <= body.count <= 5):
        raise _bad_request("count는 1~5여야 합니다.")

    axis = _resolve_axis_or_400(body.platform, body.type)
    try:
        period_key = axes.normalize_period(body.period)
    except ValueError as e:
        raise _bad_request(str(e)) from e

    try:
        snapshot_info = _load_snapshot_info_or_404()
    except SnapshotNotReady as e:
        raise HTTPException(
            status_code=503,
            detail={"error_code": "snapshot_not_ready", "message": str(e)},
        ) from e

    key = cache.cache_key(snapshot_info["snapshot_id"], keyword_id, axis.platform_key, axis.type_key, body.count)

    if not body.refresh:
        cached = cache.read(keyword_id, axis.platform_key, axis.type_key, key)
        if cached is not None:
            cached = dict(cached)
            cached["source"] = "cache"
            cached["config"] = dict(cached["config"])
            cached["config"]["period"] = period_key
            for idea in cached.get("ideas", []):
                idea["prompt"] = idea.get("prompts", {}).get(period_key, idea.get("prompt", ""))
            return cached

    try:
        result = IdeaAgent().run(
            IdeaAgentInput(keyword_id=keyword_id, platform=body.platform, type=body.type, count=body.count)
        )
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
    except ValidationError as e:
        raise _bad_request(str(e)) from e

    data = result.model_dump()
    cache.write(keyword_id, axis.platform_key, axis.type_key, key, data)

    data["config"]["period"] = period_key
    for idea in data.get("ideas", []):
        idea["prompt"] = idea.get("prompts", {}).get(period_key, idea.get("prompt", ""))
    return data


@router.get("/{keyword_id}/ideas")
def get_cached_ideas(keyword_id: str, platform: str, type: str, period: str = "하루", count: int = 3) -> dict:
    axis = _resolve_axis_or_400(platform, type)
    try:
        period_key = axes.normalize_period(period)
    except ValueError as e:
        raise _bad_request(str(e)) from e

    snapshot_info = _load_snapshot_info_or_404()
    key = cache.cache_key(snapshot_info["snapshot_id"], keyword_id, axis.platform_key, axis.type_key, count)
    cached = cache.read(keyword_id, axis.platform_key, axis.type_key, key)
    if cached is None:
        raise HTTPException(
            status_code=404,
            detail={"error_code": "keyword_not_found", "message": "캐시된 아이디어가 없습니다. POST로 먼저 생성하세요."},
        )
    cached = dict(cached)
    cached["source"] = "cache"
    cached["config"] = dict(cached["config"])
    cached["config"]["period"] = period_key
    for idea in cached.get("ideas", []):
        idea["prompt"] = idea.get("prompts", {}).get(period_key, idea.get("prompt", ""))
    return cached


def _load_snapshot_info_or_404() -> dict:
    return idea_tool.load_snapshot_info()


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
