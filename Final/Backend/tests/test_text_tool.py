"""
app/tools/text_tool.py 규칙 검증.

근거: docs/DATA_COLLECTION.md 3-2(정제) · 3-3(판별)
★ 여기서 검증하는 것은 "규칙이 문서대로 동작하는가"다. LLM은 개입하지 않는다.
"""

from datetime import datetime

import pytest

from app.config.dictionaries import PAIN_SIGNALS, PAIN_SIGNALS_TIER1, PAIN_SIGNALS_TIER2
from app.schemas.models import CollectMode, LicensePolicy, RawItem, SourceKind
from app.tools.text_tool import (
    Verdict,
    clean_text,
    content_hash,
    extract_sentences,
    has_need_signal,
    has_payment_signal,
    is_ad,
    item_text,
    payment_signal_hits,
    pick_excerpt,
    rule_judge,
    signal_hits,
    signal_score,
    strip_pii,
)

# 30자 경계 확인용. 아래 두 문장은 신호 구성이 같고 길이만 다르다.
SNIPPET_30 = "가계부 정리가 매번 번거롭고 영수증 입력이 오래 걸려요"
SNIPPET_29 = "가계부 정리가 매번 번거롭고 영수증 입력이 오래 걸려"


def make_item(
    snippet: str,
    *,
    id: str = "item-1",
    title: str = "",
    source_kind: SourceKind = SourceKind.BLOG,
    license: LicensePolicy = LicensePolicy.SUMMARY_ONLY,
    content_hash_: str = "",
) -> RawItem:
    """테스트용 RawItem. 판별에 안 쓰는 필드는 고정값으로 둔다."""
    return RawItem(
        id=id,
        title=title,
        snippet=snippet,
        url="https://example.com/1",
        source_name="테스트 매체",
        source_kind=source_kind,
        collected_at=datetime(2026, 9, 9, 12, 0, 0),
        query_keyword="가계부 번거롭",
        content_hash=content_hash_,
        collected_by=CollectMode.BATCH,
        license=license,
    )


# ══════════════════════════════════════════════
# clean_text (3-2)
# ══════════════════════════════════════════════


def test_clean_text_removes_search_api_highlight_tags():
    assert clean_text("가계부 <b>번거롭</b>다") == "가계부 번거롭다"


def test_clean_text_keeps_word_intact_when_tag_is_inside_a_word():
    # 네이버가 단어 중간에 하이라이트를 넣어도 신호 매칭이 깨지면 안 된다.
    assert clean_text("번거<b>롭</b>다") == "번거롭다"


def test_clean_text_turns_block_tags_into_space():
    assert clean_text("첫 줄<br>둘째 줄") == "첫 줄 둘째 줄"


def test_clean_text_unescapes_html_entities():
    assert clean_text("A&amp;B &lt;주의&gt; &quot;인용&quot; &#39;작은따옴표&#39;") == (
        "A&B <주의> \"인용\" '작은따옴표'"
    )


def test_clean_text_collapses_whitespace_and_trims():
    assert clean_text("  앞뒤\n\n공백\t\t정리   ") == "앞뒤 공백 정리"


def test_clean_text_truncates_at_max_len():
    assert clean_text("가" * 300) == "가" * 200
    assert clean_text("가" * 30, max_len=10) == "가" * 10


def test_clean_text_handles_empty():
    assert clean_text("") == ""


# ══════════════════════════════════════════════
# strip_pii (3-2 1번) — 배치·실시간 예외 없이 적용
# ══════════════════════════════════════════════


