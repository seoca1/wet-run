/** Far Grid entry gate (ADR-0213, Phase 2 + tightening follow-up).
 *
 * Phase 2 initial rule — "any Arc 1 mission clear unlocks the Far Grid" — was
 * too forgiving. The tightening (same ADR, follow-up phase) changes the gate
 * to a *full Arc-1 clear* check: the player must complete EVERY Sprawl
 * Arc-1 mission before the Far Grid entry becomes reachable.
 *
 * Persistence model (mirrors Phase 2 default-fill convention):
 *   - `wetrun_far_grid_unlocked` (legacy `"1"` flag) — set by the OLD Phase 2
 *     rule and preserved for backward compatibility. NEVER re-locked: any save
 *     that flipped the flag stays unlocked even if the completed-mission log
 *     is empty or partial.
 *   - `wetrun_completed_missions` (NEW, JSON array of mission ids) — the
 *     per-mission completion record that drives the new full-clear check.
 *
 * Auto-path: when `applyLootAction` clears a Sprawl Arc-1 mission it
 * (1) records the id via `recordMissionComplete`, then
 * (2) calls `evaluateFarGridUnlock()` which ORs the legacy flag against the
 *     full-clear predicate `isArcOneCleared()` and writes the flag if newly
 *     satisfied. This keeps the existing `setFarGridUnlocked()` API intact
 *     (its tests still apply) and centralizes the rule here, not in callers.
 *
 * Single source of truth: this module owns read/write of both localStorage
 * keys. All other modules import the helpers here rather than touching
 * localStorage directly. Mirrors `filterMissionsByUniverse` convention (one
 * pure helper module per concern, frozen data, no UI imports).
 *
 * Dynamic derivation: the required Sprawl Arc-1 id set comes from
 * `loadMissionsCatalog(missionsData)` — the same validated catalog `main.ts`
 * uses. No hardcoded ids; new Sprawl Arc-1 entries added to the JSON are
 * picked up on next module load.
 *
 * i18n: status message is English-only (ADR-0010, English-first) in Gibson
 * detached tone.
 */
import missionsData from "../data/missions.json";
import { loadMissionsCatalog } from "./data_loaders.ts";
import type { Mission } from "./types.ts";

/** Legacy unlock flag (Phase 2). Preserved for already-unlocked saves. */
const FLAG_STORAGE_KEY = "wetrun_far_grid_unlocked";

/** Per-mission completion record (Phase 2 tightening). JSON array of ids. */
const COMPLETED_STORAGE_KEY = "wetrun_completed_missions";

/** Memoized REQUIRED set derived from the mission catalog.
 *  Frozen so callers cannot mutate it.
 *
 *  Frozen at module load. The catalog is hand-maintained and only re-derives
 *  on hot-reload (dev) / page reload (prod) — never per-frame. Hot-reload is
 *  fine because `applyLootAction` only writes; reads happen on the next page
 *  load.
 */
const ARC_ONE_REQUIRED_IDS: ReadonlyArray<string> = Object.freeze(
  loadMissionsCatalog(missionsData)
    .filter(
      (m: Mission): boolean =>
        m.arc === 1 && (m.source_universe ?? "sprawl") === "sprawl",
    )
    .map((m: Mission): string => m.id)
    .filter((id) => id.length > 0),
);

/** Status message shown when the player tries to enter the locked Far Grid.
 *
 * English, Gibson-detached. No emoji. Updated for the full-clear semantics:
 * "Win a Sprawl Arc 1 mission" → "Clear all Sprawl Arc 1 missions".
 */
export const FAR_GRID_LOCKED_MESSAGE =
  "Clear all Sprawl Arc 1 missions to unlock the Far Grid";

