import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';
const source=readFileSync('reference-pages/collection-runtime.js','utf8');
const target={age:'30대',gender:null,jobs:['간호사'],places:[]};
const run=(id,status='completed',extra={})=>({id,status,target,target_match_policy:'evidence_v2',stage:status==='completed'?'completed':'searching',problems:[],reviews:{},counts:{collected:0},...extra});
function environment(replies, saved=null, protocol='http:'){
 const requests=[], storage=new Map(), timers=new Map(); let seq=0;
 if(saved)storage.set('eureka_collection_run_v1',JSON.stringify(saved));
 const context={window:{__dataMode:'live',__problems:[{id:'old-data'}],__reviews:{old:'data'}},location:{protocol},document:{querySelector(){return {textContent:''}}},sessionStorage:{getItem:key=>storage.get(key)||null,setItem:(key,value)=>storage.set(key,value)},AbortController,setTimeout(fn,ms){timers.set(++seq,{fn,ms});return seq},clearTimeout(id){timers.delete(id)},fetch:async(url,options)=>{
  requests.push({url,options});const next=replies.shift();
  if(next instanceof Error)throw next;
  if(!next)throw new Error('unexpected request');
  if(typeof next==='function')return next();
  return {ok:!next.httpError,status:next.httpError||200,json:async()=>next.httpError?{detail:next.detail}:next};
 }};
 vm.runInNewContext(source,context);
 return {controller:context.window.__collections, window:context.window,requests,storage,timers,async poll(){const timer=[...timers.values()].find(t=>t.ms===1500);assert.ok(timer);await timer.fn();}};
}
test('click submits entered target, polls actual stage, and exposes only this run data',async()=>{
 const e=environment([run('one','running'),run('one','completed',{problems:[{id:'fresh'}],reviews:{fresh:{decision:'hold',reason:'표본 부족'}}})]);
 await e.controller.start(target);
 assert.deepEqual(JSON.parse(e.requests[0].options.body),{target});
 assert.equal(e.window.__problems.length,0);
 assert.equal(e.controller.getState().status,'running');
 await e.poll();
 assert.equal(e.requests[1].url,'/collections/one');
 assert.equal(e.controller.getState().status,'completed');
 assert.equal(e.window.__problems[0].id,'fresh');
 assert.equal(e.window.__reviews.fresh.decision,'hold');
});
test('reload resumes saved run with GET and never issues a duplicate POST',async()=>{
 const e=environment([run('restore')],{id:'restore',target,pending:false});
 await e.controller.resume();
 assert.equal(e.requests.length,1);
 assert.equal(e.requests[0].url,'/collections/restore');
 assert.equal(e.requests[0].options.method,undefined);
});
test('changing target clears previous result even when server rejects concurrent collection',async()=>{
 const newTarget={...target,jobs:['디자이너']};
 const e=environment([{httpError:409,detail:{message:'다른 탐색 진행 중'}}],{id:'old',target});
 await e.controller.start(newTarget);
 assert.equal(JSON.parse(e.requests[0].options.body).target.jobs[0],'디자이너');
 assert.equal(e.window.__problems.length,0);
 assert.equal(e.controller.getState().status,'connection_error');
 assert.match(e.controller.getState().message,/다른 탐색/);
});
test('network failure retries saved GET explicitly; failed terminal run retries POST explicitly',async()=>{
 const e=environment([new Error('offline'),run('saved','failed',{error:'AI 호출 실패'}),run('retried')],{id:'saved',target});
 await e.controller.resume();
 assert.equal(e.controller.getState().status,'connection_error');
 await e.controller.retry();
 assert.equal(e.requests[1].url,'/collections/saved');
 assert.equal(e.controller.getState().status,'failed');
 await e.controller.retry();
 assert.equal(e.requests[2].options.method,'POST');
 assert.equal(e.controller.getState().id,'retried');
});
test('file mode and interrupted POST show instructions without automatic requests',async()=>{
 const file=environment([],null,'file:');await file.controller.start(target);
 assert.equal(file.requests.length,0);assert.match(file.controller.getState().message,/http:\/\/localhost:8000/);
 const pending=environment([],{target,pending:true});await pending.controller.resume();
 assert.equal(pending.requests.length,0);assert.match(pending.controller.getState().message,/연결이 중단/);
});
test('double click while POST is pending does not create a second POST',async()=>{
 let finish;
 const e=environment([()=>new Promise(resolve=>{finish=()=>resolve({ok:true,json:async()=>run('one')})})]);
 const first=e.controller.start(target);const second=e.controller.start(target);
 finish();await Promise.all([first,second]);
 assert.equal(e.requests.length,1);
});

test('explicit new search sends POST even after completed saved run, leaving TTL reuse to backend', async()=>{
 const e=environment([run('next')],{id:'completed-old',target});
 await e.controller.start(target);
 assert.equal(e.requests[0].options.method,'POST');
 assert.equal(e.controller.getState().id,'next');
});
test('in-flight duplicate targets ignore token order and extra whitespace', async()=>{
 let finish;
 const canonical={...target,jobs:['간호사','프리랜서'],places:['병원','사무실']};
 const e=environment([()=>new Promise(resolve=>{finish=()=>resolve({ok:true,json:async()=>run('one','running',{target:canonical})})})]);
 const first=e.controller.start(canonical);
 const second=e.controller.start({...canonical,jobs:[' 프리랜서 ','간호사'],places:['사무실','병원']});
 finish();await Promise.all([first,second]);
 assert.equal(e.requests.length,1);
});

