/** ADR-0262 — the growth reveal: the card joining the deck as a staged event.
 *
 * ADR-0261 made the acquisition honest (sound, a pause, a mark) but the
 * presentation was a colour change. This slice keeps the same discipline and
 * adds the *event*: the terminal commits the program, and the board names the
 * card again once the runner is back in play.
 *
 * The contract these tests pin:
 *  - the reveal is controller-owned and display-only — never on `GameState`,
 *    never in a save, so the balance harness cannot see it;
 *  - stages advance on the wall clock the caller passes, and are fixed steps
 *    (no interpolation, no `Math.random`);
 *  - ENTER is never blocked: reduced motion pins the final stage, and leaving
 *    the screen cancels mid-stage;
 *  - rule 7 (redundant colour): the settled state is readable as text.
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import type { Grid } from "../src/core/types";
import { renderLootScreen } from "../src/renderer/ending";
import {
  beginLootCommit,
  beginMatrixArrival,
  commitBar,
  LOOT_COMMIT_MAX_LINES,
  LOOT_COMMIT_STAGES,
  LOOT_COMMIT_STAGE_MS,
  lootCommitLines,
  lootCommitStage,
  matrixArrivalActive,
  matrixArrivalLines,
  MATRIX_ARRIVAL_MS,
  resolveGrowthReveal,
} from "../src/renderer/growth_reveal";
import { suppressMotion } from "../src/renderer/accessibility_modes";

const LAYOUTS: ReadonlyArray<readonly [number, number]> = [
  [80, 50],
  [60, 40],
  [40, 60],
];

function lines(grid: Grid): string[] {
  return grid.cells.map((row) => row.map((cell) => cell.char).join(""));
}

const COMMIT = beginLootCommit("Kraken", "PIERCE 2", 1, 1000);

describe("Growth reveal — commit stages (ADR-0262)", () => {
  it("advances through every fixed stage on the wall clock, then holds", () => {
    const seen = LOOT_COMMIT_STAGE_MS.map((offset) =>
      lootCommitStage(COMMIT, 1000 + offset, false),
    );
    expect(seen).toEqual([0, 1, 2, 3]);
    // Clamps at the settled stage long after the window.
    expect(lootCommitStage(COMMIT, 1000 + 60_000, false)).toBe(
      LOOT_COMMIT_STAGES - 1,
    );
  });

  it("treats a clock before the start as stage 0, never negative", () => {
    expect(lootCommitStage(COMMIT, 0, false)).toBe(0);
  });

  it("reduced motion pins the final, settled stage at once", () => {
    expect(suppressMotion("reveal", true)).toBe(true);
    expect(lootCommitStage(COMMIT, 1000, true)).toBe(LOOT_COMMIT_STAGES - 1);
    expect(lootCommitStage(COMMIT, 0, true)).toBe(LOOT_COMMIT_STAGES - 1);
  });

  it("the commit bar is fixed steps, monospaced, and reaches 100%", () => {
    const bars = [0, 1, 2, 3].map(commitBar);
    expect(bars).toEqual([
      "[..........]   0%",
      "[###.......]  33%",
      "[######....]  66%",
      "[##########] 100%",
    ]);
    for (const bar of bars) expect(bar).toHaveLength(17);
  });
});

describe("Growth reveal — the panel text", () => {
  it("grows into its settled state without ever showing a false promise", () => {
    const early = lootCommitLines(COMMIT, 0, true);
    const settled = lootCommitLines(COMMIT, LOOT_COMMIT_STAGES - 1, true);
    // The program signature is not signed off until the commit begins.
    expect(early.join("\n")).not.toContain("SIGNATURE");
    expect(settled.join("\n")).toContain("PROGRAM SLOT 01");
    expect(settled.join("\n")).toContain("> 1 KRAKEN");
    expect(settled.join("\n")).toContain("SIGNATURE ............ KRAKEN");
    expect(settled.join("\n")).toContain("[##########] 100%");
    expect(settled.join("\n")).toContain("[+] PROGRAM ACQUIRED");
  });

  it("fits the 40-column layout with the compact wording", () => {
    const settled = lootCommitLines(COMMIT, LOOT_COMMIT_STAGES - 1, false);
    for (const line of settled) expect(line.length).toBeLessThanOrEqual(40);
    expect(settled.join("\n")).toContain("SLOT 01");
    expect(settled.join("\n")).toContain("[+] ACQUIRED");
  });

  it("reserves no more rows than LOOT_COMMIT_MAX_LINES claims", () => {
    for (const wide of [true, false]) {
      expect(
        lootCommitLines(COMMIT, LOOT_COMMIT_STAGES - 1, wide).length,
      ).toBeLessThanOrEqual(LOOT_COMMIT_MAX_LINES);
    }
  });

  it("draws the panel inside the frame at every layout", () => {
    for (const [cols, rows] of LAYOUTS) {
      const grid = renderLootScreen(
        63,
        100,
        cols,
        rows,
        4075,
        "",
        false,
        [],
        -1,
        { commit: COMMIT, stage: LOOT_COMMIT_STAGES - 1 },
      );
      const text = lines(grid).join("\n");
      expect(text).toContain("ACQUIRED");
      // One-screen contract: no row is wider than the layout.
      for (const line of lines(grid)) {
        expect(line.length).toBeLessThanOrEqual(cols);
      }
    }
  });
});

describe("Growth reveal — the arrival hand-off", () => {
  it("keeps the note inside its window, then lapses", () => {
    const arrival = beginMatrixArrival("Kraken", 5000, false);
    expect(arrival).not.toBeNull();
    expect(matrixArrivalActive(arrival, 5000)).toBe(true);
    expect(matrixArrivalActive(arrival, 5000 + MATRIX_ARRIVAL_MS - 1)).toBe(
      true,
    );
    expect(matrixArrivalActive(arrival, 5000 + MATRIX_ARRIVAL_MS)).toBe(false);
    expect(matrixArrivalActive(null, 5000)).toBe(false);
  });

  it("reduced motion suppresses the note but the deck still grew (null)", () => {
    expect(beginMatrixArrival("Kraken", 5000, true)).toBeNull();
  });

  it("names the card in short HUD lines that fit the narrowest column", () => {
    const label = matrixArrivalLines({ cardName: "Kraken", startedMs: 0 });
    expect(label).toEqual(["+ PROGRAM", "  KRAKEN"]);
    const long = matrixArrivalLines({
      cardName: "VeryLongProgramName",
      startedMs: 0,
    });
    for (const line of long) expect(line.length).toBeLessThanOrEqual(14);
  });
});

describe("Growth reveal — the frame resolver", () => {
  it("returns null when there is nothing to reveal", () => {
    expect(resolveGrowthReveal(null, null, 0, false)).toBeNull();
  });

  it("carries the commit frame and the arrival lines independently", () => {
    const atCommit = resolveGrowthReveal(COMMIT, null, 1000, false);
    expect(atCommit?.lootCommit?.stage).toBe(0);
    expect(atCommit?.arrivalLines).toBeNull();

    const atArrival = resolveGrowthReveal(
      null,
      { cardName: "Kraken", startedMs: 1000 },
      1000,
      false,
    );
    expect(atArrival?.lootCommit).toBeNull();
    expect(atArrival?.arrivalLines).toEqual(["+ PROGRAM", "  KRAKEN"]);
  });
});

describe("Growth reveal — display-only guarantees (ADR-0251)", () => {
  // Comments name the forbidden things, so scan the code only.
  const source = readFileSync(
    fileURLToPath(new URL("../src/renderer/growth_reveal.ts", import.meta.url)),
    "utf-8",
  )
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/\/\/[^\n]*/g, "")
    .replace(/\s+/g, "");

  it("consumes no gameplay randomness", () => {
    expect(source).not.toContain("Math.random");
  });

  it("never touches GameState or the save — it is controller-owned", () => {
    expect(source).not.toContain("GameState");
    expect(source).not.toContain("stateToSaveSlot");
    expect(source).not.toContain("applyAction");
  });

  it("is not an input lock — the caller's clock drives it, not a queue", () => {
    // No timers, no pending-input bookkeeping at all.
    expect(source).not.toContain("setTimeout");
    expect(source).not.toContain("setInterval");
    expect(source).not.toContain("requestAnimationFrame");
  });
});

