/** Main menu definition + renderer (Tier 4, ADR-0207+/ADR-0209).
 *
 * Split from the former 1039-LOC `menu.ts` monolith (2026-10-12). This module
 * owns the menu option table and the top-level main-menu / stub screens.
 * Mirrors Python's main_menu.py (9 options: NEW_RUN, GRAPHIC_NOVEL,
 * CONTINUE, SETTINGS, CREDITS, HALL_OF_DEAD, HELP, ENDINGS, STATS).
 * Web Tier 4 implements the 6 reachable + 3 deferred (rendered as
 * "Coming soon" stubs to keep the menu 1:1 with Python for design parity).
 *
 * Layout: Green Grid frame (renderer/panel.ts) around a centred title block,
 * the numbered options and a footer pinned to the bottom inner rows. Selected
 * option highlighted with ▸ marker (matches mission select convention).
 */
import type { Grid } from "../core/types";
import { makeGrid, setText } from "../core/grid";
import { t, type Language } from "../core/i18n";
import { PALETTE } from "./palette";
import { formatNavIndex } from "./nav_index";
import { drawPanel, panelInnerRect, type PanelRect } from "./panel";

export type MenuOption =
  | "new_run"
  | "graphic_novel"
  | "continue"
  | "settings"
  | "craft"
  | "equipment"
  | "credits"
  | "hall_of_dead"
  | "help"
  | "endings"
  | "stats"
  | "tutorial"
  | "far_grid_hub"
  | "dungeon_crawl";

/** All 14 menu options in display order. Order matches Python OPTION_* constants. */
export const MENU_OPTIONS: ReadonlyArray<{
  key: MenuOption;
  label: string;
  available: boolean;
}> = [
  { key: "new_run", label: "NEW RUN", available: true },
  { key: "far_grid_hub", label: "FAR GRID", available: true },
  { key: "dungeon_crawl", label: "DUNGEON CRAWL", available: true },
  { key: "graphic_novel", label: "GRAPHIC NOVEL", available: true },
  { key: "continue", label: "CONTINUE", available: true },
  { key: "settings", label: "SETTINGS", available: true },
  { key: "craft", label: "CRAFT", available: true },
  { key: "equipment", label: "EQUIPMENT", available: true },
  { key: "credits", label: "CREDITS", available: true },
  { key: "hall_of_dead", label: "HALL OF DEAD", available: true },
  { key: "help", label: "HELP", available: true },
  { key: "endings", label: "ENDINGS", available: true },
  { key: "stats", label: "STATS", available: true },
  { key: "tutorial", label: "TUTORIAL", available: true },
] as const;

/** Rows from the title to the status line: title, subtitle, divider (two-row
 * gaps), the option list, then a blank row, the save hint and the status line.
 */
const MENU_BLOCK_ROWS = 6 + MENU_OPTIONS.length + 3;

/** Where the main menu places its content inside the Green Grid frame. */
export interface MainMenuLayout {
  readonly frame: PanelRect;
  readonly inner: PanelRect;
  readonly titleY: number;
  readonly optionsX: number;
  readonly optionsY: number;
  /** First of the two footer rows (controls hint, then version). */
  readonly footerY: number;
}

/** Widest option row in any gating state, so the column never jumps. */
function widestOptionRow(language: Language): number {
  let widest = 0;
  for (let i = 0; i < MENU_OPTIONS.length; i++) {
    const opt = MENU_OPTIONS[i];
    if (!opt) continue;
    let label = `${formatNavIndex(i)} ${t(`menu.${opt.key}`, language)}`;
    if (opt.key === "continue") label += `    ${t("menu.no_save", language)}`;
    if (opt.key === "far_grid_hub")
      label += `    ${t("menu.locked", language)}`;
    widest = Math.max(widest, label.length + 2);
  }
  return widest;
}

/** Compose the main menu inside a full-grid frame (ADR-0237 §2).
 *
 * The footer sits on the last two inner rows; the title-to-status block is
 * centred vertically in the space above it and the option column is centred
 * horizontally. Grids too small to centre fall back to the original offsets
 * (title two rows down, options at column 4).
 */
export function mainMenuLayout(
  grid: Grid,
  language: Language = "en",
): MainMenuLayout {
  const frame: PanelRect = {
    x: 0,
    y: 0,
    width: grid.width,
    height: grid.height,
  };
  const inner = panelInnerRect(grid, frame);
  const footerY = inner.y + inner.height - 2;
  const available = footerY - 1 - inner.y;
  const titleY =
    inner.y + Math.max(1, Math.floor((available - MENU_BLOCK_ROWS) / 2));
  const optionsX =
    inner.x +
    Math.max(3, Math.floor((inner.width - widestOptionRow(language)) / 2));
  return { frame, inner, titleY, optionsX, optionsY: titleY + 6, footerY };
}

