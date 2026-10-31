/** Pure crafting screen composition; eligibility intentionally mirrors the controller.
 *
 * Framed like the other screens (ADR-0237 §2): an inset Green Grid frame,
 * content written through `setInnerText`, frame drawn last.
 */
import { makeGrid, type Grid } from "../core/grid";
import type { Inventory } from "../core/types";
import type { MaterialDef, Recipe } from "../core/state/crafting";
import { PALETTE } from "./palette";
import {
  drawPanel,
  panelInnerRect,
  screenFrameRect,
  setInnerText,
  type PanelRect,
} from "./panel";

export interface CraftingView {
  readonly inventory: Inventory;
  readonly recipes: readonly Recipe[];
  readonly materials: readonly MaterialDef[];
  readonly marketItemCount: number;
  readonly message: string;
}

/** Where the crafting screen places its content inside the inset frame. */
export interface CraftingLayout {
  readonly frame: PanelRect;
  readonly inner: PanelRect;
  /** Column of headings, recipe rows and hints. */
  readonly x: number;
  /** Column of indented list items. */
  readonly itemX: number;
  readonly titleY: number;
  readonly inventoryY: number;
}

/** The original fixed columns and opening rows, translated into the inset
 * frame: every offset keeps its distance from the frame's top-left corner
 * that it used to have from the grid's.
 */
export function craftingLayout(cols: number, rows: number): CraftingLayout {
  const frame = screenFrameRect({ width: cols, height: rows });
  const inner = panelInnerRect(makeGrid(cols, rows), frame);
  return {
    frame,
    inner,
    x: frame.x + 2,
    itemX: frame.x + 4,
    titleY: frame.y + 1,
    inventoryY: frame.y + 3,
  };
}

/** Render inventory, numbered craftable recipes and feedback without mutating inputs. */
export function renderCraftingScreen(
  view: CraftingView,
  cols: number,
  rows: number,
): Grid {
  let grid = makeGrid(cols, rows);
  const layout = craftingLayout(cols, rows);
  const { inner, x, itemX } = layout;
  const put = (col: number, row: number, text: string, fg: string): Grid =>
    setInnerText(grid, inner, col, row, text, fg);

  let y: number = layout.titleY;
  grid = put(x, y, "CRAFTING", PALETTE.GREEN_NEON);
  y = layout.inventoryY;
  grid = put(x, y, `Credits: ${view.inventory.credits}`, PALETTE.GRAY_LIGHT);
  y += 1;
  grid = put(x, y, "Materials:", PALETTE.GRAY_LIGHT);
  y += 1;
  const materials = view.inventory.materials;
  if (Object.keys(materials).length === 0) {
    grid = put(itemX, y, "(none)", PALETTE.GRAY_LIGHT);
    y += 1;
  } else {
    for (const [mat, qty] of Object.entries(materials)) {
      grid = put(itemX, y, `- ${mat}: ${qty}`, PALETTE.GRAY_LIGHT);
      y += 1;
    }
  }
  y += 1;
  grid = put(x, y, "Programs in inventory:", PALETTE.GRAY_LIGHT);
  y += 1;
  const programs = view.inventory.programs;
  if (programs.length === 0) {
    grid = put(itemX, y, "(none)", PALETTE.GRAY_LIGHT);
    y += 1;
  } else {
    for (const p of programs) {
      grid = put(itemX, y, `- ${p.name} (T${p.tier})`, PALETTE.CYAN_LIGHT);
      y += 1;
    }
  }
  y += 1;
  grid = put(x, y, "Craftable recipes:", PALETTE.GRAY_LIGHT);
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
    grid = put(x, y, `${prefix}${recipe.name} (T${recipe.tierLevel})`, color);
    y += 1;
    if (canCraft) {
      const costStr = Object.entries(recipe.materials)
        .map(([k, v]) => `${k} x${v}`)
        .join(", ");
      grid = put(itemX, y, `  Cost: ${costStr}`, PALETTE.GRAY_LIGHT);
      y += 1;
      recipeIndex += 1;
    }
  }
  if (recipeIndex === 1) {
    grid = put(itemX, y, "(none)", PALETTE.GRAY_LIGHT);
    y += 1;
  }
  y += 1;
  grid = put(
    x,
    y,
    "Press 1-9 to craft a recipe, ESC to go back",
    PALETTE.GRAY_LIGHT,
  );
  y += 1;
  if (view.materials.length > 0) {
    const names = view.materials.map((m) => `${m.id} (${m.name})`).join(", ");
    // setInnerText clips at the inner edge, replacing the old `cols - 4` slice.
    grid = put(x, y, `Materials: ${names}`, PALETTE.GRAY_DARK);
    y += 1;
  }
  if (view.marketItemCount > 0) {
    grid = put(
      x,
      y,
      `Market items: ${view.marketItemCount}`,
      PALETTE.GRAY_DARK,
    );
    y += 1;
  }
  if (view.message !== "") grid = put(x, y, view.message, PALETTE.YELLOW_AMBER);

  // Frame last, so an overlong line can never erase a rail.
  return drawPanel(grid, layout.frame).grid;
}
