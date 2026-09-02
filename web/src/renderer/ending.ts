/** Ending screen + Loot screen renderers (Tier 5).
 *
 * - renderEndingScreen: shows ending letter + flavor text (29 in Python, 3 MVP)
 * - renderLootScreen: shows HEAL applied + reward credits between combats
 */
import type { EndingChoice, Grid } from "../core/types.ts";
import { makeGrid, setText } from "../core/grid.ts";
import { PALETTE } from "./palette.ts";
import { ENDINGS } from "../core/ending_resolver.ts";

export function renderEndingScreen(
  choice: EndingChoice | null,
  cols: number,
  rows: number,
): Grid {
  let grid = makeGrid(cols, rows);
  const c = choice ?? "arc1_wage_slave";
  const ending = ENDINGS.find(e => e.id === c);
  
  if (!ending) {
    grid = setText(
      grid,
      Math.max(2, Math.floor((cols - 12) / 2)),
      Math.floor(rows / 2),
      "UNKNOWN ENDING",
      PALETTE.RED_BRIGHT,
    );
    return grid;
  }

  const title = ending.nameEn.toUpperCase();
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - title.length) / 2)),
    Math.floor(rows / 2) - 4,
    title,
    PALETTE.GREEN_NEON,
  );

  const wrapWidth = Math.min(cols - 8, 60);
  const bodyLines = wrapText(ending.descriptionEn, wrapWidth);
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

  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 28) / 2)),
    rows - 2,
    "ENTER: continue | ESC: back",
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
    "ENTER: next node | ESC: back",
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