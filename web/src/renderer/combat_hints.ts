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

/** Draw entry instructions under feedback; the controller owns the once-per-run flag. */
export function renderCombatHints(
  grid: Grid,
  view: { readonly showHint: boolean; readonly pressLabel: string | null },
): Grid {
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
  return out;
}
