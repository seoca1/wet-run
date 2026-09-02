import { describe, it, expect } from "vitest";
import { applyAction, makeInitialState } from "../src/core/state.ts";
import type { GameState, Ice, Mission, Program } from "../src/core/types.ts";

function makeCombatState(overrides: Partial<GameState> = {}): GameState {
  const mockMission: Mission = {
    id: "test", title: "Test", fixer: "test", arc: 1, zone: "test",
    grade_min: 1, grade_max: 1, rewards: { credits: 10, materials: {} },
  };
  const mockProgram: Program = {
    id: "p1", name: "Atk", tier: 1, cost: 0, effect: "damage", description: "test", aoe: false,
  };
  const mockIce: Ice = {
    id: "enemy1", name: "Enemy", tier: 1, hp: 50, maxHp: 50, armor: 0,
    personality: "aggressive", aggression: "standard", skills: [],
  };
  const state = makeInitialState(mockMission, mockIce, [mockProgram]);
  return {
    ...state,
    iceRoster: [mockIce],
    activeIceIndex: 0,
    phase: "combat" as const,
    runPhase: "combat" as const,
    lastEnemyAttackMs: 0,
    dixieLastAttackMs: 0,
    skillCooldowns: {},
    ...overrides,
  };
}

describe("Dixie companion", () => {
  it("Dixie attacks when cooldown expired", () => {
    const state = makeCombatState({
      dixieLastAttackMs: 0,
    });
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    expect(result.message).toContain("Dixie attacks");
  });

  it("Dixie damage increases with combo count", () => {
    const state = makeCombatState({
      dixieLastAttackMs: 0,
      playerCombo: 5,
    });
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    expect(result.iceRoster[0].hp).toBeLessThanOrEqual(50 - 23);
  });

  it("Dixie does not attack when on cooldown", () => {
    const state = makeCombatState({
      dixieLastAttackMs: Date.now(),
    });
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    expect(result.message).not.toContain("Dixie attacks");
  });

  it("Dixie targets first living enemy", () => {
    const roster: Ice[] = [
      { id: "dead", name: "Dead", tier: 1, hp: 0, maxHp: 50, armor: 0, personality: "aggressive", aggression: "standard", skills: [] },
      { id: "alive", name: "Alive", tier: 1, hp: 50, maxHp: 50, armor: 0, personality: "aggressive", aggression: "standard", skills: [] },
    ];
    const state = makeCombatState({
      iceRoster: roster,
      dixieLastAttackMs: 0,
    });
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    expect(result.iceRoster[0].hp).toBe(0);
    expect(result.iceRoster[1].hp).toBeLessThan(50);
  });
});
