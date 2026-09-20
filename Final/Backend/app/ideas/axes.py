"""
플랫폼(platform) × 유형(type) 축 사양 — 이 기능의 데이터 원천.

★ 순수 데이터 파일이다. 여기서 아무것도 import 하지 않는다
  (app.core.llm 도, app.config.settings 도 안 쓴다). 그래야
  LLM 없이도 이 파일 하나만으로 축 검증 테스트가 돈다.

★ 9조합(3 플랫폼 × 3 유형)을 if/else 로 분기하지 않는다.
  모든 분기는 아래 테이블 조회로 끝낸다 — 새 축 값이 추가돼도
  이 파일에 한 줄만 늘리면 된다.

프론트(v1-trend-incubator.html, V1.3 디자인)의 칩 라벨:
  platform: "웹(Web)" / "모바일 앱(App)"
  type:     "실용(편의)" / "재미" / "수익(비즈니스)"
  period:   "하루" / "일주일" / "한 달 이상"
문서(docs/IDEA_GENERATION_HANDOFF.md)의 기간 라벨은 "1일/일주일/한달"로
다르다 — 내부 키(day/week/month)로 통일하고 둘 다 별칭으로 받는다.

★ 2026-09-17: V1.3 디자인에서 플랫폼이 웹/모바일앱 2개로 줄었다
  (데스크탑 웹 제거). 9조합 → 6조합.
★ 2026-09-19: 추천 AI가 축(플랫폼×유형)이 아니라 **개발 기간**으로
  결정된다. AI_TOOL_BY_PERIOD 참고.
"""

from dataclasses import dataclass

# ── 별칭 정규화 ──────────────────────────────────

PLATFORM_ALIASES: dict[str, str] = {
    "웹(web)": "web", "웹(web mvp)": "web", "웹": "web", "web": "web", "web mvp": "web",
    "모바일 앱(app)": "mobile", "모바일 앱": "mobile", "모바일앱": "mobile", "모바일": "mobile", "mobile": "mobile",
}

TYPE_ALIASES: dict[str, str] = {
    "실용(편의)": "utility", "실용": "utility", "편의": "utility", "utility": "utility",
    "재미": "fun", "fun": "fun",
    "수익(비즈니스)": "business", "수익": "business", "비즈니스": "business", "business": "business",
}

PERIOD_ALIASES: dict[str, str] = {
    "하루": "day", "1일": "day", "1 일": "day", "day": "day",
    "일주일": "week", "1주일": "week", "week": "week",
    "한 달 이상": "month", "한달": "month", "한 달": "month", "month": "month",
}


def _normalize(raw: str, table: dict[str, str], axis_name: str) -> str:
    key = table.get(raw.strip().lower())
    if key is None:
        valid = ", ".join(sorted(set(table.values())))
        raise ValueError(f"알 수 없는 {axis_name} 값: {raw!r} (허용: {valid})")
    return key


def normalize_platform(raw: str) -> str:
    return _normalize(raw, PLATFORM_ALIASES, "platform")


def normalize_type(raw: str) -> str:
    return _normalize(raw, TYPE_ALIASES, "type")


def normalize_period(raw: str) -> str:
    return _normalize(raw, PERIOD_ALIASES, "period")


# ── 플랫폼 축 ────────────────────────────────────

PLATFORM_SPEC: dict[str, dict] = {
    "web": {
        "label": "웹(Web)",
        "form_directive": (
            "브라우저 주소 하나로 바로 열리는 반응형 웹을 전제하라. "
            "설치·로그인 없이 첫 화면에서 핵심 가치를 바로 보여주고, 결과를 "
            "링크로 공유할 수 있어야 한다. 카메라 상시 접근·푸시 알림·백그라운드 "
            "위치처럼 네이티브 권한이 있어야만 성립하는 아이디어는 내지 마라."
        ),
        "ia_directive": (
            "depth1은 상단 네비게이션 또는 세로 스크롤 섹션으로 읽히는 3~4개로 "
            "하라. 첫 번째 depth1은 주소로 들어오자마자 보이는 랜딩 겸 핵심 "
            "화면이어야 한다. 로그인·회원가입 전용 화면을 depth1로 두지 마라."
        ),
        "ia_shape": {"depth1_min": 3, "depth1_max": 4},
        "stack_default": "Next.js 14 (App Router), TypeScript, TailwindCSS, Vercel 배포",
        "mvp_directive": (
            "새로고침·링크 재방문에도 상태가 유지되는 장치(URL 쿼리 또는 "
            "localStorage)를 기능 하나로 반드시 포함하라. 기능은 4개 이내로 하라."
        ),
        "target_directive": (
            "검색이나 SNS 링크를 타고 방금 처음 들어온 방문자로 서술하라. "
            "'가입한 회원'을 전제하지 마라."
        ),
    },
    "mobile": {
        "label": "모바일 앱(App)",
        "form_directive": (
            "손에 들고 쓰는 앱을 전제하라. 한 손 엄지 조작, 1~2분짜리 짧은 "
            "세션 안에 한 가지 일만 끝내는 흐름이어야 한다. 카메라·위치·푸시·"
            "햅틱 중 최소 하나를 핵심 가치로 쓰되, 그 기능이 없으면 서비스가 "
            "성립하지 않을 만큼 중심에 두어라."
        ),
        "ia_directive": (
            "하단 탭바를 전제하라 — depth1이 곧 탭이므로 3~4개로 하고 이름은 "
            "6자 이내 명사로 하라. 마지막 depth1은 '마이'·'보관함'처럼 개인 "
            "영역으로 하라. 넓은 표나 다단 레이아웃이 필요한 기능을 depth2에 "
            "넣지 마라."
        ),
        "ia_shape": {"depth1_min": 3, "depth1_max": 4},
        "stack_default": "React Native (Expo), TypeScript, NativeWind, Supabase",
        "mvp_directive": (
            "권한 요청은 1개 이내로 하라. 네트워크가 끊겨도 마지막 목록은 "
            "보이게 하라. 앱을 켜고 두 번의 탭 안에 핵심 동작에 도달해야 한다."
        ),
        "target_directive": (
            "이동 중·매장 안·현장처럼 '어디서 꺼내 쓰는지'를 반드시 포함해서 서술하라."
        ),
    },
}

