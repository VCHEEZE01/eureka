"""
아이디어 생성 결과 파일 캐시.

app/trends/ 가 파일(JSON) 하나로 스냅샷을 다루는 것과 같은 방식이다
(DB가 없다 — app/tools/db_tool.py 참고). DB가 생기면 이 파일만 바꾸면
된다.

★ 캐시 키에 period(기간)를 넣지 않는다. 아이디어 자체는 기간에 따라
  안 변하고 바이브코딩 프롬프트만 변하는데, 응답에 day/week/month
  프롬프트를 전부 담으므로 기간을 바꿔도 재생성이 필요 없다.

★ 2026-09-19: variant 를 추가했다. "새로고침"이 같은 키에 덮어쓰면
  ① 원래 3개가 복구 불가하게 사라지고 ② 한 사람의 새로고침이 이
  캐시를 공유하는 다른 사용자가 보는 결과까지 바꿔버린다 — 그 사람의
  쿼터는 그대로인데. variant=0(기본값, 최초 생성)은 절대 덮어쓰지
  않고, 새로고침마다 variant를 올려 별도 파일에 쓴다.
  variant=0 은 문자열이 예전과 바이트 단위로 동일해서 기존 디스크
  캐시와 테스트가 그대로 유효하다.
"""

import hashlib
import json
from pathlib import Path

from app.config.settings import settings
from app.prompts.idea_prompts import PROMPT_VERSION


def cache_key(
    snapshot_id: str, keyword_id: str, platform_key: str, type_key: str, count: int,
    variant: int = 0,
) -> str:
    raw = f"{snapshot_id}|{keyword_id}|{platform_key}|{type_key}|{count}|v{PROMPT_VERSION}"
    if variant:
        raw = f"{raw}|r{variant}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _path(keyword_id: str, platform_key: str, type_key: str, key: str) -> Path:
    return settings.IDEAS_DIR / keyword_id / f"{platform_key}-{type_key}-{key}.json"


def read(keyword_id: str, platform_key: str, type_key: str, key: str) -> dict | None:
    path = _path(keyword_id, platform_key, type_key, key)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def write(keyword_id: str, platform_key: str, type_key: str, key: str, data: dict) -> None:
    path = _path(keyword_id, platform_key, type_key, key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
