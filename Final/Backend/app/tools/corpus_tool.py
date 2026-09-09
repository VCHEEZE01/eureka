"""
코퍼스 도구 — JSONL 임시 저장소.

★ 이건 db_tool 의 자리를 잠깐 대신하는 것이다.
  DB(SQLite / PostgreSQL+pgvector / Supabase)가 정해지기 전까지,
  수집한 RawItem 을 잃어버리지 않고 쌓아 두기 위한 파일 저장소다.

  save_raw_items() 의 시그니처를 db_tool.save_raw_items() 와 똑같이 맞춰 두었다.
  나중에 DB가 붙으면 import 한 줄만 바꾸면 된다.

────────────────────────────────────────────────
디렉터리 (전부 settings.CORPUS_DIR 밑, 전부 append-only)
────────────────────────────────────────────────
    raw/{주차}/{카테고리}.jsonl          RawItem      ★ 절대 지우지 않는다
    judgements/{주차}/{카테고리}.jsonl   Judgement
    held/{주차}/{카테고리}.jsonl         규칙으로 판별 못 해 보류한 RawItem
    overflow/{주차}/{카테고리}.jsonl     LLM 상한을 넘겨 다음 주로 미룬 RawItem
    pending/candidates.jsonl             MIN_GROUP_SIZE 미만이라 승격 대기중인 묶음
    index/seen_ids.txt                   다음 배치의 중복 판정 근거
    index/seen_hashes.txt
    manifests/{주차}.json                배치 1회의 모든 숫자

주차는 ISO 주차 "2026-W37". 카테고리는 파일명에 쓰려고 "/" 를 "_" 로 바꾼다
("IT/생산성" → "IT_생산성").

★ append-only 인 이유
  RawItem 은 case_count 의 유일한 근거다(models.py). 한 번 쓴 줄은 고치지도
  지우지도 않는다. 지우는 건 테스트용 reset() 뿐이고, 그것도 CORPUS_DIR 밖으로
  나가지 못하게 막아 두었다.
"""

from __future__ import annotations

import json
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable, Optional, Sequence

from app.config.dictionaries import DOMAIN_KEYWORDS
from app.config.settings import settings
from app.schemas.models import Category, Judgement, ProblemCandidate, RawItem

# ── 디렉터리 이름. 문자열을 흩어 놓지 않으려고 여기 모아 둔다 ──
RAW_DIR = "raw"
JUDGEMENT_DIR = "judgements"
HELD_DIR = "held"
OVERFLOW_DIR = "overflow"
PENDING_DIR = "pending"
INDEX_DIR = "index"
MANIFEST_DIR = "manifests"

PENDING_CANDIDATES_FILE = "candidates.jsonl"
SEEN_IDS_FILE = "seen_ids.txt"
SEEN_HASHES_FILE = "seen_hashes.txt"

# 카테고리를 특정하지 못한 원문이 가는 곳. 버리지 않는다.
UNKNOWN_CATEGORY_SLUG = "_미분류"


# ══════════════════════════════════════════════
# 경로 계산
# ══════════════════════════════════════════════


def week_key(d: Optional[date] = None) -> str:
    """ISO 주차 문자열. 예: 2026-W37."""
    d = d or date.today()
    if isinstance(d, datetime):
        d = d.date()
    iso = d.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def recent_weeks(weeks: int = 4, end: Optional[date] = None) -> list[str]:
    """최근 N주의 주차 키. 최신이 앞이다. 중복 없이 돌려준다."""
    end = end or date.today()
    keys: list[str] = []
    for i in range(max(weeks, 0)):
        k = week_key(end - timedelta(weeks=i))
        if k not in keys:
            keys.append(k)
    return keys


def category_slug(category: Category | str) -> str:
    """파일명으로 쓸 수 있게 "/" 를 "_" 로 바꾼다."""
    value = category.value if isinstance(category, Category) else str(category)
    return value.replace("/", "_")


_SLUG_TO_CATEGORY = {category_slug(c): c for c in Category}

# 긴 키워드를 먼저 본다. "카드 명세서" 가 "카드" 보다 앞서야 한다.
_KEYWORD_TO_CATEGORY: list[tuple[str, Category]] = sorted(
    ((kw, cat) for cat, kws in DOMAIN_KEYWORDS.items() for kw in kws),
    key=lambda pair: -len(pair[0]),
)


def category_of_slug(slug: str) -> Optional[Category]:
    """파일명 → 카테고리. 미분류면 None."""
    return _SLUG_TO_CATEGORY.get(slug)


def infer_category(item: RawItem) -> Optional[Category]:
    """
    RawItem 에는 카테고리 필드가 없다. 검색어로 되짚는다.

    query_keyword 는 "도메인 키워드 × 불편 표현"으로 만들어지므로
    (dictionaries.DOMAIN_KEYWORDS), 그 안에 도메인 키워드가 들어 있다.
    ★ 검색어를 먼저 본다 — 어떤 검색어로 걸렸는지가 출처이고,
      제목은 다른 카테고리의 단어를 우연히 품고 있을 수 있다.
    못 찾으면 None — 버리지 않고 _미분류 로 간다.
    """
    for haystack in (item.query_keyword, item.title):
        for keyword, category in _KEYWORD_TO_CATEGORY:
            if keyword in haystack:
                return category
    return None


