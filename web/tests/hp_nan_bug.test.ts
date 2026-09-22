import { describe, expect, it } from "vitest";
import { applyAction, makeInitialState, buildHudLines } from "../src/core/state";
import missionsData from "../src/data/missions.json";
import iceTypesData from "../src/data/ice_types.json";
import programsData from "../src/data/programs.json";
import type { Program } from "../src/core/types";

/** Mirror of main.ts loadDeck — programs.json is keyed-by-id but values lack `id`,
 * and use the legacy `ap_cost` field where the TS Program type expects `cost`. */
function loadDeck(
  programs: Readonly<Record<string, Program>>,
  count = 5,
): ReadonlyArray<Program> {
  const ids = Object.keys(programs).sort().slice(0, count);
  return ids
    .map((id) => {
      const p = programs[id];
      if (!p) return undefined;
      const apCost = (p as { ap_cost?: number }).ap_cost;
      return {
        ...p,
        id,
        ...(apCost !== undefined && p.cost === undefined ? { cost: apCost } : {}),
      } as Program;
    })
    .filter((p): p is Program => p !== undefined);
}

/** Mirror of main.ts loadIce normalization — ice_types.json uses `defense` where
 * the TS Ice type expects `armor`. Without this, combat math produces NaN HP. */
function normalizeIce(raw: any): any {
  const defense = raw.defense;
  if (defense !== undefined && raw.armor === undefined) {
    return { ...raw, armor: defense };
  }
  return raw;
}

describe("HP NaN/100 regression (2026-09-19)", () => {
  it("combat HUD never renders NaN after repeated use_program", () => {
    const mission = Object.values(missionsData)[0]!;
    const iceTypes = iceTypesData as unknown as Record<string, any>;
    const programs = programsData as unknown as Record<string, Program>;
    const ice = normalizeIce(Object.values(iceTypes)[0]!);
    const deck = loadDeck(programs, 5);

    let state = makeInitialState(mission as any, ice as any, deck);
    const iceNodeIdx = state.matrix!.nodes.findIndex((n) => n.iceIds.length > 0);
    expect(iceNodeIdx).toBeGreaterThanOrEqual(0);
    for (let i = 0; i < iceNodeIdx; i++) {
      state = applyAction(state, { type: "move_south" });
    }
    state = applyAction(state, { type: "confirm" });
    expect(state.runPhase).toBe("combat");

    state = applyAction(state, { type: "confirm" });
    expect(state.phase).toBe("combat");

    let combatCount = 0;
    while (state.runPhase === "combat" && combatCount < 10) {
      const prog = state.deck[0];
      if (!prog) break;
      state = applyAction(state, { type: "use_program", programId: prog.id });
      combatCount++;
      if (!Number.isFinite(state.player.hp) || !Number.isFinite(state.player.alarm)) {
        const hud = buildHudLines(state);
        throw new Error(`NaN at step ${combatCount}: hp=${state.player.hp} alarm=${state.player.alarm} hud=${JSON.stringify(hud)}`);
      }
    }
  });

  it("buildHudLines must never contain NaN after a full combat run", () => {
    const mission = Object.values(missionsData)[0]!;
    const iceTypes = iceTypesData as unknown as Record<string, any>;
    const programs = programsData as unknown as Record<string, Program>;
    const ice = normalizeIce(Object.values(iceTypes)[0]!);
    const deck = loadDeck(programs, 5);

    let state = makeInitialState(mission as any, ice as any, deck);
    const iceNodeIdx = state.matrix!.nodes.findIndex((n) => n.iceIds.length > 0);
    expect(iceNodeIdx).toBeGreaterThanOrEqual(0);
    for (let i = 0; i < iceNodeIdx; i++) {
      state = applyAction(state, { type: "move_south" });
    }
    state = applyAction(state, { type: "confirm" });
    state = applyAction(state, { type: "confirm" });
    expect(state.phase).toBe("combat");

    let combatCount = 0;
    while (state.runPhase === "combat" && combatCount < 15) {
      const prog = state.deck[0];
      if (!prog) break;
      state = applyAction(state, { type: "use_program", programId: prog.id });
      combatCount++;
    }

    const hud = buildHudLines(state);
    for (const line of hud) {
      expect(line).not.toContain("NaN");
    }
  });
});
