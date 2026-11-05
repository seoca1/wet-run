/** ADR-0252: when the autosave is written, and when a run is over.
 *
 * Pure decisions; `main.ts` performs the storage side effects.
 */
import type { GameState } from "../types";

/** A node whose win ends the mission (the `applyLootAction` rule): no
 * matrix, an unknown node, a dead end, or the boss.
 *
 * ADR-0279: this is the single gate for "pay the mission reward". A terminal
 * win (boss or dead-end) pays `mission.rewards.credits` once, on top of the
 * node reward; a non-terminal win pays only the node reward. The four cases:
 *   - no matrix (run already over)        → terminal
 *   - unknown node index                   → terminal (defensive)
 *   - node with no adjacent nodes (dead end) → terminal
 *   - boss node (node.isBoss)              → terminal
 * Every other node is a mid-mission encounter → non-terminal. */
export function isTerminalNode(state: GameState): boolean {
  const node = state.matrix?.nodes[state.currentNodeIndex];
  return !state.matrix || !node || node.adjacent.length === 0 || node.isBoss;
}

/** What the controller does with slot 0 for a rendered state.
 *
 * Every live run frame is written — Matrix moves and the loot screen
 * included — so a reload resumes the committed state, never the last combat
 * frame.
 *
 * Once the run is over the slot is retired: a finished run cannot be resumed.
 * That is both the ending *and* a death (ADR-0264). A dead frame is not a
 * resumable frame: the slot carries no `runPhase`, so `slotToGameState`
 * rebuilds any save as `runPhase: "matrix"` — resuming a death restored a
 * board with 0 HP after a flatline, and resurrected a jacked-out runner at
 * full health. Retiring on death closes both. */
export function autosaveIntent(
  state: GameState | null,
): "write" | "retire" | "skip" {
  if (state === null) return "skip";
  return state.runPhase === "ending" || state.runPhase === "dead"
    ? "retire"
    : "write";
}

/** Confirm (or ESC) on the ending screen: the run is complete and the
 * controller returns to the title with the run state cleared. */
export function runCompleted(previous: GameState, next: GameState): boolean {
  return (
    previous.runPhase === "ending" &&
    previous.phase !== "menu" &&
    next.runPhase === "ending" &&
    next.phase === "menu"
  );
}

/**
 * Confirm (or ESC) on the defeat screen: the flatline ends the run and the
 * controller returns to the title with the run state cleared.
 *
 * Mirrors `runCompleted`, and exists because the defeat screen used to accept
 * no input at all — `FLATLINE` parked the player on a screen with no exit and
 * nothing to press. (The richer ADR-0040 death cycle — same jockey / new
 * jockey — stays a later slice.)
 */
export function runFailed(previous: GameState, next: GameState): boolean {
  return (
    previous.runPhase === "dead" &&
    previous.phase !== "menu" &&
    next.runPhase === "dead" &&
    next.phase === "menu"
  );
}

/** Title-screen status line after a completed run (CONTINUE is then empty). */
export const RUN_COMPLETE_MESSAGE = "Run complete. Autosave cleared.";

/** Title-screen status line after a flatline.
 *
 * Live observation (ADR-0263): a death does *not* leave a resumable slot —
 * after a jack-out death the title showed `CONTINUE (no save)` and
 * `hasSaveCache` was false, even though `autosaveIntent` answers `"write"`
 * for a dead frame. Whether the write lands is an open question, not a claim
 * made here. */
export const FLATLINE_MESSAGE = "Flatline — back at the title.";
