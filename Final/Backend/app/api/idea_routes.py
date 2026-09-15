"""
아이디어 생성 API — docs/트렌드_백엔드_설계.md 7절의
"POST /api/trends/{keyword_id}/ideas (나중) 아이디어 5개 만들기"를 채운다.

POST /api/trends/{keyword_id}/ideas   아이디어 생성 (캐시 히트 시 즉시 반환)
GET  /api/trends/{keyword_id}/ideas   캐시만 조회 (없으면 404)

trend_routes.py와 같은 prefix("/api/trends")를 쓰지만 경로가 겹치지
않는다 (거기는 "", "/{keyword_id}"만 정의).
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ValidationError

from app.agents.idea_agent import IdeaAgent, IdeaAgentInput
from app.ideas import axes, cache
from app.ideas.axes import ResolvedAxis
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
    from app.tools import idea_tool

    return idea_tool.load_snapshot_info()