@pytest.mark.parametrize(
    "raw, leaked",
    [
        ("연락처는 010-1234-5678 입니다", "010-1234-5678"),  # 휴대전화
        ("연락처는 01012345678 입니다", "01012345678"),  # 하이픈 없는 휴대전화
        ("문의는 02-123-4567 로", "02-123-4567"),  # 지역번호
        ("메일 주세요 hong.gil@example.co.kr 로", "hong.gil@example.co.kr"),  # 이메일
        ("계좌 110-234-567890 으로 입금", "110-234-567890"),  # 계좌번호
        ("주민번호 900101-1234567 입력해야 함", "900101-1234567"),  # 주민등록번호
        ("@길동이 님이 알려줬어요", "@길동이"),  # 멘션 닉네임
        ("작성자 홍길동 이 남긴 글", "홍길동"),  # 작성자 패턴
        ("글쓴이: 김철수 가 정리함", "김철수"),  # 글쓴이 패턴
    ],
)
def test_strip_pii_removes_each_kind(raw, leaked):
    assert leaked not in strip_pii(raw)


def test_strip_pii_keeps_surrounding_words_separated():
    # 빈 문자열로 지우면 앞뒤 단어가 붙어버린다. 공백으로 지우고 마지막에 정규화한다.
    assert strip_pii("전화 010-1234-5678 번거롭") == "전화 번거롭"


def test_strip_pii_keeps_iso_dates():
    # 계좌 패턴이 느슨하면 "2026-09-09" 같은 날짜까지 지워진다.
    text = "2026-09-09 에 가계부 정리가 번거롭다"
    assert strip_pii(text) == text


def test_strip_pii_does_not_eat_ordinary_sentence():
    # 구분자 없이 이어지는 "작성자가"는 일반 문장이므로 지우지 않는다.
    text = "작성자가 아니라도 가계부 정리는 번거롭다"
    assert strip_pii(text) == text


def test_strip_pii_handles_empty():
    assert strip_pii("") == ""


# ══════════════════════════════════════════════
# content_hash (3-2 3번)
# ══════════════════════════════════════════════


def test_content_hash_is_invariant_to_tags_and_whitespace():
    a = content_hash("가계부  정리", "매번 <b>번거롭</b>다")
    b = content_hash("<b>가계부</b> 정리", "매번   번거롭다\n")
    assert a == b


def test_content_hash_is_invariant_to_html_entities():
    assert content_hash("A&amp;B", "정리가 번거롭다") == content_hash("A&B", "정리가 번거롭다")


def test_content_hash_differs_when_content_differs():
    assert content_hash("가계부 정리", "번거롭다") != content_hash("가계부 정리", "귀찮다")


def test_content_hash_separates_title_and_snippet():
    # 이어붙이기만 하면 ("ab","") 와 ("a","b") 가 같아진다. 구분자가 그걸 막는다.
    assert content_hash("가계부정리", "") != content_hash("가계부", "정리")


def test_content_hash_is_not_truncated_before_hashing():
    # 200자에서 잘라 해싱하면 뒤쪽만 다른 글이 같은 해시가 된다.
    head = "가" * 250
    assert content_hash("t", head + "앞") != content_hash("t", head + "뒤")


def test_content_hash_length_is_32():
    assert len(content_hash("가계부", "번거롭다")) == 32


# ══════════════════════════════════════════════
# signal_hits / has_need_signal / is_ad (5절)
# ══════════════════════════════════════════════


def test_signal_hits_returns_only_matched_types():
    hits = signal_hits("매번 손으로 옮기는 게 번거롭다")
    assert hits["반복 노동"] == ["매번", "손으로"]
    assert hits["직접 불만"] == ["번거롭"]
    assert "실패·포기" not in hits  # 안 걸린 유형은 키를 넣지 않는다


def test_signal_hits_empty_when_no_signal():
    assert signal_hits("오늘 날씨가 좋아서 산책을 다녀왔다") == {}
    assert signal_hits("") == {}


def test_has_need_signal_true_only_for_deficiency_expressions():
    assert has_need_signal("이런 기능이 있었으면 좋겠다") is True
    assert has_need_signal("연동이 안 되는 게 아쉽다") is True
    # 불편 신호이긴 하나 결핍 유형이 아니면 False
    assert has_need_signal("매번 손으로 옮겨서 번거롭다") is False
    assert has_need_signal("") is False


