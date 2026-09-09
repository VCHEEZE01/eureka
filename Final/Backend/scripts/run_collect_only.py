"""
① 수집 → ② 해석기만 이어 붙여 돌려 보는 확인용 스크립트.

graph/pipeline.py 의 run_collect_pipeline() 은 ③④가 아직 비어 있어 통째로
NotImplementedError 다. 그래서 ①②까지의 배선을 눈으로 확인할 통로가 따로 필요하다.
③④가 채워지면 이 스크립트는 지워도 된다.

실행:
    python scripts/run_collect_only.py --category IT/생산성 --sources 블로그 --keywords 3 --no-llm
    python scripts/run_collect_only.py --category IT/생산성 --yes

★ --yes 를 안 붙이면 예상 API 호출 수와 LLM 투입 예상 건수만 보여주고 멈춘다.
  키를 넣은 채로 무심코 돌려서 하루 쿼터를 태우는 사고를 막기 위한 것이다.

★ 키가 없으면 무엇이 비었는지 알려 주고 조용히 끝낸다. 스택트레이스를 뱉지 않는다.
"""

from __future__ import annotations

import argparse
import sys
import unicodedata
from collections import Counter
from pathlib import Path

# Windows 콘솔 한글 깨짐 방지
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agents.collector_agent import CollectInput, CollectorAgent  # noqa: E402
from app.agents.interpreter_agent import InterpretInput, InterpreterAgent  # noqa: E402
from app.config.dictionaries import (  # noqa: E402
    DOMAIN_KEYWORDS,
    PAIN_SIGNALS_TIER1,
)
from app.config.settings import settings  # noqa: E402
from app.schemas.models import (  # noqa: E402
    Category,
    ProblemCandidate,
    ProgressEvent,
    RawItem,
    SourceKind,
)
from app.tools import corpus_tool, llm_tool  # noqa: E402

TOP_N = 10  # 마지막에 보여 줄 후보 개수


# ══════════════════════════════════════════════
# 인자
# ══════════════════════════════════════════════


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="run_collect_only.py",
        description="① 수집 → ② 해석기까지만 돌려 본다 (③④는 건너뛴다)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--category",
        required=True,
        choices=[c.value for c in Category],
        help="수집할 카테고리 (필수)",
    )
    p.add_argument(
        "--sources",
        nargs="+",
        default=[SourceKind.BLOG.value],
        choices=[s.value for s in SourceKind],
        help="수집할 출처. 여러 개 줄 수 있다 (기본: 블로그)",
    )
    p.add_argument(
        "--keywords",
        type=int,
        default=None,
        metavar="N",
        help="도메인 키워드를 앞에서 N개만 쓴다 (기본: 사전 전체)",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=200,
        metavar="N",
        help="해석기로 넘길 원문 상한 (기본: 200)",
    )
    p.add_argument(
        "--no-llm",
        action="store_true",
        help="LLM 판별을 건너뛰고 규칙만으로 판정한다",
    )
    p.add_argument(
        "--yes",
        action="store_true",
        help="예상치를 확인했다. 실제로 실행한다",
    )
    return p


# ══════════════════════════════════════════════
# 실행 전 안내 — 비용 사고 방지
# ══════════════════════════════════════════════


def show_plan(args: argparse.Namespace, category: Category, sources: list[SourceKind]) -> None:
    """무엇을 얼마나 부를 참인지 먼저 보여 준다. 전부 세어서 만든 수치다."""
    keywords = list(DOMAIN_KEYWORDS.get(category, []))
    if args.keywords is not None:
        keywords = keywords[: max(args.keywords, 0)]

    queries = len(keywords) * len(PAIN_SIGNALS_TIER1) * len(sources)
    max_pages = max(int(settings.COLLECT_MAX_PAGES), 1)
    llm_items = 0 if args.no_llm else min(max(args.limit, 0), int(settings.MAX_LLM_ITEMS))

    print("실행 계획")
    print(f"  카테고리        {category.value}")
    print(f"  출처            {' · '.join(s.value for s in sources)}")
    print(f"  도메인 키워드   {len(keywords)}개")
    print(f"  불편 표현       {len(PAIN_SIGNALS_TIER1)}개 (Tier1)")
    print(f"  검색어          {queries}개  (키워드 × 표현 × 출처)")
    print(f"  예상 API 호출   최대 {queries * max_pages}회  (쿼리당 {max_pages}페이지)")
    if args.no_llm:
        print("  LLM 투입        0건  (--no-llm)")
    else:
        print(
            f"  LLM 투입        최대 {llm_items}건 "
            f"→ 최대 {llm_tool.judge_call_count(llm_items)}회 호출 "
            f"(배치 {settings.JUDGE_BATCH_SIZE}건)"
        )
        print("                  ※ 규칙 선필터가 먼저 걸러내므로 실제로는 더 적다")
    print()


