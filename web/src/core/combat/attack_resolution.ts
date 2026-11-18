/** SRW-shaped attack resolution (ADR-0321) — several probabilistic cases per hit.
 *
 * The measurement that motivated this. Until now **every attack landed**: the
 * player's card always connected, and so did the ICE's auto-attack. The only
 * probability in combat was the crit roll. The owner asked for Super Robot Wars'
 * shape instead — hit / evade / guard / critical as *cases*, rolled per attack.
 *
 * What already existed and is reused rather than invented:
 *
 *   - `critical` — `combat_engine.ts` rolls it (15%, `aggressive` ICE +5%).
 *     This module does NOT roll it again; it only names the case so the screen
 *     can show it.
 *   - `evasion` — `cloak` already granted a flat "-15% incoming damage". That is
 *     NOT a dodge, it is a tax. Here it becomes what it says: a chance for the
 *     attack to MISS entirely.
 *   - `guard` — new. The runner rolls with the punch and takes half.
 *
 * One draw per attack, and the bands are ordered so a single table can be read
 * top to bottom:
 *
 *     [0, miss)  -> MISS     0 damage
 *     [miss, miss+guard) -> GUARD    half damage
 *     [miss+guard, 1)    -> HIT     full damage
 *
 * ## The mean is a dial, the variance is the point
 *
 * `BASE_MISS_PCT + BASE_GUARD_PCT * 0.5` is the expected damage the cases remove,
 * so the table can be set to be mean-neutral and the ONLY thing that changes is
 * the distribution. That matters here: g5 and g6 lose a single fight (ADR-0319),
 * so a 10% chance of taking nothing is worth far more than a 10% damage cut —
 * one dodged lethal hit is a run that lives. The balance harness is the check.
 *
 * ## Player attacks do not miss (deliberately, for now)
 *
 * Jev `choice` on the scope read `incoming_attacks_can_miss_only` 0.44 with
 * confidence 0.25 — too low to act on, and it is surfaced, not applied. What the
 * two leading options DID agree on (0.44 + 0.33) is that a CARD should not whiff:
 * a card is a resource and a turn, and ADR-0251 rule 5 says the hand states what
 * the screen will do. `PLAYER_ODDS` exists so the owner can turn the other side
 * on with one number, and it ships at zero.
 *
 * Pure: the caller injects the roll, so the balance harness keeps its own dice.
 */

/** The cases one attack can resolve into, in band order. */
export type AttackCase = "miss" | "guard" | "hit";

/** The cases in the order the roll bands use. */
export const ATTACK_CASES: ReadonlyArray<AttackCase> = ["miss", "guard", "hit"];

/** Damage multiplier for a case. Crit is the engine's own band, not this table. */
export const CASE_DAMAGE_MULTIPLIER: Readonly<Record<AttackCase, number>> = {
  miss: 0,
  guard: 0.5,
  hit: 1,
};

/** Chances for one attack, in percent. They need not sum to 100: whatever is
 * left over is a plain `hit`. */
export interface AttackOdds {
  readonly missPct: number;
  readonly guardPct: number;
}

/** The runner's own defensive luck, before any card — **the owner's dial**.
 *
 * Measured, and the measurement is why it ships at zero. A table of
 * `miss 6 / guard 12` — which removes only ~12% of incoming damage on average —
 * moved the mission curve to g3 93.8, g4 92.2, g5 46.9, g6 60.4 (from 84.5 /
 * 84.4 / 27.1 / 34.4). That is +42pp at g4, and the reason is the variance, not
 * the mean: at g5/g6 the runner dies inside a single fight (ADR-0319), so a 6%
 * chance to take nothing is worth far more than a 6% damage cut. One dodged
 * lethal hit is a run that lives.
 *
 * So the cases ship as a MECHANISM with the base at zero: the curve is
 * byte-identical until the owner picks a value, and the ICE's damage has to be
 * raised against whatever they pick. See ADR-0321.
 */
export const INCOMING_BASE_ODDS: AttackOdds = Object.freeze({
  missPct: 0,
  guardPct: 0,
});

/** Player attacks: no miss, no guard. `cloak` is the runner's, not the ICE's. */
export const PLAYER_ODDS: AttackOdds = Object.freeze({
  missPct: 0,
  guardPct: 0,
});

/** How much incoming damage the cases remove on average, as a fraction. */
export function expectedDamageCut(odds: AttackOdds): number {
  const miss = Math.max(0, odds.missPct) / 100;
  const guard = Math.max(0, odds.guardPct) / 100;
  return miss * (1 - CASE_DAMAGE_MULTIPLIER.miss) +
    guard * (1 - CASE_DAMAGE_MULTIPLIER.guard);
}

/**
 * Resolve one attack from a single draw in `[0, 1)`.
 *
 * Bands are `miss`, then `guard`, then everything else is a hit — so raising one
 * chance never silently moves another case's band.
 */
export function resolveAttackCase(roll: number, odds: AttackOdds): AttackCase {
  const r = Number.isFinite(roll) ? Math.min(0.999999, Math.max(0, roll)) : 0;
  const miss = Math.max(0, odds.missPct) / 100;
  const guard = Math.max(0, odds.guardPct) / 100;
  if (r < miss) return "miss";
  if (r < miss + guard) return "guard";
  return "hit";
}

/** Apply a case's multiplier to a damage figure. */
export function applyCase(damage: number, c: AttackCase): number {
  if (damage <= 0) return 0;
  if (c === "miss") return 0;
  return Math.max(1, Math.floor(damage * CASE_DAMAGE_MULTIPLIER[c]));
}

/** The incoming odds for a runner carrying `evasionPct` of evasion.
 *
 * `cloak`'s 15% was a flat damage cut; it is now a 15% chance to take nothing,
 * added to the runner's own base luck. */
export function incomingOddsFor(evasionPct: number): AttackOdds {
  const extra = Number.isFinite(evasionPct) && evasionPct > 0 ? evasionPct : 0;
  return {
    missPct: INCOMING_BASE_ODDS.missPct + extra,
    guardPct: INCOMING_BASE_ODDS.guardPct,
  };
}

/** The word a case shows in the combat log — EMPTY for a plain hit.
 *
 * A `[HIT]` on every line is noise; the case is worth saying exactly when it is
 * not the ordinary one. */
export function caseLabel(c: AttackCase): string {
  return c === "miss" ? "MISS" : c === "guard" ? "GUARD" : "";
}

/** The log suffix for a case: ` [MISS]`, ` [GUARD]`, or nothing. */
export function caseNote(c: AttackCase): string {
  const label = caseLabel(c);
  return label === "" ? "" : ` [${label}]`;
}
