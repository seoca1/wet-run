import { describe, it, expect } from "vitest";
import { renderLootScreen } from "../src/renderer/ending";
import type { Cell } from "../src/core/types";

function gridText(grid: { cells: ReadonlyArray<ReadonlyArray<Cell>> }): string {
  return grid.cells
    .map((row) => row.map((c) => c?.char ?? " ").join(""))
    .join("\n");
}

describe("renderLootScreen (Bug #6 regression: shows credits and items)", () => {
  it("renders credits reward when provided", () => {
    const grid = renderLootScreen(95, 100, 80, 50, 4125, "");
    expect(gridText(grid)).toContain("+4,125 credits");
  });

  it("renders loot items message when provided", () => {
    const grid = renderLootScreen(
      95,
      100,
      80,
      50,
      4125,
      "Loot: ice_shardx1, data_fragmentx1",
    );
    expect(gridText(grid)).toContain("Loot: ice_shardx1, data_fragmentx1");
  });

  it("does NOT show credits/items when omitted (default args)", () => {
    const grid = renderLootScreen(95, 100, 80, 50);
    expect(gridText(grid)).not.toContain("+");
    expect(gridText(grid)).not.toContain("Loot:");
  });

  it("renders DATA SALVAGE title and HP status", () => {
    const grid = renderLootScreen(95, 100, 80, 50);
    expect(gridText(grid)).toContain("DATA SALVAGE");
    expect(gridText(grid)).toContain("HP 95/100");
  });
});
