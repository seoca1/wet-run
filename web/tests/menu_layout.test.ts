import { describe, it, expect } from "vitest";
import { renderMainMenu } from "../src/renderer/menu";
import { mainMenuLayout } from "../src/renderer/menu_main";
import { makeGrid } from "../src/core/grid";
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
    result += row[x + i]?.char ?? " ";
  }
  return result;
}

describe("renderMainMenu (Bug A regression: CONTINUE hint placement)", () => {
  it("places the save hint below all menu items so it doesn't overlap", () => {
    const cols = 80;
    const rows = 50;
    const saveMeta = { missionId: "aleph_fragment", turnCount: 3 };
    const grid = renderMainMenu(0, cols, rows, true, saveMeta);
    const { optionsX, optionsY } = mainMenuLayout(makeGrid(cols, rows));
    const hintRow = optionsY + 14 + 1;
    const hintText = "→ aleph_fragment (turn 4)";
    const found = getGridText(grid, hintRow, optionsX + 2, hintText.length);
    expect(found, `Hint '${hintText}' should appear on row ${hintRow}`).toBe(
      hintText,
    );
  });

  it("does not render the save hint when no save exists", () => {
    const grid = renderMainMenu(0, 80, 50, false, null);
    for (let y = 0; y < 50; y++) {
      const rowText = getGridText(grid, y, 0, 80);
      expect(rowText).not.toContain("→");
    }
  });

  it("renders all 14 menu options without overlap when save exists", () => {
    const grid = renderMainMenu(0, 80, 50, true, {
      missionId: "x",
      turnCount: 0,
    });
    const expected = [
      "[1] NEW RUN",
      "[2] FAR GRID",
      "[3] DUNGEON CRAWL",
      "[4] GRAPHIC NOVEL",
      "[5] CONTINUE",
      "[6] SETTINGS",
      "[7] CRAFT",
      "[8] EQUIPMENT",
      "[9] CREDITS",
      "[10] HALL OF DEAD",
      "[11] HELP",
      "[12] ENDINGS",
      "[13] STATS",
      "[14] TUTORIAL",
    ];
    const { optionsX, optionsY } = mainMenuLayout(makeGrid(80, 50));
    for (let i = 0; i < expected.length; i++) {
      const rowText = getGridText(grid, optionsY + i, optionsX, 30);
      const label = `row ${optionsY + i} should contain '${expected[i]}'`;
      expect(rowText, label).toContain(expected[i]!);
    }
  });
});
