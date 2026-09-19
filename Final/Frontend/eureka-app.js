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

  var VERSION = '0.3.0-library';    // 5단계: 로그인 UI + 보관함 서버 저장 + 이관.
  var LOG = '[eureka]';

  /* ── 디자인 HTML 과의 계약 ──────────────────────────────────────────
   * 새 디자인이 왔을 때 여기 적힌 것이 하나라도 없으면 연동이 조용히
   * 안 붙는다. 그래서 부팅할 때 직접 확인하고 콘솔에 경고를 찍는다.
   * "조용한 실패"를 "시끄러운 실패"로 바꾸는 게 목적이다. */

  var CONTRACT = {
    // 맨이름으로 읽고 쓰는 전역 (디자인 script 의 최상위 let/const)
    globals: [
      'savedKeywords', 'savedIdeas', 'configSettings',
      'selectedKeyword', 'generatedIdeas', 'isGenerating', 'PERIOD_KEY'
    ],
    // 나중 단계에서 window.<이름> 으로 덮어쓸 함수
    overrides: [
      'toggleSaveKeyword', 'toggleSaveIdea', 'removeSavedKeyword',
      'removeSavedIdea', 'syncSavedIdea', 'updateSavedCounts',
      'executeIdeaGeneration'
    ],
    // 감싸거나 그대로 호출할 함수 (대체하지 않는다 — 디자인 소유)
    uses: [
      'renderIdeasTabs', 'renderSavedScreen', 'showIdeaDetail',
      'showToast', 'navigateTo', 'esc', 'aiToolsFor',
      'findKeywordById', 'renderBestKeywordsGrid', 'renderWeeklySlider',
      'renderDetailScreen', 'toggleSavedIdeaDetails'
    ]
  };

  var SELECTORS = {
    ideaTabsBox: 'ideas-tabs-container',
    resultScreen: 'result-main-screen',
    ideaDetailBox: 'active-idea-card-container',
    toast: 'toast-popup'
  };

  // 헤더 로그인 칩을 꽂을 자리 후보. 위에서부터 시도하고, 전부 없으면
  // 화면 우측 상단에 고정 위치로 띄운다 — 새 디자인이 header 구조를
  // 바꿔도 아예 안 뜨는 최악은 피한다.
  var HEADER_CHIP_TARGETS = ['.fixed-gnb-inner', 'header > div', 'header'];

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
      renderHeaderChip();
      if (currentSession) fireHandlers(signedInHandlers);
    });
    window.sb.auth.onAuthStateChange(function (event, session) {
      var wasLoggedIn = isLoggedIn();
      currentSession = session || null;
      renderHeaderChip();
      if (event === 'SIGNED_IN' || (isLoggedIn() && !wasLoggedIn)) {
        fireHandlers(signedInHandlers);
      } else if (event === 'SIGNED_OUT' || (!isLoggedIn() && wasLoggedIn)) {
        fireHandlers(signedOutHandlers);
      }
    });
  }

  /* ── 인증 UI — 어떤 디자인에도 없으므로 JS가 직접 주입한다 ────────── */

  var AUTH_STYLE = '' +
    '#eureka-auth-root{all:initial;}' +
    '#eureka-auth-root *{box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif;}' +
    '#eureka-auth-root .eureka-overlay{position:fixed;inset:0;background:rgba(15,15,20,.5);' +
      'display:flex;align-items:center;justify-content:center;z-index:100000;}' +
    '#eureka-auth-root .eureka-overlay[hidden]{display:none;}' +
    '#eureka-auth-root .eureka-modal{background:#fff;border-radius:20px;padding:32px;width:340px;' +
      'max-width:calc(100vw - 32px);box-shadow:0 20px 60px rgba(0,0,0,.25);position:relative;}' +
    '#eureka-auth-root .eureka-modal-close{position:absolute;top:14px;right:16px;border:none;' +
      'background:none;font-size:20px;line-height:1;cursor:pointer;color:#94A3B8;padding:4px;}' +
    '#eureka-auth-root .eureka-modal-close:hover{color:#334155;}' +
    '#eureka-auth-root .eureka-modal-tabs{display:flex;gap:4px;margin-bottom:20px;background:#F4F4F6;' +
      'border-radius:10px;padding:4px;}' +
    '#eureka-auth-root .eureka-tab{flex:1;border:none;background:none;padding:9px 0;border-radius:8px;' +
      'font-size:14px;font-weight:700;color:#71717A;cursor:pointer;}' +
    '#eureka-auth-root .eureka-tab.active{background:#fff;color:#6B42FF;box-shadow:0 1px 3px rgba(0,0,0,.08);}' +
    '#eureka-auth-root .eureka-auth-form{display:flex;flex-direction:column;gap:12px;}' +
    '#eureka-auth-root .eureka-field-label{font-size:13px;font-weight:600;color:#3F3F46;display:block;margin-bottom:6px;}' +
    '#eureka-auth-root .eureka-auth-form input{width:100%;padding:11px 13px;border:1.5px solid #E4E4E7;' +
      'border-radius:10px;font-size:14px;outline:none;}' +
    '#eureka-auth-root .eureka-auth-form input:focus{border-color:#6B42FF;}' +
    '#eureka-auth-root .eureka-auth-error{color:#DC2626;font-size:13px;margin:0;min-height:0;}' +
    '#eureka-auth-root .eureka-auth-error:empty{display:none;}' +
    '#eureka-auth-root .eureka-auth-hint{color:#16A34A;font-size:13px;margin:0;}' +
    '#eureka-auth-root .eureka-auth-hint:empty{display:none;}' +
    '#eureka-auth-root .eureka-auth-submit{margin-top:4px;background:#6B42FF;color:#fff;border:none;' +
      'border-radius:10px;padding:12px 0;font-size:15px;font-weight:700;cursor:pointer;}' +
    '#eureka-auth-root .eureka-auth-submit:disabled{opacity:.6;cursor:default;}' +
    '#eureka-auth-root .eureka-auth-submit:not(:disabled):hover{background:#5B34E0;}' +
    '.eureka-header-chip{display:flex;align-items:center;gap:10px;margin-left:auto;}' +
    '.eureka-login-btn{background:#6B42FF;color:#fff;border:none;border-radius:999px;padding:8px 18px;' +
      'font-size:13px;font-weight:700;cursor:pointer;font-family:inherit;white-space:nowrap;}' +
    '.eureka-login-btn:hover{background:#5B34E0;}' +
    '.eureka-user-chip{display:flex;align-items:center;gap:8px;}' +
    '.eureka-user-email{font-size:13px;color:#52525B;max-width:150px;overflow:hidden;' +
      'text-overflow:ellipsis;white-space:nowrap;}' +
    '.eureka-logout-btn{background:none;border:1.5px solid #E4E4E7;color:#52525B;border-radius:999px;' +
      'padding:7px 14px;font-size:13px;font-weight:600;cursor:pointer;font-family:inherit;white-space:nowrap;}' +
    '.eureka-logout-btn:hover{border-color:#CBD5E1;color:#27272A;}' +
    '.eureka-header-chip-fallback{position:fixed;top:16px;right:16px;z-index:9999;}';

  function injectStyleOnce() {
    if (document.getElementById('eureka-auth-style')) return;
    var style = document.createElement('style');
    style.id = 'eureka-auth-style';
    style.textContent = AUTH_STYLE;
    document.head.appendChild(style);
  }

  function buildAuthRoot() {
    if (document.getElementById('eureka-auth-root')) return;
    var root = document.createElement('div');
    root.id = 'eureka-auth-root';
    root.innerHTML =
      '<div class="eureka-overlay" id="eureka-auth-overlay" hidden>' +
        '<div class="eureka-modal" role="dialog" aria-modal="true" aria-label="로그인">' +
          '<button type="button" class="eureka-modal-close" id="eureka-auth-close" aria-label="닫기">&times;</button>' +
          '<div class="eureka-modal-tabs">' +
            '<button type="button" class="eureka-tab active" data-mode="signin">로그인</button>' +
            '<button type="button" class="eureka-tab" data-mode="signup">회원가입</button>' +
          '</div>' +
          '<form class="eureka-auth-form" id="eureka-auth-form">' +
            '<div>' +
              '<span class="eureka-field-label">이메일</span>' +
              '<input type="email" id="eureka-auth-email" autocomplete="email" required />' +
            '</div>' +
            '<div>' +
              '<span class="eureka-field-label">비밀번호</span>' +
              '<input type="password" id="eureka-auth-password" autocomplete="current-password" minlength="6" required />' +
            '</div>' +
            '<p class="eureka-auth-error" id="eureka-auth-error"></p>' +
            '<p class="eureka-auth-hint" id="eureka-auth-hint"></p>' +
            '<button type="submit" class="eureka-auth-submit" id="eureka-auth-submit">로그인</button>' +
          '</form>' +
        '</div>' +
      '</div>';
    document.body.appendChild(root);

    var overlay = document.getElementById('eureka-auth-overlay');
    var form = document.getElementById('eureka-auth-form');
    var tabs = root.querySelectorAll('.eureka-tab');

    document.getElementById('eureka-auth-close').addEventListener('click', closeAuthModal);
    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) closeAuthModal();
    });
    tabs.forEach(function (tab) {
      tab.addEventListener('click', function () {
        tabs.forEach(function (t) { t.classList.remove('active'); });
        tab.classList.add('active');
        setAuthMode(tab.getAttribute('data-mode'));
      });
    });
    form.addEventListener('submit', handleAuthSubmit);
  }

  var authMode = 'signin';

  function setAuthMode(mode) {
    authMode = mode;
    restoreSubmitLabel(mode);
    var pwInput = document.getElementById('eureka-auth-password');
    if (pwInput) pwInput.setAttribute('autocomplete', mode === 'signup' ? 'new-password' : 'current-password');
    setAuthError('');
    setAuthHint('');
  }

  /** 제출 버튼의 라벨/활성화 상태만 되돌린다. setAuthMode()와 갈라둔 이유:
   * 로그인 실패 뒤 "처리 중..." 라벨을 되돌릴 때 setAuthMode()를 쓰면
   * 그 함수가 끝에서 setAuthError('')/setAuthHint('')를 호출해 방금
   * 띄운 에러 메시지가 뜨자마자 지워지는 버그가 있었다(테스트로 발견). */
  function restoreSubmitLabel(mode) {
    var submit = document.getElementById('eureka-auth-submit');
    if (submit) submit.textContent = mode === 'signup' ? '회원가입' : '로그인';
  }

  function setAuthError(msg) {
    var el = document.getElementById('eureka-auth-error');
    if (el) el.textContent = msg || '';
  }

  function setAuthHint(msg) {
    var el = document.getElementById('eureka-auth-hint');
    if (el) el.textContent = msg || '';
  }

  function openAuthModal(mode) {
    if (!authEnabled) return;
    buildAuthRoot();
    var overlay = document.getElementById('eureka-auth-overlay');
    if (!overlay) return;
    var tabs = document.querySelectorAll('#eureka-auth-root .eureka-tab');
    tabs.forEach(function (t) {
      t.classList.toggle('active', t.getAttribute('data-mode') === (mode || 'signin'));
    });
    setAuthMode(mode || 'signin');
    overlay.hidden = false;
    var emailInput = document.getElementById('eureka-auth-email');
    if (emailInput) setTimeout(function () { emailInput.focus(); }, 0);
  }

  function closeAuthModal() {
    var overlay = document.getElementById('eureka-auth-overlay');
    if (overlay) overlay.hidden = true;
    setAuthError('');
    setAuthHint('');
  }

  function friendlyAuthError(message) {
    var m = String(message || '');
    if (/invalid login credentials/i.test(m)) return '이메일 또는 비밀번호가 올바르지 않습니다.';
    if (/already registered|already exists|user already/i.test(m)) return '이미 가입된 이메일입니다. 로그인 해주세요.';
    if (/password.*(least|6|characters)/i.test(m)) return '비밀번호는 6자 이상이어야 합니다.';
    if (/rate limit/i.test(m)) return '요청이 너무 잦습니다. 잠시 후 다시 시도해주세요.';
    return m || '알 수 없는 오류가 발생했습니다.';
  }

  function handleAuthSubmit(e) {
    e.preventDefault();
    if (!window.sb) return;
    var email = (document.getElementById('eureka-auth-email') || {}).value || '';
    var password = (document.getElementById('eureka-auth-password') || {}).value || '';
    var submit = document.getElementById('eureka-auth-submit');
    setAuthError('');
    setAuthHint('');
    if (submit) { submit.disabled = true; submit.textContent = '처리 중...'; }

    var action = authMode === 'signup'
      ? window.sb.auth.signUp({ email: email, password: password })
      : window.sb.auth.signInWithPassword({ email: email, password: password });

    action.then(function (result) {
      var error = result && result.error;
      if (error) {
        setAuthError(friendlyAuthError(error.message));
        return;
      }
      var session = result && result.data && result.data.session;
      if (authMode === 'signup' && !session) {
        // 이메일 확인이 켜져 있는 프로젝트라면 세션이 바로 안 온다.
        // (가이드대로 껐다면 여기 안 걸리고 바로 로그인된다.)
        setAuthHint('가입 확인 메일을 보냈습니다. 메일함을 확인해주세요.');
        return;
      }
      if (typeof window.showToast === 'function') {
        window.showToast(authMode === 'signup' ? '가입되었습니다!' : '로그인되었습니다.');
      }
      closeAuthModal();
      var form = document.getElementById('eureka-auth-form');
      if (form) form.reset();
    }).catch(function (err) {
      setAuthError(friendlyAuthError(err && err.message));
    }).then(function () {
      if (submit) { submit.disabled = false; restoreSubmitLabel(authMode); }
    });
  }

  function handleSignOut() {
    if (!window.sb) return;
    window.sb.auth.signOut().then(function () {
      if (typeof window.showToast === 'function') window.showToast('로그아웃되었습니다.');
    });
  }

  /* ── 헤더 로그인 칩 ─────────────────────────────────────────────── */

  function findHeaderMount() {
    for (var i = 0; i < HEADER_CHIP_TARGETS.length; i++) {
      var el = document.querySelector(HEADER_CHIP_TARGETS[i]);
      if (el) return el;
    }
    return null;
  }

  function mountHeaderChip() {
    if (document.getElementById('eureka-header-chip')) return renderHeaderChip();
    var chip = document.createElement('div');
    chip.className = 'eureka-header-chip';
    chip.id = 'eureka-header-chip';

    var mount = findHeaderMount();
    if (mount) {
      mount.appendChild(chip);
    } else {
      chip.classList.add('eureka-header-chip-fallback');
      document.body.appendChild(chip);
      console.warn(LOG, '헤더 마운트 지점을 못 찾아 고정 위치로 띄웠습니다 — SELECTORS/HEADER_CHIP_TARGETS 확인 필요.');
    }
    renderHeaderChip();
  }

  function renderHeaderChip() {
    var chip = document.getElementById('eureka-header-chip');
    if (!chip) return;
    var user = currentUser();
    if (user) {
      chip.innerHTML =
        '<div class="eureka-user-chip">' +
          '<span class="eureka-user-email" title="' + escapeHtml(user.email) + '">' + escapeHtml(user.email) + '</span>' +
          '<button type="button" class="eureka-logout-btn" id="eureka-logout-btn">로그아웃</button>' +
        '</div>';
      var btn = document.getElementById('eureka-logout-btn');
      if (btn) btn.addEventListener('click', handleSignOut);
    } else {
      chip.innerHTML = '<button type="button" class="eureka-login-btn" id="eureka-login-btn">로그인</button>';
      var loginBtn = document.getElementById('eureka-login-btn');
      if (loginBtn) loginBtn.addEventListener('click', function () { openAuthModal('signin'); });
    }
  }

  function escapeHtml(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
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

  function rowToIdeaItem(row) {
    var item = {};
    var payload = row.payload || {};
    for (var k in payload) item[k] = payload[k];
    item.idea_key = row.idea_key;
    item.period = row.period;
    item.periodKey = row.period;
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
    var originalSyncSavedIdea = window.syncSavedIdea;

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
        if (!isLoggedIn()) return originalToggleSaveIdea(btn, index);
        var idea = generatedIdeas[index];
        var existing = savedIdeas.filter(function (i) { return i.name === idea.name; })[0];
        var wasSaved = !!existing;
        var ideaKeyToDelete = existing ? existing.idea_key : null;

        withLocalStorageSuppressed(function () { originalToggleSaveIdea(btn, index); });

        if (wasSaved) {
          if (!ideaKeyToDelete) return; // 서버 동기 전 로컬에만 있던 항목 — 삭제할 서버 행이 없다
          window.EUREKA.auth.apiFetchJson('/api/library/ideas/' + encodeURIComponent(ideaKeyToDelete), { method: 'DELETE' })
            .then(function (r) { if (!r.ok) libToast('보관함 동기화에 실패했어요. 잠시 후 다시 시도해주세요.'); });
        } else {
          var newEntry = savedIdeas[savedIdeas.length - 1];
          if (!newEntry) return;
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

    if (typeof originalSyncSavedIdea === 'function') {
      window.syncSavedIdea = function (idea) {
        if (!isLoggedIn()) return originalSyncSavedIdea(idea);
        withLocalStorageSuppressed(function () { originalSyncSavedIdea(idea); });
        var entry = savedIdeas.filter(function (s) { return s.name === idea.name; })[0];
        if (entry && entry.idea_key) {
          window.EUREKA.auth.apiFetchJson('/api/library/ideas/' + encodeURIComponent(entry.idea_key), {
            method: 'PATCH', body: { payload: entry }
          }).then(function (r) { if (!r.ok) libToast('저장된 아이디어 동기화에 실패했어요.'); });
        }
      };
    }
  }

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
      openModal: openAuthModal,
      closeModal: closeAuthModal,
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
        injectStyleOnce();
        mountHeaderChip();
        installLibraryOverrides();
        bootSession();
        // 로그인이 확인될 때마다(부팅 시 기존 세션 포함) 이관 후 서버 기준으로 로드.
        window.EUREKA.auth.onSignedIn(function (user) {
          migrateLocalLibraryIfNeeded(user).then(function () { return loadLibrary(); });
        });
        // 로그아웃하면 화면은 빈 보관함으로 — localStorage는 건드리지 않는다.
        window.EUREKA.auth.onSignedOut(function () {
          savedKeywords = [];
          savedIdeas = [];
          rerenderAfterLibraryChange();
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
