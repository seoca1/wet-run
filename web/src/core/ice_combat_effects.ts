/** ICE-side non-damaging skill effects — ADR-0219 Option A.
 *
 * Implements the three effect families an ICE can cast on itself:
 *
 *  - `shield` — an absorbing pool. Incoming player damage is reduced by the
 *    pool before it reaches the ICE's HP; the pool shrinks by what it
 *    absorbs and is removed once it is empty or its duration runs out.
 *  - `heal` — an immediate HP restore, capped at the ICE's max HP.
 *  - `regen` — an HP restore applied on every enemy tick, capped at max HP.
 *  - `buff` — a flat outgoing-damage bonus for the ICE, with a duration.
 *
 * ## Semantics
 *
 * **Shield.** One pool per ICE. `magnitude` holds the HP the pool can still
 * absorb; `remaining` holds the lifetime in enemy ticks. Re-casting the
 * shield skill *adds* to the pool and *refreshes* the lifetime rather than
 * adding to it — the prototype-era rule in `docs/testcases/combat/depth.md`
 * (TC-DEPTH-004: "state.shield = 2, wisp duration refresh (5s from now)";
 * TC-DEPTH-005: "shield 가 3 모두 흡수... Shield status 가 consumed").
 *
 * **Heal / regen.** Both restore HP but never past the ICE's max HP. `heal`
 * restores once, immediately, when the skill fires. `regen` restores
 * `healPerTick` on every enemy tick until it expires.
 *
 * **Buff.** Adds `attackBonus` to the ICE's outgoing damage (both its skill
 * damage and its auto-attack) for the duration of the effect.
 *
 * ## Durations
 *
 * One tick is one enemy turn, i.e. one `AUTO_ATTACK_INTERVAL_MS` (2000 ms)
 * window — the cadence the combat path already uses for enemy actions. The
 * durations are therefore:
 *
 * | effect  | ticks | wall time |
 * | ------- | ----- | --------- |
 * | shield  | 3     | 6000 ms   |
 * | regen   | 4     | 8000 ms   |
 * | buff    | 3     | 6000 ms   |
 *
 * ## State
 *
 * The per-ICE state lives on the existing `GameState.statusEffects` array
 * (extended with `iceIndex` and `tickSource`) rather than on a parallel
 * collection: the array already carries `kind` / `remaining` / `magnitude` /
 * `target`, so a shield pool is exactly a `shield` instance whose `magnitude`
 * is the remaining absorb pool and whose `remaining` is the lifetime.
 *
 * The per-effect *application* (shield / heal / regen / buff) lives in
 * `ice_combat_effect_apply.ts`; this module owns the shared state helpers,
 * the damage absorption and the enemy-tick advance.
 *
 * The ICE is identified by its **roster slot index**, not by its catalog id:
 * a roster may legitimately hold two ICE with the same id (the encounter
 * band repeats ids when a node carries fewer ids than the roster needs),
 * and the roster order is stable for the whole encounter (dead ICE stay in
 * the roster with `hp === 0`).
 */
import type { GameState, Ice, StatusEffectInstance } from "./types.ts";

/** Effect kinds this module implements. Everything else stays inert. */
export const ICE_NON_DAMAGE_EFFECTS: ReadonlySet<string> = new Set([
  "shield",
  "heal",
  "regen",
  "buff",
]);

/** Lifetime of a shield pool, in enemy ticks. */
export const ICE_SHIELD_DURATION_TICKS = 3;
/** Lifetime of a regen effect, in enemy ticks. */
export const ICE_REGEN_DURATION_TICKS = 4;
/** Lifetime of an outgoing-damage buff, in enemy ticks. */
export const ICE_BUFF_DURATION_TICKS = 3;

/** The ICE skill shape this module reads. */
export interface IceEffectSkill {
  readonly id: string;
  readonly name: string;
  readonly effect: string;
  readonly magnitude?: number;
}

/** Result of applying a non-damaging ICE skill. */
export interface IceEffectOutcome {
  readonly state: GameState;
  /** Human-readable log line, or `null` when the skill had no effect. */
  readonly message: string | null;
  /** VFX instances the effect spawned — display only, never read by the
   * combat math. Empty when the effect was inert. */
  readonly vfx: ReadonlyArray<import("../renderer/combat_vfx.js").CombatVfxInstance>;
}

export function replaceEffect(
  state: GameState,
  index: number,
  next: StatusEffectInstance,
): GameState {
  const updated = [...state.statusEffects];
  updated[index] = next;
  return { ...state, statusEffects: updated };
}

