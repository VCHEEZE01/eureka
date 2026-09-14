import assert from 'node:assert/strict';
import { readFileSync, mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import path from 'node:path';
import vm from 'node:vm';
import test from 'node:test';

const viewSource = readFileSync('reference-pages/collection-runtime.js','utf8').split('/* Collection controller */')[0];
const viewContext={window:{}};vm.runInNewContext(viewSource,viewContext);
const describeCollection=viewContext.window.__describeCollection;

const fixture = {
  id: 'problem-실제-id', title: '<img src=x onerror=alert(1)> 문제', one_liner: '확인한 요약', category: 'IT/생산성',
  description: '검증용 서술', context: '검증용 맥락', complexity_note: '검증용 추가 확인',
  case_count: 1, source_count: 1, updated_at: '2026-09-13T00:00:00Z',
  gate: { passed: false, min_cases: 20, min_sources: 3, min_evidence: 3, case_count_ok: false, source_count_ok: false, evidence_count_ok: false, reason: '표본 부족' },
  signals: { source_kind_counts: {블로그:1}, source_name_counts: {네이버:1}, weekly_counts: [], undated_count: 1, observed_weeks: 0, first_posted_at: null, last_posted_at: null, severity_counts: {높음:1}, severity_labeled_count: 1, need_signal_count: 0, payment_signal_count: 0, role_counts: {}, role_labeled_count: 0, age_counts: {}, age_labeled_count: 0, gender_counts: {}, gender_labeled_count: 0, mentioned_services: [] },
  evidence: [{ raw_item_id: 'r1', source_name: '네이버', summary: '<script>bad()</script>', source_url: 'https://example.com/post?x=1&y=2', severity: '높음' }],
};
function runPage(name, problems, query = '', reviews = {}, options = {}) {
  const elements = new Map();
  function element(id) {
    if (!elements.has(id)) elements.set(id, {innerHTML: '', textContent: '', style: {}, classList: {add(){}, remove(){}, toggle(){}}, querySelectorAll(){return []}, handlers:{}, addEventListener(type,handler){this.handlers[type]=handler}, insertAdjacentHTML(_, text){this.innerHTML += text}, setAttribute(){}});
    return elements.get(id);
  }
  const source = readFileSync(`reference-pages/${name}.html`, 'utf8').match(/<script>([\s\S]*?)<\/script>/)[1];
  const parent = {__dataMode:options.mode || 'review', __problems:problems, __search:query, __reviews:reviews, __collectionRun:options.run ? {target_match_policy:'evidence_v2',...options.run} : options.run, __describeCollection:describeCollection};
  parent.__collections = {canStartFresh:run=>Boolean(run?.current_plan_version && run?.plan_version && run.current_plan_version!==run.plan_version && ['completed','failed'].includes(run.status)),canContinue:run=>Boolean(run?.has_more && run?.status==='completed'),subscribe(fn){parent.listener=fn;fn(parent.__collectionRun);return ()=>{}},resume(){}};
  element.update = run => { parent.__collectionRun={target_match_policy:'evidence_v2',...run};parent.__problems=run.problems || [];parent.__reviews=run.reviews || {};parent.listener(parent.__collectionRun); };
  vm.runInNewContext(source, {parent,window:{addEventListener(){}}, document: {getElementById:element, querySelector:element, querySelectorAll(){return []}}, localStorage:{getItem(){return null}}, URLSearchParams, URL, console});
  return element;
}
test('real string IDs navigate safely and generated text is escaped', () => {
  const el = runPage('result', [fixture]);
  assert.match(el('problem-list-wrapper').innerHTML, /data-problem-id="problem-실제-id"/);
  assert.match(el('problem-list-wrapper').innerHTML, /&lt;img/);
  assert.doesNotMatch(el('problem-list-wrapper').innerHTML, /<img/);
});
test('empty live list never falls back to demo records', () => {
  const el=runPage('result', []);
  assert.equal(el('total-count-text').textContent, '0개');
  assert.equal(el('pagination-wrapper').innerHTML, '');
  assert.match(el('problem-list-wrapper').innerHTML, /이번 조건에서 표시할 문제정의가 없습니다/);
});
test('unknown detail ID shows missing state without first-record fallback', () => {
  const el=runPage('detail', [fixture], '?id=missing');
  assert.match(el('.main-content').innerHTML, /문제를 찾을 수 없습니다/);
  assert.equal(el('side-cases-count').textContent, '–');
  assert.equal(el('side-problem-tag').textContent, '');
  assert.equal(el('side-problem-tag').hidden, true);
  assert.equal(el('btn-save-problem').onclick, null);
});
test('review detail keeps gate failure, suppresses tiny samples, and links to evidence', () => {
  const el=runPage('detail', [fixture], '?id='+encodeURIComponent(fixture.id));
  assert.equal(el('gate-result').textContent, '게시 보류');
  assert.match(el('severity-bars').textContent, /3건 미만/);
  assert.match(el('reviews-container-live').innerHTML, /https:\/\/example.com\/post\?x=1&amp;y=2/);
  assert.match(el('reviews-container-live').innerHTML, /&lt;script&gt;/);
  const unsafe=structuredClone(fixture); unsafe.evidence[0].source_url='javascript:alert(1)';
  assert.doesNotMatch(runPage('detail', [unsafe], '?id='+encodeURIComponent(fixture.id))('reviews-container-live').innerHTML, /javascript:/);
});
test('single file rejects held data in published mode; embeds review JSON safely', () => {
  const dir=mkdtempSync(path.join(tmpdir(),'eureka-ui-'));
  try {
    const input=path.join(dir,'problems.json'), output=path.join(dir,'preview.html');
    writeFileSync(input,JSON.stringify([fixture]));
    assert.throws(()=>execFileSync(process.execPath,['scripts/build-reference-single.mjs','--data',input,'--mode','published','--out',output],{stdio:'pipe'}),/게시 보류 데이터/);
    execFileSync(process.execPath,['scripts/build-reference-single.mjs','--data',input,'--mode','review','--out',output]);
    const html=readFileSync(output,'utf8');
    assert.match(html,/window.__dataMode = "review"/);
    assert.doesNotMatch(html,/<script>bad/);
    for(const match of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)) if(!match[0].includes('application/json')) new vm.Script(match[1]);
  } finally {rmSync(dir,{recursive:true,force:true});}
});

