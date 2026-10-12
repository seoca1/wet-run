/** Combat VFX core — effect taxonomy, instance model, and lifecycle.
 *
 * Split from combat_vfx.ts per ADR-0110 module-size policy. This module owns
 * the canonical effect taxonomy (ADR-0210, declared in src/data/effects.d.ts),
 * the per-instance animation model, and the spawn/advance/tick lifecycle.
 *
 * Rendering lives in combat_vfx_render_combat.ts (combat / damage / status)
 * and combat_vfx_render_scene.ts (ICE / boss / outcome / matrix). The public
 * entry point is the combat_vfx.ts barrel, which re-exports this module.
 */

export type CombatVfxKind =
  | "attack"
  | "heavy_attack"
  | "pierce"
  | "multi_hit"
  | "dot"
  | "shield"
  | "heal"
  | "regen"
  | "buff"
  | "debuff"
  | "stun"
  | "counter"
  | "lifesteal"
  | "detect"
  | "ice_hit"
  | "player_hit"
  | "critical_hit"
  | "status_apply"
  | "ice_intro"
  | "ice_death"
  | "boss_phase_transition"
  | "victory"
  | "defeat"
  | "jackin_glitch"
  | "jackout_whiteout"
  | "room_flash"
  | "data_acquired";

export interface CombatVfxInstance {
  readonly id: number;
  readonly kind: CombatVfxKind;
  /** Tick counter (0 = spawned, increments each draw). Derived from elapsedMs / WEB_TICK_MS. */
  readonly tick: number;
  /** Total ticks before expiration. Derived from durationMs / WEB_TICK_MS at spawn. */
  readonly duration: number;
  /** Total lifetime in milliseconds (canonical, derived from schema's duration_ms). */
  readonly durationMs: number;
  /** Wall-clock elapsed time in ms since spawn. Drives ms-precise expiry. */
  readonly elapsedMs: number;
  /** Optional metadata: program name, status kind, ice type, etc. */
  readonly payload: string;
  /** Numeric metadata: damage amount, boss phase, etc. Parsed as needed. */
  readonly payloadNum?: number;
  /** Optional row offset for movement effects (projectile). */
  readonly startRow?: number;
  readonly targetRow?: number;
}

/** Web frame budget (ms per tick). 16ms ≈ 60fps. */
export const WEB_TICK_MS = 16;

let nextVfxId = 1;

/** Create a new VFX instance (auto-assigns id, tick=0, elapsedMs=0). */
export function triggerCombatVfx(
  kind: CombatVfxKind,
  payload: string = "",
  duration: number = 4,
  startRow?: number,
  targetRow?: number,
  payloadNum?: number,
): CombatVfxInstance {
  const durationMs = Math.max(0, duration) * WEB_TICK_MS;
  return {
    id: nextVfxId++,
    kind,
    tick: 0,
    duration,
    durationMs,
    elapsedMs: 0,
    payload,
    payloadNum,
    startRow,
    targetRow,
  };
}

/** Create a VFX instance with explicit ms duration (ADR-0210 canonical).
 *
 * Use this when you have the schema's duration_ms value and want ms-precise
 * expiry. The `tick` and `duration` fields are derived for backward-compat
 * with the renderer switch (which reads tick to interpolate animation).
 */
export function triggerCombatVfxMs(
  kind: CombatVfxKind,
  payload: string = "",
  durationMs: number = 80,
  startRow?: number,
  targetRow?: number,
  payloadNum?: number,
): CombatVfxInstance {
  const clampedMs = Math.max(0, durationMs);
  const tickDuration = Math.ceil(clampedMs / WEB_TICK_MS);
  return {
    id: nextVfxId++,
    kind,
    tick: 0,
    duration: tickDuration,
    durationMs: clampedMs,
    elapsedMs: 0,
    payload,
    payloadNum,
    startRow,
    targetRow,
  };
}

/** Advance a VFX instance by `deltaMs` real-world milliseconds.
 *
 * Returns the updated instance, or null if it has reached its duration.
 * The `tick` field is derived from elapsedMs (floor(elapsedMs / WEB_TICK_MS))
 * so renderers stay frame-aligned.
 *
 * Tier 7: ms-precise expiry replaces the legacy tick-based advance.
 * Falls back to duration-based expiry when durationMs is 0 (legacy path).
 */
export function advanceVfxBy(
  instance: CombatVfxInstance,
  deltaMs: number,
): CombatVfxInstance | null {
  if (deltaMs < 0) return instance;
  const elapsedMs = instance.elapsedMs + deltaMs;
  // ms-precise expiry: drop when wall-clock exceeds durationMs.
  if (instance.durationMs > 0 && elapsedMs >= instance.durationMs) {
    return null;
  }
  // Legacy tick-based expiry (only if durationMs was unset = 0).
  const tick = Math.floor(elapsedMs / WEB_TICK_MS);
  if (instance.durationMs === 0 && tick >= instance.duration) {
    return null;
  }
  return { ...instance, elapsedMs, tick };
}

/** Tick a VFX instance. Returns the updated instance, or null if expired.
 *
 * Legacy API — increments tick by 1. Prefer advanceVfxBy(instance, deltaMs)
 * for ms-precise timing. Kept for backward compatibility with existing
 * call sites that don't have a deltaMs (e.g., headless test loops).
 */
export function tickCombatVfx(
  instance: CombatVfxInstance,
): CombatVfxInstance | null {
  return advanceVfxBy(instance, WEB_TICK_MS);
}

/** Advance a list of VFX instances by deltaMs. Returns survivors. */
export function advanceVfxListBy(
  list: ReadonlyArray<CombatVfxInstance>,
  deltaMs: number,
): ReadonlyArray<CombatVfxInstance> {
  return list
    .map((v) => advanceVfxBy(v, deltaMs))
    .filter((v): v is CombatVfxInstance => v !== null);
}

/** Tick a list of VFX instances by one tick (legacy API). */
export function tickCombatVfxList(
  list: ReadonlyArray<CombatVfxInstance>,
): ReadonlyArray<CombatVfxInstance> {
  return advanceVfxListBy(list, WEB_TICK_MS);
}

/** Shared render context passed to the per-concern VFX renderers.
 *
 * `t`, `dur`, and `progress` are derived once by the dispatcher so every
 * renderer interpolates against the same frame values.
 */
export interface VfxRenderCtx {
  readonly instance: CombatVfxInstance;
  readonly cols: number;
  readonly rows: number;
  readonly t: number;
  readonly dur: number;
  readonly progress: number;
}
