"""
④ 아이디어 생성기 프롬프트.

두 가지를 만든다.
  1. build_idea_prompt()   — LLM이 아이디어 N개를 뽑게 하는 프롬프트
  2. build_period_prompt() — 아이디어 하나 + 기간(하루/일주일/한달)에서
     바이브코딩 프롬프트 "완성본"을 만든다. 이건 LLM을 다시 부르지
     않는다 — Frontend/v1-trend-incubator.html:5027-5115 의
     buildPromptForPeriod()가 이미 핸드오프 문서 규칙(시간 진행 표현
     금지 등)을 만족하는 검증된 결정적 템플릿이라 그대로 파이썬으로
     옮긴 것이다. 두 파일이 갈라지지 않게 여기를 고치면 그쪽도 고칠 것.

★ 플레이스홀더 치환은 str.replace()로 한다. str.format()은 프롬프트
  안의 JSON 예시 중괄호 때문에 깨진다
  (docs/IDEA_GENERATION_HANDOFF.md:68).
"""

from app.ideas.axes import ResolvedAxis
from app.prompts.common_prompts import with_rules
from app.schemas.idea_models import IdeaSpec

# 이 값은 아이디어 캐시 키에 들어간다(app/ideas/cache.py) — 올리면
# 디스크에 남은 캐시가 전부 무효가 된다. 프롬프트 문구나 아이디어의
# 구조가 바뀌어 옛 캐시를 그대로 쓰면 안 될 때만 올린다.
#   1 → 2 (2026-09-19): "웹앱" 문구 정정 + 추천 AI가 기간별 목록으로 바뀜.
PROMPT_VERSION = 2

# ── IA 작성 규칙 (docs/IDEA_GENERATION_HANDOFF.md 원문) ───────────

IA_RULES_TEMPLATE = """## 서비스 정보구조(IA) 작성 규칙

아이디어마다 서비스의 화면 구조를 depth1(화면·섹션) → depth2(그 안의 기능)
2단 트리로 작성하라. 이 트리는 가로로 나란히 그려지므로 아래 크기를 지켜라.

- depth1은 __IA_MIN__~__IA_MAX__개로 하라. 벗어나지 마라 — 가로 폭을 벗어난다.
- depth1 이름은 명사형으로 10자 내외. 예: "메인 홈 (지도 & 레이더)"
- 각 depth1 아래 depth2는 1~3개로 하라.
- 서로 다른 depth1끼리 depth2 개수 차이를 2개 이상 벌리지 마라
  (하나는 1개, 다른 하나는 4개처럼 극단적으로 불균형하면 화면에서
  카드 높이가 비대칭으로 어색해진다).
- depth2의 title은 8자 내외 기능명, desc는 30자 내외 한 문장으로
  "무엇을 보여주는지/무엇을 하는지"만 적어라. 근거 없는 수치를
  넣지 마라 (예: "월 10만명이 이용" 금지).
- depth1의 나열 순서는 사용자가 실제로 마주치는 순서(온보딩 → 핵심
  기능 → 저장/공유)로 하라. 이 순서가 그대로 왼쪽에서 오른쪽 방향의
  플로우로 그려진다.

[이 플랫폼의 IA 제약]
__PLATFORM_IA__

[이 유형의 IA 제약]
__TYPE_IA__"""


IDEA_PROMPT_TEMPLATE = """너는 트렌드 키워드 하나에서 바이브코딩으로 만들 수 있는 서비스
아이디어를 뽑는 기획자다.

[트렌드 키워드]
- 이름: __KEYWORD__
- 분야: __CATEGORY__
- 요약: __SUMMARY__
- 왜 뜨는가: __WHY_TRENDING__
- 주 소비층: __KW_TARGET__
- 지속성 전망: __SUSTAINABILITY__

[이번 조합의 성격 — 가장 중요한 제약]
__COMBO_NOTE__

[플랫폼: __PLATFORM_LABEL__]
__PLATFORM_FORM__
MVP 방향: __PLATFORM_MVP__
타깃 서술: __PLATFORM_TARGET__

[유형: __TYPE_LABEL__]
__TYPE_ANGLE__
MVP 방향: __TYPE_MVP__
타깃 서술: __TYPE_TARGET__
이름 짓기: __TYPE_NAMING__
디자인 톤: __TYPE_TONE__

__IA_RULES__
__EXCLUDE_BLOCK__
[출력 형식]
아래 JSON 배열 하나만 출력하라. 설명, 인사말, 코드블록 표시(```)를
붙이지 마라. 서로 다른 __COUNT__개의 아이디어를, 접근 방식이 겹치지
않게 만들어라. stack과 ai_tools 필드는 비워서 보내라 — 시스템이 채운다.

[
  {
    "name": "서비스 정식 이름",
    "short_name": "짧은 이름 (20자 이내)",
    "approach": "접근 방식 한 줄 (예: 게이미피케이션 & 수집 도감)",
    "slogan": "한 줄 컨셉",
    "target": "서비스 타겟 서술",
    "problem": "해결하는 문제",
    "solution": "해결 방식",
    "architecture": "전체 구조 한 줄 요약",
    "diff": "차별점",
    "mvp_features": ["핵심 기능 3~5개"],
    "future_features": ["확장 기능 1~3개"],
    "ia": [
      { "depth1": "화면 이름",
        "depth2": [ { "title": "기능명", "desc": "무엇을 하는지 한 문장" } ] }
    ]
  }
]"""


