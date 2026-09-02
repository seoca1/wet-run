/** Unit tests for equipment_sets.ts.
 *
 * Run with: npx vitest run tests/equipment_sets.test.ts
 *
 * Tests Phase-14 equipment set schema: SetBonusV2 structure,
 * EquipmentSetV2 contracts, makeEquipmentSetsFromData() parsing,
 * bonus field extraction, immutability enforcement, and handling
 * of malformed or missing data.
 */

import { describe, it, expect } from "vitest";
import { makeEquipmentSetsFromData } from "../src/core/equipment_sets.ts";

describe("makeEquipmentSetsFromData — basic shape", () => {
  it("returns a frozen empty object for empty input", () => {
    const result = makeEquipmentSetsFromData({});
    expect(result).toEqual({});
    expect(Object.isFrozen(result)).toBe(true);
  });

  it("returns frozen top-level object for any input", () => {
    const result = makeEquipmentSetsFromData({ a_set: { set_id: "a" } });
    expect(Object.isFrozen(result)).toBe(true);
  });

  it("parses a single minimal set", () => {
    const raw = {
      ghost_set: { set_id: "ghost_set" },
    };
    const result = makeEquipmentSetsFromData(raw);
    expect(Object.keys(result)).toEqual(["ghost_set"]);
    expect(result.ghost_set.setId).toBe("ghost_set");
  });

  it("parses multiple sets in one call", () => {
    const raw = {
      set_a: { set_id: "set_a", set_name: "Set A" },
      set_b: { set_id: "set_b", set_name: "Set B" },
      set_c: { set_id: "set_c", set_name: "Set C" },
    };
    const result = makeEquipmentSetsFromData(raw);
    expect(Object.keys(result).sort()).toEqual(["set_a", "set_b", "set_c"]);
  });
});

describe("makeEquipmentSetsFromData — filtering invalid keys", () => {
  it("skips keys that start with underscore", () => {
    const raw = {
      _metadata: { version: "1.0" },
      _internal: "ignore",
      valid_set: { set_id: "valid" },
    };
    const result = makeEquipmentSetsFromData(raw);
    expect(Object.keys(result)).toEqual(["valid"]);
  });

  it("skips null values", () => {
    const raw = {
      null_entry: null,
      valid: { set_id: "valid" },
    };
    const result = makeEquipmentSetsFromData(raw);
    expect(Object.keys(result)).toEqual(["valid"]);
  });

  it("skips string, number, and boolean primitive values", () => {
    const raw = {
      str_value: "hello",
      num_value: 42,
      bool_value: true,
      valid: { set_id: "valid" },
    };
    const result = makeEquipmentSetsFromData(raw);
    expect(Object.keys(result)).toEqual(["valid"]);
  });

  it("skips array values (only plain objects are sets)", () => {
    const raw = {
      arr_value: [1, 2, 3],
      valid: { set_id: "valid" },
    };
    const result = makeEquipmentSetsFromData(raw);
    expect(Object.keys(result)).toEqual(["valid"]);
  });

  it("skips undefined values", () => {
    const raw = {
      undef_value: undefined,
      valid: { set_id: "valid" },
    };
    const result = makeEquipmentSetsFromData(raw);
    expect(Object.keys(result)).toEqual(["valid"]);
  });
});

describe("makeEquipmentSetsFromData — set_id / set_name resolution", () => {
  it("uses explicit set_id when provided", () => {
    const raw = { some_key: { set_id: "actual_id" } };
    const result = makeEquipmentSetsFromData(raw);
    expect(result.actual_id).toBeDefined();
    expect(result.actual_id.setId).toBe("actual_id");
  });

  it("falls back to object key when set_id is missing", () => {
    const raw = { ghost_set: { set_name: "Ghost Set" } };
    const result = makeEquipmentSetsFromData(raw);
    expect(result.ghost_set.setId).toBe("ghost_set");
  });

  it("falls back to setId for setName when set_name is missing", () => {
    const raw = { test_set: { set_id: "test_set" } };
    const result = makeEquipmentSetsFromData(raw);
    expect(result.test_set.setName).toBe("test_set");
  });

  it("extracts theme, description, and role strings", () => {
    const raw = {
      architect_set: {
        set_id: "architect_set",
        set_name: "Architect's Vision",
        theme: "defense",
        description: "A defensive set",
        role: "tank",
      },
    };
    const result = makeEquipmentSetsFromData(raw);
    const set = result.architect_set;
    expect(set.theme).toBe("defense");
    expect(set.description).toBe("A defensive set");
    expect(set.role).toBe("tank");
  });

  it("defaults missing string fields to empty strings", () => {
    const raw = { minimal: { set_id: "minimal" } };
    const result = makeEquipmentSetsFromData(raw);
    const set = result.minimal;
    expect(set.theme).toBe("");
    expect(set.description).toBe("");
    expect(set.role).toBe("");
  });
});

