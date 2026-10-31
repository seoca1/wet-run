import { describe, expect, it } from "vitest";
import {
  craftingLayout,
  renderCraftingScreen,
  type CraftingView,
} from "../src/renderer/crafting_screen";
import type { Recipe } from "../src/core/state/crafting";
import { PALETTE } from "../src/renderer/palette";
import { preGameView, program, rowText } from "./view_fixtures";

const recipe = (name: string, materials: Recipe["materials"]): Recipe => ({
  itemId: name,
  name,
  materials,
  tierLevel: 2,
  glyph: "*",
  ready: true,
});

describe("crafting screen", () => {
  it("keeps empty inventory sections and hints at their original coordinates", () => {
    const view = preGameView().crafting;
    const grid = renderCraftingScreen(view, 80, 50);
    expect(craftingLayout()).toEqual({
      x: 2,
      itemX: 4,
      titleY: 1,
      inventoryY: 3,
    });
    for (const [y, x, text] of [
      [1, 2, "CRAFTING"],
      [3, 2, "Credits: 0"],
      [4, 2, "Materials:"],
      [5, 4, "(none)"],
      [7, 2, "Programs in inventory:"],
      [8, 4, "(none)"],
      [10, 2, "Craftable recipes:"],
      [11, 4, "(none)"],
      [13, 2, "Press 1-9 to craft a recipe, ESC to go back"],
    ] as const)
      expect(rowText(grid, y).slice(x).trimEnd()).toBe(text);
    expect(grid.cells[1]?.[2]?.fg).toBe(PALETTE.GREEN_NEON);
  });

  it("preserves eligibility precedence, recipe order and craftable-only numbering", () => {
    const view: CraftingView = {
      ...preGameView().crafting,
      inventory: {
        credits: 17,
        materials: { shard: 2, zero: 0 },
        programs: [program],
      },
      recipes: [
        recipe("Blocked", { shard: 1 }),
        recipe("Zero", { zero: 3 }),
        recipe("Free", {}),
      ],
    };
    const grid = renderCraftingScreen(view, 80, 50);
    expect(rowText(grid, 6).slice(4).trimEnd()).toBe("- zero: 0");
    expect(rowText(grid, 9).slice(4).trimEnd()).toBe("- Atk (T1)");
    expect(grid.cells[9]?.[4]?.fg).toBe(PALETTE.CYAN_LIGHT);
    expect(rowText(grid, 12).slice(2).trimEnd()).toBe("   Blocked (T2)");
    expect(grid.cells[12]?.[5]?.fg).toBe(PALETTE.GRAY_LIGHT);
    expect(rowText(grid, 13).slice(2).trimEnd()).toBe("1. Zero (T2)");
    expect(rowText(grid, 14).slice(4).trimEnd()).toBe("  Cost: zero x3");
    expect(rowText(grid, 15).slice(2).trimEnd()).toBe("2. Free (T2)");
    expect(grid.cells[15]?.[2]?.fg).toBe(PALETTE.GREEN_NEON);
    expect(view.inventory.materials).toEqual({ shard: 2, zero: 0 });
  });

  it("clips material definitions and places market feedback after optional metadata", () => {
    const view: CraftingView = {
      ...preGameView().crafting,
      marketItemCount: 3,
      message: "Crafted!",
      materials: [{ id: "shard", name: "Very long material name", need: 1 }],
    };
    const grid = renderCraftingScreen(view, 30, 24);
    expect(rowText(grid, 14).slice(2, 28)).toBe("Materials: shard (Very lon");
    expect(rowText(grid, 15).slice(2).trimEnd()).toBe("Market items: 3");
    expect(rowText(grid, 16).slice(2).trimEnd()).toBe("Crafted!");
    expect(grid.cells[16]?.[2]?.fg).toBe(PALETTE.YELLOW_AMBER);
  });

  it("keeps the no-craftable placeholder after unavailable recipe rows", () => {
    const view = {
      ...preGameView().crafting,
      recipes: [recipe("Missing", { absent: 1 })],
    };
    const grid = renderCraftingScreen(view, 80, 50);
    expect(rowText(grid, 11).slice(2).trimEnd()).toBe("   Missing (T2)");
    expect(rowText(grid, 12).slice(4).trimEnd()).toBe("(none)");
  });
});
