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

/** Apply a new status effect to a target. Stacks (adds new instance) if same kind. */
export function applyStatus(
  state: GameState,
  target: "player" | "ice",
  kind: StatusEffectKind,
  duration: number,
  magnitude: number,
): GameState {
  const newEffect: StatusEffectInstance = {
    kind,
    remaining: duration,
    magnitude,
    target,
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

/** Apply DoT / slow / vulnerable effects at start of actor's turn.
 *
 * - burn: deals `magnitude` damage to target
 * - slow: reduces next attack damage by `magnitude`% (caller reads .slowActive)
 * - vulnerable: next attack against target deals +magnitude% damage (caller reads)
 * - stun: actor cannot act this turn (caller reads .stunned flag)
 * - silence: actor cannot use special skills this turn (caller reads)
 *
 * Returns { state, burnDamage } so caller can apply burn damage to HP.
 */
export function applyTickEffects(state: GameState): {
  state: GameState;
  burnDamagePlayer: number;
  burnDamageIce: number;
  playerStunned: boolean;
  playerSilenced: boolean;
  iceStunned: boolean;
  iceSilenced: boolean;
} {
  let burnDamagePlayer = 0;
  let burnDamageIce = 0;
  let playerStunned = false;
  let playerSilenced = false;
  let iceStunned = false;
  let iceSilenced = false;
  for (const e of state.statusEffects) {
    if (e.kind === "burn") {
      if (e.target === "player") burnDamagePlayer += e.magnitude;
      else burnDamageIce += e.magnitude;
    } else if (e.kind === "stun") {
      if (e.target === "player") playerStunned = true;
      else iceStunned = true;
    } else if (e.kind === "silence") {
      if (e.target === "player") playerSilenced = true;
      else iceSilenced = true;
    }
  }
  return { state, burnDamagePlayer, burnDamageIce, playerStunned, playerSilenced, iceStunned, iceSilenced };
}

/** Apply burn damage to state. Returns updated GameState with reduced HP. */
export function applyBurnDamage(
  state: GameState,
  playerDmg: number,
  iceDmg: number,
): GameState {
  let next = state;
  if (playerDmg > 0) {
    next = { ...next, player: { ...next.player, hp: Math.max(0, next.player.hp - playerDmg) } };
  }
  if (iceDmg > 0 && next.iceRoster.length > 0 && next.activeIceIndex < next.iceRoster.length) {
    // Apply to active ICE only (MVP). Multi-enemy: each ICE tracks own HP separately.
    const newRoster = next.iceRoster.map((ice, i) => {
      if (i !== next.activeIceIndex) return ice;
      return { ...ice, hp: Math.max(0, ice.hp - iceDmg) };
    });
    next = { ...next, iceRoster: newRoster };
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