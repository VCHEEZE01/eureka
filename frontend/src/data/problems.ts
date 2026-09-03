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
    relatedProblemIds: ['p-onboarding-docs', 'p-status-report'],
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
    relatedProblemIds: ['p-handoff', 'p-status-report'],
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
  {
    id: 'p-invest-start-trust',
    title: '소액으로 투자를 시작하려는데 무엇을 믿어야 할지 모르겠다',
    oneLiner:
      '유튜브와 커뮤니티마다 추천 종목이 달라서 결국 아무것도 시작하지 못한다.',
    category: '재테크/금융',
    description:
      '정보가 없어서가 아니라 서로 다른 말을 하는 정보가 너무 많아 무엇을 근거로 판단해야 할지 모른다는 이야기가 반복된다. 소액 투자를 시도했다가 손실을 본 뒤 판단 기준부터 다시 찾는 경우도 많다.',
    context:
      '사회초년생이나 재테크를 처음 시작하는 사람이 유튜브·커뮤니티·지인 추천 사이에서 무엇을 따라야 할지 고르는 시점에 나타난다.',
    evidence: [
      {
        id: 'e-invest-start-trust-1',
        summary:
          '유튜브에서 추천한 종목과 커뮤니티 글이 정반대 의견이라 결국 아무것도 사지 못했다는 후기.',
        sourceId: 's-invest-community',
        postedAt: '2025-11-09',
      },
      {
        id: 'e-invest-start-trust-2',
        summary:
          '증권사 앱을 깔아도 용어부터 이해가 안 돼 결국 지인에게 대신 물어봤다는 글.',
        sourceId: 's-app-review',
        postedAt: '2025-12-06',
      },
      {
        id: 'e-invest-start-trust-3',
        summary:
          '소액으로 시작했다가 손실을 보고 나서야 애초에 무엇을 근거로 샀는지 스스로도 설명하지 못한다는 자각.',
        excerpt: '"그냥 남들 따라 샀다"',
        sourceId: 's-work-forum',
        postedAt: '2026-01-14',
      },
      {
        id: 'e-invest-start-trust-4',
        summary:
          '재테크 강의를 결제했지만 결국 강사가 추천하는 상품을 사라는 이야기였다는 불만.',
        sourceId: 's-social',
        postedAt: '2026-02-02',
      },
    ],
    sources: [
      { id: 's-invest-community', name: '재테크 커뮤니티 C', platform: '커뮤니티', caseCount: 34 },
      { id: 's-work-forum', name: '직장인 포럼 B', platform: '커뮤니티', caseCount: 26 },
      { id: 's-app-review', name: '앱스토어 리뷰', platform: '리뷰', caseCount: 19 },
      { id: 's-social', name: '소셜 타임라인', platform: '소셜', caseCount: 15 },
    ],
    caseCount: 101,
    relatedProblemIds: ['p-spending-review', 'p-subscription-waste'],
    updatedAt: '2026-02-12',
  },
  {
    id: 'p-spending-review',
    title: '돈은 나갔는데 어디에 썼는지는 월말에야 안다',
    oneLiner:
      '카드 명세서를 받아보고 나서야 이번 달에 뭘 샀는지 기억을 되짚는다.',
    category: '재테크/금융',
    description:
      '가계부 앱을 깔아도 결국 손으로 항목을 나누는 일이 귀찮아 며칠 쓰다 만다는 이야기가 반복된다. 소비를 줄이고 싶어도 무엇에 얼마를 쓰는지 모르니 어디부터 줄여야 할지도 알 수 없다는 토로가 나온다.',
    context:
      '여러 카드와 간편결제를 섞어 쓰며 소비 내역이 한곳에 모이지 않는 사람들에게서 관찰된다.',
    evidence: [
      {
        id: 'e-spending-review-1',
        summary:
          '가계부 앱을 세 번째 깔았지만 이번에도 일주일을 못 넘기고 손을 놨다는 후기.',
        sourceId: 's-app-review',
        postedAt: '2025-11-16',
      },
      {
        id: 'e-spending-review-2',
        summary:
          '카드사 앱, 간편결제, 현금 지출이 각각 따로 남아 있어 합쳐서 보려면 일일이 옮겨 적어야 한다는 불만.',
        sourceId: 's-invest-community',
        postedAt: '2025-12-10',
      },
      {
        id: 'e-spending-review-3',
        summary:
          '이번 달에 뭘 그렇게 많이 샀는지 명세서를 보고도 절반은 기억이 안 난다는 글.',
        excerpt: '"이게 다 뭐였지"',
        sourceId: 's-social',
        postedAt: '2026-01-05',
      },
      {
        id: 'e-spending-review-4',
        summary:
          '자동으로 카테고리를 나눠주는 기능을 써도 분류가 틀려서 결국 다시 손으로 고친다는 리뷰.',
        sourceId: 's-work-forum',
        postedAt: '2026-01-29',
      },
    ],
    sources: [
      { id: 's-app-review', name: '앱스토어 리뷰', platform: '리뷰', caseCount: 28 },
      { id: 's-invest-community', name: '재테크 커뮤니티 C', platform: '커뮤니티', caseCount: 22 },
      { id: 's-social', name: '소셜 타임라인', platform: '소셜', caseCount: 17 },
      { id: 's-work-forum', name: '직장인 포럼 B', platform: '커뮤니티', caseCount: 14 },
    ],
    caseCount: 88,
    relatedProblemIds: ['p-invest-start-trust', 'p-subscription-waste'],
    updatedAt: '2026-02-06',
  },
  {
    id: 'p-exercise-dropout',
    title: '운동을 시작해도 2~3주면 어김없이 끊긴다',
    oneLiner:
      '헬스장 등록까지는 매번 하는데 한 달을 채워 다닌 적은 손에 꼽는다.',
    category: '건강',
    description:
      '의지 부족이라기보다 처음 몇 주가 지나면 굳이 오늘 가야 할 이유가 사라진다는 이야기가 반복된다. 같이 갈 사람이나 확인해주는 사람이 없으면 흐지부지되는 패턴이 공통적으로 나타난다.',
    context:
      '새해나 여름을 앞두고 운동을 새로 시작했다가 3주 안팎에서 그만두는 사람들에게서 관찰된다.',
    evidence: [
      {
        id: 'e-exercise-dropout-1',
        summary:
          '헬스장 3개월권을 끊어놓고 실제로 간 건 열 번도 안 된다는 자조.',
        sourceId: 's-health-community',
        postedAt: '2025-11-11',
      },
      {
        id: 'e-exercise-dropout-2',
        summary:
          '운동 기록 앱에 출석 스트릭이 끊기는 순간부터 아예 앱을 열지 않게 된다는 후기.',
        sourceId: 's-app-review',
        postedAt: '2025-12-15',
      },
      {
        id: 'e-exercise-dropout-3',
        summary:
          '혼자 하는 운동은 아파도 안 아파도 그만두는 핑계가 똑같이 쉽다는 글.',
        excerpt: '"핑계가 너무 쉽다"',
        sourceId: 's-social',
        postedAt: '2026-01-08',
      },
      {
        id: 'e-exercise-dropout-4',
        summary:
          '같이 다니던 친구가 그만두자 본인도 자연스럽게 발길이 끊겼다는 사례.',
        sourceId: 's-work-forum',
        postedAt: '2026-02-01',
      },
    ],
    sources: [
      { id: 's-health-community', name: '건강 커뮤니티 G', platform: '커뮤니티', caseCount: 30 },
      { id: 's-app-review', name: '앱스토어 리뷰', platform: '리뷰', caseCount: 24 },
      { id: 's-social', name: '소셜 타임라인', platform: '소셜', caseCount: 18 },
      { id: 's-work-forum', name: '직장인 포럼 B', platform: '커뮤니티', caseCount: 12 },
    ],
    caseCount: 90,
    relatedProblemIds: ['p-symptom-search-anxiety', 'p-skill-learning-followthrough'],
    updatedAt: '2026-02-09',
  },
  {
    id: 'p-symptom-search-anxiety',
    title: '증상을 검색할수록 불안만 커지고 판단은 못 한다',
    oneLiner:
      '두통 하나를 검색해도 최악의 케이스부터 눈에 들어와 병원에 가야 할지 그냥 넘겨도 될지 판단이 안 된다.',
    category: '건강',
    description:
      '증상 검색 결과가 가벼운 원인부터 심각한 질환까지 뒤섞여 나와 정작 지금 상황에 맞는 판단은 스스로 하기 어렵다는 이야기가 반복된다. 병원에 가기도, 안 가기도 애매한 채로 며칠을 검색만 반복하는 경우가 많다.',
    context:
      '야간이나 주말처럼 병원 진료가 어려운 시간에 몸에 이상을 느낀 사람들에게서 관찰된다.',
    evidence: [
      {
        id: 'e-symptom-search-anxiety-1',
        summary:
          '검색할수록 무서운 결과만 상단에 떠서 오히려 잠을 설쳤다는 후기.',
        sourceId: 's-health-community',
        postedAt: '2025-11-24',
      },
      {
        id: 'e-symptom-search-anxiety-2',
        summary:
          '같은 증상인데 사이트마다 원인 설명이 달라 결국 아무 결론도 못 내렸다는 글.',
        excerpt: '"다 다른 소리만"',
        sourceId: 's-social',
        postedAt: '2025-12-20',
      },
      {
        id: 'e-symptom-search-anxiety-3',
        summary:
          '응급실에 가야 할 정도인지 아닌지 판단이 안 서서 결국 날이 밝을 때까지 기다렸다는 사례.',
        sourceId: 's-news',
        postedAt: '2026-01-17',
      },
    ],
    sources: [
      { id: 's-health-community', name: '건강 커뮤니티 G', platform: '커뮤니티', caseCount: 26 },
      { id: 's-social', name: '소셜 타임라인', platform: '소셜', caseCount: 20 },
      { id: 's-news', name: '뉴스 댓글', platform: '뉴스', caseCount: 9 },
    ],
    caseCount: 61,
    relatedProblemIds: ['p-exercise-dropout', 'p-baby-safety-search'],
    updatedAt: '2026-01-30',
  },
  {
    id: 'p-pet-vet-cost',
    title: '동물병원에 가기 전에는 비용이 얼마 나올지 알 수 없다',
    oneLiner:
      '진료비를 물어봐도 병원마다 달라서 막상 가보기 전까지는 얼마가 나올지 짐작도 안 된다.',
    category: '반려동물',
    description:
      '동물병원은 진료비 공시 의무가 사람 병원만큼 촘촘하지 않아 병원별 편차를 미리 알기 어렵다는 이야기가 반복된다. 급한 상황일수록 비용을 따질 여유가 없어 나중에 청구서를 받고 놀라는 경우가 많다.',
    context:
      '반려동물이 갑자기 아파 처음 가는 병원을 급하게 찾아야 하는 보호자들에게서 관찰된다.',
    evidence: [
      {
        id: 'e-pet-vet-cost-1',
        summary:
          '같은 검사를 다른 병원 두 곳에 문의했더니 비용이 두 배 넘게 차이가 났다는 후기.',
        sourceId: 's-pet-cafe',
        postedAt: '2025-11-13',
      },
      {
        id: 'e-pet-vet-cost-2',
        summary:
          '수술이 필요하다는 말을 듣고서야 예상 비용을 들었는데 예산을 훨씬 넘어 당황했다는 글.',
        excerpt: '"그제야 금액을 들었다"',
        sourceId: 's-social',
        postedAt: '2025-12-08',
      },
      {
        id: 'e-pet-vet-cost-3',
        summary:
          '진료비가 부담스러워 병원을 옮겨 다니다 보니 진료 기록이 나뉘어 오히려 진단이 늦어졌다는 사례.',
        sourceId: 's-pet-cafe',
        postedAt: '2026-01-11',
      },
      {
        id: 'e-pet-vet-cost-4',
        summary:
          '펫보험이 있어도 실제 청구 가능한 항목인지 병원에서 바로 확인해주지 않아 답답했다는 리뷰.',
        sourceId: 's-app-review',
        postedAt: '2026-02-03',
      },
    ],
    sources: [
      { id: 's-pet-cafe', name: '반려동물 카페 E', platform: '커뮤니티', caseCount: 33 },
      { id: 's-social', name: '소셜 타임라인', platform: '소셜', caseCount: 21 },
      { id: 's-app-review', name: '앱스토어 리뷰', platform: '리뷰', caseCount: 16 },
    ],
    caseCount: 77,
    relatedProblemIds: ['p-pet-alone-anxiety', 'p-repair-quote-trust'],
    updatedAt: '2026-02-07',
  },
  {
    id: 'p-pet-alone-anxiety',
    title: '혼자 두고 나온 반려동물이 괜찮은지 확인할 방법이 없다',
    oneLiner:
      '출근하고 나면 집에 혼자 있는 아이가 잘 있는지 퇴근 전까지는 알 도리가 없다.',
    category: '반려동물',
    description:
      'CCTV를 설치해도 계속 들여다볼 수 없어 결국 확인하지 않게 된다는 이야기가 반복된다. 특히 분리불안이 있는 반려동물을 키우는 경우 외출 자체가 불안 요소가 된다는 토로가 많다.',
    context:
      '반려동물을 혼자 두고 장시간 외출·출근해야 하는 1인 가구, 맞벌이 가구에서 관찰된다.',
    evidence: [
      {
        id: 'e-pet-alone-anxiety-1',
        summary:
          '홈캠을 설치했지만 알림이 너무 자주 와서 결국 알림을 꺼버렸다는 후기.',
        sourceId: 's-app-review',
        postedAt: '2025-11-27',
      },
      {
        id: 'e-pet-alone-anxiety-2',
        summary:
          '분리불안이 있는 강아지가 짖는 소리 때문에 이웃에게 항의를 받고 나서야 상태를 알았다는 사례.',
        sourceId: 's-pet-cafe',
        postedAt: '2025-12-22',
      },
      {
        id: 'e-pet-alone-anxiety-3',
        summary:
          '회의 중에도 홈캠을 몰래 켜서 확인하다 정작 업무에 집중하지 못했다는 글.',
        excerpt: '"몰래 계속 켜봄"',
        sourceId: 's-social',
        postedAt: '2026-01-19',
      },
    ],
    sources: [
      { id: 's-app-review', name: '앱스토어 리뷰', platform: '리뷰', caseCount: 22 },
      { id: 's-pet-cafe', name: '반려동물 카페 E', platform: '커뮤니티', caseCount: 25 },
      { id: 's-social', name: '소셜 타임라인', platform: '소셜', caseCount: 13 },
    ],
    caseCount: 66,
    relatedProblemIds: ['p-pet-vet-cost', 'p-symptom-search-anxiety'],
    updatedAt: '2026-02-13',
  },
  {
    id: 'p-baby-safety-search',
    title: '아이에게 써도 되는지 매번 검색하는데 답이 제각각이다',
    oneLiner:
      '이유식 재료 하나, 로션 하나도 검색하면 된다는 글과 안 된다는 글이 동시에 나온다.',
    category: '육아',
    description:
      '육아 정보가 넘치지만 서로 다른 주장이 섞여 있어 결국 무엇을 믿어야 할지 부모가 다시 판단해야 한다는 이야기가 반복된다. 아이 건강과 직결된 문제라 잘못된 정보를 걸러내지 못하면 불안이 그대로 남는다는 토로가 많다.',
    context:
      '이유식, 육아용품, 상비약처럼 아이에게 처음 써보는 것을 결정해야 하는 초보 부모에게서 관찰된다.',
    evidence: [
      {
        id: 'e-baby-safety-search-1',
        summary:
          '같은 재료를 두고 어떤 글은 괜찮다 하고 어떤 글은 알레르기 위험이 있다고 해 결국 안 먹였다는 후기.',
        sourceId: 's-parenting-community',
        postedAt: '2025-11-06',
      },
      {
        id: 'e-baby-safety-search-2',
        summary:
          '맘카페마다 추천하는 로션 브랜드가 달라 몇 개를 사서 번갈아 발라봤다는 글.',
        sourceId: 's-social',
        postedAt: '2025-12-13',
      },
      {
        id: 'e-baby-safety-search-3',
        summary:
          '상비약 용량을 검색해도 사이트마다 기준이 달라 결국 약국에 다시 전화로 물어봤다는 사례.',
        excerpt: '"결국 다시 전화함"',
        sourceId: 's-parenting-community',
        postedAt: '2026-01-21',
      },
      {
        id: 'e-baby-safety-search-4',
        summary:
          '육아 정보 앱을 여러 개 깔아도 서로 다른 답을 주니 신뢰가 안 간다는 리뷰.',
        sourceId: 's-app-review',
        postedAt: '2026-02-05',
      },
    ],
    sources: [
      { id: 's-parenting-community', name: '육아 커뮤니티 D', platform: '커뮤니티', caseCount: 36 },
      { id: 's-social', name: '소셜 타임라인', platform: '소셜', caseCount: 24 },
      { id: 's-app-review', name: '앱스토어 리뷰', platform: '리뷰', caseCount: 15 },
    ],
    caseCount: 83,
    relatedProblemIds: ['p-parenting-milestone-worry', 'p-symptom-search-anxiety'],
    updatedAt: '2026-02-15',
  },
  {
    id: 'p-parenting-milestone-worry',
    title: '우리 아이만 늦는 건지 비교할 기준이 없다',
    oneLiner: '또래 아이는 벌써 한다는데 우리 아이는 아직이라 매번 불안해진다.',
    category: '육아',
    description:
      '발달 시기는 개인차가 크다는 걸 알면서도 비교할 만한 기준이 마땅치 않아 다른 부모 이야기에 더 흔들린다는 토로가 반복된다. 병원에 물어보기엔 애매하고 검색하기엔 정보가 흩어져 있어 판단을 미루는 경우가 많다.',
    context:
      '또래 아이를 키우는 부모들의 이야기나 맘카페 글을 접하며 발달 속도를 비교하게 되는 영유아 부모에게서 관찰된다.',
    evidence: [
      {
        id: 'e-parenting-milestone-worry-1',
        summary:
          '옆집 아이는 벌써 말을 하는데 우리 아이는 아직이라는 이야기를 듣고 하루 종일 불안했다는 후기.',
        sourceId: 's-parenting-community',
        postedAt: '2025-11-30',
      },
      {
        id: 'e-parenting-milestone-worry-2',
        summary:
          '발달 체크리스트를 검색해도 기준이 제각각이라 어디에 맞춰야 할지 몰랐다는 글.',
        excerpt: '"기준이 다 다름"',
        sourceId: 's-social',
        postedAt: '2025-12-27',
      },
      {
        id: 'e-parenting-milestone-worry-3',
        summary:
          '병원에 물어보기엔 너무 사소한 것 같아 미루다가 몇 달을 그냥 흘려보냈다는 사례.',
        sourceId: 's-news',
        postedAt: '2026-01-24',
      },
    ],
    sources: [
      { id: 's-parenting-community', name: '육아 커뮤니티 D', platform: '커뮤니티', caseCount: 29 },
      { id: 's-social', name: '소셜 타임라인', platform: '소셜', caseCount: 19 },
      { id: 's-news', name: '뉴스 댓글', platform: '뉴스', caseCount: 10 },
    ],
    caseCount: 64,
    relatedProblemIds: ['p-baby-safety-search', 'p-career-feedback'],
    updatedAt: '2026-02-01',
  },
  {
    id: 'p-moving-sequence',
    title: '이사 절차를 매번 처음부터 다시 찾아본다',
    oneLiner:
      '전입신고부터 확정일자까지 순서를 몇 번을 이사해도 매번 검색부터 다시 시작한다.',
    category: '주거/생활',
    description:
      '이사가 자주 있는 일이 아니다 보니 절차를 기억하지 못하고, 검색해도 지역이나 계약 형태에 따라 안내가 달라 헷갈린다는 이야기가 반복된다. 순서를 놓치면 불이익이 생길 수 있어 매번 처음부터 확인해야 한다는 부담이 크다.',
    context:
      '전세·월세 계약을 새로 하거나 거주지를 옮기는 세입자, 특히 이사 경험이 적은 사람들에게서 관찰된다.',
    evidence: [
      {
        id: 'e-moving-sequence-1',
        summary:
          '전입신고를 며칠 늦게 해서 확정일자 효력이 늦어질 뻔했다는 후기.',
        sourceId: 's-realty-forum',
        postedAt: '2025-11-17',
      },
      {
        id: 'e-moving-sequence-2',
        summary:
          '관리비 정산, 인터넷 이전 설치, 우편물 주소 변경 같은 자잘한 일을 하나씩 빠뜨렸다가 뒤늦게 챙겼다는 글.',
        sourceId: 's-social',
        postedAt: '2025-12-11',
      },
      {
        id: 'e-moving-sequence-3',
        summary:
          '지자체마다 안내 페이지가 달라 검색해도 지금 내 상황에 맞는 절차인지 확신이 안 섰다는 토로.',
        excerpt: '"이게 내 경우 맞나"',
        sourceId: 's-realty-forum',
        postedAt: '2026-01-06',
      },
      {
        id: 'e-moving-sequence-4',
        summary:
          '이사 체크리스트 앱을 써도 지역 특성이 반영 안 돼 결국 따로 검색을 병행했다는 리뷰.',
        sourceId: 's-app-review',
        postedAt: '2026-01-26',
      },
    ],
    sources: [
      { id: 's-realty-forum', name: '부동산 포럼 F', platform: '커뮤니티', caseCount: 27 },
      { id: 's-social', name: '소셜 타임라인', platform: '소셜', caseCount: 18 },
      { id: 's-app-review', name: '앱스토어 리뷰', platform: '리뷰', caseCount: 12 },
    ],
    caseCount: 63,
    relatedProblemIds: ['p-repair-quote-trust', 'p-home-maintenance'],
    updatedAt: '2026-02-04',
  },
  {
    id: 'p-repair-quote-trust',
    title: '집 수리 견적이 적정한지 판단할 근거가 없다',
    oneLiner: '업체 견적을 받아도 이게 비싼 건지 적당한 건지 비교할 방법이 없다.',
    category: '주거/생활',
    description:
      '같은 수리를 두고 업체마다 부르는 금액이 크게 달라 무엇을 기준으로 골라야 할지 모른다는 이야기가 반복된다. 급하게 고쳐야 하는 상황일수록 비교할 시간이 없어 일단 아는 업체나 처음 연락한 업체로 결정하는 경우가 많다.',
    context:
      '누수, 보일러 고장처럼 급하게 수리 업체를 불러야 하는 자가·임차 거주자에게서 관찰된다.',
    evidence: [
      {
        id: 'e-repair-quote-trust-1',
        summary:
          '같은 누수 수리를 두고 업체마다 견적이 두 배 넘게 차이가 나 무엇이 정상 가격인지 알 수 없었다는 후기.',
        sourceId: 's-realty-forum',
        postedAt: '2025-12-02',
      },
      {
        id: 'e-repair-quote-trust-2',
        summary:
          '견적서에 항목만 나열되어 있고 단가 근거가 없어 그대로 믿고 결제할 수밖에 없었다는 글.',
        excerpt: '"근거가 아예 없음"',
        sourceId: 's-social',
        postedAt: '2026-01-13',
      },
      {
        id: 'e-repair-quote-trust-3',
        summary:
          '급하게 부른 업체가 수리 후 추가 비용을 요구해 처음 견적과 최종 금액이 달랐다는 사례.',
        sourceId: 's-news',
        postedAt: '2026-02-08',
      },
    ],
    sources: [
      { id: 's-realty-forum', name: '부동산 포럼 F', platform: '커뮤니티', caseCount: 24 },
      { id: 's-social', name: '소셜 타임라인', platform: '소셜', caseCount: 16 },
      { id: 's-news', name: '뉴스 댓글', platform: '뉴스', caseCount: 11 },
    ],
    caseCount: 58,
    relatedProblemIds: ['p-moving-sequence', 'p-pet-vet-cost'],
    updatedAt: '2026-02-10',
  },
];
