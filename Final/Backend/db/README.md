# db — Supabase 스키마

이 폴더의 `.sql` 파일을 **Supabase 대시보드 → SQL Editor** 에 붙여넣어 손으로 실행한다.

## 왜 Alembic 을 안 쓰나

이 프로젝트엔 ORM도, 마이그레이션 러너도, CI도 없고 환경은 하나뿐이다.
Alembic 을 붙이면 SQLAlchemy + Postgres 직결이 필요한데, Supabase 직결은
무료 플랜에서 IPv6 전용이라 많은 노트북·CI 에서 "Network is unreachable" 이
난다(우회하려면 Supavisor 풀러 설정이 또 붙는다). 백엔드는 PostgREST 를
`httpx` 로 부르므로 그 문제를 아예 만들지 않는다.

## 규칙

- 파일은 **멱등**하게 쓴다 (`create table if not exists`, `drop policy if exists` 후 `create policy`, `create or replace function`). 몇 번을 돌려도 안전해야 한다.
- **이미 실행한 파일을 고치지 않는다.** 스키마가 바뀌면 `002_*.sql` 을 새로 만든다. 수정하면 누가 어디까지 돌렸는지 알 수 없게 된다.

## 실행 순서

| 파일 | 내용 |
|---|---|
| `001_auth_library_quota.sql` | 보관함 2표(`saved_keywords`, `saved_ideas`) + 새로고침 쿼터 1표(`idea_refresh_quota`) + RLS + 원자적 쿼터 함수 2개 |

## 실행 후 확인

```sql
-- 첫 번째는 true, 두 번째는 false 가 나와야 한다 (키워드당 1회)
select * from public.consume_refresh_quota('00000000-0000-0000-0000-000000000001', 'test-kw', 1);
select * from public.consume_refresh_quota('00000000-0000-0000-0000-000000000001', 'test-kw', 1);

-- 확인 끝나면 시험 데이터 정리
delete from public.idea_refresh_quota where keyword_id = 'test-kw';
```

> 위 확인용 uuid 는 `auth.users` 에 없는 값이라 외래키 때문에 거부된다.
> 실제로는 **가입한 계정의 uuid**(Authentication → Users 에서 복사)를 쓸 것.
