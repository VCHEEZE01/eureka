import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';

const sourcePath = process.argv[2];
if (!sourcePath) {
  throw new Error('사용법: node scripts/import-reference-single.mjs <공유용 HTML 경로>');
}

const source = await readFile(sourcePath, 'utf8');
const match = source.match(
  /<script id="pages" type="application\/json">([\s\S]*?)<\/script>/,
);
if (!match) {
  throw new Error('pages JSON을 찾지 못했습니다. EUREKA 단일 HTML인지 확인하세요.');
}

const pages = JSON.parse(match[1]);
const expected = [
  'index.html',
  'config.html',
  'loading.html',
  'result.html',
  'detail.html',
  'idea.html',
  'personalize.html',
  'personalized-result.html',
  'combination.html',
];

for (const name of expected) {
  if (typeof pages[name] !== 'string') {
    throw new Error(`필수 페이지가 없습니다: ${name}`);
  }
}

const outDir = path.resolve('reference-pages');
await mkdir(outDir, { recursive: true });
for (const name of expected) {
  await writeFile(path.join(outDir, name), pages[name], 'utf8');
}

console.log(`가져오기 완료: ${expected.length}개 페이지 → ${outDir}`);
