"""
전체 흐름을 한 번에 돌려보는 확인용 스크립트.

에이전트를 구현하고 나서 이걸 돌리면
전체 안에서 제대로 붙었는지 바로 알 수 있다.

실행:  cd Backend && python scripts/run_pipeline.py

※ 지금은 뼈대라 NotImplementedError 가 납니다. 정상입니다.
  각자 자기 에이전트를 구현하면 그 단계부터 통과합니다.
"""

import sys
from pathlib import Path

# Windows 콘솔 한글 깨짐 방지
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.graph.pipeline import run_collect_pipeline
from app.schemas.models import Category, ProgressEvent


def show(e: ProgressEvent) -> None:
    mark = "완료" if e.done else "진행"
    print(f"   [{e.index + 1}/{e.total}] {e.step} … {mark}")


def main() -> None:
    print("\n유레카 파이프라인 확인\n")
    try:
        problems = run_collect_pipeline(Category.PRODUCTIVITY, on_progress=show)
        print(f"\n게시된 문제: {len(problems)}개")
        for p in problems:
            print(f"  · {p.title}")
            print(f"    사례 {p.case_count}건 · 출처 {p.source_count}곳  ← DB가 센 값")
    except NotImplementedError:
        print("아직 구현되지 않았습니다. (뼈대 상태에서는 정상입니다)")


if __name__ == "__main__":
    main()
