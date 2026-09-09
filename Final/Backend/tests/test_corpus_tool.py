"""
corpus_tool 테스트 — JSONL 임시 저장소.

여기서 지키는 것
  · append-only. 두 번 저장하면 줄이 쌓인다(덮어쓰지 않는다)
  · save_raw_items 가 seen 인덱스를 같이 갱신한다 — 다음 배치의 중복 판정 근거
  · CORPUS_KEEP_SNIPPET=false 면 발췌를 안 남긴다
  · 파일이 없어도 예외 대신 빈 결과
  · reset() 이 CORPUS_DIR 밖으로 못 나간다
"""

from __future__ import annotations

from datetime import date, datetime

import pytest

from app.config.settings import settings
from app.schemas.models import Category, ProblemCandidate
from app.tools import corpus_tool as ct


# ══════════════════════════════════════════════
# 주차 · 카테고리 키
# ══════════════════════════════════════════════


def test_week_key_is_iso_week():
    assert ct.week_key(date(2026, 9, 9)) == "2026-W37"
    # 연말 경계: 2027-01-01(금)은 ISO 로 2026-W53 이다
    assert ct.week_key(date(2027, 1, 1)) == "2026-W53"
    # 한 자리 주차는 0을 채워 사전순 = 시간순이 되게 한다
    assert ct.week_key(date(2026, 1, 8)) == "2026-W02"


def test_week_key_defaults_to_today():
    assert ct.week_key() == ct.week_key(date.today())


def test_category_slug_replaces_slash():
    assert ct.category_slug(Category.IT_PRODUCTIVITY) == "IT_생산성"
    assert ct.category_slug(Category.FINANCE) == "금융"
    # 되짚기가 된다 — 파일명에서 카테고리를 복원할 수 있어야 한다
    for c in Category:
        assert ct.category_of_slug(ct.category_slug(c)) is c


def test_recent_weeks_is_newest_first():
    weeks = ct.recent_weeks(3, end=date(2026, 9, 9))
    assert weeks == ["2026-W37", "2026-W36", "2026-W35"]


# ══════════════════════════════════════════════
# save_raw_items
# ══════════════════════════════════════════════


def test_save_raw_items_writes_jsonl_under_week_and_category(corpus_dir, make_raw_item):
    item = make_raw_item(query_keyword="가계부 번거롭", collected_at=datetime(2026, 9, 9, 3))
    ct.save_raw_items([item])

    path = corpus_dir / "raw" / "2026-W37" / "금융.jsonl"
    assert path.exists()
    assert len(path.read_text(encoding="utf-8").strip().splitlines()) == 1


def test_save_raw_items_round_trips(make_raw_item):
    item = make_raw_item(title="병원 예약이 매번 번거롭다", query_keyword="병원 예약 번거롭")
    ct.save_raw_items([item])

    loaded = ct.load_raw_items()
    assert len(loaded) == 1
    assert loaded[0] == item  # 필드 하나도 잃지 않는다


def test_save_raw_items_is_append_only(make_raw_item):
    ct.save_raw_items([make_raw_item(id="a")])
    ct.save_raw_items([make_raw_item(id="b")])

    ids = {i.id for i in ct.load_raw_items()}
    assert ids == {"a", "b"}  # 두 번째 저장이 첫 번째를 덮지 않는다


def test_save_raw_items_splits_by_category(make_raw_item):
    ct.save_raw_items(
        [
            make_raw_item(id="f1", query_keyword="가계부 번거롭"),
            make_raw_item(id="h1", query_keyword="병원 예약 오래 걸려"),
            make_raw_item(id="i1", query_keyword="회의록 일일이"),
        ]
    )

    assert [i.id for i in ct.load_raw_items(category=Category.FINANCE)] == ["f1"]
    assert [i.id for i in ct.load_raw_items(category=Category.HEALTHCARE)] == ["h1"]
    assert [i.id for i in ct.load_raw_items(category=Category.IT_PRODUCTIVITY)] == ["i1"]


def test_save_raw_items_splits_by_week(make_raw_item):
    ct.save_raw_items([make_raw_item(id="w37", collected_at=datetime(2026, 9, 9, 3))])
    ct.save_raw_items([make_raw_item(id="w38", collected_at=datetime(2026, 9, 16, 3))])

    assert [i.id for i in ct.load_raw_items(week="2026-W37")] == ["w37"]
    assert [i.id for i in ct.load_raw_items(week="2026-W38")] == ["w38"]
    assert len(ct.load_raw_items()) == 2  # 주차를 안 주면 전부


