/**
 * ADR-0287 — the credit sink that grants no power: route intel.
 *
 * Four power-granting sinks were measured and rejected (ADR-0282, 0284, 0285,
 * 0286) because the difficulty curve is fitted to its targets and has no room. A
 * sink that grants INFORMATION can be added without touching it, and PROBE
 * already sets the precedent that the game sells threat knowledge for COST.
 *
 * What the player buys is the ICE composition of the routes ahead: before paying
 * the card says `route: 2 fights · 250cr`, after paying it names them.
 */
import { describe, expect, it, beforeEach, afterEach } from "vitest";
import {
  routePreview,
  routePreviewLine,
} from "../src/core/dungeon/route_preview";
import { intelTargets, lootIntelPrice } from "../src/core/state/loot_choice";
import { applyAction, makeInitialState, slotToGameState, stateToSaveSlot } from "../src/core/state/state";
import { loadIceCatalog, loadMissionsCatalog, loadProgramsCatalog } from "../src/core/data_loaders";
import type { GameState, Matrix, MatrixNode } from "../src/core/types";
import { startingDeck } from "../src/core/state/starting_deck";
import iceJson from "../src/data/ice_types.json" with { type: "json" };
import missionsJson from "../src/data/missions.json" with { type: "json" };
import programsJson from "../src/data/programs.json" with { type: "json" };

const ice = loadIceCatalog(iceJson);
const programs = loadProgramsCatalog(programsJson);
const missions = loadMissionsCatalog(missionsJson);

function node(
  id: number,
  adjacent: readonly number[],
  iceIds: readonly string[] = [],
  credits = 0,
): MatrixNode {
  return {
    id,
    zone: "mid",
    iceIds,
    iceHp: [],
    reward: { credits },
    isBoss: false,
    adjacent,
  };
}

/** 0 -> {1 ICE, 2 empty}; 2 -> 5 boss; 1 -> 3 empty; 3 -> 5 boss. */
function branching(): Matrix {
  return {
    startNode: 0,
    bossNode: 5,
    grade: 3,
    nodes: [
      node(0, [1, 2]),
      node(1, [0, 3], ["wisp"], 75),
      node(2, [0, 4, 5]),
      node(3, [1, 5]),
      node(4, [2]),
      { ...node(5, [2, 3], ["wintermute"], 175), isBoss: true },
    ],
  };
}

describe("ADR-0287 · route intel", () => {
  it("counts the route until it is paid for, then names it", () => {
    // Given: the branching graph, unpurchased.
    const before = routePreview(branching(), [], [], 2);

    // Then: a count, and no names.
    expect(before.knownIce).toEqual([]);
    expect(routePreviewLine(before)).toContain("to boss");

    // When: the same route with the intel bought.
    const after = routePreview(branching(), [], [], 2, [1, 5]);

    // Then: the ICE the runner is walking into are named.
    expect([...after.knownIce].sort()).toEqual(["wintermute", "wisp"]);
    expect(routePreviewLine(after)).toContain("wisp");
  });

  it("reveals only unresolved encounters", () => {
    // Given: one cleared and one bypassed.
    const targets = intelTargets(branching().nodes, [1], [5]);

    // Then: nothing left to buy knowledge of.
    expect(targets).toEqual([]);
    expect(intelTargets(branching().nodes, [], [])).toEqual([1, 5]);
  });

  it("prices the intel by grade, and cheaply", () => {
    // Given / When / Then: information is not sold at power prices — the
    // cheapest tier is a rounding error against a mission reward.
    expect(lootIntelPrice(1)).toBeLessThan(100);
    expect(lootIntelPrice(6)).toBeGreaterThanOrEqual(lootIntelPrice(1));
  });
});

describe("ADR-0287 · the bought intel survives a save", () => {
  beforeEach(() => localStorage.removeItem("wetrun_prep_wallet"));
  afterEach(() => localStorage.removeItem("wetrun_prep_wallet"));

  it("round-trips through the save slot", () => {
    // Given: a run on a loot screen with credits to spend.
    const mission = Object.values(missions).find((m) => m.id === "first_jack");
    expect(mission).toBeDefined();
    const initial = makeInitialState(
      mission as never,
      Object.values(ice)[0] as never,
      startingDeck(programs, "novice"),
    );
    const atLoot: GameState = {
      ...initial,
      runPhase: "loot" as const,
      phase: "victory" as const,
      player: { ...initial.player, credits: 500 },
      matrix: branching(),
      currentNodeIndex: 2,
      clearedEncounterNodes: [],
      bypassedEncounterNodes: [],
    };

    // When: the intel is bought and the run is saved.
    const bought = applyAction(atLoot, {
      type: "select_program",
      handIndex: 5,
    });
    expect(bought.intelNodes?.length ?? 0).toBeGreaterThan(0);
    const slot = stateToSaveSlot(bought);
    const restored = slotToGameState(
      slot,
      Object.values(missions),
      programs,
      Object.values(ice)[0] as never,
      ice,
    );

    // Then: the runner did not pay for knowledge the reload forgets.
    expect(restored?.intelNodes).toEqual(bought.intelNodes);
  });

  it("omits the field from an old slot's JSON (version 1 unchanged)", () => {
    // Given: the same run, no intel bought.
    const mission = Object.values(missions).find((m) => m.id === "first_jack");
    const initial = makeInitialState(
      mission as never,
      Object.values(ice)[0] as never,
      startingDeck(programs, "novice"),
    );

    // Then: no key, so an older reader sees exactly what it always did.
    expect(stateToSaveSlot(initial).intelNodes).toBeUndefined();
    expect(stateToSaveSlot(initial).version).toBe(1);
  });
});
