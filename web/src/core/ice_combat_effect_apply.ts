/** ICE-side non-damaging skill *application* — ADR-0219 Option A.
 *
 * The per-effect mechanics live here; the shared state helpers (pool / bonus
 * readers, damage absorption, enemy-tick advance) live in
 * `ice_combat_effects.ts`. Split per the ADR-0110 module-size guidance.
 */
import type { GameState, Ice, StatusEffectInstance } from "./types.ts";
import {
  ICE_BUFF_DURATION_TICKS,
  ICE_NON_DAMAGE_EFFECTS,
  ICE_REGEN_DURATION_TICKS,
  ICE_SHIELD_DURATION_TICKS,
  healIce,
  replaceEffect,
  type IceEffectOutcome,
  type IceEffectSkill,
} from "./ice_combat_effects.ts";

/** Apply an ICE's non-damaging skill to the given roster slot.
 *
 * Returns the unchanged state and a `null` message when the skill's effect is
 * not one this module implements (the effect stays inert).
 */
export function applyIceNonDamageEffect(
  state: GameState,
  iceIndex: number,
  ice: Ice,
  skill: IceEffectSkill,
): IceEffectOutcome {
  const magnitude = skill.magnitude ?? 0;
  if (!ICE_NON_DAMAGE_EFFECTS.has(skill.effect) || magnitude <= 0) {
    return { state, message: null };
  }

  if (skill.effect === "shield") {
    return applyShield(state, iceIndex, ice, magnitude);
  }
  if (skill.effect === "heal") {
    return applyHeal(state, iceIndex, ice, magnitude);
  }
  if (skill.effect === "regen") {
    return applyRegen(state, iceIndex, ice, magnitude);
  }
  return applyBuff(state, iceIndex, ice, magnitude);
}

function applyShield(
  state: GameState,
  iceIndex: number,
  ice: Ice,
  magnitude: number,
): IceEffectOutcome {
  const existingIndex = state.statusEffects.findIndex(
    (e) => e.kind === "shield" && e.iceIndex === iceIndex,
  );
  if (existingIndex < 0) {
    const effect: StatusEffectInstance = {
      kind: "shield",
      remaining: ICE_SHIELD_DURATION_TICKS,
      magnitude,
      target: "ice",
      iceIndex,
      tickSource: "enemy",
    };
    return {
      state: { ...state, statusEffects: [...state.statusEffects, effect] },
      message: `>>> ${ice.name} raises a ${magnitude} pt shield`,
    };
  }
  // Re-cast: the pool grows, the lifetime refreshes (depth.md TC-DEPTH-004).
  const existing = state.statusEffects[existingIndex];
  if (!existing) {
    return { state, message: null };
  }
  const next: StatusEffectInstance = {
    ...existing,
    magnitude: existing.magnitude + magnitude,
    remaining: ICE_SHIELD_DURATION_TICKS,
  };
  return {
    state: replaceEffect(state, existingIndex, next),
    message: `>>> ${ice.name} reinforces its shield to ${next.magnitude} pt`,
  };
}

function applyHeal(
  state: GameState,
  iceIndex: number,
  ice: Ice,
  magnitude: number,
): IceEffectOutcome {
  const { ice: healedIce, healed } = healIce(ice, magnitude);
  const roster = state.iceRoster.map((entry, i) =>
    i === iceIndex ? healedIce : entry,
  );
  return {
    state: { ...state, iceRoster: roster },
    message:
      healed > 0
        ? `>>> ${ice.name} restores ${healed} HP`
        : `>>> ${ice.name} is already at full integrity`,
  };
}

function applyRegen(
  state: GameState,
  iceIndex: number,
  ice: Ice,
  magnitude: number,
): IceEffectOutcome {
  const existingIndex = state.statusEffects.findIndex(
    (e) => e.kind === "regen" && e.iceIndex === iceIndex,
  );
  if (existingIndex < 0) {
    const effect: StatusEffectInstance = {
      kind: "regen",
      remaining: ICE_REGEN_DURATION_TICKS,
      magnitude,
      target: "ice",
      iceIndex,
      tickSource: "enemy",
      healPerTick: magnitude,
    };
    return {
      state: { ...state, statusEffects: [...state.statusEffects, effect] },
      message: `>>> ${ice.name} begins regenerating ${magnitude} HP per tick`,
    };
  }
  const existing = state.statusEffects[existingIndex];
  if (!existing) {
    return { state, message: null };
  }
  const next: StatusEffectInstance = {
    ...existing,
    magnitude,
    remaining: ICE_REGEN_DURATION_TICKS,
    healPerTick: magnitude,
  };
  return {
    state: replaceEffect(state, existingIndex, next),
    message: `>>> ${ice.name} renews its regeneration`,
  };
}

function applyBuff(
  state: GameState,
  iceIndex: number,
  ice: Ice,
  magnitude: number,
): IceEffectOutcome {
  const existingIndex = state.statusEffects.findIndex(
    (e) => e.kind === "powered" && e.iceIndex === iceIndex,
  );
  if (existingIndex < 0) {
    const effect: StatusEffectInstance = {
      kind: "powered",
      remaining: ICE_BUFF_DURATION_TICKS,
      magnitude,
      target: "ice",
      iceIndex,
      tickSource: "enemy",
      attackBonus: magnitude,
    };
    return {
      state: { ...state, statusEffects: [...state.statusEffects, effect] },
      message: `>>> ${ice.name} empowers its attacks (+${magnitude})`,
    };
  }
  const existing = state.statusEffects[existingIndex];
  if (!existing) {
    return { state, message: null };
  }
  const next: StatusEffectInstance = {
    ...existing,
    magnitude,
    remaining: ICE_BUFF_DURATION_TICKS,
    attackBonus: magnitude,
  };
  return {
    state: replaceEffect(state, existingIndex, next),
    message: `>>> ${ice.name} empowers its attacks (+${magnitude})`,
  };
}

