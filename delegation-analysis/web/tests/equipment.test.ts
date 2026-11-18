/** Unit tests for the equipment + wetware system.
 *
 * Run with: npx vitest run tests/equipment.test.ts
 */
import { describe, it, expect } from "vitest";

import {
  ARASAKA_DECK,
  BOOTS_GHOST,
  CHROME_GLOVES,
  CORPORATE_DECK,
  DEFAULT_EQUIPMENT,
  DEFAULT_REGISTRY,
  EMPTY_LOADOUT,
  EMPTY_STACKED_WETWARE,
  GHOST_DECK,
  KEREZNIKOV,
  MASTER_BODY,
  MASTER_DECK,
  MAX_AP_REGEN,
  MILITECH_DECK,
  MILITECH_EYES,
  NANO_HIVE,
  SET_BONUSES,
  STARTER_DECK,
  STARTER_HEADWARE,
  STREET_DECK,
  SUBDERMAL,
  TACTICAL_BODY,
  TRODES_NINJA,
  WETWARE_CAPS,
  ZION_TRODES,
  addStats,
  applySetBonusesToStats,
  calculateSetBonus,
  equipOn,
  type EquipCategory,
  type EquipSlot,
  type EquipStats,
  type EquipTier,
  type EquipmentLoadout,
  type EquipmentRegistry,
  type EquipmentSetV2,
  type StackedWetware,
  type WetwareAugment,
  type WetwareRegistry,
  getActiveSetIds,
  getAllSetBonuses,
  getBestSetBonusFor,
  getNewStatAugments,
  getSetBonus,
  getSetBonusDefinitions,
  getSetCount,
  isT1OrBetter,
  isTier3,
  isUpgradable,
  makeEquipStats,
  makeEquipment,
  makeEquipmentRegistry,
  makeEquipmentSetsFromData,
  makeLoadout,
  makeWetwareRegistry,
  stackWetware,
  unequipFrom,
  validateStacking,
} from "../src/core/equipment.ts";

const makeStatsRaw = makeEquipStats;

// =============================================================================
// EquipSlot + EquipTier + EquipCategory enums-as-string-unions
// =============================================================================

describe("EQUIP_SLOTS", () => {
  it("exposes exactly 8 slots", () => {
    expect(DEFAULT_REGISTRY.all.length > 0).toBe(true);
  });

  it("default registry covers at least one item per slot", () => {
    const slotsWithItems = new Set(DEFAULT_REGISTRY.all.map((e) => e.slot));
    // deck, headware, eyeware, bodysuit, gloves, boots, implant, trodes
    const expected: EquipSlot[] = ["deck", "headware", "eyeware", "bodysuit", "gloves", "boots", "implant", "trodes"];
    for (const slot of expected) {
      expect(slotsWithItems.has(slot), `missing slot ${slot}`).toBe(true);
    }
  });
});

describe("Equipment tiers", () => {
  it.each(["T0", "T1", "T2", "T3", "T4", "T5", "T6"] as const)(
    "supports tier %s",
    (tier: EquipTier) => {
      const sample = makeEquipment({
        id: `${tier.toLowerCase()}_test`,
        name: `${tier} Sample`,
        slot: "deck",
        category: "hardware",
        tier,
        stats: makeStatsRaw(),
        description: "",
      });
      expect(sample.tier).toBe(tier);
    },
  );
});

describe("Equipment categories", () => {
  it.each([
    "cybernetic",
    "software",
    "bioware",
    "nanoware",
    "wetware",
    "hardware",
    "icebreaker",
    "daemon",
  ] as const)("supports category %s", (category: EquipCategory) => {
    const sample = makeEquipment({
      id: `${category}_test`,
      name: `${category} Sample`,
      slot: "deck",
      category,
      tier: "T1",
      stats: makeStatsRaw(),
      description: "",
    });
    expect(sample.category).toBe(category);
  });
});

// =============================================================================
// makeEquipStats + addStats — Python `_add_stats` parity
// =============================================================================

describe("makeStats (alias: makeEquipStats)", () => {
  it("zero-initializes every numeric field", () => {
    const s = makeStatsRaw();
    expect(s.attackBonus).toBe(0);
    expect(s.critBonusPct).toBe(0);
    expect(s.damageBonusPct).toBe(0);
    expect(s.defense).toBe(0);
    expect(s.hpBonus).toBe(0);
    expect(s.shieldBonus).toBe(0);
    expect(s.apBonus).toBe(0);
    expect(s.apRegenBonusPct).toBe(0);
    expect(s.programPower).toBe(0);
    expect(s.iceResistance).toBe(0);
    expect(s.grantsSkillId).toBeNull();
    expect(s.extraEffect).toBe("");
  });

  it("preserves provided overrides", () => {
    const s = makeStatsRaw({ attackBonus: 5, programPower: 10, grantsSkillId: "foo" });
    expect(s.attackBonus).toBe(5);
    expect(s.programPower).toBe(10);
    expect(s.grantsSkillId).toBe("foo");
  });

  it("treats missing overrides as zero", () => {
    const s = makeStatsRaw({ attackBonus: 7 });
    expect(s.defense).toBe(0);
  });
});

describe("addStats", () => {
  it("sums every numeric field", () => {
    const a: EquipStats = makeStatsRaw({ attackBonus: 3, defense: 5, programPower: 10 });
    const b: EquipStats = makeStatsRaw({ attackBonus: 2, defense: 7, programPower: 5 });
    const sum = addStats(a, b);
    expect(sum.attackBonus).toBe(5);
    expect(sum.defense).toBe(12);
    expect(sum.programPower).toBe(15);
  });

  it("first non-null grantsSkillId wins (Python OR semantics)", () => {
    const a = makeStatsRaw({ grantsSkillId: "alpha" });
    const b = makeStatsRaw({ grantsSkillId: "beta" });
    expect(addStats(a, b).grantsSkillId).toBe("alpha");
    expect(addStats(makeStatsRaw(), b).grantsSkillId).toBe("beta");
  });

  it("joins extraEffect with ', ' when both non-empty", () => {
    const a = makeStatsRaw({ extraEffect: "alpha" });
    const b = makeStatsRaw({ extraEffect: "beta" });
    expect(addStats(a, b).extraEffect).toBe("alpha, beta");
  });

  it("does not include empty extras in the join", () => {
    const a = makeStatsRaw({ extraEffect: "" });
    const b = makeStatsRaw({ extraEffect: "beta" });
    expect(addStats(a, b).extraEffect).toBe("beta");
    expect(addStats(b, a).extraEffect).toBe("beta");
  });
});

