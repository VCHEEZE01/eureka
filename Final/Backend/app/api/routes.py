"""
프론트엔드가 부르는 입구.

TODO(담당자): Phase 2에서 채운다. 지금은 뼈대만.

★ 주의: 실시간 생성(F05·F07)은 단발 응답이 아니라
  진행 상태를 흘려보내는 스트리밍이어야 한다.
  나중에 붙이려면 API를 다시 짜야 하므로 처음부터 이렇게 설계한다.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


# TODO: GET  /problems           문제 목록 (F03)
# TODO: GET  /problems/{id}      문제 상세 (F04)
# TODO: GET  /problems/{id}/ideas 기본 아이디어 (F06)
# TODO: POST /combine            문제 조합 (F05) — 스트리밍
# TODO: POST /personalize        개인화 (F07) — 스트리밍
