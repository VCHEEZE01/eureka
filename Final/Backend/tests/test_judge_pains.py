"""
llm_tool.judge_pains 테스트.

★ 이 함수의 본체는 "모델 말을 믿지 않는" 방어 다섯 개다. 전부 여기서 검사한다.
    1. 입력에 없는 id(환각) 폐기
    2. 응답에서 빠진 건은 confidence="낮음" 으로 채움 — 조용한 유실 금지
    3. 요약 속 집계성 숫자 제거 (제1규칙: 숫자는 LLM 이 만들지 않는다)
    4. 원문 복제 차단
    5. 라벨·is_pain 정규화

★ 그리고 무슨 일이 있어도 예외를 위로 올리지 않는다.
  한 배치 때문에 주간 배치가 죽으면 그 주 수집이 통째로 날아간다.

★ 네트워크를 부르지 않는다. core.llm 싱글턴에 가짜를 꽂는다.
"""

from __future__ import annotations

import pytest

from app.config.settings import settings
from app.core.llm import EchoLLM, LLMError, reset_llm, set_llm
from app.tools import llm_tool
from app.tools.llm_tool import copy_ratio, judge_call_count, judge_pains


# ══════════════════════════════════════════════
# 도우미
# ══════════════════════════════════════════════


class FakeLLM:
    """complete_json 이 정해진 것을 돌려주는 대역. 호출 기록을 남긴다."""

    def __init__(self, *responses, error: Exception | None = None):
        self._responses = list(responses)
        self._error = error
        self.prompts: list[str] = []
        self.kwargs: list[dict] = []

    def complete_json(self, prompt: str, **kw):
        self.prompts.append(prompt)
        self.kwargs.append(kw)
        if self._error is not None:
            raise self._error
        if not self._responses:
            return []
        return self._responses.pop(0) if len(self._responses) > 1 else self._responses[0]


@pytest.fixture
def llm():
    """가짜 클라이언트를 꽂아 주는 도우미. 테스트가 끝나면 되돌린다."""
    made: list[FakeLLM] = []

    def _use(*responses, error: Exception | None = None) -> FakeLLM:
        client = FakeLLM(*responses, error=error)
        set_llm(client)
        made.append(client)
        return client

    yield _use
    reset_llm()


@pytest.fixture
def item(make_raw_item):
    """회의록 하나. 판별 대상으로 쓴다."""
    return make_raw_item(
        id="raw-001",
        title="회의록 정리가 너무 번거롭습니다",
        snippet="회의 끝나고 회의록을 매번 손으로 옮겨 적는 게 번거롭네요. 매주 반복입니다.",
        source_name="네이버 블로그",
    )


def row(item_id: str, **over) -> dict:
    """모델이 잘 대답했을 때의 한 줄."""
    base = {
        "id": item_id,
        "is_pain": True,
        "pain_summary": "회의록 작성 자동화가 안 돼 반복 입력이 쌓인다",
        "confidence": "높음",
        "severity": "중간",
        "has_need_signal": True,
    }
    base.update(over)
    return base


# ══════════════════════════════════════════════
# 기본 계약 — 개수와 순서
# ══════════════════════════════════════════════


def test_빈_입력이면_LLM_을_부르지_않는다(llm):
    client = llm([row("raw-001")])
    assert judge_pains([]) == []
    assert client.prompts == []


def test_입력과_같은_개수_같은_순서로_돌려준다(llm, make_raw_item):
    items = [make_raw_item(id=f"raw-{i:03d}") for i in range(1, 4)]
    llm([row("raw-003"), row("raw-001"), row("raw-002")])  # 순서를 섞어 응답

    out = judge_pains(items)

    assert [j.raw_item_id for j in out] == ["raw-001", "raw-002", "raw-003"]


def test_정상_응답을_그대로_옮긴다(llm, item):
    llm([row("raw-001")])

    (j,) = judge_pains([item])

    assert j.is_pain is True
    assert j.pain_summary == "회의록 작성 자동화가 안 돼 반복 입력이 쌓인다"
    assert j.confidence == "높음"
    assert j.severity == "중간"
    assert j.has_need_signal is True


# ══════════════════════════════════════════════
# 방어 1 — 환각 id
# ══════════════════════════════════════════════


def test_입력에_없는_id_는_버린다(llm, item):
    llm([row("raw-999"), row("raw-001")])

    (j,) = judge_pains([item])

    assert j.raw_item_id == "raw-001"
    assert j.pain_summary == "회의록 작성 자동화가 안 돼 반복 입력이 쌓인다"


