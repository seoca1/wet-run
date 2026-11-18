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

describe("LOOT advancement debug", () => {
  it("debug: trace transitions at node 1", () => {
    const mission = Object.values(missionsData)[0]!;
    const iceTypes = iceTypesData as unknown as Record<string, Ice>;
    const programs = programsData as unknown as Record<string, Program>;
    const ice = Object.values(iceTypes)[0]!;
    let state = makeInitialState(mission as any, ice as any, loadDeck(programs));

    state = { ...state, currentNodeIndex: 1 };
    console.log("STEP0 deck=" + JSON.stringify(state.deck.map(p => p.id)));
    console.log("STEP0 iceRoster=" + JSON.stringify(state.iceRoster.map(i => ({id: i.id, hp: i.hp}))));

    state = applyAction(state, { type: "confirm" });
    console.log("STEP1 runPhase=" + state.runPhase + " phase=" + state.phase);

    state = applyAction(state, { type: "confirm" });
    console.log("STEP1b runPhase=" + state.runPhase + " phase=" + state.phase);

    state = {
      ...state,
      iceRoster: state.iceRoster.map((i) => ({ ...i, hp: 0 })),
    };
    console.log("STEP2 iceHps=" + JSON.stringify(state.iceRoster.map(i => i.hp)));

    state = applyAction(state, { type: "use_program", programId: "backdoor" });
    console.log("STEP3 runPhase=" + state.runPhase + " phase=" + state.phase + " message=" + state.message);
    console.log("STEP3 iceHps=" + JSON.stringify(state.iceRoster.map(i => i.hp)));
    console.log("STEP3 activeIceIndex=" + state.activeIceIndex + " iceRoster.length=" + state.iceRoster.length);
    console.log("STEP3 deck.length=" + state.deck.length);
    expect(state.runPhase).toBe("loot");
  });
});

