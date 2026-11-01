/** ADR-0250 follow-up: no state may trap the player at an ICE node.
 *
 * Owner report (after ADR-0250 shipped): "보드 + 'enter ICE' + 이벤트 반복".
 * Reproduced live: JACK OUT / ESC set `phase: "menu"` but left the run on the
 * board, and a node reached without an arrival (CONTINUE) gated every
 * departure, so every Enter reopened the encounter. Fixture: a line
 * 0 - 1 - 2 - 3 where node 1 is an ICE node with exactly two neighbours.
 */
import { describe, expect, it } from "vitest";
import {
  applyAction,
  makeInitialState,
  slotToGameState,
  stateToSaveSlot,
} from "../src/core/state/state";
import {
  ENCOUNTER_VERBS,
  openArrivalEncounter,
  runAbandoned,
} from "../src/core/state/encounter_verbs";
import { renderRunScreen } from "../src/renderer/run_screen";
import { PALETTE } from "../src/renderer/palette";
import { loadMissionsCatalog, loadProgramsCatalog } from "../src/core/data_loaders";
import missionsData from "../src/data/missions.json";
import programsData from "../src/data/programs.json";
import type { GameAction, GameState, Ice, Matrix, Program } from "../src/core/types";

const WATCHDOG: Ice = { id: "watchdog", name: "Watchdog", hp: 50, armor: 0, tier: 1 };
const STRIKE: Program = { id: "strike", name: "Strike", tier: 1, cost: 0, effect: "damage", description: "", aoe: false };
const LAYOUTS = [
  [80, 50],
  [60, 40],
  [40, 60],
] as const;

const MATRIX: Matrix = {
  startNode: 0,
  bossNode: 3,
  nodes: [
    { id: 0, zone: "surface", iceIds: [], iceHp: [], reward: { credits: 0 }, adjacent: [1], isBoss: false },
    { id: 1, zone: "mid", iceIds: ["watchdog"], iceHp: [1], reward: { credits: 75 }, adjacent: [0, 2], isBoss: false },
    { id: 2, zone: "mid", iceIds: [], iceHp: [], reward: { credits: 0 }, adjacent: [1, 3], isBoss: false },
    { id: 3, zone: "core", iceIds: ["watchdog"], iceHp: [1], reward: { credits: 0 }, adjacent: [2], isBoss: true },
  ],
};

function onStart(deck: readonly Program[] = [STRIKE]): GameState {
  const initial = makeInitialState(
    { id: "esc", title: "Esc", fixer: "test", zone: "surface", arc: 1, grade_min: 1, grade_max: 1, rewards: { credits: 0, materials: {} } },
    WATCHDOG,
    deck,
  );
  return { ...initial, runPhase: "matrix", phase: "approach", matrix: MATRIX, currentNodeIndex: 0, visitedNodes: [0] };
}

const act = (state: GameState, type: GameAction["type"]): GameState => applyAction(state, { type } as GameAction);

function target(state: GameState, to: number): GameState {
  let next = state;
  for (let i = 0; i < 4 && next.selectedMatrixNodeIndex !== to; i += 1) next = act(next, "move_south");
  expect(next.selectedMatrixNodeIndex).toBe(to);
  return next;
}

const travel = (state: GameState, to: number): GameState => act(target(state, to), "confirm");

function select(state: GameState, verb: string): GameState {
  let next = state;
  for (let i = 0; i < 6 && next.encounterDecision?.selectedVerb !== verb; i += 1) next = act(next, "move_south");
  expect(next.encounterDecision?.selectedVerb).toBe(verb);
  return next;
}

const choose = (state: GameState, verb: string): GameState => act(select(state, verb), "confirm");

/** On node 1 with nothing open: what HEAD left after ESC / JACK OUT or CONTINUE. */
const stranded = (): GameState => ({ ...travel(onStart(), 1), encounterDecision: null });

