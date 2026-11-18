import { describe, it, expect } from "vitest";
import {
  makeLoadout,
  EMPTY_LOADOUT,
  equipOn,
  unequipFrom,
} from "../src/core/loadout.ts";
import {
  STARTER_DECK,
  STARTER_HEADWARE,
  STREET_DECK,
  MILITECH_EYES,
  CHROME_GLOVES,
  CORPORATE_DECK,
  SUBDERMAL,
  BOOTS_GHOST,
} from "../src/core/equipment_catalog.ts";
import type { EquipmentLoadout } from "../src/core/loadout.ts";

describe("loadout", () => {
  describe("EMPTY_LOADOUT", () => {
    it("is defined", () => {
      expect(EMPTY_LOADOUT).toBeDefined();
    });

    it("has no equipment", () => {
      expect(Object.keys(EMPTY_LOADOUT.equipment).length).toBe(0);
    });

    it("all slots are empty", () => {
      expect(EMPTY_LOADOUT.allSlotsFilled().length).toBe(0);
    });

    it("is not complete", () => {
      expect(EMPTY_LOADOUT.isComplete()).toBe(false);
    });

    it("has no set bonuses", () => {
      expect(EMPTY_LOADOUT.setBonuses().length).toBe(0);
    });

    it("totalStats returns zero stats", () => {
      const stats = EMPTY_LOADOUT.totalStats();
      expect(stats.programPower).toBe(0);
      expect(stats.attackBonus).toBe(0);
    });
  });

  describe("makeLoadout", () => {
    it("creates empty loadout with no args", () => {
      const loadout = makeLoadout();
      expect(loadout.allSlotsFilled().length).toBe(0);
    });

    it("creates loadout with initial equipment", () => {
      const loadout = makeLoadout({ deck: STARTER_DECK });
      expect(loadout.get("deck")).toBe(STARTER_DECK);
    });

    it("can initialize multiple slots", () => {
      const loadout = makeLoadout({
        deck: STARTER_DECK,
        headware: STARTER_HEADWARE,
      });
      expect(loadout.allSlotsFilled().length).toBe(2);
    });

    it("ignores undefined slots", () => {
      const loadout = makeLoadout({ deck: STARTER_DECK, headware: undefined });
      expect(loadout.allSlotsFilled().length).toBe(1);
    });
  });

  describe("equip", () => {
    it("equips item to empty slot", () => {
      const loadout = makeLoadout();
      const prev = loadout.equip(STARTER_DECK);
      expect(prev).toBe(null);
      expect(loadout.get("deck")).toBe(STARTER_DECK);
    });

    it("returns previous item when replacing", () => {
      const loadout = makeLoadout({ deck: STARTER_DECK });
      const prev = loadout.equip(STREET_DECK);
      expect(prev).toBe(STARTER_DECK);
      expect(loadout.get("deck")).toBe(STREET_DECK);
    });

    it("equips item to correct slot", () => {
      const loadout = makeLoadout();
      loadout.equip(MILITECH_EYES);
      expect(loadout.get("eyeware")).toBe(MILITECH_EYES);
    });

    it("can equip multiple different slots", () => {
      const loadout = makeLoadout();
      loadout.equip(STARTER_DECK);
      loadout.equip(STARTER_HEADWARE);
      expect(loadout.allSlotsFilled().length).toBe(2);
    });
  });

  describe("unequip", () => {
    it("removes item from slot", () => {
      const loadout = makeLoadout({ deck: STARTER_DECK });
      const removed = loadout.unequip("deck");
      expect(removed).toBe(STARTER_DECK);
      expect(loadout.get("deck")).toBe(null);
    });

    it("returns null when slot is empty", () => {
      const loadout = makeLoadout();
      expect(loadout.unequip("deck")).toBe(null);
    });

    it("leaves other slots unchanged", () => {
      const loadout = makeLoadout({ deck: STARTER_DECK, headware: STARTER_HEADWARE });
      loadout.unequip("deck");
      expect(loadout.get("headware")).toBe(STARTER_HEADWARE);
    });
  });

  describe("get", () => {
    it("returns null for empty slot", () => {
      const loadout = makeLoadout();
      expect(loadout.get("deck")).toBe(null);
    });

    it("returns equipped item", () => {
      const loadout = makeLoadout({ deck: STARTER_DECK });
      expect(loadout.get("deck")).toBe(STARTER_DECK);
    });

    it("returns correct item for each slot", () => {
      const loadout = makeLoadout();
      loadout.equip(STARTER_DECK);
      loadout.equip(MILITECH_EYES);
      expect(loadout.get("deck")).toBe(STARTER_DECK);
      expect(loadout.get("eyeware")).toBe(MILITECH_EYES);
    });
  });

  describe("allSlotsFilled", () => {
    it("returns empty array for empty loadout", () => {
      const loadout = makeLoadout();
      expect(loadout.allSlotsFilled().length).toBe(0);
    });

    it("returns array of filled slots", () => {
      const loadout = makeLoadout({ deck: STARTER_DECK, headware: STARTER_HEADWARE });
      const filled = loadout.allSlotsFilled();
      expect(filled.length).toBe(2);
      expect(filled).toContain("deck");
      expect(filled).toContain("headware");
    });

    it("returns frozen array", () => {
      const loadout = makeLoadout({ deck: STARTER_DECK });
      expect(Object.isFrozen(loadout.allSlotsFilled())).toBe(true);
    });
  });

  describe("emptySlots", () => {
    it("returns all slots when empty", () => {
      const loadout = makeLoadout();
      const empty = loadout.emptySlots();
      expect(empty.length).toBeGreaterThan(0);
    });

    it("excludes filled slots", () => {
      const loadout = makeLoadout({ deck: STARTER_DECK });
      const empty = loadout.emptySlots();
      expect(empty).not.toContain("deck");
    });

    it("returns frozen array", () => {
      const loadout = makeLoadout();
      expect(Object.isFrozen(loadout.emptySlots())).toBe(true);
    });
  });

  describe("isComplete", () => {
    it("returns false for empty loadout", () => {
      expect(makeLoadout().isComplete()).toBe(false);
    });

    it("returns false for partial loadout", () => {
      const loadout = makeLoadout({ deck: STARTER_DECK });
      expect(loadout.isComplete()).toBe(false);
    });

    it("returns true when all slots filled", () => {
      const loadout: EquipmentLoadout = makeLoadout({
        deck: STARTER_DECK,
        headware: STARTER_HEADWARE,
        eyeware: MILITECH_EYES,
        bodysuit: SUBDERMAL,
        gloves: CHROME_GLOVES,
        boots: BOOTS_GHOST,
        implant: STARTER_HEADWARE,
        trodes: STARTER_HEADWARE,
      });
      expect(loadout.isComplete()).toBe(true);
    });
  });

  describe("setCounts", () => {
    it("returns empty object for empty loadout", () => {
      const loadout = makeLoadout();
      const counts = loadout.setCounts();
      expect(Object.keys(counts).length).toBe(0);
    });

    it("counts single set", () => {
      const loadout = makeLoadout({ deck: STARTER_DECK });
      const counts = loadout.setCounts();
      expect(counts.ono_sendai).toBe(1);
    });

    it("counts multiple items in same set", () => {
      const loadout = makeLoadout();
      loadout.equip(MILITECH_EYES);
      loadout.equip(CHROME_GLOVES);
      const counts = loadout.setCounts();
      expect(counts.militech).toBe(2);
    });

    it("counts multiple sets", () => {
      const loadout = makeLoadout();
      loadout.equip(STARTER_DECK);
      loadout.equip(MILITECH_EYES);
      const counts = loadout.setCounts();
      expect(counts.ono_sendai).toBe(1);
      expect(counts.militech).toBe(1);
    });

    it("ignores items with null setId", () => {
      const loadout = makeLoadout({ bodysuit: SUBDERMAL });
      const counts = loadout.setCounts();
      expect(Object.keys(counts).length).toBe(0);
    });

    it("returns frozen object", () => {
      const loadout = makeLoadout({ deck: STARTER_DECK });
      expect(Object.isFrozen(loadout.setCounts())).toBe(true);
    });
  });

  describe("setBonuses", () => {
    it("returns empty array for empty loadout", () => {
      const loadout = makeLoadout();
      expect(loadout.setBonuses().length).toBe(0);
    });

    it("returns no bonus when threshold not met", () => {
      const loadout = makeLoadout({ deck: STARTER_DECK });
      expect(loadout.setBonuses().length).toBe(0);
    });

    it("returns bonus when 2pc threshold met", () => {
      const loadout = makeLoadout();
      loadout.equip(MILITECH_EYES);
      loadout.equip(CHROME_GLOVES);
      const bonuses = loadout.setBonuses();
      expect(bonuses.length).toBe(1);
      expect(bonuses[0]?.attackBonus).toBeGreaterThan(0);
    });

    it("returns frozen array", () => {
      const loadout = makeLoadout({ deck: STARTER_DECK });
      expect(Object.isFrozen(loadout.setBonuses())).toBe(true);
    });
  });

  describe("totalStats", () => {
    it("returns zero stats for empty loadout", () => {
      const loadout = makeLoadout();
      const stats = loadout.totalStats();
      expect(stats.programPower).toBe(0);
      expect(stats.attackBonus).toBe(0);
    });

    it("sums stats from single item", () => {
      const loadout = makeLoadout({ deck: STARTER_DECK });
      const stats = loadout.totalStats();
      expect(stats.programPower).toBe(STARTER_DECK.stats.programPower);
    });

    it("sums stats from multiple items", () => {
      const loadout = makeLoadout();
      loadout.equip(STARTER_DECK);
      loadout.equip(MILITECH_EYES);
      const stats = loadout.totalStats();
      expect(stats.programPower).toBe(STARTER_DECK.stats.programPower);
      expect(stats.attackBonus).toBe(MILITECH_EYES.stats.attackBonus);
    });

    it("includes set bonuses when applicable", () => {
      const loadout = makeLoadout();
      loadout.equip(MILITECH_EYES);
      loadout.equip(CHROME_GLOVES);
      const stats = loadout.totalStats();
      const itemAttack = MILITECH_EYES.stats.attackBonus + CHROME_GLOVES.stats.attackBonus;
      expect(stats.attackBonus).toBeGreaterThan(itemAttack);
    });
  });

  describe("equipOn (pure function)", () => {
    it("returns new loadout with item equipped", () => {
      const orig = makeLoadout();
      const result = equipOn(orig, STARTER_DECK);
      expect(result.loadout.get("deck")).toBe(STARTER_DECK);
    });

    it("does not mutate original", () => {
      const orig = makeLoadout();
      equipOn(orig, STARTER_DECK);
      expect(orig.get("deck")).toBe(null);
    });

    it("returns previous item when replacing", () => {
      const orig = makeLoadout({ deck: STARTER_DECK });
      const result = equipOn(orig, STREET_DECK);
      expect(result.previous).toBe(STARTER_DECK);
      expect(result.loadout.get("deck")).toBe(STREET_DECK);
    });

    it("returns null previous when slot empty", () => {
      const orig = makeLoadout();
      const result = equipOn(orig, STARTER_DECK);
      expect(result.previous).toBe(null);
    });
  });

  describe("unequipFrom (pure function)", () => {
    it("returns new loadout with item removed", () => {
      const orig = makeLoadout({ deck: STARTER_DECK });
      const result = unequipFrom(orig, "deck");
      expect(result.loadout.get("deck")).toBe(null);
      expect(result.removed).toBe(STARTER_DECK);
    });

    it("does not mutate original", () => {
      const orig = makeLoadout({ deck: STARTER_DECK });
      unequipFrom(orig, "deck");
      expect(orig.get("deck")).toBe(STARTER_DECK);
    });

    it("returns null removed when slot empty", () => {
      const orig = makeLoadout();
      const result = unequipFrom(orig, "deck");
      expect(result.removed).toBe(null);
    });

    it("leaves other slots unchanged", () => {
      const orig = makeLoadout({ deck: STARTER_DECK, headware: STARTER_HEADWARE });
      const result = unequipFrom(orig, "deck");
      expect(result.loadout.get("headware")).toBe(STARTER_HEADWARE);
    });
  });

  describe("edge cases", () => {
    it("handles rapid equip/unequip", () => {
      const loadout = makeLoadout();
      loadout.equip(STARTER_DECK);
      loadout.unequip("deck");
      loadout.equip(STREET_DECK);
      expect(loadout.get("deck")).toBe(STREET_DECK);
    });

    it("can swap items of same type", () => {
      const loadout = makeLoadout({ deck: STARTER_DECK });
      loadout.equip(STREET_DECK);
      loadout.equip(CORPORATE_DECK);
      expect(loadout.get("deck")).toBe(CORPORATE_DECK);
    });

    it("handles full loadout operations", () => {
      const loadout: EquipmentLoadout = makeLoadout({
        deck: STARTER_DECK,
        headware: STARTER_HEADWARE,
        eyeware: MILITECH_EYES,
        bodysuit: SUBDERMAL,
        gloves: CHROME_GLOVES,
        boots: BOOTS_GHOST,
        implant: STARTER_HEADWARE,
        trodes: STARTER_HEADWARE,
      });
      expect(loadout.isComplete()).toBe(true);
      loadout.unequip("deck");
      expect(loadout.isComplete()).toBe(false);
    });
  });
});