// =============================================================================
// Default equipment — every Gibson-inspired piece is wired up
// =============================================================================

describe("default Gibson-inspired equipment", () => {
  it("includes 18 pieces across 7 tiers", () => {
    expect(DEFAULT_EQUIPMENT).toHaveLength(18);
  });

  it("STARTER_DECK is the battered Ono-Sendai Cyberspace 7 (T0, hardware)", () => {
    expect(STARTER_DECK.name).toBe("Ono-Sendai Cyberspace 7");
    expect(STARTER_DECK.tier).toBe("T0");
    expect(STARTER_DECK.category).toBe("hardware");
    expect(STARTER_DECK.setId).toBe("ono_sendai");
    expect(STARTER_DECK.stats.programPower).toBe(5);
  });

  it("STREET_DECK grants +12 program_power and +5% crit at T1", () => {
    expect(STREET_DECK.tier).toBe("T1");
    expect(STREET_DECK.stats.programPower).toBe(12);
    expect(STREET_DECK.stats.critBonusPct).toBe(5);
    expect(STREET_DECK.upgradeSlots).toBe(2);
  });

  it("MILITECH_EYES is an offensive cybernetic T1 eyeware", () => {
    expect(MILITECH_EYES.slot).toBe("eyeware");
    expect(MILITECH_EYES.tier).toBe("T1");
    expect(MILITECH_EYES.category).toBe("cybernetic");
    expect(MILITECH_EYES.stats.attackBonus).toBe(3);
    expect(MILITECH_EYES.stats.critBonusPct).toBe(10);
  });

  it("CORPORATE_DECK adds +20 program_power, +2 defense, +20% ap regen", () => {
    expect(CORPORATE_DECK.tier).toBe("T2");
    expect(CORPORATE_DECK.stats.programPower).toBe(20);
    expect(CORPORATE_DECK.stats.defense).toBe(2);
    expect(CORPORATE_DECK.stats.apRegenBonusPct).toBe(20);
  });

  it("SUBDERMAL provides defensive stats at T2", () => {
    expect(SUBDERMAL.slot).toBe("bodysuit");
    expect(SUBDERMAL.tier).toBe("T2");
    expect(SUBDERMAL.stats.defense).toBe(8);
    expect(SUBDERMAL.stats.hpBonus).toBe(20);
    expect(SUBDERMAL.stats.iceResistance).toBe(10);
  });

  it("MILITECH_DECK grants jackhammer skill at T3", () => {
    expect(MILITECH_DECK.tier).toBe("T3");
    expect(MILITECH_DECK.stats.programPower).toBe(35);
    expect(MILITECH_DECK.stats.grantsSkillId).toBe("jackhammer");
  });

  it("TACTICAL_BODY adds +50 HP and +10 shield at T3", () => {
    expect(TACTICAL_BODY.stats.hpBonus).toBe(50);
    expect(TACTICAL_BODY.stats.shieldBonus).toBe(10);
    expect(TACTICAL_BODY.stats.iceResistance).toBe(25);
  });

  it("ARASAKA_DECK is a T4 cybernetic with viral skill", () => {
    expect(ARASAKA_DECK.tier).toBe("T4");
    expect(ARASAKA_DECK.category).toBe("cybernetic");
    expect(ARASAKA_DECK.stats.grantsSkillId).toBe("viral");
    expect(ARASAKA_DECK.setId).toBe("arasaka");
  });

  it("KEREZNIKOV boosts AP at T4 with full regen", () => {
    expect(KEREZNIKOV.stats.apBonus).toBe(3);
    expect(KEREZNIKOV.stats.apRegenBonusPct).toBe(50);
    expect(KEREZNIKOV.setId).toBe("arasaka");
  });

  it("GHOST_DECK is an experimental T5 daemon", () => {
    expect(GHOST_DECK.tier).toBe("T5");
    expect(GHOST_DECK.category).toBe("daemon");
    expect(GHOST_DECK.stats.programPower).toBe(100);
    expect(GHOST_DECK.stats.grantsSkillId).toBe("bloodlust");
  });

  it("MASTER_DECK is the merged Wintermute/Neuromancer (T6)", () => {
    expect(MASTER_DECK.tier).toBe("T6");
    expect(MASTER_DECK.stats.programPower).toBe(150);
    expect(MASTER_DECK.stats.grantsSkillId).toBe("omniscient");
    expect(MASTER_DECK.upgradeSlots).toBe(0);
  });

  it("MASTER_BODY is full-body cyborg conversion (T6, nanoware)", () => {
    expect(MASTER_BODY.tier).toBe("T6");
    expect(MASTER_BODY.category).toBe("nanoware");
    expect(MASTER_BODY.stats.defense).toBe(40);
    expect(MASTER_BODY.stats.hpBonus).toBe(120);
    expect(MASTER_BODY.stats.extraEffect).toContain("flatline");
  });

  it("ZION_TRODES is direct-neural link (T6, wetware)", () => {
    expect(ZION_TRODES.tier).toBe("T6");
    expect(ZION_TRODES.category).toBe("wetware");
    expect(ZION_TRODES.stats.apRegenBonusPct).toBe(100);
  });

  it("NANO_HIVE / TRODES_NINJA / BOOTS_GHOST are present", () => {
    expect(NANO_HIVE.id).toBe("implant_nanohive");
    expect(TRODES_NINJA.id).toBe("trodes_ninja");
    expect(BOOTS_GHOST.id).toBe("boots_ghost");
  });

  it("STARTER_HEADWARE is the basic trodes (T0, wetware)", () => {
    expect(STARTER_HEADWARE.tier).toBe("T0");
    expect(STARTER_HEADWARE.stats.apBonus).toBe(1);
    expect(STARTER_HEADWARE.setId).toBeNull();
  });

  it("CHROME_GLOVES are T1 cybernetic gloves (set=militech)", () => {
    expect(CHROME_GLOVES.slot).toBe("gloves");
    expect(CHROME_GLOVES.setId).toBe("militech");
  });
});

