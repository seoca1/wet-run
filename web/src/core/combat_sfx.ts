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
import { SFX_IDS } from "../audio/manager.ts";
import type { SoundEffectId } from "../audio/manager.ts";
import type { GameState } from "./types.ts";

/** Minimal shape the helper needs from a `GameState`. */
type CombatSnapshot = Pick<GameState, "phase" | "player" | "iceRoster" | "activeIceIndex">;

function activeIceHp(state: CombatSnapshot): number {
  const active = state.iceRoster[state.activeIceIndex];
  return active !== undefined ? active.hp : state.iceRoster[0]?.hp ?? 0;
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
