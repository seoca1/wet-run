import { describe, it, expect } from "vitest";
import { applyAction, makeInitialState } from "../src/core/state.ts";
import type { GameState, Ice, Mission, Program } from "../src/core/types.ts";

function makeCombatState(roster: Ice[], bossPhase: number = 0): GameState {
  const mockMission: Mission = {
    id: "test", title: "Test", fixer: "test", arc: 1, zone: "test",
    grade_min: 1, grade_max: 1, rewards: { credits: 10, materials: {} },
  };
  const mockProgram: Program = {
    id: "p1", name: "Atk", tier: 1, cost: 0, effect: "damage", description: "test", aoe: false,
  };
  const state = makeInitialState(mockMission, roster[0], [mockProgram]);
  return {
    ...state,
    iceRoster: roster,
    activeIceIndex: 0,
    phase: "combat" as const,
    runPhase: "combat" as const,
    bossPhase: bossPhase as any,
    lastEnemyAttackMs: 0,
    dixieLastAttackMs: Date.now(),
  };
}

const makeIce = (name: string, hp: number, tier: number = 1): Ice => ({
  id: name.toLowerCase().replace(/\s/g, "_"), name, tier, hp, maxHp: 100, armor: 0,
});

describe("boss AI overrides", () => {
  it("boss deals bonus damage in phase 2 (1.25x)", () => {
    const roster = [makeIce("Boss", 50, 3)];
    const initialState = makeCombatState(roster, 2);
    const initialHp = initialState.player.hp;
    
    const result = applyAction(initialState, { type: "use_program", programId: "p1" });
    
    const baseDamage = roster[0].tier * 3 + roster[0].armor;
    const expectedDamage = Math.floor(baseDamage * 1.25);
    const actualDamage = initialHp - result.player.hp;
    
    expect(actualDamage).toBe(expectedDamage);
    expect(result.message).toContain("attacks:");
  });

  it("boss deals bonus damage in phase 3 (1.5x) with AoE message", () => {
    const roster = [makeIce("Boss", 40, 3)];
    const initialState = makeCombatState(roster, 3);
    const initialHp = initialState.player.hp;
    
    const result = applyAction(initialState, { type: "use_program", programId: "p1" });
    
    const baseDamage = roster[0].tier * 3 + roster[0].armor;
    const expectedDamage = Math.floor(baseDamage * 1.5);
    const actualDamage = initialHp - result.player.hp;
    
    expect(actualDamage).toBe(expectedDamage);
    expect(result.message).toContain("AoE:");
    expect(result.message).toContain("(hits all!)");
  });

  it("boss deals bonus damage in phase 4 (2.0x) with AoE message", () => {
    const roster = [makeIce("Boss", 20, 3)];
    const initialState = makeCombatState(roster, 4);
    const initialHp = initialState.player.hp;
    
    const result = applyAction(initialState, { type: "use_program", programId: "p1" });
    
    const baseDamage = roster[0].tier * 3 + roster[0].armor;
    const expectedDamage = Math.floor(baseDamage * 2.0);
    const actualDamage = initialHp - result.player.hp;
    
    expect(actualDamage).toBe(expectedDamage);
    expect(result.message).toContain("AoE:");
    expect(result.message).toContain("(hits all!)");
  });

  it("phase 4 spawns minion when roster < 3", () => {
    const roster = [makeIce("Boss", 20, 3)];
    const state = makeCombatState(roster, 4);
    
    expect(state.iceRoster.length).toBe(1);
    
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    
    expect(result.iceRoster.length).toBe(2);
    const minion = result.iceRoster.find(ice => ice.name === "Drone");
    expect(minion).toBeDefined();
    expect(minion?.tier).toBe(1);
    expect(minion?.hp).toBe(30);
  });

  it("phase 4 does not spawn minion when roster >= 3", () => {
    const roster = [
      makeIce("Boss", 20, 3),
      makeIce("Minion1", 30, 1),
      makeIce("Minion2", 30, 1),
    ];
    const state = makeCombatState(roster, 4);
    
    expect(state.iceRoster.length).toBe(3);
    
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    
    expect(result.iceRoster.length).toBe(3);
  });

  it("non-boss enemies are unaffected by boss phases", () => {
    const roster = [makeIce("Minion", 50, 1)];
    const initialState = makeCombatState(roster, 3);
    const initialHp = initialState.player.hp;
    
    const result = applyAction(initialState, { type: "use_program", programId: "p1" });
    
    const expectedDamage = roster[0].tier * 3 + roster[0].armor;
    const actualDamage = initialHp - result.player.hp;
    
    expect(actualDamage).toBe(expectedDamage);
    expect(result.message).toContain("attacks:");
    expect(result.message).not.toContain("AoE:");
  });

  it("phase 1 boss deals normal damage without multiplier", () => {
    const roster = [makeIce("Boss", 80, 3)];
    const initialState = makeCombatState(roster, 1);
    const initialHp = initialState.player.hp;
    
    const result = applyAction(initialState, { type: "use_program", programId: "p1" });
    
    const expectedDamage = roster[0].tier * 3 + roster[0].armor;
    const actualDamage = initialHp - result.player.hp;
    
    expect(actualDamage).toBe(expectedDamage);
    expect(result.message).toContain("attacks:");
    expect(result.message).not.toContain("AoE:");
  });
});