test('AI hold reason is displayed literally without interpreting source text as HTML', () => {
  const el=runPage('detail', [fixture], '?id='+encodeURIComponent(fixture.id), {[fixture.id]: {decision:'hold', reason:'<script>unsafe()</script> 근거 범위 초과'}});
  assert.equal(el('ai-review-status').hidden, false);
  assert.equal(el('ai-review-status').textContent, 'AI 검수: 보류 / 사유: <script>unsafe()</script> 근거 범위 초과');
  assert.equal(el('ai-review-status').innerHTML, '');
});

test('live empty result explains zero target matches and retains actual collected/unconfirmed counts', () => {
  const el=runPage('result', [], '', {}, {mode:'live', run:{counts:{collected:31,target_matched:0,target_unconfirmed:31,judged:0,problems:0},warnings:[]}});
  assert.match(el('collection-result-counts').textContent, /타겟 확인 0건 · 타겟 미확인 31건/);
  assert.match(el('collection-result-caption').textContent, /작성자 신원·모든 속성의 인증은 아닙니다/);
  assert.match(el('problem-list-wrapper').innerHTML, /선택한 타겟과 연관된 근거를 확보하지 못해/);
  assert.ok(Number.parseInt(el('category-tab-container').style.top)>418);
});

test('collection warnings are deduplicated in collapsed details and opening them repositions results', () => {
  const el=runPage('result', [], '', {}, {mode:'live', run:{counts:{collected:31,target_matched:3,target_unconfirmed:28,judged:2,problems:0,judge_failed:0,search_failed:1},warnings:['<script>unsafe()</script>', '제외 이유', '제외 이유']}});
  assert.equal(el('collection-result-counts').textContent,'수집 31건 · 분석 2건 · 타겟 확인 3건 · 타겟 미확인 28건 · 문제정의 0개 · 검색 실패 1건');
  assert.equal(el('collection-result-details').hidden,false);
  assert.equal(el('collection-result-warnings').textContent,'<script>unsafe()</script>\n제외 이유');
  assert.equal(el('collection-result-warnings').innerHTML,'');
  const oldTop=Number.parseInt(el('category-tab-container').style.top);
  el('collection-result-note').offsetHeight=220;
  el('collection-result-details').handlers.toggle();
  assert.ok(Number.parseInt(el('category-tab-container').style.top)>oldTop);
});


