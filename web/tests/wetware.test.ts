import { describe, it, expect } from "vitest";
import {
  makeWetwareRegistry,
  stackWetware,
  getNewStatAugments,
  validateStacking,
  isTier3,
  WETWARE_CAPS,
  EMPTY_STACKED_WETWARE,
  MAX_AP_REGEN,
} from "../src/core/wetware.ts";

const sampleWetwareData = {
  reflex_boost: {
    id: "reflex_boost",
    name: "Reflex Boost",
    tier: 1,
    type: "neural",
    description: "Boosts reaction time",
    ap_regen_bonus: 0.1,
    crit_chance_bonus: 0.05,
  },
  synaptic_accelerator: {
    id: "synaptic_accelerator",
    name: "Synaptic Accelerator",
    tier: 2,
    type: "neural",
    description: "Accelerates neural signals",
    ap_regen_bonus: 0.15,
    dodge_bonus: 0.1,
  },
  neural_matrix: {
    id: "neural_matrix",
    name: "Neural Matrix",
    tier: 3,
    type: "neural",
    description: "Full neural integration",
    ap_regen_bonus: 0.25,
    crit_damage_bonus: 0.2,
  },
  bio_weave: {
    id: "bio_weave",
    name: "Bio Weave",
    tier: 1,
    type: "biological",
    description: "Organic armor",
    hp_bonus: 20,
    armor_bonus: 0.1,
  },
  nano_repair: {
    id: "nano_repair",
    name: "Nano Repair",
    tier: 2,
    type: "biological",
    description: "Nanobots for healing",
    heal_bonus: 0.15,
    hp_bonus: 30,
  },
  mana_core: {
    id: "mana_core",
    name: "Mana Core",
    tier: 3,
    type: "experimental",
    description: "New stat: mana",
    mana_bonus: 50,
    is_new_stat: true,
  },
  focus_lens: {
    id: "focus_lens",
    name: "Focus Lens",
    tier: 2,
    type: "experimental",
    description: "New stat: focus",
    focus_bonus: 0.2,
    is_new_stat: true,
  },
};

