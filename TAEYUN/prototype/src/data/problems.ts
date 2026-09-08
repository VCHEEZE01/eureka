/**
 * 프로토타입용 문제 데이터.
 *
 * 주의: 전부 화면 확인을 위한 가상 데이터다.
 * 실제 수집 파이프라인(PRD F00)과 데이터 소스는 아직 TBD 상태이며,
 * 여기 수치는 실제로 수집된 값이 아니다.
 *
 * PRD 8절을 지키기 위해 출처는 매체 유형까지만 두고
 * 실존 사이트명·원문 링크는 넣지 않는다.
 */

import type { Problem } from '@/lib/types';

export const problems: Problem[] = [
  /* ── 생산성/업무 ─────────────────────────────────────────────── */
  {
    id: 'p1',
    title: '회의 결론이 어디에 적혔는지 아무도 모른다',
    oneLiner: '회의는 했는데 결정 사항이 채팅·문서·머릿속에 흩어져 다시 논의하게 된다.',
    category: '생산성/업무',
    description:
      '회의 자체보다 회의 이후가 문제로 지목된다. 결정된 내용이 한곳에 정리되지 않아, 며칠 뒤 같은 안건을 다시 꺼내거나 서로 다르게 기억한 채 일이 진행된다.',
    context:
      '기록 담당자가 정해져 있지 않거나, 정해져 있어도 정리 시점이 회의 직후가 아닌 경우에 반복된다. 도구를 여러 개 쓰는 팀일수록 결론이 흩어지는 폭이 커진다.',
    evidence: [
      {
        id: 'p1-e1',
        summary: '회의에서 정한 걸 각자 다르게 기억해 2주 뒤 같은 논의를 반복했다는 경험 공유',
        excerpt: '분명 지난번에 정했는데 왜 또 이 얘기를 하고 있는지 모르겠어요',
        sourceId: 'p1-s1',
        postedAt: '2026-08-21',
      },
      {
        id: 'p1-e2',
        summary: '회의록을 쓰긴 쓰는데 아무도 다시 안 읽어서 쓰는 의미를 못 느낀다는 토로',
        sourceId: 'p1-s1',
        postedAt: '2026-08-14',
      },
      {
        id: 'p1-e3',
        summary: '결정 사항이 메신저 스레드에 묻혀 검색으로도 못 찾겠다는 질문 글',
        excerpt: '위로 한참 올려봐도 어디서 정해진 건지 못 찾겠네요',
        sourceId: 'p1-s2',
        postedAt: '2026-07-30',
      },
      {
        id: 'p1-e4',
        summary: '협업 도구 리뷰에서 "회의록 기능은 있는데 결론만 따로 보는 화면이 없다"는 지적',
        sourceId: 'p1-s3',
        postedAt: '2026-07-11',
      },
    ],
    sources: [
      { id: 'p1-s1', name: '직장인 커뮤니티', kind: '커뮤니티', caseCount: 71 },
      { id: 'p1-s2', name: '개발자 Q&A', kind: '커뮤니티', caseCount: 34 },
      { id: 'p1-s3', name: '협업툴 앱 리뷰', kind: '리뷰', caseCount: 22 },
    ],
    caseCount: 127,
    relatedIds: ['p2', 'p3'],
    updatedAt: '2026-08-28',
  },
  {
    id: 'p2',
    title: '업무 도구가 너무 많아 어디에 뭘 적었는지 잊는다',
    oneLiner: '메모, 할 일, 문서, 메신저가 따로 놀아 찾는 데만 시간을 쓴다.',
    category: '생산성/업무',
    description:
      '도구를 줄이려는 시도 자체가 또 하나의 일이 되어버린다는 반응이 반복된다. 통합 도구로 옮겨도 팀원 일부가 기존 도구를 계속 쓰면서 결국 분산 상태로 돌아간다.',
    context:
      '개인이 아니라 팀 단위 합의가 필요한 문제라 혼자 정리해도 해결되지 않는다. 도구 전환 비용이 체감상 크게 느껴지는 시점에 특히 자주 언급된다.',
    evidence: [
      {
        id: 'p2-e1',
        summary: '같은 내용을 메모앱과 문서에 두 번 적어두고 나중에 어느 쪽이 최신인지 모르게 됐다는 사례',
        excerpt: '두 군데 다 있는데 내용이 조금씩 달라서 뭐가 맞는지 모르겠어요',
        sourceId: 'p2-s1',
        postedAt: '2026-08-19',
      },
      {
        id: 'p2-e2',
        summary: '도구 통합을 시도했다가 팀원 절반이 안 따라와서 되돌린 후기',
        sourceId: 'p2-s1',
        postedAt: '2026-08-02',
      },
      {
        id: 'p2-e3',
        summary: '"검색을 여러 앱에서 각각 해야 한다"는 불편을 리뷰에서 반복 지적',
        sourceId: 'p2-s2',
        postedAt: '2026-07-25',
      },
    ],
    sources: [
      { id: 'p2-s1', name: '직장인 커뮤니티', kind: '커뮤니티', caseCount: 58 },
      { id: 'p2-s2', name: '생산성 앱 리뷰', kind: '리뷰', caseCount: 41 },
      { id: 'p2-s3', name: '생산성 블로그', kind: '블로그', caseCount: 15 },
    ],
    caseCount: 114,
    relatedIds: ['p1', 'p3'],
    updatedAt: '2026-08-25',
  },
  {
    id: 'p3',
    title: '반복 보고서를 매번 손으로 다시 만든다',
    oneLiner: '주간·월간 보고의 형식은 같은데 매번 자료를 새로 모아 붙여넣는다.',
    category: '생산성/업무',
    description:
      '자동화하고 싶다는 욕구는 뚜렷한데, 데이터가 여러 곳에 흩어져 있고 형식이 조금씩 달라 손을 못 대는 상태가 길게 이어진다.',
    context:
      '엑셀·스프레드시트를 쓰는 실무자에게서 특히 자주 나온다. 개발 지식이 없어 자동화 도구 진입에 부담을 느낀다는 언급이 함께 붙는다.',
    evidence: [
      {
        id: 'p3-e1',
        summary: '매주 같은 표를 다시 만드는 데 반나절이 걸린다는 호소',
        excerpt: '숫자만 바뀌는데 매번 처음부터 만들고 있어요',
        sourceId: 'p3-s1',
        postedAt: '2026-08-17',
      },
      {
        id: 'p3-e2',
        summary: '자동화 도구를 알아봤지만 어디서 시작할지 몰라 포기했다는 글',
        sourceId: 'p3-s1',
        postedAt: '2026-08-05',
      },
      {
        id: 'p3-e3',
        summary: '보고서 양식이 부서마다 달라 통합이 어렵다는 지적',
        sourceId: 'p3-s2',
        postedAt: '2026-07-19',
      },
    ],
    sources: [
      { id: 'p3-s1', name: '직장인 커뮤니티', kind: '커뮤니티', caseCount: 63 },
      { id: 'p3-s2', name: '실무 노하우 블로그', kind: '블로그', caseCount: 26 },
    ],
    caseCount: 89,
    relatedIds: ['p1', 'p2'],
    updatedAt: '2026-08-22',
  },

  /* ── 커리어/자기계발 ─────────────────────────────────────────── */
  {
    id: 'p4',
    title: '공부한 걸 정리해두지만 다시 찾아보지 않는다',
    oneLiner: '강의·아티클을 열심히 저장하는데 저장함이 무덤이 된다.',
    category: '커리어/자기계발',
    description:
      '저장 자체는 쉬운데 꺼내 쓰는 계기가 없다는 점이 공통으로 지적된다. 나중에 볼 것이라 믿고 쌓아두지만 다시 열어보는 비율은 매우 낮다고 스스로 진단한다.',
    context:
      '북마크·읽기 목록·노트 앱을 함께 쓰는 사람에게서 두드러진다. 저장한 사실 자체를 잊는 경우도 많다.',
    evidence: [
      {
        id: 'p4-e1',
        summary: '읽기 목록에 300개 넘게 쌓였는데 실제로 다시 읽은 건 손에 꼽는다는 고백',
        excerpt: '저장할 땐 꼭 읽을 것 같은데 한 번도 안 열어봤어요',
        sourceId: 'p4-s1',
        postedAt: '2026-08-23',
      },
      {
        id: 'p4-e2',
        summary: '노트를 정리하는 데 시간을 다 쓰고 정작 복습은 못 한다는 반성 글',
        sourceId: 'p4-s1',
        postedAt: '2026-08-09',
      },
      {
        id: 'p4-e3',
        summary: '"저장은 되는데 다시 알려주는 기능이 없다"는 앱 리뷰 지적',
        sourceId: 'p4-s2',
        postedAt: '2026-07-28',
      },
      {
        id: 'p4-e4',
        summary: '강의를 다 듣고도 남는 게 없다는 느낌에 대한 토론 스레드',
        sourceId: 'p4-s3',
        postedAt: '2026-07-14',
      },
    ],
    sources: [
      { id: 'p4-s1', name: '자기계발 커뮤니티', kind: '커뮤니티', caseCount: 82 },
      { id: 'p4-s2', name: '노트 앱 리뷰', kind: '리뷰', caseCount: 37 },
      { id: 'p4-s3', name: '학습 소셜', kind: '소셜', caseCount: 24 },
    ],
    caseCount: 143,
    relatedIds: ['p5', 'p6'],
    updatedAt: '2026-08-30',
  },
  {
    id: 'p5',
    title: '내가 한 일을 나중에 설명하지 못한다',
    oneLiner: '이직·평가 시점에 지난 성과를 기억해내지 못해 처음부터 뒤진다.',
    category: '커리어/자기계발',
    description:
      '기록을 남기지 않아서가 아니라, 남긴 기록이 성과 형태가 아니어서 쓸 수 없다는 진단이 반복된다. 업무 로그는 있는데 "무엇을 개선했는가"로 번역하는 과정이 통째로 빠져 있다.',
    context:
      '연말 평가나 이직 준비를 시작하는 시점에 집중적으로 언급된다. 몇 달 전 일은 이미 세부가 사라진 뒤라 복원 비용이 크다.',
    evidence: [
      {
        id: 'p5-e1',
        summary: '이력서를 쓰려는데 작년에 뭘 했는지 기억이 안 난다는 글',
        excerpt: '분명 바빴는데 막상 적으려니까 쓸 게 없어요',
        sourceId: 'p5-s1',
        postedAt: '2026-08-26',
      },
      {
        id: 'p5-e2',
        summary: '평가 자료를 만들려고 1년 치 메신저를 거슬러 올라갔다는 경험',
        sourceId: 'p5-s1',
        postedAt: '2026-08-11',
      },
      {
        id: 'p5-e3',
        summary: '업무 기록은 있지만 성과 문장으로 바꾸는 게 제일 어렵다는 반응',
        sourceId: 'p5-s2',
        postedAt: '2026-07-22',
      },
    ],
    sources: [
      { id: 'p5-s1', name: '커리어 커뮤니티', kind: '커뮤니티', caseCount: 69 },
      { id: 'p5-s2', name: '이직 정보 블로그', kind: '블로그', caseCount: 31 },
    ],
    caseCount: 100,
    relatedIds: ['p4', 'p6'],
    updatedAt: '2026-08-27',
  },
  {
    id: 'p6',
    title: '사이드 프로젝트를 시작만 하고 끝내지 못한다',
    oneLiner: '만들 능력은 있는데 매번 초반에 멈추고 다음 아이템으로 넘어간다.',
    category: '커리어/자기계발',
    description:
      '기술 문제보다 "이걸 계속할 이유"가 사라지는 게 원인으로 지목된다. 초기에 반응을 확인할 방법이 없어 혼자 만들다 확신을 잃는 흐름이 반복된다.',
    context:
      '유레카의 타깃 사용자와 가장 가까운 문제다. 아이템 선정 단계에서 이미 확신이 약한 채로 시작한 경우 이탈이 더 빠르다.',
    evidence: [
      {
        id: 'p6-e1',
        summary: '시작한 프로젝트가 폴더에만 열 개 넘게 쌓였다는 자조 섞인 글',
        excerpt: '만들다 만 게 너무 많아서 이제 새로 시작하기가 무서워요',
        sourceId: 'p6-s1',
        postedAt: '2026-08-29',
      },
      {
        id: 'p6-e2',
        summary: '"이게 진짜 필요한 건지 모르겠어서" 중단했다는 회고',
        sourceId: 'p6-s1',
        postedAt: '2026-08-13',
      },
      {
        id: 'p6-e3',
        summary: '아이템을 정하는 데만 몇 주를 쓰다 지쳤다는 토로',
        sourceId: 'p6-s2',
        postedAt: '2026-08-01',
      },
      {
        id: 'p6-e4',
        summary: '완성해도 쓸 사람이 없을 것 같아 동기가 떨어진다는 반응',
        sourceId: 'p6-s3',
        postedAt: '2026-07-16',
      },
    ],
    sources: [
      { id: 'p6-s1', name: '개발자 커뮤니티', kind: '커뮤니티', caseCount: 94 },
      { id: 'p6-s2', name: '메이커 소셜', kind: '소셜', caseCount: 45 },
      { id: 'p6-s3', name: '사이드프로젝트 블로그', kind: '블로그', caseCount: 19 },
    ],
    caseCount: 158,
    relatedIds: ['p4', 'p5'],
    updatedAt: '2026-09-01',
  },

  /* ── 라이프스타일 ────────────────────────────────────────────── */
  {
    id: 'p7',
    title: '냉장고에 뭐가 있는지 몰라 같은 재료를 또 산다',
    oneLiner: '장은 봤는데 결국 버리는 재료가 생기고, 필요한 건 빠져 있다.',
    category: '라이프스타일',
    description:
      '기록하는 앱은 많지만 "넣을 때마다 입력"이라는 부담 때문에 유지되지 않는다는 반응이 공통이다. 며칠만 안 적어도 실제와 어긋나 신뢰를 잃는다.',
    context:
      '1~2인 가구에서 특히 자주 언급된다. 소분 포장이 적어 남는 재료가 생기는 구조적 요인도 함께 지적된다.',
    evidence: [
      {
        id: 'p7-e1',
        summary: '같은 소스를 세 병째 사고 나서야 알았다는 경험담',
        excerpt: '냉장고 열어보고 사러 나가도 막상 마트에서는 기억이 안 나요',
        sourceId: 'p7-s1',
        postedAt: '2026-08-20',
      },
      {
        id: 'p7-e2',
        summary: '재고 관리 앱을 깔았지만 입력이 귀찮아 2주 만에 그만뒀다는 후기',
        sourceId: 'p7-s2',
        postedAt: '2026-08-06',
      },
      {
        id: 'p7-e3',
        summary: '유통기한을 지나 버리는 양이 아깝다는 반복 언급',
        sourceId: 'p7-s1',
        postedAt: '2026-07-27',
      },
    ],
    sources: [
      { id: 'p7-s1', name: '생활 커뮤니티', kind: '커뮤니티', caseCount: 76 },
      { id: 'p7-s2', name: '가계부 앱 리뷰', kind: '리뷰', caseCount: 33 },
    ],
    caseCount: 109,
    relatedIds: ['p8', 'p9'],
    updatedAt: '2026-08-24',
  },
  {
    id: 'p8',
    title: '구독 서비스가 몇 개인지, 얼마 나가는지 모른다',
    oneLiner: '안 쓰는 구독이 자동 결제되고 있는데 해지 시점을 놓친다.',
    category: '라이프스타일',
    description:
      '결제 내역을 모아 보는 수단이 카드사별로 흩어져 있어 전체 합계를 파악하기 어렵다는 점이 핵심으로 지목된다. 해지 경로가 서비스마다 달라 미루게 되는 흐름도 반복된다.',
    context:
      '무료 체험 후 자동 전환된 항목에서 특히 자주 발생한다. 금액이 소액이라 발견이 늦어지는 경향이 있다.',
    evidence: [
      {
        id: 'p8-e1',
        summary: '1년 넘게 안 쓴 서비스가 결제되고 있었다는 사례',
        excerpt: '카드 내역 보다가 이게 뭐지 하고 찾아보니 재작년에 가입한 거였어요',
        sourceId: 'p8-s1',
        postedAt: '2026-08-18',
      },
      {
        id: 'p8-e2',
        summary: '구독 관리 앱이 일부 카드만 연동돼 반쪽짜리라는 리뷰 지적',
        sourceId: 'p8-s2',
        postedAt: '2026-08-04',
      },
      {
        id: 'p8-e3',
        summary: '해지 버튼을 찾기 어려워 미뤘다는 반응',
        sourceId: 'p8-s1',
        postedAt: '2026-07-21',
      },
      {
        id: 'p8-e4',
        summary: '가족 계정과 개인 계정이 섞여 누가 낸 건지 모른다는 글',
        sourceId: 'p8-s3',
        postedAt: '2026-07-09',
      },
    ],
    sources: [
      { id: 'p8-s1', name: '생활 커뮤니티', kind: '커뮤니티', caseCount: 88 },
      { id: 'p8-s2', name: '금융 앱 리뷰', kind: '리뷰', caseCount: 40 },
      { id: 'p8-s3', name: '소비 뉴스', kind: '뉴스', caseCount: 12 },
    ],
    caseCount: 140,
    relatedIds: ['p7', 'p9'],
    updatedAt: '2026-08-31',
  },
  {
    id: 'p9',
    title: '주말에 뭘 할지 정하다가 주말이 끝난다',
    oneLiner: '선택지는 넘치는데 결정을 못 해 결국 아무것도 안 하고 보낸다.',
    category: '라이프스타일',
    description:
      '정보가 부족해서가 아니라 너무 많아서 생기는 문제로 진단된다. 추천 서비스가 많지만 조건(거리·예산·동행)이 반영되지 않아 다시 직접 골라야 한다는 지적이 붙는다.',
    context:
      '둘 이상이 함께 정할 때 지연이 더 커진다. 서로 의견을 묻다가 시간이 지나 무산되는 흐름이 반복된다.',
    evidence: [
      {
        id: 'p9-e1',
        summary: '검색만 두 시간 하다 결국 집에 있었다는 글',
        excerpt: '찾다 보면 지쳐서 그냥 안 나가게 돼요',
        sourceId: 'p9-s1',
        postedAt: '2026-08-16',
      },
      {
        id: 'p9-e2',
        summary: '추천 목록이 광고 위주라 믿기 어렵다는 반응',
        sourceId: 'p9-s2',
        postedAt: '2026-08-03',
      },
      {
        id: 'p9-e3',
        summary: '동행자와 조건을 맞추는 과정이 제일 오래 걸린다는 언급',
        sourceId: 'p9-s1',
        postedAt: '2026-07-24',
      },
    ],
    sources: [
      { id: 'p9-s1', name: '생활 커뮤니티', kind: '커뮤니티', caseCount: 54 },
      { id: 'p9-s2', name: '장소 추천 리뷰', kind: '리뷰', caseCount: 29 },
    ],
    caseCount: 83,
    relatedIds: ['p7', 'p8'],
    updatedAt: '2026-08-19',
  },
];

export const problemsById = new Map(problems.map((p) => [p.id, p]));

export function getProblem(id: string): Problem | undefined {
  return problemsById.get(id);
}
