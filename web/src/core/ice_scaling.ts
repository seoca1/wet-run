/** Grade-driven ICE scaling — shared by the live combat path and the balance harness.
 *
 * `ice_types.json` carries `hp_base` + `hp_per_grade` per ICE; effective HP for a
 * mission grade is `hp_base + hp_per_grade * (grade - 1)`. The encounter ICE id
 * is chosen from a per-grade band (3-4 ids) so the 97-type catalog actually
 * appears in play instead of always falling on a single tier-1 watchdog.
 * Pick is deterministic by `(grade, seed)`: a numeric `seed` selects via
 * `Math.abs(seed) % band.length`; omitting the seed pins index 0 so existing
 * callers and tests that do not pass a seed still see the legacy first id of
 * the band (watchdog @ grade 1, spider @ grade 2, black @ grade 3, goliath @
 * grade 4, neuromancer @ grade 5/6). Both fall back to safe defaults
 * (`watchdog` / `ice.hp`) for legacy rows that omit the fields.
 *
 * HP cap stays a single grade curve: `iceHpForGrade` clamps every band id to
 * the same per-grade ceiling, so the chosen id never raises HP above the
 * calibrated budget — only flavor (skills, dmg_base, speed, resistance) varies.
 */
import type { Ice } from "./types.ts";

/** Per-grade encounter bands.
 *
 * Each entry lists Gibson/Sprawl-flavored ids drawn from `ice_types.json`.
 * The first id of each band matches the legacy fixed-id behavior so callers
 * that omit a seed stay backward compatible. Boss rooms do NOT use this table
 * — `dungeon.ts` keeps the wintermute pinning for exit rooms.
 */
export const ENCOUNTER_ICE_BY_GRADE: Readonly<Record<number, ReadonlyArray<string>>> = {
  1: ["watchdog", "spider", "wisp", "zombie"],
  2: ["spider", "raven", "surveillance", "chinese_ice"],
  3: ["black", "goliath", "raven", "ai_whisper"],
  4: ["goliath", "ai_whisper", "hellhound", "morrison_echo"],
  5: ["neuromancer", "revelation", "loa_entity", "hellhound"],
  6: ["neuromancer", "wintermute", "ice_neuromancer_warden", "aleph"],
};

export function clampGrade(grade: number): number {
  const g = Number.isFinite(grade) ? Math.round(grade) : 1;
  return Math.max(1, Math.min(6, g));
}

/** Pick the encounter ICE id for a mission grade.
 *
 * When `seed` is `undefined`, returns the first id of the band (legacy
 * behavior, matches the original fixed-id table). When `seed` is a finite
 * number, returns `band[Math.abs(seed) % band.length]` — deterministic across
 * runs and independent of the date used elsewhere.
 *
 * Boss rooms are not routed through this function; callers gate on
 * `node.isBoss` and pin `wintermute` directly.
 */
export function encounterIceIdForGrade(grade: number, seed?: number): string {
  const band = ENCOUNTER_ICE_BY_GRADE[clampGrade(grade)];
  if (band === undefined || band.length === 0) return "watchdog";
  if (seed === undefined || !Number.isFinite(seed)) {
    return band[0] ?? "watchdog";
  }
  const idx = Math.abs(Math.trunc(seed)) % band.length;
  return band[idx] ?? "watchdog";
}

/** Encounter HP curve by grade (index = grade - 1). Calibrated to the opening
 * deck's measured damage budget (HP 50 -> ~100% win, HP 240 -> ~0%), so higher
 * grades are harder while every grade stays contestable. Replaces the raw
 * hp_base + hp_per_grade ramp, whose 50 -> 240 step produced a hard cliff.
 */
const ENCOUNTER_HP_BY_GRADE: ReadonlyArray<number> = [
  50, 85, 116, 118, 121, 124,
];

export function iceHpForGrade(ice: Ice, grade: number): number {
  const g = clampGrade(grade);
  const base = ice.hpBase;
  const perGrade = ice.hpPerGrade;
  const dataHp =
    base !== undefined && perGrade !== undefined
      ? base + perGrade * (g - 1)
      : Number.isFinite(ice.hp)
        ? ice.hp
        : 100;
  const cap = ENCOUNTER_HP_BY_GRADE[g - 1];
  return cap !== undefined ? Math.min(dataHp, cap) : dataHp;
}

export function missionGradeOf(mission: {
  readonly grade?: number;
  readonly grade_max?: number;
  readonly grade_min?: number;
}): number {
  return mission.grade_max ?? mission.grade_min ?? mission.grade ?? 1;
}

/** Resolve the seed the matrix generator uses for a mission.
 *
 * Mirrors the precedence applied by `state.ts` (`matrix_seed` first, then
 * `seed`, then a fixed default) so dungeon determinism propagates to the
 * encounter ICE pick: the same mission always faces the same ICE.
 */
export function missionSeedOf(mission: {
  readonly seed?: number;
  readonly matrix_seed?: number;
}): number {
  return (mission as { matrix_seed?: number }).matrix_seed ?? mission.seed ?? 42;
}
