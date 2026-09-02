import { describe, it, expect } from "vitest";
import {
  SET_BONUSES,
  getSetBonus,
  getSetBonusDefinitions,
  calculateSetBonus,
  getActiveSetIds,
  getSetCount,
  getBestSetBonusFor,
  getAllSetBonuses,
  applySetBonusesToStats,
} from "../src/core/set_bonus.ts";
import { makeLoadout, EMPTY_LOADOUT } from "../src/core/loadout.ts";
import { STARTER_DECK, STREET_DECK, MILITECH_EYES, CHROME_GLOVES, MILITECH_DECK, ARASAKA_DECK, KEREZNIKOV } from "../src/core/equipment_catalog.ts";
import { makeEquipStats } from "../src/core/equipment.ts";

describe("set_bonus", () => {
  describe("SET_BONUSES data", () => {
    it("is frozen", () => {
      expect(Object.isFrozen(SET_BONUSES)).toBe(true);
    });

    it("has ono_sendai set", () => {
      expect(SET_BONUSES.ono_sendai).toBeDefined();
    });

    it("has militech set", () => {
      expect(SET_BONUSES.militech).toBeDefined();
    });

    it("has arasaka set", () => {
      expect(SET_BONUSES.arasaka).toBeDefined();
    });

    it("ono_sendai has 2pc and 3pc thresholds", () => {
      const set = SET_BONUSES.ono_sendai;
      expect(set[2]).toBeDefined();
      expect(set[3]).toBeDefined();
    });

    it("militech has 2pc and 3pc thresholds", () => {
      const set = SET_BONUSES.militech;
      expect(set[2]).toBeDefined();
      expect(set[3]).toBeDefined();
    });

    it("arasaka has 2pc and 3pc thresholds", () => {
      const set = SET_BONUSES.arasaka;
      expect(set[2]).toBeDefined();
      expect(set[3]).toBeDefined();
    });

    it("all bonuses are frozen", () => {
      expect(Object.isFrozen(SET_BONUSES.ono_sendai[2])).toBe(true);
      expect(Object.isFrozen(SET_BONUSES.militech[2])).toBe(true);
      expect(Object.isFrozen(SET_BONUSES.arasaka[2])).toBe(true);
    });
  });

  describe("getSetBonus", () => {
    it("returns null for null setId", () => {
      expect(getSetBonus(null, 2)).toBe(null);
    });

    it("returns null for unknown setId", () => {
      expect(getSetBonus("unknown_set", 2)).toBe(null);
    });

    it("returns null when count is zero", () => {
      expect(getSetBonus("ono_sendai", 0)).toBe(null);
    });

    it("returns null when count is below lowest threshold", () => {
      expect(getSetBonus("ono_sendai", 1)).toBe(null);
    });

    it("returns 2pc bonus when count is 2", () => {
      const bonus = getSetBonus("ono_sendai", 2);
      expect(bonus).not.toBe(null);
      expect(bonus?.programPower).toBe(10);
    });

    it("returns 3pc bonus when count is 3", () => {
      const bonus = getSetBonus("ono_sendai", 3);
      expect(bonus).not.toBe(null);
      expect(bonus?.programPower).toBe(25);
    });

    it("returns highest applicable bonus when count exceeds all thresholds", () => {
      const bonus = getSetBonus("ono_sendai", 10);
      expect(bonus).not.toBe(null);
      expect(bonus?.programPower).toBe(25);
    });

    it("militech 2pc gives attackBonus", () => {
      const bonus = getSetBonus("militech", 2);
      expect(bonus?.attackBonus).toBe(5);
    });

    it("militech 3pc gives higher attackBonus and shieldBonus", () => {
      const bonus = getSetBonus("militech", 3);
      expect(bonus?.attackBonus).toBe(15);
      expect(bonus?.shieldBonus).toBe(2);
    });

    it("arasaka 2pc gives defense and iceResistance", () => {
      const bonus = getSetBonus("arasaka", 2);
      expect(bonus?.defense).toBe(8);
      expect(bonus?.iceResistance).toBe(15);
    });

    it("arasaka 3pc gives higher defense and hpBonus", () => {
      const bonus = getSetBonus("arasaka", 3);
      expect(bonus?.defense).toBe(20);
      expect(bonus?.hpBonus).toBe(30);
    });
  });

  describe("getSetBonusDefinitions", () => {
    it("returns frozen definitions", () => {
      const defs = getSetBonusDefinitions();
      expect(Object.isFrozen(defs)).toBe(true);
    });

    it("returns same reference as SET_BONUSES", () => {
      expect(getSetBonusDefinitions()).toBe(SET_BONUSES);
    });
  });

  describe("calculateSetBonus with loadout", () => {
    it("empty loadout has no bonuses", () => {
      const summary = calculateSetBonus(EMPTY_LOADOUT);
      expect(summary.activeSetIds.length).toBe(0);
      expect(summary.totalBonus.programPower).toBe(0);
    });

    it("single ono_sendai item has no bonus", () => {
      const loadout = makeLoadout({ deck: STARTER_DECK });
      const summary = calculateSetBonus(loadout);
      expect(summary.setCount.ono_sendai).toBe(1);
      expect(summary.totalBonus.programPower).toBe(0);
    });

    it("two ono_sendai items trigger 2pc bonus", () => {
      const loadout = makeLoadout({ deck: STARTER_DECK, bodysuit: STREET_DECK });
      loadout.equip(STARTER_DECK);
      loadout.equip(STREET_DECK);
      const summary = calculateSetBonus(loadout);
      expect(summary.setCount.ono_sendai).toBe(2);
      expect(summary.totalBonus.programPower).toBe(10);
    });

    it("three ono_sendai items trigger 3pc bonus", () => {
      const loadout = makeLoadout();
      loadout.equip(MILITECH_EYES);
      loadout.equip(CHROME_GLOVES);
      loadout.equip(MILITECH_DECK);
      const summary = calculateSetBonus(loadout);
      expect(summary.activeSetIds).toContain("militech");
      expect(summary.totalBonus.attackBonus).toBe(15);
    });

    it("two militech items trigger 2pc bonus", () => {
      const loadout = makeLoadout();
      loadout.equip(MILITECH_EYES);
      loadout.equip(CHROME_GLOVES);
      const summary = calculateSetBonus(loadout);
      expect(summary.setCount.militech).toBe(2);
      expect(summary.totalBonus.attackBonus).toBe(5);
    });

    it("three militech items trigger 3pc bonus", () => {
      const loadout = makeLoadout();
      loadout.equip(MILITECH_EYES);
      loadout.equip(CHROME_GLOVES);
      loadout.equip(MILITECH_DECK);
      const summary = calculateSetBonus(loadout);
      expect(summary.totalBonus.attackBonus).toBe(15);
      expect(summary.totalBonus.critBonusPct).toBe(25);
    });

    it("two arasaka items trigger 2pc bonus", () => {
      const loadout = makeLoadout();
      loadout.equip(ARASAKA_DECK);
      loadout.equip(KEREZNIKOV);
      const summary = calculateSetBonus(loadout);
      expect(summary.setCount.arasaka).toBe(2);
      expect(summary.totalBonus.defense).toBe(8);
    });
  });

  describe("getActiveSetIds", () => {
    it("empty loadout has no active sets", () => {
      const ids = getActiveSetIds(EMPTY_LOADOUT);
      expect(ids.length).toBe(0);
    });

    it("single set item shows in active sets", () => {
      const loadout = makeLoadout();
      loadout.equip(STARTER_DECK);
      const ids = getActiveSetIds(loadout);
      expect(ids).toContain("ono_sendai");
    });

    it("mixed sets show both in active", () => {
      const loadout = makeLoadout();
      loadout.equip(STARTER_DECK);
      loadout.equip(MILITECH_EYES);
      const ids = getActiveSetIds(loadout);
      expect(ids).toContain("ono_sendai");
      expect(ids).toContain("militech");
    });
  });

  describe("getSetCount", () => {
    it("returns 0 for empty loadout", () => {
      expect(getSetCount(EMPTY_LOADOUT, "ono_sendai")).toBe(0);
    });

    it("returns correct count for one item", () => {
      const loadout = makeLoadout();
      loadout.equip(STARTER_DECK);
      expect(getSetCount(loadout, "ono_sendai")).toBe(1);
    });

    it("returns correct count for two items", () => {
      const loadout = makeLoadout();
      loadout.equip(MILITECH_EYES);
      loadout.equip(CHROME_GLOVES);
      expect(getSetCount(loadout, "militech")).toBe(2);
    });

    it("returns 0 for absent set", () => {
      const loadout = makeLoadout();
      loadout.equip(STARTER_DECK);
      expect(getSetCount(loadout, "militech")).toBe(0);
    });
  });

  describe("getBestSetBonusFor", () => {
    it("returns null for empty loadout", () => {
      expect(getBestSetBonusFor(EMPTY_LOADOUT, "ono_sendai")).toBe(null);
    });

    it("returns null when count is below threshold", () => {
      const loadout = makeLoadout();
      loadout.equip(STARTER_DECK);
      expect(getBestSetBonusFor(loadout, "ono_sendai")).toBe(null);
    });

    it("returns 2pc bonus when 2 equipped", () => {
      const loadout = makeLoadout();
      loadout.equip(MILITECH_EYES);
      loadout.equip(CHROME_GLOVES);
      const bonus = getBestSetBonusFor(loadout, "militech");
      expect(bonus?.attackBonus).toBe(5);
    });

    it("returns 3pc bonus when 3 equipped", () => {
      const loadout = makeLoadout();
      loadout.equip(MILITECH_EYES);
      loadout.equip(CHROME_GLOVES);
      loadout.equip(MILITECH_DECK);
      const bonus = getBestSetBonusFor(loadout, "militech");
      expect(bonus?.attackBonus).toBe(15);
    });
  });

  describe("getAllSetBonuses", () => {
    it("returns empty array for empty loadout", () => {
      const bonuses = getAllSetBonuses(EMPTY_LOADOUT);
      expect(bonuses.length).toBe(0);
    });

    it("returns empty array when no thresholds met", () => {
      const loadout = makeLoadout();
      loadout.equip(STARTER_DECK);
      const bonuses = getAllSetBonuses(loadout);
      expect(bonuses.length).toBe(0);
    });

    it("returns one bonus when one set reaches threshold", () => {
      const loadout = makeLoadout();
      loadout.equip(MILITECH_EYES);
      loadout.equip(CHROME_GLOVES);
      const bonuses = getAllSetBonuses(loadout);
      expect(bonuses.length).toBe(1);
    });

    it("returns multiple bonuses for multiple sets", () => {
      const loadout = makeLoadout();
      loadout.equip(MILITECH_EYES);
      loadout.equip(CHROME_GLOVES);
      loadout.equip(ARASAKA_DECK);
      loadout.equip(KEREZNIKOV);
      const bonuses = getAllSetBonuses(loadout);
      expect(bonuses.length).toBe(2);
    });
  });

  describe("applySetBonusesToStats", () => {
    it("returns base when no bonuses", () => {
      const base = makeEquipStats({ programPower: 10 });
      const result = applySetBonusesToStats(base, EMPTY_LOADOUT);
      expect(result.programPower).toBe(10);
    });

    it("adds bonus stats to base", () => {
      const loadout = makeLoadout();
      loadout.equip(MILITECH_EYES);
      loadout.equip(CHROME_GLOVES);
      const base = makeEquipStats({ attackBonus: 10 });
      const result = applySetBonusesToStats(base, loadout);
      expect(result.attackBonus).toBe(15);
    });

    it("combines multiple set bonuses", () => {
      const loadout = makeLoadout();
      loadout.equip(MILITECH_EYES);
      loadout.equip(CHROME_GLOVES);
      loadout.equip(ARASAKA_DECK);
      loadout.equip(KEREZNIKOV);
      const base = makeEquipStats({ attackBonus: 5, defense: 5 });
      const result = applySetBonusesToStats(base, loadout);
      expect(result.attackBonus).toBeGreaterThan(5);
      expect(result.defense).toBeGreaterThan(5);
    });
  });
});
