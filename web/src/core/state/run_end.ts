/** ADR-0252: when the autosave is written, and when a run is over.
 *
 * Pure decisions; `main.ts` performs the storage side effects.
 */
import type { GameState } from "../types";

/** A node whose win ends the mission (the `applyLootAction` rule): no
 * matrix, an unknown node, a dead end, or the boss. */
export function isTerminalNode(state: GameState): boolean {
  const node = state.matrix?.nodes[state.currentNodeIndex];
  return !state.matrix || !node || node.adjacent.length === 0 || node.isBoss;
}

/** What the controller does with slot 0 for a rendered state.
 *
 * Every run frame is written — Matrix moves and the loot screen included —
 * so a reload resumes the committed state, never the last combat frame.
 * Once the run reaches its ending the slot is retired: a finished mission
 * cannot be resumed. */
export function autosaveIntent(
  state: GameState | null,
): "write" | "retire" | "skip" {
  if (state === null) return "skip";
  return state.runPhase === "ending" ? "retire" : "write";
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

/** Title-screen status line after a completed run (CONTINUE is then empty). */
export const RUN_COMPLETE_MESSAGE = "Run complete. Autosave cleared.";