def test_환각_id_만_왔으면_전건_강등(llm, item):
    llm([row("없는-id-1"), row("없는-id-2")])

    (j,) = judge_pains([item])

    assert j.is_pain is False
    assert j.confidence == "낮음"
    assert j.pain_summary is None


def test_같은_id_가_두_번_오면_첫_번째만_쓴다(llm, item):
    llm([row("raw-001", pain_summary="먼저 온 요약이다"), row("raw-001", pain_summary="나중 것")])

    (j,) = judge_pains([item])

    assert j.pain_summary == "먼저 온 요약이다"


# ══════════════════════════════════════════════
# 방어 2 — 응답 누락 보정 (조용한 유실 금지)
# ══════════════════════════════════════════════


def test_응답에서_빠진_건은_낮음으로_채운다(llm, make_raw_item):
    items = [make_raw_item(id=f"raw-{i:03d}") for i in range(1, 4)]
    llm([row("raw-002")])

    out = judge_pains(items)

    assert len(out) == 3
    assert [j.confidence for j in out] == ["낮음", "높음", "낮음"]
    assert [j.is_pain for j in out] == [False, True, False]


def test_강등된_건도_has_need_signal_은_규칙으로_채운다(llm, make_raw_item):
    """이 값은 모델이 아니라 사전이 만든다. 판별 실패와 무관하게 남아야 한다."""
    item = make_raw_item(
        id="raw-001",
        title="회의록 자동 정리 도구가 있었으면 좋겠다",
        snippet="회의 끝나고 손으로 옮겨 적는 게 번거로운데 그런 게 없어서 아쉽다.",
    )
    llm([])  # 아무것도 안 준 응답

    (j,) = judge_pains([item])

    assert j.confidence == "낮음"
    assert j.has_need_signal is True


# ══════════════════════════════════════════════
# 방어 3 — 집계성 숫자 차단 (제1규칙)
# ══════════════════════════════════════════════


def test_요약에서_집계성_숫자를_지운다(llm, item, assert_no_fabricated_numbers):
    llm([row("raw-001", pain_summary="회의록 정리 불편이 137건 넘게 보고되고 있다")])

    (j,) = judge_pains([item])

    assert_no_fabricated_numbers(j.pain_summary, where="pain_summary")
    assert "137" not in j.pain_summary
    assert "회의록 정리 불편이" in j.pain_summary


@pytest.mark.parametrize(
    "summary",
    [
        "회의록 정리에 불만인 사람이 42명 있다는 이야기다",
        "회의록 관련 글이 88개 올라와 있다는 내용이다",
        "회의록 정리 시간이 3배 늘었다는 이야기가 있다",
        "회의록 정리 불만이 30% 늘었다는 이야기가 있다",
        "회의록 정리 관련 글이 12만 건 있다는 이야기다",
    ],
)
def test_여러_단위의_집계_수치를_전부_지운다(
    llm, item, assert_no_fabricated_numbers, summary
):
    llm([row("raw-001", pain_summary=summary)])

    (j,) = judge_pains([item])

    assert_no_fabricated_numbers(j.pain_summary or "", where=summary)


def test_숫자를_지우고_남은_게_너무_짧으면_요약을_버린다(llm, item):
    llm([row("raw-001", pain_summary="137건")])

    (j,) = judge_pains([item])

    assert j.pain_summary is None
    assert j.is_pain is False  # 요약을 못 쓰면 불편이라 부르지 않는다


def test_시간_서술은_지우지_않는다(llm, item):
    """'3일에 한 번' 같은 서술은 집계가 아니라 정당한 진술이다."""
    llm([row("raw-001", pain_summary="회의가 끝날 때마다 회의록을 다시 옮겨 적는다")])

    (j,) = judge_pains([item])

    assert j.pain_summary == "회의가 끝날 때마다 회의록을 다시 옮겨 적는다"


# ══════════════════════════════════════════════
# 방어 4 — 원문 복제 차단
# ══════════════════════════════════════════════


def test_원문을_그대로_베낀_요약은_버린다(llm, item):
    llm([row("raw-001", pain_summary=item.snippet)])

    (j,) = judge_pains([item])

    assert j.pain_summary is None
    assert j.is_pain is False


def test_줄바꿈만_바꾼_복제도_버린다(llm, item):
    """공백을 지우고 세기 때문에 눈속임이 통하지 않는다."""
    disguised = item.snippet.replace(" ", "\n")
    llm([row("raw-001", pain_summary=disguised)])

    (j,) = judge_pains([item])

    assert j.pain_summary is None


def test_제대로_요약하면_통과한다(llm, item):
    llm([row("raw-001", pain_summary="회의록을 손으로 옮겨 적는 반복 작업이 부담이다")])

    (j,) = judge_pains([item])

    assert j.pain_summary == "회의록을 손으로 옮겨 적는 반복 작업이 부담이다"