def test_payment_signal_hits_returns_matched_expressions():
    assert payment_signal_hits("구독료가 아까워서 결제했는데 후회한다") == ["결제했는데", "구독료"]
    assert payment_signal_hits("오늘 날씨가 좋다") == []
    assert payment_signal_hits("") == []


def test_has_payment_signal_true_only_for_payment_expressions():
    assert has_payment_signal("돈 내고 쓰는데도 이 모양이다") is True
    assert has_payment_signal("환불받으려 했는데 절차가 복잡하다") is True
    # 불편 신호이긴 하나 지불 유형이 아니면 False
    assert has_payment_signal("매번 손으로 옮겨서 번거롭다") is False
    assert has_payment_signal("") is False


def test_item_text_is_public_alias_of_item_text():
    """aggregate_tool 이 판별 때와 같은 정제 텍스트를 봐야 건수가 어긋나지 않는다."""
    item = make_item("가계부 정리가 매번 번거롭다", title="가계부")
    assert item_text(item) == clean_text(f"{item.title} {item.snippet}", 1_000_000)


# ══════════════════════════════════════════════
# 사전 회귀 — PAYMENT_SIGNALS 를 PAIN_SIGNALS 로 병합하는 실수를 막는다
# (dictionaries.py 의 "4곳이 깨진다" 경고 참고)
# ══════════════════════════════════════════════


def test_pain_signal_dictionary_covers_eight_groups_without_payment_merge():
    assert len(PAIN_SIGNALS) == 8
    assert {"정보 혼선", "접근 제약"}.issubset(PAIN_SIGNALS)
    assert len(PAIN_SIGNALS_TIER1) == 10
    assert set(PAIN_SIGNALS_TIER2) == {term for values in PAIN_SIGNALS.values() for term in values if term not in PAIN_SIGNALS_TIER1}
    assert "구독료" not in {term for values in PAIN_SIGNALS.values() for term in values}


def test_is_ad_detects_promotion_patterns():
    assert is_ad("체험단으로 제공받아 작성했습니다") is True
    assert is_ad("할인코드 입력하면 최저가") is True
    assert is_ad("가계부 정리가 매번 번거롭다") is False


# ══════════════════════════════════════════════
# signal_score — LLM 입력 상위 N건 랭킹용
# ══════════════════════════════════════════════


def test_signal_score_increases_with_more_signals():
    few = make_item("가계부 정리가 번거롭다는 이야기를 오늘도 들었습니다")
    many = make_item("가계부 정리가 매번 번거롭고 답답하고 하루 종일 시간 낭비라 포기했다")
    assert signal_score(many) > signal_score(few)


def test_signal_score_rewards_type_diversity_over_repetition():
    # 같은 유형 2개보다 서로 다른 유형 2개가 높아야 한다 (다양성 × 2).
    same_type = make_item("정리가 번거롭고 귀찮다는 후기를 오늘 여러 건 읽었습니다")
    two_types = make_item("정리가 번거롭고 매번 반복한다는 후기를 오늘 읽었습니다")
    assert signal_score(two_types) > signal_score(same_type)


def test_signal_score_adds_source_weight():
    snippet = "가계부 정리가 매번 번거롭고 영수증 입력이 오래 걸려요"
    blog = make_item(snippet, source_kind=SourceKind.BLOG)
    community = make_item(snippet, source_kind=SourceKind.COMMUNITY)
    public = make_item(snippet, source_kind=SourceKind.PUBLIC_DATA)
    assert signal_score(community) == signal_score(blog) + 2
    assert signal_score(public) == signal_score(blog) + 3


def test_signal_score_is_zero_without_signals():
    assert signal_score(make_item("오늘 날씨가 좋아서 산책을 다녀왔습니다", source_kind=SourceKind.NEWS)) == 0


