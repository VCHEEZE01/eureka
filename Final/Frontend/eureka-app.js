/* =====================================================================
 * eureka-app.js — 디자인 HTML 과 분리된 연동 계층
 *
 * 왜 이 파일이 따로 있나
 *   팀원이 피그마에서 뽑은 새 v1-trend-incubator.html 을 주기적으로 준다.
 *   그 파일에는 디자인만 들어 있어서, 예전에는 새 파일이 올 때마다 백엔드
 *   연동 코드가 통째로 지워지고 손으로 다시 이식해야 했다(V1.3 때 실제로
 *   겪음). 디자인과 무관한 로직을 여기로 빼두면 새 HTML 이 와도
 *   "복사 → <head> 에 script 두 줄 → 체크리스트" 로 끝난다.
 *   자세한 절차는 옆의 INTEGRATION.md 참고.
 *
 * ─────────────────────────────────────────────────────────────────────
 * ★ 이 파일을 고치기 전에 반드시 읽을 것 — 세 가지 지뢰
 *
 *  1. 이건 **클래식 스크립트**다. type="module" 로 바꾸지 마라.
 *     모듈은 자체 스코프를 가져서 디자인의 savedIdeas 같은 전역에
 *     접근할 수 없다. 그러면 이 파일의 존재 이유가 사라진다.
 *
 *  2. 디자인이 선언한 이름을 **재선언하지 마라.**
 *     디자인 HTML 최상위의 `let savedIdeas` 와 이 파일 최상위의
 *     `let savedIdeas` 가 만나면 파싱 단계에서 SyntaxError 가 나고
 *     **파일 전체가 실행되지 않는다.** (런타임 오류가 아니라 파싱
 *     오류라 try/catch 로도 못 막는다.)
 *     → 그래서 아래 모든 코드를 IIFE 로 감쌌다. 안쪽에서 선언하면
 *       충돌하지 않으면서도, 바깥 전역은 맨이름으로 읽고 쓸 수 있다.
 *
 *  3. 최상위에서 **절대 throw 하지 마라.**
 *     중간에 터지면 덮어쓰기가 반쯤만 설치된 상태로 남는데, 이건
 *     아예 설치 안 된 것보다 나쁘다(어디까지 바뀐 건지 알 수 없다).
 *     그래서 부팅 전체가 try/catch 안에 있다.
 *
 *  4. supabase-js 의 전역 이름은 `supabase` 다.
 *     `const supabase = supabase.createClient(...)` 라고 쓰면 TDZ
 *     오류가 난다. 클라이언트는 `window.sb` 에 둔다(아래 참고).
 * ===================================================================== */

