/** Choose the jockey the run belongs to (ADR-0274).
 *
 * The graphic-novel prologue is one story per jockey. It used to hand over to
 * mission select and the run began anonymous, so the story just read left no
 * trace. This is the handover: pick the jockey, then the mission, then play —
 * and the run names its runner in the intro and in the ending summary.
 *
 * ADR-0315: the choice changes the starting deck (ADR-0276), so the screen says
 * what each jockey brings. Tagline and deck wrap; the old one-line slice cut
 * them mid-word at 40 columns.
 */
import { makeGrid, setText, type Grid } from "../core/grid";
import { JOCKEYS } from "../core/state/jockey";
import { startingDeckIds } from "../core/state/starting_deck";
import { PALETTE } from "./palette";

/** Word-wrap to `width`, at most `maxLines` lines (last line may end short). */
function wrap(text: string, width: number, maxLines: number): string[] {
  const words = text.split(" ");
  const lines: string[] = [];
  let current = "";
  for (const word of words) {
    const next = current === "" ? word : `${current} ${word}`;
    if (next.length > width && current !== "") {
      lines.push(current);
      current = word;
      if (lines.length === maxLines) return lines;
    } else {
      current = next;
    }
  }
  if (current !== "") lines.push(current);
  return lines.slice(0, maxLines);
}

export function renderJockeySelect(selected: number, cols: number, rows: number): Grid {
  let grid = makeGrid(cols, rows);
  const title = "WHO IS JACKING IN";
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - title.length) / 2)),
    Math.max(2, Math.floor(rows / 2) - 6),
    title,
    PALETTE.GREEN_NEON,
  );

  let y = Math.floor(rows / 2) - 3;
  // ADR-0315: the jockey changes the starting deck (ADR-0276), so the screen
  // says who they are AND what they bring. Wrapped, never truncated — at 40
  // columns the old one-line slice cut the tagline mid-word.
  const textWidth = Math.max(16, cols - 10);
  JOCKEYS.forEach((jockey, i) => {
    const isSelected = i === selected;
    const row = `${i + 1} ${jockey.handle}`;
    grid = setText(
      grid,
      Math.max(2, Math.floor((cols - 24) / 2)),
      y,
      `${isSelected ? ">" : " "} ${row}`,
      isSelected ? PALETTE.GREEN_NEON : PALETTE.GRAY_MID,
    );
    const x = Math.max(2, Math.floor((cols - textWidth) / 2));
    for (const line of wrap(jockey.tagline, textWidth, 2)) {
      y += 1;
      grid = setText(grid, x, y, line, isSelected ? PALETTE.GRAY_LIGHT : PALETTE.GRAY_DARK);
    }
    y += 1;
    const deck = `deck: ${startingDeckIds(jockey.id).join(" ")}`;
    for (const line of wrap(deck, textWidth, 2)) {
      grid = setText(grid, x, y, line, PALETTE.CYAN_LIGHT);
      y += 1;
    }
    y += 1;
  });

  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 30) / 2)),
    rows - 3,
    "↑↓: pick | ENTER: jack in",
    PALETTE.GRAY_DARK,
  );
  return grid;
}