# ── 유형 축 ──────────────────────────────────────

TYPE_SPEC: dict[str, dict] = {
    "utility": {
        "label": "실용(편의)",
        "angle_directive": (
            "사용자가 지금 손으로 반복하는 번거로운 일 하나를 자동화하거나 "
            "단계를 줄여라. 줄어든 단계가 화면에서 눈으로 확인돼야 한다. "
            "게임 요소나 수익 모델은 넣지 마라."
        ),
        "ia_directive": "depth1 순서에 '입력 → 처리·결과 → 저장·다시 쓰기' 흐름이 드러나게 하라.",
        "mvp_directive": "핵심 동작 하나를 끝까지 자동화하라. 설정 화면을 만들지 말고 기본값으로 동작시켜라.",
        "target_directive": "그 번거로움을 주 1회 이상 실제로 겪는 사람으로 좁혀 서술하라.",
        "tone": "군더더기 없이 정보 밀도가 높은 UI",
        "naming_hint": "무슨 기능인지 이름만 봐도 알 수 있게 지어라",
        "stack_extra": "",
    },
    "fun": {
        "label": "재미",
        "angle_directive": (
            "결과물이 캡처해서 친구에게 보내고 싶은 것이어야 한다. 한 번 "
            "해보고 → 결과를 공유하고 → 받은 사람이 또 해보는 고리가 핵심이다. "
            "정확도·완결성보다 의외성과 반응을 우선하라."
        ),
        "ia_directive": "마지막 depth1은 반드시 결과 공유·자랑 화면으로 하라.",
        "mvp_directive": (
            "회원가입 없이 30초 안에 결과가 나와야 한다. 결과를 이미지 카드로 "
            "만들어 저장·공유하는 기능을 반드시 포함하라."
        ),
        "target_directive": "심심할 때 SNS에서 유입되는 사람으로, 연령대와 커뮤니티 성향으로 서술하라.",
        "tone": "과감한 색과 애니메이션, 손맛 있는 인터랙션",
        "naming_hint": "말장난이나 밈을 써서 입에 붙는 이름으로 지어라",
        "stack_extra": "Framer Motion, html2canvas (결과 카드 이미지화)",
    },
    "business": {
        "label": "수익(비즈니스)",
        "angle_directive": (
            "누가 왜 돈을 내는지가 서비스 구조 자체에 드러나야 한다. 무료로 "
            "쓰는 사람과 돈을 내는 사람이 보는 화면이 달라야 한다. 다만 가격·"
            "매출·시장 규모 같은 숫자는 절대 지어내지 마라."
        ),
        "ia_directive": "depth1 중 하나는 판매·예약·문의처럼 거래가 일어나는 화면으로 하라.",
        "mvp_directive": (
            "결제 연동은 MVP 범위에서 외부 결제 링크나 문의 폼으로 대체하되, "
            "유료로 넘어가는 지점 하나를 기능 목록에 명시하라."
        ),
        "target_directive": "돈을 내는 쪽과 쓰는 쪽이 다르면 둘 다 나눠서 적어라.",
        "tone": "신뢰감 있는 절제된 UI",
        "naming_hint": "서비스로 신뢰가 가는 담백한 이름으로 지어라",
        "stack_extra": "Supabase (인증·데이터), 토스페이먼츠 또는 외부 결제 링크",
    },
}

# ── 6조합 전용 메모 ──────────────────────────────
# 두 축을 곱하기만 하면 결과가 비슷해질 위험이 있다(특히 '재미'는 플랫폼
# 영향을 덜 받는다). 조합마다 이 한 줄을 프롬프트 맨 앞에 박아 강제한다.

