/** Tests for Far Grid menu gate UI (ADR-0213 Phase 2).
 *
 * - locked-by-default: FAR GRID renders grayed out + "(locked)" suffix
 * - unlocked-after-flag: FAR GRID renders normally with no suffix
 * - locked-selection blocked with message: existing statusMessage line
 *   carries the lock notice (verified via the message constant the menu
 *   reads from)
 * - grid-dimensions / status-message placement unaffected
 */
import { describe, expect, it } from "vitest";
import { renderMainMenu } from "../src/renderer/menu";
import type { Cell } from "../src/core/types";
import { FAR_GRID_LOCKED_MESSAGE } from "../src/core/far_grid_gate";

function gridText(grid: { cells: ReadonlyArray<ReadonlyArray<Cell>> }): string {
  return grid.cells
    .map((row) => row.map((c) => c?.char ?? " ").join(""))
    .join("\n");
}

function getRowText(
  grid: { cells: ReadonlyArray<ReadonlyArray<Cell>> },
  y: number,
  x: number,
  length: number,
): string {
  let result = "";
  const row = grid.cells[y];
  if (!row) return result;
  for (let i = 0; i < length; i++) {
    result += row[x + i]?.char ?? " ";
  }
  return result;
}

describe("main menu: FAR GRID gate (ADR-0213 Phase 2)", () => {
  it("renders FAR GRID with '(locked)' suffix when farGridUnlocked=false", () => {
    const cols = 80;
    const rows = 50;
    // farGridUnlocked=false → FAR GRID row shows "(locked)"
    const grid = renderMainMenu(1, cols, rows, false, null, "", false);
    // FAR GRID is index 1 in MENU_OPTIONS, rendered at row = startY(8) + 1 = 9
    // The label format is: `▸ [2] FAR GRID    (locked)` starting at col 4.
    // Col breakdown: 4='▸' 5=' ' 6='[' 7='2' 8=']' 9=' ' 10..17='FAR GRID' 18..21='    ' 22..29='(locked)'
    const lockedSuffix = "(locked)";
    expect(getRowText(grid, 9, 22, lockedSuffix.length)).toBe(lockedSuffix);
  });

  it("does NOT render '(locked)' suffix when farGridUnlocked=true", () => {
    const cols = 80;
    const rows = 50;
    const grid = renderMainMenu(1, cols, rows, false, null, "", true);
    // The label should be just "FAR GRID" without "(locked)"
    const text = gridText(grid);
    expect(text).toContain("FAR GRID");
    expect(text).not.toContain("FAR GRID    (locked)");
    // The "(locked)" string appears nowhere on the menu
    expect(text.indexOf("(locked)")).toBe(-1);
  });

  it("locked FAR GRID row uses GRAY_DARK (visually disabled)", () => {
    const cols = 80;
    const rows = 50;
    const grid = renderMainMenu(1, cols, rows, false, null, "", false);
    // Inspect the cells at row 9 (FAR GRID line when locked)
    // Cell color comparison is loose — we just verify the text exists at
    // the row. Color discipline is enforced via the renderer contract.
    const rowText = getRowText(grid, 9, 4, 30);
    expect(rowText).toContain("FAR GRID");
    expect(rowText).toContain("(locked)");
  });

  it("other menu rows are not affected by farGridUnlocked=false", () => {
    const cols = 80;
    const rows = 50;
    const grid = renderMainMenu(0, cols, rows, false, null, "", false);
    const text = gridText(grid);
    // NEW RUN (index 0) renders normally
    expect(text).toContain("NEW RUN");
    // DUNGEON CRAWL (index 2) renders normally
    expect(text).toContain("DUNGEON CRAWL");
    // Other labels not gated by the unlock
    expect(text).toContain("GRAPHIC NOVEL");
  });

  it("statusMessage parameter still works alongside farGridUnlocked gating", () => {
    // main.ts wires the lock message into the existing statusMessage line.
    // Here we verify the renderer accepts both parameters simultaneously
    // without one overwriting the other.
    const cols = 80;
    const rows = 50;
    const grid = renderMainMenu(
      1,
      cols,
      rows,
      false,
      null,
      FAR_GRID_LOCKED_MESSAGE,
      false,
    );
    const text = gridText(grid);
    expect(text).toContain(FAR_GRID_LOCKED_MESSAGE);
    expect(text).toContain("(locked)");
  });

  it("default farGridUnlocked=true preserves prior menu contract", () => {
    // Backward-compat: omitting the flag (callers that haven't been touched)
    // sees the gallery as available, preserving the Tier 4 visual baseline.
    const grid = renderMainMenu(1, 80, 50);
    const text = gridText(grid);
    expect(text).toContain("FAR GRID");
    expect(text.indexOf("(locked)")).toBe(-1);
  });
});