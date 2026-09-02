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
  {
    id: 'p-status-report',
    title: '여러 팀에 같은 진행 상황을 매번 새로 정리해서 보고한다',
    oneLiner:
      '슬랙에도 있고 이슈에도 있는 내용을 보고 양식에 맞춰 또 손으로 옮겨 적는다.',
    category: '생산성/업무',
    description:
      '진행 상황 자체는 이미 여러 도구에 흩어져 존재하지만, 보고서 양식에 맞춰 다시 정리하는 수작업이 반복된다는 이야기가 나온다.',
    context:
      '주간·월간 보고 양식이 고정되어 있고, 실제 작업 기록은 이슈 트래커·메신저·문서에 따로 남는 조직에서 관찰된다.',
    evidence: [
      {
        id: 'e-status-report-1',
        summary:
          '매주 같은 항목을 다른 도구에서 복사해 붙이는 데만 한 시간 넘게 쓴다는 토로.',
        sourceId: 's-work-forum',
        postedAt: '2025-11-14',
      },
      {
        id: 'e-status-report-2',
        summary:
          '보고서를 냈는데 정작 담당자에게 물어보면 상태가 이미 바뀌어 있어 신뢰도가 떨어진다는 후기.',
        sourceId: 's-dev-community',
        postedAt: '2025-12-05',
      },
      {
        id: 'e-status-report-3',
        summary:
          '보고 양식이 팀마다 달라 같은 내용을 형식만 바꿔 두 번 쓴다는 글.',
        excerpt: '"양식만 다른 재작업"',
        sourceId: 's-social',
        postedAt: '2026-01-02',
      },
      {
        id: 'e-status-report-4',
        summary:
          '자동 리포트 기능이 있는 도구를 써도 결국 코멘트를 손으로 덧붙여야 보고서가 된다는 리뷰.',
        sourceId: 's-app-review',
        postedAt: '2026-01-20',
      },
    ],
    sources: [
      { id: 's-work-forum', name: '직장인 포럼 B', platform: '커뮤니티', caseCount: 22 },
      { id: 's-dev-community', name: '개발자 커뮤니티 A', platform: '커뮤니티', caseCount: 19 },
      { id: 's-social', name: '소셜 타임라인', platform: '소셜', caseCount: 15 },
      { id: 's-app-review', name: '앱스토어 리뷰', platform: '리뷰', caseCount: 11 },
    ],
    caseCount: 92,
    relatedProblemIds: ['p-handoff', 'p-onboarding-docs'],
    updatedAt: '2026-01-25',
  },
  {
    id: 'p-career-feedback',
    title: '일을 잘하고 있는지 판단할 근거를 회사에서 주지 않는다',
    oneLiner: '연말 평가 전까지는 지금 방향이 맞는지 확인할 방법이 없다.',
    category: '커리어/자기계발',
    description:
      '정기 피드백 체계가 없거나 형식적이어서, 스스로 성장 방향을 가늠할 근거가 부족하다는 이야기가 반복된다.',
    context:
      '1:1 미팅이 비정기적이거나 형식적인 조직, 성과 평가가 연 1~2회로 몰려 있는 조직에서 주로 나타난다.',
    evidence: [
      {
        id: 'e-career-feedback-1',
        summary:
          '1:1이 잡혀도 잡담으로 끝나고 정작 업무 피드백은 듣지 못한다는 후기.',
        sourceId: 's-work-forum',
        postedAt: '2025-11-08',
      },
      {
        id: 'e-career-feedback-2',
        summary:
          '연말 평가에서 처음 듣는 지적이 있어 미리 알았다면 고칠 수 있었다는 아쉬움.',
        excerpt: '"왜 이제 말해주지"',
        sourceId: 's-dev-community',
        postedAt: '2025-12-11',
      },
      {
        id: 'e-career-feedback-3',
        summary:
          '동료에게 대신 물어봐야 내 일이 잘 되고 있는지 감이 온다는 글.',
        sourceId: 's-social',
        postedAt: '2026-01-05',
      },
      {
        id: 'e-career-feedback-4',
        summary:
          '이직을 준비하면서야 비로소 자신의 강점을 정리해봤다는 회고.',
        sourceId: 's-news',
        postedAt: '2026-01-28',
      },
    ],
    sources: [
      { id: 's-work-forum', name: '직장인 포럼 B', platform: '커뮤니티', caseCount: 31 },
      { id: 's-dev-community', name: '개발자 커뮤니티 A', platform: '커뮤니티', caseCount: 24 },
      { id: 's-social', name: '소셜 타임라인', platform: '소셜', caseCount: 17 },
      { id: 's-news', name: '뉴스 댓글', platform: '뉴스', caseCount: 9 },
    ],
    caseCount: 105,
    relatedProblemIds: ['p-job-search-tracking', 'p-skill-learning-followthrough'],
    updatedAt: '2026-02-02',
  },
  {
    id: 'p-job-search-tracking',
    title: '여러 곳에 지원하다 보면 내가 어디에 뭘 냈는지도 헷갈린다',
    oneLiner:
      '지원한 회사, 제출한 이력서 버전, 다음 일정이 이메일 속에 흩어져 있다.',
    category: '커리어/자기계발',
    description:
      '구직 활동이 길어질수록 지원 현황을 스스로 추적하는 부담이 커진다는 이야기가 나온다.',
    context:
      '여러 채용 플랫폼과 이메일을 동시에 쓰며 장기간 구직 활동을 하는 사람들에게서 관찰된다.',
    evidence: [
      {
        id: 'e-job-search-tracking-1',
        summary:
          '어느 회사에 어떤 버전의 이력서를 냈는지 기억이 안 나 재확인하느라 시간을 쓴다는 글.',
        sourceId: 's-dev-community',
        postedAt: '2025-11-22',
      },
      {
        id: 'e-job-search-tracking-2',
        summary:
          '면접 일정 두 개가 겹치는 걸 뒤늦게 알아 하나를 급히 조정했다는 후기.',
        excerpt: '"일정 겹친 걸 몰랐다"',
        sourceId: 's-work-forum',
        postedAt: '2025-12-27',
      },
      {
        id: 'e-job-search-tracking-3',
        summary:
          '탈락 통보를 못 받은 곳은 아직 진행 중인지 끝난 건지도 알 수 없다는 토로.',
        sourceId: 's-news',
        postedAt: '2026-02-01',
      },
    ],
    sources: [
      { id: 's-dev-community', name: '개발자 커뮤니티 A', platform: '커뮤니티', caseCount: 20 },
      { id: 's-work-forum', name: '직장인 포럼 B', platform: '커뮤니티', caseCount: 18 },
      { id: 's-news', name: '뉴스 댓글', platform: '뉴스', caseCount: 8 },
    ],
    caseCount: 64,
    relatedProblemIds: ['p-career-feedback', 'p-skill-learning-followthrough'],
    updatedAt: '2026-02-05',
  },
  {
    id: 'p-skill-learning-followthrough',
    title: '강의를 결제만 하고 끝까지 들은 적이 별로 없다',
    oneLiner: '초반 몇 개 챕터를 넘기지 못하고 다음 강의를 또 결제한다.',
    category: '커리어/자기계발',
    description:
      '학습 의지가 없어서라기보다, 시작한 학습을 이어갈 계기가 없어 흐지부지된다는 이야기가 반복된다.',
    context:
      '업무 외 시간에 온라인 강의나 책으로 자기계발을 시도하는 직장인들에게서 관찰된다.',
    evidence: [
      {
        id: 'e-skill-learning-followthrough-1',
        summary: '강의를 5개 사면 끝까지 듣는 건 1개도 안 된다는 자조 섞인 글.',
        sourceId: 's-social',
        postedAt: '2025-11-30',
      },
      {
        id: 'e-skill-learning-followthrough-2',
        summary:
          '진도율이 낮다는 알림을 받아도 그때뿐이고 다시 열지 않는다는 리뷰.',
        sourceId: 's-app-review',
        postedAt: '2025-12-18',
      },
      {
        id: 'e-skill-learning-followthrough-3',
        summary: '같이 들을 사람이 있었으면 끝까지 갔을 것 같다는 후기.',
        excerpt: '"혼자라 흐지부지"',
        sourceId: 's-work-forum',
        postedAt: '2026-01-10',
      },
      {
        id: 'e-skill-learning-followthrough-4',
        summary: '완강한 강의는 스터디나 마감이 있었던 것뿐이라는 회고.',
        sourceId: 's-dev-community',
        postedAt: '2026-01-31',
      },
    ],
    sources: [
      { id: 's-social', name: '소셜 타임라인', platform: '소셜', caseCount: 16 },
      { id: 's-app-review', name: '앱스토어 리뷰', platform: '리뷰', caseCount: 21 },
      { id: 's-work-forum', name: '직장인 포럼 B', platform: '커뮤니티', caseCount: 19 },
      { id: 's-dev-community', name: '개발자 커뮤니티 A', platform: '커뮤니티', caseCount: 14 },
    ],
    caseCount: 97,
    relatedProblemIds: ['p-career-feedback', 'p-job-search-tracking'],
    updatedAt: '2026-02-08',
  },
  {
    id: 'p-subscription-waste',
    title: '안 쓰는 구독을 해지 시점을 놓쳐서 계속 돈을 낸다',
    oneLiner: '무료 체험 끝나는 날짜를 까먹고 결제가 넘어가는 일이 반복된다.',
    category: '라이프스타일',
    description:
      '구독 자체를 관리하는 습관이 없어서가 아니라, 여러 서비스의 결제일이 흩어져 있어 놓치기 쉽다는 이야기가 나온다.',
    context:
      'OTT, 클라우드, 뉴스레터 등 다수의 정기 구독을 동시에 이용하는 사람들에게서 관찰된다.',
    evidence: [
      {
        id: 'e-subscription-waste-1',
        summary:
          '카드 명세서를 보고서야 몇 달째 안 쓰는 앱 구독료가 빠져나간 걸 알았다는 후기.',
        sourceId: 's-social',
        postedAt: '2025-11-05',
      },
      {
        id: 'e-subscription-waste-2',
        summary:
          '무료 체험 해지일을 캘린더에 적어두지 않으면 반드시 잊는다는 글.',
        excerpt: '"체험은 항상 놓친다"',
        sourceId: 's-news',
        postedAt: '2025-12-09',
      },
      {
        id: 'e-subscription-waste-3',
        summary:
          '해지하려고 들어가면 절차가 복잡해서 미루다가 또 결제됐다는 토로.',
        sourceId: 's-app-review',
        postedAt: '2026-01-03',
      },
      {
        id: 'e-subscription-waste-4',
        summary:
          '가족 구성원이 각자 구독해 겹치는 서비스를 뒤늦게 발견했다는 사례.',
        sourceId: 's-social',
        postedAt: '2026-01-27',
      },
    ],
    sources: [
      { id: 's-social', name: '소셜 타임라인', platform: '소셜', caseCount: 27 },
      { id: 's-news', name: '뉴스 댓글', platform: '뉴스', caseCount: 12 },
      { id: 's-app-review', name: '앱스토어 리뷰', platform: '리뷰', caseCount: 16 },
    ],
    caseCount: 80,
    relatedProblemIds: ['p-meal-planning', 'p-home-maintenance'],
    updatedAt: '2026-02-10',
  },
  {
    id: 'p-meal-planning',
    title: '매일 저녁 뭘 먹을지 정하는 데 생각보다 많은 에너지가 든다',
    oneLiner: '퇴근하고 나서 가장 먼저 하는 고민이 저녁 메뉴 정하기다.',
    category: '라이프스타일',
    description:
      '요리 실력이나 시간의 문제가 아니라, 매번 처음부터 메뉴를 정하는 결정 자체가 피로하다는 이야기가 반복된다.',
    context:
      '혼자 살거나 맞벌이로 매 끼니를 스스로 계획해야 하는 사람들에게서 관찰된다.',
    evidence: [
      {
        id: 'e-meal-planning-1',
        summary:
          '냉장고에 재료는 있는데 뭘 만들지 몰라 결국 배달을 시켰다는 후기.',
        sourceId: 's-social',
        postedAt: '2025-11-19',
      },
      {
        id: 'e-meal-planning-2',
        summary: '매주 같은 몇 가지 메뉴만 반복하다 질렸다는 글.',
        sourceId: 's-news',
        postedAt: '2025-12-24',
      },
      {
        id: 'e-meal-planning-3',
        summary:
          '장을 봐도 계획 없이 사서 결국 상해서 버리는 재료가 많다는 토로.',
        excerpt: '"장 본 게 다 버려짐"',
        sourceId: 's-app-review',
        postedAt: '2026-01-15',
      },
    ],
    sources: [
      { id: 's-social', name: '소셜 타임라인', platform: '소셜', caseCount: 24 },
      { id: 's-news', name: '뉴스 댓글', platform: '뉴스', caseCount: 10 },
      { id: 's-app-review', name: '앱스토어 리뷰', platform: '리뷰', caseCount: 13 },
    ],
    caseCount: 68,
    relatedProblemIds: ['p-subscription-waste', 'p-home-maintenance'],
    updatedAt: '2026-01-18',
  },
  {
    id: 'p-home-maintenance',
    title: '필터 교체나 정기 점검 시기를 늘 지나서야 알아차린다',
    oneLiner:
      '정수기 필터, 에어컨 청소, 보일러 점검 같은 건 문제가 생기고 나서야 떠올린다.',
    category: '라이프스타일',
    description:
      '관리 자체가 어려운 게 아니라 주기를 기억하고 있다가 알아서 챙기는 사람이 없다는 점이 반복해서 지적된다.',
    context:
      '1인 가구나 맞벌이 가구처럼 집안 유지관리를 챙길 여유가 적은 사람들에게서 관찰된다.',
    evidence: [
      {
        id: 'e-home-maintenance-1',
        summary:
          '필터 교체 스티커를 붙여놔도 유효기간이 지난 걸 한참 뒤에 발견한다는 글.',
        sourceId: 's-social',
        postedAt: '2025-12-01',
      },
      {
        id: 'e-home-maintenance-2',
        summary:
          '에어컨에서 냄새가 나기 시작하고 나서야 마지막 청소가 언제였는지 찾아본다는 후기.',
        sourceId: 's-news',
        postedAt: '2026-01-08',
      },
      {
        id: 'e-home-maintenance-3',
        summary:
          '보일러 점검 안내 문자가 와도 그때 시간이 안 돼서 미루다 잊는다는 토로.',
        excerpt: '"안내 와도 또 미룸"',
        sourceId: 's-app-review',
        postedAt: '2026-02-04',
      },
    ],
    sources: [
      { id: 's-social', name: '소셜 타임라인', platform: '소셜', caseCount: 19 },
      { id: 's-news', name: '뉴스 댓글', platform: '뉴스', caseCount: 11 },
      { id: 's-app-review', name: '앱스토어 리뷰', platform: '리뷰', caseCount: 14 },
    ],
    caseCount: 63,
    relatedProblemIds: ['p-subscription-waste', 'p-meal-planning'],
    updatedAt: '2026-02-14',
  },
];
