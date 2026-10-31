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
import { PALETTE } from "../src/renderer/palette";
import { rowText } from "./view_fixtures";

describe("equipment screen", () => {
  it("preserves all eight slot rows and the original key hints", () => {
    const grid = renderEquipmentScreen(
      { loadout: makeLoadout(), slots: EQUIP_SLOTS, message: "" },
      80,
      50,
    );
    expect(equipmentLayout(8)).toEqual({
      x: 2,
      itemX: 4,
      titleY: 1,
      slotsY: 4,
      instructionsY: 13,
    });
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
      expect(
        rowText(grid, 4 + i)
          .slice(4)
          .trimEnd(),
      ).toBe(`- ${slot}: (empty)`),
    );
    expect(rowText(grid, 13).slice(2).trimEnd()).toBe(
      "Press 1-8 to select slot to auto-equip from registry",
    );
    expect(rowText(grid, 14).slice(2).trimEnd()).toBe("Press ESC to go back");
    expect(rowText(grid, 16).trim()).toBe("");
    expect(grid.cells[1]?.[2]?.fg).toBe(PALETTE.GREEN_NEON);
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
    expect(rowText(grid, 4).slice(4).trimEnd()).toBe(`- deck: ${item.name}`);
    expect(rowText(grid, 16).slice(2).trimEnd()).toBe("Equipped deck");
    expect(grid.cells[16]?.[2]?.fg).toBe(PALETTE.YELLOW_AMBER);
    expect(loadout.get("deck")).toBe(item);
  });
});
