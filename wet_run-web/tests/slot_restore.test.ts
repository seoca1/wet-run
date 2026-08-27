/** Tests for save/load round-trip via slotToGameState (CONTINUE option). */
import { describe, it, expect } from "vitest";
import { slotToGameState, stateToSaveSlot, makeInitialState } from "../src/core/state.ts";
import type { GameState, Ice, Mission, Program, SaveSlot } from "../src/core/types.ts";

const mockMission: Mission = {
  id: "test_mission",
  title: "Test Mission",
  fixer: "test",
  arc: 1,
  zone: "test",
  grade_min: 1,
  grade_max: 1,
  rewards: { credits: 100, materials: {} },
};

const mockIce: Ice = {
  id: "watchdog",
  name: "Watchdog",
  hp: 100,
  armor: 0,
  tier: 1,
};

const mockPrograms: Readonly<Record<string, Program>> = Object.freeze({
  strike: { id: "strike", name: "Strike", tier: 1, cost: 10, effect: "damage", description: "d" },
  shield: { id: "shield", name: "Shield", tier: 1, cost: 10, effect: "block", description: "d" },
  hack: { id: "hack", name: "Hack", tier: 1, cost: 10, effect: "debuff", description: "d" },
});

const catalog: ReadonlyArray<Mission> = [mockMission];

/** Build a mutable GameState for tests (production returns readonly state). */
function buildState(): GameState {
  const programs = Object.values(mockPrograms);
  // makeInitialState returns a frozen state; clone to allow mutation in tests.
  const state = makeInitialState(mockMission, mockIce, programs);
  return { ...state, player: { ...state.player } };
}

/** Build a state with custom draw/discard/deck for round-trip tests. */
function buildCustomState(
  drawIds: ReadonlyArray<Program>,
  discardIds: ReadonlyArray<Program>,
  handIds: ReadonlyArray<Program>,
): GameState {
  const base = buildState();
  return {
    ...base,
    drawPile: drawIds,
    discardPile: discardIds,
    deck: handIds,
  };
}

describe("slotToGameState (CONTINUE option)", () => {
  it("round-trips state via stateToSaveSlot + slotToGameState", () => {
    const base = buildState();
    const state: GameState = {
      ...base,
      player: { ...base.player, hp: 75, alarm: 30, credits: 250 },
      turnCount: 5,
    };
    const slot = stateToSaveSlot(state);
    expect(slot.version).toBe(1);
    expect(slot.missionId).toBe("test_mission");
    expect(slot.playerHp).toBe(75);

    const restored = slotToGameState(slot, catalog, mockPrograms, mockIce);
    expect(restored).not.toBeNull();
    if (!restored) return;
    expect(restored.mission.id).toBe("test_mission");
    expect(restored.player.hp).toBe(75);
    expect(restored.player.alarm).toBe(30);
    expect(restored.player.credits).toBe(250);
    expect(restored.turnCount).toBe(5);
    expect(restored.phase).toBe("approach"); // resume from approach
    expect(restored.message).toContain("Resumed");
  });

  it("returns null when missionId is not in catalog (data drift)", () => {
    const state = buildState();
    const slot = stateToSaveSlot(state);
    const orphaned: SaveSlot = { ...slot, missionId: "deleted_mission" };
    const restored = slotToGameState(orphaned, catalog, mockPrograms, mockIce);
    expect(restored).toBeNull();
  });

  it("returns null when all saved deck programs disappeared from catalog", () => {
    const state = buildState();
    const slot = stateToSaveSlot(state);
    // Empty programs catalog → all deck ids unresolvable → null.
    const emptyPrograms: Readonly<Record<string, Program>> = {};
    const restored = slotToGameState(slot, catalog, emptyPrograms, mockIce);
    expect(restored).toBeNull();
  });

  it("filters out missing programs but preserves remaining ones (defensive)", () => {
    const state = buildState();
    const slot = stateToSaveSlot(state);
    // Programs: strike (exists), deleted_one (missing), shield (exists)
    const partialCatalog = Object.freeze({
      strike: mockPrograms.strike,
      shield: mockPrograms.shield,
    });
    const slotWithMissing: SaveSlot = {
      ...slot,
      deckIds: ["strike", "deleted_one", "shield"],
    };
    const restored = slotToGameState(slotWithMissing, catalog, partialCatalog, mockIce);
    expect(restored).not.toBeNull();
    if (!restored) return;
    expect(restored.deck.length).toBe(2); // strike + shield (deleted_one dropped)
    expect(restored.deck.map((p) => p.id)).toEqual(["strike", "shield"]);
  });

  it("preserves draw pile and discard pile in correct arrays", () => {
    const state = buildCustomState(
      [mockPrograms.strike],
      [mockPrograms.hack],
      [mockPrograms.shield],
    );
    const slot = stateToSaveSlot(state);
    expect(slot.deckIds).toEqual(["shield"]);
    expect(slot.drawIds).toEqual(["strike"]);
    expect(slot.discardIds).toEqual(["hack"]);

    const restored = slotToGameState(slot, catalog, mockPrograms, mockIce);
    expect(restored).not.toBeNull();
    if (!restored) return;
    expect(restored.deck[0]?.id).toBe("shield");
    expect(restored.drawPile[0]?.id).toBe("strike");
    expect(restored.discardPile[0]?.id).toBe("hack");
  });

  it("resumes with phase 'approach' (post-combat-first-step, not 'combat')", () => {
    const base = buildState();
    const state: GameState = { ...base, turnCount: 10 };
    const slot = stateToSaveSlot(state);
    const restored = slotToGameState(slot, catalog, mockPrograms, mockIce);
    expect(restored?.phase).toBe("approach");
  });

  it("uses provided iceFallback for ice state (not in save)", () => {
    const state = buildState();
    const slot = stateToSaveSlot(state);
    const customIce: Ice = { ...mockIce, id: "custom_ice", name: "Custom" };
    const restored = slotToGameState(slot, catalog, mockPrograms, customIce);
    expect(restored?.ice.id).toBe("custom_ice");
  });
});