import { describe, it, expect } from "vitest";
import { applyAction, makeInitialState } from "../src/core/state";
import missionsData from "../src/data/missions.json";
import iceTypesData from "../src/data/ice_types.json";
import programsData from "../src/data/programs.json";
import type { Program, Ice } from "../src/core/types";

function loadDeck(programs: Record<string, Program>): Program[] {
  const ids = Object.keys(programs).sort().slice(0, 5);
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

describe("Bug #8: empty deck feedback", () => {
  it("pressing use_program with empty deck shows user-visible feedback", () => {
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
    // Trigger loot transition with all cards in deck
    state = applyAction(state, { type: "use_program", programId: state.deck[0]?.id ?? "strike" });
    expect(state.runPhase).toBe("loot");

    // Now manually drain the deck (simulating post-LOOT scenario)
    state = {
      ...state,
      deck: [],
      drawPile: [],
      discardPile: [],
    };

    // Test all hand index attempts
    const beforeMessage = state.message;
    const result1 = applyAction(state, { type: "select_program", handIndex: 1 });
    const result2 = applyAction(state, { type: "select_program", handIndex: 5 });
    const result3 = applyAction(state, { type: "use_program", programId: "nonexistent" });

    // All three should give user-visible feedback (not silent)
    expect(result1.message, "select_program handIndex=1 should produce feedback when deck empty").not.toBe(beforeMessage);
    expect(result2.message, "select_program handIndex=5 should produce feedback when deck empty").not.toBe(beforeMessage);
    expect(result3.message, "use_program with unknown id should produce feedback when deck empty").not.toBe(beforeMessage);
  });
});
