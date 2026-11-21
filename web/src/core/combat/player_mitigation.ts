// player_mitigation.ts — the player's side of damage mitigation (ADR-0255).
//
// ADR-0326 wired the missing defense step. Before it, an ICE hit went straight
// to the player's HP with only a shield pool in between, so the equipment's
// `defense` and `iceResistance` were dead numbers. The fixed order is:
//
//   raw → iceResistance (%) → defense (flat) → shield pool → HP
//
// The order matters: resistance is a share of the whole hit, defense is a flat
// subtraction after it, and the shield pool absorbs whatever is left. The ICE's
// armor is a separate axis (`attack_resolution.ts` / the card path) and never
// mixes with this one.
//
//   shield — an absorbing pool (the ICE already has one; `iceShieldPool`)
//
// **ADR-0321 moved `evasive` out of here.** It used to cut incoming damage by a
// flat percentage, which is a tax rather than a dodge. It is now the MISS
// chance in `attack_resolution.ts`, so `applyPlayerMitigation` runs AFTER the
// case roll and only spends the shield pool.

import type { GameState, StatusEffectInstance } from "../types";

/** Total absorb pool the player currently has from `shield` effects. */
export function playerShieldPool(state: GameState): number {
  return state.statusEffects
    .filter((e) => e.kind === "shield" && e.target === "player")
    .reduce((sum, e) => sum + e.magnitude, 0);
}

/** Incoming-damage reduction percent the player currently has. */
export function playerEvasionPct(state: GameState): number {
  return state.statusEffects
    .filter((e) => e.kind === "evasive" && e.target === "player")
    .reduce((sum, e) => sum + e.magnitude, 0);
}

/** Gear can never make the runner immune — resistance is a percent, capped. */
export const ICE_RESISTANCE_CAP_PCT = 75;

/** The equipment-derived defense the incoming path reads (ADR-0326). */
export interface PlayerDefense {
  /** Percent of incoming ICE damage removed before the flat `defense`. */
  readonly iceResistance: number;
  /** Flat damage removed after resistance. */
  readonly defense: number;
}

/** Resistance + defense from the equipped loadout. Empty loadout → both 0. */
export function playerDefense(state: GameState): PlayerDefense {
  const stats = state.equipmentLoadout.totalStats();
  return {
    iceResistance: Math.max(0, Math.min(ICE_RESISTANCE_CAP_PCT, stats.iceResistance)),
    defense: Math.max(0, stats.defense),
  };
}

/** `raw` minus a resistance percent, floored. A no-op for 0% / non-positive. */
export function applyIceResistance(raw: number, pct: number): number {
  if (raw <= 0) return 0;
  if (pct <= 0) return raw;
  return Math.max(0, Math.floor((raw * (100 - pct)) / 100));
}

export interface PlayerMitigationResult {
  readonly state: GameState;
  /** Damage that reaches the player's HP. */
  readonly damage: number;
  /** Damage the shield pool absorbed. */
  readonly absorbed: number;
  /** Damage removed by resistance + defense, before the shield pool. */
  readonly reduced: number;
  /** Always 0 since ADR-0321 — evasion is a MISS roll now, not a flat cut.
   * Kept so the shape of the result does not change under its callers. */
  readonly dodged: number;
}

/**
 * Apply the player's resistance, defense and shield pool to an incoming hit.
 *
 * The pool is spent down as it absorbs; the remaining pool is written back
 * so a partially used barrier keeps its remainder (ADR-0219's ICE shield
 * works the same way).
 */
export function applyPlayerMitigation(state: GameState, incoming: number): PlayerMitigationResult {
  if (incoming <= 0) {
    return { state, damage: 0, absorbed: 0, dodged: 0, reduced: 0 };
  }

  // ADR-0326: resistance, then flat defense, then the shield pool.
  const { iceResistance, defense } = playerDefense(state);
  const afterDefense = Math.max(0, applyIceResistance(incoming, iceResistance) - defense);
  const reduced = incoming - afterDefense;

  const pool = playerShieldPool(state);

  const absorbed = Math.min(pool, afterDefense);
  const remaining = afterDefense - absorbed;

  let next = state;
  if (absorbed > 0) {
    // Spend the pool across the player's shield effects, oldest first.
    let left = absorbed;
    const kept: StatusEffectInstance[] = [];
    for (const effect of state.statusEffects) {
      if (left <= 0 || effect.kind !== "shield" || effect.target !== "player") {
        kept.push(effect);
        continue;
      }
      const spend = Math.min(effect.magnitude, left);
      left -= spend;
      const rest = effect.magnitude - spend;
      if (rest > 0) {
        kept.push({ ...effect, magnitude: rest });
      }
    }
    next = { ...next, statusEffects: kept };
  }

  return { state: next, damage: remaining, absorbed, reduced, dodged: 0 };
}
