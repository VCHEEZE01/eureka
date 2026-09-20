"""
새로고침이 "매번 같은 3개"를 내던 버그를 고친 3개 조각의 단위 테스트.
   1. app/ideas/cache.py       — 캐시 키에 variant 추가
   2. app/prompts/idea_prompts.py — exclude 프롬프트 블록
   3. app/ideas/dedupe.py      — 유사도 가드

쿼터·라우트 배선(누가 언제 이 조각을 부르는지)은 인증이 붙는 다음 단계에서
테스트한다. 여기는 각 조각이 "기본값일 때 오늘과 완전히 같다"와
"켜면 실제로 다르게 동작한다"만 증명한다.
"""

from app.ideas import axes, cache, dedupe, fallback
from app.prompts.idea_prompts import build_idea_prompt


def _kw():
    return {"name": "두잇", "category": "생산성", "summary": "", "analysis": {}}


def _axis():
    return axes.resolve(axes.PLATFORM_SPEC["web"]["label"], axes.TYPE_SPEC["utility"]["label"])


# ── cache.cache_key: variant ────────────────────────────────────

def test_cache_key_variant_default_is_byte_identical_to_before():
    """variant를 안 주는 기존 호출부는 키가 한 글자도 안 바뀌어야 한다
    — 안 그러면 디스크에 쌓인 캐시가 전부 무효화된다."""
    no_variant = cache.cache_key("snap1", "r1", "web", "utility", 3)
    explicit_zero = cache.cache_key("snap1", "r1", "web", "utility", 3, variant=0)
    assert no_variant == explicit_zero


def test_cache_key_variant_nonzero_produces_different_key():
    base = cache.cache_key("snap1", "r1", "web", "utility", 3)
    v1 = cache.cache_key("snap1", "r1", "web", "utility", 3, variant=1)
    v2 = cache.cache_key("snap1", "r1", "web", "utility", 3, variant=2)
    assert len({base, v1, v2}) == 3, "variant마다 서로 다른 키가 나와야 한다"


def test_cache_key_variant_does_not_collide_with_count_change():
    """variant 문자열 조립이 우연히 다른 축과 부딪히지 않는지 — sha1 앞이라
    실수로 같은 문자열을 만들면(예: count=31과 variant=1이 이어붙어 보이는 등)
    충돌할 수 있어 명시적으로 확인한다."""
    a = cache.cache_key("snap1", "r1", "web", "utility", 3, variant=1)
    b = cache.cache_key("snap1", "r1", "web", "utility", 31)
    assert a != b


# ── build_idea_prompt: exclude ──────────────────────────────────

def test_exclude_block_absent_by_default():
    kw, axis = _kw(), _axis()
    with_none = build_idea_prompt(kw, axis, 3)
    with_empty = build_idea_prompt(kw, axis, 3, exclude=[])
    assert with_none == with_empty
    assert "이미 보여준" not in with_none


def test_exclude_block_lists_previous_ideas_when_present():
    kw, axis = _kw(), _axis()
    prev = [
        {"name": "두잇 파인더", "approach": "데이터 큐레이션 & 실시간 레이더", "slogan": "한눈에 확인"},
        {"name": "두잇 도감", "approach": "게이미피케이션 & 수집 도감", "slogan": "스탬프로 모으기"},
    ]
    prompt = build_idea_prompt(kw, axis, 3, exclude=prev)
    assert "이미 보여준" in prompt
    assert "두잇 파인더" in prompt
    assert "두잇 도감" in prompt
    assert "겹치면 안 된다" in prompt


def test_exclude_block_tolerates_missing_fields():
    """exclude 항목에 approach/slogan이 없어도 죽지 않아야 한다
    (프론트가 보내는 값이 항상 완전하다고 믿지 않는다)."""
    kw, axis = _kw(), _axis()
    prompt = build_idea_prompt(kw, axis, 3, exclude=[{"name": "이름만 있음"}])
    assert "이름만 있음" in prompt


# ── dedupe.is_too_similar ────────────────────────────────────────

def test_dedupe_flags_identical_name_sets():
    ideas = fallback.build("두잇", _axis(), count=3)
    assert dedupe.is_too_similar(ideas, ideas) is True


def test_dedupe_passes_when_no_names_overlap():
    a = fallback.build("두잇", _axis(), count=3)
    prev_dicts = [{"name": "완전히 다른 이름 1"}, {"name": "완전히 다른 이름 2"}, {"name": "완전히 다른 이름 3"}]
    assert dedupe.is_too_similar(a, prev_dicts) is False


def test_dedupe_handles_mixed_dict_and_model_input():
    """previous_ideas는 캐시에서 막 읽은 raw dict, new_ideas는 방금 만든
    IdeaSpec — 실제 호출부에서 섞여 들어올 수 있는 조합이다."""
    ideas = fallback.build("두잇", _axis(), count=3)
    prev_as_dicts = [{"name": i.name} for i in ideas]
    assert dedupe.is_too_similar(ideas, prev_as_dicts) is True


def test_dedupe_ignores_punctuation_and_case_differences():
    class Fake:
        def __init__(self, name):
            self.name = name

    new = [Fake("두잇 Finder (Beta)")]
    prev = [{"name": "두잇 finder(beta)"}]
    assert dedupe.is_too_similar(new, prev, threshold=1.0) is True


def test_dedupe_empty_inputs_never_block():
    assert dedupe.is_too_similar([], []) is False
    assert dedupe.is_too_similar([], [{"name": "x"}]) is False
    ideas = fallback.build("두잇", _axis(), count=3)
    assert dedupe.is_too_similar(ideas, []) is False
