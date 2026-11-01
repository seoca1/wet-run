// Live keypress traces against the running preview (http://127.0.0.1:5195).
// Usage: node escape-live.mjs <before|after>
// Every keypress is logged with the reducer state it produced; the canvas is
// saved at the moments the owner described. Each scenario gets a fresh
// browser context (fresh localStorage / IndexedDB).
import { mkdirSync, writeFileSync } from 'node:fs';
import { chromium } from '/Users/emilio/projects/opencodework/Game/wet_run/web/node_modules/playwright/index.mjs';

const phase = process.argv[2];
if (phase !== 'before' && phase !== 'after') throw new Error('before|after');
const base = 'http://127.0.0.1:5195/';
const out = '/Users/emilio/projects/opencodework/Game/wet_run/docs/design/matrix-encounter-escape-2026-11-01/live';
mkdirSync(out, { recursive: true });

const snap = () => {
  const g = window.wetrun;
  const s = g?.state;
  if (!s) return { screen: g?.getScreen?.(), state: null };
  const node = s.matrix?.nodes[s.currentNodeIndex];
  return {
    screen: g.getScreen(),
    runPhase: s.runPhase,
    phase: s.phase,
    cur: s.currentNodeIndex,
    sel: s.selectedMatrixNodeIndex ?? null,
    ice: node?.iceIds.length ?? null,
    adjacent: node?.adjacent ?? null,
    decision: s.encounterDecision ? (s.encounterDecision.selectedVerb ?? 'open') : null,
    probed: s.encounterDecision?.probed ?? null,
    cost: s.player.alarm,
    cleared: s.clearedEncounterNodes ?? [],
    bypassed: s.bypassedEncounterNodes ?? [],
    msg: s.message,
  };
};

