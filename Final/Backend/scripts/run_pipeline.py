"""
수집 → 해석 → 근거 조립까지 돌려보는 확인용 스크립트.

에이전트를 구현하고 나서 이걸 돌리면
전체 안에서 제대로 붙었는지 바로 알 수 있다.

실행:  cd Backend && python scripts/run_pipeline.py

※ 이 스크립트는 ①→②→②′ 진단용으로 유지한다.
  ③ 문제정의 상세 생성은 scripts/build_problems.py로 저장 후보에서 이어서 실행한다.
  실데이터가 0건이면(.env 미설정) 빈 목록으로 끝난다. 그것도 정상이다.
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
        # 수집·근거 조립 진단 경로. 서술 생성은 build_problems.py에서 실행한다.
        bundles = run_collect_pipeline(Category.IT_PRODUCTIVITY, on_progress=show)
        print(f"\n근거 묶음: {len(bundles)}개")
        for b in bundles:
            mark = "게시 가능" if b.gate.passed else f"게시 미달 ({b.gate.reason})"
            print(f"  · [{b.category.value}] {b.candidate_id} — {mark}")
            print(f"    근거 {len(b.evidence)}건 · 출처 {len(b.signals.source_name_counts)}곳  ← DB가 센 값")
    except NotImplementedError:
        print("아직 구현되지 않았습니다. (뼈대 상태에서는 정상입니다)")


if __name__ == "__main__":
    main()
