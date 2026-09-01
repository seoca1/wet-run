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

/** Render the main menu screen with the selected option highlighted.
 *
 * CONTINUE option is grayed out (GRAY_DARK + " (no save)") when hasSave=false.
 * Pass hasSave=true and saveMeta (optional) for full continue hint.
 */
export function renderMainMenu(
  selected: number,
  cols: number,
  rows: number,
  hasSave: boolean = false,
  saveMeta: { missionId: string; turnCount: number } | null = null,
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
    let label = `[${num}] ${opt.label}`;
    // CONTINUE option gating — gray out + suffix when no save.
    if (opt.key === "continue" && !hasSave) {
      label = `[${num}] CONTINUE    (no save)`;
      grid = setText(grid, 4, row, `${marker} ${label}`, PALETTE.GRAY_DARK);
      continue;
    }
    grid = setText(grid, 4, row, `${marker} ${label}`, fg);
  }

  // Continue hint sub-line (when save exists).
  if (hasSave && saveMeta) {
    const hintRow = startY + 2;
    if (hintRow < rows - 2) {
      const hint = `→ ${saveMeta.missionId} (turn ${saveMeta.turnCount + 1})`;
      grid = setText(grid, 6, hintRow, hint, PALETTE.YELLOW_AMBER);
    }
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

/** Render the settings screen with volume sliders and sync status. */
export function renderSettingsScreen(
  bgmVolume: number,
  sfxVolume: number,
  cols: number,
  rows: number,
  syncStatus?: { status: string; lastSync: string | null; error: string | null; pushed: number; pulled: number },
): Grid {
  let grid = makeGrid(cols, rows);
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 8) / 2)),
    2,
    "SETTINGS",
    PALETTE.GREEN_NEON,
  );
  grid = setText(grid, 2, 4, "─".repeat(Math.min(cols - 4, 60)), PALETTE.GRAY_MID);

  // BGM Volume
  const bgmBar = volumeBar(bgmVolume, 20);
  grid = setText(grid, 4, 8, "BGM Volume", PALETTE.GRAY_LIGHT);
  grid = setText(grid, 4, 9, bgmBar, PALETTE.YELLOW_AMBER);
  grid = setText(grid, 4, 10, `← / → to adjust  (${Math.round(bgmVolume * 100)}%)`, PALETTE.GRAY_DARK);

  // SFX Volume
  const sfxBar = volumeBar(sfxVolume, 20);
  grid = setText(grid, 4, 13, "SFX Volume", PALETTE.GRAY_LIGHT);
  grid = setText(grid, 4, 14, sfxBar, PALETTE.YELLOW_AMBER);
  grid = setText(grid, 4, 15, `← / → to adjust  (${Math.round(sfxVolume * 100)}%)`, PALETTE.GRAY_DARK);

  // Sync Status Section
  const syncStartRow = 18;
  grid = setText(grid, 2, syncStartRow, "─".repeat(Math.min(cols - 4, 60)), PALETTE.GRAY_MID);
  grid = setText(grid, 4, syncStartRow + 1, "CLOUD SYNC (Tier 3)", PALETTE.GREEN_NEON);
  
  if (syncStatus) {
    const statusColors: Record<string, string> = {
      idle: PALETTE.GRAY_LIGHT,
      syncing: PALETTE.YELLOW_AMBER,
      success: PALETTE.GREEN_NEON,
      error: PALETTE.RED_BRIGHT,
      offline: PALETTE.GRAY_DARK,
    };
    const statusColor = statusColors[syncStatus.status] ?? PALETTE.GRAY_LIGHT;
    
    grid = setText(grid, 4, syncStartRow + 3, `Status: ${syncStatus.status.toUpperCase()}`, statusColor);
    
    if (syncStatus.lastSync) {
      const lastSync = new Date(syncStatus.lastSync).toLocaleTimeString();
      grid = setText(grid, 4, syncStartRow + 4, `Last sync: ${lastSync}`, PALETTE.GRAY_DARK);
    }
    
    if (syncStatus.error) {
      grid = setText(grid, 4, syncStartRow + 5, `Error: ${syncStatus.error}`, PALETTE.RED_BRIGHT);
    }
    
    if (syncStatus.pushed > 0 || syncStatus.pulled > 0) {
      grid = setText(grid, 4, syncStartRow + 6, `Pushed: ${syncStatus.pushed}  Pulled: ${syncStatus.pulled}`, PALETTE.GRAY_LIGHT);
    }
  } else {
    grid = setText(grid, 4, syncStartRow + 3, "Status: NOT CONFIGURED", PALETTE.GRAY_DARK);
    grid = setText(grid, 4, syncStartRow + 4, "Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY", PALETTE.GRAY_DARK);
  }

  // Mute status
  const audio = (window as unknown as { audioManager?: { isMuted: () => boolean } }).audioManager;
  if (audio) {
    grid = setText(grid, 4, syncStartRow + 8, `M key: ${audio.isMuted() ? "UNMUTE" : "MUTE"} all audio`, PALETTE.GRAY_DARK);
  }

  // Footer
  grid = setText(grid, 2, rows - 2, "ENTER/ESC: back to main menu", PALETTE.GRAY_DARK);
  grid = setText(grid, 2, rows - 1, "M: toggle mute | Arrows: adjust volumes | S: sync now", PALETTE.GRAY_DARK);

  return grid;
}

/** Generate a volume bar string: [█████░░░░░░░░░░░░] */
function volumeBar(volume: number, width: number): string {
  const filled = Math.round(Math.max(0, Math.min(1, volume)) * width);
  return "[" + "█".repeat(filled) + "░".repeat(width - filled) + "]";
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