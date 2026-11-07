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
  /** What this option is worth here, including the stockpile's share. */
  readonly amount: number;
  /** How much of `amount` came from the stockpile (ADR-0284). */
  readonly fromWallet: number;
  readonly unit: string;
  readonly note: string;
}

export interface PrepView {
  readonly missionTitle: string;
  readonly grade: number;
  readonly cursor: number;
  /** The runner's banked credits, or 0 when there is none. */
  readonly wallet: number;
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
  put(
    top + 2,
    view.wallet > 0
      ? `grade ${view.grade} — advance + ${view.wallet}cr banked`
      : `grade ${view.grade} — the fixer's advance`,
    PALETTE.GRAY_LIGHT,
  );

  view.options.forEach((option, i) => {
    const mark = i === view.cursor ? ">" : " ";
    // Show the split when the stockpile paid for part of it: the screen must
    // not claim the mission gave more than it did (ADR-0251 rule 5).
    const worth =
      option.amount <= 0
        ? "nothing offered"
        : option.fromWallet > 0
          ? `+${option.amount} ${option.unit} (${option.fromWallet} banked)`
          : `+${option.amount} ${option.unit}`;
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
