/**
 * ADR-0290 — fighting has to be worth it, and the mission has to ask for it.
 *
 * ADR-0288/0289 measured the defect: skipping an encounter was free, so from
 * grade 4 up walking to the boss beat seeking encounters by up to +47pp, and no
 * loot could close it (even a full heal on every card left g6 at 16.7% against
 * 59.7%). The reward was never the problem — the fight was one the opening deck
 * usually lost, and the escape was free.
 *
 * Two changes, measured together:
 *  1. the late grades' encounters are winnable (damage penalty, lower ceiling);
 *  2. the core opens after a real path, not after a walk.
 *
 * The gate is the part that needs guarding: it must never shut a mission that
 * has fewer encounters than it demands, and it must not be satisfiable by
 * standing still.
 */
import { describe, expect, it } from "vitest";
import {
  BOSS_HP_BY_GRADE,
  bossGateClears,
  bossGateNeed,
  iceHpForGrade,
} from "../src/core/combat/ice_scaling";
import { applyAction, makeInitialState } from "../src/core/state/state";
import { startingDeck } from "../src/core/state/starting_deck";
import { loadIceCatalog, loadMissionsCatalog, loadProgramsCatalog } from "../src/core/data_loaders";
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

/** 0 -> 1 (ICE) -> 4 (boss); 0 -> 2 (ICE) -> 4. */
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

/** A run standing next to the core with nothing cleared yet. */
function standingAtTheCore(cleared: readonly number[]): GameState {
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
    matrix: fork(),
    currentNodeIndex: 3,
    selectedMatrixNodeIndex: 4,
    clearedEncounterNodes: cleared,
    bypassedEncounterNodes: [],
  };
}

describe("ADR-0290 · the core opens after a path", () => {
  it("refuses the core while nothing has been cleared", () => {
    // Given: a runner at the core's doorstep, no encounters cleared.
    const sealed = standingAtTheCore([]);

    // When: they try to enter.
    const after = applyAction(sealed, { type: "confirm" });

    // Then: they did not move, and the screen says why.
    expect(after.currentNodeIndex).toBe(3);
    expect(after.message).toContain("Core sealed");
    expect(after.message).toContain("1 more ICE");
  });

  it("opens the core once the mission's clears are paid", () => {
    // Given: one encounter already fell.
    const paid = standingAtTheCore([1]);

    // When
    const after = applyAction(paid, { type: "confirm" });

    // Then: the runner walks into the climax.
    expect(after.currentNodeIndex).toBe(4);
    expect(after.message).not.toContain("Core sealed");
  });

  it("never demands more clears than the board holds", () => {
    // Given: a board with a single non-boss encounter, at a grade whose nominal
    // demand is higher.
    const board = fork();
    const thin = {
      ...board,
      nodes: board.nodes.map((n, i) =>
        i === 2 ? { ...n, iceIds: [] } : n,
      ),
    };
    const state = standingAtTheCore([]);

    // When / Then: the demand clamps to what exists, so no mission can be shut.
    expect(bossGateNeed({ ...state, matrix: thin })).toBe(1);
    expect(
      bossGateNeed({ ...state, matrix: { ...board, nodes: researchOnly() } }),
    ).toBe(0);
  });

  it("keeps the climax's HP budget separate from the encounter ceiling", () => {
    // Given: one ICE, asked for at the same grade twice.
    const sentinel = ice["ta_sentinel"];
    expect(sentinel).toBeDefined();
    if (!sentinel) return;

    // Then: as a boss it is allowed more HP than an ordinary encounter, so
    // lowering the encounter ceiling (ADR-0290) does not cut the climax.
    expect(iceHpForGrade(sentinel, 5, true)).toBeGreaterThan(
      iceHpForGrade(sentinel, 5, false),
    );
    expect(iceHpForGrade(sentinel, 5, true)).toBe(BOSS_HP_BY_GRADE[4]);
  });

  it("keeps a gate at every grade that can pay it", () => {
    // Given / When / Then: g1 missions are the shortest, so g1 asks for nothing;
    // every later grade asks for at least one clear.
    expect(bossGateClears(1)).toBe(0);
    for (const grade of [2, 3, 4, 5, 6]) {
      expect(bossGateClears(grade)).toBeGreaterThanOrEqual(1);
    }
  });
});

/** A board whose only ICE is the core itself. */
function researchOnly(): ReadonlyArray<MatrixNode> {
  return [node(0, [1]), node(1, [0], ["ta_sentinel"], true)];
}
