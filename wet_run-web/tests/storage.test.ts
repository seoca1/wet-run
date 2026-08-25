/** Tests for save/load module. Requires jsdom environment (vitest configured).
 */
// @vitest-environment jsdom

import { describe, it, expect, beforeEach } from "vitest";
import { save, load, clear } from "../src/save/storage.ts";
import type { SaveSlot } from "../src/core/types.ts";

const sampleSlot: SaveSlot = {
  version: 1,
  missionId: "first_jack",
  playerHp: 75,
  playerMaxHp: 100,
  playerAlarm: 20,
  playerCredits: 50,
  turnCount: 3,
  deckIds: ["wisp", "strike", "sweep"],
  discardIds: ["strike"],
  drawIds: ["shield"],
  savedAt: "2026-08-25T00:00:00Z",
};

describe("storage", () => {
  beforeEach(() => {
    clear();
  });

  it("round-trips a save slot", () => {
    save(sampleSlot);
    const loaded = load();
    expect(loaded).toEqual(sampleSlot);
  });

  it("returns null when no save exists", () => {
    expect(load()).toBeNull();
  });

  it("returns null after clear", () => {
    save(sampleSlot);
    clear();
    expect(load()).toBeNull();
  });

  it("returns null on schema version mismatch", () => {
    save({ ...sampleSlot, version: 99 });
    expect(load()).toBeNull();
  });

  it("returns null on corrupted JSON", () => {
    localStorage.setItem("wetrun_mvp_save_v1", "{not valid json");
    expect(load()).toBeNull();
  });

  it("returns null on type-mismatched fields", () => {
    localStorage.setItem(
      "wetrun_mvp_save_v1",
      JSON.stringify({ version: 1, playerHp: "not a number" }),
    );
    expect(load()).toBeNull();
  });
});