def test_copy_ratio_는_유사도가_아니라_포함률이다():
    긴_원문 = "안녕하세요 " * 40 + "회의록을 매번 손으로 옮겨 적는 게 번거롭습니다"

    assert copy_ratio("회의록을 매번 손으로 옮겨 적는 게 번거롭습니다", 긴_원문) == 1.0
    assert copy_ratio("", 긴_원문) == 0.0
    assert copy_ratio("회의록", "") == 0.0
    assert copy_ratio("전혀 다른 이야기", "abcdefg") < llm_tool.COPY_RATIO_LIMIT


# ══════════════════════════════════════════════
# 방어 5 — 값 정규화
# ══════════════════════════════════════════════


@pytest.mark.parametrize("bad", ["매우 높음", "high", "", None, 3, "보통"])
def test_이상한_confidence_는_낮음으로_내린다(llm, item, bad):
    llm([row("raw-001", confidence=bad)])

    (j,) = judge_pains([item])

    assert j.confidence == "낮음"


@pytest.mark.parametrize("bad", ["심각", "high", 5, None])
def test_이상한_severity_는_None(llm, item, bad):
    llm([row("raw-001", severity=bad)])

    (j,) = judge_pains([item])

    assert j.severity is None


def test_is_pain_이_참인데_요약이_없으면_거짓으로_내린다(llm, item):
    llm([row("raw-001", pain_summary=None)])

    (j,) = judge_pains([item])

    assert j.is_pain is False
    assert j.pain_summary is None
    assert j.severity is None


def test_is_pain_이_거짓이면_요약과_severity_를_비운다(llm, item):
    llm([row("raw-001", is_pain=False)])

    (j,) = judge_pains([item])

    assert j.is_pain is False
    assert j.pain_summary is None
    assert j.severity is None


@pytest.mark.parametrize(
    "value,expected", [("true", True), ("예", True), ("false", False), ("아니오", False)]
)
def test_문자열로_온_is_pain_도_받아_준다(llm, item, value, expected):
    llm([row("raw-001", is_pain=value)])

    (j,) = judge_pains([item])

    assert j.is_pain is expected


def test_has_need_signal_을_안_주면_규칙으로_보완한다(llm, make_raw_item):
    item = make_raw_item(
        id="raw-001",
        title="회의록 정리가 번거롭다",
        snippet="회의 끝나고 손으로 옮겨 적는 게 번거로운데 자동으로 해 주는 게 없어서 아쉽다.",
    )
    llm([row("raw-001", has_need_signal=None)])

    (j,) = judge_pains([item])

    assert j.has_need_signal is True


def test_요약이_문자열이_아니면_버린다(llm, item):
    llm([row("raw-001", pain_summary={"text": "회의록 정리가 번거롭다"})])

    (j,) = judge_pains([item])

    assert j.pain_summary is None
    assert j.is_pain is False


def test_지나치게_긴_요약은_잘라낸다(llm, item):
    llm([row("raw-001", pain_summary="회의록 정리 부담 " * 40)])

    (j,) = judge_pains([item])

    assert len(j.pain_summary) <= 120


# ══════════════════════════════════════════════
# 실패해도 죽지 않는다
# ══════════════════════════════════════════════


def test_LLMError_면_배치를_통째로_강등하고_계속_간다(llm, make_raw_item):
    items = [make_raw_item(id=f"raw-{i:03d}") for i in range(1, 4)]
    llm(error=LLMError("게이트웨이가 응답하지 않는다"))

    out = judge_pains(items)  # 예외가 올라오면 안 된다

    assert len(out) == 3
    assert all(j.confidence == "낮음" and not j.is_pain for j in out)


@pytest.mark.parametrize("raw", [None, 42, "그냥 문자열", {"message": "실패"}, True])
def test_배열이_아닌_응답이면_강등한다(llm, item, raw):
    llm(raw)

    (j,) = judge_pains([item])

    assert j.confidence == "낮음"
    assert j.is_pain is False


def test_배열_안의_쓰레기_줄은_건너뛴다(llm, item):
    llm([None, "문자열", 3, row("raw-001")])

    (j,) = judge_pains([item])

    assert j.is_pain is True


def test_객체로_감싸_온_응답도_읽는다(llm, item):
    llm({"judgements": [row("raw-001")]})

    (j,) = judge_pains([item])

    assert j.is_pain is True


def test_판정_하나만_객체로_와도_읽는다(llm, item):
    llm(row("raw-001"))

    (j,) = judge_pains([item])

    assert j.is_pain is True


