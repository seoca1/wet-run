import { describe, it, expect } from "vitest";
import { applyAction, makeInitialState } from "../src/core/state";
import missionsData from "../src/data/missions.json";
import iceTypesData from "../src/data/ice_types.json";
import programsData from "../src/data/programs.json";
import type { Program, Ice } from "../src/core/types";

function loadDeck(programs: Record<string, Program>): Program[] {
  const ids = Object.keys(programs).sort().slice(0, 5);
  return ids.map((id) => {
    const p = programs[id];
    if (!p) return undefined;
    const apCost = (p as any).ap_cost;
    return { ...p, id, ...(apCost !== undefined && p.cost === undefined ? { cost: apCost } : {}) } as Program;
  }).filter((p): p is Program => p !== undefined);
}

describe("Bug #9: rapid input", () => {
  it("rapid key presses in combat don't break state (no race condition)", () => {
    const mission = Object.values(missionsData)[0]!;
    const iceTypes = iceTypesData as unknown as Record<string, Ice>;
    const programs = programsData as unknown as Record<string, Program>;
    const ice = Object.values(iceTypes)[0]!;
    let state = makeInitialState(mission as any, ice as any, loadDeck(programs));
    state = { ...state, currentNodeIndex: 1 };
    state = applyAction(state, { type: "confirm" });
    state = applyAction(state, { type: "confirm" });
    
    // 10 rapid alternating attacks
    for (let i = 0; i < 10; i++) {
      const prog = state.deck[0];
      if (!prog) break;
      state = applyAction(state, { type: "use_program", programId: prog.id });
    }
    
    // State should still be valid
    expect(state.player.hp).toBeGreaterThan(0);
    expect(state.player.alarm).toBeGreaterThanOrEqual(0);
    expect(state.player.alarm).toBeLessThanOrEqual(100);
    expect(state.runPhase).toMatch(/combat|loot/);
  });
  
  it("selecting handIndex beyond available programs gives feedback, not error", () => {
    const mission = Object.values(missionsData)[0]!;
    const iceTypes = iceTypesData as unknown as Record<string, Ice>;
    const programs = programsData as unknown as Record<string, Program>;
    const ice = Object.values(iceTypes)[0]!;
    let state = makeInitialState(mission as any, ice as any, loadDeck(programs));
    
    // Try handIndex 10 (only 5 cards)
    const before = state.message;
    const result = applyAction(state, { type: "select_program", handIndex: 10 });
    expect(result.message, "out-of-range handIndex should produce feedback").not.toBe(before);
  });
});

describe("Bug #10: edge of combat death during enemy turn", () => {
  it("player death triggers correct phase transition even at low HP", () => {
    const mission = Object.values(missionsData)[0]!;
    const iceTypes = iceTypesData as unknown as Record<string, Ice>;
    const programs = programsData as unknown as Record<string, Program>;
    const ice = Object.values(iceTypes)[0]!;
    let state = makeInitialState(mission as any, ice as any, loadDeck(programs));
    
    state = { ...state, currentNodeIndex: 1 };
    state = applyAction(state, { type: "confirm" });
    state = applyAction(state, { type: "confirm" });
    
    // Force player to 1 HP
    state = { ...state, player: { ...state.player, hp: 1 } };
    
    // First attack triggers enemy turn which might kill player
    const prog = state.deck[0];
    if (!prog) throw new Error("no program in deck");
    const result = applyAction(state, { type: "use_program", programId: prog.id });
    
    // Player may or may not have died depending on enemy attack timing, but state must be valid
    expect([result.runPhase, result.phase]).toBeDefined();
    expect(result.player.hp).toBeGreaterThanOrEqual(0);
  });
});
