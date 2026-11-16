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

  // ADR-0317 (3b): the companion speaks on the opening card.
  it("speaks the companion's beat, speaker and lines", () => {
    const beat = {
      speaker: "Dixie Flatline",
      lines: ["Hey. Hey cowboy. You hear me?", "I'm in your deck."],
    };
    const joined = text(renderRunIntro(1, 80, 50, "CASE", beat)).join("\n");
    expect(joined).toContain("FIRST JACK");
    expect(joined).toContain("Dixie Flatline");
    expect(joined).toContain("Hey cowboy");
    expect(joined).toContain("I'm in your deck");
  });

  it("still renders without a beat (CONTINUE never replays it)", () => {
    const joined = text(renderRunIntro(1, 80, 50, "CASE", null)).join("\n");
    expect(joined).toContain("FIRST JACK");
    expect(joined).not.toContain("Dixie");
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
    const beat = {
      speaker: "Dixie Flatline",
      lines: [
        "Hey. Hey cowboy. You hear me?",
        "I'm in your deck. Construct. Don't ask how. I don't know either.",
        "I'm your backup. The Finn hired me before he hired you.",
      ],
    };
    for (const [cols, rows] of [
      [80, 50],
      [60, 40],
      [40, 60],
    ] as const) {
      for (const arc of ARCS) {
        for (const b of [null, beat]) {
          const grid = renderRunIntro(arc, cols, rows, "CASE", b);
          for (const row of text(grid)) {
            expect([...row].length).toBeLessThanOrEqual(cols);
          }
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
      "if(this.runIntroArc!==null){this.runIntroArc=null;this.runIntroBeat=null;",
    );
    expect(main).toContain(
      "renderRunIntro(this.runIntroArc,this.layout.cols,this.layout.rows,jockeyHandle(this.state?.jockeyId),this.runIntroBeat,)",
    );
  });
});
