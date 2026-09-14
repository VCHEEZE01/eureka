"""
② 해석기 테스트.

★ 판별은 3층이다. 각 층이 "버리지 않는다"를 지키는지가 핵심이다.
    3-A 규칙 선필터 — HOLD 는 held 로, DROP 만 버린다
    3-B 랭킹 + 상한 — 상한 초과분은 overflow 로 쌓는다 (다음 주에 다시 본다)
    3-C LLM 판별   — 실패해도 예외가 올라오지 않는다 (llm_tool 쪽 계약)

★ 그리고 묶음 단계의 계약 셋.
    · 5건 미만 묶음은 pending 으로 — 다음 주 자동 승격 경로
    · 한 출처가 묶음의 절반을 넘지 못한다 (docs 9절)
    · 후보 id 는 구성원 id 로만 정해진다 — 같은 구성이면 주차가 달라도 같은 id

★ LLM 도 네트워크도 부르지 않는다. use_llm=False 이거나 judge_pains 를 대역으로 바꾼다.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from app.agents.interpreter_agent import InterpretInput, InterpreterAgent
from app.config.settings import settings
from app.schemas.models import (
    Category,
    Judgement,
    ProblemCandidate,
    ProgressEvent,
    RawItem,
    SourceKind,
)
from app.tools import corpus_tool, llm_tool
from app.tools import text_tool
from tests.conftest import find_aggregate_numbers

CATEGORY = Category.IT_PRODUCTIVITY


# ══════════════════════════════════════════════
# 도우미 — 실제 수집물처럼 생긴 원문들
# ══════════════════════════════════════════════


def raw(
    n: int,
    title: str,
    snippet: str,
    source_name: str = "네이버 블로그",
    kind: SourceKind = SourceKind.BLOG,
) -> RawItem:
    return RawItem(
        id=f"raw-{n:03d}",
        title=title,
        snippet=snippet,
        url=f"https://example.test/post/{n}",
        source_name=source_name,
        source_kind=kind,
        collected_at=datetime(2026, 9, 9, 3, 0, 0),
        query_keyword="회의록 번거롭",
        content_hash=f"hash-{n:03d}",
    )


#: 같은 불편을 말하는 글들. 규칙 선필터를 통과하고 서로 묶인다.
회의록_제목 = [
    "회의록을 매번 손으로 정리하는 게 번거롭다",
    "회의록을 매번 손으로 정리하기가 번거롭다",
    "회의록을 매번 손으로 정리하는 게 번거로웠다",
    "회의록을 매번 손으로 정리하는 일이 번거롭다",
    "회의록을 매번 손으로 정리하느라 번거롭다",
    "회의록을 매번 손으로 정리하는 것이 번거롭다",
]

회의록_본문 = (
    "회의가 끝날 때마다 녹음을 다시 들으면서 회의록을 손으로 옮겨 적습니다. "
    "매번 반복이라 시간이 너무 오래 걸리고 번거롭습니다."
)

#: 출처 셋을 돌려 쓴다 — 한 출처가 묶음의 절반을 넘지 않게.
출처들 = ["네이버 블로그", "티스토리", "브런치"]


def 회의록_묶음(count: int = 6, source_name: str | None = None) -> list[RawItem]:
    return [
        raw(
            i + 1,
            회의록_제목[i % len(회의록_제목)],
            f"{회의록_본문} ({i + 1})",
            source_name=source_name or 출처들[i % len(출처들)],
        )
        for i in range(count)
    ]


def 광고글(n: int) -> RawItem:
    return raw(
        n,
        "회의록 자동화 솔루션 할인 이벤트",
        "체험단 원고료를 제공받아 작성했습니다. 회의록 정리가 번거로우신 분들께 추천드립니다.",
    )


def 짧은글(n: int) -> RawItem:
    return raw(n, "회의록 번거로움", "회의록 번거롭")


def 대상불분명글(n: int) -> RawItem:
    return raw(n, "그냥 다 짜증난다", "요즘 그냥 다 짜증나고 답답하다. 진짜 너무 짜증난다. 다 귀찮다 그냥.")


def 잡담글(n: int) -> RawItem:
    return raw(
        n,
        "어제 다녀온 파스타집 후기",
        "분위기도 좋고 직원분들도 친절했습니다. 면도 알맞게 삶아져서 정말 맛있었어요. 추천합니다.",
    )


def run(items: list[RawItem], **kw) -> list[ProblemCandidate]:
    """규칙만으로 한 바퀴. 기본은 LLM 없이 돈다."""
    kw.setdefault("use_llm", False)
    return InterpreterAgent().run(InterpretInput(items=items, category=CATEGORY, **kw))


@pytest.fixture(autouse=True)
def _no_real_llm(monkeypatch):
    """
    use_llm=True 를 안 켠 테스트가 실수로 모델을 부르면 그 자리에서 실패한다.

    ★ llm_tool 은 `from app.core.llm import get_llm` 으로 이름을 묶어 뒀다.
      원본 모듈을 갈아끼워도 안 걸린다 — llm_tool 쪽 이름을 바꿔야 한다.
    """

    def boom(*_a, **_kw):
        raise AssertionError("LLM 을 부르면 안 되는 경로가 모델을 불렀다")

    monkeypatch.setattr(llm_tool, "get_llm", boom)


# ══════════════════════════════════════════════
# 계약 — 이름·단계·진행 상태
# ══════════════════════════════════════════════


def test_에이전트_이름과_단계():
    assert InterpreterAgent.name == "해석기"
    assert InterpreterAgent.steps == ["불편 판별", "묶기", "묶음 정리"]


def test_진행_상태를_0_0완료_1_1완료_2_2완료_순으로_알린다():
    events: list[ProgressEvent] = []
    agent = InterpreterAgent(on_progress=events.append)

    agent.run(InterpretInput(items=회의록_묶음(), category=CATEGORY, use_llm=False))

    assert [(e.index, e.done) for e in events] == [
        (0, False),
        (0, True),
        (1, False),
        (1, True),
        (2, False),
        (2, True),
    ]
    assert [e.step for e in events[::2]] == InterpreterAgent.steps
    assert all(e.total == 3 for e in events)


def test_진행_콜백이_없어도_돈다():
    assert run(회의록_묶음()) is not None


def test_빈_입력이면_후보가_없다():
    assert run([]) == []


# ══════════════════════════════════════════════
# 3-A 규칙 선필터 — HOLD 는 버리지 않는다
# ══════════════════════════════════════════════


def test_보류는_held_로_저장한다():
    run(회의록_묶음() + [대상불분명글(90)])

    held = corpus_tool.load_held(category=CATEGORY)

    assert [i.id for i in held] == ["raw-090"]


def test_탈락은_저장하지_않고_사유만_남긴다():
    run(회의록_묶음() + [광고글(91), 짧은글(92), 잡담글(93)])

    assert corpus_tool.load_held(category=CATEGORY) == []

    stats = 매니페스트()
    assert stats["규칙_탈락"] == 3
    assert sum(stats["탈락_사유"].values()) == 3
    assert "광고·홍보 패턴" in stats["탈락_사유"]
    assert "30자 미만" in stats["탈락_사유"]


def test_같은_입력_안의_중복은_탈락시킨다():
    items = 회의록_묶음()
    쌍둥이 = items[0].model_copy(update={"id": "raw-999"})  # 같은 content_hash
    run(items + [쌍둥이])

    assert 매니페스트()["탈락_사유"].get("중복") == 1


def test_이미_저장된_원문을_중복으로_보지_않는다():
    """① 이 방금 저장해 둔 것을 보고 전건을 중복 처리하면 안 된다."""
    items = 회의록_묶음()
    corpus_tool.save_raw_items(items, category=CATEGORY)

    run(items)

    assert 매니페스트()["규칙_통과"] == len(items)


# ══════════════════════════════════════════════
# 3-B 랭킹 + 상한 — 초과분은 이월한다
# ══════════════════════════════════════════════


def test_상한을_넘는_건은_overflow_로_쌓는다():
    items = 회의록_묶음()

    run(items, max_llm_items=2)

    overflow = corpus_tool.load_overflow(category=CATEGORY)
    assert len(overflow) == len(items) - 2
    assert 매니페스트()["LLM_이월"] == len(items) - 2


def test_이월된_건은_판정되지_않는다():
    run(회의록_묶음(), max_llm_items=2)

    assert len(corpus_tool.load_judgements(category=CATEGORY)) == 2


def test_상한이_0이면_전건_이월():
    items = 회의록_묶음()

    assert run(items, max_llm_items=0) == []
    assert len(corpus_tool.load_overflow(category=CATEGORY)) == len(items)


def test_신호가_센_것부터_LLM_에_넣는다():
    """signal_score 내림차순. 같은 점수면 id 순이라 결과가 흔들리지 않는다."""
    약한글 = raw(
        50,
        "회의록 정리를 손으로 한다",
        "회의가 끝나면 회의록을 손으로 옮겨 적고 있습니다. 그냥 그렇게 하고 있어요 계속.",
    )
    센글 = raw(
        51,
        "회의록 정리가 번거롭고 답답하다",
        "매번 손으로 옮겨 적는 게 번거롭고 답답한데 자동으로 해 주는 게 없어서 아쉽습니다.",
        source_name="네이버 카페",
        kind=SourceKind.COMMUNITY,
    )
    assert text_tool.signal_score(센글) > text_tool.signal_score(약한글)

    run([약한글, 센글], max_llm_items=1)

    assert [j.raw_item_id for j in corpus_tool.load_judgements(category=CATEGORY)] == [
        "raw-051"
    ]


def test_상한을_안_주면_settings_를_호출_시점에_읽는다(monkeypatch):
    monkeypatch.setattr(settings, "MAX_LLM_ITEMS", 1)

    run(회의록_묶음())

    assert 매니페스트()["LLM_투입"] == 1


# ══════════════════════════════════════════════
# 3-C 판별 — LLM 경로와 규칙 경로
# ══════════════════════════════════════════════


def test_use_llm_False_면_LLM_없이_판정을_만든다():
    """_no_real_llm 이 걸려 있으므로, 모델을 불렀다면 여기서 터진다."""
    candidates = run(회의록_묶음())

    judgements = corpus_tool.load_judgements(category=CATEGORY)
    assert len(judgements) == 6
    assert all(j.confidence == "중간" for j in judgements)
    assert 매니페스트()["LLM_호출"] == 0
    assert candidates


def test_use_llm_True_면_judge_pains_로_넘긴다(monkeypatch):
    본 = {}

    def fake_judge(items: list[RawItem]) -> list[Judgement]:
        본["items"] = items
        return [
            Judgement(
                raw_item_id=i.id,
                is_pain=True,
                pain_summary=text_tool.clean_text(i.title, 80),
                confidence="높음",
                severity="중간",
            )
            for i in items
        ]

    monkeypatch.setattr(llm_tool, "judge_pains", fake_judge)
    monkeypatch.setattr(settings, "JUDGE_BATCH_SIZE", 4)

    candidates = run(회의록_묶음(), use_llm=True)

    assert [i.id for i in 본["items"]] == [f"raw-{i:03d}" for i in range(1, 7)]
    assert 매니페스트()["LLM_호출"] == 2  # 6건 / 배치 4
    assert candidates


def test_판정된_건은_전부_corpus_에_남는다(monkeypatch):
    def fake_judge(items):
        return [
            Judgement(raw_item_id=i.id, is_pain=False, confidence="낮음") for i in items
        ]

    monkeypatch.setattr(llm_tool, "judge_pains", fake_judge)

    assert run(회의록_묶음(), use_llm=True) == []
    assert len(corpus_tool.load_judgements(category=CATEGORY)) == 6


# ══════════════════════════════════════════════
# 묶기 — 확신 없는 판정은 넘기지 않는다
# ══════════════════════════════════════════════


def test_확신도_낮음은_묶기로_넘어가지_않는다(monkeypatch):
    def fake_judge(items):
        return [
            Judgement(
                raw_item_id=i.id,
                is_pain=True,
                pain_summary=text_tool.clean_text(i.title, 80),
                confidence="낮음" if i.id == "raw-001" else "높음",
            )
            for i in items
        ]

    monkeypatch.setattr(llm_tool, "judge_pains", fake_judge)

    run(회의록_묶음(), use_llm=True)

    assert 매니페스트()["묶기_대상"] == 5


def test_불편이_아니면_묶기로_넘어가지_않는다(monkeypatch):
    def fake_judge(items):
        return [
            Judgement(raw_item_id=i.id, is_pain=False, confidence="높음") for i in items
        ]

    monkeypatch.setattr(llm_tool, "judge_pains", fake_judge)

    run(회의록_묶음(), use_llm=True)

    assert 매니페스트()["묶기_대상"] == 0


# ══════════════════════════════════════════════
# 묶음 정리 — 5건 미만은 승격 대기
# ══════════════════════════════════════════════


def test_다섯건_미만_묶음은_후보가_아니라_승격_대기다():
    candidates = run(회의록_묶음(count=3))

    assert candidates == []
    waiting = corpus_tool.load_pending_candidates()
    assert len(waiting) == 1
    assert len(waiting[0].raw_item_ids) == 3
    assert 매니페스트()["승격대기"] == 1


def test_다섯건_이상이면_후보가_된다():
    candidates = run(회의록_묶음(count=6))

    assert len(candidates) == 1
    assert len(candidates[0].raw_item_ids) == 6
    assert corpus_tool.load_pending_candidates() == []


def test_MIN_GROUP_SIZE_를_호출_시점에_읽는다(monkeypatch):
    monkeypatch.setattr(settings, "MIN_GROUP_SIZE", 3)

    assert len(run(회의록_묶음(count=3))) == 1


def test_후보는_큰_묶음부터_나온다():
    가계부 = [
        raw(
            20 + i,
            f"가계부에 카드 내역을 손으로 입력하는 게 귀찮다 {i}",
            "카드 명세서를 보면서 가계부에 한 줄씩 손으로 옮겨 적는 게 매번 너무 귀찮습니다.",
            source_name=출처들[i % 3],
        )
        for i in range(5)
    ]
    candidates = run(회의록_묶음(count=6) + 가계부)

    sizes = [len(c.raw_item_ids) for c in candidates]
    assert sizes == sorted(sizes, reverse=True)
    assert sizes == [6, 5]


# ══════════════════════════════════════════════
# 출처 편중 상한 (docs 9절)
# ══════════════════════════════════════════════


def test_한_출처가_묶음의_절반을_넘지_못한다():
    """한 카페에서만 나온 이야기는 아직 세상의 문제가 아니다."""
    items = 회의록_묶음(count=6, source_name="네이버 카페")

    assert run(items) == []

    waiting = corpus_tool.load_pending_candidates()
    assert waiting and len(waiting[0].raw_item_ids) < 6
    assert 매니페스트()["출처편중_잘라냄"] > 0


def test_출처가_고르면_잘라내지_않는다():
    run(회의록_묶음(count=6))

    assert 매니페스트()["출처편중_잘라냄"] == 0


def test_cap_source_bias_는_절반을_넘는_출처만_깎는다():
    agent = InterpreterAgent()
    items = 회의록_묶음(count=5, source_name="네이버 카페")
    items[4] = items[4].model_copy(update={"source_name": "티스토리"})
    raw_map = {i.id: i for i in items}
    group = [
        Judgement(raw_item_id=i.id, is_pain=True, pain_summary="회의록 정리", confidence="높음")
        for i in items
    ]

    kept = agent._cap_source_bias(group, raw_map)
    sources = [raw_map[j.raw_item_id].source_name for j in kept]

    assert sources.count("네이버 카페") <= max(len(kept) // 2, 1)
    assert len(kept) < len(group)


def test_원문을_못_찾으면_저_혼자인_출처로_본다():
    """지난 주차 판정처럼 원문이 손에 없을 때 편중으로 오해하면 안 된다."""
    agent = InterpreterAgent()
    group = [
        Judgement(raw_item_id=f"raw-{i:03d}", is_pain=True, pain_summary="회의록", confidence="높음")
        for i in range(6)
    ]

    assert agent._cap_source_bias(group, {}) == group


# ══════════════════════════════════════════════
# 후보 id — 같은 구성이면 같은 id
# ══════════════════════════════════════════════


def test_candidate_id_는_구성원만으로_정해진다():
    a = InterpreterAgent.candidate_id(["raw-003", "raw-001", "raw-002"])
    b = InterpreterAgent.candidate_id(["raw-001", "raw-002", "raw-003"])

    assert a == b
    assert a.startswith("pc-")


def test_candidate_id_는_구성이_바뀌면_달라진다():
    a = InterpreterAgent.candidate_id(["raw-001", "raw-002"])
    b = InterpreterAgent.candidate_id(["raw-001", "raw-003"])

    assert a != b


def test_두_번_돌려도_같은_후보_id_가_나온다():
    items = 회의록_묶음()
    first = [c.id for c in run(items)]

    corpus_tool.reset()
    second = [c.id for c in run(list(reversed(items)))]

    assert first == second


# ══════════════════════════════════════════════
# 후보의 내용 — 숫자를 넣지 않는다
# ══════════════════════════════════════════════


def test_후보에는_숫자_필드가_없다():
    (candidate,) = run(회의록_묶음())

    assert not any(
        isinstance(v, (int, float)) and not isinstance(v, bool)
        for v in candidate.model_dump().values()
    )
    assert "case_count" not in ProblemCandidate.model_fields
    assert "source_count" not in ProblemCandidate.model_fields


def test_theme_hint_에_집계성_숫자가_없다(assert_no_fabricated_numbers):
    (candidate,) = run(회의록_묶음())

    assert candidate.theme_hint
    assert_no_fabricated_numbers(candidate.theme_hint, where="theme_hint")


def test_후보는_묶인_요약과_카테고리를_담는다():
    (candidate,) = run(회의록_묶음())

    assert candidate.category is CATEGORY
    assert len(candidate.pain_summaries) == len(candidate.raw_item_ids)
    assert all(s for s in candidate.pain_summaries)


# ══════════════════════════════════════════════
# 지난 주차 합류 (자동 승격 경로)
# ══════════════════════════════════════════════


def test_지난_주차_판정이_합류해_5건을_채운다():
    지난주 = 회의록_묶음(count=3)
    corpus_tool.save_raw_items(지난주, category=CATEGORY)
    corpus_tool.save_judgements(
        [
            Judgement(
                raw_item_id=i.id,
                is_pain=True,
                pain_summary=text_tool.clean_text(i.title, 80),
                confidence="높음",
            )
            for i in 지난주
        ],
        CATEGORY,
    )

    이번주 = [
        raw(
            10 + i,
            회의록_제목[i % len(회의록_제목)],
            f"{회의록_본문} (이번주 {i})",
            source_name=출처들[i % 3],
        )
        for i in range(3)
    ]
    candidates = run(이번주)

    assert 매니페스트()["지난주차_합류"] == 3
    assert len(candidates) == 1
    assert len(candidates[0].raw_item_ids) == 6


def test_include_pending_False_면_지난_주차를_안_본다():
    지난주 = 회의록_묶음(count=3)
    corpus_tool.save_raw_items(지난주, category=CATEGORY)
    corpus_tool.save_judgements(
        [
            Judgement(
                raw_item_id=i.id,
                is_pain=True,
                pain_summary=text_tool.clean_text(i.title, 80),
                confidence="높음",
            )
            for i in 지난주
        ],
        CATEGORY,
    )

    이번주 = [
        raw(10 + i, 회의록_제목[i], f"{회의록_본문} (이번주 {i})", source_name=출처들[i % 3])
        for i in range(3)
    ]
    run(이번주, include_pending=False)

    assert 매니페스트()["지난주차_합류"] == 0


def test_원문을_되짚을_수_없는_지난_판정은_합류시키지_않는다():
    """근거 없는 판정을 승격시키면 출처 편중도 못 걸고 카테고리도 섞인다."""
    corpus_tool.save_judgements(
        [
            Judgement(
                raw_item_id="어디에도-없는-원문",
                is_pain=True,
                pain_summary="회의록을 매번 손으로 정리하는 게 번거롭다",
                confidence="높음",
            )
        ],
        CATEGORY,
    )

    run(회의록_묶음(count=3))

    assert 매니페스트()["지난주차_합류"] == 0


# ══════════════════════════════════════════════
# 승격된 후보가 디스크에 남는다 — ②′ 근거 조립기가 읽을 수 있어야 한다
# ══════════════════════════════════════════════


def test_run_이후_corpus_tool_로_승격된_후보를_다시_읽을_수_있다():
    candidates = run(회의록_묶음())

    reloaded = corpus_tool.load_candidates(category=CATEGORY)

    assert len(reloaded) == 1
    assert reloaded == candidates


def test_후보가_없으면_candidates_파일을_안_만든다():
    assert run(회의록_묶음(count=3)) == []  # 5건 미만 → 승격 대기, 후보 아님

    assert corpus_tool.load_candidates(category=CATEGORY) == []


# ══════════════════════════════════════════════
# 매니페스트 — 단계별 잔존 건수
# ══════════════════════════════════════════════


def 매니페스트() -> dict:
    payload = corpus_tool.read_manifest()
    assert payload is not None, "매니페스트가 안 쓰였다"
    return payload["해석기"][CATEGORY.value]


def test_매니페스트에_단계별_잔존_건수가_남는다():
    run(회의록_묶음() + [광고글(91), 대상불분명글(92)])

    stats = 매니페스트()

    assert stats["입력"] == 8
    assert stats["규칙_통과"] == 6
    assert stats["규칙_보류"] == 1
    assert stats["규칙_탈락"] == 1
    assert stats["LLM_투입"] == 6
    assert stats["불편_판정"] == 6
    assert stats["묶기_대상"] == 6
    assert stats["묶음"] == 1
    assert stats["후보"] == 1
    assert stats["승격대기"] == 0


def test_매니페스트는_다른_카테고리를_지우지_않는다():
    run(회의록_묶음())
    InterpreterAgent().run(
        InterpretInput(items=[], category=Category.FINANCE, use_llm=False)
    )

    해석기 = corpus_tool.read_manifest()["해석기"]

    assert CATEGORY.value in 해석기 and Category.FINANCE.value in 해석기


def test_매니페스트의_숫자는_실행이_만든_것이다():
    """LLM 이 쓴 문장에는 숫자가 없어야 하지만, 매니페스트는 세어서 만든 값이다."""
    (candidate,) = run(회의록_묶음())

    assert 매니페스트()["후보"] == 1
    assert not find_aggregate_numbers(" ".join(candidate.pain_summaries))


def test_semantic_target_saves_unknown_and_clusters_only_confirmed(monkeypatch):
    from app.schemas.collections import TargetProfile
    from app.tools.target_evidence_tool import profile_key
    profile=TargetProfile(jobs=["마케터"],places=["회사"])
    inputs=회의록_묶음(3)
    seen={}
    def fake(items, **kwargs):
        seen["target"]=kwargs["target_profile"]
        return [Judgement(raw_item_id=i.id,is_pain=True,pain_summary="보고 기록을 따로 옮겨 적느라 시간이 소요됨",confidence="높음",
            pain_status="pain",target_status=status,target_profile_key=profile_key(profile),target_policy="evidence_v2")
            for i,status in zip(items,["confirmed","unconfirmed","conflict"])]
    monkeypatch.setattr(llm_tool,"judge_pains",fake)
    monkeypatch.setattr("app.tools.cluster_tool.group",lambda pool:seen.setdefault("pool",list(pool)) and [])
    agent=InterpreterAgent()
    agent.run(InterpretInput(items=inputs,category=CATEGORY,target_profile=profile,require_target_confirmation=True,include_pending=False))
    assert seen["target"]==profile
    assert len(corpus_tool.load_judgements(category=CATEGORY))==3
    assert [j.target_status for j in seen["pool"]]==["confirmed"]
    assert agent.target_confirmed_ids=={inputs[0].id}
    assert agent.target_unconfirmed_ids=={inputs[1].id}
    assert agent.target_conflicting_ids=={inputs[2].id}


def test_partial_llm_failure_checkpoint_keeps_success_and_excludes_overflow(monkeypatch):
    from app.core.llm import LLMError
    from app.schemas.collections import TargetProfile
    profile=TargetProfile(jobs=["마케터"],places=["회사"])
    inputs=회의록_묶음(5)
    for item in inputs:
        item.title="회의록 입력"
        item.snippet="저는 마케터이고 회사에서 매번 손으로 회의록을 옮겨 적느라 마감 시간을 넘겼습니다."
    advertisement=raw(99,"협찬 글","협찬을 받아 사용하는 제품을 소개하는 광고 글입니다. 매번 일일이 정리하시는 분들을 위한 상품입니다.")
    class Fake:
        calls=0
        def complete_json(self,prompt,**kwargs):
            self.calls+=1
            if self.calls==2: raise LLMError("batch interrupted")
            return [dict(id=item.id,is_pain=False,pain_status="not_pain",confidence="높음",experience_type="self",experience_evidence=item.snippet,
                target_values={"jobs":"마케터","places":"회사"},target_field_status={"jobs":"confirmed","places":"confirmed"},target_evidence={"jobs":item.snippet,"places":item.snippet}) for item in inputs[:2]]
    fake=Fake()
    monkeypatch.setattr(llm_tool,"get_llm",lambda:fake)
    monkeypatch.setattr(settings,"JUDGE_BATCH_SIZE",2)
    agent=InterpreterAgent()
    agent.run(InterpretInput(items=inputs+[advertisement],category=CATEGORY,target_profile=profile,require_target_confirmation=True,include_pending=False,max_llm_items=4))
    assert agent.processed_raw_ids=={inputs[0].id,inputs[1].id,advertisement.id}
    assert agent.failed_raw_ids=={inputs[2].id,inputs[3].id}
    assert inputs[4].id not in agent.processed_raw_ids | agent.failed_raw_ids
    assert set(agent.llm_diagnostics["failed_raw_ids"])==agent.failed_raw_ids


def test_latest_negative_pending_judgement_revokes_old_pain(monkeypatch):
    item=회의록_묶음(1)[0]
    positive=Judgement(raw_item_id=item.id,is_pain=True,pain_summary="기록을 옮기는 작업 때문에 마감이 지연됨",confidence="높음")
    negative=positive.model_copy(update={"is_pain":False,"pain_summary":None,"pain_status":"not_pain"})
    agent=InterpreterAgent()
    monkeypatch.setattr(agent,"_recent_raw_map",lambda category:{item.id:item})
    monkeypatch.setattr(corpus_tool,"recent_weeks",lambda *args:["2026-W37","2026-W36"])
    for current in [[positive,negative],[negative]]:
        monkeypatch.setattr(corpus_tool,"load_judgements",lambda week,category:current if week=="2026-W37" else [positive])
        pool=[]
        _,count=agent._merge_pending(pool,{},CATEGORY)
        assert count==0 and pool==[]
