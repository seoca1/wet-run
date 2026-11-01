/** ADR-0250: the ICE encounter gate sits on the entry, not the exit.
 *
 * Arriving on an unresolved ICE node opens the decision in the same action
 * that commits the move; nodes resolved by combat or BYPASS are remembered for
 * the run, so departing from them is free. Fixture: a line 0 - 1 - 2 - 3 where
 * node 1 is the owner's case (an ICE node with exactly two neighbours).
 */
import { describe, expect, it } from "vitest";
import {
  applyAction,
  makeInitialState,
  slotToGameState,
  stateToSaveSlot,
} from "../src/core/state/state";
import { renderRunScreen } from "../src/renderer/run_screen";
import { beginMatrixTravel } from "../src/renderer/matrix_travel";
import { load, save } from "../src/save/storage";
import { loadMissionsCatalog, loadProgramsCatalog } from "../src/core/data_loaders";
import missionsData from "../src/data/missions.json";
import programsData from "../src/data/programs.json";
import type { GameAction, GameState, Ice, Matrix } from "../src/core/types";

const WATCHDOG: Ice = { id: "watchdog", name: "Watchdog", hp: 50, armor: 0, tier: 1 };
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

function onStart(): GameState {
  const initial = makeInitialState(
    {
      id: "gate",
      title: "Gate",
      fixer: "test",
      zone: "surface",
      arc: 1,
      grade_min: 1,
      grade_max: 1,
      rewards: { credits: 0, materials: {} },
    },
    WATCHDOG,
    [{ id: "strike", name: "Strike", tier: 1, cost: 0, effect: "damage", description: "", aoe: false }],
  );
  return { ...initial, runPhase: "matrix", matrix: MATRIX, currentNodeIndex: 0, visitedNodes: [0] };
}

const act = (state: GameState, type: GameAction["type"]): GameState =>
  applyAction(state, { type } as GameAction);

/** Real arrows until `to` is the highlighted route. */
function target(state: GameState, to: number): GameState {
  let next = state;
  for (let i = 0; i < 4 && next.selectedMatrixNodeIndex !== to; i += 1) next = act(next, "move_south");
  expect(next.selectedMatrixNodeIndex).toBe(to);
  return next;
}

const travel = (state: GameState, to: number): GameState => act(target(state, to), "confirm");

/** Real arrows + confirm on an open decision. */
function choose(state: GameState, verb: string): GameState {
  let next = state;
  for (let i = 0; i < 5 && next.encounterDecision?.selectedVerb !== verb; i += 1) next = act(next, "move_south");
  expect(next.encounterDecision?.selectedVerb).toBe(verb);
  return act(next, "confirm");
}

function rows(state: GameState, cols: number, height: number): { grid: string[]; hud: readonly string[] } {
  const view = renderRunScreen(state, cols, height);
  if (!view) throw new Error("no view");
  return { grid: view.grid.cells.map((row) => row.map((c) => c.char).join("")), hud: view.hud };
}

/** The controls footer: the last inner row of the matrix frame. */
function footer(state: GameState, cols: number, height: number): string {
  const grid = rows(state, cols, height).grid;
  const bottom = grid.map((line) => line.includes("╚")).lastIndexOf(true);
  return grid[bottom - 1] ?? "";
}

const CLAIMS_TRAVEL = /ENTER:? travel/;

