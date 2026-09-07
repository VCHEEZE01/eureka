# DESIGN.md

## 1. Overall Direction

전체 디자인은 깔끔하고 밝으며, 정보가 한눈에 들어오는 방향으로 구성한다.

핵심 키워드:
- 가독성
- 깔끔함
- 직관성
- 충분한 여백
- 부드러운 색감
- 명확한 정보 위계

디자인보다 콘텐츠가 먼저 보여야 한다.

과한 장식이나 시각 효과보다
사용자가 서비스의 기능과 정보를 빠르게 이해하는 것을 우선한다.


## 2. Font

한국어 기본 폰트:
Pretendard

Fallback:
-apple-system,
BlinkMacSystemFont,
"Segoe UI",
sans-serif

폰트 굵기:
- 일반 본문: 400
- 강조 본문: 500
- 소제목: 600
- 큰 제목: 700

너무 많은 굵기를 혼용하지 않는다.


## 3. Typography

Page Title:
32~40px
font-weight: 700

Section Title:
24~32px
font-weight: 700

Card / Content Title:
18~22px
font-weight: 600

Body:
15~17px
font-weight: 400
line-height: 1.6

Caption / Description:
13~14px

한 화면에 지나치게 많은 크기의 폰트를 사용하지 않는다.


## 4. Main Colors

Primary Text:
#191F28

Secondary Text:
#4E5968

Muted Text:
#8B95A1

Primary Background:
#FFFFFF

Secondary Background:
#F7F9FA

Border:
#E5E8EB

Primary Blue:
#3182F6

Light Blue:
#E8F3FF

Soft Blue Background:
#F2F8FF


## 5. Accent Colors

강조 색상은 기본적으로 Blue 계열 하나를 사용한다.

주요 버튼:
#3182F6

Hover:
#1B64DA

Selected / Active Background:
#E8F3FF

색상을 여러 개 섞지 않는다.

상태 표현이 필요한 경우에만 제한적으로 사용한다.

Success:
#20C997

Warning:
#F59F00

Error:
#F04452


## 6. Gradient

그라데이션은 메인 UI에서 남발하지 않는다.

히어로 영역이나 큰 배경에서만
아주 옅게 사용할 수 있다.

추천:

light blue
→ sky blue
→ pale yellow

그라데이션은 형태가 명확하게 보이지 않고
빛이 퍼지는 것처럼 자연스럽게 표현한다.


## 7. Background

기본 페이지:
#FFFFFF

보조 영역:
#F7F9FA

정보 영역을 구분하기 위해
회색 배경을 사용할 수 있다.

배경색만으로도 영역이 충분히 구분된다면
불필요한 border나 shadow를 추가하지 않는다.


## 8. Card

카드는 꼭 필요한 경우에만 사용한다.

Card Background:
#FFFFFF

Border:
1px solid #E5E8EB

Radius:
16px

Shadow:
기본적으로 사용하지 않거나 매우 약하게 사용한다.

권장:
0 2px 8px rgba(0,0,0,0.04)

카드 안쪽 padding:
20~24px


## 9. Button

Primary Button:

background:
#3182F6

text:
#FFFFFF

height:
44~48px

border-radius:
10~12px

font-weight:
600


Secondary Button:

background:
#FFFFFF

border:
1px solid #DDE1E6

text:
#333D4B


Ghost Button:

background:
transparent

text:
#4E5968


## 10. Input

Input height:
44~48px

Background:
#FFFFFF

Border:
#DDE1E6

Focus Border:
#3182F6

Radius:
10~12px

Placeholder:
#B0B8C1

입력 영역이 명확하게 보이도록 한다.


## 11. Spacing

작은 간격:
8px

기본 간격:
16px

컴포넌트 간:
24px

섹션 간:
64~96px

한 화면을 꽉 채우려고 하지 않는다.

정보 사이에 충분한 여백을 둔다.


## 12. Layout

Desktop 최대 콘텐츠 폭:
1100~1200px

Horizontal Padding:
24~32px

Mobile:
20px

텍스트 콘텐츠는 너무 넓게 펼치지 않는다.

긴 설명 영역은 약 700~800px 이내로 유지한다.


## 13. Visual Hierarchy

사용자가 화면을 봤을 때 다음 순서로 보여야 한다.

1. 지금 화면이 무엇인지
2. 가장 중요한 정보
3. 사용자가 해야 할 행동
4. 추가 설명

색상보다 크기와 여백을 사용해 중요도를 표현한다.


## 14. Icons

아이콘은 Lucide 계열을 기본으로 사용한다.

아이콘을 장식 목적으로 남발하지 않는다.

한 화면에서 같은 의미의 아이콘 스타일을 통일한다.


## 15. Don't

다음 요소는 피한다.

- 과한 그림자
- 과한 그라데이션
- 보라색 AI 스타일 남발
- 모든 정보를 카드로 감싸기
- 너무 많은 색상
- 너무 작은 폰트
- 긴 문장 덩어리
- 과도한 애니메이션
- 과한 Glassmorphism
- 카드마다 다른 radius
- 콘텐츠를 화면 끝까지 빽빽하게 채우기


## 16. Final Goal

최종 결과물은

“디자인이 화려하다”가 아니라

“보기 편하다”
“무슨 서비스인지 바로 이해된다”
“정보를 찾기 쉽다”
“깔끔하고 신뢰감 있다”

라는 느낌을 주는 것을 목표로 한다.

새로운 화면이나 컴포넌트를 만들 때
시각적 화려함보다 정보의 우선순위와 가독성을 먼저 판단한다.
