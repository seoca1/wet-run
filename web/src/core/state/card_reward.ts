/**
 * Card reward — the run's growth (ADR-0259).
 *
 * Winning a fight offers three programs the runner does not already hold.
 * Taking one adds it to the draw pile, so the next time the hand empties the
 * new card is in play. This is the only way to gain cards: the game has no
 * shop (the shop screen is a stub) and loot drops materials, not programs.
 *
 * The offer is a **pure function of the run**, not stored state: the same
 * fight always offers the same three cards. That keeps a reload honest — a
 * saved loot frame offers the same choice instead of re-rolling — and it
 * consumes no `Math.random`, so the balance harness is unaffected.
 */

import type { GameState, Program } from "../types";
import programsData from "../../data/programs.json";
import { loadProgramsCatalog } from "../data_loaders";
import { missionSeedOf } from "../combat/ice_scaling";
import { makeMulberry32 } from "../dungeon/dungeon";

/** The normalized catalog (`Program` objects), loaded once. */
let catalogCache: Readonly<Record<string, Program>> | null = null;
function catalog(): Readonly<Record<string, Program>> {
  catalogCache ??= loadProgramsCatalog(programsData);
  return catalogCache;
}

/** Distinct programs offered per reward. */
export const CARD_REWARD_COUNT = 3;

/** The run fields a reward depends on — enough to know what is owned. */
export type RewardSource = Pick<
  GameState,
  | "deck"
  | "drawPile"
  | "discardPile"
  | "mission"
  | "turnCount"
  | "currentNodeIndex"
  | "cardRewardTaken"
> & {
  /** The ICE that was just beaten. Optional: hand-built states, old saves and
   * tests without a roster fall back to the neutral tier (ADR-0292). */
  readonly iceRoster?: ReadonlyArray<{ readonly tier: number }>;
};

/** The tier of the fight that produced this reward (ADR-0292).
 *
 * A multi-ICE room counts as its hardest member — the reward is the room's, not
 * the last kill's. Falling back to 1 keeps every caller that has no roster
 * exactly where it was before.
 */
function iceTierOf(state: RewardSource): number {
  const tiers = (state.iceRoster ?? [])
    .map((ice) => ice.tier)
    .filter((t): t is number => Number.isFinite(t));
  return tiers.length > 0 ? Math.max(...tiers) : 1;
}

/**
 * Every program the run holds, hand and piles alike — minus the card taken
 * from this very offer. Keeping the taken card in the pool holds the offer
 * steady, so taking one does not shuffle the other two.
 */
function ownedIds(state: RewardSource): ReadonlySet<string> {
  const owned = new Set(
    [...state.deck, ...state.drawPile, ...state.discardPile].map((p) => p.id),
  );
  if (state.cardRewardTaken) owned.delete(state.cardRewardTaken);
  return owned;
}

/** Programs that only a tier-6 fight can drop (ADR-0303).
 *
 * ADR-0302 measured the skill gap: how much better the run goes when the runner
 * uses the choices. It read +40pp at g3-g4 and **+2.8 at g6** — at the top grade
 * the choices were worth nothing, because every card there is already tier 5 and
 * the drop weighting (ADR-0292) had no distance left to exploit.
 *
 * These three are the g6 axis. They are not stronger versions of the same card —
 * all three hit for the same 30 — they are three different answers to the same
 * hit (armor, body, or the hit itself), so picking one is picking what the deck
 * cannot do. And because ADR-0296 burns the strongest card for capacity, a g6
 * runner now has something worth burning.
 */
export const UNIQUE_PROGRAMS: ReadonlySet<string> = new Set([
  "ghost_key",
  "null_pointer",
  "red_shift",
]);

/** The tier a fight must be to drop a unique program. Tier 6 is the g6 band. */
export const UNIQUE_MIN_ICE_TIER = 6;

/** The three program ids offered to whoever just won at this node. */
export function offeredCardIds(
  state: RewardSource,
  count: number = CARD_REWARD_COUNT,
): readonly string[] {
  const owned = ownedIds(state);
  const iceTier = iceTierOf(state);
  const pool = Object.keys(catalog())
    .filter((id) => !owned.has(id))
    // ADR-0303: the uniques are the top grade's own axis, not a mid-run upgrade.
    .filter((id) => !UNIQUE_PROGRAMS.has(id) || iceTier >= UNIQUE_MIN_ICE_TIER)
    .sort();
  if (pool.length === 0) return [];

  // Deterministic from (mission seed, turn, node): the same fight offers the
  // same cards, and no `Math.random` is consumed.
  const seed =
    (missionSeedOf(state.mission) +
      state.turnCount * 31 +
      state.currentNodeIndex * 7) >>>
    0;
  const rng = makeMulberry32(seed);

  // ADR-0292: a card's weight is how close its tier is to the ICE that dropped
  // it. `1 / (1 + d^2)` keeps a rare ICE from being a guaranteed rare card and
  // still makes a strong fight worth more than a weak one — which is the thing
  // bought intel can now forecast (ADR-0291 measured information at ~zero while
  // every fight in a grade dropped the same pool).
  const weight = (id: string): number => {
    // ADR-0303: a unique is a FIND, not a flood. Measured: equal weighting at g6
    // dropped completion 9.7 -> 6.9 because every offer became tier-6 and the
    // tier-5 cards the deck actually wanted stopped appearing.
    if (UNIQUE_PROGRAMS.has(id)) return 0.35;
    const tier = catalog()[id]?.tier ?? 1;
    const d = Math.abs(tier - iceTier);
    return 1 / (1 + d * d);
  };

  // Weighted selection without replacement, still consuming exactly `count`
  // draws from the same seed, so a fight's offer stays a pure function of it.
  const picked: string[] = [];
  const remaining = [...pool];
  const n = Math.min(count, remaining.length);
  for (let i = 0; i < n; i += 1) {
    let total = 0;
    for (const id of remaining) total += weight(id);
    let roll = rng() * total;
    let index = remaining.length - 1;
    for (let j = 0; j < remaining.length; j += 1) {
      roll -= weight(remaining[j] as string);
      if (roll <= 0) {
        index = j;
        break;
      }
    }
    const chosen = remaining[index];
    if (chosen === undefined) break;
    remaining.splice(index, 1);
    picked.push(chosen);
  }
  return picked;
}

/** The program object behind an offer id, or undefined when the catalog lacks it. */
export function rewardProgram(id: string): Program | undefined {
  return catalog()[id];
}