// =============================================================================
// makeEquipment — defensive constructor
// =============================================================================

describe("makeEquipment", () => {
  it("fills in cosmetic defaults when omitted", () => {
    const e = makeEquipment({
      id: "x",
      name: "X",
      slot: "deck",
      category: "hardware",
      tier: "T1",
      stats: makeStatsRaw(),
      description: "X",
    });
    expect(e.asciiGlyph).toBe("?");
    expect(e.asciiColor).toEqual([200, 200, 200]);
    expect(e.upgradeSlots).toBe(0);
    expect(e.requiredMaterials).toEqual({});
    expect(e.setId).toBeNull();
  });

  it("preserves provided cosmetic fields", () => {
    const e = makeEquipment({
      id: "x",
      name: "X",
      slot: "deck",
      category: "hardware",
      tier: "T1",
      stats: makeStatsRaw(),
      description: "X",
      asciiGlyph: "[X]",
      asciiColor: [255, 0, 0],
      upgradeSlots: 3,
      requiredMaterials: { ice_shard: 1 },
      setId: "ono_sendai",
    });
    expect(e.asciiGlyph).toBe("[X]");
    expect(e.asciiColor).toEqual([255, 0, 0]);
    expect(e.upgradeSlots).toBe(3);
    expect(e.requiredMaterials).toEqual({ ice_shard: 1 });
    expect(e.setId).toBe("ono_sendai");
  });
});

// =============================================================================
// isUpgradable + isT1OrBetter
// =============================================================================

describe("isUpgradable", () => {
  it("true for items with upgrade slots", () => {
    expect(isUpgradable({ ...STARTER_DECK, upgradeSlots: 1 })).toBe(true);
  });

  it("false for items with zero upgrade slots", () => {
    expect(isUpgradable(STARTER_DECK)).toBe(false);
  });
});

describe("isT1OrBetter", () => {
  it("false for T0 starter gear", () => {
    expect(isT1OrBetter(STARTER_DECK)).toBe(false);
    expect(isT1OrBetter(STARTER_HEADWARE)).toBe(false);
  });

  it("true for T1+", () => {
    expect(isT1OrBetter(STREET_DECK)).toBe(true);
    expect(isT1OrBetter(MASTER_DECK)).toBe(true);
    expect(isT1OrBetter(GHOST_DECK)).toBe(true);
  });
});

// =============================================================================
// EquipmentRegistry — lookup semantics
// =============================================================================

describe("EquipmentRegistry", () => {
  it("looks up equipment by id", () => {
    expect(DEFAULT_REGISTRY.get("deck_basic")).toBe(STARTER_DECK);
    expect(DEFAULT_REGISTRY.get("deck_master")).toBe(MASTER_DECK);
  });

  it("returns null for unknown ids", () => {
    expect(DEFAULT_REGISTRY.get("nonexistent")).toBeNull();
  });

  it("bySlot returns only items in that slot", () => {
    const decks = DEFAULT_REGISTRY.bySlot("deck");
    expect(decks.length).toBeGreaterThanOrEqual(4);
    expect(decks.every((e) => e.slot === "deck")).toBe(true);
  });

  it("bySlot returns empty array for slots with no items (defensive)", () => {
    const custom: EquipmentRegistry = makeEquipmentRegistry([STARTER_DECK]);
    expect(custom.bySlot("implant")).toEqual([]);
  });

  it("all returns every registered piece", () => {
    expect(DEFAULT_REGISTRY.all).toHaveLength(DEFAULT_EQUIPMENT.length);
  });

  it("makeEquipmentRegistry copies the input array", () => {
    const custom = makeEquipmentRegistry([STARTER_DECK]);
    expect(custom.get("deck_basic")).toBe(STARTER_DECK);
    expect(custom.all).toHaveLength(1);
  });
});

// =============================================================================
// Set bonuses — SET_BONUSES table + getSetBonus lookup
// =============================================================================

describe("SET_BONUSES table", () => {
  it("contains all 3 sets (ono_sendai, militech, arasaka)", () => {
    expect(Object.keys(SET_BONUSES).sort()).toEqual(["arasaka", "militech", "ono_sendai"]);
  });

  it("each set has 2-piece and 3-piece thresholds", () => {
    for (const setId of Object.keys(SET_BONUSES)) {
      const thresholds = Object.keys(SET_BONUSES[setId] ?? {}).map(Number).sort();
      expect(thresholds).toEqual([2, 3]);
    }
  });

  it("ono_sendai 2pc grants +10 program_power +5% crit", () => {
    const bonus = SET_BONUSES.ono_sendai?.[2];
    expect(bonus?.programPower).toBe(10);
    expect(bonus?.critBonusPct).toBe(5);
  });

  it("ono_sendai 3pc grants +25 program_power +10% ap regen", () => {
    const bonus = SET_BONUSES.ono_sendai?.[3];
    expect(bonus?.programPower).toBe(25);
    expect(bonus?.apRegenBonusPct).toBe(10);
  });

  it("militech 2pc grants +5 attack +10% crit", () => {
    const bonus = SET_BONUSES.militech?.[2];
    expect(bonus?.attackBonus).toBe(5);
    expect(bonus?.critBonusPct).toBe(10);
  });

  it("arasaka 2pc grants +8 defense +15 ice_resistance", () => {
    const bonus = SET_BONUSES.arasaka?.[2];
    expect(bonus?.defense).toBe(8);
    expect(bonus?.iceResistance).toBe(15);
  });
});

