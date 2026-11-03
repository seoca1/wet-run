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
 * What each jockey opens with (ADR-0276).
 *
 * The prologue is one story per jockey, and the jockey already names the run;
 * this is the part that decides how it plays. Each list keeps the ADR-0260
 * shape (most cards press, at least one blunts -- the all-defense opening was
 * measured and rejected there), and differs by one or two thematic swaps:
 *
 *   CASE  the curated deck, unchanged: a little of everything.
 *   SIL   trades the support card for `exploit` -- corporate ice, cracked.
 *   KAS   trades the support card and the shield for `exploit` and `virus`:
 *         four cards that hit and one that does not. He is not careful.
 *
 * Every deck was measured on the same curve as the others (`npm run balance
 * -- --deck <jockey>`). Two design facts decided the swaps:
 *
 *   - Only five programs have a wired effect (`backdoor`, `barrier`, `boost`,
 *     `cloak`, `decoy`); every other card is a plain `tier * 5` attack. A swap
 *     that drops an effect card for a plain one is a downgrade, not a flavour
 *     change -- which is exactly how the first KAS deck measured (72.4% at
 *     grade 3, below the curated deck's 78.4%).
 *   - A tier upgrade is the one trade the plain damage path rewards: SIL's
 *     `boost` (t2) to `exploit` (t3) buys roughly five points of grade-3 win
 *     rate.
 *
 * So KAS buys aggression with tiers rather than by dropping shields, and lands
 * level with CASE (78.6% vs 78.4% at grade 3) while playing differently.
 *
 * Both `main.ts` and the balance harness read these, so a measured deck cannot
 * drift from a played one, and `npm run balance -- --deck veteran` measures
 * exactly what a SIL run plays.
 */
export const JOCKEY_DECK_IDS: Readonly<Record<string, readonly string[]>> =
  Object.freeze({
    novice: STARTING_DECK_IDS,
    veteran: ["strike", "backdoor", "exploit", "barrier", "decoy"],
    heretic: ["strike", "exploit", "virus", "surge", "decoy"],
  });

/** The deck ids for a jockey, falling back to the curated opening. */
export function startingDeckIds(jockeyId?: string | null): readonly string[] {
  return (
    (jockeyId !== null && jockeyId !== undefined
      ? JOCKEY_DECK_IDS[jockeyId]
      : undefined) ?? STARTING_DECK_IDS
  );
}

/**
 * Resolve the starting deck against a catalog, skipping any id the catalog
 * lacks so a data edit cannot crash the boot.
 */
export function startingDeck(
  catalog: Readonly<Record<string, Program>>,
  jockeyId?: string | null,
): Program[] {
  return startingDeckIds(jockeyId)
    .map((id) => catalog[id])
    .filter((p): p is Program => p !== undefined);
}