function centredX(inner: PanelRect, width: number): number {
  return inner.x + Math.max(1, Math.floor((inner.width - width) / 2));
}

/** Render the main menu screen with the selected option highlighted.
 *
 * CONTINUE option is grayed out (GRAY_DARK + " (no save)") when hasSave=false.
 * Pass hasSave=true and saveMeta (optional) for full continue hint.
 *
 * FAR GRID option is grayed out (GRAY_DARK + " (locked)") when
 * farGridUnlocked=false (ADR-0213 Phase 2 gate). Status messages from the
 * locked-selection path will surface on the existing `statusMessage` line —
 * main.ts owns the message text (no UI strings here).
 *
 * Content is placed by `mainMenuLayout` inside a `drawPanel` frame.
 */
export function renderMainMenu(
  selected: number,
  cols: number,
  rows: number,
  hasSave: boolean = false,
  saveMeta: { missionId: string; turnCount: number } | null = null,
  statusMessage: string = "",
  farGridUnlocked: boolean = true,
  language: Language = "en",
): Grid {
  let grid = makeGrid(cols, rows);
  const layout = mainMenuLayout(grid, language);
  const { inner, titleY, optionsX, optionsY: startY, footerY } = layout;

  // Title block
  const title = t("menu.title", language);
  grid = setText(
    grid,
    centredX(inner, title.length),
    titleY,
    title,
    PALETTE.GREEN_NEON,
  );
  const subtitle = t("menu.subtitle", language);
  grid = setText(
    grid,
    centredX(inner, subtitle.length),
    titleY + 2,
    subtitle,
    PALETTE.GRAY_LIGHT,
  );

  // Divider
  const dividerWidth = Math.max(0, Math.min(inner.width - 2, 60));
  grid = setText(
    grid,
    centredX(inner, dividerWidth),
    titleY + 4,
    "─".repeat(dividerWidth),
    PALETTE.GRAY_MID,
  );

  // Options list
  for (let i = 0; i < MENU_OPTIONS.length; i++) {
    const opt = MENU_OPTIONS[i];
    if (!opt) continue;
    const isSelected = i === selected;
    const marker = isSelected ? "▸" : " ";
    const num = formatNavIndex(i);
    const fg = isSelected ? PALETTE.GREEN_NEON : PALETTE.GRAY_LIGHT;
    const row = startY + i;
    if (row >= footerY) break;
    let label = `${num} ${t(`menu.${opt.key}`, language)}`;
    // CONTINUE option gating — gray out + suffix when no save.
    if (opt.key === "continue" && !hasSave) {
      label = `${num} ${t("menu.continue", language)}    ${t("menu.no_save", language)}`;
      grid = setText(
        grid,
        optionsX,
        row,
        `${marker} ${label}`,
        PALETTE.GRAY_DARK,
      );
      continue;
    }
    // FAR GRID option gating — gray out + suffix when locked (ADR-0213 Phase 2).
    if (opt.key === "far_grid_hub" && !farGridUnlocked) {
      label = `${num} ${t("menu.far_grid_hub", language)}    ${t("menu.locked", language)}`;
      grid = setText(
        grid,
        optionsX,
        row,
        `${marker} ${label}`,
        PALETTE.GRAY_DARK,
      );
      continue;
    }
    grid = setText(grid, optionsX, row, `${marker} ${label}`, fg);
  }

  // Continue hint sub-line (when save exists). Place below all menu items
  // (MENU_OPTIONS.length + 1 row after startY) to avoid overlap.
  if (hasSave && saveMeta) {
    const hintRow = startY + MENU_OPTIONS.length + 1;
    if (hintRow < footerY) {
      const hint = `→ ${saveMeta.missionId} (turn ${saveMeta.turnCount + 1})`;
      grid = setText(grid, optionsX + 2, hintRow, hint, PALETTE.YELLOW_AMBER);
    }
  }

  // Status message line (shown after save hint, before footer).
  if (statusMessage) {
    const msgRow = startY + MENU_OPTIONS.length + 2;
    if (msgRow < footerY) {
      grid = setText(
        grid,
        Math.max(inner.x + 1, optionsX - 2),
        msgRow,
        statusMessage,
        PALETTE.YELLOW_AMBER,
      );
    }
  }

  // Footer
  grid = setText(
    grid,
    inner.x + 1,
    footerY,
    t("menu.footer", language),
    PALETTE.GRAY_DARK,
  );
  grid = setText(
    grid,
    inner.x + 1,
    footerY + 1,
    t("menu.version", language),
    PALETTE.GRAY_DARK,
  );

  // Frame last, so an overlong status line can never erase a rail.
  return drawPanel(grid, layout.frame).grid;
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
    "ESC: back to main menu",
    PALETTE.GRAY_DARK,
  );
  return grid;
}
