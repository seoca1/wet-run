/** Main menu renderer (Tier 4, ADR-0207+/ADR-0209).
 *
 * Mirrors Python's main_menu.py (9 options: NEW_RUN, GRAPHIC_NOVEL,
 * CONTINUE, SETTINGS, CREDITS, HALL_OF_DEAD, HELP, ENDINGS, STATS).
 * Web Tier 4 implements the 6 reachable + 3 deferred (rendered as
 * "Coming soon" stubs to keep the menu 1:1 with Python for design parity).
 *
 * Layout: title block + 9 numbered options + footer. Selected option
 * highlighted with ▸ marker (matches mission select convention).
 */
import type { Grid } from "../core/types.ts";
import { makeGrid, setText } from "../core/grid.ts";
import { PALETTE } from "./palette.ts";

export type MenuOption =
  | "new_run"
  | "graphic_novel"
  | "continue"
  | "settings"
  | "credits"
  | "hall_of_dead"
  | "help"
  | "endings"
  | "stats";

/** All 9 menu options in display order. Order matches Python OPTION_* constants. */
export const MENU_OPTIONS: ReadonlyArray<{ key: MenuOption; label: string; available: boolean }> = [
  { key: "new_run", label: "NEW RUN", available: true },
  { key: "graphic_novel", label: "GRAPHIC NOVEL", available: true },
  { key: "continue", label: "CONTINUE", available: true },
  { key: "settings", label: "SETTINGS", available: true },
  { key: "credits", label: "CREDITS", available: true },
  { key: "hall_of_dead", label: "HALL OF DEAD", available: true },
  { key: "help", label: "HELP", available: true },
  { key: "endings", label: "ENDINGS", available: true },
  { key: "stats", label: "STATS", available: true },
] as const;

/** Render the main menu screen with the selected option highlighted. */
export function renderMainMenu(
  selected: number,
  cols: number,
  rows: number,
): Grid {
  let grid = makeGrid(cols, rows);

  // Title block (top)
  grid = setText(grid, Math.max(2, Math.floor((cols - 8) / 2)), 2, "WET RUN", PALETTE.GREEN_NEON);
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 40) / 2)),
    4,
    "A cyberpunk roguelike based on Gibson's Sprawl trilogy",
    PALETTE.GRAY_LIGHT,
  );

  // Divider
  grid = setText(grid, 2, 6, "─".repeat(Math.min(cols - 4, 60)), PALETTE.GRAY_MID);

  // Options list (starting at row 8)
  const startY = 8;
  for (let i = 0; i < MENU_OPTIONS.length; i++) {
    const opt = MENU_OPTIONS[i];
    if (!opt) continue;
    const isSelected = i === selected;
    const marker = isSelected ? "▸" : " ";
    const num = (i + 1).toString();
    const fg = isSelected ? PALETTE.GREEN_NEON : PALETTE.GRAY_LIGHT;
    const row = startY + i;
    if (row >= rows - 1) break;
    const label = `[${num}] ${opt.label}`;
    grid = setText(grid, 4, row, `${marker} ${label}`, fg);
  }

  // Footer
  const footerRow = rows - 2;
  grid = setText(
    grid,
    2,
    footerRow,
    "Arrow keys: navigate | ENTER: select | ESC/Q: quit",
    PALETTE.GRAY_DARK,
  );
  grid = setText(
    grid,
    2,
    footerRow + 1,
    "Tier 4 · v0.1.0 · ADR-0209 IDB",
    PALETTE.GRAY_DARK,
  );

  return grid;
}

/** Render a stub screen for options not yet implemented (Tier 5+).
 *
 * Shows the option name + "Coming soon" message so the user gets
 * immediate feedback when selecting a deferred menu item.
 */
export function renderStubScreen(
  optionLabel: string,
  cols: number,
  rows: number,
): Grid {
  let grid = makeGrid(cols, rows);
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - optionLabel.length) / 2)),
    Math.floor(rows / 2) - 2,
    optionLabel,
    PALETTE.GREEN_NEON,
  );
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 20) / 2)),
    Math.floor(rows / 2),
    "[ Coming soon — Tier 5+ ]",
    PALETTE.YELLOW_AMBER,
  );
  grid = setText(
    grid,
    2,
    rows - 2,
    "ENTER/ESC: back to main menu",
    PALETTE.GRAY_DARK,
  );
  return grid;
}