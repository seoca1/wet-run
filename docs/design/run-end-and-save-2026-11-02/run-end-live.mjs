// Live keypress trace of the owner's path against the running preview
// (http://127.0.0.1:5195): kill the boss -> ending -> reload -> CONTINUE.
// Usage: node run-end-live.mjs <before|after> [baseUrl] [outputTag]
//
// Every input is a real key (Enter / arrows / digits / Escape / page reload).
// After every logged key the trace records the live reducer state AND the
// decoded autosave slot (IndexedDB `wetrun_save_v1` / `slots` / `slot_0`),
// so "what the save holds" is read, not inferred. Fresh browser context.
import { mkdirSync, writeFileSync } from 'node:fs';
import { chromium } from '/Users/emilio/projects/opencodework/Game/wet_run/web/node_modules/playwright/index.mjs';
import LZString from '/Users/emilio/projects/opencodework/Game/wet_run/web/node_modules/lz-string/libs/lz-string.js';

const phase = process.argv[2];
if (phase !== 'before' && phase !== 'after') throw new Error('before|after');
const base = process.argv[3] ?? 'http://127.0.0.1:5195/';
const tag = process.argv[4] ?? phase; // output stem; screenshots use it too
const out = '/Users/emilio/projects/opencodework/Game/wet_run/docs/design/run-end-and-save-2026-11-02/live';
mkdirSync(out, { recursive: true });
// Aleph Fragment (boot mission): 0 -> 25 -> 16 -> 18 (ICE) -> 20 (boss, only exit 18).
const ROUTE = [25, 16, 18, 20];

const snap = () => {
  const g = window.wetrun;
  const s = g?.state;
  if (!s) return { screen: g?.getScreen?.(), state: null };
  return {
    screen: g.getScreen(),
    runPhase: s.runPhase,
    phase: s.phase,
    cur: s.currentNodeIndex,
    decision: s.encounterDecision ? (s.encounterDecision.selectedVerb ?? 'open') : null,
    hp: s.player.hp,
    credits: s.player.credits,
    cost: s.player.alarm,
    cleared: s.clearedEncounterNodes ?? [],
    roster: s.runPhase === 'combat' || s.runPhase === 'loot' ? s.iceRoster.map((i) => `${i.id}:${i.hp}/${i.maxHp ?? '?'}`) : [],
    ending: s.endingChoice,
    msg: s.message,
  };
};

const readSlotRaw = () =>
  new Promise((resolve) => {
    const req = indexedDB.open('wetrun_save_v1');
    req.onsuccess = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains('slots')) { db.close(); resolve(null); return; }
      const get = db.transaction('slots', 'readonly').objectStore('slots').get('slot_0');
      get.onsuccess = () => { db.close(); resolve(get.result ?? null); };
      get.onerror = () => { db.close(); resolve(null); };
    };
    req.onerror = () => resolve(null);
  });

function decodeSlot(raw) {
  if (raw === null || raw === undefined) return null;
  const text = typeof raw === 'string' ? raw : (raw.json ?? raw.data ?? JSON.stringify(raw));
  const env = JSON.parse(text);
  const json = env.v === 2 ? (env.c ? LZString.decompressFromEncodedURIComponent(env.d) : env.d) : text;
  const s = JSON.parse(json);
  return { node: s.currentNodeIndex, cleared: s.clearedEncounterNodes ?? [], hp: s.playerHp, credits: s.playerCredits, turn: s.turnCount };
}

