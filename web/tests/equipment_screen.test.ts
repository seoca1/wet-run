import { describe, expect, it } from "vitest";
import {
  equipmentLayout,
  renderEquipmentScreen,
} from "../src/renderer/equipment_screen";
import {
  makeLoadout,
  equipOn,
  DEFAULT_REGISTRY,
  EQUIP_SLOTS,
} from "../src/core/state/equipment";
import type { Grid } from "../src/core/types";
import { PALETTE } from "../src/renderer/palette";
import { rowText } from "./view_fixtures";

const colText = (grid: Grid, x: number): string =>
  grid.cells.map((row) => row[x]?.char ?? "").join("");

/** Row text inside the 80-column frame, without the right rail. */
const at = (grid: Grid, y: number, x: number): string =>
  rowText(grid, y).slice(x, 78).trimEnd();

describe("equipment screen", () => {
  it("preserves all eight slot rows and the original key hints at frame-relative coordinates", () => {
    const grid = renderEquipmentScreen(
      { loadout: makeLoadout(), slots: EQUIP_SLOTS, message: "" },
      80,
      50,
    );
    expect(equipmentLayout(8, 80, 50)).toEqual({
      frame: { x: 1, y: 1, width: 78, height: 48 },
      inner: { x: 2, y: 2, width: 76, height: 46 },
      x: 3,
      itemX: 5,
      titleY: 2,
      slotsY: 5,
      instructionsY: 14,
    });
    expect(at(grid, 2, 3)).toBe("EQUIPMENT");
    expect(at(grid, 4, 3)).toBe("Equipped:");
    const slots = [
      "deck",
      "headware",
      "eyeware",
      "bodysuit",
      "gloves",
      "boots",
      "implant",
      "trodes",
    ];
    slots.forEach((slot, i) =>
      expect(at(grid, 5 + i, 5)).toBe(`- ${slot}: (empty)`),
    );
    expect(at(grid, 14, 3)).toBe(
      "Press 1-8 to select slot to auto-equip from registry",
    );
    expect(at(grid, 15, 3)).toBe("Press ESC to go back");
    expect(at(grid, 17, 2)).toBe("");
    expect(grid.cells[2]?.[3]?.fg).toBe(PALETTE.GREEN_NEON);
  });

  it("draws the inset frame and leaves the outermost grid row/column blank", () => {
    const grid = renderEquipmentScreen(
      { loadout: makeLoadout(), slots: EQUIP_SLOTS, message: "" },
      80,
      50,
    );
    expect(grid.cells[1]?.[1]?.char).toBe("╔");
    expect(grid.cells[1]?.[78]?.char).toBe("╗");
    expect(grid.cells[48]?.[1]?.char).toBe("╚");
    expect(grid.cells[48]?.[78]?.char).toBe("╝");
    expect(grid.cells[48]?.[78]?.fg).toBe(PALETTE.GREEN_NEON);
    expect(grid.cells[20]?.[1]?.char).toBe("║");
    expect(grid.cells[20]?.[78]?.char).toBe("║");
    expect(rowText(grid, 0).trim()).toBe("");
    expect(rowText(grid, 49).trim()).toBe("");
    expect(colText(grid, 0).trim()).toBe("");
    expect(colText(grid, 79).trim()).toBe("");
  });

  it("keeps an overlong hint off the right rail on a narrow grid", () => {
    const grid = renderEquipmentScreen(
      { loadout: makeLoadout(), slots: EQUIP_SLOTS, message: "" },
      30,
      24,
    );
    expect(rowText(grid, 14).slice(3, 28)).toBe("Press 1-8 to select slot ");
    expect(grid.cells[14]?.[28]?.char).toBe("║");
    expect(grid.cells[14]?.[29]?.char).toBe(" ");
  });

  it("renders an equipped name and amber feedback without changing the loadout", () => {
    const item = DEFAULT_REGISTRY.all.find((entry) => entry.slot === "deck");
    if (!item) throw new Error("fixture requires a deck");
    const loadout = equipOn(makeLoadout(), item).loadout;
    const grid = renderEquipmentScreen(
      { loadout, slots: EQUIP_SLOTS, message: "Equipped deck" },
      80,
      50,
    );
    expect(at(grid, 5, 5)).toBe(`- deck: ${item.name}`);
    expect(at(grid, 17, 3)).toBe("Equipped deck");
    expect(grid.cells[17]?.[3]?.fg).toBe(PALETTE.YELLOW_AMBER);
    expect(loadout.get("deck")).toBe(item);
  });
});
