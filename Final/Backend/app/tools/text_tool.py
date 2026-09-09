"""
텍스트 처리 도구 — 정제·PII 제거·규칙 판별.

쓰는 사람: ② 해석기 (판별 전 단계), ① 수집 에이전트 (저장 전 정제)

★ 이 파일은 순수 규칙·계산만 한다. LLM을 부르지 않고, 숫자를 만들어내지 않는다.
  이유: 판별의 1차 관문은 재현 가능해야 한다. 같은 입력이면 항상 같은 판정이 나와야
  "왜 버렸는지"를 나중에 설명할 수 있다.

근거 문서
  · docs/DATA_COLLECTION.md 3-2 정제 — 개인정보 제거와 원문 폐기
  · docs/DATA_COLLECTION.md 3-3 판별 — 불편을 말하는 글만 남기기
  · docs/DATA_COLLECTION.md 5절   불편 신호 사전
"""

import html
import re
from enum import Enum
from hashlib import sha256
from typing import Optional

from app.config.dictionaries import (
    AD_PATTERNS,
    PAIN_SIGNALS,
    need_signal_expressions,
)
from app.schemas.models import LicensePolicy, RawItem, SourceKind

# 절단하지 않고 정제만 하고 싶을 때 쓰는 상한. 스니펫은 이보다 길 수 없다.
_UNLIMITED = 1_000_000


# ══════════════════════════════════════════════
# 정규식 — 모듈 로드 시 한 번만 컴파일해서 재사용한다
# ══════════════════════════════════════════════

# ── 정제 (3-2)
# 블록 태그는 공백으로 바꾼다. <br>·</p> 자리에 단어가 붙어버리면 안 되기 때문.
_BLOCK_TAG_RE = re.compile(
    r"</?(?:br|p|div|li|tr|td|th|ul|ol|table|section|article|h[1-6])\b[^>]*>",
    re.IGNORECASE,
)
# 나머지 인라인 태그는 그냥 지운다. 검색 API의 <b> 하이라이트가 단어 중간에
# 들어오는 경우가 있어서(예: 번거<b>롭</b>다) 공백으로 바꾸면 단어가 쪼개진다.
_TAG_RE = re.compile(r"<[^>]*>")
# \s 는 \xa0 까지 잡지만 제로폭 문자는 못 잡는다. 명시적으로 넣는다.
_WS_RE = re.compile(r"[\s​‌‍⁠﻿]+")