const browser = await chromium.launch({ headless: true });
const trace = [];
const scenario = async (name, mode) => {
  trace.push({ note: `=== scenario ${name} ===` });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
  const page = await context.newPage();
  const log = async (key, note) => {
    await page.waitForTimeout(350); // > fire-and-forget IDB write
    const s = await page.evaluate(snap);
    const slot = decodeSlot(await page.evaluate(readSlotRaw));
    const row = { key, ...(note ? { note } : {}), ...s, slot };
    trace.push(row);
    return row;
  };
  const press = async (key, note) => {
    await page.keyboard.press(key);
    return log(key, note);
  };
  const shot = async (label) => {
    await page.waitForTimeout(150);
    const file = `${tag}-${name}-${label}.png`;
    await page.locator('canvas').first().screenshot({ path: `${out}/${file}` });
    trace.push({ shot: file });
  };
  const state = () => page.evaluate(() => window.wetrun.state);
  const verb = async (want) => {
    for (let i = 0; i < 6 && (await page.evaluate(() => window.wetrun.state?.encounterDecision?.selectedVerb)) !== want; i++) await press('ArrowDown', `seek ${want}`);
    return press('Enter', `commit ${want}`);
  };
  // Fight with digit keys only: play the first hand row that the reducer accepts.
  const fight = async () => {
    for (let i = 0; i < 6 && (await page.evaluate(() => window.wetrun.getPhase())) !== 'combat'; i++) await press('Enter', 'engage');
    for (let turn = 0; turn < 80; turn++) {
      const s = await state();
      if (!s || s.runPhase !== 'combat' || s.phase !== 'combat') break;
      let played = false;
      for (let row = 1; row <= Math.min(9, s.deck.length) && !played; row++) {
        const before = await page.evaluate(() => window.wetrun.state.deck.length + ':' + window.wetrun.state.turnCount);
        await page.keyboard.press(String(row));
        await page.waitForTimeout(60);
        const after = await page.evaluate(() => (window.wetrun.state ? window.wetrun.state.deck.length + ':' + window.wetrun.state.turnCount : 'null'));
        if (after !== before) played = true;
      }
      const r = await log('digit', played ? `turn ${turn + 1}` : 'no playable row');
      if (!played) break;
      if (r.runPhase !== 'combat') break;
    }
  };
  const reloadAndContinue = async () => {
    await page.waitForTimeout(1500);
    await log('-', 'settled; reloading');
    await page.reload();
    await page.waitForFunction(() => window.wetrun !== undefined);
    await page.waitForTimeout(1200);
    await page.locator('canvas').first().focus();
    await log('-', 'after reload (menu)');
    trace.push({ note: `menu hasSaveCache=${await page.evaluate(() => window.wetrun.hasSaveCache)}` });
    await shot('menu-after-reload');
    const nav = await page.evaluate(() => ({ idx: window.wetrun.getMenuOptionKeys().indexOf('continue'), cur: window.wetrun.getSelectedMenuIndex(), len: window.wetrun.getMenuOptionKeys().length }));
    for (let i = 0; i < (nav.idx - nav.cur + nav.len) % nav.len; i++) await press('ArrowDown', 'menu -> CONTINUE');
    await shot('menu-continue-selected');
    await press('Enter', 'CONTINUE');
    await page.waitForTimeout(600);
    const restored = await log('-', 'after CONTINUE');
    await shot('after-continue');
    return restored;
  };
  try {
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
    await log('-', 'run started on node 0');

    for (const to of ROUTE) {
      for (let i = 0; i < 8 && (await page.evaluate(() => window.wetrun.state.selectedMatrixNodeIndex)) !== to; i++) await press('ArrowDown', `target ${to}`);
      const arrived = await press('Enter', `travel to ${to} (committed move)`);
      if (arrived.decision !== null) {
        await verb('BREACH');
        if (mode === 'fight' && to === 20) {
          // Reload in the middle of the boss fight: engage, play one row.
          for (let i = 0; i < 6 && (await page.evaluate(() => window.wetrun.getPhase())) !== 'combat'; i++) await press('Enter', 'engage');
          await press('1', 'one program, boss still standing');
          await shot('boss-mid-fight');
          break;
        }
        await fight();
        const s = await log('-', `fight at ${to} over`);
        if (s.runPhase !== 'loot') throw new Error(`lost or stuck at ${to}: ${s.runPhase}/${s.phase}`);
        if (to === 20) await shot('boss-loot');
        if (to !== 20) await press('Enter', 'loot -> route selection');
      }
    }
    let restored;
    if (mode !== 'owner') {
      restored = await reloadAndContinue();
    } else {
      await press('Enter', 'loot confirm at the boss -> ending');
      await shot('ending');
      await press('Enter', 'Enter on the ending');
      await shot('after-ending-enter');
      await press('Enter', 'Enter again');
      await press('Escape', 'Esc');
      await shot('after-ending-esc');
      restored = await reloadAndContinue();
    }
    if (restored.runPhase === 'loot') {
      await press('Enter', 'Enter on the restored loot screen');
      await shot('restored-loot-enter');
      await press('Enter', 'Enter on the ending');
      await shot('restored-ending-enter');
    }
    if (restored.runPhase === 'matrix' && restored.decision !== null) {
      await verb('BYPASS');
      await shot('bypass-at-boss');
      await verb('BREACH');
      for (let i = 0; i < 6 && (await page.evaluate(() => window.wetrun.getPhase())) !== 'combat'; i++) await press('Enter', 'engage');
      await log('-', 'forced re-fight: roster at engage');
      await shot('forced-refight');
    }
  } catch (e) {
    trace.push({ error: String(e) });
  } finally {
    await context.close();
  }
};
try {
  await scenario('owner', 'owner');
  await scenario('boss-loot-reload', 'loot');
  await scenario('boss-fight-reload', 'fight');
} finally {
  await browser.close();
}
writeFileSync(`${out}/${tag}-trace.json`, JSON.stringify({ phase, base, trace }, null, 1));
const lines = [];
for (const t of trace) {
  if (t.shot) { lines.push(`   [shot ${t.shot}]`); continue; }
  if (t.error) { lines.push(`   ERROR ${t.error}`); continue; }
  if (!('key' in t)) { lines.push(`   # ${t.note}`); continue; }
  const st = t.runPhase === undefined ? `scr=${t.screen} state=null` : `scr=${t.screen} rp=${t.runPhase} ph=${t.phase} cur=${t.cur} dec=${t.decision} hp=${t.hp} cr=${t.credits} cost=${t.cost} clr=${JSON.stringify(t.cleared)} roster=${JSON.stringify(t.roster)} end=${t.ending}`;
  const sl = t.slot ? `SLOT{node=${t.slot.node} clr=${JSON.stringify(t.slot.cleared)} hp=${t.slot.hp} cr=${t.slot.credits} turn=${t.slot.turn}}` : 'SLOT{none}';
  lines.push(`${String(t.key).padEnd(7)} ${String(t.note ?? '').padEnd(36)} ${st} | ${sl} | ${t.msg ?? ''}`);
}
writeFileSync(`${out}/${tag}-trace.txt`, lines.join('\n') + '\n');
console.log(lines.join('\n'));
