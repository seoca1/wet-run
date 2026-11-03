/** Run intro (ADR-0272) — the prologue beat that starts a run.
 *
 * The graphic-novel prologue (27 scenes, three jockeys) is a separate mode and
 * never touches a run, so a run began with no framing at all: mission select,
 * then a board. The story only spoke again at the ending. `story_skeleton.md`
 * already names the missing beat for Arc 1 — "First Jack (vision) — the first
 * jack-in" — so this is that beat, per arc.
 *
 * Display-only. The lines live here, not in `GameState`: nothing is saved, and
 * a resumed run (CONTINUE) does not replay its introduction. The controller
 * shows it once at run start and any key dismisses it.
 */
import type { ArcId } from "../core/combat/ending_resolver";
import { setText } from "../core/grid";
import type { Grid } from "../core/types";
import { makeGrid } from "../core/grid";
import { PALETTE } from "./palette";

/** One framing beat per arc: a title and two or three lines. Kept short so the
 * 40-column layout stays comfortable after wrapping. */
export const RUN_INTRO: Readonly<Record<ArcId, readonly string[]>> = {
  1: [
    "FIRST JACK",
    "The deck is cold in your hands.",
    "The matrix opens like a door somebody paid for, and somebody is already inside.",
  ],
  2: [
    "THE SPRAWL",
    "The city files everything. Tonight it files you.",
    "Keep your name off the record and your hands on the deck.",
  ],
  3: [
    "CORPORATE ICE",
    "Their walls are older than your hands.",
    "They build them to be forgotten, and then they forget nothing.",
  ],
  4: [
    "THE AIS",
    "Something in there is awake, and pretending not to be.",
    "Ask the question carefully. It is listening.",
  ],
  5: [
    "THE CHOICE",
    "One last run. After this the Sprawl decides what you were.",
    "Go.",
  ],
};

/** Keep the right rail free and the text readable at every layout. */
export function runIntroWidth(cols: number): number {
  return Math.max(12, Math.min(56, cols - 8));
}

/** Greedy wrap, same shape as the ending screen's, so long lines fit. */
export function wrapIntroLines(
  lines: readonly string[],
  width: number,
): readonly string[] {
  const out: string[] = [];
  for (const line of lines) {
    let current = "";
    for (const word of line.split(" ")) {
      const next = current.length === 0 ? word : `${current} ${word}`;
      if (next.length > width) {
        if (current.length > 0) out.push(current);
        current = word;
      } else {
        current = next;
      }
    }
    if (current.length > 0) out.push(current);
  }
  return out;
}

/** The intro card: title in amber, body in grey, a single exit line. */
export function renderRunIntro(arc: ArcId, cols: number, rows: number): Grid {
  let grid = makeGrid(cols, rows);
  const width = runIntroWidth(cols);
  const [title = "", ...body] = RUN_INTRO[arc] ?? RUN_INTRO[1];
  const wrapped = wrapIntroLines(body, width);
  const total = 1 + wrapped.length;
  let y = Math.max(3, Math.floor(rows / 2) - Math.floor(total / 2));

  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - title.length) / 2)),
    y,
    title,
    PALETTE.YELLOW_AMBER,
  );
  y += 2;
  for (const line of wrapped) {
    grid = setText(
      grid,
      Math.max(2, Math.floor((cols - line.length) / 2)),
      y,
      line,
      PALETTE.GRAY_LIGHT,
    );
    y += 1;
  }

  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 20) / 2)),
    rows - 3,
    "PRESS ANY KEY",
    PALETTE.GRAY_DARK,
  );
  return grid;
}
