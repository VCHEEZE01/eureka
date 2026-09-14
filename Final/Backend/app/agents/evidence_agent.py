"""
②′ 근거 조립기 (EvidenceAgent)

역할  : 승격된 문제 후보의 원문·판정을 모아 근거 묶음으로 만든다
입력  : 문제 후보(ProblemCandidate) 목록
출력  : 근거 묶음(EvidenceBundle) 목록

────────────────────────────────────────────────
②(해석기)와 ③(문제정의 생성기) 사이에 낀다
────────────────────────────────────────────────
  문장 쓰기(title·description·complexity_note 등)는 ③의 몫이고,
  근거 조립·신호 집계·게시 기준 판정은 이 에이전트의 몫이다.
  "AI는 라벨만, 숫자는 DB가"라는 원칙을 파일 경계로 강제하기 위해 쪼갰다.

★★ 이 파일은 llm_tool 을 영원히 import하지 않는다.
  LLM을 안 부르므로 --no-llm 에서도, ③이 스텁인 채로도 근거 페이지 데이터가
  완성된다.

근거 선별 규칙 (docs/DATA_COLLECTION.md 6절)
  1. 출처(source_name)별로 그룹핑한다
  2. 출처가 많은 순이 아니라 돌아가며 하나씩 뽑는다 (라운드로빈)
     → 한 출처가 근거 목록을 독식하지 못한다
  3. 같은 출처 안에서는 severity 높음 → pain_summary 있음 → id 순
  4. settings.EVIDENCE_SHOW_MAX 까지만 뽑는다
  5. is_pain=True 인 판정이 있는 원문만 후보로 삼는다

규칙
  · settings 는 run() 안에서 읽는다 — 모듈 레벨 상수로 캡처하지 않는다
  · 후보마다 corpus_tool.load_*_by_ids 를 부르지 않는다 — 전체 id 를 합쳐 한 번만
"""

from __future__ import annotations

from urllib.parse import urlsplit

import logging
from collections import Counter, defaultdict
from typing import Optional

from pydantic import BaseModel, Field

from app.agents.base import Agent
from app.config.settings import settings
from app.schemas.models import (
    Category,
    Evidence,
    EvidenceBundle,
    Judgement,
    ProblemCandidate,
    ProblemSignals,
    RawItem,
)
from app.tools import aggregate_tool, corpus_tool, text_tool

logger = logging.getLogger(__name__)

# severity 가 없거나 모르는 값이면 맨 뒤로 보낸다.
_SEVERITY_RANK = {"높음": 0, "중간": 1, "낮음": 2}


def _public_source_url(url: str) -> Optional[str]:
    try:
        parsed = urlsplit(url)
        if parsed.scheme in {"http", "https"} and parsed.hostname and not parsed.username:
            return url
    except ValueError:
        pass
    return None


class EvidenceInput(BaseModel):
    """
    ★ weeks=0 이면 settings.EVIDENCE_LOOKBACK_WEEKS 를 쓴다.
      settings 는 run() 안에서 읽는다 — 여기 default 로 캡처하지 않는다.
    """

    candidates: list[ProblemCandidate]
    weeks: int = Field(default=0, description="원문을 되짚을 주차 창. 0이면 settings 기본값")


