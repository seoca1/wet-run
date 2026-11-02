// Run-end evidence: actual renderRunScreen / renderPreGameScreen output (grid
// + HUD column) driven by the real reducer on the boot mission's owner route
// (0 -> 25 -> 16 -> 18 ICE -> 20 boss). Same method as the matrix slices
// (escape-capture.ts lineage).
//
// Usage: npx tsx run-end-capture.mts <before|after>
//   before = sources of HEAD 30d6562a (detached worktree), after = working tree.
import { mkdirSync, writeFileSync } from 'node:fs';

const phase = process.argv[2];
if (phase !== 'before' && phase !== 'after') throw new Error('Specify before or after');
const ROOT =
  phase === 'before'
    ? '/Users/emilio/.openclaw/tmp/opencode/runend/head/web/src'
    : '/Users/emilio/projects/opencodework/Game/wet_run/web/src';
const out = '/Users/emilio/projects/opencodework/Game/wet_run/docs/design/run-end-and-save-2026-11-02';
mkdirSync(out, { recursive: true });

const { applyAction, makeInitialState } = await import(`${ROOT}/core/state/state.ts`);
const { openArrivalEncounter } = await import(`${ROOT}/core/state/encounter_verbs.ts`);
const { renderRunScreen } = await import(`${ROOT}/renderer/run_screen.ts`);
const { renderPreGameScreen } = await import(`${ROOT}/renderer/pre_game_screen.ts`);
const { MENU_OPTIONS } = await import(`${ROOT}/renderer/menu.ts`);
const { loadIceCatalog, loadMissionsCatalog, loadProgramsCatalog } = await import(`${ROOT}/core/data_loaders.ts`);
const missionsData = (await import(`${ROOT}/data/missions.json`, { with: { type: 'json' } })).default;
const programsData = (await import(`${ROOT}/data/programs.json`, { with: { type: 'json' } })).default;
const iceData = (await import(`${ROOT}/data/ice_types.json`, { with: { type: 'json' } })).default;
// The completion message only exists after the change.
const RUN_COMPLETE_MESSAGE: string =
  phase === 'after' ? (await import(`${ROOT}/core/state/run_end.ts`)).RUN_COMPLETE_MESSAGE : '';

type S = any; // evidence script: the two trees' GameState types are not shared
const missions = loadMissionsCatalog(missionsData);
const programs = loadProgramsCatalog(programsData);
const ice = Object.values(loadIceCatalog(iceData))[0];
const mission = missions[0];
const deck = Object.keys(programs).sort().slice(0, 5).map((id) => ({ ...programs[id], id }));
const key = (s: S, type: string): S => applyAction(s, { type });
const travel = (s: S, to: number): S => {
  let t = s;
  for (let i = 0; i < 8 && t.selectedMatrixNodeIndex !== to; i += 1) t = key(t, 'move_south');
  if (t.selectedMatrixNodeIndex !== to) throw new Error(`cannot target ${to}`);
  return key(t, 'confirm');
};
const choose = (s: S, verb: string): S => {
  let t = s;
  for (let i = 0; i < 6 && t.encounterDecision?.selectedVerb !== verb; i += 1) t = key(t, 'move_south');
  return key(t, 'confirm');
};
const win = (s: S): S => {
  let t = key(choose(s, 'BREACH'), 'confirm');
  for (let i = 0; i < 40 && t.runPhase === 'combat'; i += 1) {
    t = { ...t, iceRoster: t.iceRoster.map((x: S) => ({ ...x, hp: Math.min(x.hp, 1) })) };
    t = applyAction(t, { type: 'use_program', programId: t.deck[0].id });
  }
  if (t.runPhase !== 'loot') throw new Error('no win');
  return t;
};
let s: S = openArrivalEncounter({ ...makeInitialState(mission, ice, deck), currentNodeIndex: 0, runPhase: 'matrix', phase: 'approach' });
for (const to of [25, 16, 18]) s = travel(s, to);
s = key(win(s), 'confirm');
s = win(travel(s, 20));
const ending = key(s, 'confirm');
const confirmed = key(ending, 'confirm'); // HEAD: still the ending; after: the controller shows the title

const continueIndex = MENU_OPTIONS.findIndex((o: S) => o.key === 'continue');
type View = { grid: S; hud: string[] };
function menuOf(menuIndex: number, hasSave: boolean, message: string, cols: number, rows: number): View {
  return renderPreGameScreen(
    {
      screen: 'menu',
      menuIndex,
      missionIndex: 0,
      missionRows: [],
      farGridMissions: [],
      hasSave,
      saveMeta: hasSave ? { missionId: mission.id, turnCount: 8, savedAt: '2026-11-02T00:00:00.000Z' } : null,
      message,
      farGridUnlocked: false,
      language: 'en',
    } as S,
    cols,
    rows,
  );
}
const shots: Record<string, (cols: number, rows: number) => View> = {
  // The ending screen itself (footer).
  ending: (c, r) => renderRunScreen(ending, c, r),
  // Enter on the ending. HEAD: the reducer leaves runPhase "ending" and the
  // controller keeps drawing it. After: runCompleted -> title, slot retired.
  'ending-confirm': (c, r) =>
    phase === 'before' ? renderRunScreen(confirmed, c, r) : menuOf(0, false, RUN_COMPLETE_MESSAGE, c, r),
  // Title after a reload, CONTINUE selected. HEAD: the stale slot (boss
  // unresolved, turn 9) is offered. After: the slot was retired.
  'continue-after-run': (c, r) => menuOf(continueIndex, phase === 'before', '', c, r),
};

const HUD: Record<string, number> = { '80x50': 24, '60x40': 20, '40x60': 16 };
for (const [name, render] of Object.entries(shots)) {
  for (const [cols, rows] of [[80, 50], [60, 40], [40, 60]] as const) {
    const view = render(cols, rows);
    if (!view) throw new Error(`no view for ${name}`);
    const stem = `${out}/${name}-${cols}x${rows}-${phase}`;
    writeFileSync(`${stem}.txt`, view.grid.cells.map((r: S) => r.map((c: S) => c.char).join('')).join('\n') + '\n');
    writeFileSync(`${stem}.hud.txt`, view.hud.join('\n') + '\n');
    writeFileSync(`${stem}.json`, JSON.stringify({ width: view.grid.width, height: view.grid.height, cells: view.grid.cells, hud: view.hud, hudCols: HUD[`${cols}x${rows}`] }));
  }
}
const summary = (st: S) => ({ runPhase: st.runPhase, phase: st.phase, node: st.currentNodeIndex, cleared: st.clearedEncounterNodes, hp: st.player.hp, credits: st.player.credits, ending: st.endingChoice, message: st.message });
writeFileSync(
  `${out}/fixture-${phase}.json`,
  JSON.stringify({ mission: mission.id, route: [0, 25, 16, 18, 20], deck: deck.map((p: S) => p.id), ending: summary(ending), afterEndingConfirm: summary(confirmed), continueIndex, runCompleteMessage: RUN_COMPLETE_MESSAGE }, null, 2),
);
console.log(JSON.stringify({ ending: summary(ending), confirmed: summary(confirmed) }, null, 1));
