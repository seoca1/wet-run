/** Growth reveal (ADR-0262) — the presentation of a card joining the deck.
 *
 * Two display-only beats, both controller-owned and transient like
 * `MatrixTravel`: nothing here touches `GameState`, a save, the reducer or
 * the balance harness. No `Math.random`, no wall-clock inside the reducer —
 * the caller passes the clock in.
 *
 *   loot commit    the terminal force-commits the program: a slot, a data
 *                  link, a signature, a commit bar. Stages advance on the
 *                  clock but the screen never blocks input.
 *   matrix arrival the card is named once the runner is back on the board,
 *                  so the growth does not vanish with the loot screen.
 *
 * ADR-0251 forbids input locks and animation queues, so ENTER is always
 * live: leaving the screen cancels the reveal mid-stage.
 * ADR-0236/rule 7: reduced motion drops the stage animation but keeps the
 * final wording.
 */
import type { Grid } from "../core/types";
import { setText } from "../core/grid";
import { PALETTE } from "./palette";
import type { PanelRect } from "./panel";
import { suppressMotion } from "./accessibility_modes";

/** Wall-clock offsets at which each commit stage becomes visible. */
export const LOOT_COMMIT_STAGE_MS: readonly number[] = [0, 90, 220, 320];
/** Stage count — the last stage is the settled, "committed" state. */
export const LOOT_COMMIT_STAGES = LOOT_COMMIT_STAGE_MS.length;
/** How long the matrix arrival note stays up. */
export const MATRIX_ARRIVAL_MS = 1200;

/** A commit reveal in progress. Controller-owned and transient. */
export interface LootCommit {
  readonly cardName: string;
  readonly effectTag: string;
  /** 1-based slot the card was taken from, for `PROGRAM SLOT NN`. */
  readonly slot: number;
  readonly startedMs: number;
}

/** The card being announced as the runner returns to the board. */
export interface MatrixArrival {
  readonly cardName: string;
  readonly startedMs: number;
}

/** A commit reveal resolved for one frame — the same shape of hand-off as
 * `MatrixTravelFrame`: the caller passes the clock, the renderer stays pure. */
export interface LootCommitFrame {
  readonly commit: LootCommit;
  readonly stage: number;
}

/** Resolve the frame to draw, or null when there is no reveal. */
export function lootCommitFrame(
  commit: LootCommit | null,
  nowMs: number,
  reducedMotion: boolean,
): LootCommitFrame | null {
  if (commit === null) return null;
  return { commit, stage: lootCommitStage(commit, nowMs, reducedMotion) };
}

/** The reveal handed to the run-screen renderer (all display-only). */
export interface GrowthReveal {
  readonly lootCommit: LootCommitFrame | null;
  /** HUD lines naming the carried card, or null outside the arrival window. */
  readonly arrivalLines: readonly string[] | null;
}

/** Build the reveal for one frame from the controller's transient state. */
export function resolveGrowthReveal(
  commit: LootCommit | null,
  arrival: MatrixArrival | null,
  nowMs: number,
  reducedMotion: boolean,
): GrowthReveal | null {
  const lootCommit = lootCommitFrame(commit, nowMs, reducedMotion);
  const arrivalLines = matrixArrivalActive(arrival, nowMs)
    ? matrixArrivalLines(arrival as MatrixArrival)
    : null;
  if (lootCommit === null && arrivalLines === null) return null;
  return { lootCommit, arrivalLines };
}

/** Begin a commit reveal. Never null: reduced motion is handled in
 * `lootCommitStage`, which pins the final stage rather than hiding the panel. */
export function beginLootCommit(
  cardName: string,
  effectTag: string,
  slot: number,
  nowMs: number,
): LootCommit {
  return { cardName, effectTag, slot, startedMs: nowMs };
}

/** The stage to draw, clamped to the last one. Reduced motion pins it there. */
export function lootCommitStage(
  commit: LootCommit,
  nowMs: number,
  reducedMotion: boolean,
): number {
  const last = LOOT_COMMIT_STAGES - 1;
  if (suppressMotion("reveal", reducedMotion)) return last;
  const elapsed = Math.max(0, nowMs - commit.startedMs);
  let stage = 0;
  for (let i = 0; i < LOOT_COMMIT_STAGE_MS.length; i += 1) {
    if (elapsed >= (LOOT_COMMIT_STAGE_MS[i] ?? 0)) stage = i;
  }
  return Math.min(stage, last);
}

