import { describe, it, expect } from "vitest";
import { applyAction, makeInitialState } from "../src/core/state";
import missionsData from "../src/data/missions.json";
import iceTypesData from "../src/data/ice_types.json";
import programsData from "../src/data/programs.json";
import type { Program, Ice } from "../src/core/types";

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

describe("Edge case (extended): alarm cap boundary", () => {
  it("program that would push alarm strictly above 100 is rejected, alarm preserved", () => {
    const mission = Object.values(missionsData)[0]!;
    const iceTypes = iceTypesData as unknown as Record<string, Ice>;
    const programs = programsData as unknown as Record<string, Program>;
    const ice = Object.values(iceTypes)[0]!;
    const deck = loadDeck(programs, 5);

    let state = makeInitialState(mission as any, ice as any, deck);
    state = { ...state, currentNodeIndex: 1 };
    state = applyAction(state, { type: "confirm" });
    state = applyAction(state, { type: "confirm" });
    expect(state.runPhase).toBe("combat");

    // Force alarm to 99 — one cost-3 program would push to 101 (> 100) and must be rejected.
    state = { ...state, player: { ...state.player, alarm: 99 } };
    const barrier = state.deck.find((p) => p.cost === 3) ?? state.deck[0];
    expect(barrier, "deck must contain a 3-cost program to bound the test").toBeDefined();

    const alarmBefore = state.player.alarm;
    const hpBefore = state.player.hp;
    const deckLenBefore = state.deck.length;
    const discardBefore = state.discardPile.length;

    const result = applyAction(state, { type: "use_program", programId: barrier!.id });

    // Rejection path: alarm preserved, deck untouched, message indicates cap.
    expect(result.player.alarm, "alarm must not overflow past 100").toBe(alarmBefore);
    expect(result.player.alarm).toBeLessThanOrEqual(100);
    expect(result.player.hp, "hp must not change on rejection").toBe(hpBefore);
    expect(result.deck.length, "deck must not lose card on rejection").toBe(deckLenBefore);
    expect(result.discardPile.length, "discard pile must not gain card on rejection").toBe(discardBefore);
    expect(result.message).toMatch(/alarm|fail/i);
  });
});

describe("Edge case (extended): matrix→combat state preservation", () => {
  it("enter ICE node, then transition approach→combat preserves player HP, alarm, deck, node index", () => {
    const mission = Object.values(missionsData)[0]!;
    const iceTypes = iceTypesData as unknown as Record<string, Ice>;
    const programs = programsData as unknown as Record<string, Program>;
    const ice = Object.values(iceTypes)[0]!;
    const deck = loadDeck(programs, 5);

    const initial = makeInitialState(mission as any, ice as any, deck);

    // Find the index of the first ICE-bearing node, walk there via move_south.
    const iceNodeIdx = initial.matrix!.nodes.findIndex((n) => n.iceIds.length > 0);
    expect(iceNodeIdx).toBeGreaterThanOrEqual(0);

    let state = initial;
    for (let i = 0; i < iceNodeIdx; i++) {
      state = applyAction(state, { type: "move_south" });
    }
    // enter ICE-bearing node: matrix.confirm transitions to approach/combat.
    state = applyAction(state, { type: "confirm" });
    expect(state.runPhase).toBe("combat");
    expect(state.phase).toBe("approach");

    // Mutate player state to distinctive values, then confirm the approach phase.
    state = {
      ...state,
      player: { ...state.player, alarm: 42 },
    };
    const alarmAtApproach = state.player.alarm;
    const hpAtApproach = state.player.hp;
    const deckLenAtApproach = state.deck.length;
    const nodeIdxAtApproach = state.currentNodeIndex;

    const inCombat = applyAction(state, { type: "confirm" });
    expect(inCombat.phase).toBe("combat");

    // Player state must be carried into combat unchanged.
    expect(inCombat.player.hp, "hp must survive approach→combat transition").toBe(hpAtApproach);
    expect(inCombat.player.alarm, "alarm must survive approach→combat transition").toBe(alarmAtApproach);
    expect(inCombat.deck.length, "deck size must survive approach→combat transition").toBe(deckLenAtApproach);
    expect(inCombat.currentNodeIndex, "currentNodeIndex must survive approach→combat transition").toBe(nodeIdxAtApproach);
  });
});