describe("makeEquipmentSetsFromData — tier handling", () => {
  it("preserves integer tier values", () => {
    const raw = { s: { set_id: "s", tier: 3 } };
    expect(makeEquipmentSetsFromData(raw).s.tier).toBe(3);
  });

  it("truncates fractional tier values", () => {
    const raw = { s: { set_id: "s", tier: 2.7 } };
    expect(makeEquipmentSetsFromData(raw).s.tier).toBe(2);
  });

  it("defaults tier to 1 when missing", () => {
    const raw = { s: { set_id: "s" } };
    expect(makeEquipmentSetsFromData(raw).s.tier).toBe(1);
  });

  it("defaults tier to 1 for non-finite tier values (NaN, Infinity, string)", () => {
    for (const tier of [Number.NaN, Number.POSITIVE_INFINITY, "high"]) {
      const raw = { s: { set_id: "s", tier } };
      expect(makeEquipmentSetsFromData(raw).s.tier).toBe(1);
    }
  });
});

describe("makeEquipmentSetsFromData — character_affinity", () => {
  it("preserves string-only affinity arrays", () => {
    const raw = {
      s: { set_id: "s", character_affinity: ["novice", "veteran"] },
    };
    expect(makeEquipmentSetsFromData(raw).s.characterAffinity).toEqual([
      "novice",
      "veteran",
    ]);
  });

  it("defaults to empty frozen array when missing", () => {
    const raw = { s: { set_id: "s" } };
    const result = makeEquipmentSetsFromData(raw);
    expect(result.s.characterAffinity).toEqual([]);
    expect(Object.isFrozen(result.s.characterAffinity)).toBe(true);
  });

  it("coerces non-string array entries to strings", () => {
    const raw = {
      s: { set_id: "s", character_affinity: [1, "veteran", null, true] },
    };
    expect(makeEquipmentSetsFromData(raw).s.characterAffinity).toEqual([
      "1",
      "veteran",
      "null",
      "true",
    ]);
  });

  it("defaults to empty array when affinity is not an array", () => {
    const raw = { s: { set_id: "s", character_affinity: "novice" } };
    expect(makeEquipmentSetsFromData(raw).s.characterAffinity).toEqual([]);
  });
});

describe("makeEquipmentSetsFromData — bonus extraction", () => {
  it("extracts a 2-piece bonus with all fields", () => {
    const raw = {
      s: {
        set_id: "s",
        set_bonus_2_piece: {
          name: "Two-Piece",
          type: "stat",
          description: "Bonus for 2 pieces",
          hp: 100,
        },
      },
    };
    const bonus = makeEquipmentSetsFromData(raw).s.bonuses[2];
    expect(bonus.name).toBe("Two-Piece");
    expect(bonus.type).toBe("stat");
    expect(bonus.description).toBe("Bonus for 2 pieces");
    expect(bonus.fields.hp).toBe(100);
  });

  it("extracts a 3-piece bonus", () => {
    const raw = {
      s: {
        set_id: "s",
        set_bonus_3_piece: {
          name: "Three-Piece",
          type: "passive",
          description: "Bonus for 3 pieces",
          attack: 50,
        },
      },
    };
    const bonus = makeEquipmentSetsFromData(raw).s.bonuses[3];
    expect(bonus.fields.attack).toBe(50);
  });

  it("extracts a 4-piece bonus", () => {
    const raw = {
      s: {
        set_id: "s",
        set_bonus_4_piece: {
          name: "Four-Piece",
          type: "active",
          description: "Bonus for 4 pieces",
          defense: 75,
        },
      },
    };
    const bonus = makeEquipmentSetsFromData(raw).s.bonuses[4];
    expect(bonus.fields.defense).toBe(75);
  });

  it("excludes reserved keys (name/type/description) from bonus fields", () => {
    const raw = {
      s: {
        set_id: "s",
        set_bonus_2_piece: {
          name: "Bonus",
          type: "stat",
          description: "Desc",
          hp: 100,
          attack: 25,
        },
      },
    };
    const fields = makeEquipmentSetsFromData(raw).s.bonuses[2].fields;
    expect(fields).not.toHaveProperty("name");
    expect(fields).not.toHaveProperty("type");
    expect(fields).not.toHaveProperty("description");
    expect(fields.hp).toBe(100);
    expect(fields.attack).toBe(25);
  });

  it("only keeps finite numeric values in bonus fields", () => {
    const raw = {
      s: {
        set_id: "s",
        set_bonus_2_piece: {
          valid: 50,
          not_number: "string",
          infinite: Number.POSITIVE_INFINITY,
          nan_value: Number.NaN,
        },
      },
    };
    const fields = makeEquipmentSetsFromData(raw).s.bonuses[2].fields;
    expect(fields.valid).toBe(50);
    expect(fields).not.toHaveProperty("not_number");
    expect(fields).not.toHaveProperty("infinite");
    expect(fields).not.toHaveProperty("nan_value");
  });

  it("defaults bonus name/type/description to empty strings when missing", () => {
    const raw = {
      s: {
        set_id: "s",
        set_bonus_2_piece: { hp: 100 },
      },
    };
    const bonus = makeEquipmentSetsFromData(raw).s.bonuses[2];
    expect(bonus.name).toBe("");
    expect(bonus.type).toBe("");
    expect(bonus.description).toBe("");
  });

  it("leaves bonus slot undefined when no bonus is provided for that tier", () => {
    const raw = { s: { set_id: "s", set_name: "No Bonus" } };
    const set = makeEquipmentSetsFromData(raw).s;
    expect(set.bonuses[2]).toBeUndefined();
    expect(set.bonuses[3]).toBeUndefined();
    expect(set.bonuses[4]).toBeUndefined();
  });

  it("parses all three bonus tiers in a single set", () => {
    const raw = {
      s: {
        set_id: "s",
        set_bonus_2_piece: { name: "2p", hp: 10 },
        set_bonus_3_piece: { name: "3p", hp: 20 },
        set_bonus_4_piece: { name: "4p", hp: 30 },
      },
    };
    const set = makeEquipmentSetsFromData(raw).s;
    expect(set.bonuses[2]?.name).toBe("2p");
    expect(set.bonuses[3]?.name).toBe("3p");
    expect(set.bonuses[4]?.name).toBe("4p");
  });
});

