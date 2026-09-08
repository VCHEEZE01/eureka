'use client';

/**
 * 1. 랜딩 (PRD F01)
 * 차별점을 빠르게 이해시키고 탐색으로 유도한다.
 * 비로그인 이용 가능하며 첫 화면에서 회원가입을 강제하지 않는다.
 */

import { ArrowRight, Combine, Quote, SlidersHorizontal } from 'lucide-react';
import { AppShell } from '@/components/AppShell';
import { Body, Caption, PageTitle, PrototypeNotice, SectionTitle, buttonClass } from '@/components/ui';
import { problems } from '@/data/problems';
import { NavLink } from '@/lib/nav';

export function LandingScreen() {
  const preview = problems.slice(0, 3);

  return (
    <AppShell>
      {/* 히어로 — DESIGN.md 6절: 그라데이션은 히어로에서만 아주 옅게 */}
      <section className="bg-[linear-gradient(180deg,#F2F8FF_0%,#FAFCFF_55%,#FFFFFF_100%)]">
        <div className="shell py-24 md:py-32">
          <div className="prose-width flex flex-col gap-6">
            <span className="inline-flex w-fit items-center h-8 px-3 rounded-lg bg-blue-light text-blue text-[13px] font-semibold">
              근거 데이터 기반 문제 발견
            </span>
            <PageTitle>
              무엇을 만들지 정하는 데
              <br />
              시간을 쓰지 않도록
            </PageTitle>
            <Body className="text-[17px]">
              유레카는 실제 사람들이 남긴 불편에서 문제를 찾아내고, 그 근거를 함께 보여준 뒤
              실행할 수 있는 아이디어로 연결합니다. 만들 능력은 있는데 방향이 없는 사람을 위한
              서비스입니다.
            </Body>
            <div className="flex flex-wrap gap-3 pt-2">
              <NavLink to="/onboarding" className={buttonClass('primary')}>
                문제 둘러보기
                <ArrowRight size={18} aria-hidden />
              </NavLink>
              <NavLink to="/problems" className={buttonClass('secondary')}>
                바로 문제 목록 보기
              </NavLink>
            </div>
            <PrototypeNotice />
          </div>
        </div>
      </section>

      {/* 작동 방식 */}
      <section className="shell py-24">
        <SectionTitle>어떻게 작동하나요</SectionTitle>
        <div className="grid gap-6 md:grid-cols-3 mt-10">
          <HowItem
            icon={<Quote size={20} aria-hidden />}
            step="01"
            title="근거부터 봅니다"
            body="커뮤니티·리뷰·뉴스에서 모은 실제 불편을 요약해 보여줍니다. 문제마다 어디서 몇 건이 나왔는지 함께 확인할 수 있습니다."
          />
          <HowItem
            icon={<Combine size={20} aria-hidden />}
            step="02"
            title="문제를 조합합니다"
            body="여러 문제를 골라 하나의 새로운 문제정의로 묶습니다. 개별 문제보다 범위가 넓어 해결 방식도 달라집니다."
          />
          <HowItem
            icon={<SlidersHorizontal size={20} aria-hidden />}
            step="03"
            title="내 조건에 맞춥니다"
            body="만들 형태와 타깃, 쓸 수 있는 리소스를 넣으면 그 조건에 맞게 아이디어를 좁혀줍니다."
          />
        </div>
      </section>

      {/* 미리보기 */}
      <section className="shell pb-24">
        <div className="flex items-end justify-between gap-4 mb-8">
          <div>
            <SectionTitle>지금 발견된 문제</SectionTitle>
            <Caption className="mt-2">근거가 모인 순서로 보여줍니다.</Caption>
          </div>
          <NavLink to="/problems" className="text-[15px] font-semibold text-blue whitespace-nowrap">
            전체 보기 →
          </NavLink>
        </div>

        <ul className="flex flex-col">
          {preview.map((p) => (
            <li key={p.id} className="border-t border-border last:border-b">
              <NavLink to={`/problems/${p.id}`} className="flex items-start gap-6 py-6 group">
                <div className="flex-1 min-w-0">
                  <p className="text-[13px] text-blue font-semibold mb-1.5">{p.category}</p>
                  <p className="text-[20px] font-semibold kr mb-1.5 group-hover:text-blue transition-colors">
                    {p.title}
                  </p>
                  <Body className="line-clamp-2">{p.oneLiner}</Body>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-[20px] font-bold">{p.caseCount}</p>
                  <Caption>관련 사례</Caption>
                </div>
              </NavLink>
            </li>
          ))}
        </ul>
      </section>
    </AppShell>
  );
}

function HowItem({
  icon,
  step,
  title,
  body,
}: {
  icon: React.ReactNode;
  step: string;
  title: string;
  body: string;
}) {
  return (
    <div className="flex flex-col gap-3">
      <span className="inline-flex items-center justify-center w-11 h-11 rounded-[12px] bg-blue-light text-blue">
        {icon}
      </span>
      <p className="text-[13px] font-semibold text-text-muted">{step}</p>
      <p className="text-[20px] font-semibold kr">{title}</p>
      <Body>{body}</Body>
    </div>
  );
}