function text(state: GameState, cols: number, rows: number): string[] {
  const view = renderRunScreen(state, cols, rows);
  if (!view) throw new Error("no view");
  return view.grid.cells.map((row) => row.map((c) => c.char).join(""));
}

function footer(state: GameState, cols: number, rows: number): string {
  const grid = text(state, cols, rows);
  const bottom = grid.map((line) => line.includes("╚")).lastIndexOf(true);
  return grid[bottom - 1] ?? "";
}

describe("fix 1 — departing a node never reopens the decision", () => {
  it("leaves an unresolved node reached without an arrival, for either neighbour", () => {
    for (const to of [0, 2]) {
      // Given: standing on node 1, nothing open, a route highlighted.
      const armed = target(stranded(), to);
      // When
      const left = act(armed, "confirm");
      // Then
      expect(left.currentNodeIndex).toBe(to);
      expect(left.encounterDecision ?? null).toBeNull();
      expect(left.player.alarm).toBe(0);
    }
  });

  it("still enters the ICE you stand on when Enter is pressed with no route", () => {
    const opened = act(stranded(), "confirm");
    expect(opened.currentNodeIndex).toBe(1);
    expect(opened.encounterDecision).toEqual({ selectedVerb: null, probed: false });
  });

  it("keeps the arrival gate: walking onto unresolved ICE still opens the decision", () => {
    const arrived = travel(onStart(), 1);
    expect(arrived.currentNodeIndex).toBe(1);
    expect(arrived.encounterDecision).toEqual({ selectedVerb: null, probed: false });
  });

  it.each(LAYOUTS)("never promises 'enter ICE' on a departure the reducer lets through (%sx%s)", (cols, rows) => {
    const armed = target(stranded(), 0);
    expect(footer(armed, cols, rows)).toMatch(/ENTER:? travel/);
    expect(footer(armed, cols, rows)).not.toMatch(/ICE blocks travel|no travel/);
  });

  it.each(LAYOUTS)("the board footer says ESC jacks out, not 'back' (%sx%s)", (cols, rows) => {
    for (const state of [onStart(), target(onStart(), 1), stranded()]) {
      const line = footer(state, cols, rows);
      expect(line).toMatch(/ESC:? jack out/);
      expect(line).not.toMatch(/ESC:? back/);
    }
  });
});

describe("fix 1 — JACK OUT and ESC really leave the run", () => {
  it("flags the JACK OUT verb as an abandoned run", () => {
    const arrived = travel(onStart(), 1);
    const out = choose(arrived, "JACK OUT");
    expect(runAbandoned(arrived, out)).toBe(true);
  });

  it("flags ESC on the encounter and on the board as an abandoned run", () => {
    const arrived = travel(onStart(), 1);
    expect(runAbandoned(arrived, act(arrived, "jack_out"))).toBe(true);
    const board = onStart();
    expect(runAbandoned(board, act(board, "jack_out"))).toBe(true);
  });

  it("does not flag travel, verb changes, BYPASS or BREACH", () => {
    const start = onStart();
    const arrived = travel(start, 1);
    const pairs: Array<[GameState, GameState]> = [
      [start, target(start, 1)],
      [target(start, 1), arrived],
      [arrived, act(arrived, "move_south")],
      [arrived, act(arrived, "confirm")],
      [select(arrived, "BYPASS"), choose(arrived, "BYPASS")],
      [select(arrived, "BREACH"), choose(arrived, "BREACH")],
    ];
    for (const [before, after] of pairs) expect(runAbandoned(before, after)).toBe(false);
  });
});