def test_explicit_category_wins_over_inference(make_raw_item):
    """수집기가 카테고리를 알고 있으면 그걸 쓴다."""
    item = make_raw_item(query_keyword="가계부 번거롭")
    ct.save_raw_items([item], category=Category.LIFESTYLE)

    assert ct.load_raw_items(category=Category.LIFESTYLE) == [item]
    assert ct.load_raw_items(category=Category.FINANCE) == []


def test_uncategorized_item_is_kept_not_dropped(corpus_dir, make_raw_item):
    """★ RawItem 은 절대 버리지 않는다. 카테고리를 몰라도 남긴다."""
    item = make_raw_item(id="x", title="그냥 잡담", query_keyword="아무 말")
    ct.save_raw_items([item])

    path = corpus_dir / "raw" / ct.week_key(date(2026, 9, 9)) / "_미분류.jsonl"
    assert path.exists()
    assert [i.id for i in ct.load_raw_items()] == ["x"]


def test_save_raw_items_empty_list_is_noop(corpus_dir):
    ct.save_raw_items([])
    assert ct.load_raw_items() == []


# ══════════════════════════════════════════════
# seen 인덱스 — 다음 배치의 중복 판정 근거
# ══════════════════════════════════════════════


def test_save_raw_items_updates_seen_index(make_raw_item):
    ct.save_raw_items(
        [
            make_raw_item(id="a", content_hash="h-a"),
            make_raw_item(id="b", content_hash="h-b"),
        ]
    )

    ids, hashes = ct.load_seen()
    assert ids == {"a", "b"}
    assert hashes == {"h-a", "h-b"}


def test_seen_index_accumulates_across_batches(make_raw_item):
    ct.save_raw_items([make_raw_item(id="a", content_hash="h-a")])
    ct.save_raw_items([make_raw_item(id="b", content_hash="h-b")])

    ids, hashes = ct.load_seen()
    assert ids == {"a", "b"}
    assert hashes == {"h-a", "h-b"}


def test_seen_index_does_not_duplicate_lines(corpus_dir, make_raw_item):
    """같은 id를 두 번 저장해도 인덱스 줄은 안 늘어난다."""
    ct.save_raw_items([make_raw_item(id="a", content_hash="h-a")])
    ct.save_raw_items([make_raw_item(id="a", content_hash="h-a")])

    lines = (corpus_dir / "index" / "seen_ids.txt").read_text("utf-8").split()
    assert lines == ["a"]


def test_load_seen_on_empty_corpus():
    assert ct.load_seen() == (set(), set())


def test_empty_content_hash_is_not_indexed(make_raw_item):
    """해시가 비어 있으면 중복 판정에 못 쓴다. 인덱스에 넣지 않는다."""
    item = make_raw_item(id="a")
    item.content_hash = ""
    ct.save_raw_items([item])

    ids, hashes = ct.load_seen()
    assert ids == {"a"}
    assert hashes == set()


# ══════════════════════════════════════════════
# CORPUS_KEEP_SNIPPET — 보수적 운영 스위치
# ══════════════════════════════════════════════


def test_snippet_kept_by_default(make_raw_item):
    ct.save_raw_items([make_raw_item(snippet="원문 발췌입니다")])
    assert ct.load_raw_items()[0].snippet == "원문 발췌입니다"


def test_snippet_dropped_when_switch_is_off(monkeypatch, make_raw_item):
    monkeypatch.setattr(settings, "CORPUS_KEEP_SNIPPET", False)
    ct.save_raw_items([make_raw_item(id="a", snippet="원문 발췌입니다")])

    loaded = ct.load_raw_items()[0]
    assert loaded.snippet == ""
    assert loaded.id == "a"  # 나머지 메타는 그대로 남는다
    assert loaded.url  # 역추적 링크는 살아 있어야 한다


# ══════════════════════════════════════════════
# 판정 · 보류 · 이월
# ══════════════════════════════════════════════


def test_save_and_load_judgements(corpus_dir, make_judgement):
    js = [make_judgement(raw_item_id="a"), make_judgement(raw_item_id="b", is_pain=False)]
    ct.save_judgements(js, Category.FINANCE, week="2026-W37")

    assert (corpus_dir / "judgements" / "2026-W37" / "금융.jsonl").exists()
    assert ct.load_judgements(week="2026-W37", category=Category.FINANCE) == js


