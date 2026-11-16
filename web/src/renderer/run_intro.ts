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
import type { DialogueBeat } from "../core/state/event_beats";
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

/** The intro card: title in amber, body in grey, a single exit line.
 *
 * ADR-0317 (3b): `beat` is the companion's voice, spoken once the arc's framing
 * lines have set the scene — the run's opening, not a menu mode. It is optional
 * so the card still renders without it (CONTINUE never replays it).
 */
export function renderRunIntro(
  arc: ArcId,
  cols: number,
  rows: number,
  jockey: string | null = null,
  beat: DialogueBeat | null = null,
): Grid {
  let grid = makeGrid(cols, rows);
  const width = runIntroWidth(cols);
  const centre = (text: string): number =>
    Math.max(2, Math.floor((cols - text.length) / 2));
  const [title = "", ...body] = RUN_INTRO[arc] ?? RUN_INTRO[1];
  const wrapped = wrapIntroLines(body, width);
  const beatLines = beat === null ? [] : wrapIntroLines(beat.lines, width);
  // A blank separator, the speaker's name when the beat has one voice, then
  // the lines.
  const beatBlock =
    beat === null ? 0 : (beat.speaker.length > 0 ? 1 : 0) + 1 + beatLines.length;
  const total = 1 + wrapped.length + (jockey === null ? 0 : 1) + beatBlock;
  let y = Math.max(3, Math.floor(rows / 2) - Math.floor(total / 2));

  grid = setText(grid, centre(title), y, title, PALETTE.YELLOW_AMBER);
  if (jockey !== null) {
    // ADR-0274: the runner is somebody. The prologue chose them; the run says so.
    const who = `${jockey} JACKS IN`;
    grid = setText(grid, centre(who), y + 1, who, PALETTE.CYAN_LIGHT);
  }
  y += 2;
  for (const line of wrapped) {
    grid = setText(grid, centre(line), y, line, PALETTE.GRAY_LIGHT);
    y += 1;
  }
  if (beat !== null) {
    y += 1; // the voice gets air between it and the framing lines.
    if (beat.speaker.length > 0) {
      grid = setText(
        grid,
        centre(beat.speaker),
        y,
        beat.speaker,
        PALETTE.YELLOW_AMBER,
      );
      y += 1;
    }
    for (const line of beatLines) {
      grid = setText(grid, centre(line), y, line, PALETTE.CYAN_LIGHT);
      y += 1;
    }
  }

  grid = setText(grid, centre("PRESS ANY KEY"), rows - 3, "PRESS ANY KEY", PALETTE.GRAY_DARK);
  return grid;
}
