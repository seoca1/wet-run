import { setText, type Grid } from "../core/grid";
import {
  COMBAT_ENTRY_HINT_LINES,
  combatEntryHintRows,
} from "../core/state/onboarding";
import { PALETTE } from "./palette";

/** Existing hint rows, shared by entry instructions and press acknowledgement. */
export function combatHintsLayout(rows: number) {
  return { x: 2, rows: combatEntryHintRows(rows) } as const;
}

/** ADR-0266: with every program over the COST limit the turn cannot advance by
 * playing, so ENTER ends it instead. The line states that, and the give-up key,
 * in that order -- it appears exactly when the refusal does, because both read
 * `everyProgramBlocked`. */
export const COST_CAPPED_LINE = "COST capped: ENTER pass · ESC quit";

export interface CombatHintView {
  readonly showHint: boolean;
  readonly pressLabel: string | null;
  /** True when every program in hand is over the COST limit. */
  readonly costCapped?: boolean;
}

/** Draw entry instructions under feedback; the controller owns the once-per-run
 * flag. The COST-capped line takes the last hint row, below the entry hint and
 * the press acknowledgement, so the three can share the band without overlap. */
export function renderCombatHints(grid: Grid, view: CombatHintView): Grid {
  let out = grid;
  const layout = combatHintsLayout(grid.height);
  if (view.showHint) {
    COMBAT_ENTRY_HINT_LINES.forEach((line, index) => {
      const row = layout.rows[index];
      if (row === undefined) return;
      out = setText(out, layout.x, row, line, PALETTE.YELLOW_AMBER);
    });
  }
  if (view.pressLabel !== null) {
    out = setText(
      out,
      layout.x,
      layout.rows[0] ?? 0,
      view.pressLabel,
      PALETTE.GREEN_NEON,
    );
  }
  if (view.costCapped === true) {
    const row = layout.rows[layout.rows.length - 1];
    // Only draw it whole: a clipped instruction would tell the player half a
    // key. The line is written for the 40-column layout (34 cells at x=2).
    if (row !== undefined && layout.x + COST_CAPPED_LINE.length <= grid.width) {
      out = setText(out, layout.x, row, COST_CAPPED_LINE, PALETTE.RED_BRIGHT);
    }
  }
  return out;
}
