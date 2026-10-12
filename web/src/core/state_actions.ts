/** State action handlers — barrel re-export (split per ADR-0110).
 *
 * The handlers were split into focused modules to keep each under the
 * 100-300 LOC module-size policy (Game/wet_run/AGENTS.md §6):
 * - `state_actions_phases.ts`   — non-combat phase handlers (matrix, loot,
 *                                 death, ending, menu, approach, end)
 * - `state_actions_combat.ts`   — combat tick (applyCombatAction, enemy turns,
 *                                 targeting, hand draw, Dixie companion)
 * - `state_actions_programs.ts` — program resolution (useProgram) + helpers
 *                                 (internal; imported directly by the combat
 *                                 module, not re-exported here so the public
 *                                 API surface is unchanged)
 *
 * This file preserves the original import path so existing imports keep
 * working unchanged.
 */

export * from "./state_actions_phases.ts";
export * from "./state_actions_combat.ts";
