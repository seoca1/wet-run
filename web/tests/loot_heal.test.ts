import { describe, it, expect } from "vitest";
import { applyAction, makeInitialState } from "../src/core/state/state";
import { breachEncounter } from "./encounter_test_helpers";
import missionsData from "../src/data/missions.json";
import iceTypesData from "../src/data/ice_types.json";
import programsData from "../src/data/programs.json";
import type { Program, Ice } from "../src/core/types";
import { lootHealPctForGrade } from "../src/core/state/loot_heal";
import { missionGradeOf } from "../src/core/combat/ice_scaling";

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

describe("Bug #7 regression: applyLootAction heals player on advance", () => {
  it("heals the grade's share of maxHp when advancing from LOOT (ADR-0280)", () => {
    const mission = Object.values(missionsData)[0]!;
    const iceTypes = iceTypesData as unknown as Record<string, Ice>;
    const programs = programsData as unknown as Record<string, Program>;
    const ice = Object.values(iceTypes)[0]!;
    let state = makeInitialState(mission as any, ice as any, loadDeck(programs));

    state = { ...state, currentNodeIndex: 1 };
    state = breachEncounter(state);
    state = applyAction(state, { type: "confirm" });
    state = {
      ...state,
      iceRoster: state.iceRoster.map((i) => ({ ...i, hp: 0 })),
      player: { ...state.player, hp: 50 },
    };
    state = applyAction(state, { type: "use_program", programId: state.deck[0]?.id ?? "strike" });
    expect(state.runPhase).toBe("loot");
    expect(state.player.hp).toBe(50);

    const damagedState = { ...state, player: { ...state.player, hp: 50 } };
    const advanced = applyAction(damagedState, { type: "confirm" });
    // ADR-0280: the share scales with the mission grade (a grade-5 mission is
    // 7.4 encounters long, a flat 15% does not fit it).
    const expectedHeal = Math.min(
      damagedState.player.maxHp,
      50 +
        Math.floor(
          damagedState.player.maxHp *
            (lootHealPctForGrade(missionGradeOf(mission as never)) / 100),
        ),
    );
    expect(advanced.runPhase).toBe("matrix");
    expect(advanced.player.hp).toBe(expectedHeal);
  });

  it("HEAL is capped at maxHp (does not overflow)", () => {
    const mission = Object.values(missionsData)[0]!;
    const iceTypes = iceTypesData as unknown as Record<string, Ice>;
    const programs = programsData as unknown as Record<string, Program>;
    const ice = Object.values(iceTypes)[0]!;
    let state = makeInitialState(mission as any, ice as any, loadDeck(programs));

    state = { ...state, currentNodeIndex: 1, runPhase: "loot", phase: "victory", message: "test" };
    const nearFullHp = Math.floor(state.player.maxHp * 0.95);
    const advanced = applyAction({ ...state, player: { ...state.player, hp: nearFullHp } }, { type: "confirm" });
    expect(advanced.player.hp).toBe(state.player.maxHp);
  });
});