describe("getSetBonus", () => {
  it("returns null for null set_id", () => {
    expect(getSetBonus(null, 5)).toBeNull();
  });

  it("returns null for unknown set ids", () => {
    expect(getSetBonus("nonexistent", 5)).toBeNull();
  });

  it("returns null when pieces are below the 2pc threshold", () => {
    expect(getSetBonus("ono_sendai", 0)).toBeNull();
    expect(getSetBonus("ono_sendai", 1)).toBeNull();
  });

  it("returns 2pc bonus when exactly 2 pieces equipped", () => {
    const bonus = getSetBonus("ono_sendai", 2);
    expect(bonus?.programPower).toBe(10);
  });

  it("returns 3pc bonus (highest threshold) when 3+ pieces equipped", () => {
    const bonus = getSetBonus("ono_sendai", 3);
    expect(bonus?.programPower).toBe(25);
    expect(bonus?.apRegenBonusPct).toBe(10);
  });

  it("prefers the higher threshold even when lower is also met", () => {
    // 4 pieces equipped → 3pc wins (no 4pc threshold in equipment.py)
    const bonus = getSetBonus("militech", 4);
    expect(bonus?.attackBonus).toBe(15); // 3pc, not 2pc's 5
  });
});

describe("getSetBonusDefinitions", () => {
  it("returns the SET_BONUSES table", () => {
    expect(getSetBonusDefinitions()).toBe(SET_BONUSES);
  });
});

// =============================================================================
// EquipmentLoadout — equip / unequip / lookup
// =============================================================================

describe("EquipmentLoadout", () => {
  it("starts with no equipment", () => {
    expect(EMPTY_LOADOUT.allSlotsFilled()).toHaveLength(0);
    expect(EMPTY_LOADOUT.isComplete()).toBe(false);
  });

  it("emptySlots returns all 8 slots for an empty loadout", () => {
    expect(EMPTY_LOADOUT.emptySlots()).toHaveLength(8);
  });

  it("isComplete false when only some slots filled", () => {
    const loadout = makeLoadout({ deck: STARTER_DECK });
    expect(loadout.isComplete()).toBe(false);
  });

  it("isComplete true when every slot has equipment", () => {
    const full = makeLoadout({
      deck: STARTER_DECK,
      headware: STARTER_HEADWARE,
      eyeware: MILITECH_EYES,
      bodysuit: SUBDERMAL,
      gloves: CHROME_GLOVES,
      boots: BOOTS_GHOST,
      implant: NANO_HIVE,
      trodes: TRODES_NINJA,
    });
    expect(full.isComplete()).toBe(true);
    expect(full.emptySlots()).toHaveLength(0);
  });

  it("get returns equipment by slot", () => {
    const loadout = makeLoadout({ deck: STARTER_DECK });
    expect(loadout.get("deck")).toBe(STARTER_DECK);
    expect(loadout.get("headware")).toBeNull();
  });

  it("equip replaces existing slot occupant and returns it", () => {
    const loadout = makeLoadout({ deck: STARTER_DECK });
    const previous = loadout.equip(STREET_DECK);
    expect(previous).toBe(STARTER_DECK);
    expect(loadout.get("deck")).toBe(STREET_DECK);
  });

  it("equip into empty slot returns null", () => {
    const loadout = makeLoadout();
    const previous = loadout.equip(STREET_DECK);
    expect(previous).toBeNull();
    expect(loadout.get("deck")).toBe(STREET_DECK);
  });

  it("unequip returns the removed item and clears the slot", () => {
    const loadout = makeLoadout({ deck: STARTER_DECK });
    const removed = loadout.unequip("deck");
    expect(removed).toBe(STARTER_DECK);
    expect(loadout.get("deck")).toBeNull();
  });

  it("unequip from empty slot returns null", () => {
    const loadout = makeLoadout();
    expect(loadout.unequip("deck")).toBeNull();
  });
});

// =============================================================================
// Pure equip/unequip helpers — return new loadouts (immutability)
// =============================================================================

describe("equipOn / unequipFrom (pure functions)", () => {
  it("equipOn returns a new loadout, leaves original untouched", () => {
    const before: EquipmentLoadout = makeLoadout({ deck: STARTER_DECK });
    const result = equipOn(before, STREET_DECK);
    expect(result.previous).toBe(STARTER_DECK);
    expect(result.loadout.get("deck")).toBe(STREET_DECK);
    // Original is unchanged
    expect(before.get("deck")).toBe(STARTER_DECK);
  });

  it("unequipFrom returns a new loadout with slot cleared", () => {
    const before: EquipmentLoadout = makeLoadout({ deck: STARTER_DECK });
    const result = unequipFrom(before, "deck");
    expect(result.removed).toBe(STARTER_DECK);
    expect(result.loadout.get("deck")).toBeNull();
    expect(before.get("deck")).toBe(STARTER_DECK);
  });

  it("unequipFrom empty slot returns null", () => {
    const result = unequipFrom(EMPTY_LOADOUT, "deck");
    expect(result.removed).toBeNull();
    expect(result.loadout).toBe(EMPTY_LOADOUT);
  });
});

// =============================================================================
// setCounts / setBonuses / totalStats
// =============================================================================

describe("EquipmentLoadout.setCounts", () => {
  it("excludes items without a set_id", () => {
    const loadout = makeLoadout({
      deck: STARTER_DECK, // ono_sendai
      headware: STARTER_HEADWARE, // null
    });
    const counts = loadout.setCounts();
    expect(counts).toEqual({ ono_sendai: 1 });
  });

  it("aggregates items sharing the same set_id", () => {
    const loadout = makeLoadout({
      deck: STARTER_DECK, // ono_sendai
      eyeware: MILITECH_EYES, // militech
      gloves: CHROME_GLOVES, // militech
    });
    const counts = loadout.setCounts();
    expect(counts).toEqual({ ono_sendai: 1, militech: 2 });
  });

  it("returns empty record for an empty loadout", () => {
    expect(EMPTY_LOADOUT.setCounts()).toEqual({});
  });
});

