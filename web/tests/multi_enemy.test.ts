import { describe, it, expect } from "vitest";
import { applyAction, makeInitialState, buildHudLines } from "../src/core/state.ts";
import type { GameState, Ice, Mission, Program } from "../src/core/types.ts";

function makeCombatState(roster: Ice[], activeIndex: number = 0): GameState {
  const mockMission: Mission = {
    id: "test",
    title: "Test",
    fixer: "test",
    arc: 1,
    zone: "test",
    grade_min: 1,
    grade_max: 1,
    rewards: { credits: 10, materials: {} },
  };
  const mockProgram: Program = {
    id: "p1",
    name: "Atk",
    tier: 1,
    cost: 0,
    effect: "damage",
    description: "test",
    aoe: false,
  };
  const state = makeInitialState(mockMission, roster[0], [mockProgram]);
  return { ...state, iceRoster: roster, activeIceIndex: activeIndex, phase: "combat" as const, runPhase: "combat" as const };
}

const makeIce = (name: string, hp: number, tier: number = 1): Ice => ({
  id: name.toLowerCase().replace(/\s/g, "_"),
  name,
  tier,
  hp,
  armor: 0,
});

describe("multi-enemy combat", () => {
  describe("cycle_target", () => {
    it("cycles to next alive enemy", () => {
      const roster = [makeIce("Alpha", 50), makeIce("Beta", 50), makeIce("Gamma", 50)];
      let state = makeCombatState(roster, 0);
      state = applyAction(state, { type: "cycle_target" });
      expect(state.activeIceIndex).toBe(1);
      state = applyAction(state, { type: "cycle_target" });
      expect(state.activeIceIndex).toBe(2);
      state = applyAction(state, { type: "cycle_target" });
      expect(state.activeIceIndex).toBe(0);
    });

    it("skips dead enemies", () => {
      const roster = [makeIce("Alpha", 0), makeIce("Beta", 50), makeIce("Gamma", 50)];
      let state = makeCombatState(roster, 1);
      state = applyAction(state, { type: "cycle_target" });
      expect(state.activeIceIndex).toBe(2);
      state = applyAction(state, { type: "cycle_target" });
      expect(state.activeIceIndex).toBe(1);
    });

    it("does nothing when only one alive enemy", () => {
      const roster = [makeIce("Alpha", 50), makeIce("Beta", 0)];
      const state = makeCombatState(roster, 0);
      const result = applyAction(state, { type: "cycle_target" });
      expect(result.activeIceIndex).toBe(0);
    });

    it("does nothing when all enemies dead", () => {
      const roster = [makeIce("Alpha", 0), makeIce("Beta", 0)];
      const state = makeCombatState(roster, 0);
      const result = applyAction(state, { type: "cycle_target" });
      expect(result.activeIceIndex).toBe(0);
    });
  });

  describe("buildHudLines roster display", () => {
    it("shows all enemies in roster", () => {
      const roster = [makeIce("Alpha", 50), makeIce("Beta", 30)];
      const state = makeCombatState(roster, 0);
      const lines = buildHudLines(state);
      const enemyLines = lines.filter(l => l.includes("Alpha") || l.includes("Beta"));
      expect(enemyLines.length).toBe(2);
    });

    it("marks active enemy with >", () => {
      const roster = [makeIce("Alpha", 50), makeIce("Beta", 30)];
      const state = makeCombatState(roster, 1);
      const lines = buildHudLines(state);
      const betaLine = lines.find(l => l.includes("Beta"));
      expect(betaLine).toMatch(/^>/);
    });

    it("shows DEAD for dead enemies", () => {
      const roster = [makeIce("Alpha", 0), makeIce("Beta", 30)];
      const state = makeCombatState(roster, 1);
      const lines = buildHudLines(state);
      const alphaLine = lines.find(l => l.includes("Alpha"));
      expect(alphaLine).toContain("DEAD");
    });
  });
});