COMBO_NOTES: dict[tuple[str, str], str] = {
    ("web", "utility"): "링크를 열어 붙여넣기 한 번으로 끝나는 도구. 계정 없이 결과가 나오고 결과 주소를 저장해 두면 다시 쓴다.",
    ("web", "fun"): "결과 주소 자체가 공유 자산이다. 남의 결과 페이지를 열어보는 것만으로도 재미가 있어야 한다.",
    ("web", "business"): "검색·광고로 들어온 방문자를 문의·예약으로 넘기는 랜딩형 구조. 판매자용 관리 화면이 따로 있다.",
    ("mobile", "utility"): "현장에서 꺼내 3초 만에 기록하고 닫는 앱. 나중에 몰아서 정리하는 화면이 따로 있다.",
    ("mobile", "fun"): "카메라나 위치로 지금·여기를 찍어 만드는 놀이. 만든 결과는 스토리 비율 카드로 나간다.",
    ("mobile", "business"): "현장에서 바로 주문·예약·정산이 일어나는 접점. 알림이 매출로 직결된다.",
}

# ── 추천 AI 카탈로그 (화이트리스트) ──────────────
# ★ LLM이 자유 생성하지 않는다. 사용자가 이 pill을 보고 실제로 가입·
#   결제하러 가므로 존재하지 않는 툴·낡은 모델명이 나오면 안 된다.
#   버전·모델명("Claude 3.5 Sonnet" 같은)은 절대 넣지 않는다 — 이름과
#   역할만 둔다.
#
# ★ 2026-09-19: 추천 기준이 "플랫폼 × 유형"에서 **개발 기간**으로 바뀌었다.
#   기간이 길수록 손으로 치는 도구에서 대신 짜주는 에이전트로 넘어간다.
#   기존의 AI_TOOL_COMBO(축 기반 표)와 pick_ai_tools()는 제거했다 —
#   두 체계를 함께 두면 화면과 응답이 어긋난다.

AI_TOOL_CATALOG: dict[str, dict] = {
    "chatgpt": {"name": "ChatGPT", "role": "대화로 기획·코드 초안 잡기"},
    "gemini": {"name": "Gemini", "role": "긴 문서·이미지까지 함께 묻기"},
    "claude": {"name": "Claude", "role": "긴 코드 읽고 고쳐 쓰기"},
    "ai_studio": {"name": "Google AI Studio", "role": "모델을 무료로 실험해 보기"},
    "antigravity": {"name": "Antigravity", "role": "에이전트가 대신 코드 작성"},
    "cursor": {"name": "Cursor", "role": "코드 편집·리팩터링 전반"},
    "claude_code": {"name": "Claude Code", "role": "터미널에서 여러 파일 한번에"},
    "codex": {"name": "Codex", "role": "작업을 통째로 맡기는 에이전트"},
}

# 기간 키(day/week/month) → 추천 AI id 목록. 축과 무관하게 고정이다.
AI_TOOL_BY_PERIOD: dict[str, list[str]] = {
    "day": ["chatgpt", "gemini", "claude", "ai_studio"],
    "week": ["antigravity", "cursor"],
    "month": ["claude_code", "codex"],
}


@dataclass(frozen=True)
class ResolvedAxis:
    platform_key: str
    type_key: str
    platform_spec: dict
    type_spec: dict
    combo_note: str


def resolve(platform_raw: str, type_raw: str) -> ResolvedAxis:
    """프론트 칩 라벨(또는 내부 키)을 받아 테이블을 조회한 값으로 묶는다."""
    p = normalize_platform(platform_raw)
    t = normalize_type(type_raw)
    return ResolvedAxis(
        platform_key=p,
        type_key=t,
        platform_spec=PLATFORM_SPEC[p],
        type_spec=TYPE_SPEC[t],
        combo_note=COMBO_NOTES[(p, t)],
    )


def build_stack(axis: ResolvedAxis) -> str:
    """stack은 LLM에 맡기지 않는다 — 존재하지 않는 라이브러리가 그대로
    사용자의 바이브코딩 프롬프트로 흘러가는 걸 막기 위해 코드가 조립한다."""
    base = axis.platform_spec["stack_default"]
    extra = axis.type_spec.get("stack_extra", "")
    return f"{base}, {extra}" if extra else base


def tools_for_period(period_key: str) -> list[dict]:
    """기간 키(day/week/month) → [{id, name, role}]. 축과 무관하게 고정이다.

    모르는 기간이 들어오면 'day'로 떨어뜨린다 — 화면의 pill이 빈 채로
    남는 것보다 낫다."""
    ordered = AI_TOOL_BY_PERIOD.get(period_key) or AI_TOOL_BY_PERIOD["day"]
    return [
        {"id": tid, "name": AI_TOOL_CATALOG[tid]["name"], "role": AI_TOOL_CATALOG[tid]["role"]}
        for tid in ordered
        if tid in AI_TOOL_CATALOG
    ]


def tools_by_period() -> dict[str, list[dict]]:
    """3개 기간 전부. 아이디어 캐시가 period를 키에 넣지 않고 기간별
    프롬프트 3벌을 한꺼번에 싣는 것과 같은 이유로, AI 목록도 한꺼번에 담는다."""
    return {p: tools_for_period(p) for p in ("day", "week", "month")}
