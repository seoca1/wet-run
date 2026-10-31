/** Pure equipment screen, preserving registry slot order. */
import { makeGrid, setText, type Grid } from "../core/grid";
import type { EquipmentLoadout } from "../core/types";
import type { EquipSlot } from "../core/state/equipment";
import { PALETTE } from "./palette";

/** Fixed slot list and instruction positions of the original equipment view. */
export function equipmentLayout(slotCount: number) {
  return {
    x: 2,
    itemX: 4,
    titleY: 1,
    slotsY: 4,
    instructionsY: 5 + slotCount,
  } as const;
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
  const layout = equipmentLayout(view.slots.length);
  grid = setText(grid, 2, layout.titleY, "EQUIPMENT", PALETTE.GREEN_NEON);
  grid = setText(grid, 2, 3, "Equipped:", PALETTE.GRAY_LIGHT);
  let y: number = layout.slotsY;
  for (const slot of view.slots) {
    const equip = view.loadout.get(slot);
    const name = equip ? equip.name : "(empty)";
    grid = setText(grid, 4, y, `- ${slot}: ${name}`, PALETTE.GRAY_LIGHT);
    y += 1;
  }
  y += 1;
  grid = setText(
    grid,
    2,
    y,
    "Press 1-8 to select slot to auto-equip from registry",
    PALETTE.GRAY_LIGHT,
  );
  y += 1;
  grid = setText(grid, 2, y, "Press ESC to go back", PALETTE.GRAY_LIGHT);
  if (view.message !== "") {
    y += 2;
    grid = setText(grid, 2, y, view.message, PALETTE.YELLOW_AMBER);
  }
  return grid;
}
