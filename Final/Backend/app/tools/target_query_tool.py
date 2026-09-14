"""전체 주제·불편 의도를 유지하며 제한 예산만큼 순환 탐색하는 결정적 계획기."""
from __future__ import annotations

import hashlib
import unicodedata
from collections import defaultdict
from urllib.parse import parse_qs, urlsplit

from app.config.dictionaries import DICT_VERSION, DOMAIN_KEYWORDS, SEARCH_PAIN_INTENTS
from app.config.settings import settings
from app.schemas.collections import CollectionCoverage, TargetProfile, TargetQuery
from app.schemas.models import Category, Judgement, RawItem, SourceKind

PLAN_VERSION = f"catalog-v4:{DICT_VERSION}:evidence_v2"
CONTEXT_INTENT = "상황 탐색"

# 경험자 속성 동의어가 아니라 검색할 업무·생활 맥락이다.
_JOB_CONTEXTS = {
    "군인": {
        Category.IT_PRODUCTIVITY: ["근무표", "당직 교대", "휴가 신청", "보고 행정", "업무 인수인계"],
        Category.LIFESTYLE: ["부대 이동", "관사", "기숙사", "택배 수령", "식사 시간"],
        Category.FINANCE: ["수당", "급여 명세서", "군인 적금"],
        Category.HEALTHCARE: ["외진 신청", "진료 예약", "건강검진 일정"],
        Category.EDUCATION_CAREER: ["전역 준비", "자격증 공부", "자기개발", "재취업"],
    },
    "마케터": {
        Category.IT_PRODUCTIVITY: ["광고 성과 취합", "채널 계정 관리", "소재 승인", "콘텐츠 일정", "보고서 작성", "데이터 연동"],
        Category.FINANCE: ["광고비 정산", "캠페인 예산", "결제 증빙"],
        Category.LIFESTYLE: ["촬영 장소 예약", "행사 이동"],
        Category.EDUCATION_CAREER: ["마케팅 도구 교육", "포트폴리오 정리"],
    },
    "개발자": {
        Category.IT_PRODUCTIVITY: ["개발 환경 설정", "코드 리뷰", "배포 승인", "장애 대응", "기술 문서"],
        Category.EDUCATION_CAREER: ["기술 면접", "개발 공부", "포트폴리오"],
        Category.LIFESTYLE: ["재택 업무 공간", "출퇴근"],
    },
    "학생": {
        Category.EDUCATION_CAREER: ["수강 신청", "팀 과제", "강의 자료", "시험 일정"],
        Category.LIFESTYLE: ["통학", "기숙사", "도서관 좌석"],
        Category.FINANCE: ["장학금 신청", "등록금 납부"],
    },
    "디자이너": {
        Category.IT_PRODUCTIVITY: ["디자인 피드백", "시안 수정", "파일 전달", "버전 관리", "소재 검색"],
        Category.EDUCATION_CAREER: ["디자인 포트폴리오", "외주 견적", "클라이언트 소통"],
    },
    "간호사": {
        Category.IT_PRODUCTIVITY: ["교대 근무표", "업무 인계", "기록 입력", "물품 재고"],
        Category.EDUCATION_CAREER: ["신규 교육", "보수 교육 신청"],
        Category.LIFESTYLE: ["야간 출퇴근", "교대 식사 시간"],
    },
}
_PLACE_CONTEXTS = {
    "집": {Category.LIFESTYLE: ["택배 수령", "쓰레기 분리", "청소", "생활 소음"], Category.IT_PRODUCTIVITY: ["재택 업무", "인터넷 연결"]},
    "사무실": {Category.IT_PRODUCTIVITY: ["회의실 예약", "업무 전달", "문서 승인", "공용 장비"], Category.LIFESTYLE: ["출입 절차", "주차"]},
    "병원": {Category.HEALTHCARE: ["접수 절차", "진료 대기", "예약 변경", "서류 발급", "수납"]},
    "학교": {Category.EDUCATION_CAREER: ["수강 신청", "강의실 변경", "과제 제출", "학사 공지"], Category.LIFESTYLE: ["통학", "식당 대기"]},
}
_NON_NEWS = (
    (SourceKind.COMMUNITY, "naver", "kin", "네이버 지식iN"),
    (SourceKind.COMMUNITY, "naver", "cafearticle", "네이버 카페"),
    (SourceKind.BLOG, "kakao", "blog", "다음 블로그"),
)


def _sources(category):
    return ((SourceKind.NEWS, "naver", "news", "네이버 뉴스"),) if category in {
        Category.FINANCE, Category.HEALTHCARE
    } else _NON_NEWS