def test_judgements_append_only(make_judgement):
    ct.save_judgements([make_judgement(raw_item_id="a")], Category.FINANCE, week="2026-W37")
    ct.save_judgements([make_judgement(raw_item_id="b")], Category.FINANCE, week="2026-W37")

    assert len(ct.load_judgements(week="2026-W37")) == 2


def test_load_pending_judgements_spans_recent_weeks(make_judgement):
    """묶기는 한 주만 봐서는 5건을 못 채운다. 지난 주차까지 같이 본다."""
    this_week = ct.week_key()
    last_week = ct.recent_weeks(2)[1]
    old_week = ct.recent_weeks(10)[9]

    ct.save_judgements([make_judgement(raw_item_id="now")], Category.FINANCE, week=this_week)
    ct.save_judgements([make_judgement(raw_item_id="prev")], Category.FINANCE, week=last_week)
    ct.save_judgements([make_judgement(raw_item_id="old")], Category.FINANCE, week=old_week)

    ids = {j.raw_item_id for j in ct.load_pending_judgements(weeks=4)}
    assert ids == {"now", "prev"}  # 10주 전 것은 안 딸려 온다


def test_load_pending_judgements_on_empty_corpus():
    assert ct.load_pending_judgements() == []


def test_save_and_load_held(corpus_dir, make_raw_item):
    items = [make_raw_item(id="h1")]
    ct.save_held(items, Category.HEALTHCARE, week="2026-W37")

    assert (corpus_dir / "held" / "2026-W37" / "헬스케어.jsonl").exists()
    assert ct.load_held(week="2026-W37") == items


def test_save_and_load_overflow(corpus_dir, make_raw_item):
    items = [make_raw_item(id="o1"), make_raw_item(id="o2")]
    ct.save_overflow(items, Category.IT_PRODUCTIVITY, week="2026-W37")

    assert (corpus_dir / "overflow" / "2026-W37" / "IT_생산성.jsonl").exists()
    assert [i.id for i in ct.load_overflow()] == ["o1", "o2"]


def test_held_and_overflow_are_separate_from_raw(make_raw_item):
    """보류·이월은 raw 를 오염시키지 않는다."""
    ct.save_held([make_raw_item(id="h")], Category.FINANCE, week="2026-W37")
    ct.save_overflow([make_raw_item(id="o")], Category.FINANCE, week="2026-W37")

    assert ct.load_raw_items() == []


# ══════════════════════════════════════════════
# 승격 대기 묶음
# ══════════════════════════════════════════════


def _candidate(cid: str, n_items: int = 3) -> ProblemCandidate:
    return ProblemCandidate(
        id=cid,
        raw_item_ids=[f"{cid}-{i}" for i in range(n_items)],
        pain_summaries=["가계부를 손으로 옮겨 적어야 한다"] * n_items,
        theme_hint="가계부 수기 입력",
        category=Category.FINANCE,
    )


def test_save_and_load_pending_candidates(corpus_dir):
    groups = [_candidate("c1"), _candidate("c2")]
    ct.save_pending_candidates(groups)

    assert (corpus_dir / "pending" / "candidates.jsonl").exists()
    assert ct.load_pending_candidates() == groups


def test_pending_candidates_append_only():
    ct.save_pending_candidates([_candidate("c1")])
    ct.save_pending_candidates([_candidate("c2")])

    assert [g.id for g in ct.load_pending_candidates()] == ["c1", "c2"]


def test_load_pending_candidates_on_empty_corpus():
    assert ct.load_pending_candidates() == []


# ══════════════════════════════════════════════
# 매니페스트
# ══════════════════════════════════════════════


def test_write_and_read_manifest(corpus_dir):
    ct.write_manifest({"week": "2026-W37", "collected": 1234, "카테고리": "금융"})

    assert (corpus_dir / "manifests" / "2026-W37.json").exists()
    m = ct.read_manifest("2026-W37")
    assert m["collected"] == 1234
    assert m["카테고리"] == "금융"  # ensure_ascii 문제 없이 한글이 살아 있다
    assert m["written_at"]


def test_manifest_defaults_to_current_week():
    ct.write_manifest({"collected": 1})
    assert ct.read_manifest()["week"] == ct.week_key()


def test_read_manifest_returns_newest_when_week_omitted():
    ct.write_manifest({"week": "2026-W36", "collected": 1})
    ct.write_manifest({"week": "2026-W37", "collected": 2})

    assert ct.read_manifest()["collected"] == 2
    assert ct.list_manifest_weeks() == ["2026-W36", "2026-W37"]


