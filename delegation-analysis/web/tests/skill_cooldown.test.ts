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
  const mockIce: Ice = { id: "enemy1", name: "Enemy", tier: 1, hp: 50, maxHp: 50, armor: 0 };
  const state = makeInitialState(mockMission, mockIce, [mockProgram]);
  return {
    ...state,
    phase: "combat" as const,
    runPhase: "combat" as const,
    lastEnemyAttackMs: 0,
    dixieLastAttackMs: Date.now(),
    skillCooldowns: {},
    ...overrides,
  };
}

const makeIceWithSkills = (name: string, hp: number, skills: Array<{ id: string; name: string; cooldownMs: number; damage: number }>): Ice => {
  const base: Ice = {
    id: name.toLowerCase().replace(/\s/g, "_"),
    name,
    tier: 2,
    hp,
    maxHp: 100,
    armor: 0,
  };
  return Object.assign(base, { skills });
};

describe("skill cooldown system", () => {
  beforeEach(() => {
    vi.spyOn(Math, "random").mockReturnValue(0.01);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("enemy uses skill when available and not on cooldown", () => {
    const enemy = makeIceWithSkills("Caster", 50, [
      { id: "fireball", name: "Fireball", cooldownMs: 2000, damage: 15 },
    ]);
    const state = makeCombatState({
      iceRoster: [enemy],
      activeIceIndex: 0,
      skillCooldowns: {},
    });
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    expect(result.message).toContain("Fireball");
  });

  it("enemy auto-attacks when skill is on cooldown", () => {
    const enemy = makeIceWithSkills("Caster", 50, [
      { id: "fireball", name: "Fireball", cooldownMs: 5000, damage: 15 },
    ]);
    const state = makeCombatState({
      iceRoster: [enemy],
      activeIceIndex: 0,
      skillCooldowns: { caster_fireball: 5000 },
    });
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    expect(result.message).toContain("attacks:");
  });

  it("cooldown decreases over time", () => {
    const enemy = makeIceWithSkills("Caster", 50, [
      { id: "fireball", name: "Fireball", cooldownMs: 2000, damage: 15 },
    ]);
    const state = makeCombatState({
      iceRoster: [enemy],
      activeIceIndex: 0,
      skillCooldowns: { caster_fireball: 3000 },
      lastEnemyAttackMs: Date.now() - 2000,
    });
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    expect(result.skillCooldowns["caster_fireball"]).toBeLessThan(3000);
    expect(result.message).toContain("attacks:");
  });

  it("enemy without skills always auto-attacks", () => {
    const enemy: Ice = { id: "basic", name: "Basic", tier: 1, hp: 50, maxHp: 50, armor: 0 };
    const state = makeCombatState({
      iceRoster: [enemy],
      activeIceIndex: 0,
      skillCooldowns: {},
    });
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    expect(result.message).toContain("attacks:");
  });
});