test('round budget, cumulative coverage and query counts are visible without invented counts',()=>{
 const el=runPage('result',[], '', {}, {mode:'live',run:{status:'completed',has_more:true,round_index:2,stop_reason:'round_budget',counts:{collected:4,judged:3,target_confirmed:2,target_unconfirmed:1,pain_items:1,problems:0},cumulative_counts:{collected:9,judged:7,target_confirmed:4,pain_items:2},coverage:{catalog_total:80,catalog_completed:12,catalog_remaining:68,topics_total:20,topics_searched:4,intents_total:8,intents_searched:3},query_results:[{keyword:'<script>query()</script>',category:'IT/생산성',topic:'협업',intent:'불편',source_name:'네이버 블로그',status:'succeeded',result_count:3,new_count:1}],exclusion_reasons:{'원문에서 타겟 연관 미확인':1}}});
 assert.match(el('collection-result-technical').textContent,/2회차 · 전체 검색 항목 12 \/ 80개 진행 · 남은 검색 68개/);
 assert.match(el('collection-result-counts').textContent,/타겟 확인 4건/);
 assert.match(el('collection-result-cumulative').textContent,/이번 처리 · 수집 4건/);
 assert.match(el('collection-result-stop').textContent,/처리 한도/);assert.equal(el('continue-search').hidden,false);
 assert.match(el('collection-query-results').textContent,/<script>query/);assert.equal(el('collection-query-results').innerHTML,'');
 assert.match(el('collection-query-results').textContent,/반환 3건 · 신규 저장 1건/);
 assert.match(el('collection-exclusion-reasons').textContent,/미확인: 1건/);
 assert.match(el('problem-list-wrapper').innerHTML,/추가 탐색을 할 수 있습니다/);
});
test('catalog exhaustion is distinguished from budget stop and cannot continue',()=>{
 const el=runPage('result',[], '', {},{mode:'live',run:{status:'completed',has_more:false,stop_reason:'catalog_exhausted',counts:{collected:0},coverage:{catalog_total:4,catalog_completed:4,catalog_remaining:0}}});
 assert.match(el('collection-result-stop').textContent,/검색 범위를 모두 확인/);assert.equal(el('continue-search').hidden,true);
 assert.doesNotMatch(el('collection-result-counts').textContent,/타겟 확인/);
});
test('production build has live routes and no sample result/detail seed fallback',()=>{
 const dir=mkdtempSync(path.join(tmpdir(),'eureka-live-'));
 try {
  const output=path.join(dir,'live.html');execFileSync(process.execPath,['scripts/build-reference-single.mjs','--out',output]);
  const html=readFileSync(output,'utf8');assert.match(html,/window.__dataMode = "live"/);
  assert.doesNotMatch(html,/demoData|study-001|food-001|workout-001|id: 24,/);
  const packed=JSON.parse(html.match(/<script id="pages" type="application\/json">([\s\S]*?)<\/script>/)[1]);
  assert.deepEqual(Object.keys(packed),['index.html','config.html','loading.html','result.html','detail.html']);
  assert.throws(()=>execFileSync(process.execPath,['scripts/build-reference-single.mjs','--mode','demo','--out',output],{stdio:'pipe'}));
  for(const page of Object.values(packed)) for(const script of page.matchAll(/<script>([\s\S]*?)<\/script>/g)) new vm.Script(script[1]);
 } finally {rmSync(dir,{recursive:true,force:true});}
});


test('target review candidates stay separate from problems and preserve reasons with safe source links',()=>{
 const el=runPage('result',[], '', {},{mode:'live',run:{status:'completed',counts:{pain_detected:3,pain_items:1},review_candidates:[{raw_item_id:'raw1',pain_summary:'<b>불편</b>',target_status:'unconfirmed',reason:'직업 근거 부족',source_name:'카페',source_url:'https://example.com/raw?x=1&y=2'},{raw_item_id:'raw2',pain_summary:'다른 실제 판정',target_status:'conflict',reason:'원문에서 다른 역할 확인',source_url:'javascript:alert(1)'}]}});
 assert.match(el('collection-result-counts').textContent,/발견 불편 3건 · 타겟 확인 불편 1건/);
 assert.equal(el('total-count-text').textContent,'0개');
 assert.equal(el('collection-target-review').hidden,false);
 assert.match(el('collection-target-review-title').textContent,/2건 · 타겟 확인 필요/);
 const html=el('collection-target-review-list').innerHTML;
 assert.match(html,/연관 미확인/);assert.match(html,/직업 근거 부족/);assert.match(html,/&lt;b&gt;불편/);
 assert.match(html,/https:\/\/example.com\/raw\?x=1&amp;y=2/);assert.doesNotMatch(html,/javascript:/);
});


test('exhausted query catalog with judgement backlog still explains continuation accurately',()=>{
 const el=runPage('result',[], '', {},{mode:'live',run:{status:'completed',has_more:true,stop_reason:'llm_budget',counts:{collected:0,judged:0,target_confirmed:0},coverage:{catalog_total:4,catalog_completed:4,catalog_remaining:0},exclusion_reasons:{awaiting_judgement:12}}});
 assert.match(el('collection-result-technical').textContent,/남은 검색 0개/);
 assert.match(el('collection-result-stop').textContent,/남은 검색·판별·문제정의 자료/);
 assert.match(el('collection-exclusion-reasons').textContent,/판별 대기: 12건/);
 assert.equal(el('continue-search').hidden,false);
 assert.match(el('problem-list-wrapper').innerHTML,/처리하지 않은 검색·판별·문제정의 자료/);
 assert.doesNotMatch(el('problem-list-wrapper').innerHTML,/검색하지 않은 항목/);
});