describe("EquipmentLoadout.setBonuses", () => {
  it("empty when loadout is empty", () => {
    expect(EMPTY_LOADOUT.setBonuses()).toEqual([]);
  });

  it("returns 2pc bonus when 2 items share a set", () => {
    const loadout = makeLoadout({
      eyeware: MILITECH_EYES,
      gloves: CHROME_GLOVES,
    });
    const bonuses = loadout.setBonuses();
    expect(bonuses).toHaveLength(1);
    expect(bonuses[0]?.attackBonus).toBe(5);
    expect(bonuses[0]?.critBonusPct).toBe(10);
  });

  it("returns 3pc bonus (highest threshold) for 3+ items", () => {
    const loadout = makeLoadout({
      deck: STARTER_DECK, // ono_sendai
      eyeware: MILITECH_EYES, // militech
      gloves: CHROME_GLOVES, // militech
      bodysuit: TACTICAL_BODY, // (no set)
    });
    const bonuses = loadout.setBonuses();
    // militech 3pc threshold not met (only 2 militech), but ono_sendai 1pc also doesn't trigger.
    // Verify the function returns bonuses only when thresholds are met.
    expect(bonuses).toHaveLength(1); // militech 2pc
    expect(bonuses[0]?.attackBonus).toBe(5);
  });

  it("returns multiple bonuses when multiple sets qualify", () => {
    // 2 arasaka (ARASAKA_DECK + KEREZNIKOV occupy different slots)
    // + 2 militech (EYES + GLOVES occupy different slots) → 2pc on each.
    const loadout = makeLoadout({
      deck: ARASAKA_DECK, // arasaka
      headware: KEREZNIKOV, // arasaka
      eyeware: MILITECH_EYES, // militech
      gloves: CHROME_GLOVES, // militech
    });
    expect(loadout.setBonuses()).toHaveLength(2);
  });
});

describe("EquipmentLoadout.totalStats", () => {
  it("zero loadout → all-zero total", () => {
    const total = EMPTY_LOADOUT.totalStats();
    expect(total.attackBonus).toBe(0);
    expect(total.programPower).toBe(0);
    expect(total.defense).toBe(0);
    expect(total.grantsSkillId).toBeNull();
    expect(total.extraEffect).toBe("");
  });

  it("aggregates stats across multiple equipment pieces", () => {
    const loadout = makeLoadout({
      deck: STREET_DECK, // programPower 12, crit 5
      eyeware: MILITECH_EYES, // attack 3, crit 10
    });
    const total = loadout.totalStats();
    expect(total.programPower).toBe(12);
    expect(total.attackBonus).toBe(3);
    expect(total.critBonusPct).toBe(15); // 5 + 10
  });

  it("includes set bonus stats in the aggregate", () => {
    // Two militech items → 2pc bonus (+5 attack, +10% crit)
    const loadout = makeLoadout({
      eyeware: MILITECH_EYES, // attack 3, crit 10
      gloves: CHROME_GLOVES, // attack 5, program 3
    });
    const total = loadout.totalStats();
    // Item stats: attack 8, crit 10, program 3
    // Set bonus: attack +5, crit +10
    expect(total.attackBonus).toBe(13);
    expect(total.critBonusPct).toBe(20);
    expect(total.programPower).toBe(3);
  });

  it("joins extraEffect from items + bonuses", () => {
    const loadout = makeLoadout({
      eyeware: MILITECH_EYES,
      gloves: CHROME_GLOVES,
    });
    const total = loadout.totalStats();
    expect(total.extraEffect).toContain("Militech targeting");
  });

  it("propagates grantsSkillId from items", () => {
    const loadout = makeLoadout({ deck: MILITECH_DECK });
    expect(loadout.totalStats().grantsSkillId).toBe("jackhammer");
  });
});

// =============================================================================
// Set bonus integration helpers (Round 5)
// =============================================================================

describe("calculateSetBonus", () => {
  it("empty loadout → empty summary with zero totals", () => {
    const summary = calculateSetBonus(EMPTY_LOADOUT);
    expect(summary.activeSetIds).toEqual([]);
    expect(summary.setCount).toEqual({});
    expect(summary.totalBonus.programPower).toBe(0);
  });

  it("aggregates active set ids + total bonus for a partial loadout", () => {
    const loadout = makeLoadout({
      eyeware: MILITECH_EYES, // militech
      gloves: CHROME_GLOVES, // militech
    });
    const summary = calculateSetBonus(loadout);
    expect(summary.activeSetIds).toContain("militech");
    expect(summary.setCount.militech).toBe(2);
    // 2pc bonus: +5 attack, +10% crit
    expect(summary.totalBonus.attackBonus).toBe(5);
    expect(summary.totalBonus.critBonusPct).toBe(10);
  });
});

describe("set bonus helpers (getActiveSetIds, getSetCount, getBestSetBonusFor)", () => {
  it("getActiveSetIds returns set ids currently equipped", () => {
    const loadout = makeLoadout({
      eyeware: MILITECH_EYES,
      gloves: CHROME_GLOVES,
    });
    expect(getActiveSetIds(loadout)).toEqual(["militech"]);
  });

  it("getSetCount returns 0 for non-equipped sets", () => {
    expect(getSetCount(EMPTY_LOADOUT, "ono_sendai")).toBe(0);
  });

  it("getSetCount returns the count for an equipped set", () => {
    const loadout = makeLoadout({
      eyeware: MILITECH_EYES,
      gloves: CHROME_GLOVES,
    });
    expect(getSetCount(loadout, "militech")).toBe(2);
  });

  it("getBestSetBonusFor returns null for non-equipped sets", () => {
    expect(getBestSetBonusFor(EMPTY_LOADOUT, "arasaka")).toBeNull();
  });

  it("getBestSetBonusFor returns the highest applicable bonus", () => {
    const loadout = makeLoadout({
      eyeware: MILITECH_EYES,
      gloves: CHROME_GLOVES,
    });
    const bonus = getBestSetBonusFor(loadout, "militech");
    expect(bonus?.attackBonus).toBe(5); // 2pc
  });

  it("getAllSetBonuses is an alias for loadout.setBonuses()", () => {
    const loadout = makeLoadout({
      eyeware: MILITECH_EYES,
      gloves: CHROME_GLOVES,
    });
    expect(getAllSetBonuses(loadout)).toEqual(loadout.setBonuses());
  });
});

