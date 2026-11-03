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
>;

/** Every program object a run currently holds, hand and piles alike. */
function ownedIds(state: RewardSource): ReadonlySet<string> {
  return new Set(
    [...state.deck, ...state.drawPile, ...state.discardPile].map((p) => p.id),
  );
}

/** The three program ids offered to whoever just won at this node. */
export function offeredCardIds(
  state: RewardSource,
  count: number = CARD_REWARD_COUNT,
): readonly string[] {
  const owned = ownedIds(state);
  const pool = Object.keys(catalog())
    .filter((id) => !owned.has(id))
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

  // Partial Fisher-Yates: pick `count` distinct entries without a full shuffle.
  const picked: string[] = [];
  const remaining = [...pool];
  const n = Math.min(count, remaining.length);
  for (let i = 0; i < n; i += 1) {
    const j = i + Math.floor(rng() * (remaining.length - i));
    const chosen = remaining[j];
    if (chosen === undefined) break;
    remaining[j] = remaining[i] as string;
    remaining[i] = chosen;
    picked.push(chosen);
  }
  return picked;
}

/** The program object behind an offer id, or undefined when the catalog lacks it. */
export function rewardProgram(id: string): Program | undefined {
  return catalog()[id];
}
