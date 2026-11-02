/** The base ICE a mission's run is built from (moved from `main.ts`).
 *
 * Deterministic in the mission (its `ice_id`, else grade + seed), so the run
 * start and a CONTINUE derive the same ICE — and `encounterRoster`, which
 * spreads this ICE into every encounter, rebuilds the same fight (ADR-0252).
 */
import type { Ice, Mission } from "../types";
import {
  encounterIceIdForGrade,
  missionGradeOf,
  missionSeedOf,
} from "../combat/ice_scaling";

/** Pick the ICE type best matched to the mission's `ice_id` (fallback: first). */
export function missionIce(
  mission: Mission,
  iceTypes: Readonly<Record<string, Ice>>,
): Ice {
  const keys = Object.keys(iceTypes);
  const preferred = (mission as { ice_id?: string }).ice_id;
  const normalize = (raw: Ice): Ice => {
    // ice_types.json uses legacy Python field names (`defense`, `hp_base`,
    // `hp_per_grade`) and carries no precomputed `hp`. Normalize them so
    // combat math and grade scaling never receive undefined.
    const r = raw as Ice & {
      defense?: number;
      hp_base?: number;
      hp_per_grade?: number;
    };
    const armor = r.armor ?? r.defense ?? 0;
    const hpBase = r.hpBase ?? r.hp_base;
    const hpPerGrade = r.hpPerGrade ?? r.hp_per_grade;
    const hp = Number.isFinite(r.hp) ? r.hp : (hpBase ?? 100);
    return {
      ...r,
      armor,
      hp,
      ...(hpBase !== undefined ? { hpBase } : {}),
      ...(hpPerGrade !== undefined ? { hpPerGrade } : {}),
    };
  };
  if (preferred && preferred in iceTypes) {
    const ice = iceTypes[preferred];
    if (ice) return normalize(ice);
  }
  const graded =
    iceTypes[
      encounterIceIdForGrade(missionGradeOf(mission), missionSeedOf(mission))
    ];
  if (graded) return normalize(graded);
  const first = keys[0];
  if (!first) throw new Error("No ICE types in ice_types.json");
  const fallback = iceTypes[first];
  if (!fallback) throw new Error("ICE entry empty");
  return normalize(fallback);
}
