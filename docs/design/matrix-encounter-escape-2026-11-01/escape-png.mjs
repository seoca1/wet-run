import { readFile, writeFile, readdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { build } from '/Users/emilio/projects/opencodework/Game/wet_run/web/node_modules/esbuild/lib/main.js';
import { chromium } from '/Users/emilio/projects/opencodework/Game/wet_run/web/node_modules/playwright/index.mjs';

const phase = process.argv[2];
if (!['before', 'after', 'pairs'].includes(phase)) throw new Error('Specify before, after or pairs');
const dir = '/Users/emilio/projects/opencodework/Game/wet_run/docs/design/matrix-encounter-escape-2026-11-01';
const bundle = await build({ entryPoints: ['/Users/emilio/.openclaw/tmp/opencode/depart-harness.ts'], bundle: true, write: false, format: 'iife', globalName: 'EscQA' });
const script = bundle.outputFiles[0].text;
const receiptPath = `${dir}/capture-receipt.json`;
const receipt = existsSync(receiptPath) ? JSON.parse(await readFile(receiptPath, 'utf8')) : { renderer: 'Actual AsciiRenderer (web/src/renderer/canvas.ts) bundled with esbuild, 10x18 cells, DPR 1, system monospace fallback; renderRunScreen grids (renderMatrix / renderEncounterDecision) plus HUD column at the layout preset hudCols (24/20/16)', captures: [] };
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ deviceScaleFactor: 1 });
  if (phase !== 'pairs') {
    const stems = (await readdir(dir)).filter((f) => f.endsWith(`-${phase}.json`) && !f.startsWith("fixture")).map((f) => f.slice(0, -5)).sort();
    for (const stem of stems) {
      const grid = JSON.parse(await readFile(`${dir}/${stem}.json`, 'utf8'));
      const w = (grid.width + grid.hudCols) * 10, h = grid.height * 18;
      await page.setViewportSize({ width: w, height: h });
      await page.setContent('<body style="margin:0;background:#000"><canvas id="screen"></canvas></body>');
      await page.addScriptTag({ content: script });
      await page.evaluate((data) => EscQA.draw(data, 'screen'), grid);
      await page.screenshot({ path: `${dir}/${stem}.png` });
      receipt.captures = receipt.captures.filter((c) => c.file !== `${stem}.png`);
      receipt.captures.push({ file: `${stem}.png`, width: w, height: h, textRows: grid.cells.length, textCols: grid.width, hudCols: grid.hudCols, captured: new Date().toISOString() });
    }
    await writeFile(receiptPath, JSON.stringify(receipt, null, 2));
    console.log(`Captured ${stems.length} ${phase} frames`);
  } else {
    const names = ['gated-route', 'encounter', 'encounter-enter', 'encounter-probed-enter', 'post-bypass', 'post-bypass-route', 'stranded-route', 'stranded-depart', 'continue'];
    for (const name of names) for (const [cols, rows] of [[80, 50], [60, 40], [40, 60]]) {
      const stem = `${dir}/${name}-${cols}x${rows}`;
      const before = JSON.parse(await readFile(`${stem}-before.json`, 'utf8'));
      const after = JSON.parse(await readFile(`${stem}-after.json`, 'utf8'));
      const w = (cols + before.hudCols) * 10, h = rows * 18;
      await page.setViewportSize({ width: 2 * w + 24, height: h + 28 });
      await page.setContent(`<body style="margin:0;background:#000;color:#c0c0c0;font:14px monospace"><div style="display:grid;grid-template-columns:${w + 12}px ${w + 12}px"><div><div style="height:28px">BEFORE ${name} ${cols}x${rows}</div><canvas id="b"></canvas></div><div><div style="height:28px">AFTER ${name} ${cols}x${rows}</div><canvas id="a"></canvas></div></div></body>`);
      await page.addScriptTag({ content: script });
      await page.evaluate(({ before, after }) => { EscQA.draw(before, 'b'); EscQA.draw(after, 'a'); }, { before, after });
      await page.screenshot({ path: `${stem}-pair.png` });
    }
    console.log('pairs done');
  }
} finally {
  await browser.close();
}