describe("fix 1 — load and start count as an arrival (save-reload cannot dodge)", () => {
  const missions = loadMissionsCatalog(missionsData);
  const programs = loadProgramsCatalog(programsData);
  const mission = missions[0]!;
  const deck = Object.keys(programs).sort().slice(0, 5).map((id) => ({ ...programs[id]!, id }));
  const real = (): GameState => ({ ...makeInitialState(mission, WATCHDOG, deck), runPhase: "matrix", phase: "approach", currentNodeIndex: 0 });
  const iceNode = (): number => {
    const state = real();
    const index = state.matrix!.nodes[0]!.adjacent.find((i) => (state.matrix!.nodes[i]?.iceIds.length ?? 0) > 0);
    if (index === undefined) throw new Error("fixture: no ICE neighbour of the start node");
    return index;
  };

  it("CONTINUE onto an unresolved node opens the decision instead of the board", () => {
    // Given: autosave written mid-combat on the ICE node (combat not won).
    const x = iceNode();
    const combat = act(act(select(travel(real(), x), "BREACH"), "confirm"), "confirm");
    expect(combat.runPhase).toBe("combat");
    // When
    const restored = slotToGameState(stateToSaveSlot(combat), missions, programs, WATCHDOG);
    // Then
    expect(restored?.currentNodeIndex).toBe(x);
    expect(restored?.runPhase).toBe("matrix");
    expect(restored?.encounterDecision).toEqual({ selectedVerb: null, probed: false });
    expect(restored?.message).toContain("BREACH");
    expect(renderRunScreen(restored!, 80, 50)?.hud[0]).toBe("ENCOUNTER");
  });

  it("a save taken with the decision open restores it open: no input reaches a route", () => {
    const x = iceNode();
    const open = travel(real(), x);
    const restored = slotToGameState(stateToSaveSlot(open), missions, programs, WATCHDOG)!;
    // Arrows drive the verb cursor, never a route.
    for (const type of ["move_south", "move_north", "move_east", "move_west"] as const) {
      const moved = act(restored, type);
      expect(moved.encounterDecision?.selectedVerb).not.toBeNull();
      expect(moved.selectedMatrixNodeIndex ?? null).toBeNull();
    }
    // Enter with nothing selected neither moves nor closes it.
    const pressed = act(act(restored, "confirm"), "confirm");
    expect(pressed.currentNodeIndex).toBe(x);
    expect(pressed.encounterDecision).not.toBeNull();
    expect(pressed.player.alarm).toBe(0);
  });

  it("restoring onto a resolved node opens nothing", () => {
    const x = iceNode();
    const bypassed = choose(travel(real(), x), "BYPASS");
    const restored = slotToGameState(stateToSaveSlot(bypassed), missions, programs, WATCHDOG);
    expect(restored?.currentNodeIndex).toBe(x);
    expect(restored?.encounterDecision ?? null).toBeNull();
    const cleared = slotToGameState(
      { ...stateToSaveSlot(bypassed), bypassedEncounterNodes: [], clearedEncounterNodes: [x] },
      missions,
      programs,
      WATCHDOG,
    );
    expect(cleared?.encounterDecision ?? null).toBeNull();
  });

  it("an old save without the bypass list still restores onto its node and opens the ICE there", () => {
    const x = iceNode();
    const { bypassedEncounterNodes: _omitted, ...old } = stateToSaveSlot({ ...real(), currentNodeIndex: x });
    const restored = slotToGameState(old, missions, programs, WATCHDOG);
    expect(restored?.bypassedEncounterNodes).toEqual([]);
    expect(restored?.encounterDecision).toEqual({ selectedVerb: null, probed: false });
  });

  it("a run that starts on an unresolved ICE node opens the decision at once", () => {
    const started = openArrivalEncounter({ ...onStart(), currentNodeIndex: 1 });
    expect(started.encounterDecision).toEqual({ selectedVerb: null, probed: false });
    expect(started.message).toContain("JACK OUT");
    // An ICE-free start is left alone.
    const free = onStart();
    expect(openArrivalEncounter(free)).toBe(free);
  });
});

