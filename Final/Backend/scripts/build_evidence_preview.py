"""
근거 조립기(EvidenceAgent)의 산출물을 미리보기용 JSON으로 찍는 확인용 스크립트.

★ 읽기 전용이다. 아무것도 저장하지 않는다 — corpus_tool.load_candidates() 로
  이미 승격된 후보(디스크에 남아 있는 것)만 읽어서 EvidenceAgent 에 넣는다.
  수집·해석을 다시 돌리지 않는다(그건 run_pipeline.py 나 run_collect_only.py 몫).

★ 코퍼스가 비어 있어도(지금 실데이터 0건) 예외 없이 빈 목록을 출력해야 한다.
  프론트가 목데이터 형식을 이 출력으로 확정하기 때문에, 빈 상태에서도 스키마가
  깨지지 않는 것 자체가 이 스크립트의 존재 이유다.

실행:
    python scripts/build_evidence_preview.py
    python scripts/build_evidence_preview.py --category IT/생산성
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Windows 콘솔 한글 깨짐 방지
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agents.evidence_agent import EvidenceAgent, EvidenceInput  # noqa: E402
from app.schemas.models import Category, ProgressEvent  # noqa: E402
from app.tools import corpus_tool  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="build_evidence_preview.py",
        description="승격된 후보를 읽어 근거 묶음(EvidenceBundle) JSON을 stdout에 찍는다 (읽기 전용)",
    )
    p.add_argument(
        "--category",
        default=None,
        choices=[c.value for c in Category],
        help="이 카테고리만 본다 (기본: 전체 카테고리)",
    )
    p.add_argument(
        "--week",
        default=None,
        help="이 주차만 본다 (기본: 저장된 전 주차)",
    )
    return p


def show(e: ProgressEvent) -> None:
    """진행 상태는 stderr 로 — stdout 은 JSON 전용으로 남겨 둔다."""
    mark = "완료" if e.done else "진행"
    print(f"   [{e.index + 1}/{e.total}] {e.step} … {mark}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    category = Category(args.category) if args.category else None

    candidates = corpus_tool.load_candidates(week=args.week, category=category)
    print(
        f"승격된 후보 {len(candidates)}개를 읽었다"
        f"{' (카테고리: ' + category.value + ')' if category else ''}",
        file=sys.stderr,
    )

    bundles = EvidenceAgent(on_progress=show).run(EvidenceInput(candidates=candidates))

    print(
        json.dumps(
            [b.model_dump() for b in bundles],
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