describe("ADR-0250 decision 1 — the gate is on the entry", () => {
  it("opens the decision in the same action that commits the arrival", () => {
    // Given: a route to the unresolved ICE node is highlighted.
    const before = target(onStart(), 1);
    // When: one confirm.
    const arrived = act(before, "confirm");
    // Then: the move committed AND the decision opened, with nothing preselected.
    expect(arrived.currentNodeIndex).toBe(1);
    expect(arrived.visitedNodes).toContain(1);
    expect(arrived.turnCount).toBe(before.turnCount + 1);
    expect(arrived.selectedMatrixNodeIndex ?? null).toBeNull();
    expect(arrived.encounterDecision).toEqual({ selectedVerb: null, probed: false });
    expect(arrived.runPhase).toBe("matrix");
    expect(arrived.player.alarm).toBe(0);
    expect(renderRunScreen(arrived, 80, 50)?.hud[0]).toBe("ENCOUNTER");
  });

  it("does not open anything when the arrival node has no ICE or is resolved", () => {
    const atTwo = travel(choose(travel(onStart(), 1), "BYPASS"), 2);
    expect(atTwo.currentNodeIndex).toBe(2);
    expect(atTwo.encounterDecision ?? null).toBeNull();
  });

  it("cannot walk past an unresolved ICE: arrows and Enter act on the verbs, never on routes", () => {
    // Given
    const arrived = travel(onStart(), 1);
    // When: everything but a verb.
    let state = arrived;
    for (const type of ["move_south", "move_north", "confirm", "move_east", "confirm"] as const) {
      state = act({ ...state, encounterDecision: { selectedVerb: null, probed: false } }, type);
    }
    // Then
    expect(state.currentNodeIndex).toBe(1);
    expect(state.encounterDecision).not.toBeNull();
    expect(state.player.alarm).toBe(0);
  });

  it("re-gates the departure from an unresolved node reached without an arrival (CONTINUE)", () => {
    // Given: the decision is transient, so a restored state stands on node 1 with none open.
    const restored = { ...travel(onStart(), 1), encounterDecision: null };
    // When
    const attempted = act(target(restored, 2), "confirm");
    // Then: no free departure.
    expect(attempted.currentNodeIndex).toBe(1);
    expect(attempted.encounterDecision).toEqual({ selectedVerb: null, probed: false });
  });

  it("names the ways forward in the arrival message, inside the 40x60 HUD width", () => {
    // Given / When
    const arrived = travel(onStart(), 1);
    // Then
    for (const word of ["Travel blocked", "BREACH", "BYPASS: 60 COST (once per run)", "JACK OUT"])
      expect(arrived.message).toContain(word);
    // The 40x60 preset gives the HUD 16 columns; drawHud reserves one.
    const hud = rows(arrived, 40, 60).hud;
    for (const line of hud) expect(line.length).toBeLessThanOrEqual(15);
    const joined = hud.join(" ");
    for (const word of ["Travel blocked.", "BREACH: fight.", "BYPASS: 60 COST", "(once per run).", "JACK OUT:", "abandon run."])
      expect(joined).toContain(word);
  });

  it("states once on the encounter screen that the node gates travel", () => {
    const arrived = travel(onStart(), 1);
    for (const [cols, height] of LAYOUTS) {
      const grid = rows(arrived, cols, height).grid.join("\n");
      expect(grid.match(/ICE blocks travel/g) ?? []).toHaveLength(1);
    }
  });
});

describe("ADR-0250 decisions 2-4 — resolved nodes are remembered for the run", () => {
  it("records BYPASS in the run-scoped list and departs freely from a 2-neighbour node", () => {
    // Given: the owner's case — node 1 has exactly two neighbours.
    expect(MATRIX.nodes[1]?.adjacent).toHaveLength(2);
    const bypassed = choose(travel(onStart(), 1), "BYPASS");
    expect(bypassed.bypassedEncounterNodes).toEqual([1]);
    expect(bypassed.player.alarm).toBe(60);
    expect("bypassedEncounterNodeIndex" in bypassed).toBe(false);
    // When / Then: either neighbour, without the decision reopening.
    for (const to of [0, 2]) {
      const left = travel(bypassed, to);
      expect(left.currentNodeIndex).toBe(to);
      expect(left.encounterDecision ?? null).toBeNull();
      expect(left.player.alarm).toBe(60);
    }
  });

  it("keeps a BYPASS-resolved node resolved after moving away and coming back", () => {
    // Given
    const bypassed = choose(travel(onStart(), 1), "BYPASS");
    // When: away, back, and away again in the other direction.
    const away = travel(bypassed, 2);
    const back = travel(away, 1);
    const onward = travel(back, 0);
    // Then
    expect(back.currentNodeIndex).toBe(1);
    expect(back.encounterDecision ?? null).toBeNull();
    expect(back.bypassedEncounterNodes).toEqual([1]);
    expect(onward.currentNodeIndex).toBe(0);
    expect(onward.encounterDecision ?? null).toBeNull();
    expect(onward.player.alarm).toBe(60);
    expect(onward.player.credits).toBe(bypassed.player.credits);
    // Enter at rest on the resolved node does not reopen it either.
    expect(act(back, "confirm").encounterDecision ?? null).toBeNull();
  });

  it("keeps a combat-resolved node free to leave and to re-enter", () => {
    const breach = choose(travel(onStart(), 1), "BREACH");
    const won = applyAction(act(breach, "confirm"), { type: "use_program", programId: "strike" });
    expect(won.runPhase).toBe("loot");
    const board = act(won, "confirm");
    expect(board.clearedEncounterNodes).toContain(1);
    const away = travel(board, 2);
    const back = travel(away, 1);
    expect(away.encounterDecision ?? null).toBeNull();
    expect(back.encounterDecision ?? null).toBeNull();
  });

  it("still gates every unresolved node on arrival and still allows only one BYPASS", () => {
    // Given: node 1 bypassed (60 COST spent), then arrive at the boss.
    const atBoss = travel(travel(choose(travel(onStart(), 1), "BYPASS"), 2), 3);
    // Then: the boss opens on arrival; BYPASS stays blocked there (boss rule).
    expect(atBoss.currentNodeIndex).toBe(3);
    expect(atBoss.encounterDecision).not.toBeNull();
    const refused = choose(atBoss, "BYPASS");
    expect(refused.player.alarm).toBe(60);
    expect(refused.bypassedEncounterNodes).toEqual([1]);
    expect(refused.encounterDecision).not.toBeNull();
  });
});