# ══════════════════════════════════════════════
# extract_sentences — 완결 문장만
# ══════════════════════════════════════════════


def test_extract_sentences_returns_complete_sentences():
    assert extract_sentences("가계부 정리가 번거롭다. 매번 손으로 옮긴다.") == [
        "가계부 정리가 번거롭다.",
        "매번 손으로 옮긴다.",
    ]


def test_extract_sentences_drops_trailing_fragment():
    # 종결부호 없이 끝나는 꼬리는 문장이 아니다.
    assert extract_sentences("가계부 정리가 번거롭다. 매번 손으로") == ["가계부 정리가 번거롭다."]


def test_extract_sentences_drops_snippet_fragment():
    # 검색 API 스니펫의 전형. 앞뒤가 잘려 인용문이 못 된다.
    assert extract_sentences("...회의록 정리가 번거롭다는 이야기...") == []


def test_extract_sentences_keeps_complete_sentence_after_ellipsis():
    assert extract_sentences("...정리가 번거롭다는 글. 매번 손으로 옮긴다.") == ["매번 손으로 옮긴다."]


def test_extract_sentences_treats_unicode_ellipsis_as_cut():
    assert extract_sentences("…회의록 정리가 번거롭다는 이야기…") == []


def test_extract_sentences_accepts_question_and_exclamation():
    assert extract_sentences("다들 어떻게 하나요? 너무 답답합니다!") == [
        "다들 어떻게 하나요?",
        "너무 답답합니다!",
    ]


def test_extract_sentences_cleans_tags_first():
    assert extract_sentences("가계부 정리가 <b>번거롭</b>다.") == ["가계부 정리가 번거롭다."]


def test_extract_sentences_handles_empty():
    assert extract_sentences("") == []


# ══════════════════════════════════════════════
# pick_excerpt (3-2 4번) — 화면의 "유저 한마디"
# ══════════════════════════════════════════════


def test_pick_excerpt_returns_none_for_summary_only():
    item = make_item("가계부 정리가 번거롭다.", license=LicensePolicy.SUMMARY_ONLY)
    assert pick_excerpt(item) is None


def test_pick_excerpt_returns_signal_sentence_when_allowed():
    item = make_item("가계부 정리가 번거롭다.", license=LicensePolicy.EXCERPT_OK)
    assert pick_excerpt(item) == "가계부 정리가 번거롭다."


def test_pick_excerpt_returns_none_without_complete_sentence():
    item = make_item("...가계부 정리가 번거롭다는 글...", license=LicensePolicy.EXCERPT_OK)
    assert pick_excerpt(item) is None


def test_pick_excerpt_returns_none_when_sentence_exceeds_max_len():
    long_sentence = "회의록 정리를 매번 손으로 옮기는 게 너무 번거롭고 시간이 오래 걸려요."
    assert len(long_sentence) > 25
    item = make_item(long_sentence, license=LicensePolicy.EXCERPT_OK)
    assert pick_excerpt(item) is None


def test_pick_excerpt_skips_sentence_without_signal():
    item = make_item(
        "어제는 비가 왔습니다. 가계부 정리가 번거롭다.", license=LicensePolicy.EXCERPT_OK
    )
    assert pick_excerpt(item) == "가계부 정리가 번거롭다."


def test_pick_excerpt_respects_custom_max_len():
    item = make_item("가계부 정리가 번거롭다.", license=LicensePolicy.EXCERPT_OK)
    assert pick_excerpt(item, max_len=5) is None


# ══════════════════════════════════════════════
# rule_judge (3-3)
# ══════════════════════════════════════════════


def test_rule_judge_drops_duplicate_id():
    item = make_item(SNIPPET_30, id="dup")
    assert rule_judge(item, {"dup"}, set()) == (Verdict.DROP, "중복")


