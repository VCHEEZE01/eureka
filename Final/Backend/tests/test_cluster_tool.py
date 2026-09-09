"""
묶기 도구 테스트.

★ 여기서 지키는 계약은 넷이다.
  1. 결정성 — 같은 입력이면 두 번 돌려도 완전히 같은 출력이다.
     이게 깨지면 "왜 이 글들이 한 문제로 묶였는지" 를 나중에 설명할 수 없다.
  2. 5건 미만도 버리지 않는다 — 1건짜리도 [[j]] 로 나온다.
     여기서 지우면 "미달 후보를 쌓아 다음 주에 자동 승격"이 불가능해진다.
  3. sklearn 이 없어도 돈다 — 순수 파이썬 폴백이 같은 답을 낸다.
  4. name_group 은 LLM 을 안 부르고, 숫자·수량 표현을 남기지 않는다.

★ 네트워크도 LLM 도 여기서는 볼 일이 없어야 정상이다.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from app.config.settings import settings
from app.schemas.models import Judgement
from app.tools import cluster_tool
from tests.conftest import find_aggregate_numbers


# ══════════════════════════════════════════════
# 도우미 — 실제 판별 결과처럼 생긴 요약들
# ══════════════════════════════════════════════


def j(raw_id: str, summary: str | None, confidence: str = "높음") -> Judgement:
    return Judgement(
        raw_item_id=raw_id,
        is_pain=summary is not None,
        pain_summary=summary,
        confidence=confidence,
    )


#: 같은 불편의 다른 표현들. ② 의 판별 단계가 한 문장으로 정규화해 둔 모습이다.
회의록_묶음 = [
    "회의록을 매번 손으로 정리하는 게 번거롭다",
    "회의록을 매번 손으로 정리하기가 번거롭다",
    "회의록을 매번 손으로 정리해야 해서 번거롭다",
    "회의록을 매번 손으로 정리하는 일이 번거롭다",
    "회의록을 매번 손으로 정리하느라 번거롭다",
]

가계부_묶음 = [
    "가계부에 카드 내역을 손으로 입력해야 해서 귀찮다",
    "가계부에 카드 내역을 손으로 입력하는 게 귀찮다",
    "가계부에 카드 내역을 손으로 입력하기가 귀찮다",
]


def two_topic_pool() -> list[Judgement]:
    """서로 다른 두 주제. 5건짜리와 3건짜리."""
    summaries = 회의록_묶음 + 가계부_묶음
    return [j(f"raw-{i:03d}", s) for i, s in enumerate(summaries)]


def ids(groups: list[list[Judgement]]) -> list[list[str]]:
    return [[x.raw_item_id for x in g] for g in groups]


@pytest.fixture(autouse=True)
def _clean_vectorizer():
    """주입된 벡터라이저가 다음 테스트로 새지 않게."""
    cluster_tool.reset_vectorizer()
    yield
    cluster_tool.reset_vectorizer()


@pytest.fixture(params=["tfidf", "hash"])
def backend(request, monkeypatch):
    """두 백엔드 모두에서 같은 계약이 성립해야 한다."""
    monkeypatch.setattr(settings, "CLUSTER_BACKEND", request.param)
    cluster_tool.reset_vectorizer()
    return request.param


# ══════════════════════════════════════════════
# group() — 입력 걸러내기
# ══════════════════════════════════════════════


def test_group_빈_입력은_빈_결과():
    assert cluster_tool.group([]) == []


def test_group_pain_summary_없는_항목은_제외한다():
    pool = [
        j("raw-001", "회의록을 매번 손으로 정리하는 게 번거롭다"),
        j("raw-002", None),  # 불편이 아니라고 판정된 건
        j("raw-003", "   "),  # 공백뿐 — 묶을 문장이 없다
    ]
    assert ids(cluster_tool.group(pool)) == [["raw-001"]]


def test_group_전부_요약이_없으면_빈_결과():
    assert cluster_tool.group([j("raw-001", None), j("raw-002", None)]) == []


def test_group_한_건이면_그_한_건짜리_묶음():
    groups = cluster_tool.group([j("raw-001", "회의록 정리가 번거롭다")])
    assert ids(groups) == [["raw-001"]]


# ══════════════════════════════════════════════
# group() — 실제로 묶이는가
# ══════════════════════════════════════════════


def test_group_같은_불편끼리_묶인다(backend):
    groups = cluster_tool.group(two_topic_pool())

    assert ids(groups) == [
        ["raw-000", "raw-001", "raw-002", "raw-003", "raw-004"],
        ["raw-005", "raw-006", "raw-007"],
    ], f"{backend} 백엔드에서 주제가 갈리지 않았다"


def test_group_큰_묶음이_앞에_온다(backend):
    sizes = [len(g) for g in cluster_tool.group(two_topic_pool())]
    assert sizes == sorted(sizes, reverse=True)


def test_group_다섯건_미만도_버리지_않는다(backend):
    """MIN_GROUP_SIZE 는 부르는 쪽이 적용한다. 여기서 지우면 자동 승격이 죽는다."""
    groups = cluster_tool.group(two_topic_pool())

    assert min(len(g) for g in groups) == 3
    assert settings.MIN_GROUP_SIZE == 5  # 기준은 있지만 여기서 쓰지 않는다
    # 입력 전건이 어딘가의 묶음에 살아 있어야 한다
    assert sorted(x for g in ids(groups) for x in g) == [
        f"raw-{i:03d}" for i in range(8)
    ]


def test_group_서로_다른_불편은_안_붙는다(backend):
    """어휘가 안 겹치면 각자 혼자 남는다."""
    pool = [
        j("raw-001", "회의록을 매번 손으로 정리하는 게 번거롭다"),
        j("raw-002", "병원 예약을 전화로만 받아서 불편하다"),
        j("raw-003", "학원 시간표가 매주 바뀌어 헷갈린다"),
    ]
    assert ids(cluster_tool.group(pool)) == [["raw-001"], ["raw-002"], ["raw-003"]]


# ══════════════════════════════════════════════
# 결정성 — 이 프로젝트의 명시적 제약
# ══════════════════════════════════════════════


def test_group_두_번_돌려도_같은_출력(backend):
    pool = two_topic_pool()
    assert ids(cluster_tool.group(pool)) == ids(cluster_tool.group(pool))


def test_group_입력_순서가_바뀌어도_같은_출력(backend):
    pool = two_topic_pool()
    shuffled = [pool[i] for i in (5, 2, 7, 0, 4, 1, 6, 3)]
    assert ids(cluster_tool.group(shuffled)) == ids(cluster_tool.group(pool))


def test_group_묶음_안은_id_순으로_정렬된다(backend):
    for group in ids(cluster_tool.group(two_topic_pool())):
        assert group == sorted(group)


# ══════════════════════════════════════════════
# 벡터라이저 — 갈아끼우는 지점
# ══════════════════════════════════════════════


class AllSameVectorizer:
    """전부 같은 벡터. 무엇을 넣든 한 묶음으로 나와야 한다."""

    name = "hash"

    def fit_transform(self, texts):
        return [{"같음": 1.0} for _ in texts]


class AllDifferentVectorizer:
    """전부 직교. 무엇을 넣든 하나도 안 붙어야 한다."""

    name = "hash"

    def fit_transform(self, texts):
        return [{f"고유-{i}": 1.0} for i in range(len(texts))]


def test_set_vectorizer_로_갈아끼울_수_있다():
    pool = two_topic_pool()

    cluster_tool.set_vectorizer(AllSameVectorizer())
    assert len(cluster_tool.group(pool)) == 1

    cluster_tool.set_vectorizer(AllDifferentVectorizer())
    assert len(cluster_tool.group(pool)) == len(pool)


def test_reset_vectorizer_는_설정대로_되돌린다(monkeypatch):
    cluster_tool.set_vectorizer(AllSameVectorizer())
    cluster_tool.reset_vectorizer()

    monkeypatch.setattr(settings, "CLUSTER_BACKEND", "tfidf")
    assert cluster_tool.current_vectorizer().name == "tfidf"


def test_current_vectorizer_hash_설정이면_순수파이썬(monkeypatch):
    monkeypatch.setattr(settings, "CLUSTER_BACKEND", "hash")
    assert isinstance(
        cluster_tool.current_vectorizer(), cluster_tool.PurePythonCharVectorizer
    )


def test_current_vectorizer_sklearn이_없으면_폴백한다(monkeypatch):
    monkeypatch.setattr(settings, "CLUSTER_BACKEND", "tfidf")
    monkeypatch.setattr(cluster_tool, "_sklearn_available", lambda: False)

    assert isinstance(
        cluster_tool.current_vectorizer(), cluster_tool.PurePythonCharVectorizer
    )


def test_sklearn_import_이_깨져도_묶기가_돈다(monkeypatch):
    """sklearn 이 아예 안 잡히는 환경(가벼운 CI)에서도 결과가 나와야 한다."""
    monkeypatch.setattr(settings, "CLUSTER_BACKEND", "tfidf")
    for name in ("sklearn", "sklearn.feature_extraction.text", "sklearn.cluster"):
        monkeypatch.setitem(sys.modules, name, None)  # import 하면 ImportError

    assert cluster_tool._sklearn_available() is False
    assert ids(cluster_tool.group(two_topic_pool())) == [
        ["raw-000", "raw-001", "raw-002", "raw-003", "raw-004"],
        ["raw-005", "raw-006", "raw-007"],
    ]


def test_군집기만_없어도_임계값_그래프로_내려간다(monkeypatch):
    """벡터는 sklearn 으로 만들되 AgglomerativeClustering 만 없는 경우."""
    monkeypatch.setattr(settings, "CLUSTER_BACKEND", "tfidf")
    monkeypatch.setitem(sys.modules, "sklearn.cluster", None)

    assert ids(cluster_tool.group(two_topic_pool())) == [
        ["raw-000", "raw-001", "raw-002", "raw-003", "raw-004"],
        ["raw-005", "raw-006", "raw-007"],
    ]


def test_두_백엔드가_같은_묶음을_낸다(monkeypatch):
    """임계값을 백엔드마다 따로 잡지 않아도 되게 가중치 식을 맞춰 뒀다."""
    pool = two_topic_pool()

    monkeypatch.setattr(settings, "CLUSTER_BACKEND", "tfidf")
    cluster_tool.reset_vectorizer()
    tfidf_groups = ids(cluster_tool.group(pool))

    monkeypatch.setattr(settings, "CLUSTER_BACKEND", "hash")
    cluster_tool.reset_vectorizer()
    assert ids(cluster_tool.group(pool)) == tfidf_groups


# ══════════════════════════════════════════════
# 임계값 선택
# ══════════════════════════════════════════════


def test_임계값은_설정을_그때그때_읽는다(monkeypatch):
    monkeypatch.setattr(settings, "CLUSTER_BACKEND", "tfidf")
    monkeypatch.setattr(settings, "CLUSTER_THRESHOLD_TFIDF", 0.11)
    assert cluster_tool._threshold_for("tfidf") == 0.11


def test_embedding_설정에서_tfidf로_폴백하면_tfidf_임계값을_쓴다(monkeypatch):
    """코사인 스케일이 다르므로 실제로 쓰인 백엔드 기준값을 써야 한다."""
    monkeypatch.setattr(settings, "CLUSTER_BACKEND", "embedding")
    assert settings.cluster_threshold() == settings.CLUSTER_THRESHOLD_EMBED
    assert cluster_tool._threshold_for("tfidf") == settings.CLUSTER_THRESHOLD_TFIDF


def test_embedding_벡터라이저가_실제로_붙으면_embed_임계값(monkeypatch):
    monkeypatch.setattr(settings, "CLUSTER_BACKEND", "tfidf")
    assert cluster_tool._threshold_for("embedding") == settings.CLUSTER_THRESHOLD_EMBED


# ══════════════════════════════════════════════
# 1차 블록 나누기
# ══════════════════════════════════════════════


def test_block_keys_조사를_떼_준다():
    keys = cluster_tool.block_keys("회의록이 회의록을 정리한다")
    assert "회의록" in keys


def test_block_keys_불용어와_숫자는_빼_준다():
    keys = cluster_tool.block_keys("그냥 너무 137 회의록")
    assert "그냥" not in keys and "너무" not in keys and "137" not in keys


def test_스무건_이상에서도_주제가_갈린다(backend):
    """
    MIN_DOCS_FOR_MIN_DF 를 넘기면 min_df=2 와 블록 열쇠말 상한이 함께 켜진다.
    실제 배치는 항상 이쪽 경로를 탄다.
    """
    병원 = [
        "병원 예약을 전화로만 받아서 불편하다",
        "병원 예약을 전화로만 받는 게 불편하다",
        "병원 예약을 전화로만 해야 해서 불편하다",
        "병원 예약을 전화로만 받아 불편했다",
    ]
    summaries = (
        [회의록_묶음[i % 5] for i in range(12)]
        + [가계부_묶음[i % 3] for i in range(10)]
        + [병원[i % 4] for i in range(8)]
    )
    pool = [j(f"raw-{i:03d}", s) for i, s in enumerate(summaries)]

    groups = cluster_tool.group(pool)

    assert [len(g) for g in groups] == [12, 10, 8]
    assert all(len(g) > 1 for g in groups)


def test_블록이_MAX_BLOCK_에서_잘린다(monkeypatch):
    """1차가 실패해 블록이 비대해져도 O(n²) 를 묶어 둬야 한다."""
    monkeypatch.setattr(cluster_tool, "MAX_BLOCK", 3)
    texts = ["회의록 정리가 번거롭다"] * 7
    blocks = cluster_tool._blocks(texts)

    assert [len(b) for b in blocks] == [3, 3, 1]
    assert sorted(i for b in blocks for i in b) == list(range(7))


# ══════════════════════════════════════════════
# name_group() — 숫자를 남기지 않는다
# ══════════════════════════════════════════════


def test_name_group_주제어를_뽑는다(backend):
    group = [j(f"raw-{i:03d}", s) for i, s in enumerate(회의록_묶음)]
    name = cluster_tool.name_group(group)

    assert "회의록" in name
    assert len(name) <= 12


def test_name_group_은_빈_묶음에서_빈_문자열():
    assert cluster_tool.name_group([]) == ""
    assert cluster_tool.name_group([j("raw-001", None)]) == ""


def test_name_group_집계성_숫자를_남기지_않는다(assert_no_fabricated_numbers):
    group = [
        j("raw-001", "회의록 정리에 매번 30분 넘게 쓴다고 137건이 말한다"),
        j("raw-002", "회의록 정리에 매번 30분 넘게 쓴다고 137건이 말한다"),
        j("raw-003", "회의록 정리에 매번 30분씩 든다는 글이 45개 있다"),
    ]
    name = cluster_tool.name_group(group)

    assert_no_fabricated_numbers(name, where="theme_hint")
    assert not any(ch.isdigit() for ch in name), name


def test_name_group_수량_표현을_남기지_않는다():
    group = [
        j("raw-001", "가계부 입력을 세 번 두 번 반복해야 한다"),
        j("raw-002", "가계부 입력을 세 번 두 번 반복해야 한다"),
    ]
    name = cluster_tool.name_group(group)

    for quantity in ("건", "명", "개", "번", "회", "배", "가지"):
        assert quantity not in name.split(), name


def test_name_group_도_결정적이다(backend):
    group = [j(f"raw-{i:03d}", s) for i, s in enumerate(회의록_묶음)]
    assert cluster_tool.name_group(group) == cluster_tool.name_group(group)
    assert cluster_tool.name_group(group) == cluster_tool.name_group(group[::-1])


def test_묶기는_LLM_을_아예_import_하지_않는다():
    """
    LLM 에 맡기면 같은 입력에도 결과가 매번 달라진다. 이 모듈은 순수 계산만 한다.
    호출을 가로채는 대신 의존 자체가 없는지 본다 — 우회할 구멍이 없다.
    """
    source = Path(cluster_tool.__file__).read_text(encoding="utf-8")
    import_lines = [
        line
        for line in source.splitlines()
        if line.startswith(("import ", "from ")) and "llm" in line
    ]

    assert import_lines == []
    assert not [name for name in vars(cluster_tool) if "llm" in name.lower()]


def test_요약에서_집계성_숫자를_찾는_도우미가_실제로_동작한다():
    """위 테스트가 헛돌지 않는지 확인한다."""
    assert find_aggregate_numbers("사례 137건") == ["137건"]
    assert find_aggregate_numbers("회의록 정리") == []
