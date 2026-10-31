/** Pure crafting screen composition; eligibility intentionally mirrors the controller. */
import { makeGrid, setText, type Grid } from "../core/grid";
import type { Inventory } from "../core/types";
import type { MaterialDef, Recipe } from "../core/state/crafting";
import { PALETTE } from "./palette";

export interface CraftingView {
  readonly inventory: Inventory;
  readonly recipes: readonly Recipe[];
  readonly materials: readonly MaterialDef[];
  readonly marketItemCount: number;
  readonly message: string;
}

/** Original fixed columns and opening rows, without adding a frame. */
export function craftingLayout() {
  return { x: 2, itemX: 4, titleY: 1, inventoryY: 3 } as const;
}

/** Render inventory, numbered craftable recipes and feedback without mutating inputs. */
export function renderCraftingScreen(
  view: CraftingView,
  cols: number,
  rows: number,
): Grid {
  let grid = makeGrid(cols, rows);
  const layout = craftingLayout();
  let y: number = layout.titleY;
  grid = setText(grid, layout.x, y, "CRAFTING", PALETTE.GREEN_NEON);
  y += 2;
  grid = setText(
    grid,
    2,
    y,
    `Credits: ${view.inventory.credits}`,
    PALETTE.GRAY_LIGHT,
  );
  y += 1;
  grid = setText(grid, 2, y, "Materials:", PALETTE.GRAY_LIGHT);
  y += 1;
  const materials = view.inventory.materials;
  if (Object.keys(materials).length === 0) {
    grid = setText(grid, 4, y, "(none)", PALETTE.GRAY_LIGHT);
    y += 1;
  } else {
    for (const [mat, qty] of Object.entries(materials)) {
      grid = setText(grid, 4, y, `- ${mat}: ${qty}`, PALETTE.GRAY_LIGHT);
      y += 1;
    }
  }
  y += 1;
  grid = setText(grid, 2, y, "Programs in inventory:", PALETTE.GRAY_LIGHT);
  y += 1;
  const programs = view.inventory.programs;
  if (programs.length === 0) {
    grid = setText(grid, 4, y, "(none)", PALETTE.GRAY_LIGHT);
    y += 1;
  } else {
    for (const p of programs) {
      grid = setText(
        grid,
        4,
        y,
        `- ${p.name} (T${p.tier})`,
        PALETTE.CYAN_LIGHT,
      );
      y += 1;
    }
  }
  y += 1;
  grid = setText(grid, 2, y, "Craftable recipes:", PALETTE.GRAY_LIGHT);
  y += 1;
  let recipeIndex = 1;
  for (const recipe of view.recipes) {
    let canCraft = true;
    for (const [mat, qty] of Object.entries(recipe.materials)) {
      if (view.inventory.materials[mat] ?? 0 < qty) {
        canCraft = false;
        break;
      }
    }
    const color = canCraft ? PALETTE.GREEN_NEON : PALETTE.GRAY_LIGHT;
    const prefix = canCraft ? `${recipeIndex}. ` : "   ";
    grid = setText(
      grid,
      2,
      y,
      `${prefix}${recipe.name} (T${recipe.tierLevel})`,
      color,
    );
    y += 1;
    if (canCraft) {
      const costStr = Object.entries(recipe.materials)
        .map(([k, v]) => `${k} x${v}`)
        .join(", ");
      grid = setText(grid, 4, y, `  Cost: ${costStr}`, PALETTE.GRAY_LIGHT);
      y += 1;
      recipeIndex += 1;
    }
  }
  if (recipeIndex === 1) {
    grid = setText(grid, 4, y, "(none)", PALETTE.GRAY_LIGHT);
    y += 1;
  }
  y += 1;
  grid = setText(
    grid,
    2,
    y,
    "Press 1-9 to craft a recipe, ESC to go back",
    PALETTE.GRAY_LIGHT,
  );
  y += 1;
  if (view.materials.length > 0) {
    const names = view.materials.map((m) => `${m.id} (${m.name})`).join(", ");
    grid = setText(
      grid,
      2,
      y,
      `Materials: ${names}`.slice(0, cols - 4),
      PALETTE.GRAY_DARK,
    );
    y += 1;
  }
  if (view.marketItemCount > 0) {
    grid = setText(
      grid,
      2,
      y,
      `Market items: ${view.marketItemCount}`,
      PALETTE.GRAY_DARK,
    );
    y += 1;
  }
  if (view.message !== "")
    grid = setText(grid, 2, y, view.message, PALETTE.YELLOW_AMBER);
  return grid;
}
