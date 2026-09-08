/**
 * 공유용 단일 HTML 빌드.
 *
 * Next.js 앱과 같은 화면 코드(src/screens)를 그대로 번들해서
 * CSS·JS·로고를 전부 인라인한 HTML 파일 하나를 만든다.
 * 결과물은 서버 없이 더블클릭만으로 열린다.
 *
 * 실행: npm run build:single
 */

import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { build } from 'esbuild';

const root = path.resolve(import.meta.dirname, '..');
const tmp = path.join(root, '.single-tmp');
/** 찾기 쉽도록 TAEYUN 폴더 바로 아래에 떨어뜨린다. */
const outFile = path.resolve(root, '..', 'eureka-공유용.html');

fs.mkdirSync(tmp, { recursive: true });

/* 1. Tailwind CSS 컴파일 ------------------------------------------------ */

const cssIn = path.join(tmp, 'input.css');
const cssOut = path.join(tmp, 'out.css');

// globals.css를 그대로 쓰되, 스캔 대상을 명시해 클래스 누락을 막는다.
fs.writeFileSync(
  cssIn,
  `@import '${path.join(root, 'src/app/globals.css').replace(/\\/g, '/')}';\n` +
    `@source '${path.join(root, 'src').replace(/\\/g, '/')}';\n`,
  'utf8',
);

console.log('[1/4] Tailwind CSS 컴파일...');
execFileSync(
  process.execPath,
  [path.join(root, 'node_modules/@tailwindcss/cli/dist/index.mjs'), '-i', cssIn, '-o', cssOut, '--minify'],
  { cwd: root, stdio: 'inherit' },
);
const css = fs.readFileSync(cssOut, 'utf8');

/* 2. 화면 번들 ---------------------------------------------------------- */

console.log('[2/4] 화면 번들...');
const bundled = await build({
  entryPoints: [path.join(root, 'src/single/entry.tsx')],
  bundle: true,
  minify: true,
  format: 'iife',
  target: ['es2020'],
  // 기본값(ascii)은 한글을 유니코드 이스케이프로 바꿔 파일이 크게 불어난다.
  charset: 'utf8',
  jsx: 'automatic',
  write: false,
  define: { 'process.env.NODE_ENV': '"production"' },
  alias: { '@': path.join(root, 'src') },
  // 'use client'는 Next.js 전용 지시어라 여기서는 의미가 없다. 경고를 끈다.
  logOverride: { 'unsupported-jsx-comment': 'silent', 'ignored-bare-import': 'silent' },
  legalComments: 'none',
});
const js = bundled.outputFiles[0].text;

/* 3. 로고 인라인 -------------------------------------------------------- */

console.log('[3/4] 로고 인라인...');
const logo = fs.readFileSync(path.join(root, 'public/eureka.png'));
const logoDataUri = `data:image/png;base64,${logo.toString('base64')}`;

/* 4. HTML 조립 ---------------------------------------------------------- */

console.log('[4/4] HTML 조립...');
const html = `<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>유레카 — 문제를 발견하고, 아이디어로 바꾸다</title>
<!--
  팀 목욕중 · 유레카 MVP 프로토타입 (공유용 단일 파일)
  이 파일 하나로 전체 화면과 흐름을 볼 수 있습니다. 설치나 서버가 필요 없습니다.
  표시되는 문제·아이디어·수치는 흐름 확인용 가상 데이터입니다.
-->
<link rel="icon" href="${logoDataUri}" />
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css" />
<style>${css}</style>
</head>
<body>
<div id="root"></div>
<script>window.__EUREKA_LOGO__ = ${JSON.stringify(logoDataUri)};</script>
<script>${js}</script>
</body>
</html>
`;

fs.writeFileSync(outFile, html, 'utf8');
fs.rmSync(tmp, { recursive: true, force: true });

const kb = (Buffer.byteLength(html, 'utf8') / 1024).toFixed(0);
console.log(`\n완료: ${outFile}`);
console.log(`크기: ${kb}KB (CSS ${(css.length / 1024).toFixed(0)}KB · JS ${(js.length / 1024).toFixed(0)}KB · 로고 ${(logoDataUri.length / 1024).toFixed(0)}KB)`);
