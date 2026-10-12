/** Far Grid entry gate (ADR-0213, Phase 2).
 *
 * The FAR GRID menu entry is gated by a cross-run unlock flag. The flag flips
 * from locked to unlocked the first time the player clears any Arc 1 mission —
 * the canonical "Arc 1 clear" signal that `applyLootAction` already emits when
 * it resolves an ending (see `state_actions.ts:applyLootAction`).
 *
 * Single source of truth: this module owns read/write of the localStorage
 * flag `wetrun_far_grid_unlocked`. All other modules import the helpers here
 * rather than touching localStorage directly. This mirrors the
 * `filterMissionsByUniverse` convention (one pure helper module per concern,
 * frozen data, no UI imports).
 *
 * Persistence model:
 * - Default-fill (NOT versioned save migration). The flag is an additive
 *   localStorage key. Existing saves that lack the key simply see the
 *   default-locked state. This avoids touching the SaveSlot schema.
 *
 * i18n: status message is English-only (ADR-0010, English-first) in Gibson
 * detached tone.
 */
const STORAGE_KEY = "wetrun_far_grid_unlocked";

/** Status message shown when the player tries to enter the locked Far Grid.
 *
 * English, Gibson-detached. No emoji. Matches the tone of existing status
 * messages (`"...coming soon in a future tier"`).
 */
export const FAR_GRID_LOCKED_MESSAGE =
  "Win a Sprawl Arc 1 mission to unlock the Far Grid";

/** Pure helper — read the unlock flag from localStorage.
 *
 * Defaults to `false` (locked) when:
 * - the key is absent (brand-new save)
 * - the stored value is not `"1"` (defensive against corrupted/legacy state)
 * - `localStorage` is unavailable (SSR / non-browser test env)
 *
 * Side-effect-free: never throws, never writes. Safe to call from the
 * draw loop on every frame.
 */
export function isFarGridUnlocked(): boolean {
  if (typeof localStorage === "undefined") return false;
  try {
    return localStorage.getItem(STORAGE_KEY) === "1";
  } catch {
    return false;
  }
}

/** Side-effecting helper — flip the flag to unlocked.
 *
 * Called from `state_actions.ts:applyLootAction` when an Arc 1 mission is
 * cleared. Idempotent: re-setting is a no-op (key already `"1"`). Silently
 * no-ops if `localStorage` is unavailable (defensive).
 *
 * Returns `true` when the flag was newly flipped this call, `false` if it
 * was already unlocked. Useful for tests + the `unlockedAchievements`
 * notification hook (out of scope here).
 */
export function setFarGridUnlocked(): boolean {
  if (typeof localStorage === "undefined") return false;
  try {
    if (localStorage.getItem(STORAGE_KEY) === "1") return false;
    localStorage.setItem(STORAGE_KEY, "1");
    return true;
  } catch {
    return false;
  }
}

/** Reset the unlock flag — test/admin escape hatch. Not wired to any UI.
 *
 * Mirrors `resetTutorial()` in `renderer/tutorial.ts`. Safe to call in
 * non-browser contexts (no-op).
 */
export function resetFarGridUnlocked(): void {
  if (typeof localStorage === "undefined") return;
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore
  }
}

/** Pure helper — derive the FAR GRID entry's `available` field from the flag.
 *
 * Single helper that the menu renderer reads; keeps the unlock predicate in
 * one place. Pure: takes the flag as input, no localStorage access.
 */
export function farGridAvailable(unlocked: boolean): boolean {
  return unlocked;
}