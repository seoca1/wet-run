import { describe, it, expect } from "vitest";
import { applyAction, makeInitialState } from "../src/core/state";
import missionsData from "../src/data/missions.json";
import iceTypesData from "../src/data/ice_types.json";
import programsData from "../src/data/programs.json";
import type { Program, Ice } from "../src/core/types";

function loadDeck(programs: Record<string, Program>, count = 5): Program[] {
  const ids = Object.keys(programs).sort().slice(0, count);
  return ids
    .map((id) => {
      const p = programs[id];
      if (!p) return undefined;
      const apCost = (p as unknown as { ap_cost?: number }).ap_cost;
      return {
        ...p,
        id,
        ...(apCost !== undefined && p.cost === undefined ? { cost: apCost } : {}),
      } as Program;
    })
    .filter((p): p is Program => p !== undefined);
}

describe("LOOT advancement (Bug #3 regression: linear progression)", () => {
  it("regression: LOOT advance does NOT move player backwards", () => {
    const mission = Object.values(missionsData)[0]!;
    const iceTypes = iceTypesData as unknown as Record<string, Ice>;
    const programs = programsData as unknown as Record<string, Program>;
    const ice = Object.values(iceTypes)[0]!;
    let state = makeInitialState(mission as any, ice as any, loadDeck(programs));

    state = { ...state, currentNodeIndex: 1 };
    state = applyAction(state, { type: "confirm" });
    state = applyAction(state, { type: "confirm" });
    state = {
      ...state,
      iceRoster: state.iceRoster.map((i) => ({ ...i, hp: 0 })),
    };

    const fallbackId = state.deck[0]?.id ?? "";
    if (fallbackId) {
      state = applyAction(state, { type: "use_program", programId: fallbackId });
    }
    expect(state.runPhase).toBe("loot");

    const beforeIdx = state.currentNodeIndex;
    state = applyAction(state, { type: "confirm" });
    expect(state.runPhase).toBe("matrix");
    expect(state.currentNodeIndex).not.toBe(0);
    expect(state.currentNodeIndex).toBeGreaterThanOrEqual(beforeIdx);
  });

  it("Bug #4 regression: use_program during approach does NOT silently consume deck", () => {
    const mission = Object.values(missionsData)[0]!;
    const iceTypes = iceTypesData as unknown as Record<string, Ice>;
    const programs = programsData as unknown as Record<string, Program>;
    const ice = Object.values(iceTypes)[0]!;
    let state = makeInitialState(mission as any, ice as any, loadDeck(programs));

    const initialDeckLen = state.deck.length;
    const initialFirstId = state.deck[0]?.id;
    state = { ...state, currentNodeIndex: 1 };
    state = applyAction(state, { type: "confirm" });
    expect(state.phase).toBe("approach");
    expect(state.runPhase).toBe("combat");

    state = applyAction(state, { type: "use_program", programId: initialFirstId ?? "strike" });

    expect(state.deck.length, "deck slot must NOT be consumed during approach").toBe(initialDeckLen);
    expect(state.deck[0]?.id, "first program should remain unchanged").toBe(initialFirstId);
    expect(state.phase).toBe("approach");
  });
});

