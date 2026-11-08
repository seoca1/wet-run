/**
 * ADR-0308 — a bypass counts as a resolved encounter for the core's gate.
 *
 * ADR-0290 sealed the core until N encounters fall, clamped to the non-boss ICE
 * the board holds. BYPASS (60 COST, once per run) appended the node to
 * `bypassedEncounterNodes` but never cleared its `iceIds`, so the clamp still
 * counted it. On a board with a single encounter that sealed the core for good:
 * `Flatline's Call` -> BYPASS its only ICE -> `Core sealed — 1 more ICE must
 * fall (0/1)` with nothing left to fight, and JACK OUT as the only exit. Three
 * of 99 soak runs ended exactly that way.
 *
 * The gate must still ask for a real path: bypassing one of two encounters has
 * to leave the other one required.
 */
import { describe, expect, it } from "vitest";
import { bossGateNeed } from "../src/core/combat/ice_scaling";
import { applyAction, makeInitialState } from "../src/core/state/state";
import { startingDeck } from "../src/core/state/starting_deck";
import {
  loadIceCatalog,
  loadMissionsCatalog,
  loadProgramsCatalog,
} from "../src/core/data_loaders";
import type { GameState, Matrix, MatrixNode } from "../src/core/types";
import iceJson from "../src/data/ice_types.json" with { type: "json" };
import missionsJson from "../src/data/missions.json" with { type: "json" };
import programsJson from "../src/data/programs.json" with { type: "json" };

const ice = loadIceCatalog(iceJson);
const programs = loadProgramsCatalog(programsJson);
const missions = loadMissionsCatalog(missionsJson);

function node(
  id: number,
  adjacent: readonly number[],
  iceIds: readonly string[] = [],
  isBoss = false,
): MatrixNode {
  return {
    id,
    zone: "mid",
    iceIds,
    iceHp: [],
    reward: { credits: 0 },
    isBoss,
    adjacent,
  };
}

/** 0 -> 1 (ICE) -> 3 -> 4 (boss); 0 -> 2 (ICE) -> 3. Two encounters. */
function fork(): Matrix {
  return {
    startNode: 0,
    bossNode: 4,
    grade: 4,
    nodes: [
      node(0, [1, 2]),
      node(1, [0, 3], ["wisp"]),
      node(2, [0, 3], ["wisp"]),
      node(3, [1, 2, 4]),
      node(4, [3], ["ta_sentinel"], true),
    ],
  };
}

/** The same board with node 2's encounter removed: a single non-boss ICE. */
function thin(): Matrix {
  const board = fork();
  return {
    ...board,
    nodes: board.nodes.map((n, i) => (i === 2 ? { ...n, iceIds: [] } : n)),
  };
}

/** A run at the core's doorstep with the given resolved encounters. */
function standingAtTheCore(
  matrix: Matrix,
  resolved: {
    readonly cleared?: readonly number[];
    readonly bypassed?: readonly number[];
  },
): GameState {
  const mission = Object.values(missions).find((m) => m.id === "ta_heist");
  expect(mission).toBeDefined();
  const base = makeInitialState(
    mission as never,
    Object.values(ice)[0] as never,
    startingDeck(programs, "novice"),
  );
  return {
    ...base,
    runPhase: "matrix",
    phase: "menu",
    matrix,
    currentNodeIndex: 3,
    selectedMatrixNodeIndex: 4,
    clearedEncounterNodes: resolved.cleared ?? [],
    bypassedEncounterNodes: resolved.bypassed ?? [],
  };
}

describe("ADR-0308 · a bypass resolves the gate", () => {
  it("opens the core when the board's only encounter was bypassed", () => {
    // Given: one encounter, already paid for with BYPASS.
    const state = standingAtTheCore(thin(), { bypassed: [1] });

    // Then: the gate asks for nothing the runner cannot get.
    expect(bossGateNeed(state)).toBe(0);

    // When: the runner steps in.
    const after = applyAction(state, { type: "confirm" });

    // Then: they reach the climax instead of reading "Core sealed".
    expect(after.currentNodeIndex).toBe(4);
    expect(after.message).not.toContain("Core sealed");
  });

  it("still demands the encounter a bypass did not resolve", () => {
    // Given: two encounters, one bypassed.
    const state = standingAtTheCore(fork(), { bypassed: [1] });

    // Then: the other one is still required and the core refuses.
    expect(bossGateNeed(state)).toBe(1);
    const after = applyAction(state, { type: "confirm" });
    expect(after.currentNodeIndex).toBe(3);
    expect(after.message).toContain("Core sealed");
  });

  it("does not let a bypass replace a clear it did not pay for", () => {
    // Given: one encounter bypassed, the other cleared.
    const state = standingAtTheCore(fork(), { bypassed: [1], cleared: [2] });

    // Then: the clear satisfies the gate.
    expect(bossGateNeed(state)).toBe(1);
    expect(applyAction(state, { type: "confirm" }).currentNodeIndex).toBe(4);
  });
});