export function removeEffect(state: GameState, index: number): GameState {
  const updated = [...state.statusEffects];
  updated.splice(index, 1);
  return { ...state, statusEffects: updated };
}

/** The ICE's effective max HP.
 *
 * Catalog ICE rows carry no `maxHp` (the JSON has `hp_base` / `hp_per_grade`
 * and the loader derives HP), and the encounter roster is built from those
 * rows, so `maxHp` is usually absent. When it is, fall back to the ICE's
 * current HP — a healing ICE that is at full HP must not be able to bank
 * healing above its current pool.
 */
export function iceMaxHp(ice: Ice): number {
  if (typeof ice.maxHp === "number" && Number.isFinite(ice.maxHp) && ice.maxHp > 0) {
    return ice.maxHp;
  }
  return Math.max(0, ice.hp);
}

/** Heal an ICE, never above its max HP. Returns the applied amount. */
export function healIce(ice: Ice, amount: number): { ice: Ice; healed: number } {
  const maxHp = iceMaxHp(ice);
  const next = Math.min(maxHp, ice.hp + Math.max(0, amount));
  const healed = next - ice.hp;
  return { ice: healed === 0 ? ice : { ...ice, hp: next }, healed };
}

/** Total outgoing-damage bonus an ICE currently has from `buff` effects. */
export function iceAttackBonus(state: GameState, iceIndex: number): number {
  return state.statusEffects
    .filter((e) => e.kind === "powered" && e.iceIndex === iceIndex)
    .reduce((sum, e) => sum + (e.attackBonus ?? 0), 0);
}

/** Total absorb pool an ICE currently has from `shield` effects. */
export function iceShieldPool(state: GameState, iceIndex: number): number {
  return state.statusEffects
    .filter((e) => e.kind === "shield" && e.iceIndex === iceIndex)
    .reduce((sum, e) => sum + e.magnitude, 0);
}

/** Damage an ICE takes after its shield pool has absorbed what it can.
 *
 * The pool is spent before the ICE's HP is touched. Returns the damage that
 * actually reaches HP and the amount the pool absorbed.
 */
export function absorbIceDamage(
  state: GameState,
  iceIndex: number,
  damage: number,
): { state: GameState; damage: number; absorbed: number } {
  const shieldIndex = state.statusEffects.findIndex(
    (e) => e.kind === "shield" && e.iceIndex === iceIndex,
  );
  if (shieldIndex < 0 || damage <= 0) {
    return { state, damage, absorbed: 0 };
  }
  const shield = state.statusEffects[shieldIndex];
  if (!shield) {
    return { state, damage, absorbed: 0 };
  }
  const absorbed = Math.min(shield.magnitude, damage);
  const left = shield.magnitude - absorbed;
  let next = state;
  if (left <= 0) {
    next = removeEffect(state, shieldIndex);
  } else {
    next = replaceEffect(state, shieldIndex, { ...shield, magnitude: left });
  }
  return { state: next, damage: damage - absorbed, absorbed };
}

/** Advance the enemy-ticked ICE effects by one enemy tick.
 *
 * Regen effects restore HP (capped at max HP) as they tick; expired effects
 * are removed.
 */
export function tickIceEffects(state: GameState): GameState {
  let next = state;
  for (let i = 0; i < state.statusEffects.length; i++) {
    const effect = state.statusEffects[i];
    if (!effect || effect.tickSource !== "enemy") continue;
    const remaining = effect.remaining - 1;
    if (remaining <= 0) {
      next = removeEffect(next, i);
      continue;
    }
    let updated: StatusEffectInstance = { ...effect, remaining };
    if (effect.kind === "regen" && effect.iceIndex !== undefined) {
      const perTick = effect.healPerTick ?? effect.magnitude;
      const ice = next.iceRoster[effect.iceIndex];
      if (ice && perTick > 0) {
        const { ice: healedIce } = healIce(ice, perTick);
        updated = { ...updated, healPerTick: perTick };
        next = {
          ...next,
          iceRoster: next.iceRoster.map((entry, idx) =>
            idx === effect.iceIndex ? healedIce : entry,
          ),
        };
      }
    }
    next = replaceEffect(next, i, updated);
  }
  return next;
}

/** Drop every ICE-cast effect — used when a new encounter starts. */
export function clearIceEffects(state: GameState): GameState {
  return {
    ...state,
    statusEffects: state.statusEffects.filter((e) => e.tickSource !== "enemy"),
  };
}