/** Pure helper — read the legacy unlock flag from localStorage.
 *
 * Defaults to `false` (locked) when:
 * - the key is absent (brand-new save)
 * - the stored value is not `"1"` (defensive against corrupted/legacy state)
 * - `localStorage` is unavailable (SSR / non-browser test env)
 *
 * Side-effect-free: never throws, never writes. Safe to call from the
 * draw loop on every frame.
 *
 * NOTE: this only reads the old `"1"` flag. For the new OR-semantics
 * (flag OR full-clear), use `farGridUnlocked()`.
 */
export function isFarGridUnlocked(): boolean {
  if (typeof localStorage === "undefined") return false;
  try {
    return localStorage.getItem(FLAG_STORAGE_KEY) === "1";
  } catch {
    return false;
  }
}

/** Side-effecting helper — flip the legacy flag to unlocked.
 *
 * Called from `state_actions.ts:applyLootAction` via `evaluateFarGridUnlock()`
 * when an Arc 1 mission is cleared. Idempotent: re-setting is a no-op
 * (key already `"1"`). Silently no-ops if `localStorage` is unavailable.
 *
 * Returns `true` when the flag was newly flipped this call, `false` if it
 * was already unlocked. Useful for tests + the `unlockedAchievements`
 * notification hook (out of scope here).
 *
 * Public so existing tests that exercise it directly stay green. New
 * callers should prefer `evaluateFarGridUnlock()` for the OR semantics.
 */
export function setFarGridUnlocked(): boolean {
  if (typeof localStorage === "undefined") return false;
  try {
    if (localStorage.getItem(FLAG_STORAGE_KEY) === "1") return false;
    localStorage.setItem(FLAG_STORAGE_KEY, "1");
    return true;
  } catch {
    return false;
  }
}

/** Reset the legacy unlock flag — test/admin escape hatch. Not wired to any UI.
 *
 * Mirrors `resetTutorial()` in `renderer/tutorial.ts`. Safe to call in
 * non-browser contexts (no-op).
 *
 * Does NOT clear the completed-mission record; call `resetCompletedMissions()`
 * for that. This preserves an already-unlocked save's "unlocked" status
 * when only one is reset (matches the "never re-lock a set flag" invariant).
 */
