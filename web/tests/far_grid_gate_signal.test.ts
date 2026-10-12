/** Tests for Far Grid gate — Arc 1 clear signal integration (ADR-0213 Phase 2).
 *
 * Exercises the canonical Arc-1-clear hook: clearing any Arc 1 mission via
 * `applyLootAction` (the existing run-completion signal — `resolveEnding`
 * is invoked at mission-complete with `arc === 1`) must flip the
 * `farGridUnlocked` flag.
 *
 * Arc 2+ clears must NOT flip the flag. This is the negative case that
 * proves the hook is gated by arc id, not by "any mission complete".
 */
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { applyLootAction } from "../src/core/state_actions";
import { makeInitialState } from "../src/core/state";
import { isFarGridUnlocked, resetFarGridUnlocked } from "../src/core/far_grid_gate";
import type { GameState, Ice, Mission, Program } from "../src/core/types";

const STORAGE_KEY = "wetrun_far_grid_unlocked";

const mockProgram: Program = {
  id: "test_prog",
  name: "Test Program",
  tier: 1,
  cost: 10,
  effect: "test",
  description: "Test",
  aoe: false,
};

const mockIce: Ice = {
  id: "watchdog",
  name: "Watchdog",
  hp: 100,
  armor: 0,
  tier: 1,
};

function makeMission(arc: number, id: string): Mission {
  return {
    id,
    title: `Arc ${arc} Mission`,
    fixer: "test_fixer",
    arc,
    zone: "test",
    grade_min: 1,
    grade_max: 1,
    rewards: { credits: 100, materials: {} },
  };
}

/** Force the matrix to the "mission complete" terminal shape.
 *
 * The completion signal in applyLootAction checks:
 *   !state.matrix || !node || node.adjacent.length === 0 || node.isBoss
 * The cleanest test fixture is a matrix with a single dead-end node.
 */
function withTerminatedMatrix(state: GameState): GameState {
  return {
    ...state,
    runPhase: "loot",
    matrix: {
      nodes: [
        {
          id: 0,
          zone: "surface",
          iceIds: [],
          iceHp: [],
          reward: { credits: 0 },
          isBoss: false,
          adjacent: [], // dead-end triggers missionComplete
        },
      ],
      startNode: 0,
      bossNode: 0,
    },
    currentNodeIndex: 0,
  };
}

beforeEach(() => {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore
  }
});

afterEach(() => {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore
  }
});

describe("Arc 1 clear → Far Grid unlock (ADR-0213 Phase 2)", () => {
  it("clearing an Arc 1 mission flips the farGridUnlocked flag", () => {
    expect(isFarGridUnlocked()).toBe(false);
    const state0 = makeInitialState(
      makeMission(1, "aleph_fragment"),
      mockIce,
      [mockProgram],
    );
    const state1 = withTerminatedMatrix(state0);
    const next = applyLootAction(state1, { type: "confirm" });
    expect(next.runPhase).toBe("ending");
    expect(isFarGridUnlocked()).toBe(true);
  });

  it("clearing a non-Arc-1 mission does NOT flip the flag", () => {
    expect(isFarGridUnlocked()).toBe(false);
    // Arc 2 mission
    const state0 = makeInitialState(
      makeMission(2, "wigan_call"),
      mockIce,
      [mockProgram],
    );
    const state1 = withTerminatedMatrix(state0);
    const next = applyLootAction(state1, { type: "confirm" });
    expect(next.runPhase).toBe("ending");
    expect(isFarGridUnlocked()).toBe(false);
  });

  it("clearing an Arc 5 mission does NOT flip the flag", () => {
    expect(isFarGridUnlocked()).toBe(false);
    const state0 = makeInitialState(
      makeMission(5, "final_choice"),
      mockIce,
      [mockProgram],
    );
    const state1 = withTerminatedMatrix(state0);
    const next = applyLootAction(state1, { type: "confirm" });
    expect(next.runPhase).toBe("ending");
    expect(isFarGridUnlocked()).toBe(false);
  });

  it("the hook is idempotent — repeated Arc 1 clears are no-ops", () => {
    expect(isFarGridUnlocked()).toBe(false);
    const state0 = makeInitialState(
      makeMission(1, "aleph_fragment"),
      mockIce,
      [mockProgram],
    );
    const state1 = withTerminatedMatrix(state0);
    applyLootAction(state1, { type: "confirm" });
    expect(isFarGridUnlocked()).toBe(true);
    // Second Arc 1 clear — flag stays unlocked, state still ending
    const state2 = withTerminatedMatrix(makeInitialState(
      makeMission(1, "second_arc1"),
      mockIce,
      [mockProgram],
    ));
    const next2 = applyLootAction(state2, { type: "confirm" });
    expect(next2.runPhase).toBe("ending");
    expect(isFarGridUnlocked()).toBe(true);
  });

  it("non-confirm actions do NOT trigger the unlock", () => {
    expect(isFarGridUnlocked()).toBe(false);
    const state0 = makeInitialState(
      makeMission(1, "aleph_fragment"),
      mockIce,
      [mockProgram],
    );
    const state1 = withTerminatedMatrix(state0);
    // jack_out should not flip the flag even though we're at mission complete
    const next = applyLootAction(state1, { type: "jack_out" });
    expect(next.runPhase).toBe("loot");
    expect(isFarGridUnlocked()).toBe(false);
  });

  it("resetFarGridUnlocked restores the locked state after a clear", () => {
    const state0 = makeInitialState(
      makeMission(1, "aleph_fragment"),
      mockIce,
      [mockProgram],
    );
    const state1 = withTerminatedMatrix(state0);
    applyLootAction(state1, { type: "confirm" });
    expect(isFarGridUnlocked()).toBe(true);
    resetFarGridUnlocked();
    expect(isFarGridUnlocked()).toBe(false);
  });
});