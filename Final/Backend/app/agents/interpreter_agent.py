"""
② 해석기

역할  : 긁어온 글 중 진짜 불편만 골라내고, 비슷한 것끼리 묶는다
입력  : 원문(RawItem) 목록
출력  : 문제 후보(ProblemCandidate) 목록

────────────────────────────────────────────────
판별은 3층이다 (docs/DATA_COLLECTION.md 3-3 · 3-6)
────────────────────────────────────────────────
  3-A 규칙 선필터   전량 · 비용 0 · 재현 가능   → text_tool.rule_judge
        PASS 통과 / HOLD 보류(버리지 않는다) / DROP 탈락
  3-B 랭킹 + 상한   signal_score 내림차순, 상위 max_llm_items 만 LLM 으로
        ★ 초과분은 버리지 않고 overflow 로 쌓는다. 다음 주에 다시 본다.
  3-C LLM 판별      llm_tool.judge_pains — 배치로 묶어 호출 수를 줄인다

★ 왜 규칙을 먼저 돌리나
  전량을 LLM 에 넣으면 비용이 수집량에 비례해 터진다. 광고·30자 미만·
  불편 신호가 없는 글도 의미 판별 대상에 포함한다. 키워드는 랭킹에만 사용한다.

★ 출처 편중 상한을 여기서 거는 이유 (docs 9절)
  Judgement 에는 출처 정보가 없다. RawItem 을 손에 쥔 건 이 에이전트뿐이라
  "한 카페 글만 잔뜩 모인 묶음"을 걸러낼 수 있는 자리가 여기밖에 없다.

규칙
  · 묶기 결과에 "몇 건" 같은 숫자를 넣지 말 것
    → raw_item_ids 길이를 세면 된다. case_count 는 ③이 만든다.
  · settings 값을 모듈 레벨 상수로 캡처하지 말 것 (테스트가 못 갈아끼운다)
"""

from __future__ import annotations

import logging
from collections import Counter
from hashlib import sha256
from typing import Optional

from pydantic import BaseModel, Field

from app.agents.base import Agent
from app.schemas.collections import TargetProfile
from app.tools.target_query_tool import target_label_conflicts
from app.config.settings import settings
from app.schemas.models import Category, Judgement, ProblemCandidate, RawItem
from app.tools import cluster_tool, corpus_tool, llm_tool, text_tool, target_evidence_tool
from app.tools.text_tool import Verdict

logger = logging.getLogger(__name__)

#: 이 확신도는 묶기로 넘기지 않는다. 다음 주에 다시 본다.
WEAK_CONFIDENCE = "낮음"

#: 지난 주차 판정을 몇 주까지 끌어와 함께 묶을 것인가 (자동 승격 경로).
PENDING_WEEKS = 4

#: 후보 id 접두어. 주차가 달라도 구성이 같으면 같은 id 가 나와야 한다.
CANDIDATE_ID_PREFIX = "pc-"
_CANDIDATE_ID_LEN = 16

#: --no-llm 로 규칙만 돌렸을 때 붙이는 확신도.
#: "높음"은 근거가 없고 "낮음"이면 묶기까지 못 가므로 가운데를 쓴다.
_RULE_ONLY_CONFIDENCE = "중간"


class InterpretInput(BaseModel):
    """
    ★ 새로 붙이는 필드는 전부 기본값을 가진다.
      기존 호출 InterpretInput(items=..., category=...) 이 그대로 살아 있어야 한다.
    """

    items: list[RawItem]
    category: Category

    use_llm: bool = Field(
        default=True, description="False 면 규칙 판별만으로 Judgement 를 만든다"
    )
    track_llm_failures: bool = False
    target_profile: Optional[TargetProfile] = None
    require_target_confirmation: bool = False
    include_pending: bool = Field(
        default=True, description="지난 주차 판정을 함께 묶는다 (자동 승격 경로)"
    )
    max_llm_items: Optional[int] = Field(
        default=None, description="LLM 투입 상한. None 이면 settings.MAX_LLM_ITEMS"
    )