# ── PII 제거 (3-2 1번). 배치·실시간 예외 없이 적용한다.
#    순서가 중요하다: 이메일 → 전화 → 주민번호 → 계좌 → 멘션 → 작성자
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+\s*@\s*[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
_PHONE_MOBILE_RE = re.compile(r"\b01[016-9][-.\s]?\d{3,4}[-.\s]?\d{4}\b")
_PHONE_AREA_RE = re.compile(r"\b0\d{1,2}[-.\s]\d{3,4}[-.\s]\d{4}\b")
_RRN_RE = re.compile(r"\b\d{6}\s*-\s*\d{7}\b")
# 마지막 묶음은 4자리 이상만 본다. \d{2,} 로 두면 "2026-09-09" 같은 날짜까지 지워진다.
_ACCOUNT_RE = re.compile(r"\b\d{2,6}-\d{2,6}-\d{4,8}\b")
_MENTION_RE = re.compile(r"@[A-Za-z0-9가-힣._-]{2,}")
# 구분자(공백·콜론)를 반드시 요구한다. 없으면 "작성자가 불편하다" 같은 일반 문장까지 지운다.
_AUTHOR_RE = re.compile(
    r"(?:작성자|글쓴이|작성인|닉네임)[\s:：]+[A-Za-z0-9가-힣][A-Za-z0-9가-힣._-]{0,15}"
)

_PII_RULES = (
    _EMAIL_RE,
    _PHONE_MOBILE_RE,
    _PHONE_AREA_RE,
    _RRN_RE,
    _ACCOUNT_RE,
    _MENTION_RE,
    _AUTHOR_RE,
)

# ── 문장 추출
# 말줄임(…, ..)은 문장 끝이 아니라 "여기서 잘렸다"는 표시다. 검색 API 스니펫의 특징.
_ELLIPSIS_RE = re.compile(r"\.{2,}|…+")
# 종결부호로 끝나는 덩어리 하나. 뒤에 닫는 따옴표·괄호가 붙는 것까지 포함한다.
_SENTENCE_RE = re.compile(r"[^.?!]*[.?!]+[\"'”’)\]】」』]*")
_HAS_CONTENT_RE = re.compile(r"[가-힣A-Za-z0-9]")

# ── 대상 명사 추정 (3-3 보류 조건)
# 형태소 분석기를 붙이지 않는다. "대상이 있는가"만 보면 되므로 근사로 충분하다.
_TOKEN_RE = re.compile(r"[가-힣]{2,}|[A-Za-z]{2,}")
# 어미로 끝나면 명사가 아니라 서술어로 본다.
_PREDICATE_TAIL_RE = re.compile(r"(?:다|요|죠|네|까|음|함|며|면|고|서|게|져|였|았|었)$")
# 대상을 가리키지 못하는 부사·지시어
_NON_TARGET_WORDS = frozenset(
    {
        "그냥", "다들", "진짜", "정말", "너무", "요즘", "이거", "그거", "저거",
        "뭔가", "자꾸", "아무", "그리고", "그래서", "하지만", "근데", "이런",
        "저런", "그런", "여기", "거기", "저기", "이제", "항상", "맨날", "완전",
        "진심", "약간", "조금", "많이", "엄청", "되게", "아주", "자체", "그거참",
        "아니", "역시", "정도", "때문", "이것", "그것", "저것", "무슨", "어디",
    }
)

# 보류 판정 문턱. 아래 둘을 모두 만족해야 "대상 불분명"으로 본다.
_VAGUE_MAX_LEN = 60  # 정제 후 이보다 짧고
_VAGUE_MIN_TARGETS = 2  # 대상 후보 명사가 이보다 적으면

# 소스 가중 — 신뢰도가 아니라 "불편 진술의 밀도"가 높은 순서다 (DATA_SOURCES 참고).
_SOURCE_WEIGHT: dict[SourceKind, int] = {
    SourceKind.PUBLIC_DATA: 3,
    SourceKind.COMMUNITY: 2,
}

MIN_SNIPPET_LEN = 30  # DATA_COLLECTION 3-3 통과 조건: 본문 30자 이상


# ══════════════════════════════════════════════
# 정제 (docs/DATA_COLLECTION.md 3-2)
# ══════════════════════════════════════════════


def clean_text(s: str, max_len: int = 200) -> str:
    """HTML·공백을 걷어낸 표시용 텍스트. 검색 API가 섞어 보내는 <b> 하이라이트를 지운다."""
    if not s:
        return ""
    s = _BLOCK_TAG_RE.sub(" ", s)
    s = _TAG_RE.sub("", s)
    s = html.unescape(s)
    s = _WS_RE.sub(" ", s).strip()
    if max_len >= 0 and len(s) > max_len:
        s = s[:max_len].rstrip()
    return s


def strip_pii(s: str) -> str:
    """작성자 식별정보·연락처를 지운다. 3-2 1번 — 배치·실시간 예외 없이 적용."""
    if not s:
        return ""
    for pattern in _PII_RULES:
        # 빈 문자열이 아니라 공백으로 치환한다. 안 그러면 앞뒤 단어가 붙어버린다.
        s = pattern.sub(" ", s)
    return _WS_RE.sub(" ", s).strip()


def content_hash(title: str, snippet: str) -> str:
    """
    중복 판정 전용 해시. 3-2 3번 — 원문 대신 이것만 남긴다.

    ★ 정제한 뒤에 해싱하므로 태그·공백 차이에 불변이다.
      절단 없이 해싱한다. 200자에서 잘라 버리면 뒤쪽만 다른 글이 같은 해시가 된다.
    """
    body = f"{clean_text(title, _UNLIMITED)}\n{clean_text(snippet, _UNLIMITED)}"
    return sha256(body.encode("utf-8")).hexdigest()[:32]


# ══════════════════════════════════════════════
# 신호 탐지 (docs/DATA_COLLECTION.md 5절)
# ══════════════════════════════════════════════


def signal_hits(text: str) -> dict[str, list[str]]:
    """불편 표현이 실제로 등장한 유형만 담아 반환한다. 안 걸린 유형은 키를 넣지 않는다."""
    if not text:
        return {}
    hits: dict[str, list[str]] = {}
    for signal_type, expressions in PAIN_SIGNALS.items():
        found = [e for e in expressions if e in text]
        if found:
            hits[signal_type] = found
    return hits


def has_need_signal(text: str) -> bool:
    """결핍 신호 등장 여부 = 화면 '필요도'의 재료 (docs/DATA_SPEC.md 4절)."""
    if not text:
        return False
    return any(e in text for e in need_signal_expressions())


def is_ad(text: str) -> bool:
    """광고·홍보 패턴 여부. 3-3 통과 조건."""
    if not text:
        return False
    return any(p in text for p in AD_PATTERNS)


def signal_score(item: RawItem) -> int:
    """
    LLM에 넣을 상위 N건을 고르는 랭킹 점수. 순수 계산이며 화면에 노출하지 않는다.

    유형 다양성 × 2 + 걸린 표현 수 + 소스 가중.
    다양성에 가중을 두는 이유: 한 표현이 여러 번 나오는 것보다
    서로 다른 유형이 함께 걸린 글이 진짜 불편일 확률이 높다.
    """
    hits = signal_hits(_item_text(item))
    diversity = len(hits)
    total = sum(len(v) for v in hits.values())
    return diversity * 2 + total + _SOURCE_WEIGHT.get(item.source_kind, 0)


# ══════════════════════════════════════════════
# 발췌 (docs/DATA_COLLECTION.md 3-2 4번)
# ══════════════════════════════════════════════


def extract_sentences(text: str) -> list[str]:
    """
    완결된 문장만 뽑는다. 검색 API 스니펫은 "...번거롭다는 글이..." 같은 조각이라
    그대로는 인용문이 못 된다. 말줄임 뒤에 오는 첫 덩어리는 앞이 잘린 것으로 보고 버린다.
    """
    cleaned = clean_text(text, _UNLIMITED)
    if not cleaned:
        return []

    # 말줄임을 경계로 자른다. 경계 뒤 첫 덩어리는 앞이 잘려 있다.
    segments: list[tuple[str, bool]] = []  # (조각, 앞이 온전한가)
    pos = 0
    for m in _ELLIPSIS_RE.finditer(cleaned):
        segments.append((cleaned[pos : m.start()], pos == 0))
        pos = m.end()
    segments.append((cleaned[pos:], pos == 0))

    sentences: list[str] = []
    for segment, head_intact in segments:
        for i, m in enumerate(_SENTENCE_RE.finditer(segment)):
            if i == 0 and not head_intact:
                continue  # 말줄임 직후 — 앞이 잘린 조각
            candidate = m.group().strip().lstrip("\"'“‘([【「『")
            if candidate and _HAS_CONTENT_RE.search(candidate):
                sentences.append(candidate)
    return sentences


def pick_excerpt(item: RawItem, max_len: int = 25) -> Optional[str]:
    """
    화면의 "유저 한마디". 없으면 None — 그 근거는 발췌 없이 요약만 쓴다.

    3-2 4번: license 가 excerpt-ok 인 경우에만 25자 이내 발췌를 남긴다.
    """
    if item.license is not LicensePolicy.EXCERPT_OK:
        return None
    for sentence in extract_sentences(item.snippet) + extract_sentences(item.title):
        if len(sentence) <= max_len and signal_hits(sentence):
            return sentence
    return None


# ══════════════════════════════════════════════
# 규칙 판별 (docs/DATA_COLLECTION.md 3-3)
# ══════════════════════════════════════════════


class Verdict(str, Enum):
    """규칙 판별 결과. HOLD 는 버리지 않고 미분류로 둔다."""

    PASS = "pass"
    HOLD = "hold"
    DROP = "drop"


def rule_judge(
    item: RawItem, seen_ids: set[str], seen_hashes: set[str]
) -> tuple[Verdict, str]:
    """
    LLM 앞단의 1차 관문. 3-3 통과·보류 조건을 그대로 옮겼다.

    ★ seen_ids / seen_hashes 를 여기서 갱신하지 않는다. 호출자가 관리한다.
      이유: 같은 입력에 항상 같은 답이 나와야 판정을 재현할 수 있다.
    """
    item_hash = item.content_hash or content_hash(item.title, item.snippet)
    if item.id in seen_ids or item_hash in seen_hashes:
        return Verdict.DROP, "중복"

    snippet = clean_text(item.snippet, _UNLIMITED)
    if len(snippet) < MIN_SNIPPET_LEN:
        return Verdict.DROP, "30자 미만"

    text = _item_text(item)
    if is_ad(text):
        return Verdict.DROP, "광고·홍보 패턴"

    hits = signal_hits(text)
    if not hits:
        return Verdict.DROP, "불편 신호 없음"

    if _is_vague_target(text, hits):
        return Verdict.HOLD, "대상 불분명"

    return Verdict.PASS, _summarize_hits(hits)


# ══════════════════════════════════════════════
# 내부 헬퍼
# ══════════════════════════════════════════════


def _item_text(item: RawItem) -> str:
    """판별에 쓰는 정제 텍스트. 제목과 스니펫을 함께 본다."""
    return clean_text(f"{item.title} {item.snippet}", _UNLIMITED)


def _target_tokens(text: str, hits: dict[str, list[str]]) -> list[str]:
    """
    "무엇에 대한 불편인가"를 가리킬 수 있는 명사 후보. 근사치다.

    걸린 불편 표현·부사·서술어를 걷어내고 남는 2자 이상 덩어리를 센다.
    """
    stripped = text
    for expressions in hits.values():
        for e in expressions:
            stripped = stripped.replace(e, " ")
    return [
        t
        for t in _TOKEN_RE.findall(stripped)
        if t not in _NON_TARGET_WORDS and not _PREDICATE_TAIL_RE.search(t)
    ]


def _is_vague_target(text: str, hits: dict[str, list[str]]) -> bool:
    """3-3 보류 조건: 불편 신호는 있으나 대상이 불분명함 ("그냥 다 짜증난다")."""
    if len(text) >= _VAGUE_MAX_LEN:
        return False
    return len(set(_target_tokens(text, hits))) < _VAGUE_MIN_TARGETS


def _summarize_hits(hits: dict[str, list[str]]) -> str:
    """통과 사유로 남길 신호 요약. 예: '직접 불만: 짜증·답답 / 반복 노동: 매번'"""
    return " / ".join(f"{t}: {'·'.join(e)}" for t, e in hits.items())