test('old unverified saved runs cannot appear as current target results and retry uses POST',async()=>{
 const e=environment([run('old','completed',{target_match_policy:'not_checked',problems:[{id:'unverified'}]}),run('new')],{id:'old',target});
 await e.controller.resume();
 assert.equal(e.controller.getState().status,'legacy');
 assert.equal(e.window.__problems.length,0);
 assert.match(e.controller.getState().message,/이전 판별 기준/);
 await e.controller.retry();
 assert.equal(e.requests[1].options.method,'POST');
 assert.equal(e.controller.getState().id,'new');
});


test('continuation posts source run and same target, then polls child with GET',async()=>{
 const first=run('round-one','completed',{has_more:true,round_index:1,stop_reason:'round_budget'});
 const child=run('round-two','running',{has_more:true,round_index:2,resume_from:'round-one'});
 const e=environment([first,child,run('round-two','completed',{has_more:false,resume_from:'round-one'})],{id:'round-one',target});
 await e.controller.resume();assert.equal(e.controller.canContinue(),true);
 await e.controller.continueSearch();
 assert.deepEqual(JSON.parse(e.requests[1].options.body),{target,resume_from:'round-one'});
 assert.equal(e.window.__problems.length,0);assert.equal(e.controller.canContinue(),false);
 await e.poll();assert.equal(e.requests[2].url,'/collections/round-two');
 assert.equal(e.controller.canContinue(),false);
 await e.controller.continueSearch();assert.equal(e.requests.length,3);
});
test('failed partial run can continue without restarting the first page',async()=>{
 const e=environment([run('partial','failed',{has_more:true}),run('next','queued',{resume_from:'partial'})],{id:'partial',target});
 await e.controller.resume();await e.controller.continueSearch();
 assert.equal(JSON.parse(e.requests[1].options.body).resume_from,'partial');
});
test('old running policy is not polled or exposed and requires an explicit new run',async()=>{
 const e=environment([run('old','running',{target_match_policy:'input_mentions_v1',problems:[{id:'old'}]})],{id:'old',target});
 await e.controller.resume();assert.equal(e.controller.getState().status,'legacy');
 assert.equal(e.window.__problems.length,0);assert.equal(e.controller.canContinue(),false);
 assert.equal([...e.timers.values()].filter(t=>t.ms===1500).length,0);
});
test('interrupted continuation retry preserves resume_from',async()=>{
 const e=environment([run('child','queued',{resume_from:'parent'})],{target,pending:true,resume_from:'parent'});
 await e.controller.resume();assert.equal(e.requests.length,0);await e.controller.retry();
 assert.equal(JSON.parse(e.requests[0].options.body).resume_from,'parent');
});
test('duplicate continuation clicks issue one request',async()=>{
 let finish;const e=environment([run('parent','completed',{has_more:true}),()=>new Promise(resolve=>{finish=()=>resolve({ok:true,json:async()=>run('child','queued',{resume_from:'parent'})})})],{id:'parent',target});
 await e.controller.resume();const first=e.controller.continueSearch();const second=e.controller.continueSearch();
 finish();await Promise.all([first,second]);assert.equal(e.requests.length,2);
});

test('opening in-progress results preserves the same job and GET polling with partial data',async()=>{
 const e=environment([run('active','running',{problems:[{id:'partial'}],reviews:{partial:{decision:'hold'}},review_candidates:[{raw_item_id:'r1',pain_summary:'불편'}]}),run('active','running',{problems:[{id:'partial'},{id:'next'}]}),run('active','completed',{problems:[{id:'final'}]})]);
 await e.controller.start(target);
 assert.equal(e.controller.canView(),true);assert.equal(e.controller.canContinue(),false);
 assert.equal(e.window.__problems[0].id,'partial');assert.equal(e.window.__reviews.partial.decision,'hold');
 const updates=[];const unsubscribe=e.controller.subscribe(value=>updates.push(value.status));
 await e.controller.resume(); // The result view restores without creating a new job.
 assert.equal(e.requests.length,1);
 await e.poll();assert.equal(e.window.__problems.length,2);
 await e.poll();assert.equal(e.window.__problems[0].id,'final');
 assert.deepEqual(e.requests.map(request=>request.options.method || 'GET'),['POST','GET','GET']);
 assert.ok(updates.includes('completed'));unsubscribe();
});
test('failed partial results remain viewable while legacy results remain blocked',async()=>{
 const e=environment([run('partial','failed',{problems:[{id:'saved'}]})],{id:'partial',target});
 await e.controller.resume();assert.equal(e.controller.canView(),true);assert.equal(e.window.__problems[0].id,'saved');
 assert.equal(e.controller.canView(run('legacy','running',{target_match_policy:'old'})),false);
});

test('old plan restore is viewable but resume is disabled; a user starts wider search without resume_from',async()=>{
 const old=run('old','completed',{plan_version:'v3',current_plan_version:'v4',can_resume:false,has_more:true,problems:[{id:'old-result'}]});
 const e=environment([old,run('wide','queued',{plan_version:'v4',current_plan_version:'v4'})],{id:'old',target});
 await e.controller.resume();assert.equal(e.controller.canView(),true);assert.equal(e.controller.canContinue(),false);assert.equal(e.controller.canStartFresh(),true);
 await e.controller.continueSearch();assert.equal(e.requests.length,1);
 await e.controller.start(e.controller.getState().target);assert.deepEqual(JSON.parse(e.requests[1].options.body),{target});
 assert.equal(e.controller.canStartFresh(),false);
});