# 새로고침이 "이미 봤던 것과 똑같은 3개"를 다시 뱉는 문제의 처방.
# 온도(0.9)만으로는 부족하다 — 프롬프트가 같으면 모델의 최빈 답이
# 재발한다(레이더/도감류가 반복 등장). 이미 보여준 아이디어를 제외
# 목록으로 못박아 접근 각도 자체를 바꾸도록 강제한다.
EXCLUDE_TEMPLATE = """
[이미 보여준 아이디어 — 절대 반복 금지]
아래는 같은 키워드·같은 조합으로 이미 사용자에게 보여준 아이디어다.
이름·접근 방식·핵심 기능이 겹치면 안 된다. 같은 아이디어를 다르게
표현한 것도 안 된다. 접근 각도 자체를 바꿔라.
__EXCLUDE_LIST__"""


def _format_exclude_block(exclude: list[dict] | None) -> str:
    if not exclude:
        return ""
    lines = "\n".join(
        f"- {item.get('name', '')} ({item.get('approach', '')}) — {item.get('slogan', '')}"
        for item in exclude
    )
    return EXCLUDE_TEMPLATE.replace("__EXCLUDE_LIST__", lines)


def build_idea_prompt(
    kw: dict, axis: ResolvedAxis, count: int, exclude: list[dict] | None = None
) -> str:
    p, t = axis.platform_spec, axis.type_spec

    ia_rules = (
        IA_RULES_TEMPLATE
        .replace("__IA_MIN__", str(p["ia_shape"]["depth1_min"]))
        .replace("__IA_MAX__", str(p["ia_shape"]["depth1_max"]))
        .replace("__PLATFORM_IA__", p["ia_directive"])
        .replace("__TYPE_IA__", t["ia_directive"])
    )

    prompt = (
        IDEA_PROMPT_TEMPLATE
        .replace("__KEYWORD__", kw.get("name", ""))
        .replace("__CATEGORY__", kw.get("category", ""))
        .replace("__SUMMARY__", kw.get("summary", ""))
        .replace("__WHY_TRENDING__", (kw.get("analysis") or {}).get("why_trending", ""))
        .replace("__KW_TARGET__", (kw.get("analysis") or {}).get("target", ""))
        .replace("__SUSTAINABILITY__", (kw.get("analysis") or {}).get("sustainability", ""))
        .replace("__COMBO_NOTE__", axis.combo_note)
        .replace("__PLATFORM_LABEL__", p["label"])
        .replace("__PLATFORM_FORM__", p["form_directive"])
        .replace("__PLATFORM_MVP__", p["mvp_directive"])
        .replace("__PLATFORM_TARGET__", p["target_directive"])
        .replace("__TYPE_LABEL__", t["label"])
        .replace("__TYPE_ANGLE__", t["angle_directive"])
        .replace("__TYPE_MVP__", t["mvp_directive"])
        .replace("__TYPE_TARGET__", t["target_directive"])
        .replace("__TYPE_NAMING__", t["naming_hint"])
        .replace("__TYPE_TONE__", t["tone"])
        .replace("__IA_RULES__", ia_rules)
        .replace("__EXCLUDE_BLOCK__", _format_exclude_block(exclude))
        .replace("__COUNT__", str(count))
    )
    return with_rules(prompt)


# ── 기간별 바이브코딩 프롬프트 (프론트 buildPromptForPeriod 이식) ──


def _format_ia_outline(idea: IdeaSpec) -> str:
    lines = []
    for node in idea.ia:
        lines.append(f"- {node.depth1}")
        for leaf in node.depth2:
            lines.append(f"  · {leaf.title} — {leaf.desc}")
    return "\n".join(lines)