export function resetFarGridUnlocked(): void {
  if (typeof localStorage === "undefined") return;
  try {
    localStorage.removeItem(FLAG_STORAGE_KEY);
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

/** Pure helper — return the dynamic set of required Sprawl Arc-1 mission ids.
 *
 * Derived from the loaded mission catalog (filter `arc === 1 && source_universe
 * === "sprawl"`). Memoized at module load and frozen. Exposed so tests can
 * pin the derivation against the catalog.
 *
 * Returned array is frozen and never mutated; do not attempt to sort or
 * push to it.
 */
export function arcOneMissionIds(): ReadonlyArray<string> {
  return ARC_ONE_REQUIRED_IDS;
}

/** Pure-ish helper — read the completed-mission record from localStorage.
 *
 * Default-fills to an empty array. Defensive against:
 *   - key absent (brand-new save)
 *   - non-array payload (corrupted/foreign key collision)
 *   - non-JSON payload (legacy/corrupted)
 *   - `localStorage` unavailable (SSR / non-browser test env)
 *
 * Returns a *fresh frozen array* on every call (caller cannot mutate the
 * internal store). Side-effect-free: never throws, never writes.
 */
export function getCompletedMissions(): ReadonlyArray<string> {
  if (typeof localStorage === "undefined") return Object.freeze([]);
  try {
    const raw = localStorage.getItem(COMPLETED_STORAGE_KEY);
    if (raw === null) return Object.freeze([]);
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return Object.freeze([]);
    const ids: string[] = [];
    for (const v of parsed) {
      if (typeof v === "string" && v.length > 0) ids.push(v);
    }
    return Object.freeze(ids);
  } catch {
    return Object.freeze([]);
  }
}

/** Side-effecting helper — record a completed mission id.
 *
 * Called from `state_actions.ts:applyLootAction` on every mission complete,
 * regardless of arc (the helper decides the arc-1 filter inside
 * `evaluateFarGridUnlock`). Idempotent: recording the same id twice is a
 * no-op and returns `false`. Returns `true` when the id was newly added.
 *
 * Silently no-ops if `localStorage` is unavailable (defensive).
 *
 * The underlying store is a JSON-encoded array; on read (`getCompletedMissions`)
 * the helper re-parses and validates. Order is insertion order. Non-string /
 * empty entries are silently dropped on the next read.
 */
export function recordMissionComplete(missionId: string): boolean {
  if (typeof localStorage === "undefined") return false;
  if (typeof missionId !== "string" || missionId.length === 0) return false;
  try {
    const current = getCompletedMissions();
    if (current.includes(missionId)) return false;
    const next = [...current, missionId];
    localStorage.setItem(COMPLETED_STORAGE_KEY, JSON.stringify(next));
    return true;
  } catch {
    return false;
  }
}

/** Pure helper — predicate: has the player cleared every required Sprawl Arc-1 mission?
 *
 * Takes the *required* set as input (defaults to the dynamic derivation).
 * Tests pass a synthetic explicit set to avoid coupling to the JSON.
 *
 * Returns `true` when `required` is a subset of the completed set. Empty
 * `required` (catalog returned zero ids) is `true` vacuously — the gate
 * should never lock when there is nothing to clear. Robust against
 * non-array inputs from a corrupted localStorage payload (returns `false`
 * when the completion set cannot be read).
 */
export function isArcOneCleared(
  required: ReadonlyArray<string> = ARC_ONE_REQUIRED_IDS,
): boolean {
  if (required.length === 0) return true;
  const completed = getCompletedMissions();
  for (const id of required) {
    if (!completed.includes(id)) return false;
  }
  return true;
}

/** Side-effecting helper — evaluate the new full-clear rule and flip the flag if newly satisfied.
 *
 * Called from `state_actions.ts:applyLootAction` on every Arc-1 mission complete.
 * Two-step behavior:
 *   1. If the legacy flag is already `"1"` → no-op (already unlocked; never re-lock).
 *   2. Else if `isArcOneCleared()` returns `true` (the completed set covers
 *      every required Sprawl Arc-1 id) → flip the legacy flag via
 *      `setFarGridUnlocked()` and report `true` (newly unlocked).
 *   3. Else → return `false` (still locked; this Arc-1 mission is recorded
 *      by the caller via `recordMissionComplete` separately).
 *
 * Returns `true` when the flag was newly flipped this call.
 *
 * This is the auto-path entry point for the new semantics. Direct callers of
 * `setFarGridUnlocked()` still work (Phase 2 tests stay green); new wiring
 * goes through this helper so the OR semantics are centralized.
 */
export function evaluateFarGridUnlock(): boolean {
  if (isFarGridUnlocked()) return false;
  if (!isArcOneCleared()) return false;
  return setFarGridUnlocked();
}

/** Pure helper — read the FAR GRID unlock state using the OR semantics.
 *
 * Equivalent to `isFarGridUnlocked() || isArcOneCleared()`. This is the
 * canonical predicate the menu + cache should use; it never re-locks an
 * already-set legacy flag AND picks up full-clear unlocks that flipped
 * after the last legacy-only check.
 *
 * Side-effect-free.
 */
export function farGridUnlocked(): boolean {
  return isFarGridUnlocked() || isArcOneCleared();
}

/** Reset the completed-mission record — test/admin escape hatch.
 *
 * Mirrors `resetFarGridUnlocked()`. Safe to call in non-browser contexts
 * (no-op). Does NOT touch the legacy unlock flag.
 */
export function resetCompletedMissions(): void {
  if (typeof localStorage === "undefined") return;
  try {
    localStorage.removeItem(COMPLETED_STORAGE_KEY);
  } catch {
    // ignore
  }
}