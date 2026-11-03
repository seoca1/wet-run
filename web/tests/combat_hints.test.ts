import { describe, expect, it } from "vitest";
import {
  COST_CAPPED_LINE,
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

  it("states the killing-blow COST rule once, at combat entry (ADR-0258)", () => {
    // The hand row may not predict the killing blow (kill prediction is
    // forbidden), so the rule is taught here.
    expect(COMBAT_ENTRY_HINT_LINES.join(" ")).toContain("last-hit");
    expect(COMBAT_ENTRY_HINT_LINES.join(" ")).toContain("no COST");
    // The new line fits the narrowest layout (40 columns, x=2).
    const rule = COMBAT_ENTRY_HINT_LINES.find((l) => l.includes("last-hit"));
    expect(rule).toBeDefined();
    expect(rule!.length).toBeLessThanOrEqual(38);
  });

  it("draws every entry line, including the COST rule", () => {
    const grid = makeGrid(80, 50);
    const out = renderCombatHints(grid, { showHint: true, pressLabel: null });
    const rows = combatEntryHintRows(50);
    expect(rows).toHaveLength(COMBAT_ENTRY_HINT_LINES.length);
    const text = rows.map((r) => rowText(out, r).trim()).join("\n");
    expect(text).toContain("last-hit");
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

describe("COST-capped pass line (ADR-0266)", () => {
  it("appears on the last hint row, in red, exactly when asked", () => {
    const grid = makeGrid(80, 50);
    const out = renderCombatHints(grid, {
      showHint: false,
      pressLabel: null,
      costCapped: true,
    });
    const row = combatEntryHintRows(50)[COMBAT_ENTRY_HINT_LINES.length - 1];
    expect(rowText(out, row!).slice(2).trimEnd()).toBe(COST_CAPPED_LINE);
    expect(out.cells[row!]?.[2]?.fg).toBe(PALETTE.RED_BRIGHT);
    // And it is not there when the cap is not hit.
    const plain = renderCombatHints(makeGrid(80, 50), {
      showHint: false,
      pressLabel: null,
      costCapped: false,
    });
    expect(rowText(plain, row!)).not.toContain("COST capped");
  });

  it("fits the narrowest layout whole — a clipped instruction is a lie", () => {
    // 40 columns is the tightest grid; the line must fit inside the frame
    // (x=2, so 40 - 2 = 38 cells, minus the rail).
    expect(COST_CAPPED_LINE.length + 2).toBeLessThanOrEqual(40 - 2);
    const grid = makeGrid(40, 60);
    const out = renderCombatHints(grid, {
      showHint: false,
      pressLabel: null,
      costCapped: true,
    });
    const row = combatEntryHintRows(60)[COMBAT_ENTRY_HINT_LINES.length - 1];
    expect(rowText(out, row!).slice(2).trimEnd()).toBe(COST_CAPPED_LINE);
    // Nothing spills past the grid either.
    for (let y = 0; y < out.height; y += 1) {
      expect(rowText(out, y).length).toBeLessThanOrEqual(40);
    }
  });
});
