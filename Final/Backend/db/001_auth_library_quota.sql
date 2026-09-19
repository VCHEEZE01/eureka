-- =====================================================================
-- 001 — 로그인 보관함 + 아이디어 새로고침 쿼터
--
-- 실행 방법: Supabase 대시보드 → SQL Editor → New query → 전체 붙여넣기 → Run
-- 이 파일은 몇 번을 돌려도 안전하다(멱등). 이미 있으면 건너뛴다.
--
-- ★ 이 파일을 고치지 마라. 스키마가 바뀌면 002_*.sql 을 새로 만든다.
--   이미 실행한 SQL 을 수정하면 누가 무엇까지 돌렸는지 알 수 없게 된다.
-- =====================================================================

create extension if not exists pgcrypto;

-- ── 1. 관심 키워드 ────────────────────────────────────────────────────
create table if not exists public.saved_keywords (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references auth.users(id) on delete cascade,
  keyword_id  text not null,
  name        text not null,
  category    text not null default '',
  -- 화면이 쓰는 나머지 필드(rate, aiSummary, platforms …)를 통째로 담는다.
  payload     jsonb not null default '{}'::jsonb,
  created_at  timestamptz not null default now(),
  constraint saved_keywords_uniq unique (user_id, keyword_id)
);

create index if not exists saved_keywords_user_created_idx
  on public.saved_keywords (user_id, created_at desc);

-- ── 2. 관심 아이디어 ──────────────────────────────────────────────────
-- payload 는 프론트의 camelCase 뷰 모양(toIdeaView 출력) 그대로 담는다.
-- 보관함 렌더가 순수 프론트라 snake_case 왕복은 양쪽에 변환기만 늘린다.
-- 정렬·필터·중복판정에 쓰는 것만 컬럼으로 승격했다.
create table if not exists public.saved_ideas (
  id           uuid primary key default gen_random_uuid(),
  user_id      uuid not null references auth.users(id) on delete cascade,
  idea_key     text not null,              -- 서버가 계산하는 안정 키
  keyword_id   text not null default '',
  keyword_name text not null default '',
  name         text not null,
  platform     text not null default '',   -- web | mobile
  type         text not null default '',   -- utility | fun | business
  period       text not null default 'day',-- 저장 당시 기간. 추천 AI가 기간별이라 필요.
  payload      jsonb not null,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now(),
  constraint saved_ideas_uniq unique (user_id, idea_key),
  constraint saved_ideas_period_chk check (period in ('day','week','month'))
);

create index if not exists saved_ideas_user_created_idx
  on public.saved_ideas (user_id, created_at desc);

-- ── 3. 새로고침 쿼터 ──────────────────────────────────────────────────
-- 키워드 하나당 1회. used 는 클라이언트가 절대 못 고친다(아래 RLS 참고).
create table if not exists public.idea_refresh_quota (
  user_id       uuid not null references auth.users(id) on delete cascade,
  keyword_id    text not null,
  used          integer not null default 0,
  quota_limit   integer not null default 1,
  first_used_at timestamptz,
  last_used_at  timestamptz,
  created_at    timestamptz not null default now(),
  primary key (user_id, keyword_id),
  constraint idea_refresh_quota_used_chk check (used >= 0 and used <= quota_limit)
);

-- =====================================================================
-- Row Level Security
-- =====================================================================
alter table public.saved_keywords     enable row level security;
alter table public.saved_ideas        enable row level security;
alter table public.idea_refresh_quota enable row level security;

drop policy if exists saved_keywords_own on public.saved_keywords;
create policy saved_keywords_own on public.saved_keywords
  for all to authenticated
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

drop policy if exists saved_ideas_own on public.saved_ideas;
create policy saved_ideas_own on public.saved_ideas
  for all to authenticated
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- ★ 쿼터는 읽기 정책만 만든다.
--   INSERT/UPDATE/DELETE 정책이 아예 없으므로 anon 도 authenticated 도
--   이 표를 고칠 수 없다. service_role(서버) 만 RLS 를 우회한다.
--   → used 는 구조적으로 위조 불가능하다.
drop policy if exists idea_refresh_quota_read_own on public.idea_refresh_quota;
create policy idea_refresh_quota_read_own on public.idea_refresh_quota
  for select to authenticated
  using (auth.uid() = user_id);

-- =====================================================================
-- 원자적 쿼터 소비 / 반납
-- =====================================================================

-- 검사와 차감을 한 문장으로 끝낸다.
-- 충돌 insert 가 행 잠금을 잡으므로 동시 요청(더블클릭)이 직렬화되고,
-- 진 쪽은 WHERE 가 거짓 → 0행 → FOUND=false → 거부된다.
-- SELECT 후 UPDATE 하는 방식의 경쟁 조건이 없고, uvicorn 워커가
-- 여러 개여도 성립한다(앱 레벨 잠금은 이 경우 무의미하다).
--
-- ⚠ OUT 파라미터에 o_ 를 붙인 이유: used / quota_limit 로 두면 테이블
--   컬럼과 이름이 부딪혀 "column reference is ambiguous" 오류가 난다.
create or replace function public.consume_refresh_quota(
  p_user    uuid,
  p_keyword text,
  p_limit   int default 1
)
returns table (o_allowed boolean, o_used int, o_limit int)
language plpgsql
security definer
set search_path = public
as $fn$
begin
  insert into public.idea_refresh_quota as q
      (user_id, keyword_id, used, quota_limit, first_used_at, last_used_at)
  values (p_user, p_keyword, 1, greatest(p_limit, 1), now(), now())
  on conflict (user_id, keyword_id) do update
     set used        = q.used + 1,
         quota_limit = greatest(q.quota_limit, p_limit),
         last_used_at = now()
   where q.used < greatest(q.quota_limit, p_limit)
  returning true, q.used, q.quota_limit
    into o_allowed, o_used, o_limit;

  -- WHERE 가 거짓이면 0행이 영향받아 FOUND 가 false 다 → 이미 다 쓴 경우.
  if not found then
    select false, q.used, q.quota_limit
      into o_allowed, o_used, o_limit
      from public.idea_refresh_quota q
     where q.user_id = p_user and q.keyword_id = p_keyword;
  end if;

  return next;
end;
$fn$;

-- LLM 이 죽어 폴백이 나갔거나 생성이 실패했을 때 돌려준다.
-- greatest(used-1, 0) 이라 두 번 불러도 음수로 내려가지 않는다.
create or replace function public.release_refresh_quota(
  p_user    uuid,
  p_keyword text
)
returns void
language sql
security definer
set search_path = public
as $fn$
  update public.idea_refresh_quota
     set used = greatest(used - 1, 0)
   where user_id = p_user and keyword_id = p_keyword;
$fn$;

-- 서버(service_role)만 부를 수 있게 한다.
revoke all on function public.consume_refresh_quota(uuid, text, int) from public, anon, authenticated;
revoke all on function public.release_refresh_quota(uuid, text)      from public, anon, authenticated;
grant execute on function public.consume_refresh_quota(uuid, text, int) to service_role;
grant execute on function public.release_refresh_quota(uuid, text)      to service_role;
