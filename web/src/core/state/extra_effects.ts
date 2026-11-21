/** The equipment `extraEffect` whitelist (ADR-0332).
 *
 * `extraEffect` is free text authored on each piece ("Immune to flatline (one
 * revive per run)"). The proposal's rule is that it is **never executed** — only
 * resolved through this whitelist — so a typo, a renamed string, or a hostile
 * value can do nothing but resolve to no effect. Every behaviour has a name
 * here; anything else is inert.
 *
 * Matching is by SUBSTRING, because `addStats` joins the effects of every
 * equipped piece with ", " — so one string can name several behaviours.
 */
import type { GameState } from "../types";

export type ExtraEffectId =
  | "revive_once"
  | "nano_regen"
  | "matrix_stealth"
  | "matrix_speed"
  | "zion_support"
  | "ice_omniscience";

/** Authored marker → behaviour. Order is the resolution order. */
const WHITELIST: ReadonlyArray<{
  readonly marker: string;
  readonly id: ExtraEffectId;
}> = Object.freeze([
  Object.freeze({ marker: "Immune to flatline", id: "revive_once" }),
  Object.freeze({ marker: "Heals 2 HP per turn", id: "nano_regen" }),
  Object.freeze({ marker: "+Stealth in Matrix", id: "matrix_stealth" }),
  Object.freeze({ marker: "+Movement speed (Matrix)", id: "matrix_speed" }),
  Object.freeze({ marker: "Connects to Zion mainframe", id: "zion_support" }),
  Object.freeze({ marker: "Sees through all ICE", id: "ice_omniscience" }),
]);

/** Every behaviour an effect string names. Unknown text resolves to nothing. */
export function resolveExtraEffects(effect: string): ReadonlyArray<ExtraEffectId> {
  if (effect.length === 0) return [];
  const out: ExtraEffectId[] = [];
  for (const { marker, id } of WHITELIST) {
    if (effect.includes(marker)) out.push(id);
  }
  return Object.freeze(out);
}

/** True when the effect string names this behaviour. */
export function hasExtraEffect(effect: string, id: ExtraEffectId): boolean {
  return resolveExtraEffects(effect).includes(id);
}

/** True when the equipped loadout grants this behaviour. */
export function loadoutHasEffect(state: GameState, id: ExtraEffectId): boolean {
  return hasExtraEffect(state.equipmentLoadout.totalStats().extraEffect, id);
}

/** HP `nano_regen` returns each enemy phase (the authored "2 HP per turn"). */
export const NANO_REGEN_HP = 2;

/** HP the one revive comes back with, as a percent of max HP. */
export const REVIVE_HP_PCT = 30;
