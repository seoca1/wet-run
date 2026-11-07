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
export const LOOT_INTEL_SLOT = LOOT_PROGRAM_SLOTS + 2; // 5
export const LOOT_VENT_SLOT = LOOT_PROGRAM_SLOTS + 3; // 6

/** Percent of max HP repaired, per grade — the price of giving up a card.
 *
 * Higher than the old automatic heal (15/15/25/40/55/65) because it now costs
 * the card: you cannot repair and grow at the same stop.
 */
export const LOOT_REPAIR_PCT_BY_GRADE: ReadonlyArray<number> = [
  70, 70, 85, 100, 100, 100,
];

/** The repair, as a percent of max HP, for a mission grade. */
export function lootRepairPctForGrade(grade: number): number {
  return LOOT_REPAIR_PCT_BY_GRADE[clampGrade(grade) - 1] ?? 40;
}

/** The repair, as an HP amount, for a runner of `maxHp` at a grade. */
export function lootRepairAmount(maxHp: number, grade: number): number {
  return Math.floor(maxHp * (lootRepairPctForGrade(grade) / 100));
}

/** Price of route intel, per grade (ADR-0287).
 *
 * Information, not power, so it does not move the difficulty curve — that is the
 * whole point after four power-granting sinks were measured and rejected
 * (ADR-0286). PROBE already sells threat knowledge for COST at the encounter
 * gate; this sells it for credits, and about the routes ahead rather than the
 * node you are standing on.
 */
export const LOOT_INTEL_PRICE_BY_GRADE: ReadonlyArray<number> = [
  30, 40, 60, 80, 110, 120,
];

/** What the intel costs at a mission grade. */
export function lootIntelPrice(grade: number): number {
  return LOOT_INTEL_PRICE_BY_GRADE[clampGrade(grade) - 1] ?? 30;
}

/** COST the vent clears, and what that costs in credits (ADR-0295).
 *
 * ADR-0294 made every kill leave a trace worth its ICE's tier, which turned
 * "how much do I fight" into a trade. A trade with no way out is a trap, though:
 * once the budget is exhausted the runner can only sit there and watch. So the
 * trace can be vented — for money, at a price that is deliberately WORSE than
 * earning it back.
 *
 * The arithmetic: a kill pays its bounty (ADR-0293) and leaves 1 COST per tier.
 * At g6 that is 200cr for 6 COST, i.e. ~33cr per point. Venting costs 40 per
 * point, so clearing a kill's whole trace loses money. Venting is therefore for
 * the moment when capacity is worth more than the credits — which is a decision,
 * not a discount.
 */
export const VENT_COST = 10;

/** Percent of max HP one vent costs.
 *
 * ADR-0295: the first design sold the vent for credits, and the measurement
 * killed it twice — cheap (40cr/COST) it reopened the fight/skip lead at +5.5pp,
 * because money minted capacity; expensive (190cr) it was never affordable, so it
 * was dead weight. There is no price in between that balances both g5 and g6.
 *
 * Paying in HP is the version that cannot inflate anything: the vent is a
 * REALLOCATION, body into capacity, at a loss. The run's total resource is the
 * same, so the fight/skip trade survives by construction.
 *
 * 40% of max HP is measured, not chosen for feel: at 15% the vent is strong
 * enough to reopen the lead (g6 31.7 vs 13.3 for skipping), at 30% it is +5.0,
 * and at 40% it is +2.5 — an emergency valve that fires occasionally (g6 15.8
 * against 14.6 with no vent at all) without buying the answer.
 */
export const VENT_HP_PCT = 40;

/** What one vent costs in HP. */
export function ventHpPrice(maxHp: number): number {
  return Math.ceil(maxHp * (VENT_HP_PCT / 100));
}

/** The slot a loot keypress refers to, or null when it is not a loot option. */
export function lootSlotChoice(
  slot: number,
): "program" | "repair" | "intel" | "vent" | null {
  if (slot >= 1 && slot <= LOOT_PROGRAM_SLOTS) return "program";
  if (slot === LOOT_REPAIR_SLOT) return "repair";
  if (slot === LOOT_INTEL_SLOT) return "intel";
  if (slot === LOOT_VENT_SLOT) return "vent";
  return null;
}

/** Uncleared encounter nodes, i.e. everything the intel can reveal. */
export function intelTargets(
  nodes: ReadonlyArray<{
    readonly iceIds: ReadonlyArray<string>;
    readonly isBoss: boolean;
  }>,
  cleared: readonly number[],
  bypassed: readonly number[],
): readonly number[] {
  const clearedSet = new Set(cleared);
  const bypassedSet = new Set(bypassed);
  const out: number[] = [];
  for (let i = 0; i < nodes.length; i += 1) {
    if (clearedSet.has(i) || bypassedSet.has(i)) continue;
    if ((nodes[i]?.iceIds.length ?? 0) === 0) continue;
    out.push(i);
  }
  return out;
}