test('running results show live discoveries and refresh without declaring an empty final result',()=>{
 const el=runPage('result',[], '', {},{mode:'live',run:{status:'running',stage:'interpreting',has_more:true,counts:{collected:30,judged:10,pain_detected:4,target_confirmed:0},coverage:{topics_searched:12,catalog_total:25344},review_candidates:[{raw_item_id:'r1',pain_summary:'대기 시간이 길다',target_status:'unconfirmed'}]}});
 assert.match(el('collection-result-progress').textContent,/자동으로 갱신/);
 assert.match(el('collection-result-counts').textContent,/분석 10건/);
 assert.equal(el('discovered-pain-count').textContent,'4건');
 assert.match(el('collection-result-coverage').textContent,/검색한 주제 12개/);
 assert.doesNotMatch(el('collection-result-coverage').textContent,/회차|25344|카탈로그/);
 assert.doesNotMatch(el('collection-result-stop').textContent,/추가 탐색/);
 assert.match(el('problem-list-wrapper').innerHTML,/탐색이 계속 진행 중/);
 assert.equal(el('collection-target-review').hidden,false);
 el.update({status:'running',stage:'generating',counts:{collected:30,judged:30,pain_detected:12},problems:[fixture]});
 assert.equal(el('total-count-text').textContent,'1개');
 assert.match(el('problem-list-wrapper').innerHTML,/problem-실제-id/);
 assert.match(el('collection-result-counts').textContent,/발견 불편 12건/);
});
test('every unconfirmed pain is accessible in twenty-item pages without hiding the section',()=>{
 const candidates=Array.from({length:45},(_,i)=>({raw_item_id:`r${i}`,pain_summary:`pain-${i}-end`,target_status:'unconfirmed'}));
 const el=runPage('result',[], '', {},{mode:'live',run:{status:'completed',review_candidates:candidates}});
 assert.match(el('collection-target-review-title').textContent,/45건/);
 assert.equal(el('collection-target-review').hidden,false);
 assert.match(el('review-page').textContent,/1 \/ 3페이지 · 전체 45건/);
 assert.match(el('collection-target-review-list').innerHTML,/pain-19-end/);
 assert.doesNotMatch(el('collection-target-review-list').innerHTML,/pain-20-end/);
 el('review-next').handlers.click();el('review-next').handlers.click();
 assert.match(el('collection-target-review-list').innerHTML,/pain-44-end/);
 assert.equal(el('review-next').disabled,true);
 assert.equal(el('total-count-text').textContent,'0개');
 el('review-prev').handlers.click();assert.match(el('review-page').textContent,/2 \/ 3페이지/);
 const page=readFileSync('reference-pages/result.html','utf8');
 assert.match(page,/<section id="collection-target-review"/);
 assert.doesNotMatch(page,/<details id="collection-target-review"/);
});

test('old plan notice preserves discoveries and offers an explicit wider search',()=>{
 const el=runPage('result',[fixture], '', {},{mode:'live',run:{status:'completed',plan_version:'v3',current_plan_version:'v4',has_more:true,counts:{pain_detected:14}}});
 assert.equal(el('discovered-pain-count').textContent,'14건');
 assert.equal(el('total-count-text').textContent,'1개');
 assert.match(el('collection-plan-notice').textContent,/새 탐색부터 적용/);
 assert.equal(el('new-range-search').hidden,false);
});

test('generation failures and retry attempts show the right units without implying more problems',()=>{
 const el=runPage('result',[fixture], '', {},{mode:'live',run:{status:'completed',counts:{generation_failed:1,generation_retries:2},cumulative_counts:{problems:1,generation_failed:3,generation_retries:4}}});
 assert.match(el('collection-result-counts').textContent,/문제정의 1개 · 문제 생성·검수 실패 3건 · 형식 재시도 4회/);
 assert.match(el('collection-result-cumulative').textContent,/문제 생성·검수 실패 1건 · 형식 재시도 2회/);
 assert.equal(el('total-count-text').textContent,'1개');
 assert.doesNotMatch(describeCollection({target_match_policy:'evidence_v2',counts:{generation_failed:0,generation_retries:0}}).counts,/생성·검수 실패|형식 재시도/);
});
