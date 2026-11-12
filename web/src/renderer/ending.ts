/** Ending screen + Loot screen renderers (Tier 5).
 *
 * - renderEndingScreen: shows ending letter + flavor text (29 in Python, 3 MVP)
 * - renderLootScreen: shows HEAL applied + reward credits between combats
 */
import type { EndingChoice, Grid } from "../core/types";
import { makeGrid, setText } from "../core/grid";
import { PALETTE } from "./palette";
import {
  drawLootCommit,
  LOOT_COMMIT_MAX_LINES,
  type LootCommitFrame,
} from "./growth_reveal";
import { ENDINGS } from "../core/combat/ending_resolver";

/** What the run cost and what it earned, shown under the ending letter.
 * Display-only: the values are the run's own final numbers, not a claim about
 * the ending (ADR-0269). */
export interface EndingSummary {
  readonly mission: string;
  /** ADR-0274 — whose run this was, when the run knows. */
  readonly jockey?: string | null;
  readonly hp: number;
  readonly maxHp: number;
  readonly credits: number;
  readonly turns: number;
}

export function renderEndingScreen(
  choice: EndingChoice | null,
  cols: number,
  rows: number,
  summary: EndingSummary | null = null,
): Grid {
  let grid = makeGrid(cols, rows);
  const c = choice ?? "arc1_wage_slave";
  const ending = ENDINGS.find((e) => e.id === c);

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

  // The run's own numbers, two lines above the footer. The ending text is a
  // verdict; without this the screen never says what the run actually was --
  // which mission, at what cost, for what. Kept to two lines that fit 40
  // columns (the narrowest layout) and truncated rather than wrapped.
  if (summary !== null) {
    const width = Math.max(8, cols - 4);
    const who = summary.jockey ?? null;
    const mission = (
      who === null ? summary.mission : `${who} — ${summary.mission}`
    ).slice(0, width);
    const stats =
      `HP ${summary.hp}/${summary.maxHp} · ` +
      `${summary.credits.toLocaleString()}cr · ` +
      `${summary.turns} turns`;
    const statLine = stats.length > width ? stats.slice(0, width) : stats;
    [mission, statLine].forEach((line, i) => {
      grid = setText(
        grid,
        Math.max(2, Math.floor((cols - line.length) / 2)),
        rows - 5 + i,
        line,
        PALETTE.GRAY_MID,
      );
    });
  }

  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 28) / 2)),
    rows - 2,
    "ENTER / ESC: return to title",
    PALETTE.GRAY_DARK,
  );
  return grid;
}

/** Render loot screen between combats (HEAL + reward credits + items). */
export function renderLootScreen(
  hp: number,
  maxHp: number,
  cols: number,
  rows: number,
  rewardCredits: number = 0,
  lootMessage: string = "",
  terminal: boolean = false,
  offers: readonly string[] = [],
  takenIndex: number = -1,
  commitFrame: LootCommitFrame | null = null,
  /** ADR-0299: the caller knows which exits actually exist, so it owns the
   * footer's wording. Without this the panel kept promising slots 1-5 while the
   * screen offered 1-8 — a false affordance under ADR-0251 rule 5. */
  hint: string | null = null,
  /** ADR-0311: the same panel carries the free unique pick before the stop. */
  mode: "loot" | "unique" = "loot",
): Grid {
  let grid = makeGrid(cols, rows);

  // Title
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 12) / 2)),
    Math.floor(rows / 2) - 4,
    mode === "unique" ? "UNIQUE PROGRAM" : "DATA SALVAGE",
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

  // Credits awarded
  if (rewardCredits > 0) {
    const creditsLine = `+${rewardCredits.toLocaleString()} credits`;
    grid = setText(
      grid,
      Math.max(2, Math.floor((cols - creditsLine.length) / 2)),
      Math.floor(rows / 2) + 1,
      creditsLine,
      PALETTE.CYAN_LIGHT,
    );
  }

  // Items dropped (raw loot message, e.g. "Loot: ice_shard x1, data_fragment x1")
  if (lootMessage) {
    grid = setText(
      grid,
      Math.max(2, Math.floor((cols - lootMessage.length) / 2)),
      Math.floor(rows / 2) + 3,
      lootMessage,
      lootMessage.startsWith("Loot: ")
        ? PALETTE.YELLOW_AMBER
        : PALETTE.GRAY_LIGHT,
    );
  }

  // ADR-0262: once a card is taken the terminal commit panel takes the
  // offer's rows — the acquisition as a settled event, not a colour change.
  if (commitFrame !== null) {
    grid = drawLootCommit(
      grid,
      { x: 0, y: 0, width: cols, height: rows },
      commitFrame.commit,
      commitFrame.stage,
      Math.floor(rows / 2) + 5,
      cols >= 60,
    );
  } else if (offers.length > 0) {
    grid = setText(
      grid,
      Math.max(2, Math.floor((cols - 12) / 2)),
      Math.floor(rows / 2) + 5,
      mode === "unique" ? "CHOOSE ONE" : "NEW PROGRAM",
      PALETTE.YELLOW_AMBER,
    );
    // Left-align the block under one margin so the slot digits line up.
    const widest = offers.reduce((w, l) => Math.max(w, l.length), 0);
    const offerX = Math.max(2, Math.floor((cols - widest) / 2));
    offers.forEach((line, i) => {
      // ADR-0261: the card the player took stands out; once one is taken the
      // rest are spent, so they fade back.
      const isTaken = i === takenIndex;
      const color =
        takenIndex < 0
          ? PALETTE.CYAN_LIGHT
          : isTaken
            ? PALETTE.GREEN_NEON
            : PALETTE.GRAY_DARK;
      grid = setText(grid, offerX, Math.floor(rows / 2) + 6 + i, line, color);
    });
  }

  // ADR-0282: there is no automatic heal any more — slot 4 is the repair, and
  // ENTER takes nothing. The old line promised a heal on confirm, which would
  // now be a lie (ADR-0251 rule 5).
  const healed = hp;
  const reserved =
    commitFrame !== null
      ? LOOT_COMMIT_MAX_LINES + 1
      : offers.length > 0
        ? offers.length + 3
        : 0;
  const healRow = Math.floor(rows / 2) + 5 + reserved;
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 22) / 2)),
    healRow,
    terminal
      ? "NO OPTIONS — this was the last node"
      : mode === "unique"
        ? "ENTER: take nothing"
        : takenIndex >= 0
          ? `ENTER → ${healed}/${maxHp}`
          : "ENTER: take nothing",
    PALETTE.GRAY_DARK,
  );

  // Footer
  const footer = terminal
    ? "ENTER: run ends"
    : takenIndex >= 0
      ? "ENTER: continue"
      : offers.length > 0
        ? (hint ??
          (mode === "unique"
            ? "1-3: unique | ENTER: skip"
            : "1-3: card | 4: repair | 5: intel"))
        : "ENTER: route selection";
  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - footer.length) / 2)),
    rows - 2,
    footer,
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
