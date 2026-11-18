import { describe, it, expect } from "vitest";
import { makeInitialState, stateToSaveSlot, slotToGameState } from "../src/core/state";
import { loadMissionsCatalog, loadProgramsCatalog, loadIceCatalog } from "../src/core/data_loaders";
import missionsData from "../src/data/missions.json";
import iceTypesData from "../src/data/ice_types.json";
import programsData from "../src/data/programs.json";

// Validate JSON data once at module load; throws if schema drifts.
// (data_loaders.test.ts already asserts each catalog loads clean.)
const missions = loadMissionsCatalog(missionsData);
const programs = loadProgramsCatalog(programsData);
const iceTypes = loadIceCatalog(iceTypesData);

function loadFirstNDeck(n: number) {
  const ids = Object.keys(programs).sort().slice(0, n);
  return ids.map((id) => programs[id]!);
}

describe("save/load round-trip", () => {
  it("GameState -> SaveSlot -> GameState preserves player HP", () => {
    const mission = missions[0]!;
    const ice = Object.values(iceTypes)[0]!;
    const state = makeInitialState(mission, ice, loadFirstNDeck(5));
    const damaged = { ...state, player: { ...state.player, hp: 42 } };
    const slot = stateToSaveSlot(damaged);
    expect(slot.playerHp).toBe(42);
    const restored = slotToGameState(slot, missions, programs, ice);
    expect(restored).not.toBeNull();
    expect(restored!.player.hp).toBe(42);
  });

  it("returns null when mission id no longer exists in catalog", () => {
    const mission = missions[0]!;
    const ice = Object.values(iceTypes)[0]!;
    const state = makeInitialState(mission, ice, loadFirstNDeck(5));
    const slot = stateToSaveSlot(state);
    (slot as { missionId: string }).missionId = "deleted_mission";
    const restored = slotToGameState(slot, missions, programs, ice);
    expect(restored).toBeNull();
  });

  it("restored deck contains all saved program ids", () => {
    const mission = missions[0]!;
    const ice = Object.values(iceTypes)[0]!;
    const state = makeInitialState(mission, ice, loadFirstNDeck(5));
    const expectedIds = state.deck.map((p) => p.id).sort();
    const slot = stateToSaveSlot(state);
    const restored = slotToGameState(slot, missions, programs, ice);
    expect(restored).not.toBeNull();
    const restoredIds = restored!.deck.map((p) => p.id).sort();
    expect(restoredIds).toEqual(expectedIds);
  });
});
