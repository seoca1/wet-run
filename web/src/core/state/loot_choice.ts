/** What a won fight hands the runner — and now, which of it they take.
 *
 * ADR-0282. The loot screen used to give a card offer **and** an automatic heal,
 * and ENTER skipped the card. So the only decision was "which program", and the
 * recovery between fights was not the player's to make.
 *
 * The owner's direction was to improve by increasing the player's choices, with
 * big impact allowed and immersion required. ADR-0280 had already ruled out
 * closing grades 5-6 from the numbers: healing (a full heal between fights still
 * leaves g3 at 54.5%), a softer curve (monotonicity caps p5 at p4), deck
 * strength (the developed deck still leaves g5 at 0.7%) and the invariants. The
 * remaining lever is what the runner carries INTO the next fight, and that is a
 * choice — the one the loot screen was already standing on.
 *
 * Now the screen is a spend: take a program, repair, or take the credits.
 */
import { clampGrade } from "../combat/ice_scaling";

/** The loot screen's option slots. Programs occupy 1..CARD_REWARD_COUNT. */
export const LOOT_PROGRAM_SLOTS = 3;
export const LOOT_REPAIR_SLOT = LOOT_PROGRAM_SLOTS + 1; // 4
export const LOOT_CREDITS_SLOT = LOOT_PROGRAM_SLOTS + 2; // 5

/** Percent of max HP repaired, per grade — the price of giving up a card.
 *
 * Higher than the old automatic heal (15/15/25/40/55/65) because it now costs
 * the card: you cannot repair and grow at the same stop.
 */
export const LOOT_REPAIR_PCT_BY_GRADE: ReadonlyArray<number> = [
  70, 70, 85, 100, 100, 100,
];

/** Credits taken instead of a card, per grade. */
export const LOOT_CREDITS_BY_GRADE: ReadonlyArray<number> = [
  50, 60, 80, 120, 160, 200,
];

/** The repair, as a percent of max HP, for a mission grade. */
export function lootRepairPctForGrade(grade: number): number {
  return LOOT_REPAIR_PCT_BY_GRADE[clampGrade(grade) - 1] ?? 40;
}

/** The repair, as an HP amount, for a runner of `maxHp` at a grade. */
export function lootRepairAmount(maxHp: number, grade: number): number {
  return Math.floor(maxHp * (lootRepairPctForGrade(grade) / 100));
}

/** The credits offered instead of a card, for a mission grade. */
export function lootCreditsForGrade(grade: number): number {
  return LOOT_CREDITS_BY_GRADE[clampGrade(grade) - 1] ?? 50;
}

/** The slot a loot keypress refers to, or null when it is not a loot option. */
export function lootSlotChoice(
  slot: number,
): "program" | "repair" | "credits" | null {
  if (slot >= 1 && slot <= LOOT_PROGRAM_SLOTS) return "program";
  if (slot === LOOT_REPAIR_SLOT) return "repair";
  if (slot === LOOT_CREDITS_SLOT) return "credits";
  return null;
}
