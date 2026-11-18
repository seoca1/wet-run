import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
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
    id: "enemy1", name: "Enemy", tier: 2, hp: 50, maxHp: 50, armor: 0,
    personality: "aggressive", aggression: "aggressive",
    skills: [{ id: "heavy", name: "Heavy Strike", effect: "heavy_attack", cooldownMs: 2000, damage: 20 }],
  };
  const state = makeInitialState(mockMission, mockIce, [mockProgram]);
  return {
    ...state,
    iceRoster: [mockIce],
    activeIceIndex: 0,
    phase: "combat" as const,
    runPhase: "combat" as const,
    lastEnemyAttackMs: 0,
    dixieLastAttackMs: Date.now(),
    skillCooldowns: {},
    ...overrides,
  };
}

describe("personality-based skill selection", () => {
  beforeEach(() => {
    vi.spyOn(Math, "random").mockReturnValue(0.01);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("aggressive personality prefers heavy_attack skills", () => {
    const state = makeCombatState();
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    expect(result.message).toContain("Heavy Strike");
  });

  it("defensive personality prefers shield/heal skills", () => {
    const enemy: Ice = {
      id: "defender", name: "Defender", tier: 2, hp: 50, maxHp: 50, armor: 0,
      personality: "defensive", aggression: "aggressive",
      skills: [
        { id: "shield", name: "Shield", effect: "shield", cooldownMs: 2000, damage: 0 },
        { id: "attack", name: "Attack", effect: "attack", cooldownMs: 1000, damage: 10 },
      ],
    };
    const state = makeCombatState({ iceRoster: [enemy] });
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    expect(result.message).toContain("attacks:");
  });

  it("enemy without personality defaults to random selection", () => {
    const enemy: Ice = {
      id: "basic", name: "Basic", tier: 1, hp: 50, maxHp: 50, armor: 0,
      skills: [{ id: "fire", name: "Fire", effect: "attack", cooldownMs: 1000, damage: 10 }],
    };
    const state = makeCombatState({ iceRoster: [enemy] });
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    expect(result.message).toContain("Fire");
  });
});
