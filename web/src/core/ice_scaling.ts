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

export function iceHpForGrade(ice: Ice, grade: number): number {
  const base = ice.hpBase;
  const perGrade = ice.hpPerGrade;
  if (base !== undefined && perGrade !== undefined) {
    return base + perGrade * (clampGrade(grade) - 1);
  }
  return Number.isFinite(ice.hp) ? ice.hp : 100;
}

export function missionGradeOf(mission: {
  readonly grade?: number;
  readonly grade_max?: number;
  readonly grade_min?: number;
}): number {
  return mission.grade_max ?? mission.grade_min ?? mission.grade ?? 1;
}
