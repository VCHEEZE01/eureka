import type { Problem } from '@/lib/types';

/**
 * 시연용 문제 시드 데이터.
 * 실제 수집 파이프라인(F00) 연결 전까지 사용하는 샘플이며,
 * 수치는 "수집 데이터 내 관련 사례 수" 기준의 가상값이다.
 */
export const problems: Problem[] = [
  {
    id: 'p-handoff',
    title: '회의에서 정해진 내용이 실제 할 일로 이어지지 않는다',
    oneLiner:
      '회의록은 쌓이는데 누가 무엇을 언제까지 하는지는 끝나고 나면 아무도 모른다.',
    category: '생산성/업무',
    description:
      '회의 자체보다 회의 이후가 문제라는 이야기가 반복된다. 결론은 문서에 남지만 담당자와 기한이 붙지 않아 다음 회의에서 같은 안건을 다시 논의하게 된다.',
    context:
      '회의록 도구와 이슈 트래커가 분리되어 있고, 회의록을 할 일로 옮기는 일이 특정 한 사람의 수작업에 의존하는 팀에서 주로 관찰된다.',
    evidence: [
      {
        id: 'e-handoff-1',
        summary:
          '회의록은 매번 남기지만 액션 아이템을 트래커로 옮기는 사람이 정해져 있지 않아 결국 아무도 옮기지 않는다는 토로.',
        sourceId: 's-dev-community',
        postedAt: '2025-11-18',
      },
      {
        id: 'e-handoff-2',
        summary:
          '지난주 회의에서 이미 결론이 난 안건을 이번 주에 다시 논의하게 되는 일이 반복된다는 후기.',
        excerpt: '"같은 얘기를 3주째 하고 있다"',
        sourceId: 's-work-forum',
        postedAt: '2025-12-02',
      },
      {
        id: 'e-handoff-3',
        summary:
          '자동 요약 기능을 켜 두어도 요약이 길기만 하고 담당자·기한이 빠져 있어 그대로는 쓸 수 없다는 리뷰.',
        sourceId: 's-app-review',
        postedAt: '2025-12-14',
      },
      {
        id: 'e-handoff-4',
        summary:
          '회의 직후에는 기억하지만 이틀만 지나도 무엇을 하기로 했는지 확인하러 문서를 다시 뒤진다는 글.',
        sourceId: 's-social',
        postedAt: '2026-01-09',
      },
    ],
    sources: [
      { id: 's-dev-community', name: '개발자 커뮤니티 A', platform: '커뮤니티', caseCount: 41 },
      { id: 's-work-forum', name: '직장인 포럼 B', platform: '커뮤니티', caseCount: 33 },
      { id: 's-app-review', name: '협업툴 스토어 리뷰', platform: '리뷰', caseCount: 27 },
      { id: 's-social', name: '소셜 타임라인', platform: '소셜', caseCount: 18 },
    ],
    caseCount: 119,
    relatedProblemIds: ['p-onboarding-docs'],
    updatedAt: '2026-02-11',
  },
  {
    id: 'p-onboarding-docs',
    title: '신규 입사자가 물어봐야만 알 수 있는 정보가 너무 많다',
    oneLiner:
      '문서는 있는데 흩어져 있어서, 결국 옆자리 사람에게 묻는 것이 가장 빠른 방법이 된다.',
    category: '생산성/업무',
    description:
      '온보딩 문서가 없는 것이 아니라 최신 문서가 어느 것인지 알 수 없는 상태가 문제로 지목된다. 신규 입사자와 기존 구성원 양쪽 모두의 시간이 소모된다.',
    context:
      '위키·드라이브·메신저 고정글에 정보가 나뉘어 있고, 문서 갱신 담당이 명시되지 않은 조직에서 반복된다.',
    evidence: [
      {
        id: 'e-onboarding-1',
        summary:
          '입사 첫 주에 가장 많이 한 일이 "이거 어디서 봐요?"를 묻는 것이었다는 회고.',
        sourceId: 's-work-forum',
        postedAt: '2025-10-27',
      },
      {
        id: 'e-onboarding-2',
        summary:
          '검색해서 나온 문서가 2년 전 버전이라 그대로 따라 했다가 잘못된 환경을 세팅했다는 사례.',
        sourceId: 's-dev-community',
        postedAt: '2025-12-19',
      },
      {
        id: 'e-onboarding-3',
        summary:
          '같은 질문을 분기마다 새 입사자에게 반복 답변하느라 시니어의 시간이 계속 소모된다는 글.',
        sourceId: 's-social',
        postedAt: '2026-01-22',
      },
    ],
    sources: [
      { id: 's-dev-community', name: '개발자 커뮤니티 A', platform: '커뮤니티', caseCount: 29 },
      { id: 's-work-forum', name: '직장인 포럼 B', platform: '커뮤니티', caseCount: 35 },
      { id: 's-social', name: '소셜 타임라인', platform: '소셜', caseCount: 14 },
    ],
    caseCount: 78,
    relatedProblemIds: ['p-handoff'],
    updatedAt: '2026-02-03',
  },
];