describe("Growth reveal — loot screen wiring", () => {
  it("does not draw the offer rows once a commit panel is present", () => {
    const grid = renderLootScreen(
      63,
      100,
      80,
      50,
      4075,
      "",
      false,
      ["1 KRAKEN", "2 INSPIRE", "3 DECRYPT"],
      0,
      { commit: COMMIT, stage: LOOT_COMMIT_STAGES - 1 },
    );
    const text = lines(grid).join("\n");
    expect(text).toContain("PROGRAM SLOT 01");
    // The plain offer list is replaced, not doubled.
    expect(text).not.toContain("NEW PROGRAM");
    expect(text).not.toContain("2 INSPIRE");
  });
});

describe("Growth reveal — controller wiring in main.ts", () => {
  const mainSource = readFileSync(
    fileURLToPath(new URL("../src/main.ts", import.meta.url)),
    "utf-8",
  )
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/\/\/[^\n]*/g, "")
    .replace(/\s+/g, "");

  it("starts the commit from the card-taken transition, after the reducer", () => {
    expect(mainSource).toContain("privatelootCommit:LootCommit|null=null;");
    expect(mainSource).toContain(
      "this.state=applyAction(this.state,resolved);",
    );
    expect(mainSource).toContain("this.syncGrowthReveal(previous,this.state);");
  });

  it("hands the arrival over when the run steps back onto the board", () => {
    expect(mainSource).toMatch(
      /previous\.runPhase==="loot"&&next\.runPhase!=="loot"/,
    );
    expect(mainSource).toContain('next.runPhase==="matrix"');
  });

  it("expires the arrival note from the render loop, on the clock", () => {
    expect(mainSource).toContain("matrixArrivalActive(this.matrixArrival,now)");
  });

  it("steps the commit panel from the render loop, then stops", () => {
    // The loot screen draws once per input, so without a clock-driven redraw
    // the panel would freeze on its first stage (found live).
    expect(mainSource).toContain(
      "lootCommitStage(this.lootCommit,now,this.reducedMotion)",
    );
    expect(mainSource).toContain("lootCommitStageShown");
  });
});
