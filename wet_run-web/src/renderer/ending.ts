/** Ending screen + Loot screen renderers (Tier 5).
 *
 * - renderEndingScreen: shows ending letter + flavor text (29 in Python, 3 MVP)
 * - renderLootScreen: shows HEAL applied + reward credits between combats
 */
import type { EndingChoice, Grid } from "../core/types.ts";
import { makeGrid, setText } from "../core/grid.ts";
import { PALETTE } from "./palette.ts";

const ENDING_TEXT: Readonly<Record<EndingChoice, { title: string; body: string }>> = {
  A: {
    title: "ENDING A — VICTORY",
    body: "You jack out cleanly. The Sprawl swallows your trace.",
  },
  B: {
    title: "ENDING B — BARGAIN",
    body: "You strike a deal in the dark. Some data follows you out.",
  },
  C: {
    title: "ENDING C — FLATLINE",
    body: "Your trace fades to white noise. The construct remembers.",
  },
};

/** Render the ending screen with the chosen ending letter + flavor text. */
export function renderEndingScreen(
  choice: EndingChoice | null,
  cols: number,
  rows: number,
): Grid {
  let grid = makeGrid(cols, rows);
  const c = choice ?? "A";
  const text = ENDING_TEXT[c];

  // Title block (centered)
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - text.title.length) / 2)),
    Math.floor(rows / 2) - 4,
    text.title,
    PALETTE.GREEN_NEON,
  );

  // Body (centered, wrapped at ~60 chars)
  const wrapWidth = Math.min(cols - 8, 60);
  const bodyLines = wrapText(text.body, wrapWidth);
  let y = Math.floor(rows / 2) - 1;
  for (const line of bodyLines) {
    grid = setText(
      grid,
      Math.max(2, Math.floor((cols - line.length) / 2)),
      y,
      line,
      PALETTE.GRAY_LIGHT,
    );
    y += 1;
  }

  // Footer
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 28) / 2)),
    rows - 2,
    "ENTER: continue | ESC: menu",
    PALETTE.GRAY_DARK,
  );
  return grid;
}

/** Render loot screen between combats (HEAL + reward credits). */
export function renderLootScreen(
  hp: number,
  maxHp: number,
  cols: number,
  rows: number,
): Grid {
  let grid = makeGrid(cols, rows);

  // Title
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 12) / 2)),
    Math.floor(rows / 2) - 4,
    "DATA SALVAGE",
    PALETTE.GREEN_NEON,
  );

  // HP status
  const hpLine = `HP ${hp}/${maxHp}`;
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - hpLine.length) / 2)),
    Math.floor(rows / 2) - 1,
    hpLine,
    hp > maxHp / 2 ? PALETTE.GREEN_NEON : PALETTE.RED_BRIGHT,
  );

  // HEAL applied
  const healed = Math.min(maxHp, hp + Math.floor(maxHp * 0.15));
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 22) / 2)),
    Math.floor(rows / 2) + 1,
    `HEAL applied → ${healed}/${maxHp}`,
    PALETTE.YELLOW_AMBER,
  );

  // Footer
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 28) / 2)),
    rows - 2,
    "ENTER: next node | ESC: jack out",
    PALETTE.GRAY_DARK,
  );
  return grid;
}

/** Simple word-wrap for ending text. */
function wrapText(text: string, width: number): string[] {
  const words = text.split(" ");
  const lines: string[] = [];
  let current = "";
  for (const word of words) {
    if ((current + " " + word).trim().length > width) {
      if (current) lines.push(current);
      current = word;
    } else {
      current = (current + " " + word).trim();
    }
  }
  if (current) lines.push(current);
  return lines;
}