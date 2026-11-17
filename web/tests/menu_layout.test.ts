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
    // ADR-0315: 13 entries + 4 group headers = 17 rows, so the hint sits at
    // lastRow + 2 = optionsY + 16 + 2.
    const hintRow = optionsY + 18;
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

  it("renders all 13 menu options without overlap when save exists", () => {
    const grid = renderMainMenu(0, 80, 50, true, {
      missionId: "x",
      turnCount: 0,
    });
    const rows: string[] = [];
    for (let y = 0; y < 50; y++) rows.push(getGridText(grid, y, 0, 80));
    // ADR-0315 grouped order, with the group headers printed above each group.
    // ADR-0317 step 4 removed GRAPHIC NOVEL, so the list is 13 long.
    const expected = [
      "[1] CONTINUE",
      "[2] NEW RUN",
      "[3] FAR GRID",
      "[4] DUNGEON CRAWL",
      "[5] TUTORIAL",
      "[6] CRAFT",
      "[7] EQUIPMENT",
      "[8] HALL OF DEAD",
      "[9] ENDINGS",
      "[10] STATS",
      "[11] SETTINGS",
      "[12] HELP",
      "[13] CREDITS",
    ];
    for (const label of expected) {
      const hits = rows.filter((r) => r.includes(label));
      expect(hits.length, `${label} should appear on exactly one row`).toBe(1);
    }
    for (const group of ["PLAY", "WORKSHOP", "ARCHIVE", "SYSTEM"]) {
      expect(rows.some((r) => r.includes(group))).toBe(true);
    }
  });
});
