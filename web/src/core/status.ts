/** Status effect state machine (Tier 5).
 *
 * 5 effects from ADR-0207 (Tier 4 glyphs only) — now with actual duration
 * ticks + effect application on player or ICE.
 *
 * Each effect has:
 * - kind: which effect
 * - remaining: turns until expiration (decremented at end of actor's turn)
 * - magnitude: effect-specific (dot damage per turn for burn, slow % for slow, etc.)
 * - target: who has the effect (player or active ICE)
 *
 * Apply pattern (typical combat turn):
 *   1. tickStatus(state)         — decrement remaining, remove expired
 *   2. applyTickEffects(state)    — apply DoT/slow etc. at start of actor's turn
 *   3. resolveAttack → may rollStatus → may add new effect
 */
import type { GameState, StatusEffectInstance, StatusEffectKind } from "./types.ts";
import { isMutatorActive, type MutableRunState } from "./run_mutators.ts";

/** Apply a new status effect to a target. Stacks (adds new instance) if same kind.
 *
 * Optional overrides allow setting effect-specific fields (healPerTick, attackBonus, etc.).
 */
export function applyStatus(
  state: GameState,
  target: "player" | "ice",
  kind: StatusEffectKind,
  duration: number,
  magnitude: number,
  overrides?: {
    dotDamage?: number;
    healPerTick?: number;
    attackBonus?: number;
    defenseBonus?: number;
    slowPct?: number;
    vulnerabilityPct?: number;
    apRegenReduction?: number;
  },
): GameState {
  const newEffect: StatusEffectInstance = {
    kind,
    remaining: duration,
    magnitude,
    target,
    ...overrides,
  };
  return { ...state, statusEffects: [...state.statusEffects, newEffect] };
}

/** Tick all effects: decrement remaining, remove expired. Returns updated state. */
export function tickStatus(state: GameState): GameState {
  const next = state.statusEffects
    .map((e) => ({ ...e, remaining: e.remaining - 1 }))
    .filter((e) => e.remaining > 0);
  // Always return the updated state (even if length unchanged, remaining
  // values were decremented). The early-return optimization was buggy.
  return { ...state, statusEffects: next };
}

/** Apply DoT / slow / vulnerable / stagger / regen / bleed / fatigue / confused / terrified effects at start of actor's turn.
 *
 * Handles all 13 status effects:
 * - burn: deals magnitude damage to target
 * - stun: actor cannot act this turn (caller reads stunned flag)
 * - silence: actor cannot use special skills (caller reads silenced flag)
 * - slow: reduces next attack damage by slowPct% (caller reads for damage calc)
 * - vulnerable: next attack deals +vulnerabilityPct% damage (caller reads)
 * - stagger: skips next auto-attack (caller reads staggered flag)
 * - regen: heals healPerTick HP to target
 * - powered: increases attack by attackBonus (caller reads)
 * - weakened: reduces attack by attackBonus (negative, caller reads)
 * - bleed: deals dotDamage per tick AND increases damage vulnerability
 * - fatigue: reduces AP regen (caller reads fatigued flag)
 * - confused: 50% chance to hit self (caller reads confused flag)
 * - terrified: reduces attack damage (caller reads terrified flag)
 *
 * Returns flags + damage/heal amounts so caller can apply to HP/AP.
 */
export function applyTickEffects(state: GameState): {
  state: GameState;
  burnDamagePlayer: number;
  burnDamageIce: number;
  bleedDamagePlayer: number;
  bleedDamageIce: number;
  healPlayer: number;
  healIce: number;
  playerStunned: boolean;
  playerSilenced: boolean;
  playerStaggered: boolean;
  playerFatigued: boolean;
  playerConfused: boolean;
  playerTerrified: boolean;
  iceStunned: boolean;
  iceSilenced: boolean;
  iceStaggered: boolean;
} {
  let burnDamagePlayer = 0;
  let burnDamageIce = 0;
  let bleedDamagePlayer = 0;
  let bleedDamageIce = 0;
  let healPlayer = 0;
  let healIce = 0;
  let playerStunned = false;
  let playerSilenced = false;
  let playerStaggered = false;
  let playerFatigued = false;
  let playerConfused = false;
  let playerTerrified = false;
  let iceStunned = false;
  let iceSilenced = false;
  let iceStaggered = false;

  for (const e of state.statusEffects) {
    const isPlayer = e.target === "player";

    switch (e.kind) {
      case "burn":
        if (isPlayer) burnDamagePlayer += e.magnitude;
        else burnDamageIce += e.magnitude;
        break;

      case "bleed":
        if (isPlayer) bleedDamagePlayer += e.dotDamage ?? e.magnitude;
        else bleedDamageIce += e.dotDamage ?? e.magnitude;
        break;

      case "regen":
        {
          let healAmount = e.healPerTick ?? 0;
          if (healAmount > 0 && isMutatorActive(state as unknown as MutableRunState, "no_heal")) {
            healAmount = 0;
          }
          if (isPlayer) healPlayer += healAmount;
          else healIce += healAmount;
        }
        break;

      case "stun":
        if (isPlayer) playerStunned = true;
        else iceStunned = true;
        break;

      case "silence":
        if (isPlayer) playerSilenced = true;
        else iceSilenced = true;
        break;

      case "stagger":
        if (isPlayer) playerStaggered = true;
        else iceStaggered = true;
        break;

      case "fatigue":
        if (isPlayer) playerFatigued = true;
        break;

      case "confused":
        if (isPlayer) playerConfused = true;
        break;

      case "terrified":
        if (isPlayer) playerTerrified = true;
        break;

      // slow, vulnerable, powered, weakened: no tick action, caller reads for damage calc
      case "slow":
      case "vulnerable":
      case "powered":
      case "weakened":
        break;
    }
  }

  return {
    state,
    burnDamagePlayer,
    burnDamageIce,
    bleedDamagePlayer,
    bleedDamageIce,
    healPlayer,
    healIce,
    playerStunned,
    playerSilenced,
    playerStaggered,
    playerFatigued,
    playerConfused,
    playerTerrified,
    iceStunned,
    iceSilenced,
    iceStaggered,
  };
}

/** Apply burn/bleed damage and regen healing to state. Returns updated GameState with modified HP. */
export function applyBurnDamage(
  state: GameState,
  playerDmg: number,
  iceDmg: number,
  playerHeal = 0,
  iceHeal = 0,
): GameState {
  let next = state;

  const netPlayerChange = playerHeal - playerDmg;
  if (netPlayerChange !== 0) {
    const newHp = Math.max(0, Math.min(next.player.maxHp, next.player.hp + netPlayerChange));
    next = { ...next, player: { ...next.player, hp: newHp } };
  }

  if ((iceDmg > 0 || iceHeal > 0) && next.iceRoster.length > 0 && next.activeIceIndex < next.iceRoster.length) {
    const netIceChange = iceHeal - iceDmg;
    if (netIceChange !== 0) {
      const newRoster = next.iceRoster.map((ice, i) => {
        if (i !== next.activeIceIndex) return ice;
        const newHp = Math.max(0, ice.hp + netIceChange);
        return { ...ice, hp: newHp };
      });
      next = { ...next, iceRoster: newRoster };
    }
  }

  return next;
}

/** Roll whether a status effect procs after an attack. MVP: 20% chance per effect kind.
 *
 * Uses an injectable RNG function (defaults to Math.random) so tests can
 * deterministically test the state machine without flaky random failures.
 */
export function rollStatusProc(_kind: StatusEffectKind, rng: () => number = Math.random): boolean {
  return rng() < 0.2;
}