import { describe, it, expect } from "vitest";
import { rollLoot, getLootTable } from "../src/core/loot.ts";
import type { LootEntry } from "../src/core/loot.ts";

describe("loot system", () => {
  describe("rollLoot", () => {
    it("drops items when rng below chance", () => {
      const table: LootEntry[] = [
        { item: "ice_shard", chance: 0.8, quantity: 1 },
        { item: "data_fragment", chance: 0.3, quantity: 1 },
      ];
      const drops = rollLoot(table, () => 0.5);
      expect(drops).toHaveLength(1);
      expect(drops[0].item).toBe("ice_shard");
    });

    it("drops multiple items when rng below all chances", () => {
      const table: LootEntry[] = [
        { item: "ice_shard", chance: 0.8, quantity: 1 },
        { item: "data_fragment", chance: 0.5, quantity: 1 },
      ];
      const drops = rollLoot(table, () => 0.2);
      expect(drops).toHaveLength(2);
    });

    it("drops nothing when rng above all chances", () => {
      const table: LootEntry[] = [
        { item: "ice_shard", chance: 0.3, quantity: 1 },
      ];
      const drops = rollLoot(table, () => 0.9);
      expect(drops).toHaveLength(0);
    });

    it("handles empty loot table", () => {
      const drops = rollLoot([], () => 0.5);
      expect(drops).toHaveLength(0);
    });

    it("respects quantity field", () => {
      const table: LootEntry[] = [
        { item: "ice_shard", chance: 1.0, quantity: 3 },
      ];
      const drops = rollLoot(table, () => 0.5);
      expect(drops).toHaveLength(1);
      expect(drops[0].quantity).toBe(3);
    });
  });

  describe("getLootTable", () => {
    it("returns loot table for known ICE type", () => {
      const data = {
        standard: { loot_table: [{ item: "ice_shard", chance: 0.7, quantity: 1 }] },
      };
      const table = getLootTable("standard", data);
      expect(table).toHaveLength(1);
      expect(table[0].item).toBe("ice_shard");
    });

    it("returns empty array for unknown ICE type", () => {
      const data = {};
      const table = getLootTable("unknown", data);
      expect(table).toHaveLength(0);
    });

    it("returns empty array when ICE type has no loot_table", () => {
      const data = {
        test_ice: {},
      };
      const table = getLootTable("test_ice", data);
      expect(table).toHaveLength(0);
    });
  });

  describe("loot accumulation", () => {
    it("accumulates loot from multiple drops", () => {
      const table: LootEntry[] = [
        { item: "ice_shard", chance: 1.0, quantity: 1 },
        { item: "data_fragment", chance: 1.0, quantity: 2 },
      ];
      const drops1 = rollLoot(table, () => 0.5);
      const drops2 = rollLoot(table, () => 0.5);
      
      let materials: Record<string, number> = {};
      for (const drop of [...drops1, ...drops2]) {
        materials[drop.item] = (materials[drop.item] ?? 0) + drop.quantity;
      }
      
      expect(materials["ice_shard"]).toBe(2);
      expect(materials["data_fragment"]).toBe(4);
    });
  });
});
