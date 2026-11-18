import { describe, it, expect } from "vitest";
import {
  craftItem,
  makeRecipesFromData,
  makeMaterialsFromData,
  type Recipe,
} from "../src/core/crafting_flow.ts";

describe("craftItem", () => {
  it("returns unknown_recipe when recipe not found", () => {
    const recipes: Recipe[] = [];
    const result = craftItem(recipes, "unknown", {});
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.reason).toBe("unknown_recipe");
    }
  });

  it("returns missing_materials when inventory is insufficient", () => {
    const recipes: Recipe[] = [
      {
        itemId: "test_item",
        name: "Test Item",
        tierLevel: 1,
        glyph: "T",
        materials: { steel: 10, copper: 5 },
        ready: true,
      },
    ];
    const inventory = { steel: 5, copper: 2 };
    const result = craftItem(recipes, "test_item", inventory);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.reason).toBe("missing_materials");
      expect(result.missing).toEqual({ steel: 5, copper: 3 });
    }
  });

  it("crafts successfully with exact materials", () => {
    const recipes: Recipe[] = [
      {
        itemId: "item1",
        name: "Item 1",
        tierLevel: 1,
        glyph: "I",
        materials: { steel: 10 },
        ready: true,
      },
    ];
    const inventory = { steel: 10 };
    const result = craftItem(recipes, "item1", inventory);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.craftedItemId).toBe("item1");
      expect(result.consumedMaterials).toEqual({ steel: 10 });
      expect(result.newInventory).toEqual({});
    }
  });

  it("crafts successfully with excess materials", () => {
    const recipes: Recipe[] = [
      {
        itemId: "item2",
        name: "Item 2",
        tierLevel: 2,
        glyph: "I",
        materials: { steel: 5, copper: 3 },
        ready: true,
      },
    ];
    const inventory = { steel: 20, copper: 10, iron: 5 };
    const result = craftItem(recipes, "item2", inventory);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.craftedItemId).toBe("item2");
      expect(result.consumedMaterials).toEqual({ steel: 5, copper: 3 });
      expect(result.newInventory).toEqual({ steel: 15, copper: 7, iron: 5 });
    }
  });

  it("removes material entry when count reaches zero", () => {
    const recipes: Recipe[] = [
      {
        itemId: "item3",
        name: "Item 3",
        tierLevel: 1,
        glyph: "I",
        materials: { steel: 10 },
        ready: true,
      },
    ];
    const inventory = { steel: 10 };
    const result = craftItem(recipes, "item3", inventory);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.newInventory).toEqual({});
    }
  });

  it("handles empty materials recipe", () => {
    const recipes: Recipe[] = [
      {
        itemId: "free_item",
        name: "Free Item",
        tierLevel: 1,
        glyph: "F",
        materials: {},
        ready: true,
      },
    ];
    const inventory = {};
    const result = craftItem(recipes, "free_item", inventory);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.craftedItemId).toBe("free_item");
      expect(result.consumedMaterials).toEqual({});
      expect(result.newInventory).toEqual({});
    }
  });

  it("correctly identifies missing materials when some are present", () => {
    const recipes: Recipe[] = [
      {
        itemId: "complex",
        name: "Complex",
        tierLevel: 3,
        glyph: "C",
        materials: { steel: 10, copper: 5, gold: 2 },
        ready: true,
      },
    ];
    const inventory = { steel: 10, copper: 3 };
    const result = craftItem(recipes, "complex", inventory);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.reason).toBe("missing_materials");
      expect(result.missing).toEqual({ copper: 2, gold: 2 });
    }
  });

  it("ignores materials not required by recipe", () => {
    const recipes: Recipe[] = [
      {
        itemId: "simple",
        name: "Simple",
        tierLevel: 1,
        glyph: "S",
        materials: { steel: 5 },
        ready: true,
      },
    ];
    const inventory = { steel: 10, copper: 100, gold: 50 };
    const result = craftItem(recipes, "simple", inventory);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.newInventory).toEqual({ steel: 5, copper: 100, gold: 50 });
    }
  });
});

