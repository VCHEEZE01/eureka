/**
 * 개발용 가상 데이터.
 *
 * 용도
 *   1. 백엔드 파이프라인(EvidenceAgent 등)이 아직 실행되지 않은 상태에서 화면을 만들 때
 *   2. 서버 없이 열리는 공유용 단일 HTML  ← 이건 영원히 이 데이터를 쓴다
 *
 * ★ 여기 숫자는 전부 손으로 쓴 예시다. 화면에 표시할 때 "예시 데이터"임을 밝힐 것
 *   (PrototypeNotice 참고).
 *
 * 타입은 api/types.ts(백엔드 계약)를 그대로 따른다. TAEYUN/prototype/src/data/problems.ts의
 * 문장 톤을 참고했지만 필드 구조는 새 계약(카테고리 5개·snake_case·ProblemSignals)을 따른다.
 *
 * 다양한 화면 상태를 확인할 수 있도록 의도적으로 섞었다:
 *   - p1, p6            : 표본이 풍부해 모든 분포가 정상적으로 보인다
 *   - p2 (age_labeled_count=2) : 연령 분포가 "표본 부족"으로 숨겨진다
 *   - p3 (role_labeled_count=1): 역할 분포가 "표본 부족"으로 숨겨진다
 *   - p4 (gender_labeled_count=0): 성별 분포가 "표본 부족"으로 숨겨진다
 *   - p1, p3            : undated_count > 0 (지식iN·카페 특성)
 *   - p1, p3, p5, p8    : mentioned_services 가 비어 있다
 *   - p2, p4, p6, p7    : mentioned_services 가 채워져 있다
 *   - 전 항목            : gate.passed = true (게시된 문제는 정의상 기준을 통과했다)
 */
import type { Idea, Problem } from '@/api/types';

