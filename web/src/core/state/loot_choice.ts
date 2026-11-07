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

/** A card can be burned instead of the body (ADR-0296).
 *
 * ADR-0295 gave the trace an exit paid in HP, and measured that a CHEAP exit
 * undoes ADR-0294's trade. A card costs something the curve does not read at all
 * — growth — so burning one is a different currency: you give up a program that
 * would have helped later in exchange for capacity right now. That is the most
 * game-shaped price of the three, and it is also the one the fitted curve can
 * never be broken by.
 */
export const LOOT_BURN_SLOT = LOOT_VENT_SLOT + 1; // 7

/** COST one burned card clears.
 *
 * Measured, and both the target and the amount came out of the measurement:
 * burning the WEAKEST card is a free lunch (g5 50.5 vs 43.3, g6 20.8 vs 13.9 —
 * the weakest program is rarely played, so the "price" costs nothing), and at the
 * vent's full 10 COST even burning the strongest still left fighting ahead by
 * 4.2pp at g6. Burning the strongest for 7 lands the trade: g5 45.6/43.3 and
 * g6 12.5/13.3 at 48 seeds.
 */
export const BURN_COST = 7;

/** The reverse exchange: spare capacity bought back into body (ADR-0298).
 *
 * ADR-0295 turned HP into COST; nothing turned COST into HP, so a runner who
 * banked capacity and then took a beating could only watch the budget go unused.
 * The rate is deliberately WORSE than the vent's, so the two cannot be cycled:
 * venting 10 COST costs 40% of max HP, and recovering 10 COST gives 25% back —
 * a round trip always loses 15%.
 */
export const LOOT_RECOVER_SLOT = LOOT_BURN_SLOT + 1; // 8
export const RECOVER_COST = 10;
export const RECOVER_HP_PCT = 25;

/** Only a HOT trace can be bled off (ADR-0298).
 *
 * The measurement is the reason this exists. COST is surplus at the end of a
 * fight-heavy run (55-74 of 100), so converting it to HP is nearly free: at any
 * price the reverse exchange made fighting better and a bigger heal made it
 * better still (g5 47.5 -> 54.2 as the price rose, which is the tell). A
 * once-per-run cap did not fix it either.
 *
 * What does: only allow the draw when the trace is hot enough to have spare
 * pressure. At 70+ the trade holds (g5 41.9 vs 43.3, g6 11.8 vs 13.9), because
 * the runner who needs the budget later has already spent it.
 */
export const RECOVER_MIN_COST = 70;

/** HP one recovery returns. */
export function recoverHpAmount(maxHp: number): number {
  return Math.floor(maxHp * (RECOVER_HP_PCT / 100));
}

/** Can the runner draw on the trace right now? */
export function canRecover(state: {
  readonly player: { readonly alarm: number; readonly hp: number; readonly maxHp: number };
}): boolean {
  return (
    state.player.alarm >= RECOVER_MIN_COST && state.player.hp < state.player.maxHp
  );
}

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
): "program" | "repair" | "intel" | "vent" | "burn" | "recover" | null {
  if (slot >= 1 && slot <= LOOT_PROGRAM_SLOTS) return "program";
  if (slot === LOOT_REPAIR_SLOT) return "repair";
  if (slot === LOOT_INTEL_SLOT) return "intel";
  if (slot === LOOT_VENT_SLOT) return "vent";
  if (slot === LOOT_BURN_SLOT) return "burn";
  if (slot === LOOT_RECOVER_SLOT) return "recover";
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