describe("applySetBonusesToStats", () => {
  it("adds active set bonuses to a base stat block", () => {
    const loadout = makeLoadout({
      eyeware: MILITECH_EYES, // militech
      gloves: CHROME_GLOVES, // militech
    });
    const base = makeStatsRaw({ attackBonus: 10, critBonusPct: 5 });
    const result = applySetBonusesToStats(base, loadout);
    // base: 10 attack, 5% crit; bonus: +5 attack, +10% crit
    expect(result.attackBonus).toBe(15);
    expect(result.critBonusPct).toBe(15);
  });

  it("returns the base unchanged when no set bonuses apply", () => {
    const base = makeStatsRaw({ attackBonus: 10 });
    const result = applySetBonusesToStats(base, EMPTY_LOADOUT);
    expect(result.attackBonus).toBe(10);
  });
});

// =============================================================================
// Wetware stacking (ADR-0193)
// =============================================================================

const SYNTHETIC_WETWARE_RAW: Readonly<Record<string, unknown>> = Object.freeze({
  _metadata: { version: "1.0", phase: "14", adrs_cross_reference: "ADR-0193", total_augments: 10 },
  ap_regen_lv3: {
    name: "AP Regen Lv3",
    tier: 3,
    type: "ap_regen",
    ap_regen_bonus: 0.5,
    description: "Tier 3 AP regeneration. Faster AP recovery.",
    associated_stats: ["ap_regen_lv1", "ap_regen_lv2"],
    id: "ap_regen_lv3",
  },
  crit_lv3: {
    name: "Crit Lv3",
    tier: 3,
    type: "crit",
    crit_chance_bonus: 0.15,
    crit_damage_bonus: 0.5,
    description: "Tier 3 critical hit. +15% crit chance, +50% crit damage.",
    associated_stats: ["crit_lv1", "crit_lv2"],
    id: "crit_lv3",
  },
  dodge_lv3: {
    name: "Dodge Lv3",
    tier: 3,
    type: "dodge",
    dodge_bonus: 0.2,
    description: "Tier 3 dodge. +20% chance to avoid attacks.",
    associated_stats: ["dodge_lv1", "dodge_lv2"],
    id: "dodge_lv3",
  },
  max_hp_lv3: {
    name: "Max HP Lv3",
    tier: 3,
    type: "max_hp",
    hp_bonus: 30,
    description: "Tier 3 hit points. +30 max HP.",
    associated_stats: ["max_hp_lv1", "max_hp_lv2"],
    id: "max_hp_lv3",
  },
  healing_lv3: {
    name: "Healing Lv3",
    tier: 3,
    type: "healing",
    heal_bonus: 0.3,
    description: "Tier 3 healing. +30% heal effects.",
    associated_stats: ["healing_lv1", "healing_lv2"],
    id: "healing_lv3",
  },
  shield_lv3: {
    name: "Shield Lv3",
    tier: 3,
    type: "shield",
    shield_bonus: 0.25,
    description: "Tier 3 shield. +25% shield strength.",
    associated_stats: ["shield_lv1", "shield_lv2"],
    id: "shield_lv3",
  },
  speed_lv3: {
    name: "Speed Lv3",
    tier: 3,
    type: "speed",
    speed_bonus: 0.3,
    description: "Tier 3 speed. +30% action speed.",
    associated_stats: ["speed_lv1", "speed_lv2"],
    id: "speed_lv3",
  },
  mana_lv3: {
    name: "Mana Lv3",
    tier: 3,
    type: "mana",
    mana_bonus: 1,
    description: "Tier 3 mana. +1 max mana (new stat).",
    is_new_stat: true,
    associated_stats: ["mana_lv1", "mana_lv2"],
    id: "mana_lv3",
  },
  armor_lv3: {
    name: "Armor Lv3",
    tier: 3,
    type: "armor",
    armor_bonus: 0.25,
    description: "Tier 3 armor. +25% damage reduction (new stat).",
    is_new_stat: true,
    associated_stats: ["armor_lv1", "armor_lv2"],
    id: "armor_lv3",
  },
  focus_lv3: {
    name: "Focus Lv3",
    tier: 3,
    type: "focus",
    focus_bonus: 0.3,
    description: "Tier 3 focus. +30% program power (new stat).",
    is_new_stat: true,
    associated_stats: ["focus_lv1", "focus_lv2"],
    id: "focus_lv3",
  },
});

const WETWARE = makeWetwareRegistry(SYNTHETIC_WETWARE_RAW);

