// Encounter-escape evidence: actual renderRunScreen output (renderMatrix /
// renderEncounterDecision grids + HUD lines) driven by the real reducer on the
// boot mission's node 1 (the owner's 2-neighbour ICE node, adjacent [0, 26]).
// Same method as matrix-entry-gate (gate-capture.ts lineage).
import { mkdirSync, writeFileSync } from 'node:fs';
import { applyAction, makeInitialState, slotToGameState, stateToSaveSlot } from '/Users/emilio/projects/opencodework/Game/wet_run/web/src/core/state/state.ts';
import { renderRunScreen } from '/Users/emilio/projects/opencodework/Game/wet_run/web/src/renderer/run_screen.ts';
import { loadIceCatalog, loadMissionsCatalog, loadProgramsCatalog } from '/Users/emilio/projects/opencodework/Game/wet_run/web/src/core/data_loaders.ts';
import missionsData from '/Users/emilio/projects/opencodework/Game/wet_run/web/src/data/missions.json';
import programsData from '/Users/emilio/projects/opencodework/Game/wet_run/web/src/data/programs.json';
import iceData from '/Users/emilio/projects/opencodework/Game/wet_run/web/src/data/ice_types.json';
import type { GameAction, GameState } from '/Users/emilio/projects/opencodework/Game/wet_run/web/src/core/types.ts';

const phase = process.argv[2];
if (phase !== 'before' && phase !== 'after') throw new Error('Specify before or after');
const out = '/Users/emilio/projects/opencodework/Game/wet_run/docs/design/matrix-encounter-escape-2026-11-01';
mkdirSync(out, { recursive: true });
const missions = loadMissionsCatalog(missionsData);
const programs = loadProgramsCatalog(programsData);
const ice = Object.values(loadIceCatalog(iceData))[0]!;
const mission = missions[0]!;
// main.ts loadDeck: first five program ids, sorted.
const deck = Object.keys(programs).sort().slice(0, 5).map((id) => ({ ...programs[id]!, id }));
const base: GameState = { ...makeInitialState(mission, ice, deck), runPhase: 'matrix', phase: 'approach', currentNodeIndex: 0 };
const X = 1;
const node = base.matrix!.nodes[X]!;
if (node.iceIds.length === 0 || node.adjacent.length !== 2) throw new Error('node 1 is not the 2-neighbour ICE node');
const [A, B] = node.adjacent as [number, number];
const act = (s: GameState, type: GameAction['type']) => applyAction(s, { type } as GameAction);
const target = (s: GameState, to: number) => {
  let t = s;
  for (let i = 0; i < 8 && t.selectedMatrixNodeIndex !== to; i += 1) t = act(t, 'move_south');
  if (t.selectedMatrixNodeIndex !== to) throw new Error(`cannot target ${to}`);
  return t;
};
const select = (s: GameState, v: string) => {
  let t = s;
  for (let i = 0; i < 6 && t.encounterDecision?.selectedVerb !== v; i += 1) t = act(t, 'move_south');
  if (t.encounterDecision?.selectedVerb !== v) throw new Error(`cannot select ${v}`);
  return t;
};
const shots: Record<string, GameState> = {};
shots['gated-route'] = target(base, X);
const encounter = act(shots['gated-route'], 'confirm');
shots['encounter'] = encounter;
shots['encounter-enter'] = act(encounter, 'confirm');
shots['encounter-probed-enter'] = act(act(select(encounter, 'PROBE'), 'confirm'), 'confirm');
shots['post-bypass'] = act(select(encounter, 'BYPASS'), 'confirm');
shots['post-bypass-route'] = target(shots['post-bypass'], B);
// Standing on the unresolved node with no decision open (HEAD: after ESC /
// JACK OUT, or CONTINUE), a route targeted, then Enter.
const stranded: GameState = { ...encounter, encounterDecision: null, message: 'Jacked out — run abandoned' };
shots['stranded-route'] = target(stranded, A);
shots['stranded-depart'] = act(shots['stranded-route'], 'confirm');
// CONTINUE: autosave written mid-combat on node 1, restored through slotToGameState.
const combat = act(act(select(encounter, 'BREACH'), 'confirm'), 'confirm');
const restored = slotToGameState(stateToSaveSlot(combat), missions, programs, ice);
if (!restored) throw new Error('restore failed');
shots['continue'] = restored;

const HUD: Record<string, number> = { '80x50': 24, '60x40': 20, '40x60': 16 };
for (const [name, state] of Object.entries(shots)) {
  for (const [cols, rows] of [[80, 50], [60, 40], [40, 60]] as const) {
    const view = renderRunScreen(state, cols, rows);
    if (!view) throw new Error(`no view for ${name}`);
    const stem = `${out}/${name}-${cols}x${rows}-${phase}`;
    writeFileSync(`${stem}.txt`, view.grid.cells.map((r) => r.map((c) => c.char).join('')).join('\n') + '\n');
    writeFileSync(`${stem}.hud.txt`, view.hud.join('\n') + '\n');
    writeFileSync(`${stem}.json`, JSON.stringify({ width: view.grid.width, height: view.grid.height, cells: view.grid.cells, hud: view.hud, hudCols: HUD[`${cols}x${rows}`] }));
  }
}
const s = (st: GameState) => ({
  phase: st.phase,
  runPhase: st.runPhase,
  current: st.currentNodeIndex,
  selected: st.selectedMatrixNodeIndex ?? null,
  cleared: st.clearedEncounterNodes ?? [],
  bypassed: st.bypassedEncounterNodes ?? [],
  alarm: st.player.alarm,
  decision: st.encounterDecision ?? null,
  message: st.message,
});
const summary = Object.fromEntries(Object.entries(shots).map(([k, st]) => [k, s(st)]));
writeFileSync(
  `${out}/fixture-${phase}.json`,
  JSON.stringify({ mission: mission.id, title: mission.title, node: X, adjacent: node.adjacent, iceIds: node.iceIds, deck: deck.map((p) => p.id), shots: summary }, null, 2),
);
console.log(JSON.stringify(summary, null, 1));
