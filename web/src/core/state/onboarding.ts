/** Onboarding state (proposal P11) — pure, testable module.
 *
 * Two problems are solved here, and both are pure decisions so they can be
 * unit-tested without booting the canvas renderer:
 *
 * 1. **First-boot tutorial auto-show.** `renderer/tutorial.ts` documents
 *    "Shown once on first boot (localStorage flag 'tutorial_completed')" but
 *    nothing ever called it on boot — the tutorial was reachable from the menu
 *    only. `shouldAutoShowTutorial` decides whether the boot path may enter
 *    the tutorial, and it is gated on the same localStorage key the tutorial
 *    overlay itself writes, so the tutorial appears exactly once per profile.
 *
 * 2. **Combat-entry hint.** The first combat screen has to tell the player
 *    that `1-9` uses a program. `combatEntryHint` builds that hint and
 *    `combatEntryHintRows` places it, keeping the hint off the HUD rows the
 *    player needs (mission title, HP bar, hand) and clear of the VFX banner
 *    band that `ice_intro` paints (proposal P15 / §R note).
 *
 * The module deliberately has no DOM dependency beyond an injectable storage
 * port, so it imports cleanly under vitest's `node` environment (where
 * `main.ts` cannot be imported at all — it self-boots).
 */

import { combatHandRow } from "../combat/program_affordance";

/** localStorage key the tutorial overlay writes on completion. */
export const TUTORIAL_COMPLETED_KEY = "wetrun_tutorial_completed";

/** Minimal storage port — `localStorage` in the browser, a stub in tests. */
export interface OnboardingStorage {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
}

/** Read the tutorial-completed flag. Returns `false` when storage is absent. */
export function isTutorialCompleted(
  storage: OnboardingStorage | null | undefined,
): boolean {
  if (!storage) return false;
  try {
    return storage.getItem(TUTORIAL_COMPLETED_KEY) === "true";
  } catch {
    // A blocked / quota-exceeded localStorage must never break the boot.
    return false;
  }
}

/** Mark the tutorial as completed. Silently no-ops when storage is absent. */
export function markTutorialCompleted(
  storage: OnboardingStorage | null | undefined,
): void {
  if (!storage) return;
  try {
    storage.setItem(TUTORIAL_COMPLETED_KEY, "true");
  } catch {
    // ignore — the tutorial is a nicety, never a hard requirement.
  }
}

/**
 * Whether the boot path should enter the tutorial automatically.
 *
 * True only on a first boot (the completion flag is absent) — the tutorial is
 * shown exactly once per profile, then the flag is written and the flag
 * short-circuits every later boot.
 */
export function shouldAutoShowTutorial(
  storage: OnboardingStorage | null | undefined,
): boolean {
  return !isTutorialCompleted(storage);
}

/** The combat-entry hint lines shown on the first combat screen. */
export const COMBAT_ENTRY_HINT_LINES: readonly string[] = [
  "1-9: USE PROGRAM   (tap the program buttons on touch devices)",
  "ICE first. You first. COST over 100 blocks programs.",
  // ADR-0258: the killing blow charges no COST. The hand row may not predict
  // it (kill prediction is forbidden), so the rule is stated once here.
  "The last-hit program costs no COST.",
] as const;

/** A combat-entry hint rendered as a single line (used by the HUD). */
export function combatEntryHint(): string {
  return COMBAT_ENTRY_HINT_LINES[0] ?? "";
}

/**
 * Rows the hint may occupy, relative to the bottom of the grid.
 *
 * The hint sits above the hand header (`combatHandRow`, ADR-0251) so it
 * never covers the programs the player must press, and it stays clear of the
 * `ice_intro` banner band the renderer paints on rows 1..5.
 */
export function combatEntryHintRows(rows: number): readonly number[] {
  const handRow = combatHandRow(rows);
  const lines = COMBAT_ENTRY_HINT_LINES.length;
  return Array.from({ length: lines }, (_, i) => handRow - lines + i);
}

/**
 * Whether the combat-entry hint still fits on the given grid.
 *
 * Two conditions: the hint must start below the `ice_intro` banner band
 * (row 5) so the two never overlap, and the last hint row must be inside the
 * grid. A degenerate grid (fewer rows than the hand row) therefore cannot
 * carry the hint.
 */
export function combatEntryHintFits(rows: number): boolean {
  const hintRows = combatEntryHintRows(rows);
  const first = hintRows[0];
  const last = hintRows[hintRows.length - 1];
  if (first === undefined || last === undefined) return false;
  return first >= 6 && last < rows;
}

/** The Matrix-entry hint (ADR-0249 affordance slice): the first board with a
 * route teaches how to read it, once, the same way the combat hint does. */
export const MATRIX_ENTRY_HINT_LINES: readonly string[] = [
  "TIP: solid lines from @ are routes",
  "↓↑ picks one · ENTER travels there",
] as const;

/** The slice of state the Matrix-entry hint decision reads. */
export interface MatrixHintState {
  readonly runPhase: string;
  readonly encounterDecision?: unknown;
  readonly matrix?: {
    readonly nodes: ReadonlyArray<{ readonly adjacent: readonly number[] }>;
  } | null;
  readonly currentNodeIndex: number;
}

/**
 * Whether the Matrix-entry hint belongs on this frame: not yet shown, on the
 * board itself (no crossing menu open) and with at least one route to take.
 * The controller sets its flag on the first input made while this is true,
 * so the hint is dismissed by that input and never returns.
 */
export function shouldShowMatrixEntryHint(
  alreadyShown: boolean,
  state: MatrixHintState | null,
): boolean {
  if (alreadyShown || state === null || state.runPhase !== "matrix")
    return false;
  if (state.encounterDecision) return false;
  const nodes = state.matrix?.nodes ?? [];
  const here = nodes[state.currentNodeIndex];
  return (here?.adjacent ?? []).some(
    (i) => i !== state.currentNodeIndex && nodes[i] !== undefined,
  );
}
