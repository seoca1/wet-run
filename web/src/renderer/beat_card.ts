/** A beat card (ADR-0317 3b) — a spoken beat that owns the screen until a key.
 *
 * The run's opening beat (ADR-0272) proved the shape: a full-screen card is
 * roomy at every layout and cannot push a key hint off a panel the way an
 * inline line on the encounter screen did. Beats that would not fit inline get
 * a card, and the player dismisses it with the same key they were going to
 * press anyway.
 *
 * Display-only. The lines live in `event_beats.ts`, never in `GameState`, so
 * nothing is saved and a resumed run does not replay a card it already read.
 */
import type { DialogueBeat } from "../core/state/event_beats";
import { makeGrid, setText } from "../core/grid";
import type { Grid } from "../core/types";
import { PALETTE } from "./palette";
import { runIntroWidth, wrapIntroLines } from "./run_intro";

/** The beat card: a title, the voice, and one exit line. */
export function renderBeatCard(
  title: string,
  beat: DialogueBeat,
  cols: number,
  rows: number,
): Grid {
  let grid = makeGrid(cols, rows);
  const width = runIntroWidth(cols);
  const centre = (text: string): number => Math.max(2, Math.floor((cols - text.length) / 2));
  const body = wrapIntroLines(beat.lines, width);
  const speaker = beat.speaker.length > 0 ? 1 : 0;
  const total = 1 + speaker + body.length;
  let y = Math.max(3, Math.floor(rows / 2) - Math.floor(total / 2));

  grid = setText(grid, centre(title), y, title, PALETTE.YELLOW_AMBER);
  y += 2;
  if (beat.speaker.length > 0) {
    grid = setText(grid, centre(beat.speaker), y, beat.speaker, PALETTE.YELLOW_AMBER);
    y += 1;
  }
  for (const line of body) {
    grid = setText(grid, centre(line), y, line, PALETTE.CYAN_LIGHT);
    y += 1;
  }

  grid = setText(grid, centre("PRESS ANY KEY"), rows - 3, "PRESS ANY KEY", PALETTE.GRAY_DARK);
  return grid;
}