def corpus_root() -> Path:
    """저장소 루트. 설정을 호출 시점에 읽는다(테스트가 갈아끼울 수 있게)."""
    return Path(settings.CORPUS_DIR)


def _path(*parts: str) -> Path:
    return corpus_root().joinpath(*parts)


def _bucket_path(kind: str, week: str, slug: str) -> Path:
    return _path(kind, week, f"{slug}.jsonl")


# ══════════════════════════════════════════════
# 파일 입출력 — 전부 append-only
# ══════════════════════════════════════════════


def _append_lines(path: Path, lines: Sequence[str]) -> None:
    if not lines:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for line in lines:
            f.write(line.replace("\n", " ") + "\n")


def _read_lines(path: Path) -> list[str]:
    """파일이 없으면 빈 목록. 예외를 내지 않는다."""
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def _read_models(path: Path, model: type) -> list:
    """깨진 줄은 건너뛴다. 한 줄 때문에 배치 전체가 멈추면 안 된다."""
    out = []
    for line in _read_lines(path):
        try:
            out.append(model.model_validate_json(line))
        except Exception:
            continue
    return out


def _dump(items: Iterable) -> list[str]:
    return [i.model_dump_json() for i in items]


def _bucket_files(kind: str, week: Optional[str], category: Optional[Category]):
    """(주차, 슬러그, 경로) 를 순회한다. 없는 디렉터리는 조용히 건너뛴다."""
    base = _path(kind)
    if not base.is_dir():
        return
    weeks = [week] if week else sorted(p.name for p in base.iterdir() if p.is_dir())
    wanted = category_slug(category) if category else None
    for wk in weeks:
        wdir = base / wk
        if not wdir.is_dir():
            continue
        for f in sorted(wdir.glob("*.jsonl")):
            slug = f.stem
            if wanted and slug != wanted:
                continue
            yield wk, slug, f


# ══════════════════════════════════════════════
# 원문 (raw) — ★ db_tool 과 같은 시그니처
# ══════════════════════════════════════════════


def save_raw_items(items: list[RawItem], *, category: Optional[Category] = None) -> None:
    """
    수집한 원문을 저장한다. 절대 삭제하지 않는다.

    ★ seen_ids / seen_hashes 인덱스도 같이 갱신한다.
      이게 다음 배치의 중복 판정 근거다.

    category 를 주면 그대로 쓰고, 안 주면 검색어로 되짚는다.
    db_tool.save_raw_items(items) 와 호출 방식이 같다(추가 인자는 키워드 전용).
    """
    if not items:
        return

    keep_snippet = settings.CORPUS_KEEP_SNIPPET
    seen_ids, seen_hashes = load_seen()

    buckets: dict[tuple[str, str], list[str]] = {}
    new_ids: list[str] = []
    new_hashes: list[str] = []

    for item in items:
        cat = category or infer_category(item)
        slug = category_slug(cat) if cat else UNKNOWN_CATEGORY_SLUG
        week = week_key(item.collected_at.date())

        # CORPUS_KEEP_SNIPPET=false 는 보수적 운영 스위치다.
        # 원문 발췌를 아예 남기지 않고 메타만 남긴다.
        record = item if keep_snippet else item.model_copy(update={"snippet": ""})
        buckets.setdefault((week, slug), []).append(record.model_dump_json())

        if item.id and item.id not in seen_ids:
            seen_ids.add(item.id)
            new_ids.append(item.id)
        if item.content_hash and item.content_hash not in seen_hashes:
            seen_hashes.add(item.content_hash)
            new_hashes.append(item.content_hash)

    for (week, slug), lines in buckets.items():
        _append_lines(_bucket_path(RAW_DIR, week, slug), lines)

    _append_lines(_path(INDEX_DIR, SEEN_IDS_FILE), new_ids)
    _append_lines(_path(INDEX_DIR, SEEN_HASHES_FILE), new_hashes)


def load_raw_items(
    week: Optional[str] = None, category: Optional[Category] = None
) -> list[RawItem]:
    """week 를 안 주면 전 주차, category 를 안 주면 전 카테고리."""
    out: list[RawItem] = []
    for _, _, path in _bucket_files(RAW_DIR, week, category):
        out.extend(_read_models(path, RawItem))
    return out


def load_seen() -> tuple[set[str], set[str]]:
    """(이미 본 id, 이미 본 content_hash). 파일이 없으면 빈 집합."""
    ids = set(_read_lines(_path(INDEX_DIR, SEEN_IDS_FILE)))
    hashes = set(_read_lines(_path(INDEX_DIR, SEEN_HASHES_FILE)))
    return ids, hashes


# ══════════════════════════════════════════════
# 판정 (judgements)
# ══════════════════════════════════════════════


