import type { Idea } from '@/lib/types';

/**
 * 문제별 기본 아이디어 풀 (F04).
 * 변형 B의 "다른 아이디어 보기"가 서로 다른 묶음을 돌려 보여줄 수 있도록
 * 문제당 노출 개수(3개)보다 넉넉하게 둔다.
 * 모두 AI 생성 추천 후보이며 시장성이 검증된 결과가 아니다.
 */
export const ideas: Idea[] = [
  {
    id: 'i-handoff-1',
    problemId: 'p-handoff',
    name: '액션 아이템 추출 봇',
    oneLiner:
      '회의록을 붙여 넣으면 담당자·기한이 붙은 할 일 목록으로 바꿔 준다.',
    target: '회의록은 남기지만 트래커 이관이 안 되는 5~20인 팀',
    serviceForm: '챗봇',
    whyLinked:
      '근거에서 반복된 불편은 "회의록이 없다"가 아니라 "회의록이 할 일로 변환되지 않는다"였다. 변환 단계만 자동화하는 접근이다.',
    howItWorks:
      '메신저 채널에 회의록을 공유하면 봇이 결정 사항과 액션 아이템을 분리하고, 담당자·기한이 비어 있으면 되물어 채운 뒤 목록으로 고정한다.',
    coreFeatures: [
      '회의록에서 결정/액션 분리',
      '담당자·기한 누락 시 되묻기',
      '채널 고정 메시지로 미완료 항목 유지',
    ],
    differentiator:
      '요약을 더 잘하는 대신, 담당자와 기한이 채워질 때까지 대화로 되묻는 데 집중한다.',
  },
  {
    id: 'i-handoff-2',
    problemId: 'p-handoff',
    name: '다음 회의 안건 자동 상속',
    oneLiner:
      '지난 회의의 미완료 항목을 다음 회의 안건 맨 위에 자동으로 올려 준다.',
    target: '정기 회의를 운영하는 팀 리드',
    serviceForm: '웹 서비스',
    whyLinked:
      '"같은 안건을 다시 논의한다"는 근거는 미완료 항목이 회의 사이에서 사라지기 때문에 생긴다. 회의 간 연결을 만드는 접근이다.',
    howItWorks:
      '정기 회의 시리즈를 등록해 두면 직전 회의의 미완료 항목을 다음 회차 안건 초안 상단에 자동으로 붙여 넣는다.',
    coreFeatures: ['회의 시리즈 관리', '미완료 항목 상속', '안건 초안 자동 생성'],
    differentiator:
      '개별 회의를 잘 기록하는 도구가 아니라 회의와 회의 사이를 잇는 데 초점을 둔다.',
  },
  {
    id: 'i-handoff-3',
    problemId: 'p-handoff',
    name: '48시간 리마인더',
    oneLiner:
      '회의 이틀 뒤에 "이거 하기로 했어요"를 담당자에게 한 번만 알려 준다.',
    target: '별도 트래커를 도입하기 어려운 소규모 팀',
    serviceForm: '자동화 스크립트',
    whyLinked:
      '근거에서 "이틀만 지나도 잊는다"는 시점이 반복 언급됐다. 그 시점 하나만 겨냥한 최소 개입이다.',
    coreFeatures: ['액션 아이템 등록', '48시간 후 1회 알림', '완료 회신 처리'],
    howItWorks:
      '회의 후 액션 아이템을 등록하면 정확히 48시간 뒤 담당자에게 개인 알림을 보내고, 회신으로 완료 처리한다.',
    differentiator:
      '새 도구를 도입하지 않고 기존 메신저 안에서 알림 한 번으로 끝낸다.',
  },
  {
    id: 'i-handoff-4',
    problemId: 'p-handoff',
    name: '결정 로그 검색기',
    oneLiner:
      '"이거 언제 어떻게 정했더라"를 한 줄 검색으로 찾아 준다.',
    target: '회의록이 오래 쌓인 조직',
    serviceForm: '브라우저 확장 프로그램',
    whyLinked:
      '문서를 다시 뒤진다는 불편은 기록이 아니라 검색의 문제다. 결정 사항만 따로 색인하는 접근이다.',
    howItWorks:
      '회의록 문서에서 결정 문장만 추출해 별도 색인을 만들고, 확장 프로그램에서 결정 내용·날짜·참석자로 검색한다.',
    coreFeatures: ['결정 문장 추출', '결정 전용 색인', '문서 원문 위치로 이동'],
    differentiator:
      '문서 전체 검색이 아니라 "결정"만 대상으로 삼아 결과 수를 줄인다.',
  },
  {
    id: 'i-handoff-5',
    problemId: 'p-handoff',
    name: '회의 종료 3분 체크리스트',
    oneLiner:
      '회의 마지막 3분에 담당자와 기한을 강제로 확인시키는 진행 도구.',
    target: '회의 진행을 맡는 실무 리드',
    serviceForm: '모바일 앱',
    whyLinked:
      '변환 단계를 자동화하는 대신 회의 안에서 미리 채우게 하는, 반대 방향의 해결책이다.',
    howItWorks:
      '회의 종료 3분 전에 알림이 뜨고, 그날 나온 안건별로 담당자와 기한을 입력해야 회의를 종료할 수 있다.',
    coreFeatures: ['종료 3분 전 알림', '안건별 담당자·기한 입력', '종료 시 요약 공유'],
    differentiator:
      '회의 후 처리를 돕는 대신 회의 안에서 끝내도록 진행 흐름을 바꾼다.',
  },
  {
    id: 'i-handoff-6',
    problemId: 'p-handoff',
    name: '액션 아이템 정체 알림',
    oneLiner:
      '옮겨지긴 했지만 2주째 움직이지 않는 항목만 골라 리드에게 보고한다.',
    target: '여러 팀의 진행 상황을 보는 관리자',
    serviceForm: '웹 서비스',
    whyLinked:
      '이관 이후에도 항목이 방치되는 상황을 다루며, 앞선 아이디어들과 다른 단계를 겨냥한다.',
    howItWorks:
      '트래커와 연결해 상태 변화가 없는 항목을 추적하고, 정체 기간이 임계값을 넘으면 주간 요약으로 묶어 보낸다.',
    coreFeatures: ['정체 항목 탐지', '주간 요약 리포트', '임계 기간 설정'],
    differentiator:
      '모든 항목을 알리지 않고 멈춰 있는 것만 좁혀서 알림 피로를 줄인다.',
  },
  {
    id: 'i-onboarding-1',
    problemId: 'p-onboarding-docs',
    name: '온보딩 질문 수집기',
    oneLiner:
      '신규 입사자가 실제로 물어본 질문을 모아 문서 보강 순서를 정해 준다.',
    target: '온보딩을 개선하려는 팀 리드',
    serviceForm: '챗봇',
    whyLinked:
      '"같은 질문을 반복 답변한다"는 근거는 질문이 기록되지 않아 생긴다. 질문 자체를 자산으로 만드는 접근이다.',
    howItWorks:
      '온보딩 채널의 질문을 자동 수집·분류해 빈도가 높은 순으로 정리하고, 답변을 문서 초안으로 만들어 준다.',
    coreFeatures: ['질문 수집·분류', '빈도순 정렬', '답변 문서 초안 생성'],
    differentiator:
      '문서를 처음부터 쓰게 하는 대신 이미 오간 답변에서 문서를 역으로 만든다.',
  },
  {
    id: 'i-onboarding-2',
    problemId: 'p-onboarding-docs',
    name: '문서 신선도 배지',
    oneLiner:
      '문서 상단에 최신 여부와 담당자를 표시해 낡은 문서를 걸러 준다.',
    target: '위키가 오래 쌓인 조직',
    serviceForm: '브라우저 확장 프로그램',
    whyLinked:
      '2년 전 문서를 그대로 따라 했다는 사례는 최신 여부를 알 수 없어서 생긴다. 판단 근거를 문서에 얹는 접근이다.',
    howItWorks:
      '문서의 최종 수정일과 소유자를 읽어 신선도 배지를 문서 상단에 덧붙이고, 기준을 넘으면 소유자에게 확인을 요청한다.',
    coreFeatures: ['신선도 배지 표시', '문서 소유자 지정', '갱신 확인 요청'],
    differentiator:
      '문서를 옮기거나 새 도구로 이전하지 않고 지금 쓰는 위키 위에 얹는다.',
  },
  {
    id: 'i-onboarding-3',
    problemId: 'p-onboarding-docs',
    name: '첫 주 길잡이',
    oneLiner:
      '입사 후 5일 동안 매일 아침 그날 필요한 문서만 한 개씩 보내 준다.',
    target: '신규 입사자',
    serviceForm: '자동화 스크립트',
    whyLinked:
      '문서가 흩어져 있다는 불편을 검색이 아니라 순서로 푼다. 필요한 시점에만 하나씩 노출한다.',
    howItWorks:
      '입사일을 기준으로 미리 정해 둔 문서 시퀀스를 하루 한 개씩 개인 메시지로 전달하고 읽음 여부를 확인한다.',
    coreFeatures: ['입사일 기준 스케줄', '일 1건 문서 전달', '완료 확인'],
    differentiator:
      '한 번에 모든 문서를 주는 온보딩 위키와 반대로 하루치로 쪼개 전달한다.',
  },
  {
    id: 'i-onboarding-4',
    problemId: 'p-onboarding-docs',
    name: '문서 위치 안내 봇',
    oneLiner:
      '"그거 어디 있어요?"에 링크 하나로 답하는 사내 검색 봇.',
    target: '문서가 여러 도구에 흩어진 조직',
    serviceForm: '챗봇',
    whyLinked:
      '옆자리에 묻는 것이 가장 빠르다는 근거를, 묻는 대상을 봇으로 바꾸는 방식으로 다룬다.',
    howItWorks:
      '위키·드라이브·메신저 고정글을 한 색인으로 묶고, 자연어 질문에 문서 링크와 최종 수정일을 함께 답한다.',
    coreFeatures: ['다중 도구 통합 색인', '자연어 질의응답', '최종 수정일 함께 표시'],
    differentiator:
      '답변 본문을 생성하는 대신 정확한 문서 링크와 신선도를 돌려주는 데 집중한다.',
  },
  {
    id: 'i-onboarding-5',
    problemId: 'p-onboarding-docs',
    name: '온보딩 버디 매칭',
    oneLiner:
      '질문을 받아 줄 담당자를 주차별로 지정해 질문 부담을 나눈다.',
    target: '분기마다 입사자가 있는 팀',
    serviceForm: '웹 서비스',
    whyLinked:
      '시니어 시간이 계속 소모된다는 근거를, 문서화가 아니라 담당 분산으로 푸는 다른 접근이다.',
    howItWorks:
      '입사자마다 주차별 버디를 자동 배정하고, 질문·답변 기록을 남겨 다음 입사자에게 재사용한다.',
    coreFeatures: ['버디 자동 배정', '질문 기록 축적', '부담 균등 분배'],
    differentiator:
      '문서 도구가 아니라 사람 배치를 다루기 때문에 문서화 여력이 없는 팀도 바로 쓸 수 있다.',
  },
  {
    id: 'i-onboarding-6',
    problemId: 'p-onboarding-docs',
    name: '설정 스크립트 검증기',
    oneLiner:
      '개발 환경 세팅 문서를 실제로 실행해 보고 깨진 단계를 찾아 준다.',
    target: '개발 온보딩 문서를 관리하는 팀',
    serviceForm: '자동화 스크립트',
    whyLinked:
      '잘못된 환경을 세팅했다는 사례를 문서 표시가 아니라 실행 검증으로 다룬다.',
    howItWorks:
      '문서의 명령어 블록을 추출해 정기적으로 깨끗한 환경에서 실행하고, 실패한 단계를 문서 소유자에게 알린다.',
    coreFeatures: ['명령어 블록 추출', '정기 실행 검증', '실패 단계 리포트'],
    differentiator:
      '사람이 문서를 검토하는 대신 문서를 실행해 낡음을 자동으로 검출한다.',
  },
  {
    id: 'i-status-report-1',
    problemId: 'p-status-report',
    name: '보고 초안 자동 생성 봇',
    oneLiner:
      '이슈 트래커와 메신저에서 있었던 일을 모아 보고서 초안으로 만들어 준다.',
    target: '주간·월간 보고를 정해진 양식으로 내야 하는 실무자',
    serviceForm: '챗봇',
    whyLinked:
      '근거에서 반복된 불편은 같은 내용을 다른 도구에서 복사해 붙이는 데만 한 시간 넘게 쓴다는 것이었다. 수집과 정리를 자동화하는 접근이다.',
    howItWorks:
      '보고 대상 기간과 담당 프로젝트를 지정하면 이슈 트래커의 상태 변경과 메신저의 관련 언급을 모아 보고 양식에 맞춘 초안을 채팅으로 전달한다.',
    coreFeatures: ['다중 도구 연동 수집', '보고 양식별 초안 생성', '기간·담당자 필터'],
    differentiator:
      '요약 문장을 새로 쓰는 대신 이미 남아 있는 기록을 양식에 옮기는 데만 집중한다.',
  },
  {
    id: 'i-status-report-2',
    problemId: 'p-status-report',
    name: '실시간 현황판',
    oneLiner: '보고서를 쓰는 대신 링크 하나로 지금 상태를 바로 보여준다.',
    target: '정기 보고를 받는 팀 리더와 유관 부서',
    serviceForm: '웹 서비스',
    whyLinked:
      '보고서를 냈는데 이미 상태가 바뀌어 있어 신뢰도가 떨어진다는 근거를 다룬다. 정적인 보고서 대신 항상 최신 상태를 보여주는 접근이다.',
    howItWorks:
      '이슈 트래커와 연동한 현황판을 만들어, 보고를 받는 사람이 정해진 시각이 아니라 원하는 때에 직접 최신 상태를 확인하도록 한다.',
    coreFeatures: ['실시간 상태 동기화', '부서별 보기 권한', '변경 이력 타임라인'],
    differentiator: '보고서 작성 자체를 없애고 확인 방식을 조회로 바꾼다.',
  },
  {
    id: 'i-status-report-3',
    problemId: 'p-status-report',
    name: '열린 탭 모아보기',
    oneLiner:
      '이슈 트래커, 문서, 메신저에 열려 있는 상태 정보를 한 화면에 모아 보여준다.',
    target: '여러 도구를 동시에 띄워 놓고 보고서를 쓰는 실무자',
    serviceForm: '브라우저 확장 프로그램',
    whyLinked:
      '복사해 붙이는 시간이 길다는 근거를, 새 도구 없이 지금 쓰는 화면들을 정리하는 방식으로 줄인다.',
    howItWorks:
      '지정한 이슈 트래커·문서·메신저 탭에서 상태 관련 텍스트를 인식해 사이드 패널에 모아 보여주고, 그대로 복사할 수 있는 형태로 정리한다.',
    coreFeatures: ['다중 탭 상태 인식', '사이드 패널 요약', '복사용 텍스트 정리'],
    differentiator:
      '새 플랫폼으로 이전하지 않고 기존에 열어 두는 화면 위에서 동작한다.',
  },
  {
    id: 'i-status-report-4',
    problemId: 'p-status-report',
    name: '마감 전 코멘트 수집기',
    oneLiner: '보고 마감 몇 시간 전 담당자별 최신 코멘트를 자동으로 모아 보낸다.',
    target: '보고서 취합을 맡은 실무자',
    serviceForm: '자동화 스크립트',
    whyLinked:
      '자동 리포트 기능을 써도 결국 코멘트를 손으로 덧붙여야 한다는 근거를 다룬다. 코멘트 수집만 자동화하는 최소 개입이다.',
    howItWorks:
      '보고 마감 시각을 등록해 두면 그 몇 시간 전 담당자별 이슈에 달린 최신 코멘트를 모아 정리된 메시지로 취합자에게 전달한다.',
    coreFeatures: ['마감 시각 기준 수집', '담당자별 최신 코멘트 정리', '취합자에게 자동 전달'],
    differentiator: '보고서 형식을 만들지 않고 취합에 필요한 재료만 모아 준다.',
  },
  {
    id: 'i-status-report-5',
    problemId: 'p-status-report',
    name: '30초 음성 상태 기록',
    oneLiner: '말로 남긴 오늘 진행 상황을 텍스트로 바꿔 보고 항목에 반영한다.',
    target: '이동 중이거나 타이핑할 여유가 적은 현장 실무자',
    serviceForm: '모바일 앱',
    whyLinked:
      '보고서 작성이 별도 시간을 내야 하는 일이 되지 않도록, 근거에 나온 반복 작업 부담을 입력 방식을 바꿔 줄이는 접근이다.',
    howItWorks:
      '하루 중 짧은 음성 메모로 진행 상황을 남기면 텍스트로 변환해 담당 프로젝트의 보고 항목 초안에 자동으로 쌓아 둔다.',
    coreFeatures: ['음성 메모 녹음', '텍스트 자동 변환', '프로젝트별 항목 누적'],
    differentiator: '키보드 입력 대신 짧은 음성으로 기록 부담을 낮춘다.',
  },
  {
    id: 'i-status-report-6',
    problemId: 'p-status-report',
    name: '상태 태그 규칙 카드',
    oneLiner:
      '이슈마다 정해진 상태 이모지만 붙이기로 팀 규칙을 정하고 한 장으로 배포한다.',
    target: '새 도구 도입 없이 바로 바꿔보고 싶은 소규모 팀',
    serviceForm: '웹 서비스',
    whyLinked:
      '양식만 다른 재작업이 반복된다는 근거를 자동화가 아니라 규칙 통일로 접근한다. 소프트웨어 없이도 시도할 수 있는 최소 개입이다.',
    howItWorks:
      '팀이 쓰는 이슈 트래커에 붙일 상태 이모지 규칙(예: 진행·지연·완료)을 정하고, 그 규칙을 설명한 카드 한 장을 만들어 공유한다.',
    coreFeatures: ['표준 상태 태그 정의', '한 장짜리 규칙 카드 생성', '팀 채널 공유용 링크'],
    differentiator:
      '연동이나 자동 수집 없이 팀이 태그를 통일하는 것만으로 조회 부담을 줄인다.',
  },
  {
    id: 'i-career-feedback-1',
    problemId: 'p-career-feedback',
    name: '1:1 피드백 질문 카드',
    oneLiner: '1:1 시작 전 구체적인 업무 피드백 질문 3개를 미리 던져 준다.',
    target: '1:1이 있어도 잡담으로 끝나는 팀원',
    serviceForm: '챗봇',
    whyLinked:
      '1:1이 잡혀도 업무 피드백은 듣지 못한다는 근거를 다룬다. 대화 내용을 바꾸는 최소 개입이다.',
    howItWorks:
      '1:1 일정 전 최근 진행한 업무를 바탕으로 구체적인 피드백 질문 후보를 만들어 당사자에게 전달하고, 원하면 그대로 매니저에게 전달한다.',
    coreFeatures: ['최근 업무 기반 질문 생성', '1:1 일정 연동 알림', '매니저 공유 여부 선택'],
    differentiator: '새로운 평가 체계를 만들지 않고 기존 1:1 시간의 내용만 바꾼다.',
  },
  {
    id: 'i-career-feedback-2',
    problemId: 'p-career-feedback',
    name: '동료 관찰 기록장',
    oneLiner:
      '함께 일한 동료가 남긴 짧은 관찰을 모아 연말 평가 전에 미리 보여준다.',
    target: '정기 피드백 체계가 없는 조직의 구성원',
    serviceForm: '웹 서비스',
    whyLinked:
      '연말 평가에서 처음 듣는 지적이 있었다는 근거를 다룬다. 평가 시점이 아니라 그 이전에 신호를 모으는 접근이다.',
    howItWorks:
      '프로젝트가 끝날 때마다 함께 일한 동료에게 짧은 관찰 메모를 요청해 쌓아 두고, 본인이 원할 때 모아서 열람할 수 있게 한다.',
    coreFeatures: ['프로젝트 종료 시 관찰 요청', '누적 관찰 기록 열람', '익명·실명 선택'],
    differentiator:
      '정식 평가 제도를 새로 만들지 않고 이미 있는 협업 관계에서 신호를 모은다.',
  },
  {
    id: 'i-career-feedback-3',
    problemId: 'p-career-feedback',
    name: '동료에게 대신 물어보기 창구',
    oneLiner: '내 일이 잘 되고 있는지 동료에게 편하게 물어볼 수 있는 창구를 만든다.',
    target: '누구에게 어떻게 물어봐야 할지부터 막막한 구성원',
    serviceForm: '브라우저 확장 프로그램',
    whyLinked:
      '동료에게 대신 물어봐야 감이 온다는 근거를 그대로 인정하고, 그 과정을 더 쉽게 만드는 접근이다.',
    howItWorks:
      '업무 도구 화면에서 특정 작업을 선택해 짧은 의견을 요청할 수 있는 버튼을 붙이고, 익명으로 짧은 답변만 받을 수 있게 한다.',
    coreFeatures: ['작업 단위 의견 요청', '익명 짧은 답변', '요청 이력 보관'],
    differentiator:
      '정식 피드백 프로세스 대신 이미 하고 있는 비공식 질문을 도구 안으로 옮긴다.',
  },
  {
    id: 'i-career-feedback-4',
    problemId: 'p-career-feedback',
    name: '강점 정리 인터뷰 봇',
    oneLiner: '이직 준비 없이도 주기적으로 자신의 강점과 최근 성과를 정리해 준다.',
    target: '평소에는 자기 강점을 정리할 계기가 없는 직장인',
    serviceForm: '챗봇',
    whyLinked:
      '이직을 준비하면서야 강점을 정리해봤다는 근거를 다룬다. 그 계기를 평소로 앞당기는 접근이다.',
    howItWorks:
      '분기마다 최근 진행한 업무에 대해 몇 가지 질문을 던지고, 답변을 모아 강점과 성과를 정리한 요약본을 만들어 준다.',
    coreFeatures: ['분기별 정리 질문', '성과 요약 자동 생성', '이력서용 문구 추출'],
    differentiator: '평가나 승진 시즌이 아니라 정해진 주기마다 정리하도록 만든다.',
  },
  {
    id: 'i-career-feedback-5',
    problemId: 'p-career-feedback',
    name: '월간 자가 회고 알림',
    oneLiner: '매달 마지막 날, 이번 달 잘한 일과 아쉬운 일 세 가지만 적게 한다.',
    target: '가벼운 습관으로 시작하고 싶은 개인',
    serviceForm: '자동화 스크립트',
    whyLinked:
      '회사가 피드백을 주지 않는다는 근거를 회사 제도를 바꾸는 대신 개인 기록 습관으로 보완하는 최소 개입이다.',
    howItWorks:
      '매달 마지막 영업일에 짧은 알림을 보내 잘한 일·아쉬운 일 각 세 가지를 적게 하고, 지난 기록을 함께 보여준다.',
    coreFeatures: ['월말 자동 알림', '세 줄 회고 입력', '지난 기록 비교'],
    differentiator: '제도나 도구 도입 없이 알림 하나로 회고 습관만 만든다.',
  },
  {
    id: 'i-career-feedback-6',
    problemId: 'p-career-feedback',
    name: '피드백 요청 매너 가이드',
    oneLiner: '매니저에게 부담 없이 피드백을 요청하는 문장 템플릿을 제공한다.',
    target: '피드백을 요청하는 것 자체가 어색한 구성원',
    serviceForm: '웹 서비스',
    whyLinked:
      '피드백을 받지 못하는 이유 중에는 요청하는 쪽도 방법을 모른다는 점이 있다는 근거를 다룬다. 도구가 아니라 요청 방법을 바꾸는 접근이다.',
    howItWorks:
      '상황별(1:1 전, 프로젝트 종료 후 등) 피드백 요청 문장 예시를 제공하고, 원하는 문장을 골라 바로 복사해 쓸 수 있게 한다.',
    coreFeatures: ['상황별 요청 문장 예시', '복사용 템플릿', '요청 타이밍 안내'],
    differentiator: '시스템을 만들지 않고 요청하는 쪽의 언어를 바꾸는 데만 집중한다.',
  },
  {
    id: 'i-job-search-tracking-1',
    problemId: 'p-job-search-tracking',
    name: '지원 현황 자동 정리 봇',
    oneLiner: '채용 사이트에서 온 메일을 읽어 지원 현황표를 자동으로 채워 준다.',
    target: '여러 플랫폼에 동시에 지원하는 구직자',
    serviceForm: '챗봇',
    whyLinked:
      '어느 회사에 뭘 냈는지 기억이 안 나 재확인한다는 근거를 다룬다. 메일에 이미 있는 정보를 정리하는 접근이다.',
    howItWorks:
      '채용 관련 메일을 연동하면 회사명·지원일·현재 단계를 인식해 지원 현황표에 자동으로 채우고 변경 사항이 있으면 업데이트한다.',
    coreFeatures: ['채용 메일 자동 인식', '현황표 자동 채움', '단계 변경 업데이트'],
    differentiator: '직접 입력하는 트래커 대신 이미 오는 메일에서 정보를 뽑아낸다.',
  },
  {
    id: 'i-job-search-tracking-2',
    problemId: 'p-job-search-tracking',
    name: '이력서 버전 관리 확장',
    oneLiner:
      '어느 회사에 어떤 버전의 이력서를 보냈는지 붙여넣기 순간 기록해 둔다.',
    target: '회사마다 이력서를 조금씩 다르게 수정해서 내는 구직자',
    serviceForm: '브라우저 확장 프로그램',
    whyLinked:
      '낸 이력서 버전이 기억나지 않아 재확인한다는 근거를 다룬다. 제출 시점에 자동으로 기록하는 접근이다.',
    howItWorks:
      '채용 사이트에서 파일을 첨부하거나 자기소개서를 붙여넣는 순간을 감지해 회사명과 함께 어떤 파일·버전이 제출됐는지 기록한다.',
    coreFeatures: ['제출 시점 자동 감지', '회사별 버전 기록', '제출 파일 미리보기'],
    differentiator: '별도로 표를 만들지 않아도 지원하는 행동 자체에서 기록이 남는다.',
  },
  {
    id: 'i-job-search-tracking-3',
    problemId: 'p-job-search-tracking',
    name: '일정 겹침 경고',
    oneLiner: '새 면접 일정을 등록하면 기존 일정과 겹치는지 바로 알려준다.',
    target: '여러 회사와 동시에 일정을 조율하는 구직자',
    serviceForm: '웹 서비스',
    whyLinked: '면접 일정이 겹치는 걸 뒤늦게 알았다는 근거를 정확히 겨냥한다.',
    howItWorks:
      '면접 일정을 입력하면 등록된 다른 일정과 시간이 겹치는지 확인하고, 겹치면 조정이 필요하다는 경고를 바로 보여준다.',
    coreFeatures: ['일정 등록', '겹침 자동 확인', '조정 필요 경고'],
    differentiator: '지원 현황 전체를 관리하지 않고 겹침 확인이라는 한 가지 기능만 다룬다.',
  },
  {
    id: 'i-job-search-tracking-4',
    problemId: 'p-job-search-tracking',
    name: '무응답 정리 알림',
    oneLiner: '지원 후 일정 기간 응답이 없는 회사를 모아 상태를 물어봐 준다.',
    target: '지원한 곳이 많아 진행 상태를 놓치는 구직자',
    serviceForm: '자동화 스크립트',
    whyLinked:
      '탈락 통보를 못 받은 곳이 진행 중인지 끝난 건지 알 수 없다는 근거를 다룬다.',
    howItWorks:
      '지원일 기준으로 정해진 기간이 지나도 상태 변경이 없는 회사를 모아 정리해 주고, 직접 상태를 표시하도록 묻는다.',
    coreFeatures: ['무응답 기간 추적', '주간 정리 알림', '상태 직접 표시'],
    differentiator: '모든 지원 건을 매번 보여주지 않고 무응답 건만 골라 알려준다.',
  },
  {
    id: 'i-job-search-tracking-5',
    problemId: 'p-job-search-tracking',
    name: '구직 현황 한 장 시트',
    oneLiner: '지원 현황을 관리할 스프레드시트 양식 한 장과 작성 가이드를 제공한다.',
    target: '새 도구 없이 바로 정리를 시작하고 싶은 구직자',
    serviceForm: '웹 서비스',
    whyLinked:
      '지원 현황이 흩어져 헷갈린다는 근거를 소프트웨어 없이 정리 습관만으로 줄이는 최소 개입이다.',
    howItWorks:
      '회사명·지원일·이력서 버전·현재 단계·다음 일정을 담은 스프레드시트 양식과 채우는 방법을 안내해 바로 내려받아 쓰게 한다.',
    coreFeatures: ['구직 현황 양식', '작성 가이드', '즉시 사용 가능한 다운로드'],
    differentiator: '연동이나 자동화 없이 정리 습관을 만드는 데만 집중한다.',
  },
  {
    id: 'i-job-search-tracking-6',
    problemId: 'p-job-search-tracking',
    name: '면접 준비 리마인더',
    oneLiner: '확정된 면접 하루 전, 지원했던 이력서와 자기소개서를 다시 보여준다.',
    target: '여러 회사 면접을 병행하는 구직자',
    serviceForm: '모바일 앱',
    whyLinked:
      '지원 정보가 흩어져 있어 면접 직전 다시 찾아봐야 하는 부담을 겨냥한다.',
    howItWorks:
      '면접 일정을 등록하면 하루 전 해당 회사에 제출했던 이력서·자기소개서·채용 공고 링크를 모아 알림으로 보여준다.',
    coreFeatures: ['면접 전날 알림', '제출 자료 모아보기', '공고 링크 재확인'],
    differentiator: '지원 전 단계가 아니라 면접 직전 준비 단계만 겨냥한다.',
  },
  {
    id: 'i-skill-learning-followthrough-1',
    problemId: 'p-skill-learning-followthrough',
    name: '완강 대신 다음 챕터 알림',
    oneLiner: '전체 진도가 아니라 딱 다음 챕터 하나만 알려준다.',
    target: '강의를 결제만 하고 몇 챕터 못 넘기는 학습자',
    serviceForm: '챗봇',
    whyLinked:
      '초반 몇 챕터를 넘기지 못한다는 근거를 다룬다. 완강이 아니라 다음 한 걸음만 낮추는 접근이다.',
    howItWorks:
      '듣고 있는 강의의 마지막 진도를 기억해 두었다가, 정해진 주기마다 딱 다음 챕터 하나만 알림으로 보내 이어보게 한다.',
    coreFeatures: ['마지막 진도 기억', '다음 챕터 단위 알림', '재개 링크 바로 연결'],
    differentiator: '전체 진도율 대신 다음 한 챕터에만 초점을 맞춘다.',
  },
  {
    id: 'i-skill-learning-followthrough-2',
    problemId: 'p-skill-learning-followthrough',
    name: '학습 동료 매칭',
    oneLiner: '같은 강의를 듣는 사람과 짝을 지어 서로의 진도를 확인하게 한다.',
    target: '혼자 들으면 흐지부지된다는 학습자',
    serviceForm: '웹 서비스',
    whyLinked: '같이 들을 사람이 있었으면 끝까지 갔을 것 같다는 근거를 그대로 반영한다.',
    howItWorks:
      '같은 강의를 등록한 사람끼리 짝을 지어 주고, 서로의 진도 현황을 주기적으로 공유하며 짧은 인증을 남기게 한다.',
    coreFeatures: ['같은 강의 수강생 매칭', '진도 공유', '짧은 인증 기록'],
    differentiator: '콘텐츠나 알고리즘이 아니라 함께 듣는 사람을 만들어 이어가게 한다.',
  },
  {
    id: 'i-skill-learning-followthrough-3',
    problemId: 'p-skill-learning-followthrough',
    name: '진도율 위젯',
    oneLiner: '홈 화면에서 항상 보이는 진도율 위젯으로 미룬 강의를 계속 눈에 띄게 한다.',
    target: '알림을 받아도 다시 열지 않는 학습자',
    serviceForm: '모바일 앱',
    whyLinked:
      '진도율 알림을 받아도 그때뿐이라는 근거를 다룬다. 알림 대신 상시 노출로 접근을 바꾼다.',
    howItWorks:
      '수강 중인 강의의 진도율을 홈 화면 위젯으로 항상 보여주고, 탭하면 마지막으로 보던 위치부터 바로 이어보게 한다.',
    coreFeatures: ['홈 화면 진도율 위젯', '마지막 위치 이어보기', '여러 강의 동시 표시'],
    differentiator: '푸시 알림이 아니라 항상 보이는 화면으로 존재감을 유지한다.',
  },
  {
    id: 'i-skill-learning-followthrough-4',
    problemId: 'p-skill-learning-followthrough',
    name: '완강 마감일 설정기',
    oneLiner: '강의를 결제할 때 스스로 마감일을 정하고 지키는지 확인해 준다.',
    target: '마감이 있어야 끝까지 듣는다는 학습자',
    serviceForm: '브라우저 확장 프로그램',
    whyLinked:
      '완강한 강의는 스터디나 마감이 있었던 것뿐이라는 근거를 다룬다. 마감이라는 조건을 인위적으로 만드는 접근이다.',
    howItWorks:
      '강의 결제 페이지에서 확장 프로그램이 마감일을 설정하도록 유도하고, 마감일이 다가오면 남은 챕터 수를 계산해 알려준다.',
    coreFeatures: ['결제 시점 마감일 설정', '남은 챕터 계산', '마감 임박 알림'],
    differentiator: '새 학습 콘텐츠를 만들지 않고 결제 시점의 다짐을 관리 대상으로 삼는다.',
  },
  {
    id: 'i-skill-learning-followthrough-5',
    problemId: 'p-skill-learning-followthrough',
    name: '결제 전 재고 확인',
    oneLiner: '새 강의를 결제하려 할 때 이미 사둔 미완강 강의를 먼저 보여준다.',
    target: '강의를 반복해서 새로 결제하는 학습자',
    serviceForm: '브라우저 확장 프로그램',
    whyLinked:
      '강의를 5개 사면 1개도 완강 못 한다는 근거를 결제 시점에서 막는 최소 개입이다.',
    howItWorks:
      '강의 플랫폼 결제 버튼을 누르는 순간 이미 구매했지만 다 듣지 않은 강의 목록을 먼저 보여주고, 계속 진행할지 묻는다.',
    coreFeatures: ['미완강 강의 감지', '결제 시점 알림', '계속 진행 여부 선택'],
    differentiator: '새로운 학습 기능 없이 결제 순간의 판단만 한 번 더 끼워 넣는다.',
  },
  {
    id: 'i-skill-learning-followthrough-6',
    problemId: 'p-skill-learning-followthrough',
    name: '완강 선언 한 줄 게시판',
    oneLiner: '오늘 들을 강의 한 줄을 적어 올리는 것만으로 시작하는 가벼운 게시판.',
    target: '거창한 도구 없이 우선 시작해보고 싶은 학습자',
    serviceForm: '웹 서비스',
    whyLinked:
      '흐지부지되는 이유가 계기가 없어서라는 근거를 소프트웨어 기능 대신 짧은 공개 선언 습관으로 접근한다.',
    howItWorks:
      '오늘 들을 강의와 목표 챕터를 한 줄로 적어 올리는 게시판만 제공하고, 다음 날 이어서 적으면 자연히 기록이 쌓이게 한다.',
    coreFeatures: ['한 줄 선언 게시', '연속 기록 표시', '진도 관리 기능 없음'],
    differentiator: '진도 추적이나 알림 기능 없이 짧은 공개 선언만으로 계기를 만든다.',
  },
  {
    id: 'i-subscription-waste-1',
    problemId: 'p-subscription-waste',
    name: '결제일 통합 캘린더',
    oneLiner:
      '여러 서비스의 결제일과 무료 체험 종료일을 한 캘린더에 모아 보여준다.',
    target: '구독 서비스를 여러 개 동시에 쓰는 사람',
    serviceForm: '모바일 앱',
    whyLinked:
      '무료 체험 종료일을 까먹어 결제로 넘어간다는 근거를 다룬다. 흩어진 날짜를 한 곳에 모으는 접근이다.',
    howItWorks:
      '구독 중인 서비스와 결제일을 등록하면 캘린더에 모아 보여주고, 무료 체험은 종료 며칠 전 별도로 표시한다.',
    coreFeatures: ['구독 결제일 등록', '통합 캘린더 보기', '체험 종료 별도 표시'],
    differentiator: '각 서비스 앱을 따로 확인하지 않고 한 화면에서 전체 일정을 본다.',
  },
  {
    id: 'i-subscription-waste-2',
    problemId: 'p-subscription-waste',
    name: '체험 종료 하루 전 알림',
    oneLiner: '무료 체험이 끝나기 정확히 하루 전에 해지 여부를 묻는다.',
    target: '체험 후 자동 결제로 넘어가는 걸 반복해서 놓치는 사람',
    serviceForm: '챗봇',
    whyLinked:
      '체험 해지일을 캘린더에 적어두지 않으면 반드시 잊는다는 근거를 정확히 겨냥한다.',
    howItWorks:
      '가입한 무료 체험의 종료일을 등록하면 하루 전 알림을 보내 계속 쓸지 해지할지 선택하게 하고, 해지를 고르면 해지 페이지 링크를 바로 연결한다.',
    coreFeatures: ['체험 종료일 등록', '하루 전 선택 알림', '해지 페이지 바로가기'],
    differentiator: '결제일 전체가 아니라 놓치기 가장 쉬운 체험 종료 시점 하나에 집중한다.',
  },
  {
    id: 'i-subscription-waste-3',
    problemId: 'p-subscription-waste',
    name: '해지 절차 안내',
    oneLiner: '해지 절차가 복잡한 서비스마다 정확한 해지 경로를 단계별로 안내한다.',
    target: '해지 절차가 복잡해서 미루다 또 결제되는 사람',
    serviceForm: '브라우저 확장 프로그램',
    whyLinked:
      '해지하려고 들어가면 절차가 복잡해서 미루다가 또 결제됐다는 근거를 다룬다.',
    howItWorks:
      '구독 서비스의 해지 페이지에 들어가면 실제 해지까지 필요한 클릭 단계를 미리 안내하는 안내창을 띄운다.',
    coreFeatures: ['서비스별 해지 경로 안내', '단계별 클릭 가이드', '해지 완료 확인 표시'],
    differentiator: '결제를 관리하는 대신 해지라는 마지막 단계의 진입 장벽을 낮춘다.',
  },
  {
    id: 'i-subscription-waste-4',
    problemId: 'p-subscription-waste',
    name: '가족 구독 중복 확인',
    oneLiner: '가족 구성원의 구독 목록을 모아 겹치는 서비스를 찾아 준다.',
    target: '가족이 각자 구독료를 내고 있는 가구',
    serviceForm: '웹 서비스',
    whyLinked:
      '가족 구성원이 각자 구독해 겹치는 서비스를 뒤늦게 발견했다는 근거를 다룬다.',
    howItWorks:
      '가족 구성원을 초대해 각자의 구독 목록을 등록하게 하고, 같은 서비스를 중복 구독 중이면 표시해 통합을 제안한다.',
    coreFeatures: ['가족 구성원 초대', '구독 목록 통합', '중복 서비스 표시'],
    differentiator: '개인 구독 관리가 아니라 가족 단위 중복을 겨냥한다.',
  },
  {
    id: 'i-subscription-waste-5',
    problemId: 'p-subscription-waste',
    name: '카드 명세서 훑어보기 습관',
    oneLiner: '매달 카드 명세서가 오면 구독 항목만 다섯 줄로 뽑아 보여준다.',
    target: '명세서를 잘 확인하지 않는 사람',
    serviceForm: '자동화 스크립트',
    whyLinked:
      '카드 명세서를 보고서야 안 쓰는 구독료를 알았다는 근거를, 명세서 확인 자체를 쉽게 만들어 접근한다.',
    howItWorks:
      '매달 카드 명세서 데이터에서 정기 결제로 보이는 항목만 추려 짧은 목록으로 정리해 보내준다.',
    coreFeatures: ['정기 결제 항목 추출', '월간 요약 발송', '전월 대비 변화 표시'],
    differentiator: '구독을 새로 등록하게 하지 않고 이미 나가는 명세서에서 정보를 뽑아낸다.',
  },
  {
    id: 'i-subscription-waste-6',
    problemId: 'p-subscription-waste',
    name: '구독 목록 종이 체크리스트',
    oneLiner: '가입한 구독 서비스를 손으로 적어 두는 체크리스트 양식 한 장을 제공한다.',
    target: '앱 설치 없이 지금 당장 점검해보고 싶은 사람',
    serviceForm: '웹 서비스',
    whyLinked:
      '구독이 여러 곳에 흩어져 있어 놓친다는 근거를 소프트웨어 없이 한 번 손으로 점검하는 방식으로 접근한다.',
    howItWorks:
      '서비스명·결제일·월 금액을 적는 칸이 있는 체크리스트 양식을 내려받아, 카드 명세서를 보며 한 번에 채워보게 안내한다.',
    coreFeatures: ['구독 점검 체크리스트 양식', '작성 가이드', '인쇄용 레이아웃'],
    differentiator: '연동이나 자동 알림 없이 한 번의 수동 점검만으로 전체 구독을 파악하게 한다.',
  },
  {
    id: 'i-meal-planning-1',
    problemId: 'p-meal-planning',
    name: '냉장고 재료 기반 메뉴 추천',
    oneLiner: '냉장고에 있는 재료를 적으면 오늘 만들 수 있는 메뉴를 몇 개 골라 준다.',
    target: '재료는 있는데 뭘 만들지 못 정하는 사람',
    serviceForm: '모바일 앱',
    whyLinked:
      '재료는 있는데 뭘 만들지 몰라 결국 배달을 시켰다는 근거를 다룬다.',
    howItWorks:
      '가지고 있는 재료 몇 가지를 입력하면 그 재료로 만들 수 있는 메뉴 후보를 조리 시간과 함께 보여준다.',
    coreFeatures: ['보유 재료 입력', '메뉴 후보 추천', '예상 조리 시간 표시'],
    differentiator: '레시피를 검색하게 하는 대신 있는 재료에서 거꾸로 메뉴를 좁혀 준다.',
  },
  {
    id: 'i-meal-planning-2',
    problemId: 'p-meal-planning',
    name: '일주일 메뉴 자동 배정',
    oneLiner: '일주일치 메뉴를 한 번에 짜서 매일 아침 오늘 메뉴만 알려준다.',
    target: '매일 새로 정하는 게 피곤한 사람',
    serviceForm: '웹 서비스',
    whyLinked:
      '매일 저녁 메뉴를 정하는 결정 자체가 피로하다는 근거를, 결정을 하루 단위가 아니라 주 단위로 한 번에 처리하는 방식으로 다룬다.',
    howItWorks:
      '선호하는 음식 유형과 최근 먹은 메뉴를 반영해 일주일치 메뉴를 미리 배정하고, 매일 정해진 시간에 오늘 메뉴만 알려준다.',
    coreFeatures: ['주간 메뉴 자동 배정', '최근 식단 반영', '일일 메뉴 알림'],
    differentiator: '매일 결정하는 대신 결정 시점을 주 1회로 줄인다.',
  },
  {
    id: 'i-meal-planning-3',
    problemId: 'p-meal-planning',
    name: '메뉴 다양화 알림',
    oneLiner: '같은 메뉴가 반복되면 다른 메뉴를 슬쩍 끼워 넣어 준다.',
    target: '매주 같은 몇 가지 메뉴만 반복한다는 사람',
    serviceForm: '챗봇',
    whyLinked: '매주 같은 몇 가지 메뉴만 반복하다 질렸다는 근거를 다룬다.',
    howItWorks:
      '최근 먹은 메뉴 기록을 바탕으로 반복 빈도가 높은 메뉴를 확인하고, 대신 시도해볼 만한 새 메뉴를 주기적으로 제안한다.',
    coreFeatures: ['최근 메뉴 기록', '반복 빈도 확인', '대체 메뉴 제안'],
    differentiator: '메뉴를 매번 새로 추천하지 않고 반복이 심할 때만 개입한다.',
  },
  {
    id: 'i-meal-planning-4',
    problemId: 'p-meal-planning',
    name: '장보기 목록 자동 생성',
    oneLiner: '정한 메뉴에 필요한 재료만 뽑아 장보기 목록을 만들어 준다.',
    target: '계획 없이 장을 봐서 재료를 버리게 되는 사람',
    serviceForm: '브라우저 확장 프로그램',
    whyLinked: '계획 없이 사서 결국 상해서 버리는 재료가 많다는 근거를 다룬다.',
    howItWorks:
      '이번 주 정한 메뉴를 바탕으로 필요한 재료를 계산해 장보기 목록으로 정리하고, 장보기 사이트에서 그대로 담을 수 있게 연결한다.',
    coreFeatures: ['메뉴 기반 재료 계산', '장보기 목록 생성', '쇼핑몰 담기 연동'],
    differentiator: '메뉴 추천이 아니라 정해진 메뉴를 실제 장보기로 옮기는 단계에 집중한다.',
  },
  {
    id: 'i-meal-planning-5',
    problemId: 'p-meal-planning',
    name: '저녁 메뉴 주사위',
    oneLiner: '정하기 귀찮은 날은 몇 가지 후보 중 하나를 무작위로 골라 준다.',
    target: '결정 자체를 아예 넘기고 싶은 사람',
    serviceForm: '자동화 스크립트',
    whyLinked:
      '매번 처음부터 메뉴를 정하는 결정 자체가 피로하다는 근거를, 아예 결정을 대신 내려주는 방식으로 가장 단순하게 다룬다.',
    howItWorks:
      '미리 등록해 둔 메뉴 후보 중 하나를 매일 저녁 정해진 시각에 무작위로 골라 알려준다.',
    coreFeatures: ['메뉴 후보 등록', '매일 무작위 선택', '마음에 안 들면 다시 뽑기'],
    differentiator: '추천 로직 없이 결정을 무작위에 맡겨 고민 시간을 아예 없앤다.',
  },
  {
    id: 'i-meal-planning-6',
    problemId: 'p-meal-planning',
    name: '냉장고 재료 소진 순서표',
    oneLiner: '유통기한이 임박한 재료부터 먼저 쓰도록 순서만 적어 붙여 준다.',
    target: '앱보다 냉장고 앞에 붙여 둘 무언가가 필요한 사람',
    serviceForm: '웹 서비스',
    whyLinked:
      '장 본 재료가 상해서 버려진다는 근거를 메뉴 추천이 아니라 소진 순서를 정하는 가장 단순한 방식으로 접근한다.',
    howItWorks:
      '구입한 재료와 예상 유통기한을 적으면 먼저 써야 할 순서대로 정리한 목록을 인쇄해 냉장고에 붙여 두게 한다.',
    coreFeatures: ['재료·유통기한 입력', '소진 우선순위 정렬', '인쇄용 목록 출력'],
    differentiator: '메뉴를 정해주지 않고 무엇부터 써야 하는지만 알려준다.',
  },
  {
    id: 'i-home-maintenance-1',
    problemId: 'p-home-maintenance',
    name: '관리 주기 통합 알림',
    oneLiner:
      '정수기 필터, 에어컨 청소, 보일러 점검 주기를 한 곳에 등록해 때가 되면 알려준다.',
    target: '여러 가전·설비를 따로 챙겨야 하는 1인 가구',
    serviceForm: '모바일 앱',
    whyLinked:
      '필터 교체나 점검 시기를 지나서야 알아차린다는 근거를 다룬다. 흩어진 주기를 한 곳에 모으는 접근이다.',
    howItWorks:
      '집에 있는 가전·설비와 각각의 권장 관리 주기를 등록하면 시기가 다가올 때 항목별로 알림을 보낸다.',
    coreFeatures: ['가전·설비 등록', '항목별 주기 설정', '시기별 알림'],
    differentiator: '스티커나 개별 앱 대신 집안의 모든 관리 주기를 한 화면에서 관리한다.',
  },
  {
    id: 'i-home-maintenance-2',
    problemId: 'p-home-maintenance',
    name: '이상 신호 기록장',
    oneLiner: '냄새나 소음처럼 애매한 이상 신호를 짧게 남겨 다음 점검 근거로 쓴다.',
    target: '문제가 애매해서 점검을 미루게 되는 사람',
    serviceForm: '챗봇',
    whyLinked:
      '에어컨 냄새가 나고서야 마지막 청소가 언제였는지 찾아본다는 근거를 다룬다. 이상 신호를 그때그때 기록해 두는 접근이다.',
    howItWorks:
      '이상하다고 느낀 순간 한 줄로 기록해 두면 해당 설비의 마지막 관리 이력과 함께 모아 보여주고, 반복되면 점검을 제안한다.',
    coreFeatures: ['이상 신호 한 줄 기록', '설비별 이력 연결', '반복 시 점검 제안'],
    differentiator: '정기 알림이 아니라 사용자가 느낀 이상 신호를 기준으로 개입한다.',
  },
  {
    id: 'i-home-maintenance-3',
    problemId: 'p-home-maintenance',
    name: '점검 문자 일정 재확인',
    oneLiner: '점검 안내 문자를 받으면 실제 가능한 날짜로 다시 예약하도록 도와준다.',
    target: '안내 문자를 받고도 시간이 안 맞아 미루는 사람',
    serviceForm: '자동화 스크립트',
    whyLinked:
      '점검 안내 문자가 와도 시간이 안 돼서 미루다 잊는다는 근거를 정확히 겨냥한다.',
    howItWorks:
      '점검 안내 문자를 받으면 캘린더의 빈 시간을 확인해 가능한 날짜 후보를 만들어 알려주고, 재예약 여부를 며칠 뒤 다시 확인한다.',
    coreFeatures: ['안내 문자 감지', '빈 시간 기반 날짜 제안', '재예약 여부 재확인'],
    differentiator: '점검을 새로 관리하지 않고 이미 오는 안내 문자에 이어지는 다음 행동만 돕는다.',
  },
  {
    id: 'i-home-maintenance-4',
    problemId: 'p-home-maintenance',
    name: '관리 이력 스티커 QR',
    oneLiner: '가전에 붙이는 QR 스티커를 스캔하면 마지막 관리일과 다음 예정일을 보여준다.',
    target: '스티커에 직접 날짜를 적어도 놓치는 사람',
    serviceForm: '브라우저 확장 프로그램',
    whyLinked:
      '필터 교체 스티커를 붙여도 유효기간이 지난 걸 뒤늦게 발견한다는 근거를 다룬다. 스티커 자체를 조회 가능한 형태로 바꾸는 접근이다.',
    howItWorks:
      '가전마다 QR 스티커를 붙이고 스캔하면 마지막 관리일을 기록·조회할 수 있는 페이지로 연결해 다음 예정일을 계산해 보여준다.',
    coreFeatures: ['QR 스티커 발급', '스캔 시 이력 조회', '다음 예정일 계산'],
    differentiator: '손으로 적는 스티커의 한계를 스캔으로 조회하는 방식으로 보완한다.',
  },
  {
    id: 'i-home-maintenance-5',
    problemId: 'p-home-maintenance',
    name: '우리 집 관리 주기표',
    oneLiner: '흔한 가전·설비의 권장 관리 주기를 정리한 표 한 장을 냉장고에 붙여 둔다.',
    target: '앱 없이 지금 바로 기준부터 잡고 싶은 사람',
    serviceForm: '웹 서비스',
    whyLinked:
      '관리 주기를 기억하고 있다가 챙기는 사람이 없다는 근거를, 소프트웨어 없이 기준표 하나로 접근하는 최소 개입이다.',
    howItWorks:
      '정수기, 에어컨, 보일러 등 흔한 항목의 일반적인 권장 관리 주기를 정리한 표를 제공하고, 마지막 관리일을 손으로 적어 넣게 한다.',
    coreFeatures: ['항목별 권장 주기 표', '손으로 기입하는 칸', '인쇄용 레이아웃'],
    differentiator: '알림이나 연동 없이 기준을 아는 것만으로 스스로 챙기게 한다.',
  },
  {
    id: 'i-home-maintenance-6',
    problemId: 'p-home-maintenance',
    name: '출장 서비스 예약 한 번에 묶기',
    oneLiner: '여러 설비의 점검이 몰리는 시기를 찾아 한 번의 출장으로 묶어 예약한다.',
    target: '출장 기사를 여러 번 부르기 번거로운 가구',
    serviceForm: '웹 서비스',
    whyLinked:
      '관리 시기를 놓쳐 문제가 생기고 나서야 알아차린다는 근거를, 예약 자체의 번거로움을 줄여 미리 하도록 접근한다.',
    howItWorks:
      '등록된 설비들의 다음 관리 예정일이 가까운 시기를 찾아, 여러 업체 출장을 같은 날짜로 묶어 예약하도록 제안한다.',
    coreFeatures: ['설비별 예정일 확인', '일정 묶음 제안', '업체별 예약 연결'],
    differentiator: '개별 알림에서 그치지 않고 실제 예약 행동으로 이어지는 번거로움을 줄인다.',
  },
];
