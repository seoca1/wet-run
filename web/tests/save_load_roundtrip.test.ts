import { describe, it, expect } from "vitest";
import {
  makeInitialState,
  applyAction,
  stateToSaveSlot,
  slotToGameState,
} from "../src/core/state/state";
import {
  loadMissionsCatalog,
  loadProgramsCatalog,
  loadIceCatalog,
} from "../src/core/data_loaders";
import missionsData from "../src/data/missions.json";
import iceTypesData from "../src/data/ice_types.json";
import programsData from "../src/data/programs.json";
import { save, load } from "../src/save/storage";

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
  it("keeps cleared encounters unrepeatable after storage and CONTINUE", async () => {
    // Given: the current node and a different node have already been cleared.
    const mission = missions[0];
    const ice = Object.values(iceTypes)[0];
    const initial = makeInitialState(mission, ice, loadFirstNDeck(5));
    const index =
      initial.matrix?.nodes.findIndex((node) => node.iceIds.length > 0) ?? -1;
    expect(index).toBeGreaterThanOrEqual(0);
    const state = {
      ...initial,
      currentNodeIndex: index,
      clearedEncounterNodes: [index, index + 1],
    };
    const slot = stateToSaveSlot(state);
    // When
    await save(3, slot);
    const loaded = await load(3);
    const restored =
      loaded === null ? null : slotToGameState(loaded, missions, programs, ice);
    expect(restored).not.toBeNull();
    if (!restored) return;
    const confirmed = applyAction(restored, { type: "confirm" });
    // Then
    expect(restored.clearedEncounterNodes).toEqual([index, index + 1]);
    expect(confirmed.runPhase).toBe("matrix");
    expect(confirmed.player.credits).toBe(state.player.credits);
  });

  it("loads legacy slots without encounter markers without treating visits as clears", async () => {
    // Given: old slots omit clearedEncounterNodes entirely.
    const mission = missions[0];
    const ice = Object.values(iceTypes)[0];
    const initial = makeInitialState(mission, ice, loadFirstNDeck(5));
    const slot = {
      ...stateToSaveSlot(initial),
      clearedEncounterNodes: undefined,
    };
    // When
    await save(3, slot);
    const loaded = await load(3);
    const restored =
      loaded === null ? null : slotToGameState(loaded, missions, programs, ice);
    // Then
    expect(loaded).not.toHaveProperty("clearedEncounterNodes");
    expect(restored?.clearedEncounterNodes).toEqual([]);
    expect(restored?.runPhase).toBe("matrix");
  });

  it.each([null, "1", ["1"], [-1], [1.5]])(
    "rejects malformed persisted encounter markers: %j",
    async (clearedEncounterNodes) => {
      // Given: an otherwise valid legacy-format slot with malformed markers.
      const initial = makeInitialState(
        missions[0],
        Object.values(iceTypes)[0],
        loadFirstNDeck(5),
      );
      localStorage.setItem(
        "wetrun_mvp_save_v1_slot_3",
        JSON.stringify({ ...stateToSaveSlot(initial), clearedEncounterNodes }),
      );
      // When
      const loaded = await load(3);
      // Then
      expect(loaded).toBeNull();
    },
  );

  it("loads existing SaveSlot data and resets ephemeral Dixie timing on matrix resume", async () => {
    // Given: neither Dixie field belongs to the persisted SaveSlot schema.
    const mission = missions[0];
    const ice = Object.values(iceTypes)[0];
    const state = {
      ...makeInitialState(mission, ice, loadFirstNDeck(5)),
      dixieLastAttackMs: 12345,
      dixiePlayerTurnsSinceAttack: 0,
    };
    const slot = stateToSaveSlot(state);
    // When
    await save(3, slot);
    const loaded = await load(3);
    const restored =
      loaded === null ? null : slotToGameState(loaded, missions, programs, ice);
    // Then
    expect(loaded).toEqual(slot);
    expect(slot).not.toHaveProperty("dixieLastAttackMs");
    expect(slot).not.toHaveProperty("dixiePlayerTurnsSinceAttack");
    expect(restored?.runPhase).toBe("matrix");
    expect(restored?.dixiePlayerTurnsSinceAttack).toBe(1);
    expect(restored?.dixieLastAttackMs).toBe(0);
  });

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