class EvidenceAgent(Agent[EvidenceInput, list[EvidenceBundle]]):
    name = "근거 조립기"
    steps = ["근거 모으기", "신호 세기", "게시 기준 확인"]

    # ══════════════════════════════════════════
    # 실행
    # ══════════════════════════════════════════

    def run(self, data: EvidenceInput) -> list[EvidenceBundle]:
        weeks = data.weeks if data.weeks > 0 else int(settings.EVIDENCE_LOOKBACK_WEEKS)

        # ── 1단계: 근거 모으기 ────────────────
        self.report(0)
        all_ids = {rid for c in data.candidates for rid in c.raw_item_ids}
        raw_map = corpus_tool.load_raw_items_by_ids(all_ids, weeks=weeks) if all_ids else {}
        judgement_map = (
            corpus_tool.load_judgements_by_ids(all_ids, weeks=weeks) if all_ids else {}
        )
        self.report(0, done=True)

        # ── 2단계: 신호 세기 ──────────────────
        self.report(1)
        found_items: dict[str, list[RawItem]] = {}
        found_judgements: dict[str, list[Judgement]] = {}
        signals_by_candidate: dict[str, ProblemSignals] = {}

        for c in data.candidates:
            items = [raw_map[rid] for rid in c.raw_item_ids if rid in raw_map]
            judgements = [judgement_map[rid] for rid in c.raw_item_ids if rid in judgement_map]
            missing = len(c.raw_item_ids) - len(items)
            if missing:
                logger.info("후보 %s: 원문 %d건을 못 찾아 카운트에서 뺀다", c.id, missing)

            found_items[c.id] = items
            found_judgements[c.id] = judgements
            signals_by_candidate[c.id] = aggregate_tool.signals_for(items, judgements)
        self.report(1, done=True)

        # ── 3단계: 게시 기준 확인 + 근거 선별 ──
        self.report(2)
        by_category: dict[Category, dict] = {}
        bundles: list[EvidenceBundle] = []

        for c in data.candidates:
            items = found_items[c.id]
            judgement_by_raw_id = {j.raw_item_id: j for j in found_judgements[c.id]}
            case_count = len(items)

            evidence = self._select_evidence(items, judgement_by_raw_id)
            signals = signals_by_candidate[c.id]
            gate = aggregate_tool.publish_gate(signals, case_count, len(evidence))

            bundles.append(
                EvidenceBundle(
                    candidate_id=c.id,
                    category=c.category,
                    evidence=evidence,
                    signals=signals,
                    gate=gate,
                )
            )

            stats = by_category.setdefault(
                c.category, {"후보_입력": 0, "게시가능": 0, "게시미달": 0, "미달사유": Counter()}
            )
            stats["후보_입력"] += 1
            if gate.passed:
                stats["게시가능"] += 1
            else:
                stats["게시미달"] += 1
                if gate.reason:
                    stats["미달사유"][gate.reason] += 1

        self._write_manifest(by_category)
        self.report(2, done=True)
        return bundles

    # ══════════════════════════════════════════
    # 근거 선별 — 출처 라운드로빈 (docs/DATA_COLLECTION.md 6절)
    # ══════════════════════════════════════════

    @staticmethod
    def _select_evidence(
        items: list[RawItem], judgement_by_raw_id: dict[str, Judgement]
    ) -> list[Evidence]:
        """
        is_pain=True 인 판정이 있는 원문만 후보로 삼아 출처별로 돌아가며 뽑는다.

        ★ 많은 출처 순이 아니라 라운드로빈이다 — 한 출처가 목록을 독식하지 못한다.
          같은 출처 안에서는 severity 높음 → pain_summary 있음 → id 순으로 줄 세운다.
        """
        by_source: dict[str, list[tuple[RawItem, Judgement]]] = defaultdict(list)
        for item in items:
            j = judgement_by_raw_id.get(item.id)
            if j is None or not j.is_pain:
                continue
            by_source[item.source_name].append((item, j))

        def sort_key(pair: tuple[RawItem, Judgement]) -> tuple:
            item, j = pair
            return (
                _SEVERITY_RANK.get(j.severity, len(_SEVERITY_RANK)),
                0 if j.pain_summary else 1,
                item.id,
            )

        # 출처 이름 사전순으로 큐를 고정한다 — 같은 입력이면 같은 결과가 나와야 한다.
        queues = [sorted(pairs, key=sort_key) for _, pairs in sorted(by_source.items())]

        max_show = max(int(settings.EVIDENCE_SHOW_MAX), 0)
        evidence: list[Evidence] = []
        while len(evidence) < max_show and any(queues):
            for q in queues:
                if not q:
                    continue
                item, j = q.pop(0)
                evidence.append(
                    Evidence(
                        raw_item_id=item.id,
                        summary=j.pain_summary or "",
                        excerpt=text_tool.pick_excerpt(item),
                        source_name=item.source_name,
                        source_url=_public_source_url(item.url),
                        source_kind=item.source_kind,
                        posted_at=item.posted_at,
                        severity=j.severity,
                        has_payment_signal=j.has_payment_signal,
                        has_need_signal=j.has_need_signal,
                    )
                )
                if len(evidence) >= max_show:
                    break
        return evidence

    # ══════════════════════════════════════════
    # 매니페스트 — 카테고리별 게시 가능/미달
    # ══════════════════════════════════════════

    @staticmethod
    def _write_manifest(by_category: dict[Category, dict]) -> None:
        """
        interpreter_agent._write_manifest 와 같은 패턴 — 읽어서 합친 뒤 쓴다.

        후보가 하나도 없으면(빈 candidates) 아무것도 쓰지 않는다. 빈 코퍼스에서
        build_evidence_preview.py 를 돌려도 매니페스트 파일이 생기지 않아야 한다.
        """
        if not by_category:
            return

        week = corpus_tool.week_key()
        payload = dict(corpus_tool.read_manifest(week) or {})
        payload.pop("written_at", None)
        payload["week"] = week

        existing = dict(payload.get("근거조립") or {})
        for category, stats in by_category.items():
            existing[category.value] = {
                "후보_입력": stats["후보_입력"],
                "게시가능": stats["게시가능"],
                "게시미달": stats["게시미달"],
                "미달사유": dict(stats["미달사유"]),
            }
        payload["근거조립"] = existing
        corpus_tool.write_manifest(payload)
