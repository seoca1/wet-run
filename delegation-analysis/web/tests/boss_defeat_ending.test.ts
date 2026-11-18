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

describe("Boss defeat transitions to ending (Bug regression)", () => {
  it("defeating boss ICE at currentNodeIndex=20 transitions runPhase to 'ending'", () => {
    const mission = Object.values(missionsData)[0]!;
    const iceTypes = iceTypesData as unknown as Record<string, Ice>;
    const programs = programsData as unknown as Record<string, Program>;
    const ice = Object.values(iceTypes)[0]!;
    const state = makeInitialState(mission as any, ice as any, loadDeck(programs));

    // Navigate to BOSS node (index 20)
    const withBoss = {
      ...state,
      currentNodeIndex: 20,
    };
    const matrix = withBoss.matrix;
    if (!matrix) throw new Error("no matrix");
    const bossNode = matrix.nodes[20];
    if (!bossNode?.isBoss) throw new Error("node 20 should be boss");

    // Confirm to enter matrix/approach
    let s = applyAction(withBoss, { type: "confirm" });
    s = applyAction(s, { type: "confirm" });
    expect(s.phase).toBe("combat");

    // Force kill boss
    s = {
      ...s,
      iceRoster: s.iceRoster.map((i) => ({ ...i, hp: 0 })),
    };
    // Trigger combat action to detect all-defeated → loot
    const deck = s.deck;
    const progId = deck[0]?.id;
    if (!progId) throw new Error("no program in deck");
    s = applyAction(s, { type: "use_program", programId: progId });

    expect(s.runPhase, "defeating boss should transition to loot").toBe("loot");

    // Confirm on loot → ending
    s = applyAction(s, { type: "confirm" });
    expect(s.runPhase, "confirming loot after boss kill should transition to ending").toBe("ending");
    expect(s.phase).toBe("victory");
  });
});
