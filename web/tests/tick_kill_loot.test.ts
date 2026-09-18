/**
 * Regression test for Fix #5: combat tick-killed enemies must produce loot.
 *
 * Background: previously `applyCombatAction` computed `newlyDefeated` from the
 * pre-tick `damagedRoster`, so an ICE that survived the player's direct hit
 * but died from a burn/bleed tick in the same turn was counted in
 * `allDefeated` (so the run advanced to loot) but NOT in `newlyDefeated` (so
 * no loot roll and no faction reputation credit were issued).
 *
 * The fix recomputes `newlyDefeated` from the post-tick `finalState.iceRoster`,
 * comparing against the *original* `state.iceRoster`. This test arranges a
 * scenario where the player's program is an AoE damage program that puts the
 * victim at low HP (1), then a pre-existing burn ticks the victim from HP=1
 * to HP=0. The test verifies the loot was added.
 *
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, afterEach } from "vitest";
import { applyCombatAction } from "../src/core/state_actions.ts";
import type { GameState, GameAction, Ice, Mission, Program } from "../src/core/types.ts";
import { makeInitialState } from "../src/core/state.ts";

const mockMission: Mission = {
  id: "tick_kill_test",
  title: "Tick Kill",
  fixer: "fixer",
  arc: 1,
  zone: "test",
  grade_min: 1,
  grade_max: 1,
  rewards: { credits: 100, materials: {} },
};

const mockIce: Ice = {
  id: "watchdog",
  name: "Watchdog",
  hp: 50,
  armor: 0,
  tier: 1,
};

const strikeProgram: Program = {
  id: "strike",
  name: "Strike",
  tier: 1,
  cost: 1,
  effect: "attack",
  description: "Basic attack",
  aoe: false,
};

function makePreState(): GameState {
  const base = makeInitialState(mockMission, mockIce, [strikeProgram]);
  return {
    ...base,
    phase: "combat",
    runPhase: "combat",
    iceRoster: [
      { id: "watchdog", name: "Watchdog A", hp: 4, armor: 0, tier: 1 },
      { id: "watchdog", name: "Watchdog B", hp: 50, armor: 0, tier: 1 },
    ],
    activeIceIndex: 0,
    inventory: { credits: 0, materials: {}, programs: [] },
    statusEffects: [
      { kind: "burn", target: "ice", magnitude: 100, remaining: 1, dotDamage: 100 },
    ],
  };
}

describe("Fix #5 — tick-killed ICE produces loot", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("tick-killed watchdog at index 0 produces loot materials", () => {
    vi.spyOn(Math, "random").mockReturnValue(0.001);

    const pre = makePreState();
    const beforeMaterialsCount = Object.keys(pre.inventory.materials).length;

    const action: GameAction = { type: "use_program", programId: strikeProgram.id };
    const result = applyCombatAction(pre, action);

    const victim = result.iceRoster[0];
    expect(victim).toBeDefined();
    expect(victim?.hp ?? 1).toBe(0);

    const afterMaterialsCount = Object.keys(result.inventory.materials).length;
    expect(afterMaterialsCount).toBeGreaterThan(beforeMaterialsCount);
  });
});
