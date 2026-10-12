/** Tests for Far Grid gate — Arc 1 clear signal integration (ADR-0213 Phase 2 + tightening).
 *
 * Phase 2 originally: clearing any Arc 1 mission flipped the flag.
 * Phase 2 tightening: the flag only flips after EVERY required Sprawl Arc-1
 * mission has been cleared. The completion-log + full-clear predicate lives
 * in `far_grid_gate.ts`; this test verifies the wiring through
 * `applyLootAction`.
 *
 * Positive cases:
 *  - 1 of 6 Arc-1 clears → flag stays false (no longer flips on any single Arc-1 clear)
 *  - 5 of 6 Arc-1 clears → flag stays false (one short)
 *  - 6 of 6 Arc-1 clears → flag flips true
 *  - Idempotent: 7th clear of an already-unlocked mission is a no-op
 *
 * Negative cases:
 *  - Arc 2+ clears never flip
 *  - non-confirm actions never flip
 *  - Far-Grid-tagged Arc-1 missions (source_universe=far-grid) never flip on
 *    their own — they are not part of the Sprawl Arc-1 required set
 */
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { applyLootAction } from "../src/core/state_actions";
import { makeInitialState } from "../src/core/state";
import {
  arcOneMissionIds,
  farGridUnlocked,
  getCompletedMissions,
  isFarGridUnlocked,
  resetCompletedMissions,
  resetFarGridUnlocked,
} from "../src/core/far_grid_gate";
import type { GameState, Ice, Mission, Program } from "../src/core/types";

const FLAG_STORAGE_KEY = "wetrun_far_grid_unlocked";
const COMPLETED_STORAGE_KEY = "wetrun_completed_missions";

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
    localStorage.removeItem(FLAG_STORAGE_KEY);
    localStorage.removeItem(COMPLETED_STORAGE_KEY);
  } catch {
    // ignore
  }
});

afterEach(() => {
  try {
    localStorage.removeItem(FLAG_STORAGE_KEY);
    localStorage.removeItem(COMPLETED_STORAGE_KEY);
  } catch {
    // ignore
  }
});

/** Drive `applyLootAction` on a fresh state for the given mission. */
function clearMission(missionId: string, arc: number): GameState {
  const state0 = makeInitialState(
    makeMission(arc, missionId),
    mockIce,
    [mockProgram],
  );
  const state1 = withTerminatedMatrix(state0);
  return applyLootAction(state1, { type: "confirm" });
}

