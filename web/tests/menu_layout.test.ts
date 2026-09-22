import { describe, it, expect } from "vitest";
import { renderMainMenu } from "../src/renderer/menu";
import type { Cell } from "../src/core/types";

function getGridText(
  grid: { cells: ReadonlyArray<ReadonlyArray<Cell>> },
  y: number,
  x: number,
  length: number,
): string {
  let result = "";
  for (let i = 0; i < length; i++) {
    const row = grid.cells[y];
    if (!row) return result;
    result += (row[x + i]?.char ?? " ");
  }
  return result;
}

describe("renderMainMenu (Bug A regression: CONTINUE hint placement)", () => {
  it("places the save hint below all menu items so it doesn't overlap", () => {
    const cols = 80;
    const rows = 50;
    const saveMeta = { missionId: "aleph_fragment", turnCount: 3 };
    const grid = renderMainMenu(0, cols, rows, true, saveMeta);
    const hintRow = 8 + 13 + 1;
    const hintText = "→ aleph_fragment (turn 4)";
    const found = getGridText(grid, hintRow, 6, hintText.length);
    expect(found, `Hint '${hintText}' should appear on row ${hintRow}`).toBe(hintText);
  });

  it("does not render the save hint when no save exists", () => {
    const grid = renderMainMenu(0, 80, 50, false, null);
    for (let y = 8; y <= 22; y++) {
      const rowText = getGridText(grid, y, 4, 30);
      expect(rowText).not.toContain("→");
    }
  });

  it("renders all 13 menu options without overlap when save exists", () => {
    const grid = renderMainMenu(0, 80, 50, true, { missionId: "x", turnCount: 0 });
    const expected = [
      "[1] NEW RUN",
      "[2] DUNGEON CRAWL",
      "[3] GRAPHIC NOVEL",
      "[4] CONTINUE",
      "[5] SETTINGS",
      "[6] CRAFT",
      "[7] EQUIPMENT",
      "[8] CREDITS",
      "[9] HALL OF DEAD",
      "[10] HELP",
      "[11] ENDINGS",
      "[12] STATS",
      "[13] TUTORIAL",
    ];
    for (let i = 0; i < expected.length; i++) {
      const rowText = getGridText(grid, 8 + i, 0, 30);
      expect(rowText, `row ${8 + i} should contain '${expected[i]}'`).toContain(expected[i]!);
    }
  });
});

