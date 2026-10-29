/**
 * ICE-side crit roll — ADR-0161's `aggressive` archetype bonus, made live.
 *
 * ## Why this module exists
 *
 * `ice_ai.ts` documents four archetype behaviors. Three of them are now
 * accounted for:
 *
 *   - `shouldDefensiveAct` — **already wired** by ADR-0226, as the
 *     two-regime rule inside `selectSkillByPersonality` (it reads the same
 *     `DEFENSIVE_HP_THRESHOLD`). Not re-wired here.
 *   - `getAlarmMultiplier` — **not wired**: the web build has no alarm
 *     accrual loop (see `combat_engine.ts` `tickAlarm`, which has no
 *     production caller), so there is no rate for a multiplier to scale.
 *   - `shouldTargetAlly` — **not wired**: the enemy path has no per-target
 *     skill resolution (every roster ICE acts on the player), so there is
 *     no ally for a support ICE to target.
 *   - `getCritBonus` — **wired here**. A crit roll already exists in the
 *     combat engine (`calculateDamage`), and this module is the bridge that
 *     lets an ICE's archetype contribute to it.
 *
 * ## Semantics
 *
 * The enemy's **base** damage is computed exactly as before, and this module
 * applies only the archetype's *crit* contribution on top:
 *
 *   - The crit chance is `getCritBonus(ice)` — **+5% for `aggressive`, 0 for
 *     every other archetype**. A non-aggressive ICE therefore never crits
 *     here; it keeps its pre-existing deterministic damage.
 *   - The crit multiplier is the engine's own `CRIT_MULTIPLIER` band
 *     (1.8 .. 2.2), rolled from the same injected RNG, so the result is
 *     consistent with the player-side crit in `combat_engine.ts`.
 *
 * ## Why the enemy does NOT go through `calculateDamage`
 *
 * `calculateDamage` is the *player's* damage pipeline. Routing the enemy
 * through it would also apply:
 *
 *   - `DAMAGE_VARIANCE_MIN..MAX` (0.8 .. 1.2) variance to every enemy hit,
 *   - the base `CRIT_CHANCE` (0.15) to **every** ICE, including `defensive`,
 *     `stealth` and `support`.
 *
 * Both are outside the scope of "the aggressive archetype gets +5% crit":
 * the first would re-roll the whole balance curve, and the second would
 * break the rule that the bonus applies to `aggressive` and *not* to
 * others. Applying the crit as a local modifier keeps the change
 * behaviour-local and keeps the enemy baseline damage identical.
 *
 * ## Purity
 *
 * The roll is a pure function of its inputs: the RNG is injected, and the
 * module holds no mutable state. `scripts/balance_sim.ts` overrides
 * `Math.random` for the duration of a run, so a roll that consumes
 * `Math.random` stays deterministic under the harness.
 */
import {
  CRIT_MULTIPLIER_MAX,
  CRIT_MULTIPLIER_MIN,
} from "./combat_engine.ts";
import { getCritBonus, type PersonalityBearer } from "./ice_ai.ts";

/** Result of an ICE crit roll. */
export interface IceCritResult {
  /** The damage the ICE deals, after any crit multiplier. */
  readonly damage: number;
  /** True when the roll critted. */
  readonly isCrit: boolean;
}

/**
 * Apply an ICE's archetype crit bonus to a damage number.
 *
 * `damage` is the ICE's already-computed base damage (skill damage or
 * auto-attack). It is returned unchanged unless the roll crits.
 *
 * @param ice The acting ICE — only its `personality` is read.
 * @param damage The ICE's base damage.
 * @param rng The injected random source. Consumes **one** value when the
 *   archetype can crit (the chance roll) and **two** more when it crits
 *   (the multiplier roll), matching `calculateDamage`'s consumption order.
 */
export function rollIceCrit(
  ice: PersonalityBearer,
  damage: number,
  rng: () => number,
): IceCritResult {
  const critChance = getCritBonus(ice);
  if (critChance <= 0) {
    // Non-aggressive archetypes never crit here — no RNG is consumed, so the
    // deterministic enemy damage is preserved exactly.
    return { damage, isCrit: false };
  }
  if (rng() >= critChance) {
    return { damage, isCrit: false };
  }
  const critMult =
    rng() * (CRIT_MULTIPLIER_MAX - CRIT_MULTIPLIER_MIN) +
    CRIT_MULTIPLIER_MIN;
  return {
    damage: Math.max(1, Math.floor(damage * critMult)),
    isCrit: true,
  };
}