describe("Full Sprawl Arc-1 clear → Far Grid unlock (ADR-0213 Phase 2 tightening)", () => {
  it("clearing ONE Arc-1 mission does NOT flip the flag (was: did)", () => {
    expect(isFarGridUnlocked()).toBe(false);
    const next = clearMission("data_retrieval", 1);
    expect(next.runPhase).toBe("ending");
    // The mission id was logged for the completion record.
    expect(getCompletedMissions()).toEqual(["data_retrieval"]);
    // ...but the flag stays false because 5 more Arc-1 clears remain.
    expect(isFarGridUnlocked()).toBe(false);
  });

  it("clearing FIVE of SIX Arc-1 missions keeps the flag locked", () => {
    const ids = arcOneMissionIds();
    expect(ids.length).toBe(6);
    for (let i = 0; i < 5; i++) {
      const next = clearMission(ids[i] as string, 1);
      expect(next.runPhase).toBe("ending");
    }
    expect(getCompletedMissions().length).toBe(5);
    expect(isFarGridUnlocked()).toBe(false);
    expect(farGridUnlocked()).toBe(false);
  });

  it("clearing ALL SIX Sprawl Arc-1 missions flips the flag", () => {
    const ids = arcOneMissionIds();
    expect(ids.length).toBe(6);
    for (let i = 0; i < ids.length; i++) {
      const next = clearMission(ids[i] as string, 1);
      expect(next.runPhase).toBe("ending");
      if (i < ids.length - 1) {
        expect(isFarGridUnlocked()).toBe(false);
      }
    }
    expect(getCompletedMissions().length).toBe(6);
    expect(isFarGridUnlocked()).toBe(true);
    expect(farGridUnlocked()).toBe(true);
  });

  it("clearing an Arc 2 mission never flips the flag", () => {
    expect(isFarGridUnlocked()).toBe(false);
    const next = clearMission("wigan_call", 2);
    expect(next.runPhase).toBe("ending");
    expect(isFarGridUnlocked()).toBe(false);
  });

  it("clearing an Arc 5 mission never flips the flag", () => {
    expect(isFarGridUnlocked()).toBe(false);
    const next = clearMission("final_choice", 5);
    expect(next.runPhase).toBe("ending");
    expect(isFarGridUnlocked()).toBe(false);
  });

  it("non-confirm actions do NOT trigger the unlock (Arc-1 or otherwise)", () => {
    expect(isFarGridUnlocked()).toBe(false);
    const state0 = makeInitialState(
      makeMission(1, "data_retrieval"),
      mockIce,
      [mockProgram],
    );
    const state1 = withTerminatedMatrix(state0);
    const next = applyLootAction(state1, { type: "jack_out" });
    expect(next.runPhase).toBe("loot");
    expect(isFarGridUnlocked()).toBe(false);
    expect(getCompletedMissions()).toEqual([]);
  });

  it("recordMissionComplete persists across the auto-path — survives a manual reset of just the flag", () => {
    for (const id of arcOneMissionIds()) clearMission(id, 1);
    expect(isFarGridUnlocked()).toBe(true);
    // Manual flag reset (admin escape hatch) — completion record intact.
    resetFarGridUnlocked();
    expect(isFarGridUnlocked()).toBe(false);
    expect(getCompletedMissions().length).toBe(6);
    // farGridUnlocked (OR semantics) still returns true because the
    // full-clear predicate is satisfied.
    expect(farGridUnlocked()).toBe(true);
  });

  it("clearing a Far-Grid-tagged Arc-1 mission does NOT count toward Sprawl clear", () => {
    // source_universe=far-grid missions are not in the Sprawl Arc-1 set.
    expect(getCompletedMissions()).toEqual([]);
    expect(isFarGridUnlocked()).toBe(false);
    // Clear every Far-Grid Arc-1 mission (none are sprawl).
    for (const id of [
      "far_grid_prelude",
      "don_mac_audit",
      "deathspiders_news",
      "warren_meadow",
      "blue_silk_wall",
      "maidens_first_run",
      "pollack_after_dark",
      "hetmans_meeting",
      "maurice_princes",
      "dodgers_office",
      "tin_soldiers_end",
      "moat_burned_blue",
      "rogers_backyard",
      "arkady_in_orange",
    ]) {
      clearMission(id, 1);
    }
    // 14 far-grid arc-1 clears: NONE unlock. The completion log captures
    // every clear, but the flag is gated by the Sprawl-Arc-1 set, not by raw count.
    expect(isFarGridUnlocked()).toBe(false);
    expect(getCompletedMissions().length).toBe(14);
  });

  it("repeated Arc-1 clears are idempotent in the completion record", () => {
    clearMission("data_retrieval", 1);
    clearMission("data_retrieval", 1);
    expect(getCompletedMissions()).toEqual(["data_retrieval"]);
    expect(isFarGridUnlocked()).toBe(false);
  });

  it("resetCompletedMissions clears the log without touching the flag", () => {
    for (const id of arcOneMissionIds()) clearMission(id, 1);
    expect(isFarGridUnlocked()).toBe(true);
    resetCompletedMissions();
    expect(getCompletedMissions()).toEqual([]);
    // Already-unlocked save never re-locks (ADR invariant).
    expect(isFarGridUnlocked()).toBe(true);
  });
});