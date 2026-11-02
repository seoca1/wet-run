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

/** ADR-0251 rule 5 — the loot screen states what will actually happen.
 *
 * A terminal node ends the run on confirm: `applyLootAction` branches to
 * runPhase "ending" and applies no heal. The screen used to announce
 * "HEAL applied" and "ENTER: route selection" anyway, and to promise
 * "ESC: back" although `applyLootAction` ignores cancel and the move keys.
 */
describe("renderLootScreen — terminal node", () => {
  it("does not promise a heal on the node that ends the run", () => {
    const grid = renderLootScreen(48, 100, 80, 50, 4075, "", true);
    const text = gridText(grid);
    expect(text).not.toContain("HEAL applied");
    expect(text).toContain("NO HEAL");
  });

  it("does not promise a route on the node that ends the run", () => {
    const grid = renderLootScreen(48, 100, 80, 50, 4075, "", true);
    expect(gridText(grid)).toContain("ENTER: run ends");
    expect(gridText(grid)).not.toContain("route selection");
  });

  it("keeps the heal promise on a node that continues the run", () => {
    const grid = renderLootScreen(48, 100, 80, 50, 4075, "", false);
    const text = gridText(grid);
    expect(text).toContain("HEAL applied → 63/100");
    expect(text).toContain("ENTER: route selection");
    expect(text).not.toContain("NO HEAL");
  });

  it("never promises ESC on a screen where ESC does nothing", () => {
    for (const terminal of [true, false]) {
      const text = gridText(
        renderLootScreen(48, 100, 80, 50, 4075, "", terminal),
      );
      expect(text).not.toContain("ESC");
    }
  });
});
