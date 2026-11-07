/** The prep screen — what the fixer's advance is spent on (ADR-0283 C''').
 *
 * Two options, and the right one depends on the mission: a max-HP stim buys the
 * long haul (the loot repair is a percentage of max HP, so a bigger pool
 * compounds), while a starting shield buys the opening fights, where the damage
 * per fight is modest. Measured, each wins at different grades.
 *
 * Two rows, so it needs no new key: ↑↓ moves, ENTER jacks in with the pick, ESC
 * goes back to the board.
 */
import { makeGrid, setText } from "../core/grid";
import { PALETTE } from "./palette";
import type { Grid } from "../core/types";
import type { PrepChoice } from "../core/state/prep";

export interface PrepOptionRow {
  readonly id: PrepChoice;
  readonly label: string;
  /** What this option is worth at the mission's grade; 0 means nothing to buy. */
  readonly amount: number;
  readonly unit: string;
  readonly note: string;
}

export interface PrepView {
  readonly missionTitle: string;
  readonly grade: number;
  readonly cursor: number;
  readonly options: readonly PrepOptionRow[];
}

/** The narrowest preset (40 columns) leaves 36 usable. */
const TEXT_COLS = 34;

export function renderPrep(view: PrepView, cols: number, rows: number): Grid {
  let grid = makeGrid(cols, rows);
  const put = (y: number, text: string, fg: string): void => {
    const clipped = text.slice(0, TEXT_COLS);
    grid = setText(
      grid,
      Math.max(1, Math.floor((cols - clipped.length) / 2)),
      y,
      clipped,
      fg,
    );
  };

  const top = Math.max(1, Math.floor(rows / 2) - 6);
  put(top, "PREP", PALETTE.GREEN_NEON);
  put(top + 1, view.missionTitle, PALETTE.CYAN_LIGHT);
  put(top + 2, `grade ${view.grade} — the fixer's advance`, PALETTE.GRAY_LIGHT);

  view.options.forEach((option, i) => {
    const mark = i === view.cursor ? ">" : " ";
    const worth =
      option.amount > 0 ? `+${option.amount} ${option.unit}` : "nothing offered";
    put(
      top + 4 + i * 2,
      `${mark} ${option.label}  ${worth}`,
      i === view.cursor ? PALETTE.CYAN_LIGHT : PALETTE.GRAY_LIGHT,
    );
    put(top + 5 + i * 2, `    ${option.note}`, PALETTE.GRAY_DARK);
  });

  put(rows - 3, "ENTER: jack in with this", PALETTE.YELLOW_AMBER);
  put(rows - 2, "ESC: back to the board", PALETTE.GRAY_DARK);
  return grid;
}
