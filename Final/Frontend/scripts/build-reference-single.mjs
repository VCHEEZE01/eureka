import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';

const pageNames = ['index.html', 'config.html', 'loading.html', 'result.html', 'detail.html'];

const args = process.argv.slice(2);
const options = {};
for (let i = 0; i < args.length; i += 2) {
  if (!['--data', '--mode', '--out', '--report'].includes(args[i]) || !args[i + 1]) throw new Error('사용법: --mode live 또는 --data problems.json --mode published|review [--out output.html] [--report review.report.json]');
  options[args[i]] = args[i + 1];
}
const mode = options['--mode'] || (options['--data'] ? 'published' : 'live');
if (!['live', 'published', 'review'].includes(mode) || (options['--data'] && !['published', 'review'].includes(mode)) || (!options['--data'] && ['published','review'].includes(mode))) throw new Error('live는 --data 없이, published/review는 --data와 함께 사용하세요.');
let problems = null;
if (options['--data']) {
  problems = JSON.parse(await readFile(path.resolve(options['--data']), 'utf8'));
  if (!Array.isArray(problems)) throw new Error('입력은 Problem[] JSON이어야 합니다.');
  const ids = new Set();
  for (const p of problems) {
    if (typeof p.id !== 'string' || ids.has(p.id) || !p.title || !p.signals || !p.gate || !Array.isArray(p.evidence) || !Number.isInteger(p.case_count) || !Number.isInteger(p.source_count)) throw new Error('유효한 고유 ID와 Problem 필드가 필요합니다.');
    ids.add(p.id);
    if (mode === 'published' && !p.gate.passed) throw new Error('게시 보류 데이터는 --mode review로만 열 수 있습니다.');
  }
}
const reviews = Object.create(null);
if (options['--report']) {
  if (mode !== 'review') throw new Error('--report는 --mode review에서만 사용할 수 있습니다.');
  const report = JSON.parse(await readFile(path.resolve(options['--report']), 'utf8'));
  if (!Array.isArray(report.results)) throw new Error('검수 보고서에 results 배열이 필요합니다.');
  const includedIds = new Set(problems.map(p => p.id));
  for (const result of report.results) {
    const id = result.problem?.id;
    if (!includedIds.has(id)) continue;
    if (reviews[id] || !['publish', 'hold', 'merge'].includes(result.review?.decision) || typeof result.review?.reason !== 'string') throw new Error('문제별 검수 결과가 유효하지 않거나 중복되었습니다.');
    reviews[id] = {decision: result.review.decision, reason: result.review.reason};
  }
}
const collectionRuntime = await readFile(path.resolve('reference-pages/collection-runtime.js'), 'utf8');
const labels = {live: '실제 타겟 탐색 · 이번 실행의 문제와 근거를 확인합니다', published: '실제 수집 데이터 · 게시 기준 통과', review: '실제 수집 데이터 · 게시 보류 검토용 (공개 목록 아님)'};
const pages = {};
for (const name of pageNames) {
  pages[name] = await readFile(path.resolve('reference-pages', name), 'utf8');
}

// JSON 안의 '<'를 이스케이프해 페이지 본문 속 </script>가 바깥 script를 닫지 않게 한다.
const packedPages = JSON.stringify(pages).replaceAll('<', '\\u003c');
const output = `<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>EUREKA</title>
<style>html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#fff}body{display:flex;flex-direction:column}iframe{display:block;width:100%;flex:1;min-height:0;border:0}.data-mode-label{flex-shrink:0;padding:9px 16px;background:#211a40;color:white;font:13px/1.5 sans-serif;text-align:center;word-break:keep-all}</style>
</head>
<body>
<iframe id="app" title="EUREKA"></iframe>
<div class="data-mode-label" role="status">${labels[mode]}</div>
<script id="pages" type="application/json">${packedPages}</script>
<script>
const pages = JSON.parse(document.getElementById('pages').textContent);
window.__dataMode = ${JSON.stringify(mode)};
window.__reviews = Object.fromEntries(${JSON.stringify(Object.entries(reviews)).replaceAll('<', '\\u003c')});
window.__problems = ${JSON.stringify(problems).replaceAll('<', '\\u003c')};
${collectionRuntime}
let depth = 0;
window.__navigate = function (target) {
  const url = new URL(target, 'https://eureka.local/');
  if (!pages[url.pathname.slice(1)] && !['idea.html','personalize.html','personalized-result.html','combination.html'].includes(url.pathname.slice(1))) return;
  depth += 1;
  history.pushState({depth}, '', '#' + url.pathname.slice(1) + url.search);
  setTimeout(render, 0);
};
function render() {
  const route = new URL(location.hash.slice(1) || 'index.html', 'https://eureka.local/');
  const requestedPage = route.pathname.slice(1);
  const waiting = window.__dataMode === 'live' && ['result.html','detail.html'].includes(requestedPage) && !window.__collections?.canView();
  window.__collectionDestination = waiting ? requestedPage + route.search : null;
  const locked = ['idea.html', 'personalize.html', 'personalized-result.html', 'combination.html'].includes(route.pathname.slice(1));
  const source = locked ? '<!doctype html><html lang="ko"><body><h1>준비 중인 기능입니다</h1><p>지금은 문제정의와 근거 확인까지 이용할 수 있습니다.</p></body></html>' : (pages[waiting ? 'loading.html' : route.pathname.slice(1)] || pages['index.html']);
  window.__search = route.search;
  window.__hasPrevious = depth > 0;
  const frame = document.createElement('iframe');
  frame.id = 'app';
  frame.title = 'EUREKA';
  document.getElementById('app').replaceWith(frame);
  const doc = frame.contentDocument;
  doc.open();
  doc.write(source);
  doc.close();
  document.title = doc.title || 'EUREKA';
}
history.replaceState({depth:0}, '', location.href);
window.addEventListener('popstate', function(event) {
  depth = event.state ? event.state.depth || 0 : 0;
  render();
});
render();
</script>
</body>
</html>
`;

const outputPath = path.resolve(options['--out'] || (mode === 'live' ? 'eureka-공유용.html' : 'eureka-실데이터.html'));
await writeFile(outputPath, output, 'utf8');
console.log(`완료: ${outputPath}`);
console.log(`페이지: ${pageNames.length}개 · 크기: ${Math.ceil(Buffer.byteLength(output) / 1024)}KB`);
