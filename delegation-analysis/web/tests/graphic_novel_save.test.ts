import { describe, it, expect } from "vitest";
import { stateToSaveSlot, slotToGameState, makeInitialState } from "../src/core/state.ts";
import type { GameState, Ice, Mission, Program } from "../src/core/types.ts";

function makeTestState(): GameState {
  const mockMission: Mission = {
    id: "test",
    title: "Test",
    fixer: "test",
    arc: 1,
    zone: "test",
    grade_min: 1,
    grade_max: 1,
    rewards: { credits: 10, materials: {} },
  };
  const mockProgram: Program = {
    id: "p1",
    name: "Atk",
    tier: 1,
    cost: 0,
    effect: "damage",
    description: "test",
    aoe: false,
  };
  const mockIce: Ice = {
    id: "enemy1",
    name: "Enemy",
    tier: 1,
    hp: 50,
    maxHp: 50,
    armor: 0,
  };
  return makeInitialState(mockMission, mockIce, [mockProgram]);
}

describe("graphic novel save/load", () => {
  it("saves graphic novel progress to SaveSlot", () => {
    const state = makeTestState();
    const stateWithGN = {
      ...state,
      graphicNovel: {
        player: {
          mode: "prologue" as const,
          chain: [],
          character_id: "veteran" as const,
          ending: "A" as const,
          scene_index: 2,
          dialogue_index: 5,
          elapsed_ms: 0,
          paused: false,
          done: false,
        },
        currentScene: null,
        currentText: "",
        isPaused: false,
      },
    };
    const slot = stateToSaveSlot(stateWithGN);
    expect(slot.graphicNovelProgress).toEqual({
      chainId: "prologue_veteran",
      sceneIndex: 2,
      dialogueIndex: 5,
    });
  });

  it("saves null when no graphic novel active", () => {
    const state = makeTestState();
    const slot = stateToSaveSlot(state);
    expect(slot.graphicNovelProgress).toBeNull();
  });

  it("restores graphic novel progress from SaveSlot", () => {
    const state = makeTestState();
    const slot = stateToSaveSlot({
      ...state,
      graphicNovel: {
        player: {
          mode: "heretic" as const,
          chain: [],
          character_id: "heretic" as const,
          ending: "A" as const,
          scene_index: 1,
          dialogue_index: 3,
          elapsed_ms: 0,
          paused: false,
          done: false,
        },
        currentScene: null,
        currentText: "",
        isPaused: false,
      },
    });
    const restored = slotToGameState(slot, [state.mission], { p1: state.deck[0] }, state.ice);
    expect(restored?.graphicNovel?.player.mode).toBe("heretic");
    expect(restored?.graphicNovel?.player.character_id).toBe("heretic");
    expect(restored?.graphicNovel?.player.scene_index).toBe(1);
    expect(restored?.graphicNovel?.player.dialogue_index).toBe(3);
  });

  it("handles missing graphic novel progress in old saves", () => {
    const state = makeTestState();
    const slot = stateToSaveSlot(state);
    const oldSlot = { ...slot, graphicNovelProgress: undefined };
    const restored = slotToGameState(oldSlot, [state.mission], { p1: state.deck[0] }, state.ice);
    expect(restored?.graphicNovel).toBeNull();
  });
});
