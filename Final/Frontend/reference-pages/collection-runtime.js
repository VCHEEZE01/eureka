/* Same-origin collection controller for the reference HTML. No sample fallback. */
// Shared textual presentation; counts are server measurements, never estimates.
window.__describeCollection = function(run) {
  const legacy = run?.target_match_policy !== 'evidence_v2';
  if (legacy) return {counts:'', cumulative:'', coverage:'', technical:'', progress:'', planNotice:'', stop:'', queries:'', exclusions:'', warnings:''};
  const integer = n => Number.isInteger(n) && n >= 0;
  const describeCounts = counts => {
    const values = {...(counts || {}), target_confirmed:counts?.target_confirmed ?? counts?.target_matched};
    const labels = {collected:'수집', judged:'분석', target_confirmed:'타겟 확인', target_unconfirmed:'타겟 미확인', pain_detected:'발견 불편', pain_items:'타겟 확인 불편', problems:'문제정의'};
    const parts = Object.entries(labels).filter(([key]) => integer(values[key])).map(([key,label]) => `${label} ${values[key]}${key === 'problems' ? '개' : '건'}`);
    for (const [key,label] of [['target_conflicts','타겟 충돌'],['search_failed','검색 실패'],['judge_failed','판별 실패']]) if (integer(values[key]) && values[key] > 0) parts.push(`${label} ${values[key]}${key === 'problems' ? '개' : '건'}`);
    if (integer(values.generation_failed) && values.generation_failed > 0) parts.push(`문제 생성·검수 실패 ${values.generation_failed}건`);
    if (integer(values.generation_retries) && values.generation_retries > 0) parts.push(`형식 재시도 ${values.generation_retries}회`);
    return parts.join(' · ');
  };
  const coverage = run.coverage || {};
  const coverageParts = [];
  if (integer(run.round_index)) coverageParts.push(`${run.round_index}회차`);
  if (integer(coverage.catalog_completed) && integer(coverage.catalog_total)) coverageParts.push(`전체 검색 항목 ${coverage.catalog_completed} / ${coverage.catalog_total}개 진행`);
  if (integer(coverage.catalog_remaining)) coverageParts.push(`남은 검색 ${coverage.catalog_remaining}개`);
  if (integer(coverage.topics_searched) && integer(coverage.topics_total)) coverageParts.push(`주제 ${coverage.topics_searched} / ${coverage.topics_total}개`);
  if (integer(coverage.intents_searched) && integer(coverage.intents_total)) coverageParts.push(`검색 의도 ${coverage.intents_searched} / ${coverage.intents_total}개`);
  const oldPlan = Boolean(run.current_plan_version && run.plan_version && run.current_plan_version !== run.plan_version);
  const planNotice = oldPlan ? '이전 탐색 범위의 기록입니다. 새로 넓어진 검색 범위와 처리량은 새 탐색부터 적용됩니다.' : '';
  const topicSummary = integer(coverage.topics_searched) ? `검색한 주제 ${coverage.topics_searched}개` : '';
  const progress = ['queued','running'].includes(run.status) ? ({queued:'탐색을 준비하고 있습니다.',searching:'관련 주제의 글을 수집하고 있습니다.',interpreting:'수집한 글을 분석하며 불편과 타겟 연관성을 확인하고 있습니다.',evidence:'확인된 불편의 근거를 연결하고 있습니다.',generating:'근거를 바탕으로 문제정의를 작성하고 검수하고 있습니다.'}[run.stage] || '탐색을 진행하고 있습니다.') + ' 이 화면에서도 발견한 내용이 자동으로 갱신됩니다.' : run.status === 'completed' ? '수집한 자료의 탐색 결과입니다.' : run.status === 'failed' ? '탐색이 중단되었습니다. 현재까지 확인한 내용은 아래에서 볼 수 있습니다.' : run.error || run.message || '';
  const stops = {round_budget:'이번 탐색의 처리 한도에 도달했습니다.', time_budget:'이번 탐색의 실행 시간 한도에 도달했습니다.', llm_budget:'이번 탐색의 AI 분석 한도에 도달했습니다.', catalog_exhausted:'계획된 검색 범위를 모두 확인했습니다.', failed:'이번 실행이 실패했습니다.'};
  const stop = (stops[run.stop_reason] || '') + (run.has_more === true && !oldPlan && ['completed','failed'].includes(run.status) ? ' 필요하면 추가 탐색으로 남은 검색·판별·문제정의 자료를 처리할 수 있습니다.' : '');
  const queries = (Array.isArray(run.query_results) ? run.query_results : []).map(row => {
    const result = integer(row.result_count) ? `반환 ${row.result_count}건` : '반환 건수 미기록';
    const fresh = integer(row.new_count) ? `신규 저장 ${row.new_count}건` : '신규 건수 미기록';
    return `${row.keyword || '검색어 미기록'}
${[row.category,row.topic,row.intent,row.source_name].filter(Boolean).join(' · ')} · ${row.status === 'succeeded' ? '성공' : row.status === 'failed' ? '실패' : '상태 확인 필요'} · ${result} · ${fresh}${row.error ? '\n사유: ' + row.error : ''}`;
  }).join('\n\n');
  const exclusionLabels = {target_unconfirmed:'타겟 연관 미확인',target_conflict:'타겟 조건 충돌',not_pain:'불편 아님',insufficient:'판단 정보 부족',rule_filtered:'규칙 필터 제외',awaiting_judgement:'판별 대기'};
  const exclusions = Object.entries(run.exclusion_reasons || {}).filter(([,count]) => integer(count)).map(([reason,count]) => `${exclusionLabels[reason] || reason}: ${count}건`).join('\n');
  const warnings = [...new Set((Array.isArray(run.warnings) ? run.warnings : []).filter(value => typeof value === 'string' && value.trim()))].join('\n');
  return {counts:describeCounts(run.counts), cumulative:describeCounts(run.cumulative_counts), coverage:topicSummary, technical:coverageParts.join(' · '), progress, planNotice, stop, queries, exclusions, warnings};
};
/* Collection controller */
(() => {
  if (window.__dataMode !== 'live') return;
  const storageKey = 'eureka_collection_run_v1';
  const listeners = new Set();
  let state = null;
  let timer = null;
  let requestVersion = 0;
  let activeRequest = null;
  const safeRead = () => { try { return JSON.parse(sessionStorage.getItem(storageKey) || 'null'); } catch { return null; } };
  const save = value => { try { sessionStorage.setItem(storageKey, JSON.stringify(value)); } catch {} };
  const normalizedTokens = values => [...new Set((values || []).map(value => value.trim().replace(/\s+/g, ' ')).filter(Boolean))].sort();
  const targetKey = target => JSON.stringify({age:target.age || null, gender:target.gender || null, jobs:normalizedTokens(target.jobs), places:normalizedTokens(target.places)});
  const notify = () => { window.__collectionRun = state; listeners.forEach(fn => fn(state)); };
  const clearData = () => { window.__problems = []; window.__reviews = {}; };
  const setError = (message, saved = safeRead()) => {
    state = {...(state || {}), id:saved?.id, target:saved?.target, status:'connection_error', message, error:message};
    notify();
  };
  const requireServer = () => {
    if (!['http:', 'https:'].includes(location.protocol)) throw new Error('실제 탐색은 서버에서 실행됩니다. 백엔드를 실행한 뒤 http://localhost:8000 에서 열어 주세요.');
  };
  async function api(url, options = {}) {
    requireServer();
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000);
    try {
      const response = await fetch(url, {...options, signal:controller.signal, cache:'no-store'});
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        const detail = typeof body.detail === 'string' ? body.detail : body.detail?.message;
        throw new Error(detail || (response.status === 409 ? '다른 조건의 탐색이 진행 중입니다. 해당 실행이 끝난 뒤 다시 시도해 주세요.' : `탐색 요청을 처리하지 못했습니다. (${response.status})`));
      }
      if (!body.id || !['queued','running','completed','failed'].includes(body.status)) throw new Error('서버의 탐색 응답을 확인할 수 없습니다.');
      return body;
    } catch (error) {
      if (error.name === 'AbortError') throw new Error('서버 응답 대기 시간이 초과되었습니다. 실행 상태 확인을 다시 시도해 주세요.');
      throw error;
    } finally { clearTimeout(timeout); }
  }
  function accept(run, version) {
    if (version !== requestVersion) return;
    const legacy = run.target_match_policy !== 'evidence_v2';
    state = legacy ? {...run, status:'legacy', message:'이전 판별 기준의 실행입니다. 근거에 기반한 타겟 확인을 위해 같은 조건으로 새로 탐색해 주세요.'} : run;
    save({id:run.id, target:run.target, resume_from:run.resume_from || null, pending:false});
    window.__collectionTarget = run.target;
    if (!legacy) {
      window.__problems = Array.isArray(run.problems) ? run.problems : [];
      window.__reviews = run.reviews || {};
    } else clearData();
    notify();
    if (!legacy && ['queued','running'].includes(run.status)) timer = setTimeout(() => poll(run.id, version), 1500);
  }
  async function poll(id, version) {
    if (version !== requestVersion) return;
    try { accept(await api('/collections/' + encodeURIComponent(id)), version); }
    catch (error) { if (version === requestVersion) setError(error.message); }
  }
  async function resume() {
    if (activeRequest) return activeRequest;
    if (state && ['queued','running','completed','failed'].includes(state.status)) { notify(); return; }
    const saved = safeRead();
    clearTimeout(timer);
    clearData();
    try { requireServer(); } catch (error) { setError(error.message, saved); return; }
    if (!saved?.id) {
      setError(saved?.pending ? '실행 번호를 받기 전에 연결이 중단되었습니다.' : '탐색을 시작하려면 먼저 타겟 조건을 입력해 주세요.', saved);
      if (saved?.pending) setError('실행 번호를 받기 전에 연결이 중단되었습니다. 아래 재시도 버튼으로 같은 조건의 실행을 확인해 주세요.', saved);
      return;
    }
    state = {id:saved.id, target:saved.target, status:'restoring', message:'저장된 실행 상태를 확인하고 있습니다.'};
    notify();
    const version = ++requestVersion;
    activeRequest = poll(saved.id, version).finally(() => {activeRequest = null;});
    return activeRequest;
  }
  async function start(target, resumeFrom = null) {
    if (activeRequest) { await activeRequest; const saved = safeRead(); if (targetKey(saved?.target || {}) === targetKey(target) && (saved?.resume_from || null) === resumeFrom) return; }
    try { requireServer(); } catch (error) { setError(error.message, {target}); return; }
    clearTimeout(timer);
    const version = ++requestVersion;
    clearData();
    window.__collectionTarget = target;
    save({target, resume_from:resumeFrom, pending:true});
    state = {status:'submitting', target, message:resumeFrom ? '남은 검색·분석 자료의 추가 탐색을 요청하고 있습니다.' : '입력한 조건으로 탐색을 요청하고 있습니다.'};
    notify();
    activeRequest = (async () => {
      try { accept(await api('/collections', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(resumeFrom ? {target, resume_from:resumeFrom} : {target})}), version); }
      catch (error) { if (version === requestVersion) setError(error.message); }
      finally { activeRequest = null; }
    })();
    return activeRequest;
  }
  async function retry() {
    const saved = safeRead();
    if (saved?.id && !['failed','legacy'].includes(state?.status)) { state = null; return resume(); }
    if (saved?.target) return start(saved.target, saved.pending ? saved.resume_from || null : null);
  }
  function canContinue(run = state) {
    if (run?.can_resume === false || (run?.current_plan_version && run?.plan_version && run.current_plan_version !== run.plan_version)) return false;
    return Boolean(run?.id && run.target_match_policy === 'evidence_v2' && ['completed','failed'].includes(run.status) && run.has_more === true);
  }
  function canStartFresh(run = state) {
    return Boolean(run?.target && run.current_plan_version && run.plan_version && run.current_plan_version !== run.plan_version && ['completed','failed'].includes(run.status));
  }
  function canView(run = state) {
    return Boolean(run?.id && run.target_match_policy === 'evidence_v2' && ['queued','running','completed','failed','connection_error'].includes(run.status));
  }
  async function continueSearch() {
    if (!canContinue()) return;
    return start(state.target, state.id);
  }
  window.__collections = {
    start, resume, retry, continueSearch, canContinue, canView, canStartFresh,
    getState: () => state,
    hasTarget: () => Boolean(safeRead()?.target),
    subscribe(fn) { listeners.add(fn); fn(state); return () => listeners.delete(fn); },
  };
  if (location.protocol === 'file:' && document.querySelector('.data-mode-label')) document.querySelector('.data-mode-label').textContent = '실제 탐색: 백엔드를 실행한 뒤 http://localhost:8000 에서 열어 주세요.';
})();
