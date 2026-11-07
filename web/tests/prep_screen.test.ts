/**
 * ADR-0283 C''' — the prep screen prices the advance, and the two options cross.
 *
 * Prep was an automatic max-HP grant until the shield was measured: it beats the
 * pool at grades 3-4 (a small pool covers the early fights) and loses badly at
 * grade 5, because the loot repair is a percentage of max HP so a bigger pool
 * compounds. That crossover is what makes this a decision rather than a buff.
 *
 * Measured at 20 seeds, loot=smart:
 *   stim  100.0 / 98.1 / 82.3 / 46.5 / 30.6 / 16.7   (all six inside tolerance)
 *   ice   100.0 / 98.8 / 68.2 / 53.5 / 22.2 / 10.0   (five; stim wins 3 and 5)
 */
import { describe, expect, it } from "vitest";
import { renderPrep } from "../src/renderer/prep";
import {
  PREP_HP_BY_GRADE,
  PREP_OPTIONS,
  PREP_SHIELD_BY_GRADE,
  prepGrantFor,
} from "../src/core/state/prep";

function text(grid: { cells: ReadonlyArray<ReadonlyArray<{ char: string }>> }): string {
  return grid.cells
    .map((row) => row.map((c) => c.char).join(""))
    .join("\n");
}

function view(grade: number, cursor = 0, wallet = 0) {
  return {
    missionTitle: "Test Mission",
    grade,
    cursor,
    wallet,
    options: PREP_OPTIONS.map((o) => {
      const grant = prepGrantFor(grade, o.id, wallet);
      return {
        id: o.id,
        label: o.label,
        amount: grant.total,
        fromWallet: grant.fromWallet,
        unit: o.id === "ice" ? "shield" : "HP",
        note: o.short,
      };
    }),
  };
}

describe("ADR-0283 C''' · the prep screen", () => {
  it("prints the amount each option is actually worth here", () => {
    // Given / When: a grade-5 mission, where both options are granted.
    const screen = text(renderPrep(view(5), 80, 50));

    // Then: the numbers are the tables' own, so the screen cannot lie.
    expect(screen).toContain(`+${PREP_HP_BY_GRADE[4]} HP`);
    expect(screen).toContain(`+${PREP_SHIELD_BY_GRADE[4]} shield`);
  });

  it("marks the row under the cursor", () => {
    // Given / When
    const first = text(renderPrep(view(5, 0), 80, 50));
    const second = text(renderPrep(view(5, 1), 80, 50));

    // Then
    expect(first).toMatch(/> STIM/);
    expect(second).toMatch(/> ICE/);
  });

  it("says when a grade offers nothing", () => {
    // Given: grade 1, where both tables are zero.
    const screen = text(renderPrep(view(1), 80, 50));

    // Then
    expect(screen).toContain("nothing offered");
  });

  it("fits the narrowest preset (40 columns)", () => {
    // Given / When
    const screen = text(renderPrep(view(5), 40, 60));

    // Then: the choice is on screen, not clipped away.
    expect(screen).toContain("STIM");
    expect(screen).toContain("ICE");
    expect(screen).toContain("ENTER");
  });

  it("offers exactly the two options the tables price", () => {
    // Then: a third option without a table would silently sell nothing.
    expect(PREP_OPTIONS.map((o) => o.id)).toEqual(["stim", "ice"]);
    expect(PREP_HP_BY_GRADE).toHaveLength(6);
    expect(PREP_SHIELD_BY_GRADE).toHaveLength(6);
  });
});
