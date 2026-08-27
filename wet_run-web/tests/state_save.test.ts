/** Tier 2a tests for GameState ↔ SaveSlot round-trip.
 */
import { describe, it, expect } from "vitest";
import {
  applyAction,
  makeInitialState,
  stateToSaveSlot,
} from "../src/core/state.js";
import type { Ice, Mission, Program } from "../src/core/types.js";

const mockMission: Mission = {
  id: "test_mission",
  title: "Test",
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
  hp: 50,
  armor: 0,
  tier: 1,
};

const mockPrograms: Program[] = [
  { id: "p1", name: "Alpha", tier: 1, cost: 5, effect: "x", description: "" },
  { id: "p2", name: "Beta", tier: 1, cost: 5, effect: "x", description: "" },
  { id: "p3", name: "Gamma", tier: 1, cost: 5, effect: "x", description: "" },
];

describe("stateToSaveSlot round-trip", () => {
  it("captures all required SaveSlot fields", () => {
    const state = makeInitialState(mockMission, mockIce, mockPrograms);
    const slot = stateToSaveSlot(state);
    expect(slot.version).toBe(1);
    expect(slot.missionId).toBe("test_mission");
    expect(slot.playerHp).toBe(state.player.hp);
    expect(slot.playerMaxHp).toBe(state.player.maxHp);
    expect(slot.playerAlarm).toBe(state.player.alarm);
    expect(slot.playerCredits).toBe(state.player.credits);
    expect(slot.turnCount).toBe(state.turnCount);
    expect(Array.isArray(slot.deckIds)).toBe(true);
    expect(Array.isArray(slot.discardIds)).toBe(true);
    expect(Array.isArray(slot.drawIds)).toBe(true);
  });

  it("serializes deck, discard, and draw as id arrays", () => {
    const state = makeInitialState(mockMission, mockIce, mockPrograms);
    const slot = stateToSaveSlot(state);
    const handCount = state.deck.length;
    expect(slot.deckIds.length).toBe(handCount);
    if (handCount > 0) expect(slot.deckIds[0]).toBe(state.deck[0]?.id);
  });

  it("serializes combat damage (turn count + alarm) changes", () => {
    let state = makeInitialState(mockMission, mockIce, mockPrograms);
    // Tier 5: set up matrix so Enter transitions to combat.
    const withMatrix = {
      ...state,
      matrix: { nodes: [{ id: 0, zone: "surface" as const, iceIds: ["watchdog"], iceHp: [100], reward: { credits: 50 }, isBoss: false, adjacent: [] }], startNode: 0, bossNode: 0 },
      currentNodeIndex: 0,
    };
    const inCombat = applyAction(applyAction(withMatrix, { type: "confirm" }), {
      type: "confirm",
    });
    const afterUse = applyAction(inCombat, {
      type: "use_program",
      programId: mockPrograms[0]?.id ?? "p1",
    });
    const slot = stateToSaveSlot(afterUse);
    expect(slot.turnCount).toBeGreaterThan(state.turnCount);
    expect(slot.playerAlarm).toBeGreaterThan(0);
  });

  it("includes ISO 8601 timestamp in savedAt", () => {
    const state = makeInitialState(mockMission, mockIce, mockPrograms);
    const slot = stateToSaveSlot(state);
    expect(slot.savedAt).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/);
    // ISO format round-trips through Date
    expect(() => new Date(slot.savedAt).toISOString()).not.toThrow();
  });
});
