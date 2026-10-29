/** State helper utilities — extracted from state.ts per ADR-0110.
 *
 * Contains VFX creation helpers, duration lookups, and other utility functions
 * used by state actions.
 */

const WEB_TICK_MS = 16;

/** Maximum number of combat log lines kept on `GameState.combatLog`. */
export const COMBAT_LOG_CAP = 8;

/** Create a VFX instance directly (tick-based duration). */
export function import_vfx(
  kind: import("../renderer/combat_vfx.js").CombatVfxKind,
  payload: string,
  duration: number,
  startRow?: number,
  targetRow?: number,
  payloadNum?: number,
): import("../renderer/combat_vfx.js").CombatVfxInstance {
  const durationMs = Math.max(0, duration) * WEB_TICK_MS;
  return {
    id: Math.floor(Math.random() * 1e9) + 1,
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

/** MS-precision variant: pass canonical duration_ms from schema. */
export function import_vfx_ms(
  kind: import("../renderer/combat_vfx.js").CombatVfxKind,
  payload: string,
  durationMs: number,
  startRow?: number,
  targetRow?: number,
  payloadNum?: number,
): import("../renderer/combat_vfx.js").CombatVfxInstance {
  const clampedMs = Math.max(0, durationMs);
  return {
    id: Math.floor(Math.random() * 1e9) + 1,
    kind,
    tick: 0,
    duration: Math.ceil(clampedMs / WEB_TICK_MS),
    durationMs: clampedMs,
    elapsedMs: 0,
    payload,
    payloadNum,
    startRow,
    targetRow,
  };
}

/** Content hash for a deterministic VFX id.
 *
 * A 31-bit FNV-1a over the spawn's own fields. Deterministic, RNG-free and
 * independent of how many VFX were spawned before — which is what keeps the
 * reducer pure (ADR-0231's global counter made two identical `applyAction`
 * calls produce different ids, breaking the reducer-determinism invariant in
 * `tests/property_reducer_fuzz.test.ts`).
 */
function deterministicVfxId(
  kind: string,
  payload: string,
  payloadNum: number | undefined,
  duration: number,
): number {
  let hash = 0x811c9dc5;
  const mix = (text: string): void => {
    for (let i = 0; i < text.length; i++) {
      hash ^= text.charCodeAt(i);
      hash = Math.imul(hash, 0x01000193) >>> 0;
    }
  };
  mix(kind);
  mix("|");
  mix(payload);
  mix("|");
  mix(String(payloadNum ?? ""));
  mix("|");
  mix(String(duration));
  // 0 is reserved for "no id" — shift into 1..2^31-1.
  return (hash % 2147483646) + 1;
}

/** Spawn a VFX instance without consuming a `Math.random` draw.
 *
 * The balance harness seeds `Math.random` with a PRNG, so every draw shifts
 * the seeded crit / proc / skill rolls and moves the ADR-0229 grade curve.
 * `import_vfx` draws its id from `Math.random`, which is fine for the spawn
 * sites that already existed (their draw count is baked into the recorded
 * baseline) but NOT for newly added ones — those would silently shift the
 * whole curve. New spawn sites use this helper so they stay RNG-neutral.
 *
 * The id is derived from the spawn's own content, so it is stable across
 * runs and independent of call order — two identical reducer calls produce
 * identical instances. Two spawns with identical content therefore share an
 * id; nothing reads `CombatVfxInstance.id` for logic (it is an identity key
 * only) and rendering composites by array order, not by id.
 */
export function import_vfx_deterministic(
  kind: import("../renderer/combat_vfx.js").CombatVfxKind,
  payload: string,
  duration: number,
  startRow?: number,
  targetRow?: number,
  payloadNum?: number,
): import("../renderer/combat_vfx.js").CombatVfxInstance {
  const durationMs = Math.max(0, duration) * WEB_TICK_MS;
  return {
    id: deterministicVfxId(kind, payload, payloadNum, duration),
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

/** Map a program to its primary VFX kind. */
export function pickProgramVfxKind(
  program: { tier: number; role?: string; effect?: string },
  damage: number,
): import("../renderer/combat_vfx.js").CombatVfxKind {
  if (program.effect === "noise_attraction") return "detect";
  if (program.effect === "reset_ap") return "buff";
  if (program.role === "strike") return "pierce";
  if (program.role === "burst" && damage >= 20) return "heavy_attack";
  if (program.role === "burst" && damage >= 10) return "multi_hit";
  if (program.role === "guard") return "shield";
  if (program.role === "support") return "regen";
  return "attack";
}

/** Tier 5 SFX mapping: pick the SFX id for a program outcome.
 *
 * Pure helper — returns one of the SFX_IDS strings (e.g. "sounds/sfx/...").
 * Logic:
 *  - damage === 0 with a non-support program → COMBAT_BLOCK
 *    (ICE had armor/guard reducing it; alternate would be heal/buff for
 *    pure defensive programs — but role-driven dispatch keeps it deterministic)
 *  - role === "strike" → COMBAT_SKILL_STRIKE
 *  - role === "burst"  → COMBAT_SKILL_BURST
 *  - role === "guard"  → COMBAT_SKILL_GUARD
 *  - role === "support" → COMBAT_SKILL_SUPPORT
 *  - default → COMBAT_HIT (matches existing behavior for non-typed programs)
 *
 * Callers (main.ts / state_actions_programs.ts) dispatch AudioManager.playSfx()
 * with the returned id; if the audio file is missing the call no-ops gracefully.
 */
export function pickProgramSfxId(
  program: { role?: string; effect?: string },
  damage: number,
): import("../audio/manager.ts").SoundEffectId {
  if (damage <= 0 && program.role !== "guard" && program.role !== "support") {
    return "sounds/sfx/combat_block.wav" as const;
  }
  switch (program.role) {
    case "strike":
      return "sounds/sfx/combat_skill_strike.wav" as const;
    case "burst":
      return "sounds/sfx/combat_skill_burst.wav" as const;
    case "guard":
      return "sounds/sfx/combat_skill_guard.wav" as const;
    case "support":
      return "sounds/sfx/combat_skill_support.wav" as const;
    default:
      return "sounds/sfx_combat_hit.wav" as const;
  }
}

/** Tier 5 SFX: pick the SFX id for a matrix movement (approach phase).
 *
 * Pure helper — returns one of the SFX_IDS strings. Callers dispatch
 * AudioManager.playSfx() with the returned id; missing files no-op gracefully.
 *
 * Logic:
 *  - forwardMove = true → MOVEMENT_STEP (room-to-room transition)
 *  - forwardMove = false → MOVEMENT_NODE (backtrack between distinct nodes)
 */
export function pickMovementSfxId(
  forwardMove: boolean,
): import("../audio/manager.ts").SoundEffectId {
  return forwardMove
    ? ("sounds/sfx/movement_step.wav" as const)
    : ("sounds/sfx/movement_node.wav" as const);
}

/** Canonical duration in ticks for a VFX kind. */
export function durationForKind(
  kind: import("../renderer/combat_vfx.js").CombatVfxKind,
): number {
  switch (kind) {
    case "attack":
      return 3;
    case "heavy_attack":
      return 9;
    case "pierce":
      return 4;
    case "multi_hit":
      return 4;
    case "dot":
      return 7;
    case "shield":
      return 4;
    case "heal":
      return 4;
    case "regen":
      return 6;
    case "buff":
      return 3;
    case "debuff":
      return 3;
    case "stun":
      return 4;
    case "counter":
      return 6;
    case "lifesteal":
      return 7;
    case "detect":
      return 7;
    case "ice_hit":
      return 2;
    case "player_hit":
      return 3;
    case "critical_hit":
      return 4;
    case "status_apply":
      return 3;
    case "ice_intro":
      return 8;
    case "ice_death":
      return 8;
    case "boss_phase_transition":
      return 5;
    case "victory":
      return 5;
    case "defeat":
      return 5;
    case "jackin_glitch":
      return 7;
    case "jackout_whiteout":
      return 5;
    case "room_flash":
      return 1;
    case "data_acquired":
      return 7;
  }
}

/** Canonical duration in milliseconds for a VFX kind. */
export function durationMsForKind(
  kind: import("../renderer/combat_vfx.js").CombatVfxKind,
): number {
  switch (kind) {
    case "attack":
      return 240;
    case "heavy_attack":
      return 900;
    case "pierce":
      return 310;
    case "multi_hit":
      return 290;
    case "dot":
      return 550;
    case "shield":
      return 280;
    case "heal":
      return 320;
    case "regen":
      return 450;
    case "buff":
      return 240;
    case "debuff":
      return 240;
    case "stun":
      return 320;
    case "counter":
      return 420;
    case "lifesteal":
      return 490;
    case "detect":
      return 550;
    case "ice_hit":
      return 160;
    case "player_hit":
      return 200;
    case "critical_hit":
      return 320;
    case "status_apply":
      return 240;
    case "ice_intro":
      return 640;
    case "ice_death":
      return 640;
    case "boss_phase_transition":
      return 800;
    case "victory":
      return 800;
    case "defeat":
      return 800;
    case "jackin_glitch":
      return 500;
    case "jackout_whiteout":
      return 400;
    case "room_flash":
      return 80;
    case "data_acquired":
      return 500;
  }
}
