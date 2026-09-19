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
 * ===================================================================== */

(function () {
  'use strict';

  var VERSION = '0.1.0-seam';       // 단계 1: 이음매만. 동작 변경 없음.
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
      'showToast', 'navigateTo', 'esc', 'aiToolsFor'
    ]
  };

  var SELECTORS = {
    ideaTabsBox: 'ideas-tabs-container',
    resultScreen: 'result-main-screen',
    ideaDetailBox: 'active-idea-card-container',
    toast: 'toast-popup'
  };

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
   * (지금은 훅만 있고 붙이는 건 없다 — 새로고침 버튼이 여기 올라탄다.) */

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

  /* ── 바깥에 내보내는 것 ─────────────────────────────────────────────
   * 다음 단계(인증·보관함·새로고침)가 여기에 올라탄다.
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
    /** 화면에 이미 떠 있는 요소를 건드리지 않고 상태만 보고 싶을 때. */
    describe: function () {
      return {
        version: VERSION,
        served: isServed,
        contractOk: checkContract(),
        tabsHooked: !!(window.renderIdeasTabs && window.renderIdeasTabs.__eurekaWrapped),
        hooks: afterTabsRender.length
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
      if (isDebug) console.info(LOG, 'boot 완료', window.EUREKA.describe());
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
