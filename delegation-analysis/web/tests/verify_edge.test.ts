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

describe("Edge: meaningful feedback (not vacuous test)", () => {
  it("select_program in matrix phase changes message meaningfully", () => {
    const mission = Object.values(missionsData)[0]!;
    const iceTypes = iceTypesData as unknown as Record<string, Ice>;
    const programs = programsData as unknown as Record<string, Program>;
    const ice = Object.values(iceTypes)[0]!;
    const state = makeInitialState(mission as any, ice as any, loadDeck(programs));
    const before = state.message;
    expect(before, "initial message should be defined").toBeDefined();
    const result = applyAction(state, { type: "select_program", handIndex: 1 });
    expect(result.message).not.toBe(before);
    expect(result.message).toMatch(/combat|matrix/i);
  });

  it("select_program in approach phase gives meaningful feedback", () => {
    const mission = Object.values(missionsData)[0]!;
    const iceTypes = iceTypesData as unknown as Record<string, Ice>;
    const programs = programsData as unknown as Record<string, Program>;
    const ice = Object.values(iceTypes)[0]!;
    let state = makeInitialState(mission as any, ice as any, loadDeck(programs));
    state = { ...state, currentNodeIndex: 1 };
    state = applyAction(state, { type: "confirm" }); // matrix → approach
    expect(state.phase).toBe("approach");
    const before = state.message;
    const result = applyAction(state, { type: "select_program", handIndex: 1 });
    expect(result.message).not.toBe(before);
  });

  it("select_program in menu phase gives meaningful feedback", () => {
    const mission = Object.values(missionsData)[0]!;
    const iceTypes = iceTypesData as unknown as Record<string, Ice>;
    const programs = programsData as unknown as Record<string, Program>;
    const ice = Object.values(iceTypes)[0]!;
    const state = makeInitialState(mission as any, ice as any, loadDeck(programs));
    expect(state.phase).toBe("menu");
    const before = state.message;
    const result = applyAction(state, { type: "select_program", handIndex: 1 });
    expect(result.message).not.toBe(before);
  });
});
