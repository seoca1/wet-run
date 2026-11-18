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

describe("jack_out in combat (Bug regression: runPhase must be 'dead')", () => {
  it("jack_out from combat sets runPhase to 'dead', not 'combat'", () => {
    const mission = Object.values(missionsData)[0]!;
    const iceTypes = iceTypesData as unknown as Record<string, Ice>;
    const programs = programsData as unknown as Record<string, Program>;
    const ice = Object.values(iceTypes)[0]!;
    let state = makeInitialState(mission as any, ice as any, loadDeck(programs));

    state = { ...state, currentNodeIndex: 1 };
    state = applyAction(state, { type: "confirm" });
    state = applyAction(state, { type: "confirm" });
    expect(state.runPhase).toBe("combat");
    expect(state.phase).toBe("combat");

    const after = applyAction(state, { type: "jack_out" });
    expect(after.runPhase, "runPhase must be 'dead' for consistent state machine").toBe("dead");
    expect(after.phase).toBe("defeat");
    expect(after.message).toBe("Jacked out — mission failed");
  });
});
