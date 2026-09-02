import { ButtonLink, Card } from '@/components/ui';
import { getAllProblems } from '@/lib/data';

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

  return (
    <div className="space-y-16">
      <section className="pt-6">
        <p className="text-sm font-semibold text-brand">팀 목욕중</p>
        <h1 className="kr-text mt-3 text-4xl font-extrabold leading-tight sm:text-5xl">
          만들 능력은 있는데
          <br />
          무엇을 만들지 모를 때
        </h1>
        <p className="kr-text mt-5 max-w-2xl text-lg text-muted">
          유레카는 세상의 불편 데이터를 모아 실제로 존재하는 문제를 보여주고,
          그 근거를 확인한 뒤 만들 수 있는 아이디어까지 연결합니다.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <ButtonLink href="/problems">문제 둘러보기</ButtonLink>
          <ButtonLink href="/library" variant="secondary">
            보관함 보기
          </ButtonLink>
        </div>
        <p className="mt-4 text-sm text-muted">
          로그인 없이 문제와 기본 아이디어까지 볼 수 있습니다.
        </p>
      </section>

      <section>
        <h2 className="text-xl font-bold">지금 이렇게 작동합니다</h2>
        <ol className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((item, index) => (
            <li key={item.step}>
              <Card className="h-full">
                <span className="text-xs font-bold text-brand">
                  0{index + 1}
                </span>
                <p className="mt-2 font-semibold">{item.step}</p>
                <p className="kr-text mt-2 text-sm text-muted">{item.body}</p>
              </Card>
            </li>
          ))}
        </ol>
      </section>

      <section>
        <h2 className="text-xl font-bold">지금 담긴 데이터</h2>
        <div className="mt-5 grid gap-4 sm:grid-cols-3">
          <Card>
            <p className="text-sm text-muted">수집된 문제</p>
            <p className="mt-1 text-3xl font-extrabold tabular-nums">
              {problems.length}
            </p>
          </Card>
          <Card>
            <p className="text-sm text-muted">관련 사례</p>
            <p className="mt-1 text-3xl font-extrabold tabular-nums">
              {totalCases}
            </p>
          </Card>
          <Card>
            <p className="text-sm text-muted">활성 카테고리</p>
            <p className="mt-1 text-3xl font-extrabold tabular-nums">3</p>
          </Card>
        </div>
        <p className="kr-text mt-4 text-sm text-muted">
          프로토타입 단계라 위 수치는 시연용 샘플 데이터 기준입니다.
        </p>
      </section>
    </div>
  );
}
