/**
 * Starting deck — the five programs a NEW RUN opens with (ADR-0260).
 *
 * This used to be "the first five ids in alphabetical order", which was an
 * accident of naming rather than a design choice: it happened to give one
 * attack and four defensive/support cards, so the opening was very tanky.
 * The list below is chosen on purpose: three cards that press the attack and
 * two that blunt the counter-attack, all at tier 1-2 so the opening teaches
 * the basics.
 *
 * Both `main.ts` (the game) and the balance harness read this list, so the
 * measured deck cannot drift away from the played one.
 */

import type { Program } from "../types";

/** Opening hand, in slot order. Three offensive, two defensive. */
export const STARTING_DECK_IDS: readonly string[] = [
  "strike", // t1 attack — the basic swing
  "backdoor", // t2 attack — ignores 2 armor
  "boost", // t2 support — +2 damage for 2 turns
  "barrier", // t3 defense — 2-point shield for 2 turns
  "decoy", // t2 defense — half of the next hit
] as const;

/** Cards in the opening hand (the draw pile is the rest of the deck). */
export const STARTING_DECK_SIZE = 5;

/**
 * Resolve the starting deck against a catalog, skipping any id the catalog
 * lacks so a data edit cannot crash the boot.
 */
export function startingDeck(
  catalog: Readonly<Record<string, Program>>,
): Program[] {
  return STARTING_DECK_IDS.map((id) => catalog[id]).filter(
    (p): p is Program => p !== undefined,
  );
}