(function () {
  'use strict';

  var VERSION = '0.4.0-refresh';    // 7단계: + 새로고침 쿼터 버튼.
  var LOG = '[eureka]';

  /* ── 디자인 HTML 과의 계약 ──────────────────────────────────────────
   * 새 디자인이 왔을 때 여기 적힌 것이 하나라도 없으면 연동이 조용히
   * 안 붙는다. 그래서 부팅할 때 직접 확인하고 콘솔에 경고를 찍는다.
   * "조용한 실패"를 "시끄러운 실패"로 바꾸는 게 목적이다. */

  var CONTRACT = {
    // 맨이름으로 읽고 쓰는 전역 (디자인 script 의 최상위 let/const)
    globals: [
      'savedKeywords', 'savedIdeas', 'configSettings',
      'selectedKeyword', 'generatedIdeas'
    ],
    // 나중 단계에서 window.<이름> 으로 덮어쓸 함수
    overrides: [
      'toggleSaveKeyword', 'toggleSaveIdea', 'removeSavedKeyword',
      'removeSavedIdea', 'updateSavedCounts', 'executeIdeaGeneration',
      'handleFigmaLogin', 'handleFigmaSignup'
    ],
    // 감싸거나 그대로 호출할 함수 (대체하지 않는다 — 디자인 소유)
    uses: [
      'renderIdeasTabs', 'renderSavedScreen', 'showToast', 'navigateTo',
      'findKeywordById', 'renderBestKeywordsGrid', 'renderWeeklySlider'
    ],
    // 서버 생성 실패 시 오프라인 폴백으로만 쓴다 — 없으면 폴백 없이
    // 로딩 화면만 사라지고 오류 토스트를 띄운다(치명적이지 않음).
    optionalUses: ['finishIdeaGeneration']
  };

  var SELECTORS = {
    ideaTabsBox: 'ideas-tabs-container',
    resultScreen: 'result-main-screen',
    ideaDetailBox: 'active-idea-card-container',
    toast: 'toast-popup',
    resultLoadingScreen: 'result-loading-screen',
    loadingStepText: 'loading-step-text',
    resultKeywordName: 'result-keyword-name'
  };

  // 백엔드 IdeaSpec(스네이크케이스) → 이 디자인의 아이디어 카드가 기대하는
  // 모양. 이 디자인은 toIdeaView() 같은 매핑 함수를 자체적으로 갖고
  // 있지 않으므로 여기서 직접 변환한다(Final/Backend/app/schemas/idea_models.py 참고).
  function mapBackendIdea(x) {
    return {
      id: x.id || '',
      name: x.name || x.short_name || '아이디어',
      shortName: x.short_name || x.name || '',
      approach: x.approach || '',
      slogan: x.slogan || '',
      target: x.target || '',
      problem: x.problem || '',
      solution: x.solution || '',
      concept: x.architecture || '',
      diff: x.diff || '',
      mvpFeatures: x.mvp_features || [],
      futureFeatures: x.future_features || [],
      stack: x.stack || '',
      prompt: x.prompt || ''
    };
  }

  // 이 디자인의 script 최상위에는 period 라벨→키 매핑이 없다(예전
  // 디자인의 PERIOD_KEY 가 사라짐). configSettings.period 라벨은
  // '하루'/'일주일'/'한 달 이상' 그대로이므로 여기서 자체 관리한다.
  // toggleSaveIdea 오버라이드(보관함 저장 시 기간 태깅)가 이걸 쓴다.
  var EUREKA_PERIOD_KEY = { '하루': 'day', '일주일': 'week', '한 달 이상': 'month' };

  /* ── 환경 판정 ─────────────────────────────────────────────────────
   * file:// 로 더블클릭해 열면 서버 API 도 Supabase 도 못 쓴다.
   * 그 경우 디자인의 오프라인 폴백이 그대로 동작해야 하므로,
   * 이 파일은 조용히 아무것도 하지 않는다(그것도 의도된 동작이다). */
  var isServed = ['http:', 'https:'].indexOf(location.protocol) !== -1;
  var isDebug = /[?&]debug=1\b/.test(location.search);

  /* ── 계약 점검 ─────────────────────────────────────────────────────── */

  function globalExists(name) {
    // 최상위 let/const 는 window 의 속성이 아니라 전역 렉시컬 환경에
    // 있으므로 window[name] 으로는 안 잡힌다. 실제로 이름을 평가해 본다.
    try {
      // eslint-disable-next-line no-new-func
      return new Function('return typeof ' + name + ' !== "undefined";')();
    } catch (e) {
      return false;
    }
  }

  function checkContract() {
    var missing = { globals: [], overrides: [], uses: [], dom: [] };

    CONTRACT.globals.forEach(function (n) {
      if (!globalExists(n)) missing.globals.push(n);
    });
    CONTRACT.overrides.concat(CONTRACT.uses).forEach(function (n) {
      if (typeof window[n] !== 'function') {
        (CONTRACT.overrides.indexOf(n) !== -1 ? missing.overrides : missing.uses).push(n);
      }
    });
    Object.keys(SELECTORS).forEach(function (k) {
      if (!document.getElementById(SELECTORS[k])) missing.dom.push(SELECTORS[k]);
    });

    var total = missing.globals.length + missing.overrides.length +
                missing.uses.length + missing.dom.length;

    if (total === 0) {
      if (isDebug) console.info(LOG, 'v' + VERSION, '통합 계약 확인 — 이상 없음');
      return true;
    }

    console.warn(
      LOG + ' 통합 계약 누락 ' + total + '건 — 새 디자인 HTML 이 들어왔다면 ' +
      'Final/Frontend/INTEGRATION.md 의 체크리스트를 다시 밟으세요.'
    );
    if (missing.globals.length)   console.warn(LOG, '  없는 전역   :', missing.globals.join(', '));
    if (missing.overrides.length) console.warn(LOG, '  없는 함수(덮어쓸 대상):', missing.overrides.join(', '));
    if (missing.uses.length)      console.warn(LOG, '  없는 함수(호출 대상)  :', missing.uses.join(', '));
    if (missing.dom.length)       console.warn(LOG, '  없는 DOM id :', missing.dom.join(', '));

    if (isDebug) showContractBanner(missing, total);
    return false;
  }

  function showContractBanner(missing, total) {
    try {
      var el = document.createElement('div');
      el.style.cssText =
        'position:fixed;left:0;right:0;bottom:0;z-index:99999;padding:10px 16px;' +
        'background:#7F1D1D;color:#FEE2E2;font:600 13px/1.5 -apple-system,sans-serif;';
      el.textContent =
        '[eureka] 통합 계약 누락 ' + total + '건 — ' +
        [].concat(missing.globals, missing.overrides, missing.uses, missing.dom).join(', ');
      document.body.appendChild(el);
    } catch (e) { /* 배너는 부가 기능이다. 실패해도 조용히 넘어간다. */ }
  }

  /* ── 렌더 훅 ────────────────────────────────────────────────────────
   * #ideas-tabs-container 는 renderIdeasTabs() 가 innerHTML 로 통째
   * 갈아치운다. 그 안에 붙인 요소는 카드를 전환할 때마다 사라진다.
   * 그래서 대체하지 않고 **감싸서**, 매 렌더 뒤에 다시 붙일 기회를 만든다.
   * (새로고침 버튼이 여기 올라탄다 — 다음 단계.) */

  var afterTabsRender = [];

  function installTabsHook() {
    var original = window.renderIdeasTabs;
    if (typeof original !== 'function') return false;
    if (original.__eurekaWrapped) return true;   // --reload 등으로 두 번 실행되는 경우 방지

    var wrapped = function () {
      var out = original.apply(this, arguments);
      for (var i = 0; i < afterTabsRender.length; i++) {
        try {
          afterTabsRender[i]();
        } catch (e) {
          // 훅 하나가 터져도 화면 렌더 자체는 끝나야 한다.
          console.warn(LOG, '탭 렌더 훅 실패:', e && e.message);
        }
      }
      return out;
    };
    wrapped.__eurekaWrapped = true;
    wrapped.__original = original;
    window.renderIdeasTabs = wrapped;
    return true;
  }

  /* =====================================================================
   * 인증 — 회원가입/로그인/로그아웃은 브라우저에서 supabase-js가 전담한다.
   * FastAPI는 비밀번호를 보지도, 토큰을 발급하지도 않는다(검증만 한다,
   * app/core/auth.py). GET /api/config 로 anon key를 받아온다 — HTML에
   * 박아두지 않는 이유는 새 디자인이 와도 잃어버릴 수 없게 하기 위해서고,
   * auth_enabled:false 일 때 Supabase 없이도 깔끔히 도는 모드를 얻기
   * 위해서다.
   * ===================================================================== */

  var authEnabled = false;
  var currentSession = null;          // supabase-js Session 객체 또는 null
  var signedInHandlers = [];          // 로그인 성공(세션 확인 포함) 시 부를 함수들
  var signedOutHandlers = [];         // 로그아웃 시 부를 함수들

  function isLoggedIn() {
    return !!(currentSession && currentSession.access_token);
  }

  function currentUser() {
    if (!currentSession || !currentSession.user) return null;
    return { id: currentSession.user.id, email: currentSession.user.email || '' };
  }

  function fireHandlers(list) {
    list.forEach(function (fn) {
      try { fn(currentUser()); } catch (e) { console.warn(LOG, '인증 콜백 실패:', e && e.message); }
    });
  }

  /**
   * apiFetch(path, opts) — 서버 API 호출용 fetch 래퍼.
   *   - 매 요청 직전에 getSession() 을 불러 access_token 을 얻는다.
   *     (변수에 캐시하지 않는 이유: 탭을 오래 열어두면 1시간 뒤 토큰이
   *     만료되는데, supabase-js가 만료 직전 자동 갱신한 최신 토큰을
   *     매번 가져와야 그 문제가 안 생긴다.)
   *   - opts.body 가 문자열이 아니면 JSON으로 인코딩하고 Content-Type을 단다.
   *   - 401을 한 번 받으면 refreshSession() 후 딱 한 번만 재시도한다.
   */
  function getFreshAccessToken() {
    if (!authEnabled || !window.sb) return Promise.resolve(null);
    return window.sb.auth.getSession().then(function (r) {
      var session = r && r.data && r.data.session;
      return session ? session.access_token : null;
    }).catch(function () { return null; });
  }

  function buildRequest(opts, token) {
    var headers = {};
    for (var k in (opts.headers || {})) headers[k] = opts.headers[k];
    var body = opts.body;
    if (body !== undefined && body !== null && typeof body !== 'string' && !(body instanceof FormData)) {
      body = JSON.stringify(body);
      headers['Content-Type'] = 'application/json';
    }
    if (token) headers['Authorization'] = 'Bearer ' + token;
    return { method: opts.method || 'GET', headers: headers, body: body, signal: opts.signal };
  }

  function apiFetch(path, opts) {
    opts = opts || {};
    return getFreshAccessToken().then(function (token) {
      return fetch(path, buildRequest(opts, token));
    }).then(function (res) {
      if (res.status !== 401 || !authEnabled || !window.sb) return res;
      // 401 한 번은 토큰 갱신 후 재시도. 그래도 401이면 그대로 돌려준다
      // (호출부가 "로그인 필요"로 처리하면 된다 — 여기서 강제 로그아웃하지 않는다).
      return window.sb.auth.refreshSession().then(function () {
        return getFreshAccessToken();
      }).catch(function () { return null; }).then(function (retryToken) {
        return fetch(path, buildRequest(opts, retryToken));
      });
    });
  }

  /** apiFetch + JSON 파싱까지. 실패해도 throw하지 않고 {ok:false,...}를 준다
   * — 호출부가 매번 try/catch를 안 써도 되게. */
  function apiFetchJson(path, opts) {
    return apiFetch(path, opts).then(function (res) {
      return res.text().then(function (text) {
        var body = null;
        try { body = text ? JSON.parse(text) : null; } catch (e) { /* JSON이 아닐 수도 있다 */ }
        return { ok: res.ok, status: res.status, body: body };
      });
    }).catch(function (err) {
      return { ok: false, status: 0, body: null, networkError: err };
    });
  }

  /* ── Supabase 클라이언트 초기화 ───────────────────────────────────── */

  function initSupabase(cfg) {
    if (!cfg || !cfg.auth_enabled || !cfg.supabase_url || !cfg.supabase_anon_key) {
      return false;
    }
    if (typeof window.supabase === 'undefined' || typeof window.supabase.createClient !== 'function') {
      console.warn(LOG, 'Supabase SDK가 로드되지 않았습니다(CDN 차단 등) — 로그인 기능을 건너뜁니다.');
      return false;
    }
    // ★ window.sb — window.supabase 는 SDK 전역 이름이라 그대로 덮어쓰면 안 된다.
    window.sb = window.supabase.createClient(cfg.supabase_url, cfg.supabase_anon_key, {
      auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: false }
    });
    return true;
  }

  function bootSession() {
    window.sb.auth.getSession().then(function (r) {
      currentSession = (r && r.data && r.data.session) || null;
      if (currentSession) fireHandlers(signedInHandlers);
    });
    window.sb.auth.onAuthStateChange(function (event, session) {
      var wasLoggedIn = isLoggedIn();
      currentSession = session || null;
      if (event === 'SIGNED_IN' || (isLoggedIn() && !wasLoggedIn)) {
        fireHandlers(signedInHandlers);
      } else if (event === 'SIGNED_OUT' || (!isLoggedIn() && wasLoggedIn)) {
        fireHandlers(signedOutHandlers);
      }
    });
  }

  /* ── 인증 UI ────────────────────────────────────────────────────────
   * ★ 예전엔 여기서 로그인/회원가입 모달을 직접 그렸다(어떤 디자인에도
   *   자체 인증 화면이 없을 거라 가정했었다). 그런데 2026-09-20
   *   new1.3.html은 자체 로그인/회원가입 화면(view-login/view-signup,
   *   handleFigmaLogin/handleFigmaSignup)을 갖고 있었고, 우리 모달을
   *   얹었더니 "팀원이 만든 화면이 아니다"라는 피드백을 받았다 —
   *   당연하다, 진짜 다른 화면이었으니까. 그래서 자체 모달은 걷어내고
   *   대신 디자인의 handleFigmaLogin/handleFigmaSignup을 실제 Supabase
   *   호출로 덮어쓴다(아래 installLoginOverrides). 헤더 로그인 버튼도
   *   디자인 자신의 것(마이페이지 버튼과 같은 자리)을 그대로 쓴다 —
   *   더 이상 우리가 헤더에 칩을 따로 얹지 않는다.
   *   (다음에 자체 인증 화면이 아예 없는 디자인이 오면, 그때 다시
   *   최소한의 모달을 만든다 — 지금 없는 디자인을 미리 대비해 두지
   *   않는다.) */

  function friendlyAuthError(message) {
    var m = String(message || '');
    if (/invalid login credentials/i.test(m)) return '이메일 또는 비밀번호가 올바르지 않습니다.';
    if (/already registered|already exists|user already/i.test(m)) return '이미 가입된 이메일입니다. 로그인 해주세요.';
    if (/password.*(least|6|characters)/i.test(m)) return '비밀번호는 6자 이상이어야 합니다.';
    if (/rate limit/i.test(m)) return '요청이 너무 잦습니다. 잠시 후 다시 시도해주세요.';
    return m || '알 수 없는 오류가 발생했습니다.';
  }

  function handleSignOut() {
    if (!window.sb) return;
    window.sb.auth.signOut().then(function () {
      if (typeof window.showToast === 'function') window.showToast('로그아웃되었습니다.');
    });
  }

  /* ── 로그인/회원가입 — 디자인 자체 화면을 실제 Supabase로 연결 ───────
   * ★ 이 디자인은 자체 로그인/회원가입 화면(view-login/view-signup)과
   *   그걸 처리하는 handleFigmaLogin()/handleFigmaSignup()을 갖고
   *   있다 — 원본은 Supabase와 무관한 순수 로컬 목업이라(isLoggedIn
   *   플래그만 localStorage에 씀) 그대로 두면 "로그인"해도 진짜 세션이
   *   안 생겨 보관함 서버 저장·새로고침이 조용히 계속 깨진다.
   *   (예전엔 여기서 별도 모달로 이 화면 자체를 가로챘는데, 그러면
   *   사용자가 보는 화면이 팀원 디자인과 달라져 버렸다 — 그래서 화면은
   *   디자인 것 그대로 두고, 제출 핸들러만 실제 Supabase 호출로
   *   덮어쓴다. toggleSaveIdea 등과 같은 "원본 함수를 window.X = 로
   *   갈아끼우기" 패턴이다.) */
  function installLoginOverrides() {
    if (typeof window.handleFigmaLogin === 'function') {
      window.handleFigmaLogin = function (e) {
        if (e) e.preventDefault();
        if (!window.sb) return;
        var emailEl = document.getElementById('figma-login-email');
        var pwEl = document.getElementById('figma-login-pw');
        var email = emailEl ? emailEl.value.trim() : '';
        var password = pwEl ? pwEl.value : '';
        window.sb.auth.signInWithPassword({ email: email, password: password }).then(function (result) {
          var error = result && result.error;
          if (error) { libToast(friendlyAuthError(error.message)); return; }
          libToast('로그인되었습니다.');
          navigateTo('home');
        }).catch(function (err) { libToast(friendlyAuthError(err && err.message)); });
      };
    }

    if (typeof window.handleFigmaSignup === 'function') {
      window.handleFigmaSignup = function (e) {
        if (e) e.preventDefault();
        if (!window.sb) return;
        var emailEl = document.getElementById('figma-signup-email');
        var pwEl = document.getElementById('figma-signup-pw');
        var termsAge = document.getElementById('terms-age');
        var termsService = document.getElementById('terms-service');
        var email = emailEl ? emailEl.value.trim() : '';
        var password = pwEl ? pwEl.value : '';
        if (!termsAge || !termsAge.checked || !termsService || !termsService.checked) {
          libToast('필수 약관에 모두 동의해주세요.');
          return;
        }
        window.sb.auth.signUp({ email: email, password: password }).then(function (result) {
          var error = result && result.error;
          if (error) { libToast(friendlyAuthError(error.message)); return; }
          var session = result && result.data && result.data.session;
          if (!session) {
            // 이메일 확인이 켜진 프로젝트라면 세션이 바로 안 온다
            // (가이드대로 껐다면 여기 안 걸리고 바로 로그인된다).
            libToast('가입 확인 메일을 보냈습니다. 메일함을 확인해주세요.');
            navigateTo('login');
            return;
          }
          libToast('가입되었습니다!');
          navigateTo('home');
        }).catch(function (err) { libToast(friendlyAuthError(err && err.message)); });
      };
    }

    // ★ 2026-09-20: "중복확인" 버튼은 이 브라우저의 로컬 registeredEmails
    // 배열(가짜 시드값 + 예전 로컬 목업 가입 때만 쌓임)을 보고 "사용
    // 가능"을 단언했는데, handleFigmaSignup을 실제 Supabase로 바꾼
    // 뒤로는 그 배열이 실제 가입 여부와 완전히 무관해져서 이미 가입된
    // 이메일에 "사용 가능"이라고 잘못 알려주는 사고가 났다(실제 있었던
    // 버그). 게다가 Supabase는 이메일 열거(enumeration) 공격을 막으려고
    // "이 이메일 가입됐는지" 미리 물어볼 공개 API를 일부러 안 줘서,
    // 이 버튼은 애초에 정확한 답을 줄 수 없었다(형식 확인은 이미
    // `<input type="email" required>`가 한다) — 그래서 버튼 자체를
    // 디자인 마크업에서 지웠다. 여기서 더 손댈 것 없음.
  }

  /** 이 디자인의 마이페이지엔 "로그아웃하기" 링크가 handleLogout()을
   * 직접 부른다. 원본은 로컬 목업 isLoggedIn 플래그만 끄고 실제
   * Supabase 세션은 그대로 둔다 — 그러면 새로고침 시 세션이 남아 있어
   * 다시 로그인 상태로 돌아오는 버그가 난다. 있으면 실제 signOut으로
   * 갈아끼운다(없으면 이 디자인엔 로그아웃 진입점이 아예 없다는 뜻). */
  function installLogoutOverride() {
    if (typeof window.handleLogout === 'function') {
      window.handleLogout = handleSignOut;
    }
  }

  /** 우리가 진짜로 로그인/로그아웃시켰다는 걸 디자인 자신의 GNB 버튼에도
   * 반영한다 — 안 그러면 우리 헤더 칩(#eureka-header-chip)은 "로그인됨"을
   * 보여주는데 디자인 고유의 GNB "로그인" 버튼은 그대로 남아 화면에
   * 서로 다른 두 상태가 동시에 뜬다. isLoggedIn은 디자인 script
   * 최상위의 `let`이라 이 IIFE 안에서 맨이름으로 대입하면 이 파일
   * 자신의 동명 지역 함수(위의 isLoggedIn())를 덮어써 버린다 — 그래서
   * 반드시 간접 eval(페이지 전역 스코프에서 실행됨)로 건드린다. */
  function syncDesignAuthFlag(loggedIn) {
    try {
      window.eval(
        'isLoggedIn = ' + (loggedIn ? 'true' : 'false') + ';' +
        'if (typeof updateAuthUI === "function") updateAuthUI();'
      );
    } catch (e) { /* 디자인에 isLoggedIn/updateAuthUI가 없으면 조용히 넘어간다 */ }
  }

  /* =====================================================================
   * 보관함 — 로그인 상태에서만 서버에 저장한다. 로그아웃 상태는 지금까지와
   * 완전히 동일하게 localStorage만 쓴다(데모가 로그인 없이도 그대로
   * 돌아가야 한다).
   *
   * ★ 전략: 디자인의 원본 함수(toggleSaveKeyword 등)를 다시 구현하지
   *   않는다. 배열 변경 + 화면 재렌더 로직은 원본이 이미 정확히 하고
   *   있으므로, 로그인 중에는 **원본을 그대로 호출하되 localStorage.setItem
   *   만 일시적으로 무력화**하고, 그 결과(배열이 어떻게 바뀌었는지)를 보고
   *   서버에 동기화한다. 이러면 원본 함수의 토스트 문구·재렌더 호출까지
   *   전부 공짜로 따라온다.
   * ===================================================================== */

  function withLocalStorageSuppressed(fn) {
    var original;
    try {
      original = window.localStorage.setItem.bind(window.localStorage);
      window.localStorage.setItem = function () {};
    } catch (e) {
      // localStorage 자체를 못 쓰는 환경(사파일 프라이빗 모드 등) — 그냥 원래 함수를 부른다.
      return fn();
    }
    try {
      return fn();
    } finally {
      try { window.localStorage.setItem = original; } catch (e) { /* 무시 */ }
    }
  }

  function libToast(msg) {
    if (typeof window.showToast === 'function') window.showToast(msg);
  }

  /** 서버에서 받은 보관함 행을 화면이 기대하는 camelCase 모양으로 편다.
   * idea_key/keyword_id를 필드로 남겨야 나중에 삭제·수정 때 쓸 수 있다. */
  function rowToKeywordItem(row) {
    var item = {};
    var payload = row.payload || {};
    for (var k in payload) item[k] = payload[k];
    item.id = row.keyword_id;
    item.name = row.name;
    item.category = row.category;
    return item;
  }

  var EUREKA_PERIOD_LABEL = { day: '하루', week: '일주일', month: '한 달 이상' };

  function rowToIdeaItem(row) {
    var item = {};
    var payload = row.payload || {};
    for (var k in payload) item[k] = payload[k];
    item.idea_key = row.idea_key;
    item.periodKey = row.period;
    // payload.period(한글 라벨, getRecommendedAiList가 기대하는 형태)가
    // 이미 있으면 그대로 두고, 없으면(이관된 옛 데이터 등) DB의 영문
    // period 키로부터 복원한다 — row.period로 그냥 덮어쓰면 한글 라벨이
    // 영문 키로 바뀌어 추천 AI 목록이 항상 '한 달 이상'으로 잘못 떨어진다.
    if (!item.period) item.period = EUREKA_PERIOD_LABEL[row.period] || '하루';
    return item;
  }

  function rerenderAfterLibraryChange() {
    if (typeof window.updateSavedCounts === 'function') window.updateSavedCounts();
    if (typeof window.renderBestKeywordsGrid === 'function') { try { window.renderBestKeywordsGrid(); } catch (e) {} }
    if (typeof window.renderWeeklySlider === 'function') { try { window.renderWeeklySlider(); } catch (e) {} }
    var savedView = document.getElementById('view-saved');
    if (savedView && savedView.classList.contains('active') && typeof window.renderSavedScreen === 'function') {
      try { window.renderSavedScreen(); } catch (e) {}
    }
  }

  /** 로그인 상태에서 보관함 전체를 서버 기준으로 다시 채운다. 서버가
   * 진실이므로 배열을 통째로 교체한다 — localStorage와 섞지 않는다. */
  function loadLibrary() {
    return Promise.all([
      window.EUREKA.auth.apiFetchJson('/api/library/keywords'),
      window.EUREKA.auth.apiFetchJson('/api/library/ideas')
    ]).then(function (results) {
      var kwRes = results[0], idRes = results[1];
      if (kwRes.ok && kwRes.body && Array.isArray(kwRes.body.items)) {
        savedKeywords = kwRes.body.items.map(rowToKeywordItem);
      }
      if (idRes.ok && idRes.body && Array.isArray(idRes.body.items)) {
        savedIdeas = idRes.body.items.map(rowToIdeaItem);
      }
      rerenderAfterLibraryChange();
    }).catch(function (err) {
      console.warn(LOG, '보관함 불러오기 실패:', err && err.message);
    });
  }

  /** 최초 로그인 이관. 3중 중복 방지: ① 계정별 localStorage 마커
   * ② 서버 unique 제약(merge-duplicates) ③ 서버가 반환한 개수가 0이면
   * 토스트를 안 띄운다. 원본 localStorage는 지우지 않는다 — 로그아웃
   * 상태 데이터를 날리면 되돌릴 수 없다. */
  function migrationMarkerKey(userId) {
    return 'eureka_migrated_v1_' + userId;
  }

  function migrateLocalLibraryIfNeeded(user) {
    if (!user) return Promise.resolve();
    var marker = migrationMarkerKey(user.id);
    var already = null;
    try { already = localStorage.getItem(marker); } catch (e) { /* 접근 불가 — 매번 재시도하게 둔다 */ }
    if (already) return Promise.resolve();

    var localKw = [], localIdeas = [];
    try { localKw = JSON.parse(localStorage.getItem('eureka_saved_keywords') || '[]'); } catch (e) {}
    try { localIdeas = JSON.parse(localStorage.getItem('eureka_saved_ideas') || '[]'); } catch (e) {}

    if (!localKw.length && !localIdeas.length) {
      try { localStorage.setItem(marker, 'empty'); } catch (e) {}
      return Promise.resolve();
    }

    return window.EUREKA.auth.apiFetchJson('/api/library/migrate', {
      method: 'POST', body: { keywords: localKw, ideas: localIdeas }
    }).then(function (r) {
      if (!r.ok) return; // 실패하면 마커를 안 남긴다 — 다음 로그인 때 다시 시도된다.
      try { localStorage.setItem(marker, new Date().toISOString()); } catch (e) {}
      var n = (r.body && ((r.body.imported_keywords || 0) + (r.body.imported_ideas || 0))) || 0;
      if (n > 0) libToast('보관함 ' + n + '건을 계정으로 옮겼어요.');
    }).catch(function () { /* 조용히 넘어간다 — 마커가 없으니 다음 로그인 때 재시도 */ });
  }

  /* ── 원본 함수 캡처 + 덮어쓰기 ────────────────────────────────────── */

  function installLibraryOverrides() {
    var originalToggleSaveKeyword = window.toggleSaveKeyword;
    var originalToggleSaveIdea = window.toggleSaveIdea;
    var originalRemoveSavedKeyword = window.removeSavedKeyword;
    var originalRemoveSavedIdea = window.removeSavedIdea;

    if (typeof originalToggleSaveKeyword === 'function') {
      window.toggleSaveKeyword = function (e, id) {
        if (!isLoggedIn()) return originalToggleSaveKeyword(e, id);
        var item = (typeof window.findKeywordById === 'function') ? window.findKeywordById(id) : null;
        var wasSaved = savedKeywords.some(function (k) { return k.id === id; });
        withLocalStorageSuppressed(function () { originalToggleSaveKeyword(e, id); });
        if (wasSaved) {
          window.EUREKA.auth.apiFetchJson('/api/library/keywords/' + encodeURIComponent(id), { method: 'DELETE' })
            .then(function (r) { if (!r.ok) libToast('보관함 동기화에 실패했어요. 잠시 후 다시 시도해주세요.'); });
        } else if (item) {
          window.EUREKA.auth.apiFetchJson('/api/library/keywords', {
            method: 'POST',
            body: { keyword_id: id, name: item.name, category: item.category || '', payload: item }
          }).then(function (r) {
            if (!r.ok) {
              withLocalStorageSuppressed(function () { originalToggleSaveKeyword(null, id); });
              libToast('보관함 동기화에 실패했어요. 잠시 후 다시 시도해주세요.');
            }
          });
        }
      };
    }

    if (typeof originalToggleSaveIdea === 'function') {
      window.toggleSaveIdea = function (btn, index) {
        var idea = generatedIdeas[index];
        var existing = idea ? savedIdeas.filter(function (i) { return i.name === idea.name; })[0] : null;
        var wasSaved = !!existing;
        var ideaKeyToDelete = existing ? existing.idea_key : null;

        if (!isLoggedIn()) {
          originalToggleSaveIdea(btn, index);
          // 로그아웃 상태에서도 기간을 남겨 둔다 — 이 디자인의 저장 객체엔
          // period/periodKey가 없어(toggleSaveIdea가 ...idea만 펼침),
          // 나중에 로그인해서 이관될 때도 기간이 맞게 표시되도록 여기서 채운다.
          if (!wasSaved) {
            var localNewEntry = savedIdeas[savedIdeas.length - 1];
            if (localNewEntry && !localNewEntry.periodKey) {
              localNewEntry.period = configSettings.period;
              localNewEntry.periodKey = EUREKA_PERIOD_KEY[configSettings.period] || 'day';
            }
          }
          return;
        }

        withLocalStorageSuppressed(function () { originalToggleSaveIdea(btn, index); });

        if (wasSaved) {
          if (!ideaKeyToDelete) return; // 서버 동기 전 로컬에만 있던 항목 — 삭제할 서버 행이 없다
          window.EUREKA.auth.apiFetchJson('/api/library/ideas/' + encodeURIComponent(ideaKeyToDelete), { method: 'DELETE' })
            .then(function (r) { if (!r.ok) libToast('보관함 동기화에 실패했어요. 잠시 후 다시 시도해주세요.'); });
        } else {
          var newEntry = savedIdeas[savedIdeas.length - 1];
          if (!newEntry) return;
          if (!newEntry.periodKey) {
            newEntry.period = configSettings.period;
            newEntry.periodKey = EUREKA_PERIOD_KEY[configSettings.period] || 'day';
          }
          window.EUREKA.auth.apiFetchJson('/api/library/ideas', {
            method: 'POST',
            body: {
              keyword_id: (typeof selectedKeyword !== 'undefined' && selectedKeyword) ? selectedKeyword.id : '',
              keyword_name: newEntry.keyword || '',
              name: newEntry.name,
              platform: (typeof configSettings !== 'undefined' && configSettings.platform) || '',
              type: (typeof configSettings !== 'undefined' && configSettings.type) || '',
              period: newEntry.periodKey || 'day',
              payload: newEntry
            }
          }).then(function (r) {
            if (r.ok && r.body && r.body.idea_key) {
              newEntry.idea_key = r.body.idea_key;
            } else if (!r.ok) {
              withLocalStorageSuppressed(function () { originalToggleSaveIdea(btn, index); });
              libToast('보관함 동기화에 실패했어요. 잠시 후 다시 시도해주세요.');
            }
          });
        }
      };
    }

    if (typeof originalRemoveSavedKeyword === 'function') {
      window.removeSavedKeyword = function (i) {
        if (!isLoggedIn()) return originalRemoveSavedKeyword(i);
        var item = savedKeywords[i];
        withLocalStorageSuppressed(function () { originalRemoveSavedKeyword(i); });
        if (item) {
          window.EUREKA.auth.apiFetchJson('/api/library/keywords/' + encodeURIComponent(item.id), { method: 'DELETE' })
            .then(function (r) { if (!r.ok) libToast('삭제 동기화에 실패했어요. 새로고침 후 다시 시도해주세요.'); });
        }
      };
    }

    if (typeof originalRemoveSavedIdea === 'function') {
      window.removeSavedIdea = function (i) {
        if (!isLoggedIn()) return originalRemoveSavedIdea(i);
        var item = savedIdeas[i];
        withLocalStorageSuppressed(function () { originalRemoveSavedIdea(i); });
        if (item && item.idea_key) {
          window.EUREKA.auth.apiFetchJson('/api/library/ideas/' + encodeURIComponent(item.idea_key), { method: 'DELETE' })
            .then(function (r) { if (!r.ok) libToast('삭제 동기화에 실패했어요. 새로고침 후 다시 시도해주세요.'); });
        }
      };
    }

  }

  /* =====================================================================
   * 새로고침 — 로그인 후 키워드당 정해진 횟수만큼 아이디어 3개를 다시
   * 뽑는다. 실제 판정은 서버(app/api/idea_routes.py, DB 원자적 함수)가
   * 전부 한다 — 여기는 버튼 상태를 그 결과에 맞춰 그리기만 한다.
   * ===================================================================== */

  var lastRefreshInfo = null;  // 마지막 생성 응답의 {applied,reason,used,limit,variant}
  var isGeneratingFlag = false;  // 이 디자인엔 전역 isGenerating 이 없어 모듈 내부에서만 관리한다.

  function errorCodeOf(err) {
    return err && err.detail && err.detail.detail && err.detail.detail.error_code;
  }

  function showResultScreen(loading) {
    var loadingEl = document.getElementById(SELECTORS.resultLoadingScreen);
    var mainEl = document.getElementById(SELECTORS.resultScreen);
    if (loadingEl) loadingEl.style.display = loading ? 'block' : 'none';
    if (mainEl) mainEl.style.display = loading ? 'none' : 'block';
  }

  /** 디자인의 executeIdeaGeneration()을 완전히 대체한다(부분 재사용이 안
   * 되는 이유: 원본은 인자를 안 받고 요청 바디도 고정이며, 서버 대신
   * 로컬 목업 데이터를 그리는데 refresh 필드와 Authorization 헤더를
   * 끼워 넣을 자리가 없다). 일반 생성 버튼의 onclick="executeIdeaGeneration()"
   * 은 opts가 없어도 그대로 동작한다(refresh 기본값 false).
   * 서버 호출이 실패하면(오프라인·서버 다운) 디자인 자신의 로컬 목업
   * 생성기 finishIdeaGeneration() 을 그대로 불러 폴백으로 쓴다 — 그
   * 쪽이 이미 완결된 오프라인 체험을 갖고 있어 다시 만들 필요가 없다. */
  window.executeIdeaGeneration = function (opts) {
    opts = opts || {};
    var isRefresh = !!opts.refresh;

    navigateTo('result');
    showResultScreen(true);
    var loadingTextEl = document.getElementById(SELECTORS.loadingStepText);
    if (loadingTextEl) {
      loadingTextEl.innerText = isRefresh
        ? '새로운 관점의 아이디어 3가지를 구상하고 있습니다...'
        : ('#' + selectedKeyword.name + '의 검색어 데이터 및 SNS 반응 분석 중...');
    }

    var period = configSettings.period;
    isGeneratingFlag = true;
    updateRefreshButton();  // 이미 화면에 있던 버튼이 있다면 "만드는 중"으로 즉시 반영

    return apiFetch('/api/trends/' + selectedKeyword.id + '/ideas', {
      method: 'POST',
      body: { platform: configSettings.platform, type: configSettings.type, period: period, count: 3, refresh: isRefresh }
    }).then(function (res) {
      if (!res.ok) {
        return res.text().then(function (text) {
          var detail = null;
          try { detail = JSON.parse(text); } catch (e) { /* JSON이 아닐 수도 있다 */ }
          var err = new Error('아이디어 생성 요청 실패: ' + res.status);
          err.status = res.status;
          err.detail = detail;
          throw err;
        });
      }
      return res.json();
    }).then(function (data) {
      lastRefreshInfo = data.refresh || null;
      generatedIdeas = (data.ideas || []).map(mapBackendIdea);
      activeIdeaIndex = 0;
      showResultScreen(false);
      var kwEl = document.getElementById(SELECTORS.resultKeywordName);
      if (kwEl) kwEl.innerText = '#' + selectedKeyword.name;
      renderIdeasTabs();
      if (typeof window.showIdeaDetail === 'function') window.showIdeaDetail(0);
    }).catch(function (err) {
      console.warn(LOG, '[아이디어 생성] API 호출 실패:', err && err.message);
      if (isRefresh) {
        // 새로고침 실패는 화면을 폴백 데이터로 덮어쓰지 않는다 — 지금
        // 보이는(직전에 성공한) 아이디어를 그대로 둔다.
        var code = errorCodeOf(err);
        var msg = '새로고침에 실패했어요. 잠시 후 다시 시도해주세요.';
        if (code === 'refresh_requires_login') msg = '로그인 후 새로고침할 수 있어요.';
        else if (code === 'quota_spent') msg = '이 키워드는 새로고침을 모두 사용했어요.';
        else if (code === 'refresh_unavailable') msg = '지금은 새로고침을 쓸 수 없어요.';
        showResultScreen(false);
        libToast(msg);
        return;
      }
      lastRefreshInfo = null;
      if (typeof window.finishIdeaGeneration === 'function') {
        window.finishIdeaGeneration();
      } else {
        showResultScreen(false);
        libToast('아이디어 생성에 실패했어요. 잠시 후 다시 시도해주세요.');
      }
    }).then(function () {
      isGeneratingFlag = false;
      updateRefreshButton();
    }).catch(function (e) {
      isGeneratingFlag = false;
      updateRefreshButton();
      console.error(LOG, '아이디어 생성 처리 중 예기치 못한 오류:', e);
    });
  };

  function refreshButtonIconSvg() {
    return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
      'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">' +
      '<polyline points="1 4 1 10 7 10"></polyline>' +
      '<path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path></svg>';
  }

  /** #ideas-tabs-container 는 renderIdeasTabs()가 매번 innerHTML로 갈아
   * 치우므로, 안에 넣지 않고 그 바깥 padded 박스(.figma-result-tabs-box,
   * 카드 3개 + "새로받기" 영역을 함께 감싸는 회색 도형)에 절대위치로
   * 얹는다. #ideas-tabs-container 자체에 얹으면 grid 여백이 없어 버튼이
   * 세 번째 카드 위에 그대로 겹쳐 보였다(실제로 겹쳐서 카드를 가림).
   * 바깥 박스는 padding이 있어 그 여백 안에 뜬다. 바깥 박스를 못 찾으면
   * (구조가 또 바뀐 경우) 안전하게 컨테이너 자신으로 되돌아간다. */
  function mountRefreshButton() {
    var tabsBox = document.getElementById(SELECTORS.ideaTabsBox);
    if (!tabsBox) return;
    var box = tabsBox.closest('.figma-result-tabs-box') || tabsBox.parentElement || tabsBox;
    if (getComputedStyle(box).position === 'static') box.style.position = 'relative';

    var btn = document.getElementById('eureka-refresh-btn');
    if (!btn) {
      btn = document.createElement('button');
      btn.id = 'eureka-refresh-btn';
      btn.type = 'button';
      btn.className = 'figma-btn-edit-feature';
      btn.style.cssText = 'position:absolute; top:14px; right:18px; z-index:3;';
      btn.innerHTML = refreshButtonIconSvg() + '<span></span>';
      btn.addEventListener('click', onRefreshButtonClick);
      box.appendChild(btn);
    }
    updateRefreshButton();
  }

  function onRefreshButtonClick() {
    if (isGeneratingFlag) return;
    if (!isLoggedIn()) { navigateTo('login'); return; }
    if (lastRefreshInfo && lastRefreshInfo.used >= lastRefreshInfo.limit) return;
    window.executeIdeaGeneration({ refresh: true });
  }

  function updateRefreshButton() {
    var btn = document.getElementById('eureka-refresh-btn');
    if (!btn) return;
    var label = btn.querySelector('span');

    if (!authEnabled) { btn.style.display = 'none'; return; }
    btn.style.display = '';
    btn.title = '';

    if (isGeneratingFlag) {
      btn.disabled = true;
      btn.style.opacity = '0.6'; btn.style.cursor = 'default';
      if (label) label.textContent = '새 아이디어를 만드는 중...';
      return;
    }
    if (!isLoggedIn()) {
      btn.disabled = false;
      btn.style.opacity = ''; btn.style.cursor = 'pointer';
      if (label) label.textContent = '로그인하고 새로고침';
      return;
    }
    var used = lastRefreshInfo ? lastRefreshInfo.used : 0;
    var limit = lastRefreshInfo ? lastRefreshInfo.limit : settings_REFRESH_QUOTA_DEFAULT;
    if (used >= limit) {
      btn.disabled = true;
      btn.style.opacity = '0.5'; btn.style.cursor = 'not-allowed';
      btn.title = '키워드당 ' + limit + '회만 가능해요';
      if (label) label.textContent = '새로고침을 모두 사용했어요';
    } else {
      btn.disabled = false;
      btn.style.opacity = ''; btn.style.cursor = 'pointer';
      if (label) label.textContent = '아이디어 새로고침 (' + (limit - used) + '회 남음)';
    }
  }

  // 서버가 아직 응답을 안 준 시점(막 로그인 직후 등)의 기본 표시값.
  // 실제 한도는 항상 서버(GET /api/config가 아니라 매 생성 응답의
  // refresh 블록)가 최종 권위를 갖는다 — 이건 그 전까지의 자리표시일 뿐.
  var settings_REFRESH_QUOTA_DEFAULT = 1;

  /* ── 바깥에 내보내는 것 ─────────────────────────────────────────────
   * window.EUREKA 하나만 추가한다 — 디자인 이름과 부딪힐 일이 없다. */

  window.EUREKA = {
    version: VERSION,
    served: isServed,
    debug: isDebug,
    selectors: SELECTORS,
    contract: CONTRACT,
    /** 탭이 다시 그려질 때마다 부를 함수를 등록한다. 등록 즉시 한 번 부른다. */
    onTabsRender: function (fn) {
      if (typeof fn !== 'function') return;
      afterTabsRender.push(fn);
      try { fn(); } catch (e) { console.warn(LOG, '훅 최초 실행 실패:', e && e.message); }
    },
    auth: {
      isEnabled: function () { return authEnabled; },
      isLoggedIn: isLoggedIn,
      currentUser: currentUser,
      signOut: handleSignOut,
      apiFetch: apiFetch,
      apiFetchJson: apiFetchJson,
      /** 로그인 상태가 확인될 때마다(부팅 시 기존 세션 포함) 부른다. */
      onSignedIn: function (fn) {
        if (typeof fn !== 'function') return;
        signedInHandlers.push(fn);
        if (isLoggedIn()) { try { fn(currentUser()); } catch (e) { /* 무시 */ } }
      },
      onSignedOut: function (fn) {
        if (typeof fn === 'function') signedOutHandlers.push(fn);
      }
    },
    /** 화면에 이미 떠 있는 요소를 건드리지 않고 상태만 보고 싶을 때. */
    describe: function () {
      return {
        version: VERSION,
        served: isServed,
        contractOk: checkContract(),
        tabsHooked: !!(window.renderIdeasTabs && window.renderIdeasTabs.__eurekaWrapped),
        hooks: afterTabsRender.length,
        authEnabled: authEnabled,
        loggedIn: isLoggedIn(),
        user: currentUser()
      };
    }
  };

  /* ── 부팅 ───────────────────────────────────────────────────────────
   * defer 스크립트는 문서 파싱이 끝난 뒤, DOMContentLoaded 앞에 실행된다.
   * 디자인의 DOMContentLoaded 핸들러가 먼저 등록돼 있으므로 디자인 초기화가
   * 먼저 돌고 우리가 나중에 돈다 — 우리가 원하는 순서다. */

  function boot() {
    try {
      if (!isServed) {
        console.info(LOG, 'file:// 로 열렸습니다 — 연동을 건너뜁니다(디자인 폴백으로 동작).');
        return;
      }
      checkContract();
      installTabsHook();

      fetch('/api/config').then(function (r) {
        if (!r.ok) throw new Error('status ' + r.status);
        return r.json();
      }).then(function (cfg) {
        authEnabled = initSupabase(cfg);
        if (!authEnabled) {
          if (isDebug) console.info(LOG, '로그인 기능 꺼짐(auth_enabled=false 또는 SDK 미로드)');
          return;
        }
        installLoginOverrides();
        installLogoutOverride();
        installLibraryOverrides();
        window.EUREKA.onTabsRender(mountRefreshButton);
        bootSession();
        // 로그인이 확인될 때마다(부팅 시 기존 세션 포함) 이관 후 서버 기준으로 로드.
        window.EUREKA.auth.onSignedIn(function (user) {
          migrateLocalLibraryIfNeeded(user).then(function () { return loadLibrary(); });
          updateRefreshButton();
          syncDesignAuthFlag(true);
        });
        // 로그아웃하면 화면은 빈 보관함으로 — localStorage는 건드리지 않는다.
        window.EUREKA.auth.onSignedOut(function () {
          savedKeywords = [];
          savedIdeas = [];
          lastRefreshInfo = null;
          rerenderAfterLibraryChange();
          updateRefreshButton();
          syncDesignAuthFlag(false);
        });
        if (isDebug) console.info(LOG, 'boot 완료', window.EUREKA.describe());
      }).catch(function (err) {
        // /api/config 자체가 없거나 네트워크 문제 — 로그인 기능만 없이 계속한다.
        console.warn(LOG, '/api/config 조회 실패 — 로그인 기능 없이 계속합니다:', err && err.message);
      });
    } catch (e) {
      // 여기서 터져도 앱은 계속 돌아야 한다. 연동만 없는 상태가 된다.
      console.error(LOG, 'boot 실패 — 연동 없이 계속합니다:', e);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
