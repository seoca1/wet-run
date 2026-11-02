import { describe, it, expect } from "vitest";
import { useProgram } from "../src/core/combat/state_actions_programs";
import type { GameState } from "../src/core/types";

/**
 * The COST the killing blow charges.
 *
 * ADR-0251 open question (a): the reducer does not charge COST when the
 * play defeats the last ICE — the victory branch returns before the
 * `alarm: newAlarm` assignment that the normal branch makes. That is why
 * the hand label may not promise a predicted remaining COST (see
 * program_affordance.test.ts).
 *
 * This pins the behaviour the label is derived from: a non-lethal play
 * charges the card's COST, a lethal play charges nothing.
 */
function combatState(iceHp: number): GameState {
  const ice = {
    id: "ice1",
    name: "Yakuza Enforcer",
    hp: iceHp,
    maxHp: 165,
    armor: 0,
    level: 3,
    iceIds: [],
    programs: [],
    weak: false,
  };
  return {
    runPhase: "combat",
    phase: "combat",
    turnCount: 1,
    player: { hp: 100, maxHp: 100, alarm: 10, credits: 0, playerCombo: 0 },
    deck: [
      {
        id: "p1",
        name: "Test",
        tier: 2,
        cost: 2,
        effect: "attack",
        description: "d",
        aoe: false,
      },
    ],
    discardPile: [],
    iceRoster: [ice],
    ice: ice,
    activeIceIndex: 0,
    statusEffects: [],
    combatLog: [],
    vfxInstances: [],
    matrix: null,
    visitedNodes: [],
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

describe("COST charged by a play", () => {
  it("charges the card's COST when the play does not defeat the ICE", () => {
    const before = combatState(165);
    const after = useProgram(before, "p1");
    expect(after.player.alarm).toBe(12);
    expect(after.runPhase).toBe("combat");
  });

  it("charges nothing when the play defeats the ICE", () => {
    const before = combatState(1);
    const after = useProgram(before, "p1");
    expect(after.player.alarm).toBe(10);
    expect(after.runPhase).toBe("loot");
  });
});