def topic_catalog(target: TargetProfile) -> list[tuple[Category, str, str]]:
    """기존 120개는 빠짐없이 남긴다. 타겟 맥락은 우선순위가 높은 별도 후보다."""
    context = defaultdict(list)
    for job in target.jobs:
        context_key = next((key for key in _JOB_CONTEXTS if job == key or job.endswith(" " + key)), job)
        rows = _JOB_CONTEXTS.get(context_key, {
            Category.IT_PRODUCTIVITY: ["업무 일정", "서류 제출", "장비 사용", "업무 인수인계"],
            Category.LIFESTYLE: ["근무 환경", "출퇴근"],
            Category.EDUCATION_CAREER: ["직무 교육", "교육 신청"],
        })
        for category, topics in rows.items():
            context[category].extend(topics)
    for place in target.places:
        rows = _PLACE_CONTEXTS.get("사무실" if place == "회사" else place, {Category.LIFESTYLE: ["이용 절차", "이동 경로", "시설 이용", "대기 시간"],
                                          Category.IT_PRODUCTIVITY: ["예약 변경", "정보 확인"]})
        for category, topics in rows.items():
            context[category].extend(topics)
    queues = {}
    for category in Category:
        preferred = list(dict.fromkeys(context[category]))
        base = list(DOMAIN_KEYWORDS[category])
        # 입력에 직접 등장하는 주제도 우선한다. 나머지는 절대로 삭제하지 않는다.
        base.sort(key=lambda topic: (not any(token in topic or topic in token for token in target.jobs + target.places),
                                     DOMAIN_KEYWORDS[category].index(topic)))
        ordered = list(dict.fromkeys(preferred + base))
        queues[category] = [(category, topic, hashlib.sha256(f"{category.value}:{topic}".encode()).hexdigest()[:16])
                            for topic in ordered]
    return [queues[category][index] for index in range(max(map(len, queues.values())))
            for category in Category if index < len(queues[category])]


def _combinations(target):
    jobs, places = target.jobs or [None], target.places or [None]
    return [(job, places[(index + offset) % len(places)])
            for offset in range(len(places)) for index, job in enumerate(jobs)]


def _anchor_tracks(target: TargetProfile) -> list[tuple[str, tuple[str, ...]]]:
    full, broad = [], []
    seen = set()
    for job, place in _combinations(target):
        variants = [
            ("all_conditions", [target.age, target.gender, job, place]),
            ("job_place_context", [job, place]),
            ("age_context", [target.age, job, place]),
            ("gender_context", [target.gender, job, place]),
            ("job_only", [job]), ("place_only", [place]),
        ]
        for name, values in variants:
            anchors = tuple(dict.fromkeys(v for v in values if v))
            if not anchors or anchors in seen:
                continue
            seen.add(anchors)
            (full if name == "all_conditions" else broad).append((name, anchors))
    if target.age == "50대 이상":
        # 범위 선택을 문자 그대로의 '50대 이상' 검색에 가두지 않는다.
        # 이는 검색 확장일 뿐, 경험자 나이 확인은 별도 근거 검증을 거친다.
        for age_term in ("50대", "60대", "70대", "80대", "90대", "100세"):
            anchors = (age_term,)
            if anchors not in seen:
                seen.add(anchors)
                broad.append(("age_range", anchors))
    # 첫 회차부터 전체 조건과 넓은 맥락을 섞는다. 동일 토큰 요청은 서로 다른 이름으로 재과금하지 않는다.
    return [rows[index] for index in range(max(len(full), len(broad))) for rows in (full, broad)
            if index < len(rows)]


def catalog_size(target: TargetProfile) -> int:
    expressions = 1 + sum(len(phrases) for phrases in SEARCH_PAIN_INTENTS.values())
    return sum(expressions * len(_anchor_tracks(target)) * len(_sources(category))
               for category, _, _ in topic_catalog(target))


