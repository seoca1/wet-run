/** ADR-0325 — equipment ownership.
 *
 * The catalog (18 pieces) and the recipes (16) existed with nothing tying them
 * together: crafting pushed a throwaway Program and the EQUIPMENT menu equipped
 * the first registry entry, owned or not. This store is the missing axis —
 * tier-0 starters are owned, everything else is earned by crafting.
 */
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
  STARTING_OWNED,
  isOwned,
  mergeDroppedEquipment,
  ownEquipment,
  ownedIds,
  readOwnedIds,
  writeOwnedIds,
} from "../src/core/state/owned_equipment";
import { DEFAULT_REGISTRY } from "../src/core/state/equipment";

const KEY = "wetrun_owned_equipment";

describe("owned_equipment", () => {
  it("starts with exactly the tier-0 gear", () => {
    const t0 = DEFAULT_REGISTRY.all
      .filter((e) => e.tier === "T0")
      .map((e) => e.id)
      .sort();
    expect([...STARTING_OWNED].sort()).toEqual(t0);
    expect(STARTING_OWNED).toContain("deck_basic");
    expect(STARTING_OWNED).toContain("head_basic");
  });

  it("isOwned is true for starters and crafted ids, false otherwise", () => {
    const owned = ownEquipment({}, "deck_street");
    expect(isOwned(owned, "deck_basic")).toBe(true); // starter, never crafted
    expect(isOwned(owned, "deck_street")).toBe(true); // crafted
    expect(isOwned(owned, "deck_master")).toBe(false);
    expect(isOwned({}, "deck_master")).toBe(false);
  });

  it("ownEquipment is idempotent and never mutates the input", () => {
    const a = ownEquipment({}, "deck_street");
    const b = ownEquipment(a, "deck_street");
    expect(b).toBe(a); // same record when already owned
    expect(Object.isFrozen(a)).toBe(true);
    expect(isOwned({}, "deck_street")).toBe(false); // original untouched
  });

  it("ownEquipment also accepts a starter without recording it", () => {
    const owned = ownEquipment({}, "deck_basic");
    expect(owned).toEqual({}); // starters need no record
    expect(isOwned(owned, "deck_basic")).toBe(true);
  });

  it("ownedIds lists starters first, then crafted in sorted order", () => {
    const owned = ownEquipment(ownEquipment({}, "deck_master"), "deck_street");
    const ids = ownedIds(owned);
    expect(ids.slice(0, STARTING_OWNED.length)).toEqual([...STARTING_OWNED]);
    expect(ids).toContain("deck_street");
    expect(ids).toContain("deck_master");
    // sorted: deck_master before deck_street
    expect(ids.indexOf("deck_master")).toBeLessThan(ids.indexOf("deck_street"));
  });

  describe("persistence", () => {
    beforeEach(() => localStorage.removeItem(KEY));
    afterEach(() => localStorage.removeItem(KEY));

    it("round-trips through storage", () => {
      writeOwnedIds(ownEquipment({}, "deck_street"));
      expect(readOwnedIds()).toEqual({ deck_street: true });
      expect(isOwned(readOwnedIds(), "deck_street")).toBe(true);
    });

    it("degrades to empty on malformed storage", () => {
      localStorage.setItem(KEY, "{not json");
      expect(readOwnedIds()).toEqual({});
    });

    it("drops non-true values", () => {
      localStorage.setItem(KEY, JSON.stringify({ a: false, b: true, c: 1 }));
      expect(readOwnedIds()).toEqual({ b: true });
    });
  });
});

describe("ADR-0346 · merging a run's salvaged gear", () => {
  it("makes every dropped piece owned", () => {
    const owned = mergeDroppedEquipment({}, ["eyes_militech", "deck_militech"]);
    expect(isOwned(owned, "eyes_militech")).toBe(true);
    expect(isOwned(owned, "deck_militech")).toBe(true);
  });

  it("returns the SAME record when nothing new is dropped (so the write is skipped)", () => {
    const before = ownEquipment({}, "eyes_militech");
    expect(mergeDroppedEquipment(before, ["eyes_militech"])).toBe(before);
    expect(mergeDroppedEquipment(before, [])).toBe(before);
    // A starter is already owned, so dropping it changes nothing.
    expect(mergeDroppedEquipment(before, [STARTING_OWNED[0] as string])).toBe(before);
  });

  it("does not depend on the order the drops were picked up", () => {
    const ab = mergeDroppedEquipment({}, ["eyes_militech", "deck_militech"]);
    const ba = mergeDroppedEquipment({}, ["deck_militech", "eyes_militech"]);
    expect(ownedIds(ab)).toEqual(ownedIds(ba));
  });
});