describe("wetware", () => {
  describe("WETWARE_CAPS", () => {
    it("is frozen", () => {
      expect(Object.isFrozen(WETWARE_CAPS)).toBe(true);
    });

    it("has apRegen cap", () => {
      expect(WETWARE_CAPS.apRegen).toBe(1.0);
    });

    it("has critChance cap", () => {
      expect(WETWARE_CAPS.critChance).toBe(0.95);
    });

    it("has dodge cap", () => {
      expect(WETWARE_CAPS.dodge).toBe(0.95);
    });

    it("has all necessary caps", () => {
      expect(WETWARE_CAPS.critDamage).toBeDefined();
      expect(WETWARE_CAPS.healing).toBeDefined();
      expect(WETWARE_CAPS.shield).toBeDefined();
      expect(WETWARE_CAPS.speed).toBeDefined();
      expect(WETWARE_CAPS.armor).toBeDefined();
      expect(WETWARE_CAPS.focus).toBeDefined();
    });
  });

  describe("EMPTY_STACKED_WETWARE", () => {
    it("is frozen", () => {
      expect(Object.isFrozen(EMPTY_STACKED_WETWARE)).toBe(true);
    });

    it("has all stats at zero", () => {
      expect(EMPTY_STACKED_WETWARE.apRegen).toBe(0);
      expect(EMPTY_STACKED_WETWARE.critChance).toBe(0);
      expect(EMPTY_STACKED_WETWARE.dodge).toBe(0);
      expect(EMPTY_STACKED_WETWARE.hpBonus).toBe(0);
      expect(EMPTY_STACKED_WETWARE.augmentCount).toBe(0);
    });
  });

  describe("makeWetwareRegistry", () => {
    it("creates registry from data", () => {
      const registry = makeWetwareRegistry(sampleWetwareData);
      expect(registry.all.length).toBeGreaterThan(0);
    });

    it("normalizes snake_case to camelCase", () => {
      const registry = makeWetwareRegistry(sampleWetwareData);
      const aug = registry.get("reflex_boost");
      expect(aug?.apRegenBonus).toBe(0.1);
    });

    it("skips keys starting with underscore", () => {
      const data = { _metadata: { version: 1 }, test: { id: "test", name: "Test", tier: 1 } };
      const registry = makeWetwareRegistry(data);
      expect(registry.all.length).toBe(1);
    });

    it("handles missing fields with defaults", () => {
      const data = { minimal: { id: "minimal" } };
      const registry = makeWetwareRegistry(data);
      const aug = registry.get("minimal");
      expect(aug?.name).toBe("minimal");
      expect(aug?.tier).toBe(0);
      expect(aug?.apRegenBonus).toBe(0);
    });

    it("freezes all augments", () => {
      const registry = makeWetwareRegistry(sampleWetwareData);
      for (const aug of registry.all) {
        expect(Object.isFrozen(aug)).toBe(true);
      }
    });
  });

  describe("WetwareRegistry.get", () => {
    const registry = makeWetwareRegistry(sampleWetwareData);

    it("returns augment by id", () => {
      const aug = registry.get("reflex_boost");
      expect(aug?.id).toBe("reflex_boost");
    });

    it("returns null for unknown id", () => {
      expect(registry.get("unknown")).toBe(null);
    });

    it("returns correct augment data", () => {
      const aug = registry.get("neural_matrix");
      expect(aug?.tier).toBe(3);
      expect(aug?.type).toBe("neural");
    });
  });

  describe("WetwareRegistry.byType", () => {
    const registry = makeWetwareRegistry(sampleWetwareData);

    it("filters by type", () => {
      const neural = registry.byType("neural");
      expect(neural.length).toBe(3);
      expect(neural.every((a) => a.type === "neural")).toBe(true);
    });

    it("returns empty array for unknown type", () => {
      expect(registry.byType("unknown").length).toBe(0);
    });

    it("returns frozen array", () => {
      const result = registry.byType("biological");
      expect(Object.isFrozen(result)).toBe(true);
    });
  });

  describe("WetwareRegistry.countTier3", () => {
    const registry = makeWetwareRegistry(sampleWetwareData);

    it("returns 0 for empty list", () => {
      expect(registry.countTier3([])).toBe(0);
    });

    it("counts tier 3 augments", () => {
      const ids = ["neural_matrix", "mana_core"];
      expect(registry.countTier3(ids)).toBe(2);
    });

    it("ignores non-tier-3", () => {
      const ids = ["reflex_boost", "bio_weave"];
      expect(registry.countTier3(ids)).toBe(0);
    });

    it("ignores unknown ids", () => {
      const ids = ["neural_matrix", "unknown"];
      expect(registry.countTier3(ids)).toBe(1);
    });

    it("counts mixed list correctly", () => {
      const ids = ["reflex_boost", "neural_matrix", "bio_weave"];
      expect(registry.countTier3(ids)).toBe(1);
    });
  });

  describe("stackWetware", () => {
    const registry = makeWetwareRegistry(sampleWetwareData);

    it("returns empty for no augments", () => {
      const stacked = stackWetware(registry, []);
      expect(stacked.apRegen).toBe(0);
      expect(stacked.augmentCount).toBe(0);
    });

    it("stacks single augment", () => {
      const stacked = stackWetware(registry, ["reflex_boost"]);
      expect(stacked.apRegen).toBe(0.1);
      expect(stacked.critChance).toBe(0.05);
      expect(stacked.augmentCount).toBe(1);
    });

    it("stacks multiple augments additively", () => {
      const stacked = stackWetware(registry, ["reflex_boost", "synaptic_accelerator"]);
      expect(stacked.apRegen).toBe(0.25);
      expect(stacked.dodge).toBe(0.1);
    });

    it("applies caps to percentage stats", () => {
      const stacked = stackWetware(registry, ["reflex_boost", "synaptic_accelerator", "neural_matrix"]);
      expect(stacked.apRegen).toBeLessThanOrEqual(WETWARE_CAPS.apRegen);
    });

    it("does not cap hp bonus", () => {
      const stacked = stackWetware(registry, ["bio_weave", "nano_repair"]);
      expect(stacked.hpBonus).toBe(50);
    });

    it("skips unknown augment ids", () => {
      const stacked = stackWetware(registry, ["reflex_boost", "unknown"]);
      expect(stacked.apRegen).toBe(0.1);
      expect(stacked.augmentCount).toBe(2);
    });

    it("returns frozen result", () => {
      const stacked = stackWetware(registry, ["reflex_boost"]);
      expect(Object.isFrozen(stacked)).toBe(true);
    });

    it("handles new stat augments", () => {
      const stacked = stackWetware(registry, ["mana_core"]);
      expect(stacked.mana).toBe(50);
    });

    it("handles focus stat", () => {
      const stacked = stackWetware(registry, ["focus_lens"]);
      expect(stacked.focus).toBe(0.2);
    });

    it("stacks armor bonus with cap", () => {
      const stacked = stackWetware(registry, ["bio_weave"]);
      expect(stacked.armor).toBe(0.1);
    });
  });

  describe("getNewStatAugments", () => {
    const registry = makeWetwareRegistry(sampleWetwareData);

    it("filters augments with isNewStat flag", () => {
      const newStat = getNewStatAugments(registry);
      expect(newStat.length).toBe(2);
      expect(newStat.every((a) => a.isNewStat)).toBe(true);
    });

    it("includes mana_core", () => {
      const newStat = getNewStatAugments(registry);
      expect(newStat.some((a) => a.id === "mana_core")).toBe(true);
    });

    it("includes focus_lens", () => {
      const newStat = getNewStatAugments(registry);
      expect(newStat.some((a) => a.id === "focus_lens")).toBe(true);
    });

    it("returns frozen array", () => {
      const result = getNewStatAugments(registry);
      expect(Object.isFrozen(result)).toBe(true);
    });
  });

  describe("validateStacking", () => {
    const registry = makeWetwareRegistry(sampleWetwareData);

    it("returns true for empty list", () => {
      expect(validateStacking(registry, [])).toBe(true);
    });

    it("returns true when all ids are valid", () => {
      expect(validateStacking(registry, ["reflex_boost", "bio_weave"])).toBe(true);
    });

    it("returns false when any id is unknown", () => {
      expect(validateStacking(registry, ["reflex_boost", "unknown"])).toBe(false);
    });

    it("returns false for all unknown ids", () => {
      expect(validateStacking(registry, ["unknown1", "unknown2"])).toBe(false);
    });
  });

  describe("isTier3", () => {
    const registry = makeWetwareRegistry(sampleWetwareData);

    it("returns true for tier 3 augment", () => {
      expect(isTier3(registry, "neural_matrix")).toBe(true);
    });

    it("returns false for tier 1 augment", () => {
      expect(isTier3(registry, "reflex_boost")).toBe(false);
    });

    it("returns false for unknown id", () => {
      expect(isTier3(registry, "unknown")).toBe(false);
    });

    it("returns true for mana_core", () => {
      expect(isTier3(registry, "mana_core")).toBe(true);
    });
  });

  describe("MAX_AP_REGEN constant", () => {
    it("is defined", () => {
      expect(MAX_AP_REGEN).toBeDefined();
    });

    it("has expected value", () => {
      expect(MAX_AP_REGEN).toBe(0.5);
    });
  });

  describe("edge cases", () => {
    it("handles empty data object", () => {
      const registry = makeWetwareRegistry({});
      expect(registry.all.length).toBe(0);
      expect(registry.get("any")).toBe(null);
    });

    it("stacking with empty registry returns empty", () => {
      const registry = makeWetwareRegistry({});
      const stacked = stackWetware(registry, ["any"]);
      expect(stacked.apRegen).toBe(0);
    });

    it("byType on empty registry returns empty", () => {
      const registry = makeWetwareRegistry({});
      expect(registry.byType("any").length).toBe(0);
    });

    it("handles invalid data types gracefully", () => {
      const data = {
        valid: { id: "valid", tier: 1 },
        invalid: null,
        invalid2: "string",
        invalid3: [],
      };
      const registry = makeWetwareRegistry(data);
      expect(registry.all.length).toBe(1);
    });
  });
});
