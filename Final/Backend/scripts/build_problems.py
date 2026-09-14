"""저장된 후보에서 문제 상세 JSON을 만든다. 재수집하지 않는다.

기본은 실행 계획만 표시한다. --execute로 실제 Gemini 생성·검수를 실행한다.
--review --include-pending은 게시 기준 미달 후보를 검토용으로만 내보낸다.
리뷰 자료는 공개 문제 저장소에 저장하지 않는다.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config.settings import settings
from app.graph.pipeline import build_problem_outputs
from app.schemas.models import Category
from app.tools import corpus_tool


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--category", choices=[c.value for c in Category])
    parser.add_argument("--corpus-dir", type=Path)
    parser.add_argument("--candidate-id", action="append", default=[])
    parser.add_argument("--max-candidates", type=int, default=10)
    parser.add_argument("--review", action="store_true")
    parser.add_argument("--include-pending", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.max_candidates < 1:
        parser.error("--max-candidates는 양수여야 합니다")
    if args.include_pending and not args.review:
        parser.error("승격 대기 후보는 --review 검토 모드에서만 사용할 수 있습니다")
    if args.corpus_dir:
        settings.CORPUS_DIR = args.corpus_dir.resolve()
    category = Category(args.category) if args.category else None
    candidates = corpus_tool.load_candidates(category=category)
    if args.include_pending:
        candidates += [c for c in corpus_tool.load_pending_candidates()
                       if category is None or c.category == category]
    candidates = list({c.id: c for c in candidates}.values())
    if args.candidate_id:
        known = {c.id for c in candidates}
        if set(args.candidate_id) - known:
            parser.error("요청한 후보를 현재 코퍼스에서 찾을 수 없습니다")
        candidates = [c for c in candidates if c.id in args.candidate_id]
    candidates = sorted(candidates, key=lambda c: (-len(c.raw_item_ids), c.id))[:args.max_candidates]
    print(f"후보 {len(candidates)}개 · {'검토 전용' if args.review else '검수 통과 시 저장'}", flush=True)
    print("생성·검수 각 한 배치 호출(오류·JSON 재시도 별도), 게시 미달은 기본 생성 생략", flush=True)
    if not args.execute:
        print("실행하려면 --execute를 지정하세요")
        return 0
    if settings.LLM_DRY_RUN or settings.LLM_PROVIDER == "echo":
        parser.error("실제 문제 생성에는 LLM_DRY_RUN=false와 실제 LLM provider가 필요합니다")
    if args.output.exists() or args.output.with_suffix(".report.json").exists():
        parser.error("기존 결과를 보존합니다. 새 --output 파일명을 사용하세요")
    outputs = build_problem_outputs(candidates, persist=not args.review, allow_hold_draft=args.review)
    problems = [o.problem for o in outputs if o.problem is not None
                and (args.review or o.review.decision == "publish")]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps([p.model_dump(mode="json") for p in problems],
                                     ensure_ascii=False, indent=2), encoding="utf-8")
    report = {"mode": "review" if args.review else "published", "model": settings.judge_model,
              "corpus_dir": str(settings.CORPUS_DIR), "candidate_ids": [c.id for c in candidates],
              "results": [o.model_dump(mode="json") for o in outputs]}
    args.output.with_suffix(".report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for c, output in zip(candidates, outputs):
        print(f"{c.id}: {output.review.decision} · {output.review.reason}", flush=True)
    print(f"상세 데이터 {len(problems)}개 → {args.output}", flush=True)
    return 0 if len(problems) or not candidates or all(o.review.decision in {"hold", "merge"} for o in outputs) else 1


if __name__ == "__main__":
    raise SystemExit(main())