def build_period_prompt(idea: IdeaSpec, kw_name: str, axis: ResolvedAxis, period: str) -> str:
    """period는 내부 키(day/week/month)."""
    ia_outline = _format_ia_outline(idea)
    mvp_list = "\n".join(f"- [핵심 기능 {i + 1}]: {f}" for i, f in enumerate(idea.mvp_features))
    future_list = "\n".join(f"- {f}" for f in idea.future_features)
    stack_line = f"추천 기술 스택: {idea.stack}"
    period_label = {"day": "하루", "week": "일주일", "month": "한 달 이상"}[period]

    header = f"""당신은 뛰어난 풀스택 시니어 소프트웨어 엔지니어입니다.
최근 트렌드 키워드 '#{kw_name}'을(를) 활용한 바이브코딩 프로젝트 [{idea.short_name}]을(를) 지금부터 개발합니다.

# 1. 프로젝트 목표
- 서비스명: {idea.short_name}
- 한 줄 컨셉: {idea.slogan}
- 핵심 트렌드: #{kw_name}
- 타깃 사용자: {idea.target}
- 플랫폼: {axis.platform_spec['label']} — {axis.platform_spec['form_directive']}
- 기획 유형: {axis.type_spec['label']} 중심 — 디자인 톤: {axis.type_spec['tone']}
- 개발 기간: {period_label}
- 해결하는 문제: {idea.problem}
- 해결 방식: {idea.solution}
- 차별점: {idea.diff}"""

    architecture_section = f"""
# 2. 시스템 아키텍처 및 서비스 정보구조(IA)
- 전체 구조: {idea.architecture}
- 디자인 톤앤매너: 깨끗하고 세련된 모던 UI, 라운드 카드 레이아웃, 직관적인 칩/버튼 인터랙션
- 아래 정보구조(IA)를 그대로 페이지·섹션 구조에 반영하세요. 절대 임의로
  다른 화면 구성을 지어내지 마세요:
{ia_outline}"""

    mvp_section = f"""
# 3. MVP 핵심 기능 명세
{mvp_list}"""

    if period == "week":
        return f"""{header}
{architecture_section}
{mvp_section}

# 4. 진행 방식 — 먼저 질문하세요
바로 코드를 작성하지 마세요. 아래 항목을 저에게 먼저 물어보고, 제 답을 받은 뒤에 설계와 코드를 시작하세요.
- 제가 실제로 이 서비스를 쓸 상황(언제·어디서·왜 켜보는지)이 위 타깃 설명과 맞는지
- 위 IA의 화면 중 제가 가장 먼저 완성하고 싶은 화면이 무엇인지
- 데이터를 어디서 가져올지 (직접 입력 / 공개 API / 목업 고정값 중 무엇으로 시작할지)
- 위 디자인 톤을 그대로 쓸지, 다른 무드를 원하는지

# 5. 개발 제약 사항 및 기술 스택 — 하루 완성본보다 한 단계 높은 완성도
- {stack_line} (경량 BaaS 연동 포함, 예: Supabase)
- 목업이 아니라 실제 데이터베이스에 저장·조회되는 인증·데이터 흐름을 갖추세요. 이것이 하루 완성본과의 핵심 차이입니다.
- 결제, 복잡한 권한 체계는 이번 범위에서 제외합니다.
- 제 답변을 반영해 위 IA를 1Depth·2Depth까지 전부 구현하세요.
- 예외 상황(검색 결과 없음, 잘못된 입력)에 대한 친절한 Empty State 안내 UI를 포함하세요.
- 모바일 화면에서도 깨짐 없는 완전 반응형(Responsive) 레이아웃을 작성하세요."""

    if period == "month":
        return f"""{header}
{architecture_section}
{mvp_section}

# 4. 확장 기능 (이 완성도에서는 반드시 반영)
{future_list or '- (별도 확장 기능 없음 — 대신 아키텍처 완성도를 최고 수준으로 높이는 데 집중하세요)'}

# 5. 진행 방식 및 요구 완성도 — 실제 서비스 수준
- 먼저 전체 아키텍처(화면 구조, 데이터 모델, API 설계, 인증 방식)를 설계하고 저에게 검토받은 뒤 구현하세요.
- 하루·일주일 버전과의 차이는 일정이 아니라 완성도입니다: 인증, 실 데이터베이스, 배포 파이프라인, 테스트를 전부 갖춘 프로덕션 수준으로 만드세요.
- 위 IA와 확장 기능을 전부 반영하세요. 프론트엔드뿐 아니라 백엔드·배포까지 다룰 수 있는 실력이 필요한 범위입니다.
- 각 구조적 결정의 이유를 간단히 남기세요 (ADR 형식 권장).
- 핵심 로직에는 테스트를 작성하세요.

# 6. 기술 스택
- {stack_line}를 베이스로 하되, 데이터베이스·인증·배포 환경을 실제 서비스 수준으로 구성하세요.
- 확장 가능한 폴더 구조와 타입 안정성(TypeScript 등)을 갖추세요.

전체 아키텍처 설계부터 시작해 주세요."""

    # 기본값: 'day' (하루)
    return f"""{header}
{architecture_section}
{mvp_section}

# 4. 개발 제약 사항 및 기술 스택
- {stack_line}
- 복잡한 회원가입, 결제, 백엔드 서버 구축은 배제하고 프론트엔드 단독 또는 경량 API만으로 구축합니다.
- 위 IA의 1Depth 중 핵심 화면 1~2개에 집중하고 나머지는 최소한으로 단순화하세요.
- 예외 상황(검색 결과 없음, 잘못된 입력)에 대한 친절한 Empty State 안내 UI를 포함하세요.
- 모바일 화면에서도 깨짐 없는 완전 반응형(Responsive) 레이아웃을 작성하세요.

질문하지 말고 지금 바로 폴더 구조와 전체 컴포넌트 코드 작성을 시작해 주세요. 비개발자가 그대로 실행만 하면 되는 완성본으로 주세요."""
