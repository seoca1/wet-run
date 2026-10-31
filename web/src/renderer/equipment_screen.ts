/** Pure equipment screen, preserving registry slot order.
 *
 * Framed like the other screens (ADR-0237 §2): an inset Green Grid frame,
 * content written through `setInnerText`, frame drawn last.
 */
import { makeGrid, type Grid } from "../core/grid";
import type { EquipmentLoadout } from "../core/types";
import type { EquipSlot } from "../core/state/equipment";
import { PALETTE } from "./palette";
import {
  drawPanel,
  panelInnerRect,
  screenFrameRect,
  setInnerText,
  type PanelRect,
} from "./panel";

/** Where the equipment screen places its content inside the inset frame. */
export interface EquipmentLayout {
  readonly frame: PanelRect;
  readonly inner: PanelRect;
  /** Column of the title, "Equipped:" heading and key hints. */
  readonly x: number;
  /** Column of the slot rows. */
  readonly itemX: number;
  readonly titleY: number;
  readonly slotsY: number;
  readonly instructionsY: number;
}

/** The original slot list and instruction positions, translated into the
 * inset frame: every offset keeps its distance from the frame's top-left
 * corner that it used to have from the grid's.
 */
export function equipmentLayout(
  slotCount: number,
  cols: number,
  rows: number,
): EquipmentLayout {
  const frame = screenFrameRect({ width: cols, height: rows });
  const inner = panelInnerRect(makeGrid(cols, rows), frame);
  return {
    frame,
    inner,
    x: frame.x + 2,
    itemX: frame.x + 4,
    titleY: frame.y + 1,
    slotsY: frame.y + 4,
    instructionsY: frame.y + 5 + slotCount,
  };
}

/** Render equipped slots and the controller's feedback, without equipping anything. */
export function renderEquipmentScreen(
  view: {
    readonly loadout: EquipmentLoadout;
    readonly slots: readonly EquipSlot[];
    readonly message: string;
  },
  cols: number,
  rows: number,
): Grid {
  let grid = makeGrid(cols, rows);
  const layout = equipmentLayout(view.slots.length, cols, rows);
  const { inner, x, itemX } = layout;
  const put = (col: number, row: number, text: string, fg: string): Grid =>
    setInnerText(grid, inner, col, row, text, fg);

  grid = put(x, layout.titleY, "EQUIPMENT", PALETTE.GREEN_NEON);
  grid = put(x, layout.slotsY - 1, "Equipped:", PALETTE.GRAY_LIGHT);
  let y: number = layout.slotsY;
  for (const slot of view.slots) {
    const equip = view.loadout.get(slot);
    const name = equip ? equip.name : "(empty)";
    grid = put(itemX, y, `- ${slot}: ${name}`, PALETTE.GRAY_LIGHT);
    y += 1;
  }
  y += 1;
  grid = put(
    x,
    y,
    "Press 1-8 to select slot to auto-equip from registry",
    PALETTE.GRAY_LIGHT,
  );
  y += 1;
  grid = put(x, y, "Press ESC to go back", PALETTE.GRAY_LIGHT);
  if (view.message !== "") {
    y += 2;
    grid = put(x, y, view.message, PALETTE.YELLOW_AMBER);
  }

  // Frame last, so an overlong line can never erase a rail.
  return drawPanel(grid, layout.frame).grid;
}
