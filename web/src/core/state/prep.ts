/** What the fixer's advance buys before a run (ADR-0283).
 *
 * ADR-0280 §9: at grades 4-6 the runner loses its FIRST fight, so nothing that
 * happens *between* fights reaches it — which is why the route (ADR-0281) and the
 * loot stop (ADR-0282) move the middle grades and leave 4-6 at zero.
 *
 * Three capacity levers were measured, because the obvious one — buy cards — was
 * measured to make runs WORSE (the opening deck is a curated five-slot
 * instrument; a purchase evicts `barrier` or `decoy`, and under the "one enemy
 * phase per card" model a defensive slot is worth more than a tier buys):
 *
 *   extra max HP   +30 -> g4 31.7 -> 42.5, +250 -> g5 0 -> 19.4   WORKS
 *   extra hand     +2  -> g4 31.7 -> 31.7                          INERT
 *   card purchases      -> g2/g3 down, g4 +9.2                     HARMFUL
 *
 * So prep is HP: the first fight is a survivability check, and nothing else the
 * advance can buy survives it. A bigger hand does not help because the runner
 * dies holding the extra cards, and the COST cap bounds a turn regardless.
 *
 * NOTE the table is NOT monotone: grade 5 needs more than grade 6 (7.4 encounters
 * against 7.3, and `neuromancer`'s armour 9 against `aleph`'s 7). Unlike the ICE
 * HP cap there is no invariant on a player stat, so the honest shape is allowed.
 *
 * `state/loadout.ts` is the EQUIPMENT loadout; this module is the run's prep.
 */
import type { GameState } from "../types";
import { missionGradeOf } from "../combat/ice_scaling";
import { clampGrade } from "../combat/ice_scaling";

/** Extra starting max HP per grade, measured against the mission targets. */
export const PREP_HP_BY_GRADE: ReadonlyArray<number> = [0, 0, 20, 25, 270, 175];

/** Extra max HP the advance buys at a grade. */
export function prepHpBonus(grade: number): number {
  return PREP_HP_BY_GRADE[clampGrade(grade) - 1] ?? 0;
}

/**
 * Apply prep to a freshly built run: a bigger pool, filled.
 *
 * Applied at run start rather than in `makeInitialState`, so the per-encounter
 * balance harness keeps measuring the same fight it always did (prep is a run
 * fact, not an encounter fact).
 */
export function applyPrep(state: GameState): GameState {
  const bonus = prepHpBonus(missionGradeOf(state.mission));
  if (bonus <= 0) return state;
  const maxHp = state.player.maxHp + bonus;
  return { ...state, player: { ...state.player, maxHp, hp: maxHp } };
}
