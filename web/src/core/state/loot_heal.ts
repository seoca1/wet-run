/** How much a runner recovers between fights (ADR-0280).
 *
 * The only healing in the game: when a non-terminal loot screen closes, the
 * runner heals a share of max HP. It used to be a flat 15% at every grade,
 * which is the wrong shape — a mission's length grows with the grade
 * (2.3 encounters at g1 against 7.4 at g5), so a long mission bleeds the runner
 * out through attrition no matter how winnable each fight is.
 *
 * This is also the one lever that **cannot** distort the per-encounter curve:
 * `balance_sim.ts` starts every encounter at full HP and stops at the win, so it
 * never sees a loot screen. Difficulty per fight stays where the recorded curve
 * puts it; this decides whether a *mission* is survivable.
 *
 * Measured with `npm run survival` (ADR-0280 question (d) option C).
 */
import { clampGrade } from "../combat/ice_scaling";

/** Percent of max HP recovered when a non-terminal loot screen closes.
 *
 * Rising with grade because the missions are longer, not because the fights are
 * kinder. A grade-5 mission is 7.4 encounters; at the old flat 15% the runner
 * had 90 HP of recovery to absorb several hundred points of attrition.
 */
export const LOOT_HEAL_PCT_BY_GRADE: ReadonlyArray<number> = [
  15, 15, 25, 40, 55, 65,
];

/** The heal, as a percent of max HP, for a mission grade. */
export function lootHealPctForGrade(grade: number): number {
  return LOOT_HEAL_PCT_BY_GRADE[clampGrade(grade) - 1] ?? 15;
}
