import { describe, expect, it } from "vitest";
import {
  craftingLayout,
  renderCraftingScreen,
  type CraftingView,
} from "../src/renderer/crafting_screen";
import type { Recipe } from "../src/core/state/crafting";
import type { Grid } from "../src/core/types";
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

const colText = (grid: Grid, x: number): string =>
  grid.cells.map((row) => row[x]?.char ?? "").join("");

describe("crafting screen", () => {
  it("keeps empty inventory sections and hints at their original frame-relative coordinates", () => {
    const view = preGameView().crafting;
    const grid = renderCraftingScreen(view, 80, 50);
    expect(craftingLayout(80, 50)).toEqual({
      frame: { x: 1, y: 1, width: 78, height: 48 },
      inner: { x: 2, y: 2, width: 76, height: 46 },
      x: 3,
      itemX: 5,
      titleY: 2,
      inventoryY: 4,
    });
    for (const [y, x, text] of [
      [2, 3, "CRAFTING"],
      [4, 3, "Credits: 0"],
      [5, 3, "Materials:"],
      [6, 5, "(none)"],
      [8, 3, "Programs in inventory:"],
      [9, 5, "(none)"],
      [11, 3, "Craftable recipes:"],
      [12, 5, "(none)"],
      [14, 3, "Press 1-9 to craft a recipe, ESC to go back"],
    ] as const)
      expect(rowText(grid, y).slice(x, 78).trimEnd()).toBe(text);
    expect(grid.cells[2]?.[3]?.fg).toBe(PALETTE.GREEN_NEON);
  });

  it("draws the inset frame and leaves the outermost grid row/column blank", () => {
    const grid = renderCraftingScreen(preGameView().crafting, 80, 50);
    expect(grid.cells[1]?.[1]?.char).toBe("╔");
    expect(grid.cells[1]?.[78]?.char).toBe("╗");
    expect(grid.cells[48]?.[1]?.char).toBe("╚");
    expect(grid.cells[48]?.[78]?.char).toBe("╝");
    expect(grid.cells[1]?.[1]?.fg).toBe(PALETTE.GREEN_NEON);
    expect(grid.cells[20]?.[1]?.char).toBe("║");
    expect(grid.cells[20]?.[78]?.char).toBe("║");
    expect(rowText(grid, 0).trim()).toBe("");
    expect(rowText(grid, 49).trim()).toBe("");
    expect(colText(grid, 0).trim()).toBe("");
    expect(colText(grid, 79).trim()).toBe("");
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
    const at = (y: number, x: number): string =>
      rowText(grid, y).slice(x, 78).trimEnd();
    expect(at(7, 5)).toBe("- zero: 0");
    expect(at(10, 5)).toBe("- Atk (T1)");
    expect(grid.cells[10]?.[5]?.fg).toBe(PALETTE.CYAN_LIGHT);
    expect(at(13, 3)).toBe("   Blocked (T2)");
    expect(grid.cells[13]?.[6]?.fg).toBe(PALETTE.GRAY_LIGHT);
    expect(at(14, 3)).toBe("1. Zero (T2)");
    expect(at(15, 5)).toBe("  Cost: zero x3");
    expect(at(16, 3)).toBe("2. Free (T2)");
    expect(grid.cells[16]?.[3]?.fg).toBe(PALETTE.GREEN_NEON);
    expect(view.inventory.materials).toEqual({ shard: 2, zero: 0 });
  });

  it("clips material definitions at the inner edge and places market feedback after optional metadata", () => {
    const view: CraftingView = {
      ...preGameView().crafting,
      marketItemCount: 3,
      message: "Crafted!",
      materials: [{ id: "shard", name: "Very long material name", need: 1 }],
    };
    const grid = renderCraftingScreen(view, 30, 24);
    // Inner box is columns 2..27; the line stops before the right rail.
    expect(rowText(grid, 15).slice(3, 28)).toBe("Materials: shard (Very lo");
    expect(grid.cells[15]?.[28]?.char).toBe("║");
    expect(grid.cells[15]?.[29]?.char).toBe(" ");
    expect(rowText(grid, 16).slice(3, 28).trimEnd()).toBe("Market items: 3");
    expect(rowText(grid, 17).slice(3, 28).trimEnd()).toBe("Crafted!");
    expect(grid.cells[17]?.[3]?.fg).toBe(PALETTE.YELLOW_AMBER);
  });

  it("keeps the no-craftable placeholder after unavailable recipe rows", () => {
    const view = {
      ...preGameView().crafting,
      recipes: [recipe("Missing", { absent: 1 })],
    };
    const grid = renderCraftingScreen(view, 80, 50);
    expect(rowText(grid, 12).slice(3, 78).trimEnd()).toBe("   Missing (T2)");
    expect(rowText(grid, 13).slice(5, 78).trimEnd()).toBe("(none)");
  });
});