def test_한_배치가_실패해도_다른_배치는_살아_있다(llm, make_raw_item, monkeypatch):
    monkeypatch.setattr(settings, "JUDGE_BATCH_SIZE", 2)
    items = [make_raw_item(id=f"raw-{i:03d}") for i in range(1, 5)]

    class 반쪽LLM(FakeLLM):
        def complete_json(self, prompt, **kw):
            self.prompts.append(prompt)
            if len(self.prompts) == 1:
                raise LLMError("첫 배치만 실패")
            return [row("raw-003"), row("raw-004")]

    set_llm(반쪽LLM())
    out = judge_pains(items)

    assert [j.confidence for j in out] == ["낮음", "낮음", "높음", "높음"]


# ══════════════════════════════════════════════
# 배치 나누기
# ══════════════════════════════════════════════


def test_JUDGE_BATCH_SIZE_대로_나눠_부른다(llm, make_raw_item, monkeypatch):
    monkeypatch.setattr(settings, "JUDGE_BATCH_SIZE", 2)
    items = [make_raw_item(id=f"raw-{i:03d}") for i in range(1, 6)]
    client = llm([])

    out = judge_pains(items)

    assert len(client.prompts) == 3  # 2 + 2 + 1
    assert len(out) == 5


def test_설정을_호출_시점에_읽는다(llm, make_raw_item, monkeypatch):
    """모듈 레벨에 캡처해 뒀다면 이 테스트가 깨진다."""
    items = [make_raw_item(id=f"raw-{i:03d}") for i in range(1, 5)]
    client = llm([])

    monkeypatch.setattr(settings, "JUDGE_BATCH_SIZE", 4)
    judge_pains(items)
    monkeypatch.setattr(settings, "JUDGE_BATCH_SIZE", 1)
    judge_pains(items)

    assert len(client.prompts) == 1 + 4


def test_배치_크기가_0이하여도_무한루프에_빠지지_않는다(llm, make_raw_item, monkeypatch):
    monkeypatch.setattr(settings, "JUDGE_BATCH_SIZE", 0)
    items = [make_raw_item(id=f"raw-{i:03d}") for i in range(1, 4)]
    client = llm([])

    assert len(judge_pains(items)) == 3
    assert len(client.prompts) == 3


def test_judge_call_count(monkeypatch):
    monkeypatch.setattr(settings, "JUDGE_BATCH_SIZE", 20)

    assert judge_call_count(0) == 0
    assert judge_call_count(-5) == 0
    assert judge_call_count(1) == 1
    assert judge_call_count(20) == 1
    assert judge_call_count(21) == 2
    assert judge_call_count(200) == 10


def test_judge_call_count_가_실제_호출_수와_맞는다(llm, make_raw_item, monkeypatch):
    """실행 전 비용 안내가 실제와 어긋나면 안내의 의미가 없다."""
    monkeypatch.setattr(settings, "JUDGE_BATCH_SIZE", 3)
    items = [make_raw_item(id=f"raw-{i:03d}") for i in range(1, 8)]
    client = llm([])

    judge_pains(items)

    assert len(client.prompts) == judge_call_count(len(items)) == 3


# ══════════════════════════════════════════════
# 프롬프트에 실리는 것
# ══════════════════════════════════════════════


def test_프롬프트에는_정제된_스니펫만_들어간다(llm, make_raw_item):
    item = make_raw_item(
        id="raw-001",
        title="<b>회의록</b> 정리가 번거롭다",
        snippet="연락처 010-1234-5678 로 문의 주세요. 회의록을 손으로 옮겨 적는 게 번거롭습니다.",
    )
    client = llm([row("raw-001")])

    judge_pains([item])

    prompt = client.prompts[0]
    assert "<b>" not in prompt
    assert "raw-001" in prompt


def test_판별은_temperature_0_으로_부른다(llm, item):
    client = llm([row("raw-001")])

    judge_pains([item])

    assert client.kwargs[0]["temperature"] == 0.0


# ══════════════════════════════════════════════
# 오프라인 경로 (LLM_DRY_RUN)
# ══════════════════════════════════════════════


def test_EchoLLM_으로도_배선이_돈다(make_raw_item):
    """키 없이 --no-llm 없이 돌려도 판별 배선이 끝까지 간다."""
    reset_llm()
    set_llm(EchoLLM())
    items = [make_raw_item(id=f"raw-{i:03d}") for i in range(1, 6)]

    try:
        out = judge_pains(items)
    finally:
        reset_llm()

    assert [j.raw_item_id for j in out] == [f"raw-{i:03d}" for i in range(1, 6)]
    assert all(j.confidence in ("높음", "중간", "낮음") for j in out)