def warn_missing_keys() -> bool:
    """키가 비었으면 무엇이 비었는지 알려 준다. True 면 실행하지 않는다."""
    missing = settings.missing_keys()
    if not missing:
        return False

    print("실행할 수 없다 — .env 에 다음 값이 비어 있다:")
    for key in missing:
        print(f"  · {key}")
    print()
    print("  .env.example 을 복사해 값을 채운 뒤 다시 실행해라.")
    print("  키 없이 배선만 확인하려면 tests/ 를 돌리는 편이 빠르다:")
    print("      .venv/bin/python -m pytest tests/ -q")
    return True


# ══════════════════════════════════════════════
# 진행 상태 — scripts/run_pipeline.py 와 같은 형식
# ══════════════════════════════════════════════


def show(e: ProgressEvent) -> None:
    mark = "완료" if e.done else "진행"
    print(f"   [{e.index + 1}/{e.total}] {e.step} … {mark}")


# ══════════════════════════════════════════════
# 결과 보고
# ══════════════════════════════════════════════


def pad(label: str, width: int = 18) -> str:
    """한글은 터미널에서 두 칸을 먹는다. 글자 수가 아니라 칸 수로 맞춘다."""
    cells = sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in label)
    return label + " " * max(width - cells, 1)


def show_funnel(category: Category, collected: int) -> None:
    """단계별 잔존 건수. 매니페스트에 남은 값을 그대로 읽어 온다."""
    print("\n단계별 잔존 건수")
    print(f"  {pad('수집')}{collected:>6}")

    manifest = corpus_tool.read_manifest() or {}
    stats = (manifest.get("해석기") or {}).get(category.value)
    if not stats:
        print("  (해석기 매니페스트가 없다 — 입력이 없었거나 저장에 실패했다)")
        return

    for label in (
        "입력",
        "규칙_통과",
        "규칙_보류",
        "규칙_탈락",
        "LLM_투입",
        "LLM_호출",
        "LLM_이월",
        "불편_판정",
        "묶기_대상",
        "지난주차_합류",
        "묶음",
        "출처편중_잘라냄",
        "후보",
        "승격대기",
    ):
        if label in stats:
            print(f"  {pad(label.replace('_', ' '))}{stats[label]:>6}")

    reasons = stats.get("탈락_사유") or {}
    if reasons:
        print("  탈락 사유")
        for reason, count in sorted(reasons.items(), key=lambda kv: (-kv[1], kv[0])):
            print(f"    · {reason}: {count}")


def source_mix(candidate: ProblemCandidate, raw_map: dict[str, RawItem]) -> str:
    """이 묶음이 어느 출처에서 왔는가. 근거를 못 찾은 건은 그렇다고 적는다."""
    counts = Counter(
        raw_map[rid].source_name if rid in raw_map else "출처 미상"
        for rid in candidate.raw_item_ids
    )
    return " · ".join(
        f"{name} {count}" for name, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    )


def show_candidates(
    candidates: list[ProblemCandidate], raw_map: dict[str, RawItem]
) -> None:
    print(f"\n문제 후보 {len(candidates)}개", end="")
    print(f" (상위 {min(len(candidates), TOP_N)}개)" if candidates else "")

    for i, c in enumerate(candidates[:TOP_N], start=1):
        print(f"\n  {i}. {c.theme_hint or '(주제 힌트 없음)'}   묶음 {len(c.raw_item_ids)}건")
        print(f"     출처  {source_mix(c, raw_map)}")
        print(f"     id    {c.id}")
        for summary in c.pain_summaries[:3]:
            print(f"     · {summary}")

    waiting = corpus_tool.load_pending_candidates()
    if waiting:
        print(
            f"\n  ※ 5건에 못 미쳐 승격 대기로 쌓인 묶음 {len(waiting)}개. "
            "다음 주에 사례가 더 모이면 자동으로 올라간다."
        )


# ══════════════════════════════════════════════
# 본체
# ══════════════════════════════════════════════


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    category = Category(args.category)
    sources = [SourceKind(s) for s in dict.fromkeys(args.sources)]

    print("\n유레카 ①수집 → ②해석 확인 (③④는 건너뛴다)\n")
    show_plan(args, category, sources)

    if warn_missing_keys():
        return 0

    if not args.yes:
        print("여기까지가 예상치다. 실제로 돌리려면 --yes 를 붙여라.")
        return 0

    print("① 수집 에이전트")
    collected = CollectorAgent(on_progress=show).run(
        CollectInput(
            category=category,
            source_kinds=sources,
            limit=args.limit,
            keyword_limit=args.keywords,
        )
    )
    print(f"   → {len(collected)}건\n")

    print("② 해석기")
    candidates = InterpreterAgent(on_progress=show).run(
        InterpretInput(
            items=collected,
            category=category,
            use_llm=not args.no_llm,
        )
    )

    show_funnel(category, len(collected))
    show_candidates(candidates, {i.id: i for i in collected})
    print(f"\n원문·판정·매니페스트는 {corpus_tool.corpus_root()} 아래에 남았다.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n중단했다. 여기까지 저장된 것은 그대로 남아 있다.")
        raise SystemExit(130)