/** The commit bar for a stage, e.g. `[######....] 66%`. Fixed steps only —
 * no interpolation, so the frames are identical on every machine. */
export function commitBar(stage: number): string {
  const pct = [0, 33, 66, 100][stage] ?? 100;
  const filled = [0, 3, 6, 10][stage] ?? 10;
  return `[${"#".repeat(filled)}${".".repeat(10 - filled)}] ${String(pct).padStart(3)}%`;
}

/** The panel as text lines. `wide` uses the full wording; the compact form
 * fits the 40-column layout. Only lines the stage has reached are included,
 * so the panel grows into its settled state. */
export function lootCommitLines(
  commit: LootCommit,
  stage: number,
  wide: boolean,
): readonly string[] {
  const slot = String(commit.slot).padStart(2, "0");
  const name = commit.cardName.toUpperCase();
  const tag = commit.effectTag ? `  [${commit.effectTag}]` : "";
  const link = wide ? "DATA LINK ............ OPEN" : "LINK OPEN";
  const linkShown = stage >= 0;
  const sig = wide ? `SIGNATURE ............ ${name}` : `SIG ${name}`;
  const commitLine = wide
    ? `DECK COMMIT ......... ${commitBar(stage)}`
    : `COMMIT ${commitBar(stage)}`;
  const acquired = wide ? "[+] PROGRAM ACQUIRED" : "[+] ACQUIRED";

  const lines: string[] = [];
  if (wide) {
    lines.push(`PROGRAM SLOT ${slot}`);
    lines.push(`> ${commit.slot} ${name}${tag}`);
    if (linkShown) lines.push(link);
    if (stage >= 1) lines.push(sig);
    if (stage >= 1) lines.push(commitLine);
    if (stage >= LOOT_COMMIT_STAGES - 1) lines.push(acquired);
  } else {
    lines.push(`SLOT ${slot} / ${name}${tag}`);
    if (linkShown) lines.push(link);
    if (stage >= 1) lines.push(sig);
    if (stage >= 1) lines.push(commitLine);
    if (stage >= LOOT_COMMIT_STAGES - 1) lines.push(acquired);
  }
  return lines;
}

/** Lines the panel can occupy — the layout must clear this many rows. */
export const LOOT_COMMIT_MAX_LINES = 6;

/** Draw the panel centred at one left margin inside `inner`. */
export function drawLootCommit(
  grid: Grid,
  inner: PanelRect,
  commit: LootCommit,
  stage: number,
  firstRow: number,
  wide: boolean,
): Grid {
  const lines = lootCommitLines(commit, stage, wide);
  const widest = lines.reduce((w, l) => Math.max(w, l.length), 0);
  const x = Math.max(
    inner.x + 1,
    inner.x + Math.floor((inner.width - widest) / 2),
  );
  let out = grid;
  lines.forEach((line, i) => {
    const last = i === lines.length - 1;
    // The final line is the confirmation, so it reads as the settled state.
    const colour = last
      ? PALETTE.GREEN_NEON
      : i === 0
        ? PALETTE.YELLOW_AMBER
        : PALETTE.CYAN_LIGHT;
    out = setText(out, x, firstRow + i, line, colour);
  });
  return out;
}

/** Begin the arrival note. Null when reduced motion suppresses it — the
 * growth is still recorded (the deck grew); only the note is motion. */
export function beginMatrixArrival(
  cardName: string,
  nowMs: number,
  reducedMotion: boolean,
): MatrixArrival | null {
  if (suppressMotion("reveal", reducedMotion)) return null;
  return { cardName, startedMs: nowMs };
}

/** Whether the arrival note is still within its window. */
export function matrixArrivalActive(
  arrival: MatrixArrival | null,
  nowMs: number,
): boolean {
  if (arrival === null) return false;
  return nowMs - arrival.startedMs < MATRIX_ARRIVAL_MS;
}

/** The HUD lines naming the card the runner is carrying. Kept short so they
 * fit the narrowest HUD panel (40x60 -> 15 usable columns). */
export function matrixArrivalLines(arrival: MatrixArrival): readonly string[] {
  const name = arrival.cardName.toUpperCase().slice(0, 12);
  return ["+ PROGRAM", `  ${name}`];
}
