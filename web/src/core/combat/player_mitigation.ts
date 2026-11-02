// player_mitigation.ts — the player's side of damage mitigation (ADR-0255).
//
// The ICE deals its damage straight at the player's HP: there was no
// defense step on that path. These programs need one, so it lives here
// rather than inside the enemy turn.
//
// Two kinds, both player-targeted status effects:
//   shield  — an absorbing pool (the ICE already has one; `iceShieldPool`)
//   evasive — incoming damage reduced by a percentage
//
// Order: the pool absorbs first, then the percentage applies to what is
// left. A discrete resource is spent before a continuous modifier runs.

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

export interface PlayerMitigationResult {
  readonly state: GameState;
  /** Damage that reaches the player's HP. */
  readonly damage: number;
  /** Damage the shield pool absorbed. */
  readonly absorbed: number;
  /** Damage the evasion percent removed. */
  readonly dodged: number;
}

/**
 * Apply the player's shield pool and evasion to an incoming hit.
 *
 * The pool is spent down as it absorbs; the remaining pool is written back
 * so a partially used barrier keeps its remainder (ADR-0219's ICE shield
 * works the same way).
 */
export function applyPlayerMitigation(
  state: GameState,
  incoming: number,
): PlayerMitigationResult {
  if (incoming <= 0) {
    return { state, damage: 0, absorbed: 0, dodged: 0 };
  }

  const pool = playerShieldPool(state);
  const evasionPct = playerEvasionPct(state);

  const absorbed = Math.min(pool, incoming);
  let remaining = incoming - absorbed;

  const dodged =
    evasionPct > 0 ? Math.floor((remaining * evasionPct) / 100) : 0;
  remaining -= dodged;

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

  return { state: next, damage: remaining, absorbed, dodged };
}