export const problems: Problem[] = [
  /* ── 금융 ────────────────────────────────────────────────────── */
  {
    id: 'p1',
    title: '안 쓰는 구독이 몇 달째 자동 결제되고 있었다',
    one_liner: '결제 내역이 카드사별로 흩어져 있어 전체 구독 목록과 합계를 한눈에 못 본다.',
    category: '금융',
    description:
      '구독 서비스를 해지하지 않아서가 아니라, 결제 중인 구독이 몇 개인지 한곳에서 확인할 방법이 없어서 방치되는 경우가 반복된다. 무료 체험 종료 후 자동 전환된 항목에서 특히 자주 나타난다.',
    context:
      '카드 여러 장을 나눠 쓰는 사람일수록 발견이 늦어진다. 해지 경로가 서비스마다 달라 발견하고도 미루는 흐름이 함께 관찰된다.',
    complexity_note:
      '결제 문자·메일 파싱으로 정기 결제 여부를 추정하는 규칙만으로도 1차 버전은 가능해 보인다. 다만 카드사·통신사마다 문구가 달라 오탐을 줄이는 데 반복 튜닝이 필요할 것으로 보인다.',
    evidence: [
      {
        raw_item_id: 'p1-r1',
        severity: '높음', has_payment_signal: true, has_need_signal: false,
        summary: '1년 넘게 켜져 있던 구독을 카드 명세서를 보다가 우연히 발견했다는 경험담',
        excerpt: '작년에 가입한 건데 지금까지 계속 나가고 있었더라고요',
      },
      {
        raw_item_id: 'p1-r2',
        severity: '중간', has_payment_signal: false, has_need_signal: true,
        summary: '구독 관리 앱을 깔았지만 일부 카드만 연동돼 절반만 잡힌다는 불만',
      },
      {
        raw_item_id: 'p1-r3',
        severity: '높음', has_payment_signal: true, has_need_signal: true,
        summary: '해지 버튼을 찾기 어려워 결국 다음 달로 미뤘다는 글',
        excerpt: '해지하려고 들어갔는데 메뉴가 하도 복잡해서 그냥 나왔어요',
      },
      {
        raw_item_id: 'p1-r4',
        severity: '낮음', has_payment_signal: true, has_need_signal: false,
        summary: '가족 공유 계정과 개인 결제가 섞여 누가 얼마를 내는지 모르겠다는 질문',
      },
    ],
    case_count: 47,
    source_count: 4,
    signals: {
      source_kind_counts: { 커뮤니티: 28, 블로그: 9, 소셜: 7, 뉴스: 3 },
      source_name_counts: { '재테크 커뮤니티': 20, '생활 커뮤니티': 8, '가계부 블로그': 9, '소셜 타임라인': 7, '경제 뉴스': 3 },
      first_posted_at: '2026-07-14',
      last_posted_at: '2026-09-05',
      observed_weeks: 7,
      weekly_counts: [
        { week: '2026-W29', count: 4, partial: false },
        { week: '2026-W30', count: 6, partial: false },
        { week: '2026-W31', count: 5, partial: false },
        { week: '2026-W32', count: 7, partial: false },
        { week: '2026-W33', count: 6, partial: false },
        { week: '2026-W34', count: 8, partial: false },
        { week: '2026-W35', count: 5, partial: true },
      ],
      undated_count: 6,
      severity_counts: { 높음: 12, 중간: 15, 낮음: 8 },
      severity_labeled_count: 35,
      need_signal_count: 19,
      signal_type_counts: { 불만: 30, 대안탐색: 12 },
      payment_signal_count: 22,
      role_counts: { 직장인: 6, 프리랜서: 2 },
      role_labeled_count: 8,
      age_counts: { '20대': 3, '30대': 5, '40대': 2 },
      age_labeled_count: 10,
      gender_counts: { 여자: 6, 남자: 4 },
      gender_labeled_count: 10,
      mentioned_services: [],
    },
    gate: { case_count_ok: true, source_count_ok: true, evidence_count_ok: true, passed: true, reason: '', min_cases: 20, min_sources: 3, min_evidence: 3 },
    updated_at: '2026-09-06',
  },
  {
    id: 'p2',
    title: '받을 수 있는 환급금을 몰라서 못 받는다',
    one_liner: '카드 캐시백·통신비 환급·소액 세금 환급을 신청 기간을 놓쳐 못 받는 경우가 반복된다.',
    category: '금융',
    description:
      '제도 자체를 몰라서라기보다, 내가 대상인지 확인하는 절차가 여러 기관 사이트에 흩어져 있어 확인을 미루다 기간을 넘기는 패턴이 공통적으로 나타난다.',
    context:
      '연말정산·통신비 조정 등 연 1~2회 발생하는 이벤트라 기억하기 어렵고, 신청 알림을 보내는 채널이 기관마다 달라 놓치기 쉽다.',
    complexity_note:
      '공공데이터 API로 환급 대상 여부를 조회하는 부분은 명확하지만, 기관별 신청 절차와 마감일이 제각각이라 이를 하나의 캘린더로 통합하는 유지보수 부담이 클 것으로 보인다.',
    evidence: [
      {
        raw_item_id: 'p2-r1',
        summary: '통신비 환급 신청 기간이 지나서 몇 만 원을 놓쳤다는 후기',
      },
      {
        raw_item_id: 'p2-r2',
        summary: '연말정산 환급 대상인지조차 몰랐다가 뒤늦게 알게 됐다는 글',
        excerpt: '나만 몰랐나 싶어서 검색해봤더니 아는 사람도 별로 없더라고요',
      },
      {
        raw_item_id: 'p2-r3',
        summary: '카드 캐시백 신청을 까먹어서 자동 소멸됐다는 경험 공유',
      },
    ],
    case_count: 24,
    source_count: 3,
    signals: {
      source_kind_counts: { 커뮤니티: 14, 공공데이터: 6, 뉴스: 4 },
      source_name_counts: { '재테크 커뮤니티': 14, '정부 지원사업 공고': 6, '경제 뉴스': 4 },
      first_posted_at: '2026-08-01',
      last_posted_at: '2026-09-04',
      observed_weeks: 5,
      weekly_counts: [
        { week: '2026-W31', count: 3, partial: false },
        { week: '2026-W32', count: 5, partial: false },
        { week: '2026-W33', count: 4, partial: false },
        { week: '2026-W34', count: 6, partial: false },
        { week: '2026-W35', count: 4, partial: true },
      ],
      undated_count: 2,
      severity_counts: { 높음: 5, 중간: 9, 낮음: 4 },
      severity_labeled_count: 18,
      need_signal_count: 10,
      signal_type_counts: { 불만: 14, 정보요청: 6 },
      payment_signal_count: 11,
      role_counts: { 직장인: 3, 자영업자: 1 },
      role_labeled_count: 4,
      // ★ 표본 부족 케이스 — age_labeled_count(2) < MIN_LABELED_TO_SHOW(3) → 화면에서 숨겨야 한다
      age_counts: { '30대': 2 },
      age_labeled_count: 2,
      gender_counts: { 여자: 3, 남자: 2 },
      gender_labeled_count: 5,
      mentioned_services: [
        { name: '삼쩜삼', count: 4 },
        { name: '토스', count: 2 },
      ],
    },
    gate: { case_count_ok: true, source_count_ok: true, evidence_count_ok: true, passed: true, reason: '', min_cases: 20, min_sources: 3, min_evidence: 3 },
    updated_at: '2026-09-05',
  },

  /* ── 헬스케어 ────────────────────────────────────────────────── */
  {
    id: 'p3',
    title: '병원 예약 변경이 전화로만 가능해서 놓친다',
    one_liner: '진료 예약 취소·변경 창구가 전화뿐이라 근무 시간 중엔 시도조차 못 한다.',
    category: '헬스케어',
    description:
      '예약 자체는 앱으로 되는 병원이 늘었지만, 변경·취소는 여전히 전화로만 받는 곳이 많아 평일 낮 시간에 짬을 내지 못하면 그대로 노쇼가 되거나 위약금을 무는 경우가 나온다.',
    context:
      '중소형 병원·한의원에서 특히 두드러진다. 대형 병원 앱은 변경 기능이 있어도 예약 변경 자체를 제한하는 정책을 두는 경우가 많다는 언급도 함께 나온다.',
    complexity_note:
      '병원마다 예약 시스템이 제각각이라 표준 연동이 어렵다. 초기 버전은 특정 병원과의 개별 연동 없이, 사용자가 직접 입력한 예약 정보를 기준으로 알림·재통화 요청만 대행하는 좁은 범위로 시작하는 편이 현실적으로 보인다.',
    evidence: [
      {
        raw_item_id: 'p3-r1',
        summary: '업무 중에 전화를 못 받아 예약 변경 시간을 넘겨 위약금을 냈다는 경험',
        excerpt: '점심시간에 겨우 걸었는데 통화 중이라 결국 못 바꿨어요',
      },
      {
        raw_item_id: 'p3-r2',
        summary: '한의원 예약을 바꾸려고 며칠째 전화했지만 계속 안 받는다는 하소연',
      },
      {
        raw_item_id: 'p3-r3',
        summary: '대형 병원 앱은 있지만 변경은 결국 전화로 하라는 안내를 받았다는 후기',
      },
    ],
    case_count: 31,
    source_count: 3,
    signals: {
      source_kind_counts: { 커뮤니티: 22, 소셜: 6, 블로그: 3 },
      source_name_counts: { '지역맘 커뮤니티': 15, '지식iN': 7, '소셜 타임라인': 6, '육아 블로그': 3 },
      first_posted_at: '2026-07-20',
      last_posted_at: '2026-09-02',
      observed_weeks: 6,
      weekly_counts: [
        { week: '2026-W30', count: 5, partial: false },
        { week: '2026-W31', count: 3, partial: false },
        { week: '2026-W32', count: 6, partial: false },
        { week: '2026-W33', count: 4, partial: false },
        { week: '2026-W34', count: 5, partial: false },
        { week: '2026-W35', count: 3, partial: true },
      ],
      // ★ 지식iN 비중이 커서 undated_count가 상대적으로 크다
      undated_count: 9,
      severity_counts: { 높음: 9, 중간: 8, 낮음: 3 },
      severity_labeled_count: 20,
      need_signal_count: 12,
      signal_type_counts: { 불만: 17, 대안탐색: 5 },
      payment_signal_count: 4,
      // ★ 표본 부족 케이스 — role_labeled_count(1) < 3 → 화면에서 숨겨야 한다
      role_counts: { 직장인: 1 },
      role_labeled_count: 1,
      age_counts: { '30대': 3, '40대': 2 },
      age_labeled_count: 5,
      gender_counts: { 여자: 4, 남자: 1 },
      gender_labeled_count: 5,
      mentioned_services: [],
    },
    gate: { case_count_ok: true, source_count_ok: true, evidence_count_ok: true, passed: true, reason: '', min_cases: 20, min_sources: 3, min_evidence: 3 },
    updated_at: '2026-09-03',
  },
  {
    id: 'p4',
    title: '복약 시간을 자꾸 놓쳐서 약효가 들쭉날쭉하다',
    one_liner: '하루 2~3번 챙겨야 하는 약을 일정 시간에 맞춰 먹기가 생각보다 어렵다.',
    category: '헬스케어',
    description:
      '알림 자체는 휴대폰 기본 기능으로도 되지만, 먹었는지 여부를 확인하는 절차가 없어 알림만 끄고 넘어가는 경우가 반복된다는 지적이 많다.',
    context:
      '만성질환으로 장기 복약 중인 사람에게서 특히 자주 나온다. 식사 시간이 불규칙한 직장인일수록 복약 시간도 함께 흔들린다는 언급이 붙는다.',
    complexity_note:
      '알림·체크 기능만 놓고 보면 구현 난이도는 낮은 편이다. 다만 "정말 먹었는지"를 신뢰성 있게 확인하는 수단(사진 인증 등)까지 가려면 사용자 부담과 정확도 사이의 균형을 잡는 설계가 필요해 보인다.',
    evidence: [
      {
        raw_item_id: 'p4-r1',
        summary: '알림이 울려도 하던 일을 마저 하다가 결국 잊어버린다는 반복 언급',
        excerpt: '알림 끄고 나서 딴 거 하다 보면 그새 까먹어요',
      },
      {
        raw_item_id: 'p4-r2',
        summary: '식사 시간이 불규칙해서 약 먹는 시간도 같이 흔들린다는 글',
      },
      {
        raw_item_id: 'p4-r3',
        summary: '먹었는지 안 먹었는지 헷갈려서 두 번 먹은 적도 있다는 우려 섞인 후기',
      },
      {
        raw_item_id: 'p4-r4',
        summary: '복약 관리 앱을 써봤지만 입력이 번거로워 며칠 만에 그만뒀다는 리뷰',
      },
    ],
    case_count: 38,
    source_count: 3,
    signals: {
      source_kind_counts: { 커뮤니티: 24, 블로그: 8, 소셜: 6 },
      source_name_counts: { '건강 커뮤니티': 18, '지식iN': 6, '투병 블로그': 8, '소셜 타임라인': 6 },
      first_posted_at: '2026-07-25',
      last_posted_at: '2026-09-07',
      observed_weeks: 6,
      weekly_counts: [
        { week: '2026-W30', count: 6, partial: false },
        { week: '2026-W31', count: 5, partial: false },
        { week: '2026-W32', count: 7, partial: false },
        { week: '2026-W33', count: 6, partial: false },
        { week: '2026-W34', count: 8, partial: false },
        { week: '2026-W35', count: 6, partial: true },
      ],
      undated_count: 4,
      severity_counts: { 높음: 7, 중간: 14, 낮음: 9 },
      severity_labeled_count: 30,
      need_signal_count: 16,
      signal_type_counts: { 불만: 22, 대안탐색: 8 },
      payment_signal_count: 3,
      role_counts: { 직장인: 3, 학생: 1 },
      role_labeled_count: 4,
      age_counts: { '20대': 2, '50대 이상': 3 },
      age_labeled_count: 5,
      // ★ 표본 부족 케이스 — gender_labeled_count(0) < 3 → 화면에서 숨겨야 한다
      gender_counts: {},
      gender_labeled_count: 0,
      mentioned_services: [{ name: '필타', count: 2 }],
    },
    gate: { case_count_ok: true, source_count_ok: true, evidence_count_ok: true, passed: true, reason: '', min_cases: 20, min_sources: 3, min_evidence: 3 },
    updated_at: '2026-09-08',
  },

  /* ── 라이프스타일 ────────────────────────────────────────────── */
  {
    id: 'p5',
    title: '택배 재배송 요청이 매번 번거롭다',
    one_liner: '부재중 택배를 다시 받으려면 매번 전화·앱을 오가며 같은 절차를 반복해야 한다.',
    category: '라이프스타일',
    description:
      '택배사·물류대행사마다 재배송 신청 방법이 달라, 같은 사람이 겪는 불편인데도 매번 다른 절차를 새로 익혀야 한다는 점이 반복 지적된다.',
    context:
      '1인 가구·재택 시간이 짧은 직장인에게서 특히 자주 나타난다. 경비실·문 앞 보관 옵션이 없는 건물일수록 재배송 빈도가 높다.',
    complexity_note:
      '택배사별 API가 표준화돼 있지 않아 전체 자동화는 어렵다. 초기에는 사용자가 송장번호를 직접 넣으면 재배송 신청 화면으로 바로 연결해주는 정도의 좁은 범위로 시작하는 편이 무난해 보인다.',
    evidence: [
      {
        raw_item_id: 'p5-r1',
        summary: '재배송 신청을 하려고 택배사 앱을 새로 깔아야 했다는 불만',
      },
      {
        raw_item_id: 'p5-r2',
        summary: '같은 아파트인데 택배사마다 재배송 절차가 달라 매번 헷갈린다는 글',
        excerpt: '이번엔 문자로 되는데 저번 건 전화로만 된다고 하더라고요',
      },
      {
        raw_item_id: 'p5-r3',
        summary: '재배송 신청 후에도 안내 없이 또 부재중 처리됐다는 경험',
      },
    ],
    case_count: 26,
    source_count: 3,
    signals: {
      source_kind_counts: { 커뮤니티: 16, 소셜: 6, 블로그: 4 },
      source_name_counts: { '생활 커뮤니티': 16, '소셜 타임라인': 6, '1인가구 블로그': 4 },
      first_posted_at: '2026-08-05',
      last_posted_at: '2026-09-01',
      observed_weeks: 4,
      weekly_counts: [
        { week: '2026-W32', count: 6, partial: false },
        { week: '2026-W33', count: 7, partial: false },
        { week: '2026-W34', count: 8, partial: false },
        { week: '2026-W35', count: 5, partial: true },
      ],
      undated_count: 0,
      severity_counts: { 높음: 3, 중간: 10, 낮음: 8 },
      severity_labeled_count: 21,
      need_signal_count: 9,
      signal_type_counts: { 불만: 15, 대안탐색: 4 },
      payment_signal_count: 1,
      role_counts: { 직장인: 5 },
      role_labeled_count: 5,
      age_counts: { '20대': 4, '30대': 2 },
      age_labeled_count: 6,
      gender_counts: { 여자: 3, 남자: 3 },
      gender_labeled_count: 6,
      mentioned_services: [],
    },
    gate: { case_count_ok: true, source_count_ok: true, evidence_count_ok: true, passed: true, reason: '', min_cases: 20, min_sources: 3, min_evidence: 3 },
    updated_at: '2026-09-02',
  },

  /* ── IT/생산성 ───────────────────────────────────────────────── */
  {
    id: 'p6',
    title: '협업툴이 여러 개라 알림을 다 못 챙긴다',
    one_liner: '메신저·이슈트래커·문서도구 알림이 따로 와서 중요한 걸 놓친다.',
    category: 'IT/생산성',
    description:
      '도구를 줄이자는 논의는 늘 나오지만 팀마다 이미 쓰는 도구가 달라 통합이 어렵고, 결국 각자 알림을 몇 개씩 끄면서 중요한 메시지를 놓치는 패턴이 반복된다.',
    context:
      '5인 이상 팀, 특히 여러 팀과 동시에 협업하는 사람에게서 두드러진다. 알림을 다 켜두면 피로가 커서 스스로 꺼버리는 역설적인 상황도 함께 언급된다.',
    complexity_note:
      '각 도구가 제공하는 웹훅·API를 엮어 알림을 한곳에 모으는 것 자체는 기술적으로 어렵지 않다. 다만 도구별 인증·요금제 제약이 있어 모든 조합을 지원하려면 범위를 단계적으로 넓히는 접근이 필요해 보인다.',
    evidence: [
      {
        raw_item_id: 'p6-r1',
        summary: '슬랙·지라·노션 알림이 따로 와서 중요한 멘션을 하루 늦게 봤다는 사례',
        excerpt: '알림이 너무 많아서 다 꺼놨다가 정작 중요한 걸 놓쳤어요',
      },
      {
        raw_item_id: 'p6-r2',
        summary: '도구 통합을 시도했지만 팀 절반이 안 옮겨서 되돌렸다는 후기',
      },
      {
        raw_item_id: 'p6-r3',
        summary: '알림을 다 켜두면 집중이 안 돼서 결국 몰아서 확인하게 된다는 글',
      },
      {
        raw_item_id: 'p6-r4',
        summary: '노션 코멘트는 이메일로만 와서 확인이 항상 늦다는 지적',
      },
    ],
    case_count: 52,
    source_count: 4,
    signals: {
      source_kind_counts: { 커뮤니티: 30, 소셜: 12, 블로그: 8, 뉴스: 2 },
      source_name_counts: {
        '개발자 커뮤니티': 22,
        '직장인 커뮤니티': 8,
        '소셜 타임라인': 12,
        '생산성 블로그': 8,
        'IT 뉴스': 2,
      },
      first_posted_at: '2026-07-10',
      last_posted_at: '2026-09-08',
      observed_weeks: 8,
      weekly_counts: [
        { week: '2026-W28', count: 5, partial: false },
        { week: '2026-W29', count: 6, partial: false },
        { week: '2026-W30', count: 7, partial: false },
        { week: '2026-W31', count: 6, partial: false },
        { week: '2026-W32', count: 8, partial: false },
        { week: '2026-W33', count: 7, partial: false },
        { week: '2026-W34', count: 8, partial: false },
        { week: '2026-W35', count: 5, partial: true },
      ],
      undated_count: 3,
      severity_counts: { 높음: 10, 중간: 20, 낮음: 12 },
      severity_labeled_count: 42,
      need_signal_count: 24,
      signal_type_counts: { 불만: 36, 대안탐색: 14 },
      payment_signal_count: 6,
      role_counts: { 직장인: 9, 프리랜서: 3 },
      role_labeled_count: 12,
      age_counts: { '20대': 5, '30대': 6, '40대': 1 },
      age_labeled_count: 12,
      gender_counts: { 남자: 7, 여자: 5 },
      gender_labeled_count: 12,
      mentioned_services: [
        { name: 'Slack', count: 14 },
        { name: 'Notion', count: 9 },
        { name: 'Jira', count: 5 },
      ],
    },
    gate: { case_count_ok: true, source_count_ok: true, evidence_count_ok: true, passed: true, reason: '', min_cases: 20, min_sources: 3, min_evidence: 3 },
    updated_at: '2026-09-09',
  },
  {
    id: 'p7',
    title: '재택근무 중 집중한 시간을 기록할 방법이 없다',
    one_liner: '몇 시간 일했는지는 알아도 실제로 몰입한 시간이 얼마였는지는 감으로만 판단한다.',
    category: 'IT/생산성',
    description:
      '근태 기록은 있지만 그 시간이 실제 집중 시간인지 알 방법이 없어, 스스로 컨디션을 관리하기 어렵다는 언급이 반복된다.',
    context:
      '재택·하이브리드 근무자에게서 자주 나타난다. 회사 근태 시스템과는 별개로 개인이 자기 리듬을 파악하려는 목적이 크다.',
    complexity_note:
      '화면 사용 시간이나 키보드 활동을 단순 집계하는 수준은 구현 부담이 적다. 다만 "집중"을 어떻게 정의할지가 모호해 사용자마다 다른 기준을 어떻게 반영할지 설계가 더 필요해 보인다.',
    evidence: [
      {
        raw_item_id: 'p7-r1',
        summary: '하루 종일 앉아 있었는데 실제로 뭘 했는지 기억이 안 난다는 글',
      },
      {
        raw_item_id: 'p7-r2',
        summary: '집중 시간대를 몰라서 회의를 아무 때나 잡다가 능률이 떨어졌다는 경험',
        excerpt: '오후에 제일 집중 잘 되는 걸 뒤늦게 알았어요',
      },
      {
        raw_item_id: 'p7-r3',
        summary: '타이머 앱을 켜놓긴 하는데 끄는 걸 자꾸 잊어서 기록이 부정확하다는 후기',
      },
    ],
    case_count: 21,
    source_count: 3,
    signals: {
      source_kind_counts: { 커뮤니티: 12, 블로그: 6, 소셜: 3 },
      source_name_counts: { '개발자 커뮤니티': 12, '생산성 블로그': 6, '소셜 타임라인': 3 },
      first_posted_at: '2026-08-10',
      last_posted_at: '2026-09-06',
      observed_weeks: 5,
      weekly_counts: [
        { week: '2026-W32', count: 3, partial: false },
        { week: '2026-W33', count: 5, partial: false },
        { week: '2026-W34', count: 6, partial: false },
        { week: '2026-W35', count: 4, partial: false },
        { week: '2026-W36', count: 3, partial: true },
      ],
      undated_count: 1,
      severity_counts: { 높음: 2, 중간: 8, 낮음: 6 },
      severity_labeled_count: 16,
      need_signal_count: 8,
      signal_type_counts: { 불만: 10, 정보요청: 5 },
      payment_signal_count: 2,
      role_counts: { 프리랜서: 4, 직장인: 2 },
      role_labeled_count: 6,
      age_counts: { '20대': 3, '30대': 3 },
      age_labeled_count: 6,
      gender_counts: { 남자: 4, 여자: 2 },
      gender_labeled_count: 6,
      mentioned_services: [{ name: 'Toggl', count: 3 }],
    },
    gate: { case_count_ok: true, source_count_ok: true, evidence_count_ok: true, passed: true, reason: '', min_cases: 20, min_sources: 3, min_evidence: 3 },
    updated_at: '2026-09-07',
  },

  /* ── 교육/커리어 ─────────────────────────────────────────────── */
  {
    id: 'p8',
    title: '이력서에 쓸 성과를 기억하지 못해 매번 다시 찾아본다',
    one_liner: '이직·평가 시점마다 지난 업무를 처음부터 뒤져가며 복원한다.',
    category: '교육/커리어',
    description:
      '기록이 아예 없는 게 아니라, 남긴 기록이 "무엇을 개선했는가" 형태가 아니어서 이력서 문장으로 바로 못 쓴다는 진단이 반복된다.',
    context:
      '연말 평가나 이직 준비를 시작하는 시점에 집중적으로 나타난다. 몇 달 전 일은 이미 세부가 사라져 복원 비용이 크다는 언급이 함께 붙는다.',
    complexity_note:
      '주기적으로 짧은 질문을 던져 답을 모으는 수준의 기록 도구는 구현 부담이 크지 않다. 모은 기록을 실제로 설득력 있는 성과 문장으로 다듬는 부분은 표현 품질 편차가 커서 반복 검증이 필요해 보인다.',
    evidence: [
      {
        raw_item_id: 'p8-r1',
        summary: '이력서를 쓰려는데 작년에 뭘 했는지 기억이 안 난다는 글',
        excerpt: '분명 바빴는데 막상 적으려니 쓸 게 없더라고요',
      },
      {
        raw_item_id: 'p8-r2',
        summary: '평가 자료를 만들려고 1년 치 메신저를 거슬러 올라갔다는 경험',
      },
      {
        raw_item_id: 'p8-r3',
        summary: '업무 기록은 있지만 성과 문장으로 바꾸는 게 제일 어렵다는 반응',
      },
    ],
    case_count: 29,
    source_count: 3,
    signals: {
      source_kind_counts: { 커뮤니티: 18, 블로그: 7, 소셜: 4 },
      source_name_counts: { '커리어 커뮤니티': 18, '이직 정보 블로그': 7, '소셜 타임라인': 4 },
      first_posted_at: '2026-07-28',
      last_posted_at: '2026-09-04',
      observed_weeks: 6,
      weekly_counts: [
        { week: '2026-W30', count: 4, partial: false },
        { week: '2026-W31', count: 5, partial: false },
        { week: '2026-W32', count: 6, partial: false },
        { week: '2026-W33', count: 4, partial: false },
        { week: '2026-W34', count: 5, partial: false },
        { week: '2026-W35', count: 3, partial: true },
      ],
      undated_count: 2,
      severity_counts: { 높음: 6, 중간: 10, 낮음: 5 },
      severity_labeled_count: 21,
      need_signal_count: 11,
      signal_type_counts: { 불만: 16, 정보요청: 5 },
      payment_signal_count: 1,
      role_counts: { 직장인: 7, 프리랜서: 1 },
      role_labeled_count: 8,
      age_counts: { '20대': 3, '30대': 4 },
      age_labeled_count: 7,
      gender_counts: { 여자: 4, 남자: 3 },
      gender_labeled_count: 7,
      mentioned_services: [],
    },
    gate: { case_count_ok: true, source_count_ok: true, evidence_count_ok: true, passed: true, reason: '', min_cases: 20, min_sources: 3, min_evidence: 3 },
    updated_at: '2026-09-05',
  },
];

export const problemsById = new Map(problems.map((p) => [p.id, p]));

export function getProblem(id: string): Problem | undefined {
  return problemsById.get(id);
}

/**
 * 아이디어는 현재 잠금 기능(app/ideas, app/personalize)이라 목데이터를 채우지 않는다.
 * 타입만 계약(api/types.ts)대로 유지해 관련 화면이 다시 열릴 때 그대로 쓸 수 있게 한다.
 */
export const ideas: Idea[] = [];