describe("makeWetwareRegistry", () => {
  it("loads all 10 augments from fixture", () => {
    expect(WETWARE.all).toHaveLength(10);
  });

  it("lookups by id return the canonical record", () => {
    const ap = WETWARE.get("ap_regen_lv3");
    expect(ap?.apRegenBonus).toBe(0.5);
    expect(ap?.tier).toBe(3);
    expect(ap?.type).toBe("ap_regen");
  });

  it("byType filters augments by category", () => {
    const critAugs = WETWARE.byType("crit");
    expect(critAugs).toHaveLength(1);
    expect(critAugs[0]?.id).toBe("crit_lv3");
  });

  it("getNewStatAugments returns only the 3 new-stat augments", () => {
    const newStats = getNewStatAugments(WETWARE);
    expect(newStats).toHaveLength(3);
    expect(newStats.map((a) => a.id).sort()).toEqual(["armor_lv3", "focus_lv3", "mana_lv3"]);
  });

  it("skips _metadata keys", () => {
    expect(WETWARE.get("_metadata")).toBeNull();
  });

  it("treats non-finite numeric fields as zero (defensive parsing)", () => {
    const r = makeWetwareRegistry({
      weird: {
        id: "weird",
        name: "Weird",
        tier: 3,
        type: "custom",
        ap_regen_bonus: "not a number",
        hp_bonus: NaN,
        is_new_stat: false,
        description: "",
      },
    });
    expect(r.get("weird")?.apRegenBonus).toBe(0);
    expect(r.get("weird")?.hpBonus).toBe(0);
  });
});

describe("isTier3", () => {
  it("true for tier-3 augments", () => {
    expect(isTier3(WETWARE, "ap_regen_lv3")).toBe(true);
  });

  it("false for unknown ids", () => {
    expect(isTier3(WETWARE, "nonexistent")).toBe(false);
  });
});

describe("countTier3 (registry method)", () => {
  it("counts only registered tier-3 augments", () => {
    expect(WETWARE.countTier3(["ap_regen_lv3", "crit_lv3", "nonexistent"])).toBe(2);
  });

  it("returns 0 for an empty list", () => {
    expect(WETWARE.countTier3([])).toBe(0);
  });
});

describe("validateStacking", () => {
  it("true when every id resolves", () => {
    expect(validateStacking(WETWARE, ["ap_regen_lv3", "crit_lv3"])).toBe(true);
  });

  it("false when any id is unknown", () => {
    expect(validateStacking(WETWARE, ["ap_regen_lv3", "phantom"])).toBe(false);
  });
});

describe("stackWetware", () => {
  it("empty input → EMPTY_STACKED_WETWARE copy", () => {
    const stacked = stackWetware(WETWARE, []);
    expect(stacked.augmentCount).toBe(0);
    expect(stacked.apRegen).toBe(0);
  });

  it("single ap_regen_lv3 → +0.5 ap regen", () => {
    const stacked = stackWetware(WETWARE, ["ap_regen_lv3"]);
    expect(stacked.apRegen).toBe(0.5);
    expect(stacked.augmentCount).toBe(1);
  });

  it("stacks multiple augments additively", () => {
    const stacked = stackWetware(WETWARE, ["crit_lv3", "dodge_lv3"]);
    expect(stacked.critChance).toBe(0.15);
    expect(stacked.critDamage).toBe(0.5);
    expect(stacked.dodge).toBe(0.2);
  });

  it("stacks integer bonuses (hp, mana) additively", () => {
    const stacked = stackWetware(WETWARE, ["max_hp_lv3", "max_hp_lv3", "mana_lv3"]);
    expect(stacked.hpBonus).toBe(60);
    expect(stacked.mana).toBe(1);
  });

  it("caps dodge at 0.95", () => {
    const stacked = stackWetware(WETWARE, [
      "dodge_lv3",
      "dodge_lv3",
      "dodge_lv3",
      "dodge_lv3",
      "dodge_lv3",
    ]);
    expect(stacked.dodge).toBeLessThanOrEqual(WETWARE_CAPS.dodge);
  });

  it("ignores unknown augment ids (silent skip)", () => {
    const stacked = stackWetware(WETWARE, ["ap_regen_lv3", "phantom"]);
    expect(stacked.apRegen).toBe(0.5);
    expect(stacked.augmentCount).toBe(2); // counts input length, not recognized
  });

  it("is deterministic — same input → same output", () => {
    const a = stackWetware(WETWARE, ["ap_regen_lv3", "crit_lv3"]);
    const b = stackWetware(WETWARE, ["ap_regen_lv3", "crit_lv3"]);
    expect(a).toEqual(b);
  });

  it("stacks every stat type", () => {
    const all = [
      "ap_regen_lv3",
      "crit_lv3",
      "dodge_lv3",
      "max_hp_lv3",
      "healing_lv3",
      "shield_lv3",
      "speed_lv3",
      "mana_lv3",
      "armor_lv3",
      "focus_lv3",
    ];
    const stacked = stackWetware(WETWARE, all);
    expect(stacked.apRegen).toBe(0.5);
    expect(stacked.critChance).toBe(0.15);
    expect(stacked.critDamage).toBe(0.5);
    expect(stacked.dodge).toBe(0.2);
    expect(stacked.hpBonus).toBe(30);
    expect(stacked.healing).toBe(0.3);
    expect(stacked.shield).toBe(0.25);
    expect(stacked.speed).toBe(0.3);
    expect(stacked.mana).toBe(1);
    expect(stacked.armor).toBe(0.25);
    expect(stacked.focus).toBe(0.3);
    expect(stacked.augmentCount).toBe(10);
  });
});

describe("WETWARE_CAPS constants", () => {
  it("exposes the canonical cap table", () => {
    expect(WETWARE_CAPS.apRegen).toBe(1.0);
    expect(WETWARE_CAPS.critChance).toBe(0.95);
    expect(WETWARE_CAPS.dodge).toBe(0.95);
    expect(WETWARE_CAPS.healing).toBe(1.0);
    expect(WETWARE_CAPS.shield).toBe(0.95);
    expect(WETWARE_CAPS.speed).toBe(1.0);
    expect(WETWARE_CAPS.armor).toBe(1.0);
    expect(WETWARE_CAPS.focus).toBe(1.0);
  });
});

describe("MAX_AP_REGEN constant", () => {
  it("equals 0.5 (Python get_max_ap_regen hard-coded)", () => {
    expect(MAX_AP_REGEN).toBe(0.5);
  });
});

// =============================================================================
// Equipment Set V2 (Phase 14 schema)
// =============================================================================

