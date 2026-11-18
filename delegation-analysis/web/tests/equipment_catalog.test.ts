import { describe, it, expect } from "vitest";
import {
  DEFAULT_EQUIPMENT,
  STARTER_DECK,
  STARTER_HEADWARE,
  STREET_DECK,
  MILITECH_EYES,
  CHROME_GLOVES,
  CORPORATE_DECK,
  SUBDERMAL,
  MILITECH_DECK,
  TACTICAL_BODY,
  ARASAKA_DECK,
  KEREZNIKOV,
  GHOST_DECK,
  MASTER_DECK,
  MASTER_BODY,
  ZION_TRODES,
  NANO_HIVE,
  TRODES_NINJA,
  BOOTS_GHOST,
} from "../src/core/equipment_catalog.ts";
import type { EquipSlot } from "../src/core/equipment.ts";

describe("equipment_catalog", () => {
  describe("DEFAULT_EQUIPMENT array", () => {
    it("contains 18 equipment pieces", () => {
      expect(DEFAULT_EQUIPMENT.length).toBe(18);
    });

    it("all entries are frozen", () => {
      for (const eq of DEFAULT_EQUIPMENT) {
        expect(Object.isFrozen(eq)).toBe(true);
      }
    });

    it("every equipment has unique id", () => {
      const ids = DEFAULT_EQUIPMENT.map((e) => e.id);
      expect(new Set(ids).size).toBe(ids.length);
    });

    it("every equipment has frozen stats", () => {
      for (const eq of DEFAULT_EQUIPMENT) {
        expect(Object.isFrozen(eq.stats)).toBe(true);
      }
    });
  });

  describe("Tier distribution", () => {
    it("has T0 starter items", () => {
      const t0 = DEFAULT_EQUIPMENT.filter((e) => e.tier === "T0");
      expect(t0.length).toBeGreaterThan(0);
      expect(t0.some((e) => e.id === "deck_basic")).toBe(true);
    });

    it("has T1 street items", () => {
      const t1 = DEFAULT_EQUIPMENT.filter((e) => e.tier === "T1");
      expect(t1.length).toBeGreaterThan(0);
    });

    it("has T2 corporate items", () => {
      const t2 = DEFAULT_EQUIPMENT.filter((e) => e.tier === "T2");
      expect(t2.length).toBeGreaterThan(0);
    });

    it("has T3 militech items", () => {
      const t3 = DEFAULT_EQUIPMENT.filter((e) => e.tier === "T3");
      expect(t3.length).toBeGreaterThan(0);
    });

    it("has T4 arasaka items", () => {
      const t4 = DEFAULT_EQUIPMENT.filter((e) => e.tier === "T4");
      expect(t4.length).toBeGreaterThan(0);
    });

    it("has T5 ghost items", () => {
      const t5 = DEFAULT_EQUIPMENT.filter((e) => e.tier === "T5");
      expect(t5.length).toBeGreaterThan(0);
    });

    it("has T6 master items", () => {
      const t6 = DEFAULT_EQUIPMENT.filter((e) => e.tier === "T6");
      expect(t6.length).toBeGreaterThan(0);
    });
  });

  describe("Slot coverage", () => {
    const slots: EquipSlot[] = ["deck", "headware", "eyeware", "bodysuit", "gloves", "boots", "implant", "trodes"];

    for (const slot of slots) {
      it(`has at least one item for slot: ${slot}`, () => {
        const items = DEFAULT_EQUIPMENT.filter((e) => e.slot === slot);
        expect(items.length).toBeGreaterThan(0);
      });
    }
  });

  describe("STARTER_DECK", () => {
    it("is frozen", () => {
      expect(Object.isFrozen(STARTER_DECK)).toBe(true);
    });

    it("has correct id", () => {
      expect(STARTER_DECK.id).toBe("deck_basic");
    });

    it("is T0 tier", () => {
      expect(STARTER_DECK.tier).toBe("T0");
    });

    it("has deck slot", () => {
      expect(STARTER_DECK.slot).toBe("deck");
    });

    it("has programPower stat", () => {
      expect(STARTER_DECK.stats.programPower).toBeGreaterThan(0);
    });

    it("has ono_sendai set", () => {
      expect(STARTER_DECK.setId).toBe("ono_sendai");
    });
  });

  describe("STARTER_HEADWARE", () => {
    it("has correct id", () => {
      expect(STARTER_HEADWARE.id).toBe("head_basic");
    });

    it("is T0 tier", () => {
      expect(STARTER_HEADWARE.tier).toBe("T0");
    });

    it("has headware slot", () => {
      expect(STARTER_HEADWARE.slot).toBe("headware");
    });

    it("has apBonus stat", () => {
      expect(STARTER_HEADWARE.stats.apBonus).toBeGreaterThan(0);
    });

    it("has no set", () => {
      expect(STARTER_HEADWARE.setId).toBe(null);
    });
  });

  describe("STREET_DECK", () => {
    it("is T1", () => {
      expect(STREET_DECK.tier).toBe("T1");
    });

    it("has programPower and critBonusPct", () => {
      expect(STREET_DECK.stats.programPower).toBeGreaterThan(0);
      expect(STREET_DECK.stats.critBonusPct).toBeGreaterThan(0);
    });

    it("has upgrade slots", () => {
      expect(STREET_DECK.upgradeSlots).toBeGreaterThan(0);
    });

    it("has ono_sendai set", () => {
      expect(STREET_DECK.setId).toBe("ono_sendai");
    });
  });

  describe("MILITECH_EYES", () => {
    it("has correct slot", () => {
      expect(MILITECH_EYES.slot).toBe("eyeware");
    });

    it("has militech set", () => {
      expect(MILITECH_EYES.setId).toBe("militech");
    });

    it("has attackBonus and critBonusPct", () => {
      expect(MILITECH_EYES.stats.attackBonus).toBeGreaterThan(0);
      expect(MILITECH_EYES.stats.critBonusPct).toBeGreaterThan(0);
    });
  });

  describe("CHROME_GLOVES", () => {
    it("has gloves slot", () => {
      expect(CHROME_GLOVES.slot).toBe("gloves");
    });

    it("has militech set", () => {
      expect(CHROME_GLOVES.setId).toBe("militech");
    });
  });

  describe("CORPORATE_DECK", () => {
    it("is T2", () => {
      expect(CORPORATE_DECK.tier).toBe("T2");
    });

    it("has ono_sendai set", () => {
      expect(CORPORATE_DECK.setId).toBe("ono_sendai");
    });

    it("has programPower, defense, apRegenBonusPct", () => {
      expect(CORPORATE_DECK.stats.programPower).toBeGreaterThan(0);
      expect(CORPORATE_DECK.stats.defense).toBeGreaterThan(0);
      expect(CORPORATE_DECK.stats.apRegenBonusPct).toBeGreaterThan(0);
    });
  });

  describe("SUBDERMAL", () => {
    it("has bodysuit slot", () => {
      expect(SUBDERMAL.slot).toBe("bodysuit");
    });

    it("is T2", () => {
      expect(SUBDERMAL.tier).toBe("T2");
    });

    it("has defense, hpBonus, iceResistance", () => {
      expect(SUBDERMAL.stats.defense).toBeGreaterThan(0);
      expect(SUBDERMAL.stats.hpBonus).toBeGreaterThan(0);
      expect(SUBDERMAL.stats.iceResistance).toBeGreaterThan(0);
    });
  });

  describe("MILITECH_DECK", () => {
    it("is T3", () => {
      expect(MILITECH_DECK.tier).toBe("T3");
    });

    it("grants skill", () => {
      expect(MILITECH_DECK.stats.grantsSkillId).toBe("jackhammer");
    });

    it("has militech set", () => {
      expect(MILITECH_DECK.setId).toBe("militech");
    });
  });

  describe("TACTICAL_BODY", () => {
    it("is T3", () => {
      expect(TACTICAL_BODY.tier).toBe("T3");
    });

    it("has high defense and hp", () => {
      expect(TACTICAL_BODY.stats.defense).toBeGreaterThanOrEqual(20);
      expect(TACTICAL_BODY.stats.hpBonus).toBeGreaterThanOrEqual(50);
    });
  });

  describe("ARASAKA_DECK", () => {
    it("is T4", () => {
      expect(ARASAKA_DECK.tier).toBe("T4");
    });

    it("has arasaka set", () => {
      expect(ARASAKA_DECK.setId).toBe("arasaka");
    });

    it("grants viral skill", () => {
      expect(ARASAKA_DECK.stats.grantsSkillId).toBe("viral");
    });
  });

  describe("KEREZNIKOV", () => {
    it("has headware slot", () => {
      expect(KEREZNIKOV.slot).toBe("headware");
    });

    it("is T4", () => {
      expect(KEREZNIKOV.tier).toBe("T4");
    });

    it("has arasaka set", () => {
      expect(KEREZNIKOV.setId).toBe("arasaka");
    });

    it("has apBonus and apRegenBonusPct", () => {
      expect(KEREZNIKOV.stats.apBonus).toBeGreaterThan(0);
      expect(KEREZNIKOV.stats.apRegenBonusPct).toBeGreaterThan(0);
    });
  });

  describe("GHOST_DECK", () => {
    it("is T5", () => {
      expect(GHOST_DECK.tier).toBe("T5");
    });

    it("has no set", () => {
      expect(GHOST_DECK.setId).toBe(null);
    });

    it("grants bloodlust skill", () => {
      expect(GHOST_DECK.stats.grantsSkillId).toBe("bloodlust");
    });

    it("has high upgrade slots", () => {
      expect(GHOST_DECK.upgradeSlots).toBeGreaterThanOrEqual(5);
    });
  });

  describe("MASTER_DECK", () => {
    it("is T6", () => {
      expect(MASTER_DECK.tier).toBe("T6");
    });

    it("has very high programPower", () => {
      expect(MASTER_DECK.stats.programPower).toBeGreaterThanOrEqual(150);
    });

    it("grants omniscient skill", () => {
      expect(MASTER_DECK.stats.grantsSkillId).toBe("omniscient");
    });

    it("has no upgrade slots", () => {
      expect(MASTER_DECK.upgradeSlots).toBe(0);
    });

    it("has extraEffect", () => {
      expect(MASTER_DECK.stats.extraEffect.length).toBeGreaterThan(0);
    });
  });

  describe("MASTER_BODY", () => {
    it("is T6", () => {
      expect(MASTER_BODY.tier).toBe("T6");
    });

    it("has very high defense and hp", () => {
      expect(MASTER_BODY.stats.defense).toBeGreaterThanOrEqual(40);
      expect(MASTER_BODY.stats.hpBonus).toBeGreaterThanOrEqual(120);
    });

    it("has nanoware category", () => {
      expect(MASTER_BODY.category).toBe("nanoware");
    });
  });

  describe("ZION_TRODES", () => {
    it("is T6", () => {
      expect(ZION_TRODES.tier).toBe("T6");
    });

    it("has trodes slot", () => {
      expect(ZION_TRODES.slot).toBe("trodes");
    });

    it("has high apBonus and apRegenBonusPct", () => {
      expect(ZION_TRODES.stats.apBonus).toBeGreaterThan(0);
      expect(ZION_TRODES.stats.apRegenBonusPct).toBeGreaterThanOrEqual(100);
    });
  });

  describe("NANO_HIVE", () => {
    it("has implant slot", () => {
      expect(NANO_HIVE.slot).toBe("implant");
    });

    it("is T3", () => {
      expect(NANO_HIVE.tier).toBe("T3");
    });

    it("has extraEffect", () => {
      expect(NANO_HIVE.stats.extraEffect.length).toBeGreaterThan(0);
    });
  });

  describe("TRODES_NINJA", () => {
    it("has trodes slot", () => {
      expect(TRODES_NINJA.slot).toBe("trodes");
    });

    it("is T2", () => {
      expect(TRODES_NINJA.tier).toBe("T2");
    });
  });

  describe("BOOTS_GHOST", () => {
    it("has boots slot", () => {
      expect(BOOTS_GHOST.slot).toBe("boots");
    });

    it("is T2", () => {
      expect(BOOTS_GHOST.tier).toBe("T2");
    });
  });

  describe("Equipment by ID lookup", () => {
    it("can find STARTER_DECK by id", () => {
      const found = DEFAULT_EQUIPMENT.find((e) => e.id === "deck_basic");
      expect(found).toBe(STARTER_DECK);
    });

    it("can find MASTER_DECK by id", () => {
      const found = DEFAULT_EQUIPMENT.find((e) => e.id === "deck_master");
      expect(found).toBe(MASTER_DECK);
    });

    it("returns undefined for invalid id", () => {
      const found = DEFAULT_EQUIPMENT.find((e) => e.id === "invalid_id");
      expect(found).toBeUndefined();
    });
  });

  describe("Set assignments", () => {
    it("ono_sendai set has 3 items", () => {
      const items = DEFAULT_EQUIPMENT.filter((e) => e.setId === "ono_sendai");
      expect(items.length).toBe(3);
    });

    it("militech set has 3 items", () => {
      const items = DEFAULT_EQUIPMENT.filter((e) => e.setId === "militech");
      expect(items.length).toBe(3);
    });

    it("arasaka set has 2 items", () => {
      const items = DEFAULT_EQUIPMENT.filter((e) => e.setId === "arasaka");
      expect(items.length).toBe(2);
    });

    it("standalone items have null setId", () => {
      const standalone = DEFAULT_EQUIPMENT.filter((e) => e.setId === null);
      expect(standalone.length).toBeGreaterThan(0);
    });
  });
});