def test_read_manifest_missing_returns_none():
    assert ct.read_manifest() is None
    assert ct.read_manifest("1999-W01") is None


def test_manifest_file_is_utf8_not_escaped(corpus_dir):
    ct.write_manifest({"week": "2026-W37", "note": "헬스케어"})
    text = (corpus_dir / "manifests" / "2026-W37.json").read_text("utf-8")
    assert "헬스케어" in text


# ══════════════════════════════════════════════
# 없는 파일 · reset
# ══════════════════════════════════════════════


def test_loads_on_empty_corpus_do_not_raise():
    assert ct.load_raw_items() == []
    assert ct.load_judgements() == []
    assert ct.load_held() == []
    assert ct.load_overflow() == []
    assert ct.list_manifest_weeks() == []


def test_broken_line_is_skipped_not_fatal(corpus_dir, make_raw_item):
    ct.save_raw_items([make_raw_item(id="ok")])
    path = next((corpus_dir / "raw").rglob("*.jsonl"))
    with path.open("a", encoding="utf-8") as f:
        f.write("{깨진 줄}\n")

    assert [i.id for i in ct.load_raw_items()] == ["ok"]


def test_reset_clears_corpus_only(corpus_dir, make_raw_item):
    outside = corpus_dir.parent / "건드리면_안_되는_파일.txt"
    outside.write_text("남아 있어야 한다", encoding="utf-8")

    ct.save_raw_items([make_raw_item()])
    ct.write_manifest({"collected": 1})
    assert ct.load_raw_items()

    ct.reset()

    assert ct.load_raw_items() == []
    assert ct.load_seen() == (set(), set())
    assert corpus_dir.exists()  # 루트 자체는 남긴다
    assert outside.exists()  # ★ 밖은 안 건드린다


def test_reset_on_missing_dir_is_noop(corpus_dir):
    assert not corpus_dir.exists()
    ct.reset()  # 예외 없이 통과


def test_reset_refuses_shallow_root(monkeypatch, tmp_path):
    """/ 나 /data 같은 얕은 경로를 통째로 지우는 사고를 막는다."""
    from pathlib import Path

    monkeypatch.setattr(settings, "CORPUS_DIR", Path("/"))
    with pytest.raises(RuntimeError):
        ct.reset()


def test_reset_does_not_follow_symlink_out(corpus_dir, tmp_path):
    """심링크는 링크만 끊고, 가리키던 실제 파일은 남긴다."""
    target_dir = tmp_path / "밖"
    target_dir.mkdir()
    keep = target_dir / "소중한.txt"
    keep.write_text("남아 있어야 한다", encoding="utf-8")

    corpus_dir.mkdir(parents=True, exist_ok=True)
    (corpus_dir / "링크").symlink_to(target_dir)

    ct.reset()

    assert keep.exists()
    assert not (corpus_dir / "링크").exists()


# ══════════════════════════════════════════════
# db_tool 과의 계약
# ══════════════════════════════════════════════


def test_save_raw_items_matches_db_tool_signature():
    """
    ★ 나중에 DB가 붙으면 import 한 줄만 바꿔서 갈아끼울 수 있어야 한다.
      추가 인자는 전부 키워드 전용이라 db_tool 호출 방식과 어긋나지 않는다.
    """
    import inspect

    from app.tools import db_tool

    ours = inspect.signature(ct.save_raw_items, eval_str=True)
    theirs = inspect.signature(db_tool.save_raw_items, eval_str=True)

    positional = [
        p
        for p in ours.parameters.values()
        if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
    ]
    assert [p.name for p in positional] == list(theirs.parameters)
    assert positional[0].annotation == theirs.parameters["items"].annotation
    assert all(
        p.default is not inspect.Parameter.empty
        for p in ours.parameters.values()
        if p.kind == p.KEYWORD_ONLY
    )


# ══════════════════════════════════════════════
# 격리 — conftest 가 진짜 data/ 를 막고 있는가
# ══════════════════════════════════════════════


def test_corpus_dir_is_isolated_to_tmp(corpus_dir, tmp_path):
    assert corpus_dir.is_relative_to(tmp_path)
    assert "data/corpus" not in str(corpus_dir)


def test_llm_dry_run_is_forced():
    assert settings.LLM_DRY_RUN is True