describe("fix 2 — SCAN with no utility in hand never swallows input", () => {
  it("is skipped in both arrow directions when no utility program is in hand", () => {
    const arrived = travel(onStart(), 1);
    for (const direction of ["move_south", "move_north", "move_east", "move_west"] as const) {
      let state = arrived;
      const seen: Array<string | null> = [];
      for (let i = 0; i < 10; i += 1) {
        state = act(state, direction);
        seen.push(state.encounterDecision?.selectedVerb ?? null);
      }
      expect(seen).not.toContain("SCAN");
      expect(new Set(seen)).toEqual(new Set(["PROBE", "BYPASS", "BREACH", "JACK OUT"]));
    }
  });

  it("keeps the fixed order of the remaining verbs (ADR-0246)", () => {
    let state = travel(onStart(), 1);
    const order: Array<string | null> = [];
    for (let i = 0; i < 4; i += 1) {
      state = act(state, "move_south");
      order.push(state.encounterDecision?.selectedVerb ?? null);
    }
    expect(order).toEqual(["PROBE", "BYPASS", "BREACH", "JACK OUT"]);
    expect(act(travel(onStart(), 1), "move_north").encounterDecision?.selectedVerb).toBe("JACK OUT");
  });

  it("stays reachable, last in the cycle, when a utility program is in hand", () => {
    const scan: Program = { ...STRIKE, id: "scan", name: "Scan" };
    const arrived = travel(onStart([STRIKE, scan]), 1);
    expect(act(arrived, "move_north").encounterDecision?.selectedVerb).toBe("SCAN");
  });

  it("says why if SCAN is somehow committed without a utility program", () => {
    const arrived = travel(onStart(), 1);
    const forced = { ...arrived, encounterDecision: { selectedVerb: "SCAN" as const, probed: false } };
    const result = act(forced, "confirm");
    expect(result.message).toMatch(/no utility program/i);
    expect(result.deck).toEqual(forced.deck);
  });

  it.each(LAYOUTS)("still lists SCAN and why it cannot be used (%sx%s)", (cols, rows) => {
    const joined = text(travel(onStart(), 1), cols, rows).join("\n");
    expect(joined).toContain("SCAN");
    expect(joined).toContain("NO UTILITY IN HAND");
  });
});

describe("fix 3 — Enter on the encounter is never silent", () => {
  it("with nothing selected, says plainly what to do and names the exits; nothing is paid or moved", () => {
    const arrived = travel(onStart(), 1);
    const pressed = act(arrived, "confirm");
    expect(pressed.message).not.toBe(arrived.message);
    expect(pressed.message).toMatch(/nothing selected/i);
    expect(pressed.message).toContain("↓");
    for (const exit of ["BYPASS", "BREACH", "JACK OUT"]) expect(pressed.message).toContain(exit);
    expect(pressed.encounterDecision).toEqual({ selectedVerb: null, probed: false });
    expect(pressed.currentNodeIndex).toBe(1);
    expect(pressed.player.alarm).toBe(0);
  });

  it.each(LAYOUTS)("the encounter screen itself tells a player with nothing selected to press ↓ (%sx%s)", (cols, rows) => {
    const joined = text(travel(onStart(), 1), cols, rows).join("\n");
    expect(joined).toMatch(/Nothing selected/);
  });

  it("Enter on an already-used PROBE says the threat is revealed and points at the exits", () => {
    const probed = choose(travel(onStart(), 1), "PROBE");
    expect(probed.player.alarm).toBe(8);
    const again = act(probed, "confirm");
    expect(again.message).not.toBe(probed.message);
    expect(again.message).toMatch(/already revealed/i);
    for (const exit of ["BYPASS", "BREACH", "JACK OUT"]) expect(again.message).toContain(exit);
    expect(again.player.alarm).toBe(8);
  });

  it("Enter on an already-revealed SCAN says so instead of doing nothing", () => {
    const scan: Program = { ...STRIKE, id: "scan", name: "Scan" };
    const probed = choose(travel(onStart([STRIKE, scan]), 1), "PROBE");
    const onScan = { ...probed, encounterDecision: { selectedVerb: "SCAN" as const, probed: true } };
    const again = act(onScan, "confirm");
    expect(again.message).toMatch(/already revealed/i);
    expect(again.deck).toEqual(onScan.deck);
  });

  it("every confirm on every selectable verb changes what the player sees", () => {
    const boss = travel(travel(choose(travel(onStart(), 1), "BYPASS"), 2), 3);
    const roots = [travel(onStart(), 1), choose(travel(onStart(), 1), "PROBE"), boss];
    const marked = (s: GameState): GameState => ({ ...s, message: "<previous>" });
    for (const root of roots) {
      for (const alarm of [0, 95]) {
        for (const verb of [null, ...ENCOUNTER_VERBS]) {
          const state = marked({
            ...root,
            player: { ...root.player, alarm },
            encounterDecision: { selectedVerb: verb, probed: root.encounterDecision?.probed ?? false },
          });
          const next = act(state, "confirm");
          const visible =
            next.message !== state.message ||
            next.encounterDecision !== state.encounterDecision ||
            next.runPhase !== state.runPhase ||
            next.phase !== state.phase;
          expect(visible, `${verb ?? "null"} at COST ${alarm}`).toBe(true);
        }
      }
    }
  });
});

