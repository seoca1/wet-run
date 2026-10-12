/** Death / flatline menu screens (Tier 4).
 *
 * Split from the former 1039-LOC `menu.ts` monolith (2026-10-12). This module
 * owns the terminal run-end screens: the death restart summary and the
 * unrecoverable flatline screen.
 */
import type { Grid } from "../core/types.ts";
import { makeGrid, setText } from "../core/grid.ts";
import { PALETTE } from "./palette.ts";

/** Render the death restart screen (death_restart stage).
 *
 * Stage: death_restart — After death screen. Player chooses to restart or quit.
 */
export function renderDeathRestartScreen(
  cols: number,
  rows: number,
  summary: {
    jockeyName: string;
    mission: string;
    grade: number;
    playtimeMinutes: number;
    totalRuns: number;
    totalDeaths: number;
  },
): Grid {
  let grid = makeGrid(cols, rows);

  // Title
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 14) / 2)),
    1,
    "⚠ FLATLINE",
    PALETTE.RED_BRIGHT,
  );

  // ASCII art
  const asciiArt = [
    "  ┌──────────────────────┐",
    "  │  ⚠ FLATLINE         │",
    "  │  ◢◣◢◣◢◣◢◣◢◣◢◣◢◣◢◣  │",
    "  │  ░▒▓ Equipment LOST ▓▒░  │",
    "  │  ░▒▓ Grade kept     ▓▒░  │",
    "  └──────────────────────┘",
  ];
  const startY = 3;
  for (let i = 0; i < asciiArt.length; i++) {
    grid = setText(
      grid,
      Math.max(2, Math.floor((cols - 28) / 2)),
      startY + i,
      asciiArt[i],
      PALETTE.RED_BRIGHT,
    );
  }

  // Jockey summary
  const summaryY = startY + asciiArt.length + 1;
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 20) / 2)),
    summaryY,
    `Jockey: ${summary.jockeyName}`,
    PALETTE.GRAY_LIGHT,
  );
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 20) / 2)),
    summaryY + 1,
    `Mission: ${summary.mission} (Grade ${summary.grade})`,
    PALETTE.GRAY_LIGHT,
  );
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 25) / 2)),
    summaryY + 2,
    `Playtime: ${summary.playtimeMinutes} min | Runs: ${summary.totalRuns} | Deaths: ${summary.totalDeaths}`,
    PALETTE.GRAY_LIGHT,
  );

  // Options
  const optionsY = summaryY + 4;
  const options = [
    { label: "[ENTER] Restart — New Jockey", action: "restart" },
    { label: "[ESC] Quit to Menu", action: "quit" },
  ];
  for (let i = 0; i < options.length; i++) {
    const opt = options[i];
    grid = setText(
      grid,
      Math.max(2, Math.floor((cols - opt.label.length) / 2)),
      optionsY + i,
      opt.label,
      PALETTE.GRAY_LIGHT,
    );
  }

  // Footer
  const footerY = rows - 2;
  grid = setText(
    grid,
    2,
    footerY,
    "ENTER: restart | ESC: quit to menu",
    PALETTE.GRAY_DARK,
  );

  return grid;
}

/** Render the failed/flatline screen (failed stage).
 *
 * Stage: failed — Terminal flatline state. No recovery, only acknowledgment.
 */
export function renderFailedScreen(cols: number, rows: number): Grid {
  let grid = makeGrid(cols, rows);

  // Title
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 14) / 2)),
    1,
    "✗ FLATLINE",
    PALETTE.RED_BRIGHT,
  );

  // ASCII art
  const asciiArt = [
    "  ┌──────────────────────┐",
    "  │  ✗ FLATLINE          │",
    "  │  ◢◣◢◣◢◣◢◣◢◣◢◣◢◣◢◣  │",
    "  │  ░▒▓ Equipment LOST ▓▒░  │",
    "  │  ░▒▓ Grade kept     ▓▒░  │",
    "  └──────────────────────┘",
  ];
  const startY = 3;
  for (let i = 0; i < asciiArt.length; i++) {
    grid = setText(
      grid,
      Math.max(2, Math.floor((cols - 28) / 2)),
      startY + i,
      asciiArt[i],
      PALETTE.RED_BRIGHT,
    );
  }

  // Footer
  const footerY = rows - 2;
  grid = setText(
    grid,
    2,
    footerY,
    "ENTER: return to menu | ESC: quit",
    PALETTE.GRAY_DARK,
  );

  return grid;
}
