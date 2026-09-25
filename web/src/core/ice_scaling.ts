/** Grade-driven ICE scaling — shared by the live combat path and the balance harness.
 *
 * `ice_types.json` carries `hp_base` + `hp_per_grade` per ICE; effective HP for a
 * mission grade is `hp_base + hp_per_grade * (grade - 1)`. The encounter ICE id
 * is chosen by grade tier so higher grades face harder ICE. Both fall back to
 * safe defaults (watchdog / ice.hp) for legacy rows that omit the fields.
 */
import type { Ice } from "./types.ts";

const ENCOUNTER_ICE_BY_GRADE: Readonly<Record<number, string>> = {
  1: "watchdog",
  2: "spider",
  3: "black",
  4: "goliath",
  5: "neuromancer",
  6: "neuromancer",
};

export function clampGrade(grade: number): number {
  const g = Number.isFinite(grade) ? Math.round(grade) : 1;
  return Math.max(1, Math.min(6, g));
}

export function encounterIceIdForGrade(grade: number): string {
  return ENCOUNTER_ICE_BY_GRADE[clampGrade(grade)] ?? "watchdog";
}

/** Encounter HP curve by grade (index = grade - 1). Calibrated to the opening
 * deck's measured damage budget (HP 50 -> ~100% win, HP 240 -> ~0%), so higher
 * grades are harder while every grade stays contestable. Replaces the raw
 * hp_base + hp_per_grade ramp, whose 50 -> 240 step produced a hard cliff.
 */
const ENCOUNTER_HP_BY_GRADE: ReadonlyArray<number> = [50, 85, 116, 118, 121, 124];

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