def iter_query_catalog(target: TargetProfile):
    """전체 조합은 지연 생성한다. 분야·주제·8의도·출처·타겟 맥락을 첫 회차부터 섞는다."""
    topics = topic_catalog(target)
    tracks = _anchor_tracks(target)
    intents = list(SEARCH_PAIN_INTENTS)
    # 감정 단어나 불만 표현을 쓰지 않은 실제 경험도 검색 단계에서 발견한다.
    phrase_slots = [(CONTEXT_INTENT, "")] + [(intent, phrase) for offset in range(max(map(len, SEARCH_PAIN_INTENTS.values())))
                    for intent in intents for phrase in SEARCH_PAIN_INTENTS[intent][offset:offset + 1]]
    cycle = len(phrase_slots)
    max_waves = cycle * len(tracks) * max(len(_sources(c)) for c in Category)
    ranks = defaultdict(int)
    ranked = []
    for category, topic, topic_id in topics:
        ranked.append((category, topic, topic_id, ranks[category]))
        ranks[category] += 1
    for phase in range(max_waves):
        for category, topic, topic_id, rank in ranked:
            sources = _sources(category)
            if phase >= cycle * len(sources) * len(tracks):
                continue
            phrase_index = (phase + rank + list(Category).index(category)) % cycle
            intent, phrase = phrase_slots[phrase_index]
            source_index = (phase // cycle + phrase_index + list(Category).index(category)) % len(sources)
            track_index = (phase // (cycle * len(sources)) + rank * len(Category) + list(Category).index(category)) % len(tracks)
            anchor_mode, anchors = tracks[track_index]
            kind, provider, endpoint, source_name = sources[source_index]
            key = f"{PLAN_VERSION}|{topic_id}|{intent}|{phrase}|{anchors}|{provider}|{endpoint}"
            yield TargetQuery(
                id="q-" + hashlib.sha256(key.encode()).hexdigest()[:20], topic=topic, topic_id=topic_id,
                intent=intent, anchor_mode=anchor_mode, keyword=" ".join(v for v in [*anchors, topic, phrase] if v),
                category=category, source_kind=kind, provider=provider, endpoint=endpoint, source_name=source_name,
                reason="전체 카탈로그에서 타겟 맥락을 우선하고 분야·불편 유형·미탐색 범위를 순환",
            )


def build_target_queries(target: TargetProfile, *, completed_ids=None, budget=None) -> list[TargetQuery]:
    done = set(completed_ids or [])
    limit = max(1, int(settings.COLLECTION_QUERY_BUDGET if budget is None else budget))
    selected = []
    for query in iter_query_catalog(target):
        if query.id in done:
            continue
        selected.append(query)
        if len(selected) >= limit:
            break
    return selected


def coverage_for(target: TargetProfile, *, completed_ids=(), topic_ids=(), intents=()) -> CollectionCoverage:
    total = catalog_size(target)
    completed = min(len(set(completed_ids)), total)
    return CollectionCoverage(topics_total=len(topic_catalog(target)), topics_searched=len(set(topic_ids)),
                              intents_total=len(SEARCH_PAIN_INTENTS) + 1, intents_searched=len(set(intents)),
                              catalog_total=total, catalog_completed=completed, catalog_remaining=total - completed)


def canonical_item_key(item: RawItem) -> str:
    """지식iN PC/모바일/답변 URL을 같은 질문 docId로 센다. 원래 출처 URL은 보존한다."""
    try:
        parts = urlsplit(item.url)
        host = (parts.hostname or "").lower()
        params = {key.lower(): values for key, values in parse_qs(parts.query).items()}
        if (host == "kin.naver.com" or host.endswith(".kin.naver.com")) and params.get("docid"):
            return "naver-kin:" + params["docid"][0]
    except ValueError:
        pass
    return item.id


def target_warnings(target: TargetProfile) -> list[str]:
    return [
        "검색 문구 일치만으로 자료를 제외하지 않습니다. 불편 경험과 타겟 조건이 같은 경험자에게 연결되는지 원문 근거로 판별합니다.",
        "타겟을 확인하지 못한 불편도 검토 후보로 보존하지만 확인된 문제정의의 근거에는 섞지 않습니다.",
        "금융·헬스케어는 현재 민감정보 정책에 따라 뉴스만 사용합니다. 서비스 이용 불편의 추가 출처는 별도 검토가 필요합니다.",
        "이번 회차는 설정된 검색·판별 예산만 사용합니다. 전체 카탈로그를 모두 검색했다는 의미가 아닙니다.",
        "같은 조건의 근거는 기존 묶기 정책에 따라 최근 4주 수집 자료에서 누적합니다. 근거 상세 조회는 최근 8주이며 저장된 과거 원문은 별도로 보존합니다.",
        "생성 결과는 사람 검수 전의 검토용 문제정의이며 공개 게시되지 않습니다.",
    ]

def _normalized_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return "".join(char for char in normalized if not char.isspace() and unicodedata.category(char) != "Cf")


def input_mentions(target: TargetProfile, item: RawItem) -> bool:
    """원문 제목·검색 요약의 문구 확인만 한다. 작성자 속성이나 의미를 추론하지 않는다."""
    text = _normalized_text(f"{item.title} {item.snippet}")
    checks = []
    if target.age:
        checks.append(_normalized_text(target.age) in text)
    if target.gender:
        forms = ("여성", "여자") if target.gender == "여성" else ("남성", "남자")
        checks.append(any(_normalized_text(form) in text for form in forms))
    if target.jobs:
        checks.append(any(_normalized_text(job) in text for job in target.jobs))
    if target.places:
        checks.append(any(_normalized_text(place) in text for place in target.places))
    return all(checks)



def target_label_conflicts(target: TargetProfile, judgement: Judgement) -> bool:
    """명시적으로 다른 연령·성별 라벨만 제외한다. 미상이나 직업 범주를 추정하지 않는다."""
    if target.age and judgement.sufferer_age_band and target.age != judgement.sufferer_age_band:
        return True
    gender = {"여자": "여성", "남자": "남성"}.get(judgement.sufferer_gender or "")
    return bool(target.gender and gender and target.gender != gender)
