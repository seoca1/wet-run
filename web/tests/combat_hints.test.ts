import { describe, expect, it } from "vitest";
import {
  combatHintsLayout,
  renderCombatHints,
} from "../src/renderer/combat_hints";
import { makeGrid } from "../src/core/grid";
import {
  COMBAT_ENTRY_HINT_LINES,
  combatEntryHintRows,
} from "../src/core/state/onboarding";
import { PALETTE } from "../src/renderer/palette";
import { rowText } from "./view_fixtures";

describe("combat hint composition", () => {
  it("returns the input grid when neither hint nor feedback is requested", () => {
    const grid = makeGrid(80, 50);
    expect(renderCombatHints(grid, { showHint: false, pressLabel: null })).toBe(
      grid,
    );
  });

  it("keeps entry instructions at their original rows in amber", () => {
    const grid = makeGrid(80, 50);
    const out = renderCombatHints(grid, { showHint: true, pressLabel: null });
    expect(combatHintsLayout(50)).toEqual({
      x: 2,
      rows: combatEntryHintRows(50),
    });
    combatEntryHintRows(50).forEach((row, i) => {
      expect(rowText(out, row).slice(2).trimEnd()).toBe(
        COMBAT_ENTRY_HINT_LINES[i],
      );
      expect(out.cells[row]?.[2]?.fg).toBe(PALETTE.YELLOW_AMBER);
    });
  });

  it("draws press acknowledgement last in green over the entry hint", () => {
    const grid = makeGrid(80, 50);
    const out = renderCombatHints(grid, {
      showHint: true,
      pressLabel: "Pressed ATK",
    });
    const row = combatEntryHintRows(50)[0] ?? 0;
    expect(rowText(out, row).slice(2, 13)).toBe("Pressed ATK");
    expect(out.cells[row]?.[2]?.fg).toBe(PALETTE.GREEN_NEON);
    expect(rowText(grid, row).trim()).toBe("");
  });
});
