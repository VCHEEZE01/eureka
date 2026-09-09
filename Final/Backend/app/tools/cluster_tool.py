"""
묶기 도구 — 비슷한 불편끼리 뭉친다.

쓰는 사람: ② 해석기

★ 이 파일은 LLM을 부르지 않는다. 순수 계산만 한다.
  이유: 같은 입력이면 항상 같은 묶음이 나와야 "왜 이 글들이 한 문제로 묶였는지"를
  나중에 설명할 수 있다. LLM에 통째로 맡기면 매번 결과가 달라진다.

입력은 `pain_summary` 다 (스니펫이 아니다).
  ②의 판별 단계가 이미 한 문장으로 정규화해 둔 것이라 HTML 잔재·광고 문구·인사말
  같은 노이즈가 없다. 같은 불편끼리는 어휘가 겹치고 다른 불편끼리는 안 겹친다.
  `pain_summary` 가 없는(=불편이 아닌) 항목은 묶기 대상이 아니므로 제외한다.

2단계로 묶는다 (docs/DATA_COLLECTION.md 3-4).
  1차 — 어절 토큰 겹침으로 블록을 나눈다. 계산이 싸고, 2차의 O(n²)를
        전체 건수가 아니라 블록 크기로 묶어 준다.
  2차 — 블록 안에서만 벡터 유사도로 판정한다.

벡터라이저는 갈아끼울 수 있다 (`Vectorizer` 프로토콜 · `set_vectorizer`).
나중에 임베딩으로 옮길 때 이 파일에서 바꿀 곳은 그 클래스 하나뿐이다.

★ `group()` 은 5건 미만 묶음도 버리지 않는다.
  "유사한 글 5건 이상" 조건은 부르는 쪽(② 해석기)이 적용한다.
  여기서 소형 묶음을 지우면 docs/DATA_COLLECTION.md 3-6의
  "미달 후보는 쌓아 두고 다음 주에 사례가 더 모이면 자동 승격"이 불가능해진다.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from math import log, sqrt
from typing import Any, Iterator, Optional, Protocol

from app.config.settings import settings
from app.schemas.models import Judgement

# 2차 계산은 블록 크기의 제곱이다. 1차가 실패해 블록이 비대해져도
# 여기서 잘라 메모리·시간을 묶어 둔다. (자를 때도 순서는 결정적이다)
MAX_BLOCK = 600

# 이 수보다 문서가 적으면 min_df=1 로 내린다.
# min_df=2 는 "두 문서 이상에 나온 n-gram"만 남기는데, 문서가 적으면 남은 어휘가
# 전부 공유 어휘라서 서로 다른 불편의 코사인이 1.0 가까이 부풀어 오른다.
MIN_DOCS_FOR_MIN_DF = 20


# ══════════════════════════════════════════════
# 토큰화 — 형태소 분석기 없이 근사한다
# ══════════════════════════════════════════════

_NON_WORD_RE = re.compile(r"[^0-9a-z가-힣\s]+")
_DIGIT_RE = re.compile(r"\d")

# 조사·어미. 긴 것부터 본다. 한 번만 떼고, 떼고 나서 2자 미만이면 안 뗀다.
_SUFFIXES = (
    "에서는", "으로는", "에게서", "이라는", "한테서", "습니다", "합니다", "입니다",
    "네요", "어요", "아요", "해요", "예요", "이라", "라는", "으로", "에서", "에게",
    "한테", "까지", "부터", "보다", "처럼", "마다", "이나", "라도", "조차", "밖에",
    "이다", "하다", "되다", "이야",
    "은", "는", "이", "가", "을", "를", "의", "에", "도", "만", "과", "와", "랑",
    "로", "다", "요", "고", "며", "서",
)

# 주제어가 될 수 없는 말들. 최빈 어절을 뽑을 때만 쓴다.
STOPWORDS = frozenset(
    {
        "것", "수", "때", "좀", "너무", "정말", "그냥", "등", "및", "저", "제", "내",
        "나", "우리", "이거", "그거", "저거", "여기", "거기", "무슨", "어떤", "진짜",
        "완전", "조금", "계속", "자꾸", "항상", "다시", "또", "더", "가장", "제일",
        "그리고", "하지만", "근데", "그래서", "일단", "약간", "같은", "같이", "하는",
        "되는", "있는", "없는", "해야", "한다", "된다", "하기", "되기", "하고", "되고",
        "있다", "없다", "인데", "는데", "라고", "에는", "만들", "생기",
    }
)

# 수량 표현. 이 프로젝트의 제1규칙("숫자는 지어내지 않는다") 때문에 주제 힌트에서 지운다.
_QUANTITY_RE = re.compile(
    r"^(한|두|세|네|다섯|여섯|일곱|여덟|아홉|열|스무|몇|여러|매)?"
    r"(건|명|개|번|회|배|위|가지|차례|퍼센트|프로)$"
)


def _words(text: str) -> list[str]:
    """어절 목록. 기호는 공백으로 바꾸고 영문은 소문자로."""
    return _NON_WORD_RE.sub(" ", (text or "").lower()).split()


def _stem(word: str) -> str:
    """조사·어미를 한 번 떼어 낸다. 정확할 필요는 없다 — 겹침만 늘리면 된다."""
    for suffix in _SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 2:
            return word[: -len(suffix)]
    return word


def _char_ngrams(text: str, lo: int = 2, hi: int = 4) -> Iterator[str]:
    """어절 경계를 지키는 char n-gram (sklearn 의 analyzer='char_wb' 와 같은 뜻)."""
    for word in _words(text):
        padded = f" {word} "
        for n in range(lo, hi + 1):
            for i in range(len(padded) - n + 1):
                yield padded[i : i + n]


# ══════════════════════════════════════════════
# 벡터라이저 — 갈아끼우는 지점
# ══════════════════════════════════════════════


class Vectorizer(Protocol):
    """
    텍스트 목록 → 벡터 목록.

    돌려주는 것은 둘 중 하나면 된다.
      · 행렬 (scipy 희소 행렬 또는 numpy 배열) — 행이 문서
      · dict 목록 — {특징: 가중치}, 라이브러리 없이 계산할 때
    """

    name: str

    def fit_transform(self, texts: list[str]) -> Any: ...


class CharTfidfVectorizer:
    """
    기본안 — char n-gram TF-IDF (sklearn).

    한국어는 조사·어미 변형("회의록이 / 회의록을 / 회의록 정리가")이 심해 어절 BoW가
    잘 안 맞는다. 형태소 분석기는 설치가 무겁다. char 2~4gram이 설치 부담 없이
    어간 부분 일치를 잡아 준다.
    """

    name = "tfidf"

    def _build(self, min_df: int):
        from sklearn.feature_extraction.text import TfidfVectorizer

        return TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 4),
            min_df=min_df,
            sublinear_tf=True,
            max_features=50_000,
        )

    def fit_transform(self, texts: list[str]) -> Any:
        min_df = 2 if len(texts) >= MIN_DOCS_FOR_MIN_DF else 1
        try:
            return self._build(min_df).fit_transform(texts)
        except ValueError:
            # min_df 가 어휘를 통째로 날린 경우. 한 번 더 내려서 살린다.
            return self._build(1).fit_transform(texts)


class PurePythonCharVectorizer:
    """
    폴백 — 같은 char n-gram TF-IDF를 순수 파이썬으로.

    sklearn·numpy 가 없는 환경(가벼운 CI 등)에서도 묶기가 돌아가야 한다.
    가중치 식은 sklearn 기본값과 같게 맞춘다(smooth idf · sublinear tf · L2 정규화).
    그래야 임계값을 백엔드마다 따로 잡지 않아도 된다.
    """

    name = "hash"

    def fit_transform(self, texts: list[str]) -> list[dict[str, float]]:
        counts = [Counter(_char_ngrams(t)) for t in texts]
        n = len(texts)
        doc_freq: Counter[str] = Counter()
        for c in counts:
            doc_freq.update(c.keys())

        vectors: list[dict[str, float]] = []
        for c in counts:
            vec = {
                gram: (1.0 + log(tf)) * (log((1 + n) / (1 + doc_freq[gram])) + 1.0)
                for gram, tf in c.items()
            }
            norm = sqrt(sum(w * w for w in vec.values()))
            vectors.append({g: w / norm for g, w in vec.items()} if norm else {})
        return vectors


_vectorizer: Optional[Vectorizer] = None


def set_vectorizer(v: Optional[Vectorizer]) -> None:
    """벡터라이저를 갈아끼운다. 테스트와 임베딩 전환의 주입점."""
    global _vectorizer
    _vectorizer = v


def reset_vectorizer() -> None:
    """설정(settings.CLUSTER_BACKEND)대로 고르는 기본 상태로 되돌린다."""
    set_vectorizer(None)


def _sklearn_available() -> bool:
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: F401
    except Exception:  # ImportError 말고도 깨진 설치가 있다
        return False
    return True


def current_vectorizer() -> Vectorizer:
    """지금 쓰는 벡터라이저. 주입된 것이 있으면 그것, 없으면 설정대로."""
    if _vectorizer is not None:
        return _vectorizer
    # "embedding" 은 아직 구현이 없다. 붙기 전까지는 tfidf 로 내려간다.
    if settings.CLUSTER_BACKEND != "hash" and _sklearn_available():
        return CharTfidfVectorizer()
    return PurePythonCharVectorizer()


def _threshold_for(name: str) -> float:
    """
    실제로 쓰인 벡터라이저에 맞는 임계값.

    ★ settings 는 함수 안에서 읽는다. 모듈 레벨 상수로 잡아 두면
      테스트가 settings 를 제자리에서 바꿔도 옛 값을 계속 본다.
    """
    if name == settings.CLUSTER_BACKEND:
        return settings.cluster_threshold()
    # 폴백이 일어난 경우. 코사인 스케일이 다르므로 실제 백엔드 기준값을 쓴다.
    if name == "embedding":
        return settings.CLUSTER_THRESHOLD_EMBED
    return settings.CLUSTER_THRESHOLD_TFIDF


# ══════════════════════════════════════════════
# 1차 — 어절 겹침으로 블록 나누기
# ══════════════════════════════════════════════


class _UnionFind:
    """묶음 합치기. 경로 압축만 한다."""

    def __init__(self, n: int) -> None:
        self.parent = list(range(n))

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            # 작은 쪽을 뿌리로 — 결과가 입력 순서에 흔들리지 않게 한다.
            lo, hi = (ra, rb) if ra < rb else (rb, ra)
            self.parent[hi] = lo


def _components(uf: _UnionFind, n: int) -> list[list[int]]:
    """연결요소를 인덱스 오름차순 목록으로. 목록 자체도 정렬해 돌려준다."""
    buckets: dict[int, list[int]] = defaultdict(list)
    for i in range(n):
        buckets[uf.find(i)].append(i)
    return sorted(buckets.values())


def block_keys(text: str) -> set[str]:
    """
    블록 나누기용 열쇠말.

    조사·어미를 뗀 어절과, 거기서 뒤를 한두 글자 더 깎은 형태를 함께 넣는다.
    "회의록이 / 회의록을" 은 어절이 다르지만 깎으면 "회의록" 에서 만난다.
    거칠어도 된다 — 여기서 넉넉히 붙여 놓고 정밀한 판정은 2차가 한다.
    """
    keys: set[str] = set()
    for word in _words(text):
        if word in STOPWORDS or word.isdigit():
            continue
        stem = _stem(word)
        if len(stem) < 2:
            if len(word) >= 2:
                keys.add(word)
            continue
        keys.add(stem)
        if len(stem) >= 3:
            keys.add(stem[:-1])
        if len(stem) >= 4:
            keys.add(stem[:-2])
    return keys


def _blocks(texts: list[str]) -> list[list[int]]:
    """열쇠말을 공유하는 것끼리 묶어 블록으로. 반환은 전역 인덱스 목록들."""
    n = len(texts)
    postings: dict[str, list[int]] = defaultdict(list)
    for i, text in enumerate(texts):
        for key in block_keys(text):
            postings[key].append(i)

    # 너무 흔한 열쇠말은 블록을 통째로 붙여 버리고 정보도 없다. 건수가 많을 때만 거른다.
    cap = n * 0.5 if n >= MIN_DOCS_FOR_MIN_DF else n

    uf = _UnionFind(n)
    for key in sorted(postings):
        idxs = postings[key]
        if len(idxs) > cap:
            continue
        for j in idxs[1:]:
            uf.union(idxs[0], j)

    blocks: list[list[int]] = []
    for block in _components(uf, n):
        for start in range(0, len(block), MAX_BLOCK):
            blocks.append(block[start : start + MAX_BLOCK])
    return blocks


# ══════════════════════════════════════════════
# 2차 — 블록 안에서 벡터 유사도로 판정
# ══════════════════════════════════════════════


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    """이미 L2 정규화된 희소 벡터 둘의 코사인."""
    if len(a) > len(b):
        a, b = b, a
    return sum(w * b[g] for g, w in a.items() if g in b)


def _cluster_sparse(vectors: list[dict[str, float]], threshold: float) -> list[list[int]]:
    """폴백 경로 — 임계값을 넘는 쌍을 잇고 연결요소를 묶음으로 본다."""
    n = len(vectors)
    uf = _UnionFind(n)
    for i in range(n):
        if not vectors[i]:
            continue
        for j in range(i + 1, n):
            if _cosine(vectors[i], vectors[j]) > threshold:
                uf.union(i, j)
    return _components(uf, n)


def _cluster_matrix(matrix: Any, threshold: float) -> list[list[int]]:
    """기본 경로 — 코사인 거리로 평균연결 응집 군집."""
    import numpy as np

    if hasattr(matrix, "toarray"):  # 희소 행렬. TF-IDF는 이미 L2 정규화돼 있다
        sim = np.asarray((matrix @ matrix.T).todense(), dtype=float)
    else:
        arr = np.asarray(matrix, dtype=float)
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        arr = arr / norms
        sim = arr @ arr.T

    try:
        from sklearn.cluster import AgglomerativeClustering
    except Exception:
        # 벡터는 numpy 로 만들었지만 군집기가 없는 경우. 임계값 그래프로 내려간다.
        n = len(sim)
        uf = _UnionFind(n)
        for i in range(n):
            for j in range(i + 1, n):
                if sim[i][j] > threshold:
                    uf.union(i, j)
        return _components(uf, n)

    dist = np.clip(1.0 - sim, 0.0, 2.0)
    dist = (dist + dist.T) / 2.0  # 부동소수 비대칭 제거 — precomputed 는 대칭을 요구한다
    np.fill_diagonal(dist, 0.0)

    # k를 미리 몰라도 되고 결정적이다. single linkage 의 체이닝(과병합)을 피해 average.
    labels = AgglomerativeClustering(
        n_clusters=None,
        metric="precomputed",
        linkage="average",
        distance_threshold=1.0 - threshold,
    ).fit_predict(dist)

    buckets: dict[Any, list[int]] = defaultdict(list)
    for i, label in enumerate(labels):
        buckets[int(label)].append(i)
    return sorted(buckets.values())


def _cluster(texts: list[str], threshold: float, vectorizer: Vectorizer) -> list[list[int]]:
    """블록 하나를 묶음들로. 반환은 블록 안 지역 인덱스."""
    if len(texts) == 1:
        return [[0]]
    try:
        vectors = vectorizer.fit_transform(texts)
    except ValueError:
        # 어휘를 하나도 못 만든 경우(기호뿐인 문장 등). 붙이지 않는다.
        return [[i] for i in range(len(texts))]
    if isinstance(vectors, list):
        return _cluster_sparse(vectors, threshold)
    return _cluster_matrix(vectors, threshold)


# ══════════════════════════════════════════════
# 공개 함수
# ══════════════════════════════════════════════


def group(judgements: list[Judgement]) -> list[list[Judgement]]:
    """
    비슷한 불편끼리 묶는다. 반환: 묶음들의 목록.

    · `pain_summary` 가 없는 항목은 제외한다 (묶을 문장이 없다).
    · 1건짜리 묶음도 그대로 돌려준다. 5건 기준은 부르는 쪽이 적용한다.
    · 같은 입력이면 항상 같은 출력이다 — 입력을 raw_item_id 로 정렬해 처리하고,
      묶음 안과 묶음들의 순서도 정렬해서 돌려준다.
    """
    items = sorted(
        (j for j in judgements if (j.pain_summary or "").strip()),
        key=lambda j: j.raw_item_id,
    )
    if not items:
        return []
    if len(items) == 1:
        return [[items[0]]]

    texts = [j.pain_summary.strip() for j in items]  # type: ignore[union-attr]
    vectorizer = current_vectorizer()
    threshold = _threshold_for(getattr(vectorizer, "name", ""))

    groups: list[list[Judgement]] = []
    for block in _blocks(texts):
        block_texts = [texts[i] for i in block]
        for local in _cluster(block_texts, threshold, vectorizer):
            groups.append(sorted((items[block[i]] for i in local), key=lambda j: j.raw_item_id))

    # 큰 묶음부터. 같은 크기면 id 순 — 어느 쪽이든 입력이 같으면 순서도 같다.
    groups.sort(key=lambda g: (-len(g), tuple(j.raw_item_id for j in g)))
    return groups


def _is_theme_token(token: str) -> bool:
    """주제 힌트에 남길 어절인가."""
    if len(token) < 2 or token in STOPWORDS:
        return False
    # ★ 숫자·수량 표현은 남기지 않는다. 이 프로젝트의 제1규칙이 "숫자는 지어내지 않는다"이고,
    #   theme_hint 는 화면에 안 나가는 ③의 재료라 규칙 하나로 충분하다.
    return not _DIGIT_RE.search(token) and not _QUANTITY_RE.match(token)


def _rank(freq: Counter[str]) -> list[str]:
    """많이 나온 것 → 긴 것 → 사전 순. 동점에서도 결정적이어야 한다."""
    return [t for t, _ in sorted(freq.items(), key=lambda kv: (-kv[1], -len(kv[0]), kv[0]))]


def name_group(group_items: list[Judgement]) -> str:
    """
    이 묶음이 무엇에 관한 것인지 한 구절로 (12자 이내).

    LLM을 부르지 않는다. 묶음의 `pain_summary` 들에서 가장 여러 글에 나온
    2-gram·어절을 뽑아 붙일 뿐이다. 숫자·수량 표현은 남기지 않는다.
    """
    summaries = [(j.pain_summary or "").strip() for j in group_items]
    summaries = [s for s in summaries if s]
    if not summaries:
        return ""

    # 몇 번 나왔나가 아니라 "몇 글에 나왔나"로 센다. 한 글이 반복해도 주제가 되진 않는다.
    unigram_df: Counter[str] = Counter()
    bigram_df: Counter[str] = Counter()
    for summary in summaries:
        tokens = [t for t in (_stem(w) for w in _words(summary)) if _is_theme_token(t)]
        unigram_df.update(set(tokens))
        bigram_df.update({f"{a} {b}" for a, b in zip(tokens, tokens[1:])})

    parts: list[str] = []
    top_bigrams = _rank(bigram_df)
    if top_bigrams and bigram_df[top_bigrams[0]] >= 2:
        parts = top_bigrams[0].split()
    elif unigram_df:
        parts = [_rank(unigram_df)[0]]
    if not parts:
        return ""

    # 12자가 남으면 다음 순위 어절을 하나까지 덧붙인다.
    for token in _rank(unigram_df):
        if len(parts) >= 3:
            break
        if token in parts:
            continue
        if len(" ".join(parts + [token])) <= 12:
            parts.append(token)

    phrase = " ".join(parts)
    return phrase if len(phrase) <= 12 else phrase[:12].strip()