describe("ADR-0250 decision 5 — the footer never claims travel when Enter opens the encounter", () => {
  it.each(LAYOUTS)("on an unresolved node with a route targeted (%sx%s)", (cols, height) => {
    // Given: CONTINUE-style state on node 1, route to node 2 highlighted.
    const state = target({ ...travel(onStart(), 1), encounterDecision: null }, 2);
    // When / Then: Enter opens the encounter, so the footer must not say travel.
    expect(act(state, "confirm").encounterDecision).not.toBeNull();
    const line = footer(state, cols, height);
    expect(line).not.toMatch(CLAIMS_TRAVEL);
    expect(line).toMatch(/ENTER:? (enter )?ICE/);
  });

  it.each(LAYOUTS)("and says travel exactly when Enter travels (%sx%s)", (cols, height) => {
    const state = target(choose(travel(onStart(), 1), "BYPASS"), 2);
    expect(act(state, "confirm").currentNodeIndex).toBe(2);
    expect(footer(state, cols, height)).toMatch(CLAIMS_TRAVEL);
  });

  it.each(LAYOUTS)("never claims travel on any frame where Enter would open the encounter (%sx%s)", (cols, height) => {
    // Walk the whole fixture and check every board frame against the reducer.
    const frames: GameState[] = [];
    let state = onStart();
    for (const step of [
      (s: GameState) => target(s, 1),
      (s: GameState) => act(s, "confirm"),
      (s: GameState) => choose(s, "BYPASS"),
      (s: GameState) => target(s, 2),
      (s: GameState) => act(s, "confirm"),
      (s: GameState) => target(s, 3),
      (s: GameState) => ({ ...s, currentNodeIndex: 3, selectedMatrixNodeIndex: 2 }),
    ]) {
      state = step(state);
      frames.push(state);
    }
    let checked = 0;
    for (const frame of frames) {
      if (frame.encounterDecision) continue;
      if (act(frame, "confirm").encounterDecision == null) continue;
      expect(footer(frame, cols, height)).not.toMatch(CLAIMS_TRAVEL);
      checked += 1;
    }
    expect(checked).toBeGreaterThan(0);
  });
});

describe("ADR-0250 decision 6 — save compatibility", () => {
  const missions = loadMissionsCatalog(missionsData);
  const programs = loadProgramsCatalog(programsData);

  function realRun(): GameState {
    const mission = missions[0]!;
    return makeInitialState(mission, WATCHDOG, []);
  }

  it("round-trips bypassedEncounterNodes through storage without a version bump", async () => {
    // Given
    const state = { ...realRun(), bypassedEncounterNodes: [2, 5] };
    const slot = stateToSaveSlot(state);
    // When
    await save(3, slot);
    const loaded = await load(3);
    const restored = loaded === null ? null : slotToGameState(loaded, missions, programs, WATCHDOG);
    // Then
    expect(slot.version).toBe(1);
    expect(slot.bypassedEncounterNodes).toEqual([2, 5]);
    expect(loaded?.bypassedEncounterNodes).toEqual([2, 5]);
    expect(restored?.bypassedEncounterNodes).toEqual([2, 5]);
  });

  it("loads an old save without the field as an empty list", async () => {
    // Given: a version-1 slot written before ADR-0250.
    const { bypassedEncounterNodes: _omitted, ...old } = stateToSaveSlot(realRun());
    localStorage.setItem("wetrun_mvp_save_v1_slot_3", JSON.stringify(old));
    // When
    const loaded = await load(3);
    const restored = loaded === null ? null : slotToGameState(loaded, missions, programs, WATCHDOG);
    // Then
    expect(loaded).not.toBeNull();
    expect(loaded).not.toHaveProperty("bypassedEncounterNodes");
    expect(loaded?.version).toBe(1);
    expect(restored?.bypassedEncounterNodes).toEqual([]);
  });

  it.each([null, "1", ["1"], [-1], [1.5]])("rejects a malformed bypassedEncounterNodes list: %j", async (bypassedEncounterNodes) => {
    localStorage.setItem(
      "wetrun_mvp_save_v1_slot_3",
      JSON.stringify({ ...stateToSaveSlot(realRun()), bypassedEncounterNodes }),
    );
    expect(await load(3)).toBeNull();
  });
});

describe("ADR-0250 — travel animation when the arrival opens a decision", () => {
  it("does not start a traversal the encounter screen would hide", () => {
    const before = target(onStart(), 1);
    const arrived = act(before, "confirm");
    expect(arrived.encounterDecision).not.toBeNull();
    expect(beginMatrixTravel(before, arrived, 0, false)).toBeNull();
  });

  it("still animates a free arrival", () => {
    const before = target(choose(travel(onStart(), 1), "BYPASS"), 2);
    const arrived = act(before, "confirm");
    expect(beginMatrixTravel(before, arrived, 0, false)).toEqual({ from: 1, to: 2, startedMs: 0 });
  });
});
