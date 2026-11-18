/** ADR-0324/0325 — the craft data files, checked against the tree.
 *
 * `recipes.json` (16 craftable equipment) and `materials.json` (28) are the
 * registry the crafting screen reads. These tests pin the three joins that
 * would otherwise drift silently: recipe id ↔ equipment id, recipe cost ↔
 * material registry, and material registry ↔ the actual loot table.
 */
import { describe, expect, it } from "vitest";
import recipesData from "../src/data/recipes.json" with { type: "json" };
import materialsData from "../src/data/materials.json" with { type: "json" };
import iceData from "../src/data/ice_types.json" with { type: "json" };
import {
  makeMaterialsFromData,
  makeRecipesFromData,
} from "../src/core/state/crafting";
import { DEFAULT_REGISTRY } from "../src/core/state/equipment";

const recipes = makeRecipesFromData(
  recipesData as unknown as Record<string, unknown>,
);
const materials = makeMaterialsFromData(
  materialsData as unknown as Record<string, unknown>,
);

describe("craft recipes data", () => {
  it("parses 16 craftable recipes (T1..T6; the two T0 starters are given)", () => {
    expect(recipes).toHaveLength(16);
    expect(recipes.every((r) => r.tierLevel >= 1)).toBe(true);
  });

  it("every recipe id is a real equipment id", () => {
    for (const r of recipes) {
      expect(DEFAULT_REGISTRY.get(r.itemId), r.itemId).not.toBeNull();
    }
  });

  it("every T1+ equipment has a recipe, and no T0 does", () => {
    const expected = DEFAULT_REGISTRY.all
      .filter((e) => e.tier !== "T0")
      .map((e) => e.id)
      .sort();
    expect(recipes.map((r) => r.itemId).sort()).toEqual(expected);
    expect(recipes.some((r) => r.itemId === "deck_basic")).toBe(false);
  });

  it("recipe tier_level matches the equipment tier", () => {
    for (const r of recipes) {
      expect(DEFAULT_REGISTRY.get(r.itemId)?.tier, r.itemId).toBe(
        `T${r.tierLevel}`,
      );
    }
  });

  it("every recipe cost material exists in the material registry", () => {
    const known = new Set(materials.map((m) => m.id));
    for (const r of recipes) {
      for (const mat of Object.keys(r.materials)) {
        expect(known.has(mat), `${r.itemId} needs unknown ${mat}`).toBe(true);
      }
    }
  });

  it("catalog requiredMaterials equals the recipe cost (no drift)", () => {
    for (const r of recipes) {
      expect(DEFAULT_REGISTRY.get(r.itemId)?.requiredMaterials, r.itemId).toEqual(
        r.materials,
      );
    }
  });

  it("the material registry covers exactly the loot item ids (28)", () => {
    const loot = new Set<string>();
    const catalog = iceData as unknown as Record<
      string,
      { loot_table?: ReadonlyArray<{ item?: string }> }
    >;
    for (const ice of Object.values(catalog)) {
      for (const entry of ice.loot_table ?? []) {
        if (typeof entry.item === "string") loot.add(entry.item);
      }
    }
    const registry = new Set(materials.map((m) => m.id));
    expect([...registry].sort()).toEqual([...loot].sort());
    expect(registry.size).toBe(28);
  });

  it("costs are positive and reference only positive quantities", () => {
    for (const r of recipes) {
      expect(Object.keys(r.materials).length, r.itemId).toBeGreaterThan(0);
      for (const qty of Object.values(r.materials)) {
        expect(qty).toBeGreaterThan(0);
      }
    }
  });
});