class InterpreterAgent(Agent[InterpretInput, list[ProblemCandidate]]):
    name = "해석기"
    steps = ["불편 판별", "묶기", "묶음 정리"]

    # ══════════════════════════════════════════
    # 실행
    # ══════════════════════════════════════════

    def run(self, data: InterpretInput) -> list[ProblemCandidate]:
        # ── 1단계: 불편 판별 ──────────────────
        self.report(0)
        if data.require_target_confirmation and data.target_profile is None:
            raise ValueError("타겟 확인에는 target_profile이 필요합니다")
        passed, held, drop_reasons = self._rule_filter(data.items, allow_semantic=data.use_llm)
        if held:
            corpus_tool.save_held(held, data.category)

        target, overflow = self._rank_and_cap(passed, data.max_llm_items)
        if overflow:
            # 버리지 않는다. 다음 주에 먼저 처리한다 (docs 3-6).
            corpus_tool.save_overflow(overflow, data.category)

        self.llm_diagnostics: dict = {}
        if data.use_llm:
            judge_options = {}
            if data.track_llm_failures or data.require_target_confirmation:
                judge_options["diagnostics"] = self.llm_diagnostics
            if data.require_target_confirmation:
                judge_options["target_profile"] = data.target_profile
            judgements = llm_tool.judge_pains(target, **judge_options)
            llm_calls = llm_tool.judge_call_count(len(target))
        else:
            judgements = [self._rule_judgement(i) for i in target]
            llm_calls = 0

        target_ids = {item.id for item in target}
        successful = {j.raw_item_id for j in judgements} - set(self.llm_diagnostics.get("failed_raw_ids", []))
        if data.require_target_confirmation:
            successful &= {j.raw_item_id for j in judgements if j.target_policy == target_evidence_tool.POLICY
                           and j.target_profile_key == target_evidence_tool.profile_key(data.target_profile)}
        self.failed_raw_ids = target_ids - successful
        # Rule DROP/HOLD are terminal decisions; ranked overflow has not been processed.
        rule_processed = {item.id for item in data.items} - {item.id for item in passed}
        self.processed_raw_ids = rule_processed | successful
        if judgements:
            corpus_tool.save_judgements(judgements, data.category)
        self.report(0, done=True)

        # ── 2단계: 묶기 ───────────────────────
        self.report(1)
        self.target_confirmed_ids = {j.raw_item_id for j in judgements if j.target_status == "confirmed"}
        self.target_unconfirmed_ids = {j.raw_item_id for j in judgements if j.target_status == "unconfirmed"}
        self.target_conflicting_ids = {j.raw_item_id for j in judgements
            if j.target_status == "conflict" or (not data.require_target_confirmation and data.target_profile and target_label_conflicts(data.target_profile, j))}
        pool = [j for j in judgements if self._is_strong(j) and j.raw_item_id not in self.target_conflicting_ids
                and (not data.require_target_confirmation or self._confirmed_for(j, data.target_profile))]
        raw_map: dict[str, RawItem] = {i.id: i for i in data.items}
        pending_added = 0

        if data.include_pending:
            raw_map, pending_added = self._merge_pending(pool, raw_map, data.category, target_profile=data.target_profile if data.require_target_confirmation else None)

        groups = cluster_tool.group(pool) if pool else []
        self.report(1, done=True)

        # ── 3단계: 묶음 정리 ──────────────────
        self.report(2)
        candidates: list[ProblemCandidate] = []
        waiting: list[ProblemCandidate] = []
        min_size = max(int(settings.MIN_GROUP_SIZE), 1)
        trimmed_total = 0

        for group_items in groups:
            kept = self._cap_source_bias(group_items, raw_map)
            trimmed_total += len(group_items) - len(kept)
            if not kept:
                continue
            candidate = self._candidate(kept, data.category)
            if len(kept) >= min_size:
                candidates.append(candidate)
            else:
                # 아직 5건이 안 된다. 버리지 않고 다음 주에 다시 본다.
                waiting.append(candidate)

        if waiting:
            corpus_tool.save_pending_candidates(waiting)

        # 큰 묶음부터. 같은 크기면 id 로 고정해 순서가 흔들리지 않게 한다.
        candidates.sort(key=lambda c: (-len(c.raw_item_ids), c.id))

        # ★ 여기 없으면 반환값이 파이프라인 밖에서 즉시 사라진다. 근거 조립기가
        #   다음 단계에서 다시 읽을 수 있게 디스크에 남긴다.
        if candidates:
            corpus_tool.save_candidates(candidates, data.category)

        self._write_manifest(
            data.category,
            {
                "입력": len(data.items),
                "규칙_통과": len(passed),
                "규칙_보류": len(held),
                "규칙_탈락": len(drop_reasons),
                "탈락_사유": dict(Counter(drop_reasons)),
                "LLM_투입": len(target),
                "LLM_호출": llm_calls,
                "LLM_이월": len(overflow),
                "불편_판정": sum(1 for j in judgements if j.is_pain),
                "묶기_대상": len(pool),
                "지난주차_합류": pending_added,
                "묶음": len(groups),
                "출처편중_잘라냄": trimmed_total,
                "후보": len(candidates),
                "승격대기": len(waiting),
            },
        )
        logger.info(
            "%s: 입력 %d건 → 규칙통과 %d · LLM %d건(%d회) → 불편 %d → 묶음 %d → 후보 %d",
            data.category.value,
            len(data.items),
            len(passed),
            len(target),
            llm_calls,
            sum(1 for j in judgements if j.is_pain),
            len(groups),
            len(candidates),
        )
        self.report(2, done=True)
        return candidates

    # ══════════════════════════════════════════
    # 3-A 규칙 선필터
    # ══════════════════════════════════════════

    @staticmethod
    def _rule_filter(
        items: list[RawItem], *, allow_semantic: bool = False,
    ) -> tuple[list[RawItem], list[RawItem], list[str]]:
        """
        (통과, 보류, 탈락사유) 로 가른다.

        ★ 중복 판정 기준은 "이번 입력 안에서"다.
          corpus 의 seen 인덱스에는 ① 수집기가 방금 저장한 이 글들이 이미 들어
          있다(save_raw_items 가 인덱스를 갱신한다). 그대로 넘기면 전건이
          "중복"으로 탈락한다. 지난 배치와의 중복은 ① 이 이미 걸렀으므로
          여기서는 같은 입력 안의 중복만 본다.
        """
        seen_ids: set[str] = set()
        seen_hashes: set[str] = set()

        passed: list[RawItem] = []
        held: list[RawItem] = []
        drop_reasons: list[str] = []

        for item in items:
            verdict, reason = text_tool.rule_judge(item, seen_ids, seen_hashes)
            seen_ids.add(item.id)
            item_hash = item.content_hash or text_tool.content_hash(
                item.title, item.snippet
            )
            seen_hashes.add(item_hash)

            if verdict is Verdict.PASS or (allow_semantic and verdict is Verdict.DROP and reason == "불편 신호 없음"):
                passed.append(item)
            elif verdict is Verdict.HOLD:
                held.append(item)
            else:
                drop_reasons.append(reason)

        return passed, held, drop_reasons

    # ══════════════════════════════════════════
    # 3-B 랭킹 + 하드 상한
    # ══════════════════════════════════════════

    @staticmethod
    def _rank_and_cap(
        passed: list[RawItem], max_llm_items: Optional[int]
    ) -> tuple[list[RawItem], list[RawItem]]:
        """신호가 센 것부터 상한까지만 LLM 으로. 나머지는 이월한다."""
        # ★ settings 는 호출 시점에 읽는다.
        cap = max_llm_items if max_llm_items is not None else int(settings.MAX_LLM_ITEMS)
        cap = max(int(cap), 0)
        # 점수가 같으면 id 순 — 같은 입력이면 같은 결과가 나와야 한다.
        ranked = sorted(passed, key=lambda i: (-text_tool.signal_score(i), i.id))
        return ranked[:cap], ranked[cap:]

    # ══════════════════════════════════════════
    # 3-C 규칙만으로 판정 (use_llm=False)
    # ══════════════════════════════════════════

    @staticmethod
    def _rule_judgement(item: RawItem) -> Judgement:
        """
        LLM 없이 만드는 판정. 규칙을 통과했다는 것 이상은 주장하지 않는다.

        요약 자리에는 정제한 제목을 넣는다 — 모델이 쓴 문장이 아니므로
        "AI 서술"로 취급하면 안 된다. 배선 확인·오프라인 실행용이다.
        """
        text = f"{item.title} {item.snippet}"
        summary = text_tool.clean_text(item.title, 80) or text_tool.clean_text(
            item.snippet, 80
        )
        return Judgement(
            raw_item_id=item.id,
            is_pain=bool(summary),
            pain_summary=summary or None,
            confidence=_RULE_ONLY_CONFIDENCE,
            severity=None,
            has_need_signal=text_tool.has_need_signal(text),
            # ★ 규칙만으로 채워진다. --no-llm 에서도 ① "돈이 걸린 문제인가"가
            #   비어 있지 않도록 has_need_signal 과 같은 자리에서 채운다.
            has_payment_signal=text_tool.has_payment_signal(text),
        )

    # ══════════════════════════════════════════
    # 묶기 — 지난 주차 합류 (자동 승격 경로)
    # ══════════════════════════════════════════

    @staticmethod
    def _is_strong(j: Judgement) -> bool:
        """묶기로 넘길 판정인가. 확신 없는 건 다음 주에 다시 본다."""
        return j.is_pain and j.confidence != WEAK_CONFIDENCE

    @staticmethod
    def _confirmed_for(j: Judgement, target: TargetProfile) -> bool:
        return (j.target_status == "confirmed" and j.target_policy == target_evidence_tool.POLICY
                and j.target_profile_key == target_evidence_tool.profile_key(target))

    def _merge_pending(
        self,
        pool: list[Judgement],
        raw_map: dict[str, RawItem],
        category: Category, *, target_profile: Optional[TargetProfile] = None,
    ) -> tuple[dict[str, RawItem], int]:
        """
        지난 주차 판정을 pool 에 더한다. pool 은 제자리에서 늘어난다.

        ★ 원문을 되짚을 수 있는 것만 더한다.
          load_pending_judgements 는 카테고리를 가리지 않고 다 읽어 온다.
          이번 카테고리의 raw 에서 찾을 수 있는 건만 남겨야 (a) 다른 카테고리가
          섞이지 않고 (b) 출처 편중 상한을 걸 수 있다. 근거 없는 판정은
          승격시키지 않는다.
        """
        known = self._recent_raw_map(category)
        known.update(raw_map)  # 이번 주에 받은 원문이 우선

        seen = {j.raw_item_id for j in pool} | set(raw_map)
        # JSONL appends new judgements. Read old weeks first and let the latest
        # record win, including false/insufficient judgements that revoke old pain.
        latest: dict[str, Judgement] = {}
        for week in reversed(corpus_tool.recent_weeks(PENDING_WEEKS)):
            for judgement in corpus_tool.load_judgements(week=week, category=category):
                latest[judgement.raw_item_id] = judgement
        added = 0
        for j in latest.values():
            if j.raw_item_id in seen or not self._is_strong(j):
                continue
            if target_profile is not None and not self._confirmed_for(j, target_profile):
                continue
            if j.raw_item_id not in known:
                continue
            seen.add(j.raw_item_id)
            pool.append(j)
            added += 1

        if added:
            logger.info("지난 %d주 판정 %d건을 함께 묶는다", PENDING_WEEKS, added)
        return known, added

    @staticmethod
    def _recent_raw_map(category: Category) -> dict[str, RawItem]:
        """최근 주차의 이 카테고리 원문. 출처 편중 판정과 카테고리 확인에 쓴다."""
        out: dict[str, RawItem] = {}
        for week in reversed(corpus_tool.recent_weeks(PENDING_WEEKS)):
            for item in corpus_tool.load_raw_items(week=week, category=category):
                out[item.id] = item
        return out

    # ══════════════════════════════════════════
    # 묶음 정리 — 출처 편중 상한 (docs 9절)
    # ══════════════════════════════════════════

    @staticmethod
    def _source_of(j: Judgement, raw_map: dict[str, RawItem]) -> str:
        item = raw_map.get(j.raw_item_id)
        if item is None:
            # 원문을 못 찾으면 편중을 따질 수 없다. 저 혼자인 출처로 둔다.
            return f"?{j.raw_item_id}"
        return item.source_name or item.source_kind.value

    def _cap_source_bias(
        self, group_items: list[Judgement], raw_map: dict[str, RawItem]
    ) -> list[Judgement]:
        """
        한 출처가 묶음의 절반을 넘지 않게 잘라낸다.

        ★ 잘라내면 묶음이 작아지고 상한도 같이 내려간다. 그래서 한 번이 아니라
          더 잘라낼 게 없을 때까지 돈다. 한 출처가 압도적이면 묶음이 통째로
          MIN_GROUP_SIZE 밑으로 내려가 승격 대기로 간다 — 의도한 결과다.
          "한 카페에서만 나온 이야기"는 아직 세상의 문제가 아니다.
        """
        kept = list(group_items)
        while len(kept) > 1:
            limit = max(len(kept) // 2, 1)
            counts = Counter(self._source_of(j, raw_map) for j in kept)
            over = {s for s, c in counts.items() if c > limit}
            if not over:
                break

            used: Counter = Counter()
            trimmed: list[Judgement] = []
            for j in kept:
                source = self._source_of(j, raw_map)
                if source in over and used[source] >= limit:
                    continue
                used[source] += 1
                trimmed.append(j)

            if len(trimmed) == len(kept):  # 더 줄지 않는다
                break
            kept = trimmed
        return kept

    # ══════════════════════════════════════════
    # 묶음 → 후보
    # ══════════════════════════════════════════

    @staticmethod
    def candidate_id(raw_item_ids: list[str]) -> str:
        """
        ★ 구성원 id 를 정렬해 해싱한다.

        다음 주에 같은 묶음이 나오면 같은 id 가 나와야 ③이 "새 문제"와
        "기존 문제 갱신"을 구분할 수 있다. 순서·주차에 흔들리면 안 된다.
        """
        body = "|".join(sorted(raw_item_ids))
        digest = sha256(body.encode("utf-8")).hexdigest()[:_CANDIDATE_ID_LEN]
        return f"{CANDIDATE_ID_PREFIX}{digest}"

    def _candidate(
        self, kept: list[Judgement], category: Category
    ) -> ProblemCandidate:
        """★ 숫자 필드를 넣지 않는다. 몇 건인지는 raw_item_ids 를 세면 된다."""
        raw_item_ids = [j.raw_item_id for j in kept]
        return ProblemCandidate(
            id=self.candidate_id(raw_item_ids),
            raw_item_ids=raw_item_ids,
            pain_summaries=[j.pain_summary for j in kept if j.pain_summary],
            theme_hint=cluster_tool.name_group(kept),
            category=category,
        )

    # ══════════════════════════════════════════
    # 매니페스트 — 단계별 잔존 건수
    # ══════════════════════════════════════════

    @staticmethod
    def _write_manifest(category: Category, stats: dict) -> None:
        """
        ★ 숫자는 여기 남는다. 실행 결과가 만든 숫자다.

        write_manifest 는 주차 파일을 통째로 덮어쓴다. 다른 카테고리·다른
        에이전트가 적어 둔 것을 지우지 않으려고 읽어서 합친 뒤 쓴다.
        """
        week = corpus_tool.week_key()
        payload = dict(corpus_tool.read_manifest(week) or {})
        payload.pop("written_at", None)  # 이번 실행 시각으로 다시 찍는다
        payload["week"] = week

        by_category = dict(payload.get("해석기") or {})
        by_category[category.value] = stats
        payload["해석기"] = by_category

        corpus_tool.write_manifest(payload)
