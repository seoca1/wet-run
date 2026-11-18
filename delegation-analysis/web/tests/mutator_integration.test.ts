import { describe, it, expect } from "vitest";
import { applyAction, makeInitialState } from "../src/core/state.ts";
import type { GameState, Ice, Mission, Program } from "../src/core/types.ts";
import type { RunMutator } from "../src/core/run_mutators.ts";
import { applyStatus, applyTickEffects } from "../src/core/status.ts";

function makeCombatState(mutators: RunMutator[] = []): GameState {
  const mockMission: Mission = {
    id: "test",
    title: "Test",
    fixer: "test",
    arc: 1,
    zone: "test",
    grade_min: 1,
    grade_max: 1,
    rewards: { credits: 10, materials: {} },
    grade: 1,
    seed: 42,
  };
  const mockProgram: Program = {
    id: "p1",
    name: "Atk",
    tier: 1,
    cost: 5,
    effect: "damage",
    description: "test",
    aoe: false,
  };
  const mockIce: Ice = {
    id: "enemy1",
    name: "Enemy",
    tier: 1,
    hp: 50,
    maxHp: 50,
    armor: 0,
    personality: "aggressive",
    aggression: "standard",
    skills: [],
  };
  const state = makeInitialState(mockMission, mockIce, [mockProgram], [], mutators);
  return {
    ...state,
    iceRoster: [mockIce],
    activeIceIndex: 0,
    phase: "combat" as const,
    runPhase: "combat" as const,
    lastEnemyAttackMs: 0,
    dixieLastAttackMs: 0,
    skillCooldowns: {},
  };
}

describe("mutator integration", () => {
  it("double_alarm increases alarm cost", () => {
    const state = makeCombatState(["double_alarm"]);
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    expect(result.player.alarm).toBe(10);
  });

  it("active mutators are tracked in state", () => {
    const state = makeCombatState(["low_hp", "no_heal"]);
    expect(state.activeMutators).toContain("low_hp");
    expect(state.activeMutators).toContain("no_heal");
  });

  it("no mutators by default", () => {
    const state = makeCombatState([]);
    expect(state.activeMutators).toHaveLength(0);
  });

  it("normal alarm cost without double_alarm", () => {
    const state = makeCombatState([]);
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    expect(result.player.alarm).toBe(5);
  });

  it("activeMutators is frozen array", () => {
    const state = makeCombatState(["ice_x2"]);
    expect(Object.isFrozen(state.activeMutators)).toBe(true);
  });

  it("makeInitialState accepts empty mutators array", () => {
    const mockMission: Mission = {
      id: "test",
      title: "Test",
      fixer: "test",
      arc: 1,
      zone: "test",
      grade_min: 1,
      grade_max: 1,
      rewards: { credits: 10, materials: {} },
      grade: 1,
      seed: 42,
    };
    const mockIce: Ice = {
      id: "enemy1",
      name: "Enemy",
      tier: 1,
      hp: 50,
      maxHp: 50,
      armor: 0,
      personality: "aggressive",
      aggression: "standard",
      skills: [],
    };
    const mockProgram: Program = {
      id: "p1",
      name: "Atk",
      tier: 1,
      cost: 5,
      effect: "damage",
      description: "test",
      aoe: false,
    };
    const state = makeInitialState(mockMission, mockIce, [mockProgram], [], []);
    expect(state.activeMutators).toHaveLength(0);
  });

  it("makeInitialState defaults to empty mutators when omitted", () => {
    const mockMission: Mission = {
      id: "test",
      title: "Test",
      fixer: "test",
      arc: 1,
      zone: "test",
      grade_min: 1,
      grade_max: 1,
      rewards: { credits: 10, materials: {} },
      grade: 1,
      seed: 42,
    };
    const mockIce: Ice = {
      id: "enemy1",
      name: "Enemy",
      tier: 1,
      hp: 50,
      maxHp: 50,
      armor: 0,
      personality: "aggressive",
      aggression: "standard",
      skills: [],
    };
    const mockProgram: Program = {
      id: "p1",
      name: "Atk",
      tier: 1,
      cost: 5,
      effect: "damage",
      description: "test",
      aoe: false,
    };
    const state = makeInitialState(mockMission, mockIce, [mockProgram]);
    expect(state.activeMutators).toHaveLength(0);
  });

  it("no_heal disables regen healing for player", () => {
    const state = makeCombatState(["no_heal"]);
    const stateWithRegen = applyStatus(state, "player", "regen", 3, 5, { healPerTick: 10 });
    const tickResult = applyTickEffects(stateWithRegen);
    expect(tickResult.healPlayer).toBe(0);
  });

  it("regen works normally without no_heal", () => {
    const state = makeCombatState([]);
    const stateWithRegen = applyStatus(state, "player", "regen", 3, 5, { healPerTick: 10 });
    const tickResult = applyTickEffects(stateWithRegen);
    expect(tickResult.healPlayer).toBe(10);
  });

  it("no_heal disables regen healing for ice", () => {
    const state = makeCombatState(["no_heal"]);
    const stateWithRegen = applyStatus(state, "ice", "regen", 3, 5, { healPerTick: 8 });
    const tickResult = applyTickEffects(stateWithRegen);
    expect(tickResult.healIce).toBe(0);
  });
});