const browser = await chromium.launch({ headless: true });
const result = { phase, base, scenarios: {} };
try {
  const scenario = async (name, body) => {
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
    const page = await context.newPage();
    const trace = [];
    const log = async (key, note) => {
      await page.waitForTimeout(250);
      const s = await page.evaluate(snap);
      trace.push({ key, ...(note ? { note } : {}), ...s });
      return s;
    };
    const press = async (key, note) => {
      await page.keyboard.press(key);
      return log(key, note);
    };
    const shot = async (label) => {
      await page.waitForTimeout(150);
      const file = `${phase}-${name}-${label}.png`;
      await page.locator('canvas').first().screenshot({ path: `${out}/${file}` });
      trace.push({ shot: file });
    };
    await page.goto(base);
    await page.evaluate(() => {
      localStorage.clear();
      localStorage.setItem('wetrun_tutorial_completed', 'true');
      localStorage.setItem('wetrun_reduced_motion', '1');
    });
    await page.evaluate(() => new Promise((r) => { const q = indexedDB.deleteDatabase('wetrun_save_v1'); q.onsuccess = q.onerror = q.onblocked = () => r(); }));
    await page.goto(base);
    await page.waitForFunction(() => window.wetrun !== undefined);
    await page.waitForTimeout(500);
    await page.locator('canvas').first().focus();
    for (let i = 0; i < 8 && (await page.evaluate(() => window.wetrun.getScreen())) !== 'mission_select'; i++) await press('Enter', 'menu');
    for (let i = 0; i < 8 && (await page.evaluate(() => window.wetrun.state?.runPhase)) !== 'matrix'; i++) await press('Enter', 'launch');
    await log('-', 'run started');
    const arriveAtOne = async () => {
      for (let i = 0; i < 6 && (await page.evaluate(() => window.wetrun.state.selectedMatrixNodeIndex)) !== 1; i++) await press('ArrowDown', 'target node 1');
      return press('Enter', 'travel to node 1');
    };
    try {
      await body({ page, press, log, shot, arriveAtOne });
    } catch (e) {
      trace.push({ error: String(e) });
    }
    result.scenarios[name] = trace;
    await context.close();
  };

  // T: the owner-style "just press keys" trace on node 1 (mirrors the lead's).
  await scenario('keys', async ({ press, shot, arriveAtOne }) => {
    await arriveAtOne();
    await shot('arrival');
    await press('Enter', 'confirm, nothing chosen');
    await press('ArrowDown');
    await press('Enter', 'confirm first verb reached by Down');
    await press('Enter', 'confirm again');
    await press('ArrowLeft');
    await press('Enter', 'confirm verb reached by Left');
    await press('ArrowDown');
    await press('Enter');
    await press('ArrowDown');
    await press('Enter');
    await shot('end');
  });

  // (a) BYPASS on node 1, then the board and a departure.
  await scenario('a-bypass', async ({ page, press, shot, arriveAtOne }) => {
    await arriveAtOne();
    for (let i = 0; i < 6 && (await page.evaluate(() => window.wetrun.state.encounterDecision?.selectedVerb)) !== 'BYPASS'; i++) await press('ArrowDown', 'seek BYPASS');
    await press('Enter', 'commit BYPASS');
    await shot('post-bypass-board');
    await press('Enter', 'Enter at rest after BYPASS');
    await press('ArrowDown', 'target a route');
    await shot('post-bypass-route');
    await press('Enter', 'depart');
    await shot('departed');
  });

  // (b) CONTINUE onto an unresolved node: BREACH starts combat (autosave), reload, CONTINUE.
  await scenario('b-continue', async ({ page, press, log, shot, arriveAtOne }) => {
    await arriveAtOne();
    for (let i = 0; i < 6 && (await page.evaluate(() => window.wetrun.state.encounterDecision?.selectedVerb)) !== 'BREACH'; i++) await press('ArrowDown', 'seek BREACH');
    await press('Enter', 'commit BREACH');
    for (let i = 0; i < 4 && (await page.evaluate(() => window.wetrun.getPhase())) !== 'combat'; i++) await press('Enter', 'engage');
    await page.waitForTimeout(2500); // autosave (fire-and-forget IDB write on draw)
    await log('-', 'in combat, autosaved; reloading');
    await page.reload();
    await page.waitForFunction(() => window.wetrun !== undefined);
    await page.waitForTimeout(1000);
    await page.locator('canvas').first().focus();
    const nav = await page.evaluate(() => ({ idx: window.wetrun.getMenuOptionKeys().indexOf('continue'), cur: window.wetrun.getSelectedMenuIndex(), len: window.wetrun.getMenuOptionKeys().length }));
    for (let i = 0; i < (nav.idx - nav.cur + nav.len) % nav.len; i++) await press('ArrowDown', 'menu → CONTINUE');
    await press('Enter', 'CONTINUE');
    await page.waitForTimeout(500);
    await log('-', 'restored');
    await shot('restored');
    await press('ArrowDown', 'target a route');
    await shot('restored-route');
    await press('Enter', 'depart attempt 1');
    await shot('after-enter-1');
    await press('Escape', 'ESC (footer says ESC: back)');
    await shot('after-esc-1');
    await press('ArrowDown', 'target a route');
    await press('Enter', 'depart attempt 2');
    await press('Escape', 'ESC');
    await press('ArrowDown', 'target a route');
    await press('Enter', 'depart attempt 3');
    await shot('after-enter-3');
  });

  // (c) In-session: arrival opens the encounter; ESC; Enter; repeat.
  await scenario('c-escape', async ({ press, shot, arriveAtOne }) => {
    await arriveAtOne();
    await shot('arrival');
    await press('Escape', 'ESC on encounter');
    await shot('after-esc');
    await press('ArrowDown', 'pick left/right route');
    await shot('route');
    await press('Enter', 'travel attempt');
    await shot('after-enter');
    await press('Escape', 'ESC');
    await press('ArrowUp', 'pick the other route');
    await press('Enter', 'travel attempt');
  });

  // (d) JACK OUT committed from the encounter list.
  await scenario('d-jackout', async ({ page, press, shot, arriveAtOne }) => {
    await arriveAtOne();
    for (let i = 0; i < 6 && (await page.evaluate(() => window.wetrun.state.encounterDecision?.selectedVerb)) !== 'JACK OUT'; i++) await press('ArrowDown', 'seek JACK OUT');
    await press('Enter', 'commit JACK OUT');
    await shot('after-jackout');
    await press('Enter', 'Enter');
    await shot('after-enter');
  });
} finally {
  await browser.close();
}
writeFileSync(`${out}/${phase}-trace.json`, JSON.stringify(result, null, 1));
for (const [name, trace] of Object.entries(result.scenarios)) {
  console.log(`\n## ${name}`);
  for (const t of trace) {
    if (t.shot) { console.log(`   [shot ${t.shot}]`); continue; }
    if (t.error) { console.log(`   ERROR ${t.error}`); continue; }
    console.log(`${String(t.key).padEnd(10)} ${String(t.note ?? '').padEnd(34)} scr=${t.screen} rp=${t.runPhase} ph=${t.phase} cur=${t.cur} sel=${t.sel} ice=${t.ice} adj=${JSON.stringify(t.adjacent)} dec=${t.decision} probed=${t.probed} cost=${t.cost} clr=${JSON.stringify(t.cleared)} byp=${JSON.stringify(t.bypassed)} | ${t.msg}`);
  }
}
