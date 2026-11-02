import { describe, it, expect } from "vitest";
import { applyLootAction } from "../src/core/state/state_actions_phases";
import type { GameState } from "../src/core/types";

/**
 * What the loot screen's keys actually do.
 *
 * The loot screen used to promise "↑↓: navigate | ENTER: continue | ESC:
 * back" while only ENTER did anything: `applyLootAction` ignores cancel
 * and the move keys, and returns the state unchanged. ADR-0251 rule 5
 * applies, so the screen no longer claims them — and this test pins why.
 */
function lootState(): GameState {
  return {
    runPhase: "loot",
    phase: "victory",
    turnCount: 3,
    player: { hp: 48, maxHp: 100, alarm: 15, credits: 4075, playerCombo: 0 },
    deck: [],
    discardPile: [],
    iceRoster: [],
    activeIceIndex: 0,
    statusEffects: [],
    combatLog: [],
    vfxInstances: [],
    matrix: {
      nodes: [
        {
          id: "n1",
          zone: "mid",
          iceIds: [],
          adjacent: [],
          reward: { credits: 0, materials: {} },
        },
      ],
    },
    visitedNodes: [0],
    currentNodeIndex: 0,
    selectedMatrixNodeIndex: null,
    encounterDecision: null,
    bypassedEncounterNodeIndex: null,
    missionsCompleted: [],
    missionId: "m1",
    tier: 3,
    mission: { rewards: { credits: 100 } },
    equipmentLoadout: {
      slots: {},
      totalStats: () => ({
        attackBonus: 0,
        critBonusPct: 0,
        damageBonusPct: 0,
        armorBonus: 0,
      }),
    },
    activeMutators: [],
    factionReputation: {},
    unlockedAchievements: [],
    achievementCredits: 0,
    factionScores: {},
  } as unknown as GameState;
}

describe("loot screen key contract", () => {
  it("ignores cancel (ESC) — the screen must not promise it", () => {
    const before = lootState();
    const after = applyLootAction(before, { type: "cancel" });
    expect(after).toBe(before);
  });

  it("ignores the move keys (↑↓) — the screen must not promise them", () => {
    const before = lootState();
    expect(applyLootAction(before, { type: "move_north" })).toBe(before);
    expect(applyLootAction(before, { type: "move_south" })).toBe(before);
  });
});