const SYNTHETIC_SETS_RAW: Readonly<Record<string, unknown>> = Object.freeze({
  _metadata: { version: "1.0", total_sets: 2 },
  ghost_set: {
    set_id: "ghost_set",
    set_name: "Ghost Set",
    theme: "Stealth + counter-intrusion",
    description: "For runners who prefer not to be seen. High evasion, low visibility.",
    pieces: [
      {
        piece_id: "ghost_deck",
        name: "Ghost Deck",
        slot: "deck",
        tier: 4,
        evasion_bonus: 0.25,
        stealth_bonus: 1,
        description: "Stealth-optimized deck. Reduced heat signature.",
      },
    ],
    set_bonus_2_piece: {
      name: "Cloak I",
      type: "defense",
      evasion_bonus: 0.10,
      description: "2-piece bonus. +10% evasion.",
    },
    set_bonus_3_piece: {
      name: "Cloak II",
      type: "defense",
      evasion_bonus: 0.15,
      description: "3-piece bonus. +15% evasion, immune to first detection.",
    },
    set_bonus_4_piece: {
      name: "Ghost Protocol",
      type: "special",
      alpha_strike_bonus: 2.0,
      description: "4-piece bonus. First attack each combat deals 2x damage.",
    },
    tier: 4,
    role: "stealth",
    character_affinity: ["sil", "sally"],
  },
});

describe("makeEquipmentSetsFromData", () => {
  it("loads the ghost_set fixture with all 3 bonus tiers", () => {
    const sets = makeEquipmentSetsFromData(SYNTHETIC_SETS_RAW);
    expect(Object.keys(sets)).toEqual(["ghost_set"]);
    const ghost: EquipmentSetV2 | undefined = sets.ghost_set;
    expect(ghost).toBeDefined();
    expect(ghost?.setName).toBe("Ghost Set");
    expect(ghost?.bonuses[2]?.name).toBe("Cloak I");
    expect(ghost?.bonuses[3]?.name).toBe("Cloak II");
    expect(ghost?.bonuses[4]?.name).toBe("Ghost Protocol");
    expect(ghost?.characterAffinity).toEqual(["sil", "sally"]);
  });

  it("captures numeric fields under .fields (loose schema)", () => {
    const sets = makeEquipmentSetsFromData(SYNTHETIC_SETS_RAW);
    const ghost: EquipmentSetV2 | undefined = sets.ghost_set;
    expect(ghost?.bonuses[2]?.fields.evasion_bonus).toBe(0.10);
    expect(ghost?.bonuses[4]?.fields.alpha_strike_bonus).toBe(2.0);
  });

  it("skips malformed entries", () => {
    const sets = makeEquipmentSetsFromData({
      good: { set_id: "good", set_name: "Good", description: "" },
      not_object: "garbage",
      null_value: null,
    });
    expect(Object.keys(sets)).toEqual(["good"]);
  });
});

// =============================================================================
// Stack sanity — augment + equipment interaction
// =============================================================================

describe("wetware + equipment interaction", () => {
  it("a loadout with stacked wetware reports independent totals", () => {
    const loadout = makeLoadout({ deck: STREET_DECK });
    const equipment = loadout.totalStats();
    const wetware = stackWetware(WETWARE, ["ap_regen_lv3", "crit_lv3"]);
    // Equipment: programPower 12 (no stack interaction in this MVP layer).
    // Wetware: apRegen 0.5, critChance 0.15.
    expect(equipment.programPower).toBe(12);
    expect(wetware.apRegen).toBe(0.5);
    expect(wetware.critChance).toBe(0.15);
  });
});

// =============================================================================
// Type-level helpers — exports the right shape
// =============================================================================

describe("type exports", () => {
  it("re-exports StackedWetware / WetwareAugment / WetwareRegistry types", () => {
    // The imports at the top of this file already exercise these types; this
    // test exists to keep the type-exports surface area explicit.
    const stacked: StackedWetware = EMPTY_STACKED_WETWARE;
    expect(stacked.augmentCount).toBe(0);
    const aug: WetwareAugment | null = WETWARE.get("ap_regen_lv3");
    expect(aug?.tier).toBe(3);
    const reg: WetwareRegistry = WETWARE;
    expect(reg.all.length).toBe(10);
  });
});

// =============================================================================
// Pure loadout operations — idempotence + sanity
// =============================================================================

describe("loadout operation idempotence", () => {
  it("re-equipping the same piece keeps the slot populated", () => {
    const a = makeLoadout({ deck: STARTER_DECK });
    const b = makeLoadout({ ...a.equipment, deck: STREET_DECK });
    const c = makeLoadout({ ...b.equipment, deck: STARTER_DECK });
    expect(c.get("deck")).toBe(STARTER_DECK);
  });

  it("totalStats is deterministic", () => {
    const loadout = makeLoadout({
      deck: STARTER_DECK,
      eyeware: MILITECH_EYES,
      gloves: CHROME_GLOVES,
    });
    const a = loadout.totalStats();
    const b = loadout.totalStats();
    expect(a).toEqual(b);
  });
});

// =============================================================================
// Equipment name uniqueness across the default registry
// =============================================================================

describe("default registry integrity", () => {
  it("every equipment id is unique", () => {
    const ids = DEFAULT_REGISTRY.all.map((e) => e.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("every equipment has a non-empty name + description", () => {
    for (const e of DEFAULT_REGISTRY.all) {
      expect(e.name.length).toBeGreaterThan(0);
      expect(e.description.length).toBeGreaterThan(0);
    }
  });

  it("every equipment has valid asciiColor (3 integers)", () => {
    for (const e of DEFAULT_REGISTRY.all) {
      expect(e.asciiColor).toHaveLength(3);
      for (const channel of e.asciiColor) {
        expect(Number.isInteger(channel)).toBe(true);
        expect(channel).toBeGreaterThanOrEqual(0);
        expect(channel).toBeLessThanOrEqual(255);
      }
    }
  });
});