describe("makeEquipmentSetsFromData — immutability", () => {
  it("freezes the returned top-level object", () => {
    const result = makeEquipmentSetsFromData({ a: { set_id: "a" } });
    expect(Object.isFrozen(result)).toBe(true);
  });

  it("freezes each individual set entry", () => {
    const result = makeEquipmentSetsFromData({ a: { set_id: "a" } });
    expect(Object.isFrozen(result.a)).toBe(true);
  });

  it("freezes the characterAffinity array", () => {
    const result = makeEquipmentSetsFromData({
      a: { set_id: "a", character_affinity: ["novice"] },
    });
    expect(Object.isFrozen(result.a.characterAffinity)).toBe(true);
  });

  it("freezes the bonuses map and each bonus object", () => {
    const result = makeEquipmentSetsFromData({
      a: {
        set_id: "a",
        set_bonus_2_piece: { hp: 10 },
      },
    });
    expect(Object.isFrozen(result.a.bonuses)).toBe(true);
    expect(Object.isFrozen(result.a.bonuses[2])).toBe(true);
    expect(Object.isFrozen(result.a.bonuses[2].fields)).toBe(true);
  });

  it("throws in strict mode when attempting to mutate the result object", () => {
    const result = makeEquipmentSetsFromData({ a: { set_id: "a" } });
    expect(() => {
      (result as Record<string, unknown>).injected = "value";
    }).toThrow();
  });
});

describe("makeEquipmentSetsFromData — realistic fixtures", () => {
  it("parses a complete Phase-14 set (ghost_set) end-to-end", () => {
    const raw = {
      ghost_set: {
        set_id: "ghost_set",
        set_name: "Ghost Protocol",
        theme: "stealth",
        description: "Phase-14 stealth set",
        tier: 2,
        role: "attacker",
        character_affinity: ["novice", "heretic"],
        set_bonus_2_piece: {
          name: "Ghost 2p",
          type: "stat",
          description: "Evasion +15",
          evasion: 15,
        },
        set_bonus_3_piece: {
          name: "Ghost 3p",
          type: "passive",
          description: "Phase shift on crit",
          crit_chance: 10,
        },
        set_bonus_4_piece: {
          name: "Ghost 4p",
          type: "active",
          description: "Cloak for 3 turns",
          duration_ms: 3000,
        },
      },
    };
    const set = makeEquipmentSetsFromData(raw).ghost_set;
    expect(set.setId).toBe("ghost_set");
    expect(set.setName).toBe("Ghost Protocol");
    expect(set.theme).toBe("stealth");
    expect(set.tier).toBe(2);
    expect(set.role).toBe("attacker");
    expect(set.characterAffinity).toEqual(["novice", "heretic"]);
    expect(set.bonuses[2]?.fields.evasion).toBe(15);
    expect(set.bonuses[3]?.fields.crit_chance).toBe(10);
    expect(set.bonuses[4]?.fields.duration_ms).toBe(3000);
  });

  it("parses an architect_set with only 2-piece bonus", () => {
    const raw = {
      architect_set: {
        set_id: "architect_set",
        set_name: "Architect's Vision",
        set_bonus_2_piece: {
          name: "Architect 2p",
          defense: 25,
        },
      },
    };
    const set = makeEquipmentSetsFromData(raw).architect_set;
    expect(set.setName).toBe("Architect's Vision");
    expect(set.bonuses[2]?.fields.defense).toBe(25);
    expect(set.bonuses[3]).toBeUndefined();
    expect(set.bonuses[4]).toBeUndefined();
  });
});