describe("makeRecipesFromData", () => {
  it("returns empty array when recipes key is missing", () => {
    const result = makeRecipesFromData({});
    expect(result).toEqual([]);
  });

  it("returns empty array when recipes is not an array", () => {
    const result = makeRecipesFromData({ recipes: "not an array" });
    expect(result).toEqual([]);
  });

  it("parses valid recipe entry", () => {
    const data = {
      recipes: [
        {
          item_id: "test_id",
          name: "Test Name",
          tier_level: 2,
          glyph: "T",
          ready: true,
          materials: { steel: 10, copper: 5 },
        },
      ],
    };
    const result = makeRecipesFromData(data);
    expect(result.length).toBe(1);
    expect(result[0]).toEqual({
      itemId: "test_id",
      name: "Test Name",
      tierLevel: 2,
      glyph: "T",
      ready: true,
      materials: { steel: 10, copper: 5 },
    });
  });

  it("generates itemId from name when item_id is missing", () => {
    const data = {
      recipes: [{ name: "Cool Item Name" }],
    };
    const result = makeRecipesFromData(data);
    expect(result.length).toBe(1);
    expect(result[0]?.itemId).toBe("cool_item_name");
  });

  it("uses default tier_level of 1 when missing", () => {
    const data = {
      recipes: [{ name: "Item" }],
    };
    const result = makeRecipesFromData(data);
    expect(result[0]?.tierLevel).toBe(1);
  });

  it("uses empty string for glyph when missing", () => {
    const data = {
      recipes: [{ name: "Item" }],
    };
    const result = makeRecipesFromData(data);
    expect(result[0]?.glyph).toBe("");
  });

  it("sets ready to false when missing", () => {
    const data = {
      recipes: [{ name: "Item" }],
    };
    const result = makeRecipesFromData(data);
    expect(result[0]?.ready).toBe(false);
  });

  it("sets ready to true only when explicitly true", () => {
    const data = {
      recipes: [{ name: "Ready Item", ready: true }],
    };
    const result = makeRecipesFromData(data);
    expect(result[0]?.ready).toBe(true);
  });

  it("skips entries without name", () => {
    const data = {
      recipes: [
        { item_id: "no_name" },
        { name: "Valid" },
      ],
    };
    const result = makeRecipesFromData(data);
    expect(result.length).toBe(1);
    expect(result[0]?.name).toBe("Valid");
  });

  it("skips null entries", () => {
    const data = {
      recipes: [null, { name: "Valid" }, null],
    };
    const result = makeRecipesFromData(data);
    expect(result.length).toBe(1);
  });

  it("skips non-object entries", () => {
    const data = {
      recipes: ["string", 123, { name: "Valid" }, true],
    };
    const result = makeRecipesFromData(data);
    expect(result.length).toBe(1);
  });

  it("parses materials with numeric values", () => {
    const data = {
      recipes: [
        {
          name: "Item",
          materials: { steel: 10.7, copper: 5.2 },
        },
      ],
    };
    const result = makeRecipesFromData(data);
    expect(result[0]?.materials).toEqual({ steel: 10, copper: 5 });
  });

  it("ignores non-numeric material values", () => {
    const data = {
      recipes: [
        {
          name: "Item",
          materials: { steel: 10, copper: "invalid", gold: 5 },
        },
      ],
    };
    const result = makeRecipesFromData(data);
    expect(result[0]?.materials).toEqual({ steel: 10, gold: 5 });
  });

  it("clamps negative material values to zero", () => {
    const data = {
      recipes: [
        {
          name: "Item",
          materials: { steel: -5, copper: 10 },
        },
      ],
    };
    const result = makeRecipesFromData(data);
    expect(result[0]?.materials).toEqual({ steel: 0, copper: 10 });
  });

  it("handles empty materials object", () => {
    const data = {
      recipes: [{ name: "Item", materials: {} }],
    };
    const result = makeRecipesFromData(data);
    expect(result[0]?.materials).toEqual({});
  });

  it("handles missing materials field", () => {
    const data = {
      recipes: [{ name: "Item" }],
    };
    const result = makeRecipesFromData(data);
    expect(result[0]?.materials).toEqual({});
  });

  it("truncates non-integer tier_level", () => {
    const data = {
      recipes: [{ name: "Item", tier_level: 3.9 }],
    };
    const result = makeRecipesFromData(data);
    expect(result[0]?.tierLevel).toBe(3);
  });

  it("slugifies complex names", () => {
    const data = {
      recipes: [{ name: "Ultra-Cool/Item #123!" }],
    };
    const result = makeRecipesFromData(data);
    expect(result[0]?.itemId).toBe("ultra_cool_item_123");
  });
});

