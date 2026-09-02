import Link from 'next/link';
import { ArrowRightIcon, EvidenceIcon, SparkIcon } from '@/components/icons';
import { ButtonLink } from '@/components/ui';
import { countByCategory, getAllProblems } from '@/lib/data';
import { CATEGORIES, sourceCount } from '@/lib/types';

/** F01 랜딩. 비로그인으로 이용 가능하며 회원가입을 강제하지 않는다. */

const STEPS = [
  {
    step: '문제 발견',
    body: '커뮤니티·리뷰·뉴스·소셜에서 모은 실제 불편에서 문제 후보를 추립니다.',
  },
  {
    step: '근거 확인',
    body: '어떤 사용자가 어떤 상황에서 불편을 말했는지 원문 요약과 출처로 확인합니다.',
  },
  {
    step: '아이디어 확인',
    body: '하나의 문제에서 서로 다른 해결 방향의 아이디어를 봅니다.',
  },
  {
    step: '개인화',
    body: '만들고 싶은 형태·타깃·리소스를 반영해 내 조건에 맞게 좁힙니다.',
  },
];

export default function LandingPage() {
  const problems = getAllProblems();
  const totalCases = problems.reduce((sum, p) => sum + p.caseCount, 0);
  const activeCategories = CATEGORIES.filter(
    (category) => countByCategory(category) > 0,
  ).length;
  const totalSources = new Set(
    problems.flatMap((problem) => problem.sources.map((source) => source.name)),
  ).size;
  const featured = [...problems]
    .sort((a, b) => b.caseCount - a.caseCount)
    .slice(0, 3);

  return (
    <div className="space-y-20 sm:space-y-28">
      <section className="aurora -mt-2 pt-6">
        <p className="rise text-sm text-brand">
          <span className="display tracking-[0.2em] uppercase">Eureka</span>
          <span className="kr-text ml-2 font-semibold">팀 목욕중</span>
        </p>
        <h1 className="kr-text rise rise-1 mt-4 text-4xl leading-[1.15] font-extrabold tracking-tight text-balance sm:text-6xl">
          만들 능력은 있는데
          <br />
          <span className="text-brand-strong">무엇을 만들지</span> 모를 때
        </h1>
        <p className="kr-text rise rise-2 mt-6 max-w-2xl text-lg leading-relaxed text-muted">
          유레카는 세상의 불편 데이터를 모아 실제로 존재하는 문제를 보여주고, 그 근거를
          확인한 뒤 만들 수 있는 아이디어까지 연결합니다.
        </p>

        <div className="rise rise-3 mt-9 flex flex-wrap items-center gap-3">
          <ButtonLink href="/problems" size="lg">
            문제 둘러보기
            <ArrowRightIcon />
          </ButtonLink>
          <ButtonLink href="/mypage" variant="secondary" size="lg">
            마이페이지
          </ButtonLink>
        </div>
        <p className="kr-text rise rise-4 mt-4 text-sm text-muted">
          로그인 없이 문제와 기본 아이디어까지 볼 수 있습니다.
        </p>

        {/* 수치를 카드로 나누는 대신 한 줄 띠로 묶어 히어로의 마침표 역할을 하게 한다. */}
        <dl className="rise rise-4 mt-12 grid grid-cols-2 gap-px overflow-hidden rounded-2xl border border-border bg-border sm:grid-cols-4">
          <HeroStat label="수집된 문제" value={problems.length} unit="건" />
          <HeroStat label="관련 사례" value={totalCases} unit="건" />
          <HeroStat label="출처" value={totalSources} unit="곳" />
          <HeroStat label="활성 카테고리" value={activeCategories} unit="개" />
        </dl>
        <p className="kr-text mt-3 text-xs text-muted">
          프로토타입 단계라 위 수치는 시연용 샘플 데이터 기준입니다.
        </p>
      </section>

      <section>
        <h2 className="kr-text text-xl font-bold tracking-tight">지금 이렇게 작동합니다</h2>
        <p className="kr-text mt-2 max-w-2xl text-sm text-muted">
          네 단계 모두 &ldquo;이 말이 어디서 나왔는지&rdquo;를 잃지 않는 것이 원칙입니다.
        </p>
        <ol className="mt-8 grid gap-x-6 gap-y-8 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((item, index) => (
            <li key={item.step} className="relative">
              {/* 단계 사이를 잇는 가는 선. 마지막 항목에는 붙이지 않는다. */}
              {index < STEPS.length - 1 && (
                <span
                  aria-hidden
                  className="absolute top-3.5 left-9 hidden h-px w-[calc(100%-1rem)] bg-border lg:block"
                />
              )}
              <span className="relative flex size-7 items-center justify-center rounded-full border border-brand/40 bg-brand-soft text-xs font-bold text-brand-strong">
                {index + 1}
              </span>
              <p className="kr-text mt-4 font-bold">{item.step}</p>
              <p className="kr-text mt-2 text-sm leading-relaxed text-muted">{item.body}</p>
            </li>
          ))}
        </ol>
      </section>

      {featured.length > 0 && (
        <section>
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="kr-text text-xl font-bold tracking-tight">
                지금 사례가 가장 많은 문제
              </h2>
              <p className="kr-text mt-2 text-sm text-muted">
                수집된 불편 사례 수 기준입니다.
              </p>
            </div>
            <ButtonLink href="/problems" variant="ghost" size="sm">
              전체 보기
              <ArrowRightIcon />
            </ButtonLink>
          </div>
          <ol className="mt-6 divide-y divide-border overflow-hidden rounded-2xl border border-border bg-surface">
            {featured.map((problem, index) => (
              <li key={problem.id}>
                <Link
                  href={`/problems/${problem.id}`}
                  className="focus-ring group flex items-start gap-4 px-5 py-4 transition-colors hover:bg-surface-muted"
                >
                  <span className="display mt-0.5 w-6 shrink-0 text-lg text-brand tabular-nums">
                    {String(index + 1).padStart(2, '0')}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="kr-text block font-semibold group-hover:text-brand-strong">
                      {problem.title}
                    </span>
                    <span className="kr-text mt-1 block text-sm text-muted">
                      {problem.oneLiner}
                    </span>
                  </span>
                  <span className="shrink-0 pt-0.5 text-right text-xs text-muted tabular-nums">
                    {problem.caseCount}건
                    <span className="block">{sourceCount(problem)}곳</span>
                  </span>
                </Link>
              </li>
            ))}
          </ol>
        </section>
      )}

      {/* 색 규칙을 처음부터 설명해 두면 상세 화면의 초록/보라 구분이 바로 읽힌다. */}
      <section className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-2xl border border-evidence/25 bg-evidence-soft/45 p-5">
          <p className="flex items-center gap-2 font-bold text-evidence">
            <EvidenceIcon />
            실제 수집 데이터
          </p>
          <p className="kr-text mt-2 text-sm leading-relaxed text-muted">
            초록으로 표시된 영역은 실제로 수집된 사용자 불편과 그 출처입니다. 원문 링크가
            허용된 경우 함께 보여줍니다.
          </p>
        </div>
        <div className="rounded-2xl border border-ai/25 bg-ai-soft/45 p-5">
          <p className="flex items-center gap-2 font-bold text-ai">
            <SparkIcon />
            AI 생성 설명
          </p>
          <p className="kr-text mt-2 text-sm leading-relaxed text-muted">
            보라로 표시된 영역은 AI가 쓴 해석과 아이디어입니다. 시장성이나 성공 가능성이
            검증된 결과가 아닙니다.
          </p>
        </div>
      </section>
    </div>
  );
}

function HeroStat({
  label,
  value,
  unit,
}: {
  label: string;
  value: number;
  unit: string;
}) {
  return (
    <div className="bg-surface px-4 py-4">
      <dt className="kr-text text-xs text-muted">{label}</dt>
      <dd className="display mt-1 text-3xl tabular-nums">
        {value}
        <span className="ml-0.5 font-sans text-sm font-medium text-muted">{unit}</span>
      </dd>
    </div>
  );
}
