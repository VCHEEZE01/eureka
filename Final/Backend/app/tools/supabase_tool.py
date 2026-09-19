"""
Supabase Postgres 접근 — PostgREST를 httpx로 직접 부른다.

★ service_role 키를 쓴다 = RLS를 완전히 우회한다. 그래서 모든 쿼리에
  user_id 필터를 이 파일이 직접 넣는다 — 빠뜨리면 다른 사용자 행까지
  보이거나 지워진다. app/agents/base.py:8 규칙("외부 API는 tools/를
  거친다")과 같은 이유로 API 라우트가 아니라 여기에 이 책임을 둔다.

★ 왜 supabase-py가 아니라 httpx 직접 호출인가: 신규 런타임 의존성을
  팀 공유 requirements.txt에 추가하지 않기 위해서고, 무엇보다
  respx(이미 있음, tests/test_gemini_llm.py가 쓰는 패턴)로 그대로
  테스트 가능하기 때문이다.
"""

import hashlib

import httpx

from app.config.settings import settings


class SupabaseUnavailable(RuntimeError):
    """AUTH_ENABLED=False거나 필요한 키가 없다. 호출부는 503으로 번역한다."""


class SupabaseError(RuntimeError):
    """PostgREST가 2xx가 아닌 응답을 줬다."""

    def __init__(self, status_code: int, body: str):
        self.status_code = status_code
        self.body = body
        super().__init__(f"Supabase 오류 {status_code}: {body}")


def _base_headers(prefer: str | None = None) -> dict:
    if not settings.supabase_ready:
        raise SupabaseUnavailable("Supabase가 설정되지 않았습니다.")
    headers = {
        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def _client() -> httpx.Client:
    return httpx.Client(
        base_url=f"{settings.SUPABASE_URL}/rest/v1", timeout=settings.SUPABASE_TIMEOUT_SEC
    )


def _check(r: httpx.Response) -> httpx.Response:
    if r.status_code >= 400:
        raise SupabaseError(r.status_code, r.text[:500])
    return r


def idea_key_for(keyword_id: str, platform: str, type_: str, name: str) -> str:
    """저장할 아이디어의 안정적인 중복판정 키를 서버가 계산한다(클라이언트가
    보낸 값을 그대로 믿지 않는다). keyword_id가 없는 옛 데이터(이관분)는
    이름만으로 만든다 — 이 경우 dedupe 정확도가 낮아지는 건 감수한다."""
    if keyword_id:
        raw = f"{keyword_id}|{platform}|{type_}|{name}"
    else:
        raw = f"legacy|{name}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:24]


# ── 관심 키워드 ───────────────────────────────────────────────────

def list_saved_keywords(user_id: str) -> list[dict]:
    with _client() as c:
        r = _check(c.get(
            "/saved_keywords",
            headers=_base_headers(),
            params={"user_id": f"eq.{user_id}", "order": "created_at.desc"},
        ))
        return r.json()


def upsert_saved_keyword(user_id: str, keyword_id: str, name: str, category: str, payload: dict) -> dict:
    with _client() as c:
        r = _check(c.post(
            "/saved_keywords",
            headers=_base_headers(prefer="resolution=merge-duplicates,return=representation"),
            params={"on_conflict": "user_id,keyword_id"},
            json=[{
                "user_id": user_id, "keyword_id": keyword_id, "name": name,
                "category": category, "payload": payload,
            }],
        ))
        rows = r.json()
        return rows[0] if rows else {}


def delete_saved_keyword(user_id: str, keyword_id: str) -> None:
    with _client() as c:
        _check(c.delete(
            "/saved_keywords", headers=_base_headers(),
            params={"user_id": f"eq.{user_id}", "keyword_id": f"eq.{keyword_id}"},
        ))


# ── 관심 아이디어 ─────────────────────────────────────────────────

def list_saved_ideas(user_id: str) -> list[dict]:
    with _client() as c:
        r = _check(c.get(
            "/saved_ideas",
            headers=_base_headers(),
            params={"user_id": f"eq.{user_id}", "order": "created_at.desc"},
        ))
        return r.json()


def upsert_saved_idea(
    user_id: str, idea_key: str, keyword_id: str, keyword_name: str,
    name: str, platform: str, type_: str, period: str, payload: dict,
) -> dict:
    with _client() as c:
        r = _check(c.post(
            "/saved_ideas",
            headers=_base_headers(prefer="resolution=merge-duplicates,return=representation"),
            params={"on_conflict": "user_id,idea_key"},
            json=[{
                "user_id": user_id, "idea_key": idea_key, "keyword_id": keyword_id,
                "keyword_name": keyword_name, "name": name, "platform": platform,
                "type": type_, "period": period, "payload": payload,
            }],
        ))
        rows = r.json()
        return rows[0] if rows else {}


def patch_saved_idea(user_id: str, idea_key: str, patch: dict) -> dict | None:
    """patch: {"payload": ..., "period": ...} 중 있는 것만. 대상이 없으면 None."""
    with _client() as c:
        r = _check(c.patch(
            "/saved_ideas",
            headers=_base_headers(prefer="return=representation"),
            params={"user_id": f"eq.{user_id}", "idea_key": f"eq.{idea_key}"},
            json=patch,
        ))
        rows = r.json()
        return rows[0] if rows else None


def delete_saved_idea(user_id: str, idea_key: str) -> None:
    with _client() as c:
        _check(c.delete(
            "/saved_ideas", headers=_base_headers(),
            params={"user_id": f"eq.{user_id}", "idea_key": f"eq.{idea_key}"},
        ))


# ── 새로고침 쿼터 (원자적 RPC — db/001_auth_library_quota.sql 참고) ──

def get_refresh_quota(user_id: str, keyword_id: str, default_limit: int) -> dict:
    """소비하지 않고 현재 상태만 본다 — 새로고침 버튼을 그릴 때, 그리고
    캐시 variant를 정할 때 쓴다. 행이 아직 없으면(한 번도 새로고침 안
    했으면) used=0으로 본다."""
    with _client() as c:
        r = _check(c.get(
            "/idea_refresh_quota",
            headers=_base_headers(),
            params={
                "user_id": f"eq.{user_id}", "keyword_id": f"eq.{keyword_id}",
                "select": "used,quota_limit",
            },
        ))
        rows = r.json()
        if rows:
            return {"used": rows[0]["used"], "limit": rows[0]["quota_limit"]}
        return {"used": 0, "limit": default_limit}


def consume_refresh_quota(user_id: str, keyword_id: str, limit: int) -> dict:
    """returns {"o_allowed": bool, "o_used": int, "o_limit": int}."""
    with _client() as c:
        r = _check(c.post(
            "/rpc/consume_refresh_quota",
            headers=_base_headers(),
            json={"p_user": user_id, "p_keyword": keyword_id, "p_limit": limit},
        ))
        rows = r.json()
        return rows[0] if rows else {"o_allowed": False, "o_used": 0, "o_limit": limit}


def release_refresh_quota(user_id: str, keyword_id: str) -> None:
    with _client() as c:
        _check(c.post(
            "/rpc/release_refresh_quota",
            headers=_base_headers(),
            json={"p_user": user_id, "p_keyword": keyword_id},
        ))