def test_rule_judge_drops_duplicate_hash():
    h = content_hash("", SNIPPET_30)
    item = make_item(SNIPPET_30, content_hash_=h)
    assert rule_judge(item, set(), {h}) == (Verdict.DROP, "중복")


def test_rule_judge_computes_hash_when_item_has_none():
    # content_hash 가 비어 있어도 중복은 잡혀야 한다. 빈 문자열끼리 비교하면 안 된다.
    item = make_item(SNIPPET_30, content_hash_="")
    h = content_hash("", SNIPPET_30)
    assert rule_judge(item, set(), {h}) == (Verdict.DROP, "중복")


def test_rule_judge_does_not_treat_empty_hash_as_duplicate():
    item = make_item(SNIPPET_30, content_hash_="")
    verdict, _ = rule_judge(item, set(), {""})
    assert verdict is Verdict.PASS


def test_rule_judge_drops_below_30_chars():
    assert len(SNIPPET_29) == 29
    item = make_item(SNIPPET_29)
    assert rule_judge(item, set(), set()) == (Verdict.DROP, "30자 미만")


def test_rule_judge_passes_at_exactly_30_chars():
    assert len(SNIPPET_30) == 30
    verdict, reason = rule_judge(make_item(SNIPPET_30), set(), set())
    assert verdict is Verdict.PASS
    assert "번거롭" in reason


def test_rule_judge_measures_length_after_cleaning():
    # 태그·공백은 길이에 포함하지 않는다.
    padded = "<b>" + SNIPPET_29 + "</b>   \n  "
    assert rule_judge(make_item(padded), set(), set()) == (Verdict.DROP, "30자 미만")


def test_rule_judge_drops_ads():
    item = make_item("체험단으로 제공받아 작성한 후기인데 정리가 매번 번거롭고 오래 걸려요")
    assert rule_judge(item, set(), set()) == (Verdict.DROP, "광고·홍보 패턴")


def test_rule_judge_drops_when_no_signal():
    item = make_item("오늘 날씨가 좋아서 한강 공원까지 산책을 다녀왔고 사진도 여러 장 찍었습니다")
    assert rule_judge(item, set(), set()) == (Verdict.DROP, "불편 신호 없음")


def test_rule_judge_holds_when_target_is_vague():
    # 3-3 보류 조건: 신호는 있으나 무엇에 대한 것인지 없음
    item = make_item("그냥 다 짜증난다 진짜 너무 답답하고 스트레스 받는다 정말")
    assert rule_judge(item, set(), set()) == (Verdict.HOLD, "대상 불분명")


def test_rule_judge_passes_when_target_is_clear():
    item = make_item("회의록 정리를 매번 손으로 옮기는 게 너무 번거롭고 시간이 오래 걸려요")
    verdict, reason = rule_judge(item, set(), set())
    assert verdict is Verdict.PASS
    assert "반복 노동" in reason


def test_rule_judge_uses_title_and_snippet_together():
    # 광고 표시가 제목에만 있어도 걸러야 한다.
    item = make_item(SNIPPET_30, title="[협찬] 가계부 앱 후기")
    assert rule_judge(item, set(), set()) == (Verdict.DROP, "광고·홍보 패턴")


def test_rule_judge_is_pure():
    # 호출해도 호출자의 집합을 건드리지 않는다. 판정은 재현 가능해야 한다.
    seen_ids: set[str] = set()
    seen_hashes: set[str] = set()
    item = make_item(SNIPPET_30)
    rule_judge(item, seen_ids, seen_hashes)
    assert seen_ids == set() and seen_hashes == set()
    assert rule_judge(item, seen_ids, seen_hashes) == rule_judge(item, seen_ids, seen_hashes)


def test_verdict_values():
    assert (Verdict.PASS.value, Verdict.HOLD.value, Verdict.DROP.value) == (
        "pass",
        "hold",
        "drop",
    )