describe("fix 4 — the three exits read as the ways off this node", () => {
  function verbRow(lines: string[], verb: string): { y: number; line: string } {
    const y = lines.findIndex((line) => new RegExp(`[> ] ${verb}\\b`).test(line) && !line.includes("EXITS"));
    expect(y, verb).toBeGreaterThanOrEqual(0);
    return { y, line: lines[y]! };
  }

  it.each(LAYOUTS)("tags BYPASS / BREACH / JACK OUT as EXIT and PROBE / SCAN as INFO (%sx%s)", (cols, rows) => {
    const lines = text(travel(onStart(), 1), cols, rows);
    for (const exit of ["BYPASS", "BREACH", "JACK OUT"]) expect(verbRow(lines, exit).line).toMatch(/\bEXIT\b/);
    for (const info of ["PROBE", "SCAN"]) {
      expect(verbRow(lines, info).line).toMatch(/\bINFO\b/);
      expect(verbRow(lines, info).line).not.toMatch(/\bEXIT\b/);
    }
    expect(lines.join("\n")).toMatch(/EXITS: BYPASS · BREACH · JACK OUT/);
  });

  it.each(LAYOUTS)("draws unselected exits in a colour the information verbs do not use (%sx%s)", (cols, rows) => {
    const state = travel(onStart(), 1);
    const view = renderRunScreen(state, cols, rows)!;
    const lines = view.grid.cells.map((row) => row.map((c) => c.char).join(""));
    const fgOf = (verb: string): string => {
      const { y, line } = verbRow(lines, verb);
      return view.grid.cells[y]![line.indexOf(verb)]!.fg;
    };
    const exits = new Set(["BYPASS", "BREACH", "JACK OUT"].map(fgOf));
    const infos = new Set(["PROBE", "SCAN"].map(fgOf));
    expect(exits.size).toBe(1);
    for (const colour of infos) expect(exits.has(colour)).toBe(false);
    expect([...exits][0]).toBe(PALETTE.CYAN_LIGHT);
  });

  it.each(LAYOUTS)("keeps costs, BLOCKED, the gate line and the controls, and names ESC (%sx%s)", (cols, rows) => {
    const blocked = { ...travel(onStart(), 1), player: { ...onStart().player, alarm: 95 } };
    const joined = text(blocked, cols, rows).join("\n");
    expect(joined).toContain("+8 COST BLOCKED");
    expect(joined).toContain("+60 COST BLOCKED");
    expect(joined.match(/ICE blocks travel until resolved/g) ?? []).toHaveLength(1);
    expect(joined).toContain("ENTER/SPACE: act");
    expect(joined).toMatch(/ESC: jack out/);
  });
});
