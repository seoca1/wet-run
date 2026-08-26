/** Tests for save/load module (Tier 2a multi-slot). Requires jsdom environment.
 */
// @vitest-environment jsdom

import { describe, it, expect, beforeEach } from "vitest";
import {
  save,
  load,
  clear,
  listSlots,
  MAX_SAVE_SLOT,
  MANUAL_SLOTS,
  SAVE_SLOT_LABELS,
} from "../src/save/storage.ts";
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

describe("storage (Tier 2a multi-slot)", () => {
  beforeEach(() => {
    for (let s = 0; s <= MAX_SAVE_SLOT; s++) {
      clear(s);
    }
    localStorage.removeItem("wetrun_mvp_save_v1");
  });

  it("exposes 4 slots (autosave + 3 manual)", () => {
    expect(MAX_SAVE_SLOT).toBe(3);
    expect(MANUAL_SLOTS).toEqual([1, 2, 3]);
    // Verify all 4 slots (0..3) are reachable
    for (let s = 0; s <= 3; s++) {
      save(s, sampleSlot);
      expect(load(s)).not.toBeNull();
      clear(s);
    }
  });

  it("each slot has a label", () => {
    expect(SAVE_SLOT_LABELS[0]).toBe("Autosave");
    expect(SAVE_SLOT_LABELS[1]).toBe("Slot 1");
    expect(SAVE_SLOT_LABELS[3]).toBe("Slot 3");
  });

  it("round-trips a save on slot 0 (autosave)", () => {
    save(0, sampleSlot);
    expect(load(0)).toEqual(sampleSlot);
  });

  it("saves and loads each slot independently", () => {
    save(1, { ...sampleSlot, turnCount: 1 });
    save(2, { ...sampleSlot, turnCount: 2 });
    save(3, { ...sampleSlot, turnCount: 3 });
    expect(load(1)?.turnCount).toBe(1);
    expect(load(2)?.turnCount).toBe(2);
    expect(load(3)?.turnCount).toBe(3);
  });

  it("clears only the specified slot", () => {
    save(1, sampleSlot);
    save(2, sampleSlot);
    clear(1);
    expect(load(1)).toBeNull();
    expect(load(2)).not.toBeNull();
  });

  it("listSlots returns occupied slots with metadata", () => {
    save(1, sampleSlot);
    save(3, sampleSlot);
    const listed = listSlots();
    expect(listed.length).toBe(2);
    const slots = listed.map((s) => s.slot);
    expect(slots).toContain(1);
    expect(slots).toContain(3);
    expect(listed.every((s) => s.savedAt === sampleSlot.savedAt)).toBe(true);
  });

  it("rejects invalid slot numbers", () => {
    expect(() => save(-1, sampleSlot)).toThrow();
    expect(() => save(99, sampleSlot)).toThrow();
    expect(() => load(99)).toThrow();
  });

  it("returns null for empty slots", () => {
    expect(load(1)).toBeNull();
    expect(load(3)).toBeNull();
  });

  it("rejects corrupted JSON", () => {
    localStorage.setItem("wetrun_mvp_save_v1_slot_1", "{not valid");
    expect(load(1)).toBeNull();
  });

  it("rejects schema version mismatch", () => {
    save(1, { ...sampleSlot, version: 99 });
    expect(load(1)).toBeNull();
  });

  it("rejects type-mismatched fields", () => {
    localStorage.setItem(
      "wetrun_mvp_save_v1_slot_1",
      JSON.stringify({ version: 1, playerHp: "not a number" }),
    );
    expect(load(1)).toBeNull();
  });

  it("migrates legacy single-slot save to slot 0", () => {
    localStorage.setItem("wetrun_mvp_save_v1", JSON.stringify(sampleSlot));
    const loaded = load(0);
    expect(loaded).not.toBeNull();
    expect(loaded?.turnCount).toBe(3);
    expect(localStorage.getItem("wetrun_mvp_save_v1")).toBeNull();
  });
});
