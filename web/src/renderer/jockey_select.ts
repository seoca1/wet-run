/** Choose the jockey the run belongs to (ADR-0274).
 *
 * The graphic-novel prologue is one story per jockey. It used to hand over to
 * mission select and the run began anonymous, so the story just read left no
 * trace. This is the handover: pick the jockey, then the mission, then play —
 * and the run names its runner in the intro and in the ending summary.
 *
 * Display-only: the choice changes no number.
 */
import { makeGrid, setText, type Grid } from "../core/grid";
import { JOCKEYS } from "../core/state/jockey";
import { PALETTE } from "./palette";

/** Lines the screen needs, so a narrow layout can be checked against it. */
export function jockeySelectFits(rows: number): boolean {
  return rows >= 12;
}

export function renderJockeySelect(
  selected: number,
  cols: number,
  rows: number,
): Grid {
  let grid = makeGrid(cols, rows);
  const title = "WHO IS JACKING IN";
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - title.length) / 2)),
    Math.max(2, Math.floor(rows / 2) - 6),
    title,
    PALETTE.GREEN_NEON,
  );

  let y = Math.floor(rows / 2) - 3;
  JOCKEYS.forEach((jockey, i) => {
    const row = `${i + 1} ${jockey.handle}`;
    const isSelected = i === selected;
    grid = setText(
      grid,
      Math.max(2, Math.floor((cols - 24) / 2)),
      y,
      `${isSelected ? ">" : " "} ${row}`,
      isSelected ? PALETTE.GREEN_NEON : PALETTE.GRAY_MID,
    );
    const tagline = jockey.tagline.slice(0, Math.max(8, cols - 6));
    grid = setText(
      grid,
      Math.max(2, Math.floor((cols - tagline.length) / 2)),
      y + 1,
      tagline,
      isSelected ? PALETTE.GRAY_LIGHT : PALETTE.GRAY_DARK,
    );
    y += 3;
  });

  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 30) / 2)),
    rows - 3,
    "↑↓: pick | ENTER: jack in",
    PALETTE.GRAY_DARK,
  );
  return grid;
}
