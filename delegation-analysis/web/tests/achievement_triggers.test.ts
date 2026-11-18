import { describe, it, expect } from "vitest";
import { applyAction, makeInitialState } from "../src/core/state.ts";
import type { GameState, Ice, Mission, Program } from "../src/core/types.ts";

function makeCombatState(overrides: Partial<GameState> = {}): GameState {
  const mockMission: Mission = {
    id: "test",
    title: "Test Mission",
    fixer: "test",
    arc: 1,
    zone: "test_zone",
    grade_min: 1,
    grade_max: 1,
    rewards: { credits: 100, materials: {} },
  };
  
  const mockProgram: Program = {
    id: "p1",
    name: "Attack",
    tier: 1,
    cost: 0,
    effect: "damage",
    description: "test program",
    aoe: false,
  };
  
  const mockIce: Ice = {
    id: "enemy1",
    name: "Test Enemy",
    tier: 1,
    hp: 1,
    maxHp: 50,
    armor: 0,
    personality: "aggressive",
    aggression: "standard",
    skills: [],
  };
  
  const state = makeInitialState(mockMission, mockIce, [mockProgram]);
  return {
    ...state,
    iceRoster: [mockIce],
    activeIceIndex: 0,
    phase: "combat",
    runPhase: "combat",
    lastEnemyAttackMs: 0,
    dixieLastAttackMs: 0,
    skillCooldowns: {},
    unlockedAchievements: [],
    achievementCredits: 0,
    ...overrides,
  };
}

describe("achievement triggers", () => {
  it("unlocks first_blood on first enemy kill", () => {
    const state = makeCombatState();
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    expect(result.unlockedAchievements).toContain("first_blood");
  });

  it("grants achievement credits for first_blood", () => {
    const state = makeCombatState();
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    expect(result.achievementCredits).toBe(50);
  });

  it("does not unlock first_blood twice", () => {
    const state = makeCombatState({ unlockedAchievements: ["first_blood"] });
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    const firstBloodCount = result.unlockedAchievements.filter(a => a === "first_blood").length;
    expect(firstBloodCount).toBe(1);
  });

  it("unlocks boss_slayer when defeating first boss", () => {
    const state = makeCombatState({
      bossPhase: 1,
      unlockedAchievements: ["first_blood"],
    });
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    expect(result.unlockedAchievements).toContain("boss_slayer");
    expect(result.achievementCredits).toBeGreaterThanOrEqual(1000);
  });

  it("does not unlock boss_slayer twice", () => {
    const state = makeCombatState({
      bossPhase: 1,
      unlockedAchievements: ["first_blood", "boss_slayer"],
      achievementCredits: 1050,
    });
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    const bossSlayerCount = result.unlockedAchievements.filter(a => a === "boss_slayer").length;
    expect(bossSlayerCount).toBe(1);
  });

  it("unlocks combo_master with 6+ combo", () => {
    const state = makeCombatState({
      playerCombo: 6,
      unlockedAchievements: ["first_blood"],
    });
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    expect(result.unlockedAchievements).toContain("combo_master");
  });

  it("does not unlock combo_master with combo < 6", () => {
    const state = makeCombatState({
      playerCombo: 3,
      unlockedAchievements: ["first_blood"],
    });
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    expect(result.unlockedAchievements).not.toContain("combo_master");
  });

  it("accumulates achievement credits across multiple unlocks", () => {
    const state = makeCombatState({
      bossPhase: 1,
      playerCombo: 6,
    });
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    expect(result.achievementCredits).toBe(50 + 1000 + 500);
  });
});
