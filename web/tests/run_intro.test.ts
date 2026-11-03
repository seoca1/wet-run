/** ADR-0272 — a run opens on its arc's framing beat.
 *
 * The graphic-novel prologue is a separate mode and never touches a run, so a
 * run used to begin with no framing at all and only speak again at the ending.
 * `story_skeleton.md` names the missing beat for Arc 1 ("First Jack"), so this
 * is that beat per arc: display-only, dismissed by any key, never saved.
 */
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import {
  RUN_INTRO,
  renderRunIntro,
  runIntroWidth,
  wrapIntroLines,
} from "../src/renderer/run_intro";
import type { ArcId } from "../src/core/combat/ending_resolver";

const ARCS: readonly ArcId[] = [1, 2, 3, 4, 5];

const text = (grid: ReturnType<typeof renderRunIntro>) =>
  grid.cells.map((row) => row.map((c) => c.char).join(""));

describe("ADR-0272 — run intro", () => {
  it("has a beat for every arc", () => {
    for (const arc of ARCS) {
      expect(RUN_INTRO[arc].length).toBeGreaterThanOrEqual(2);
      expect(RUN_INTRO[arc][0]?.length).toBeGreaterThan(0);
    }
  });

  it("shows the title, the body and one exit line", () => {
    const lines = text(renderRunIntro(1, 80, 50));
    expect(lines.join("\n")).toContain("FIRST JACK");
    expect(lines.join("\n")).toContain("PRESS ANY KEY");
  });

  it("fits the 40-column layout after wrapping", () => {
    for (const arc of ARCS) {
      const width = runIntroWidth(40);
      expect(width).toBeLessThanOrEqual(32);
      const [, ...body] = RUN_INTRO[arc];
      for (const line of wrapIntroLines(body, width)) {
        expect(line.length).toBeLessThanOrEqual(width);
      }
      const grid = renderRunIntro(arc, 40, 60);
      for (const row of text(grid)) expect(row.length).toBeLessThanOrEqual(40);
    }
  });

  it("never spills a line past the grid at any layout", () => {
    for (const [cols, rows] of [
      [80, 50],
      [60, 40],
      [40, 60],
    ] as const) {
      for (const arc of ARCS) {
        const grid = renderRunIntro(arc, cols, rows);
        for (const row of text(grid)) {
          expect([...row].length).toBeLessThanOrEqual(cols);
        }
      }
    }
  });

  it("is shown once at run start and dismissed by the first key (source wiring)", () => {
    const main = readFileSync(
      fileURLToPath(new URL("../src/main.ts", import.meta.url)),
      "utf-8",
    ).replace(/\s+/g, "");
    // Set only in launchSelected (a fresh run), never in handleContinue.
    expect(main).toContain(
      "this.runIntroArc=((mission.arcasArcId)||1)asArcId;",
    );
    expect(main).toContain(
      "if(this.runIntroArc!==null){this.runIntroArc=null;",
    );
    expect(main).toContain(
      "renderRunIntro(this.runIntroArc,this.layout.cols,this.layout.rows,jockeyHandle(this.state?.jockeyId),)",
    );
  });
});
