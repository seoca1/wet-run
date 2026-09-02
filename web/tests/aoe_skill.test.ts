import { describe, it, expect } from "vitest";
import { applyAction, makeInitialState } from "../src/core/state.ts";
import type { GameState, Ice, Mission, Program } from "../src/core/types.ts";

function makeCombatState(roster: Ice[], program: Program): GameState {
  const mockMission: Mission = {
    id: "test", title: "Test", fixer: "test", arc: 1, zone: "test",
    grade_min: 1, grade_max: 1, rewards: { credits: 10, materials: {} },
  };
  const state = makeInitialState(mockMission, roster[0], [program]);
  return { ...state, iceRoster: roster, activeIceIndex: 0, phase: "combat" as const, runPhase: "combat" as const };
}

const makeIce = (name: string, hp: number, tier: number = 1): Ice => ({
  id: name.toLowerCase().replace(/\s/g, "_"), name, tier, hp, armor: 0,
});

describe("AoE skill support", () => {
  it("damages all alive enemies when program.aoe is true", () => {
    const roster = [makeIce("Alpha", 50), makeIce("Beta", 50), makeIce("Gamma", 30)];
    const program: Program = { id: "p1", name: "AoE Blast", tier: 2, cost: 0, effect: "damage", description: "AoE", aoe: true };
    const state = makeCombatState(roster, program);
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    // All enemies should take damage
    expect(result.iceRoster[0].hp).toBeLessThan(50);
    expect(result.iceRoster[1].hp).toBeLessThan(50);
    expect(result.iceRoster[2].hp).toBeLessThan(30);
  });

  it("damages only active target when program.aoe is false", () => {
    const roster = [makeIce("Alpha", 50), makeIce("Beta", 50)];
    const program: Program = { id: "p1", name: "Single Shot", tier: 1, cost: 0, effect: "damage", description: "Single", aoe: false };
    const state = makeCombatState(roster, program);
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    // Only Alpha (index 0) should take damage
    expect(result.iceRoster[0].hp).toBeLessThan(50);
    expect(result.iceRoster[1].hp).toBe(50);
  });

  it("skips dead enemies in AoE", () => {
    const roster = [makeIce("Alpha", 0), makeIce("Beta", 50)];
    const program: Program = { id: "p1", name: "AoE", tier: 1, cost: 0, effect: "damage", description: "AoE", aoe: true };
    const state = makeCombatState(roster, program);
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    expect(result.iceRoster[0].hp).toBe(0); // still dead
    expect(result.iceRoster[1].hp).toBeLessThan(50);
  });

  it("AoE program damages target (verified by HP change)", () => {
    const roster = [makeIce("Alpha", 50)];
    const program: Program = { id: "p1", name: "Nova", tier: 1, cost: 0, effect: "damage", description: "AoE", aoe: true };
    const state = makeCombatState(roster, program);
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    expect(result.iceRoster[0].hp).toBeLessThan(50);
  });
});
