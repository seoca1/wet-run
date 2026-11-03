/** P5 — combat SFX layering.
 *
 * `SFX_IDS.DAMAGE` / `SFX_IDS.ATTACK` / `SFX_IDS.ICE_BREAK` are defined in
 * `src/audio/manager.ts` and their WAV files exist under
 * `web/public/sounds/sfx/`, but nothing ever played them — the
 * "built-but-unwired" class the proposal calls out as U13 (§1.2).
 *
 * This module owns the *decision*: which SFX ids should sound for a given
 * state transition. It is a pure function over (previous, next) so it can
 * be unit-tested without an AudioContext, and so the audio layer stays a
 * thin dispatcher (as it already is in `main.ts`).
 *
 * Layering discipline (proposal P5):
 * - the player taking damage gets its own `DAMAGE` sound — until now the
 *   player was hit in silence;
 * - an ICE hit layers `ATTACK` on top of the existing `COMBAT_HIT` so the
 *   impact has thickness, with no duplicate ids in one transition;
 * - a defeated ICE gets `ICE_BREAK` on top of the hit.
 */
import { SFX_IDS } from "../../audio/manager";
import type { SoundEffectId } from "../../audio/manager";
import type { GameState } from "../types";

/** Minimal shape the helper needs from a `GameState`. */
type CombatSnapshot = Pick<
  GameState,
  "phase" | "player" | "iceRoster" | "activeIceIndex"
>;

function activeIceHp(state: CombatSnapshot): number {
  const active = state.iceRoster[state.activeIceIndex];
  return active !== undefined ? active.hp : (state.iceRoster[0]?.hp ?? 0);
}

/**
 * Pick the SFX ids that should sound for a (previous → next) transition.
 *
 * Returns an empty array when nothing audible changed. The list is
 * de-duplicated and its order is the intended playback order (base layer
 * first, accent layer second).
 */
export function pickCombatSfxLayers(
  previous: CombatSnapshot,
  next: CombatSnapshot,
): ReadonlyArray<SoundEffectId> {
  const layers: SoundEffectId[] = [];
  const inCombat = previous.phase === "combat" && next.phase === "combat";

  if (!inCombat) return layers;

  // The player took damage — a dedicated sound, previously silent.
  if (next.player.hp < previous.player.hp) {
    layers.push(SFX_IDS.DAMAGE);
  }

  const prevIceHp = activeIceHp(previous);
  const nextIceHp = activeIceHp(next);
  if (nextIceHp < prevIceHp) {
    // Impact thickness: the existing hit sound plus an attack layer.
    layers.push(SFX_IDS.COMBAT_HIT);
    layers.push(SFX_IDS.ATTACK);
    if (nextIceHp <= 0 && prevIceHp > 0) {
      layers.push(SFX_IDS.ICE_BREAK);
    }
  }

  return [...new Set(layers)];
}

/** Slice of state the event picker reads. */
type EventSnapshot = Pick<
  GameState,
  "phase" | "runPhase" | "player" | "bossPhase" | "inventory"
>;

function materialCount(state: EventSnapshot): number {
  return Object.values(state.inventory.materials).reduce(
    (sum, n) => sum + n,
    0,
  );
}

/**
 * ADR-0251 slice B — sound ids that existed in `SFX_IDS` but were never
 * dispatched, each wired to the one real transition it names:
 *
 * - `BOSS_INTRO`   — a fight starts with a boss phase set (boss node breach);
 * - `PHASE_CHANGE` — the boss phase advances mid-fight;
 * - `CREDIT_GAIN`  — `player.credits` rises (victory reward, achievements);
 * - `LOOT_DROP`    — material counts rise (loot rolled on a kill);
 * - `HEAL`         — player HP rises while alive (loot-screen heal);
 * - `DEATH`        — player HP reaches 0 (FLATLINE). Jacking out is not a
 *   death and stays silent here (`DEFEAT` still plays on the phase change).
 *
 * `CREDIT_SPEND` is deliberately absent: no in-game action lowers
 * `player.credits` (`purchaseItem` has no caller), so there is no event to
 * name. ADR-0261 adds `EQUIP` on deck growth. Pure over (previous, next);
 * no RNG, no clock.
 */
export function pickEventSfx(
  previous: EventSnapshot,
  next: EventSnapshot,
): ReadonlyArray<SoundEffectId> {
  const ids: SoundEffectId[] = [];
  if (
    previous.runPhase !== "combat" &&
    next.runPhase === "combat" &&
    next.bossPhase > 0
  ) {
    ids.push(SFX_IDS.BOSS_INTRO);
  } else if (previous.bossPhase > 0 && next.bossPhase > previous.bossPhase) {
    ids.push(SFX_IDS.PHASE_CHANGE);
  }
  if (next.player.credits > previous.player.credits) {
    ids.push(SFX_IDS.CREDIT_GAIN);
  }
  if (materialCount(next) > materialCount(previous)) {
    ids.push(SFX_IDS.LOOT_DROP);
  }
  // ADR-0261: the run gained a program — the growth moment gets its own
  // sound. `EQUIP` was defined with a WAV but never dispatched; a new card
  // joining the deck is exactly what it names.
  if (next.inventory.programs.length > previous.inventory.programs.length) {
    ids.push(SFX_IDS.EQUIP);
  }
  if (previous.player.hp > 0 && next.player.hp > previous.player.hp) {
    ids.push(SFX_IDS.HEAL);
  }
  if (previous.player.hp > 0 && next.player.hp <= 0) {
    ids.push(SFX_IDS.DEATH);
  }
  return ids;
}

/** Everything a (previous → next) transition should sound: the combat
 * layers first, then the event ids, de-duplicated. */
export function pickTransitionSfx(
  previous: CombatSnapshot & EventSnapshot,
  next: CombatSnapshot & EventSnapshot,
): ReadonlyArray<SoundEffectId> {
  return [
    ...new Set([
      ...pickCombatSfxLayers(previous, next),
      ...pickEventSfx(previous, next),
    ]),
  ];
}