def save_judgements(
    items: list[Judgement], category: Category, *, week: Optional[str] = None
) -> None:
    _append_lines(
        _bucket_path(JUDGEMENT_DIR, week or week_key(), category_slug(category)),
        _dump(items),
    )


def load_judgements(
    week: Optional[str] = None, category: Optional[Category] = None
) -> list[Judgement]:
    out: list[Judgement] = []
    for _, _, path in _bucket_files(JUDGEMENT_DIR, week, category):
        out.extend(_read_models(path, Judgement))
    return out


def load_pending_judgements(weeks: int = 4) -> list[Judgement]:
    """
    최근 N주의 판정을 모아 준다.

    묶기는 한 주 안에서만 하면 5건을 못 채운다. 지난 주차까지 같이 봐야
    "유사한 글 5건 이상" 조건(MIN_GROUP_SIZE)이 현실적으로 성립한다.
    """
    out: list[Judgement] = []
    for wk in recent_weeks(weeks):
        out.extend(load_judgements(week=wk))
    return out


# ══════════════════════════════════════════════
# 보류 (held) · 이월 (overflow)
# ══════════════════════════════════════════════


def save_held(
    items: list[RawItem], category: Category, *, week: Optional[str] = None
) -> None:
    """규칙으로 광고인지 불편인지 못 가른 것들. 사람이 나중에 본다."""
    _append_lines(
        _bucket_path(HELD_DIR, week or week_key(), category_slug(category)),
        _dump(items),
    )


def load_held(
    week: Optional[str] = None, category: Optional[Category] = None
) -> list[RawItem]:
    out: list[RawItem] = []
    for _, _, path in _bucket_files(HELD_DIR, week, category):
        out.extend(_read_models(path, RawItem))
    return out


def save_overflow(
    items: list[RawItem], category: Category, *, week: Optional[str] = None
) -> None:
    """MAX_LLM_ITEMS 를 넘겨 이번 주에 못 돌린 것들. 다음 주에 먼저 처리한다."""
    _append_lines(
        _bucket_path(OVERFLOW_DIR, week or week_key(), category_slug(category)),
        _dump(items),
    )


def load_overflow(
    week: Optional[str] = None, category: Optional[Category] = None
) -> list[RawItem]:
    out: list[RawItem] = []
    for _, _, path in _bucket_files(OVERFLOW_DIR, week, category):
        out.extend(_read_models(path, RawItem))
    return out


# ══════════════════════════════════════════════
# 승격 대기 묶음 (pending)
# ══════════════════════════════════════════════


def save_pending_candidates(groups: list[ProblemCandidate]) -> None:
    """MIN_GROUP_SIZE 미만이라 아직 문제로 못 올리는 묶음. 다음 주에 다시 본다."""
    _append_lines(_path(PENDING_DIR, PENDING_CANDIDATES_FILE), _dump(groups))


def load_pending_candidates() -> list[ProblemCandidate]:
    return _read_models(_path(PENDING_DIR, PENDING_CANDIDATES_FILE), ProblemCandidate)


# ══════════════════════════════════════════════
# 매니페스트 — 배치 1회의 모든 숫자
# ══════════════════════════════════════════════


def write_manifest(data: dict) -> None:
    """
    ★ 숫자는 여기 남는다. LLM이 아니라 실행 결과가 만든 숫자다.

    data 에 "week" 가 있으면 그 주차로, 없으면 이번 주차로 쓴다.
    """
    payload = dict(data)
    week = str(payload.get("week") or week_key())
    payload["week"] = week
    payload.setdefault("written_at", datetime.now().isoformat(timespec="seconds"))

    path = _path(MANIFEST_DIR, f"{week}.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def read_manifest(week: Optional[str] = None) -> Optional[dict]:
    """week 를 안 주면 가장 최근 주차. 없으면 None."""
    base = _path(MANIFEST_DIR)
    if not base.is_dir():
        return None
    if week:
        path = base / f"{week}.json"
    else:
        files = sorted(base.glob("*.json"))  # ISO 주차는 사전순 = 시간순
        if not files:
            return None
        path = files[-1]
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def list_manifest_weeks() -> list[str]:
    base = _path(MANIFEST_DIR)
    if not base.is_dir():
        return []
    return sorted(p.stem for p in base.glob("*.json"))


# ══════════════════════════════════════════════
# 테스트용
# ══════════════════════════════════════════════


def reset() -> None:
    """
    CORPUS_DIR 안을 비운다. 테스트 전용.

    ★ CORPUS_DIR 밖으로는 절대 나가지 않는다.
      루트가 너무 얕거나(/, /tmp 같은) 심링크로 밖을 가리키면 아무것도 안 한다.
    """
    root = corpus_root().resolve()
    if not root.is_dir():
        return
    # "/" 나 "/data" 같은 얕은 경로를 통째로 지우는 사고를 막는다.
    if len(root.parts) < 3:
        raise RuntimeError(f"CORPUS_DIR 이 너무 얕아 지울 수 없다: {root}")

    for child in root.iterdir():
        if child.is_symlink():
            child.unlink()
            continue
        if not child.resolve().is_relative_to(root):
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