describe("makeMaterialsFromData", () => {
  it("returns empty array when materials key is missing", () => {
    const result = makeMaterialsFromData({});
    expect(result).toEqual([]);
  });

  it("returns empty array when materials is not an array", () => {
    const result = makeMaterialsFromData({ materials: {} });
    expect(result).toEqual([]);
  });

  it("parses valid material entry", () => {
    const data = {
      materials: [
        { id: "steel", name: "Steel", need: 10 },
      ],
    };
    const result = makeMaterialsFromData(data);
    expect(result.length).toBe(1);
    expect(result[0]).toEqual({ id: "steel", name: "Steel", need: 10 });
  });

  it("skips entries without id", () => {
    const data = {
      materials: [
        { name: "Steel", need: 10 },
        { id: "copper", name: "Copper", need: 5 },
      ],
    };
    const result = makeMaterialsFromData(data);
    expect(result.length).toBe(1);
    expect(result[0]?.id).toBe("copper");
  });

  it("skips entries without name", () => {
    const data = {
      materials: [
        { id: "steel", need: 10 },
        { id: "copper", name: "Copper", need: 5 },
      ],
    };
    const result = makeMaterialsFromData(data);
    expect(result.length).toBe(1);
    expect(result[0]?.id).toBe("copper");
  });

  it("skips entries without need", () => {
    const data = {
      materials: [
        { id: "steel", name: "Steel" },
        { id: "copper", name: "Copper", need: 5 },
      ],
    };
    const result = makeMaterialsFromData(data);
    expect(result.length).toBe(1);
    expect(result[0]?.id).toBe("copper");
  });

  it("skips entries with non-numeric need", () => {
    const data = {
      materials: [
        { id: "steel", name: "Steel", need: "not a number" },
        { id: "copper", name: "Copper", need: 5 },
      ],
    };
    const result = makeMaterialsFromData(data);
    expect(result.length).toBe(1);
    expect(result[0]?.id).toBe("copper");
  });

  it("truncates fractional need values", () => {
    const data = {
      materials: [
        { id: "steel", name: "Steel", need: 10.9 },
      ],
    };
    const result = makeMaterialsFromData(data);
    expect(result[0]?.need).toBe(10);
  });

  it("clamps negative need to zero", () => {
    const data = {
      materials: [
        { id: "steel", name: "Steel", need: -5 },
      ],
    };
    const result = makeMaterialsFromData(data);
    expect(result[0]?.need).toBe(0);
  });

  it("skips null entries", () => {
    const data = {
      materials: [
        null,
        { id: "steel", name: "Steel", need: 10 },
      ],
    };
    const result = makeMaterialsFromData(data);
    expect(result.length).toBe(1);
  });

  it("skips non-object entries", () => {
    const data = {
      materials: [
        "string",
        { id: "steel", name: "Steel", need: 10 },
        123,
      ],
    };
    const result = makeMaterialsFromData(data);
    expect(result.length).toBe(1);
  });

  it("handles multiple valid entries", () => {
    const data = {
      materials: [
        { id: "steel", name: "Steel", need: 10 },
        { id: "copper", name: "Copper", need: 5 },
        { id: "gold", name: "Gold", need: 2 },
      ],
    };
    const result = makeMaterialsFromData(data);
    expect(result.length).toBe(3);
    expect(result[0]?.id).toBe("steel");
    expect(result[1]?.id).toBe("copper");
    expect(result[2]?.id).toBe("gold");
  });
});
