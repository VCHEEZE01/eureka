/**
 * 공유용 단일 HTML의 진입점.
 *
 * Next.js 앱과 화면(screens/)을 그대로 공유하고, 라우팅만 해시로 바꾼다.
 * 덕분에 UI를 두 벌 관리하지 않아도 된다.
 */

import { createRoot } from 'react-dom/client';
import { NavProvider, useHashNav } from '@/lib/nav';
import { CombineConfirmScreen, CombinedDetailScreen } from '@/screens/Combine';
import { BasicIdeasScreen, IdeaDetailScreen } from '@/screens/Ideas';
import { LandingScreen } from '@/screens/Landing';
import { LoginScreen } from '@/screens/Login';
import { MyPageScreen } from '@/screens/MyPage';
import { OnboardingScreen } from '@/screens/Onboarding';
import {
  PersonalizeFormScreen,
  PersonalizeResultScreen,
  PersonalizedIdeaDetailScreen,
} from '@/screens/Personalize';
import { ProblemDetailScreen } from '@/screens/ProblemDetail';
import { ProblemListScreen } from '@/screens/ProblemList';

/**
 * 경로 → 화면 매핑.
 * Next.js의 app/ 라우트 구조와 같은 경로를 쓴다.
 */
function route(path: string) {
  const seg = path.split('/').filter(Boolean);

  if (seg.length === 0) return <LandingScreen />;

  if (seg[0] === 'onboarding') return <OnboardingScreen />;
  if (seg[0] === 'login') return <LoginScreen />;
  if (seg[0] === 'mypage') return <MyPageScreen />;

  if (seg[0] === 'problems') {
    if (seg.length === 1) return <ProblemListScreen />;
    if (seg[1] === 'combine') return <CombineConfirmScreen />;
    if (seg[2] === 'ideas') return <BasicIdeasScreen problemId={seg[1]} />;
    return <ProblemDetailScreen problemId={seg[1]} />;
  }

  if (seg[0] === 'combined' && seg[1]) return <CombinedDetailScreen combinedId={seg[1]} />;
  if (seg[0] === 'ideas' && seg[1]) return <IdeaDetailScreen ideaId={seg[1]} />;

  if (seg[0] === 'personalize') {
    if (seg[1] === 'from' && seg[2]) return <PersonalizeFormScreen baseId={seg[2]} />;
    if (seg[1] && seg[2]) return <PersonalizedIdeaDetailScreen id={seg[1]} ideaId={seg[2]} />;
    if (seg[1]) return <PersonalizeResultScreen id={seg[1]} />;
  }

  return <LandingScreen />;
}

function App() {
  const nav = useHashNav();
  return <NavProvider value={nav}>{route(nav.path)}</NavProvider>;
}

const container = document.getElementById('root');
if (container) createRoot(container).render(<App />);
