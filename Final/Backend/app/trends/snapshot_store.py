"""
게시된 최신 스냅샷을 읽는 곳 — trend_routes.py 와 tools/idea_tool.py 가 같이 쓴다.

평소에는 build_snapshot.py 가 써 둔 data/trends/latest_snapshot.json 을 읽기만
한다. 파일이 없으면 None → 호출하는 쪽이 503(snapshot_not_ready)을 낸다.

★ Vercel(settings.VERCEL)에서만 예외: data/ 는 gitignore 대상이라 배포에
  올라가지 않고, 함수 폴더는 읽기 전용이라 배치로 파일을 써 둘 수도 없다.
  그래서 파일이 없으면 fixtures 로 메모리에서 한 번 만들어 인스턴스가 살아
  있는 동안 재사용한다. build_snapshot() 을 그대로 부르므로 계산 규칙은 같다.
"""

import copy
import json
from functools import lru_cache

from app.config.settings import settings
from app.trends import build_snapshot as _builder


def load_latest() -> dict | None:
    path = _builder.LATEST_PATH
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    if settings.VERCEL:
        # 호출하는 쪽이 응답을 고쳐 써도 캐시된 원본이 오염되지 않게 복사해서 준다.
        return copy.deepcopy(_build_in_memory())
    return None


@lru_cache(maxsize=1)
def _build_in_memory() -> dict:
    return _builder.build_snapshot()
