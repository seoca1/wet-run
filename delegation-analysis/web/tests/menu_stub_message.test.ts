import { describe, it, expect } from "vitest";
import { renderMainMenu } from "../src/renderer/menu";
import type { Cell } from "../src/core/types";

function gridText(grid: { cells: ReadonlyArray<ReadonlyArray<Cell>> }): string {
  return grid.cells
    .map((row) => row.map((c) => c?.char ?? " ").join(""))
    .join("\n");
}

describe("Menu: stub options show 'coming soon' status (Bug regression)", () => {
  it("renders statusMessage parameter in menu", () => {
    const grid = renderMainMenu(7, 80, 50, false, null, "credits - coming soon in a future tier");
    expect(gridText(grid)).toContain("coming soon");
  });

  it("does NOT render status message line when omitted", () => {
    const grid = renderMainMenu(7, 80, 50);
    expect(gridText(grid)).not.toContain("coming soon");
  });

  it("places status message below save hint and above footer", () => {
    const grid = renderMainMenu(
      3, 80, 50,
      true,
      { missionId: "aleph_fragment", turnCount: 3 },
      "credits - coming soon in a future tier",
    );
    const text = gridText(grid);
    const idxHint = text.indexOf("aleph_fragment");
    const idxStatus = text.indexOf("coming soon");
    const idxFooter = text.indexOf("navigate | ENTER");
    expect(idxHint).toBeGreaterThan(-1);
    expect(idxStatus).toBeGreaterThan(idxHint);
    expect(idxFooter).toBeGreaterThan(idxStatus);
  });
});
