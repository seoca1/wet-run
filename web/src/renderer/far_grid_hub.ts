/** Far Grid hub renderer (ADR-0213, Phase 1).
 *
 * Mirrors the mission select layout convention (header / intro / list /
 * footer) so the player gets the same navigation muscle memory. Renders
 * Far Grid-tagged missions as a separate list, framing the Far Grid as
 * a destination set apart from the Sprawl's regular mission board.
 */
import type { Grid, Mission } from "../core/types.ts";
import { makeGrid, setText } from "../core/grid.ts";
import { PALETTE } from "./palette.ts";

/** Render the Far Grid hub screen.
 *
 * Layout (matches mission_select convention from main.ts):
 *   row 1   : header "FAR GRID HUB"
 *   row 3   : intro line framing Far Grid as set apart from Sprawl
 *   row 5.. : mission list (title per row, ▸ marker on selected)
 *   row N   : empty-list message when missions array is empty
 *   footer  : ESC/ENTER hints mirroring mission_select
 */
export function renderFarGridHub(
  missions: ReadonlyArray<Mission>,
  selected: number,
  cols: number,
  rows: number,
  statusMessage: string = "",
): Grid {
  let grid = makeGrid(cols, rows);

  // Header (mirrors mission_select's "WET RUN — Select Mission" line)
  grid = setText(grid, 2, 1, "FAR GRID HUB", PALETTE.GREEN_NEON);

  // Intro — frame the Far Grid as set apart from Sprawl's mission board
  grid = setText(
    grid,
    2,
    3,
    "Beyond the Sprawl — Far Grid-tagged missions",
    PALETTE.GRAY_LIGHT,
  );

  // Mission list — start at row 5 to mirror mission_select's spacing
  const listStartY = 5;
  if (missions.length === 0) {
    grid = setText(
      grid,
      2,
      listStartY,
      "(no Far Grid missions available)",
      PALETTE.GRAY_DARK,
    );
  } else {
    let y = listStartY;
    for (let i = 0; i < missions.length; i++) {
      const m = missions[i];
      if (!m) continue;
      const isSelected = i === selected;
      const fg = isSelected ? PALETTE.GREEN_NEON : PALETTE.GRAY_LIGHT;
      const marker = isSelected ? "▸" : " ";
      const source = m.story?.source
        ? ` [Source: ${m.story.source.slice(0, 60)}]`
        : "";
      grid = setText(grid, 4, y, `${marker} ${m.title}${source}`, fg);
      y += 1;
    }
  }

  // Optional status line — placed just above the footer, only when given.
  if (statusMessage) {
    const statusY = rows - 3;
    if (statusY > listStartY) {
      grid = setText(grid, 2, statusY, statusMessage, PALETTE.YELLOW_AMBER);
    }
  }

  // Footer — mirror mission_select's "↑↓: navigate | ENTER: launch | ESC: back"
  const footerY = rows - 2;
  grid = setText(
    grid,
    2,
    footerY,
    "↑↓: navigate | ENTER: launch | ESC: back",
    PALETTE.GRAY_DARK,
  );

  return grid;
}
