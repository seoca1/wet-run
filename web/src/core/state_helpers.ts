/** State helper utilities — extracted from state.ts per ADR-0110.
 *
 * Contains VFX creation helpers, duration lookups, and other utility functions
 * used by state actions.
 */

const WEB_TICK_MS = 16;

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

/** Canonical duration in ticks for a VFX kind. */
export function durationForKind(kind: import("../renderer/combat_vfx.js").CombatVfxKind): number {
  switch (kind) {
    case "attack": return 3;
    case "heavy_attack": return 9;
    case "pierce": return 4;
    case "multi_hit": return 4;
    case "dot": return 7;
    case "shield": return 4;
    case "heal": return 4;
    case "regen": return 6;
    case "buff": return 3;
    case "debuff": return 3;
    case "stun": return 4;
    case "counter": return 6;
    case "lifesteal": return 7;
    case "detect": return 7;
    case "ice_hit": return 2;
    case "player_hit": return 3;
    case "critical_hit": return 4;
    case "status_apply": return 3;
    case "ice_intro": return 8;
    case "ice_death": return 8;
    case "boss_phase_transition": return 5;
    case "victory": return 5;
    case "defeat": return 5;
    case "jackin_glitch": return 7;
    case "jackout_whiteout": return 5;
    case "room_flash": return 1;
    case "data_acquired": return 7;
  }
}

/** Canonical duration in milliseconds for a VFX kind. */
export function durationMsForKind(kind: import("../renderer/combat_vfx.js").CombatVfxKind): number {
  switch (kind) {
    case "attack": return 240;
    case "heavy_attack": return 900;
    case "pierce": return 310;
    case "multi_hit": return 290;
    case "dot": return 550;
    case "shield": return 280;
    case "heal": return 320;
    case "regen": return 450;
    case "buff": return 240;
    case "debuff": return 240;
    case "stun": return 320;
    case "counter": return 420;
    case "lifesteal": return 490;
    case "detect": return 550;
    case "ice_hit": return 160;
    case "player_hit": return 200;
    case "critical_hit": return 320;
    case "status_apply": return 240;
    case "ice_intro": return 640;
    case "ice_death": return 640;
    case "boss_phase_transition": return 800;
    case "victory": return 800;
    case "defeat": return 800;
    case "jackin_glitch": return 500;
    case "jackout_whiteout": return 400;
    case "room_flash": return 80;
    case "data_acquired": return 500;
  }
}
