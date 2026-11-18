import { describe, it, expect } from "vitest";
import {
  craftItem,
  hasMaterials,
  getHubRecipes,
  makeRecipesFromData,
  type Recipe,
} from "../src/core/crafting_flow.ts";
import { HUB_NPCS, HUB_SERVICES, enterHub, moveToLocation } from "../src/core/hub.ts";

describe("Hub Workshop Integration", () => {
  const TEST_RECIPES: ReadonlyArray<Recipe> = Object.freeze([
    Object.freeze({
      itemId: "basic_tool",
      name: "Basic Tool",
      tierLevel: 1,
      glyph: "T",
      materials: Object.freeze({ steel: 5, copper: 2 }),
      ready: true,
    }),
    Object.freeze({
      itemId: "advanced_tool",
      name: "Advanced Tool",
      tierLevel: 2,
      glyph: "A",
      materials: Object.freeze({ steel: 10, copper: 5, gold: 2 }),
      ready: true,
    }),
    Object.freeze({
      itemId: "master_tool",
      name: "Master Tool",
      tierLevel: 3,
      glyph: "M",
      materials: Object.freeze({ gold: 10, platinum: 5 }),
      ready: false,
    }),
  ]);

  describe("hasMaterials", () => {
    it("returns true when inventory has exact materials", () => {
      const inventory = Object.freeze({ steel: 5, copper: 2 });
      expect(hasMaterials(TEST_RECIPES, "basic_tool", inventory)).toBe(true);
    });

    it("returns true when inventory has excess materials", () => {
      const inventory = Object.freeze({ steel: 10, copper: 5, iron: 3 });
      expect(hasMaterials(TEST_RECIPES, "basic_tool", inventory)).toBe(true);
    });

    it("returns false when inventory is missing some materials", () => {
      const inventory = Object.freeze({ steel: 3, copper: 2 });
      expect(hasMaterials(TEST_RECIPES, "basic_tool", inventory)).toBe(false);
    });

    it("returns false when inventory has zero of required material", () => {
      const inventory = Object.freeze({ steel: 5, copper: 0 });
      expect(hasMaterials(TEST_RECIPES, "basic_tool", inventory)).toBe(false);
    });

    it("returns false when inventory is missing all required materials", () => {
      const inventory = Object.freeze({ iron: 100 });
      expect(hasMaterials(TEST_RECIPES, "basic_tool", inventory)).toBe(false);
    });

    it("returns false for unknown recipe", () => {
      const inventory = Object.freeze({ steel: 100, copper: 100 });
      expect(hasMaterials(TEST_RECIPES, "unknown_recipe", inventory)).toBe(false);
    });

    it("returns true for recipe with no materials required", () => {
      const recipesWithFree = [
        ...TEST_RECIPES,
        Object.freeze({
          itemId: "free_item",
          name: "Free Item",
          tierLevel: 1,
          glyph: "F",
          materials: Object.freeze({}),
          ready: true,
        }),
      ];
      expect(hasMaterials(recipesWithFree, "free_item", Object.freeze({}))).toBe(true);
    });

    it("checks multiple materials correctly", () => {
      const inventory = Object.freeze({ steel: 10, copper: 5, gold: 2 });
      expect(hasMaterials(TEST_RECIPES, "advanced_tool", inventory)).toBe(true);
    });

    it("returns false when one of multiple materials is insufficient", () => {
      const inventory = Object.freeze({ steel: 10, copper: 5, gold: 1 });
      expect(hasMaterials(TEST_RECIPES, "advanced_tool", inventory)).toBe(false);
    });

    it("handles empty inventory for non-empty requirements", () => {
      expect(hasMaterials(TEST_RECIPES, "basic_tool", Object.freeze({}))).toBe(false);
    });
  });

  describe("getHubRecipes", () => {
    it("returns only ready recipes", () => {
      const recipes = getHubRecipes(TEST_RECIPES);
      expect(recipes).toHaveLength(2);
      expect(recipes).toContain("basic_tool");
      expect(recipes).toContain("advanced_tool");
      expect(recipes).not.toContain("master_tool");
    });

    it("returns empty array when no recipes are ready", () => {
      const notReadyRecipes: ReadonlyArray<Recipe> = Object.freeze([
        Object.freeze({
          itemId: "item1",
          name: "Item 1",
          tierLevel: 1,
          glyph: "I",
          materials: Object.freeze({ steel: 5 }),
          ready: false,
        }),
      ]);
      expect(getHubRecipes(notReadyRecipes)).toHaveLength(0);
    });

    it("returns all recipe IDs when all are ready", () => {
      const allReadyRecipes: ReadonlyArray<Recipe> = Object.freeze([
        Object.freeze({
          itemId: "r1",
          name: "R1",
          tierLevel: 1,
          glyph: "1",
          materials: Object.freeze({}),
          ready: true,
        }),
        Object.freeze({
          itemId: "r2",
          name: "R2",
          tierLevel: 1,
          glyph: "2",
          materials: Object.freeze({}),
          ready: true,
        }),
      ]);
      expect(getHubRecipes(allReadyRecipes)).toHaveLength(2);
    });

    it("returns frozen array", () => {
      const recipes = getHubRecipes(TEST_RECIPES);
      expect(Object.isFrozen(recipes)).toBe(true);
    });

    it("handles empty recipe list", () => {
      expect(getHubRecipes(Object.freeze([]))).toHaveLength(0);
    });
  });

  describe("craftItem with Hub inventory", () => {
    it("crafts item successfully with Hub-style inventory", () => {
      const inventory = Object.freeze({ steel: 10, copper: 5 });
      const result = craftItem(TEST_RECIPES, "basic_tool", inventory);
      expect(result.ok).toBe(true);
      if (result.ok) {
        expect(result.craftedItemId).toBe("basic_tool");
        expect(result.consumedMaterials).toEqual({ steel: 5, copper: 2 });
        expect(result.newInventory).toEqual({ steel: 5, copper: 3 });
      }
    });

    it("fails when materials are insufficient", () => {
      const inventory = Object.freeze({ steel: 3, copper: 1 });
      const result = craftItem(TEST_RECIPES, "basic_tool", inventory);
      expect(result.ok).toBe(false);
      if (!result.ok) {
        expect(result.reason).toBe("missing_materials");
        expect(result.missing).toEqual({ steel: 2, copper: 1 });
      }
    });

    it("produces immutable inventory result", () => {
      const inventory = Object.freeze({ steel: 10, copper: 5 });
      const result = craftItem(TEST_RECIPES, "basic_tool", inventory);
      expect(result.ok).toBe(true);
      if (result.ok) {
        expect(Object.isFrozen(result.newInventory)).toBe(true);
        expect(Object.isFrozen(result.consumedMaterials)).toBe(true);
      }
    });

    it("handles crafting with multiple material types", () => {
      const inventory = Object.freeze({ steel: 15, copper: 8, gold: 3 });
      const result = craftItem(TEST_RECIPES, "advanced_tool", inventory);
      expect(result.ok).toBe(true);
      if (result.ok) {
        expect(result.newInventory).toEqual({ steel: 5, copper: 3, gold: 1 });
        expect(result.consumedMaterials).toEqual({ steel: 10, copper: 5, gold: 2 });
      }
    });
  });

  describe("Hub Workshop NPC Integration", () => {
    it("Molly Millions is located at workshop", () => {
      const molly = HUB_NPCS.find((npc) => npc.id === "molly");
      expect(molly).toBeDefined();
      expect(molly?.location).toBe("workshop");
      expect(molly?.role).toBe("instructor");
    });

    it("Hub workshop location can be accessed", () => {
      const hubState = enterHub();
      const workshopState = moveToLocation(hubState, "workshop");
      expect(workshopState.currentLocation).toBe("workshop");
      expect(workshopState.visitedLocations).toContain("workshop");
    });

    it("Workshop services are available", () => {
      const workshopServices = HUB_SERVICES.filter((s) => s.location === "workshop");
      expect(workshopServices.length).toBeGreaterThan(0);
    });
  });

  describe("Integration with recipes from data", () => {
    it("parses recipes and checks materials with hasMaterials", () => {
      const rawData = {
        recipes: [
          {
            item_id: "test_item",
            name: "Test Item",
            tier_level: 1,
            glyph: "T",
            ready: true,
            materials: { ore: 5, crystal: 2 },
          },
        ],
      };
      const recipes = makeRecipesFromData(rawData);
      const inventory = Object.freeze({ ore: 10, crystal: 3 });
      expect(hasMaterials(recipes, "test_item", inventory)).toBe(true);
    });

    it("getHubRecipes filters parsed recipes by ready flag", () => {
      const rawData = {
        recipes: [
          { name: "Ready 1", ready: true, materials: {} },
          { name: "Not Ready", ready: false, materials: {} },
          { name: "Ready 2", ready: true, materials: {} },
        ],
      };
      const recipes = makeRecipesFromData(rawData);
      const hubRecipes = getHubRecipes(recipes);
      expect(hubRecipes).toHaveLength(2);
      expect(hubRecipes).toContain("ready_1");
      expect(hubRecipes).toContain("ready_2");
    });

    it("full workflow: parse recipes, check materials, craft", () => {
      const rawData = {
        recipes: [
          {
            item_id: "sword",
            name: "Iron Sword",
            tier_level: 1,
            glyph: "S",
            ready: true,
            materials: { iron: 10, wood: 5 },
          },
        ],
      };
      const recipes = makeRecipesFromData(rawData);
      const inventory = Object.freeze({ iron: 15, wood: 8 });
      
      expect(hasMaterials(recipes, "sword", inventory)).toBe(true);
      
      const hubRecipes = getHubRecipes(recipes);
      expect(hubRecipes).toContain("sword");
      
      const result = craftItem(recipes, "sword", inventory);
      expect(result.ok).toBe(true);
      if (result.ok) {
        expect(result.craftedItemId).toBe("sword");
        expect(result.newInventory).toEqual({ iron: 5, wood: 3 });
      }
    });
  });

  describe("Edge cases", () => {
    it("hasMaterials handles recipe with materials as undefined", () => {
      const edgeRecipes: ReadonlyArray<Recipe> = Object.freeze([
        Object.freeze({
          itemId: "no_materials",
          name: "No Materials",
          tierLevel: 1,
          glyph: "N",
          materials: Object.freeze({}),
          ready: true,
        }),
      ]);
      expect(hasMaterials(edgeRecipes, "no_materials", Object.freeze({}))).toBe(true);
    });

    it("getHubRecipes handles recipes with same item_id but different ready states", () => {
      const conflictRecipes: ReadonlyArray<Recipe> = Object.freeze([
        Object.freeze({
          itemId: "duplicate",
          name: "Duplicate 1",
          tierLevel: 1,
          glyph: "D",
          materials: Object.freeze({}),
          ready: true,
        }),
        Object.freeze({
          itemId: "duplicate",
          name: "Duplicate 2",
          tierLevel: 2,
          glyph: "D",
          materials: Object.freeze({}),
          ready: false,
        }),
      ]);
      const hubRecipes = getHubRecipes(conflictRecipes);
      expect(hubRecipes).toContain("duplicate");
      expect(hubRecipes.filter((id) => id === "duplicate")).toHaveLength(1);
    });

    it("craftItem returns consistent error for non-existent recipe", () => {
      const inventory = Object.freeze({ anything: 1000 });
      const result = craftItem(TEST_RECIPES, "does_not_exist", inventory);
      expect(result.ok).toBe(false);
      if (!result.ok) {
        expect(result.reason).toBe("unknown_recipe");
      }
    });
  });
});
