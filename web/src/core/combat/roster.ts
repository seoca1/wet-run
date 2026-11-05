/** Which ICE the screen should name.
 *
 * ADR-0278. `state.ice` is the run's *base* ICE — the one the mission opens
 * with. The encounter roster is a different list: the node's `iceIds` resolved
 * against the catalog. Naming the base ICE made the boss room announce
 * "Combat vs ICE — Wisp" and celebrate "ICE — Wisp defeated!" while the
 * opponent was the wintermute.
 *
 * These helpers read the roster, so the screen names who is actually in front
 * of the player. They are pure reads — no RNG, no clock.
 */
import type { GameState, Ice } from "../types";

/** The ICE the player is currently targeting. */
export function activeIceOf(state: GameState): Ice {
  return state.iceRoster[state.activeIceIndex] ?? state.ice;
}

/** The name of the ICE a victory refers to.
 *
 * Prefers the ICE that was just defeated (the last one to fall), so a
 * multi-ICE fight names a name that was actually killed. Falls back to the
 * active target when the roster is empty.
 */
export function defeatedIceName(
  state: GameState,
  defeated: ReadonlyArray<Ice> = [],
): string {
  const lastDefeated = defeated[defeated.length - 1];
  if (lastDefeated) return lastDefeated.name;
  const active = state.iceRoster[state.activeIceIndex];
  return active?.name ?? state.ice.name;
}
