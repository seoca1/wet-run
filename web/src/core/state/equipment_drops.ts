/** Equipment the loot stop can drop, by mission grade (ADR-0329).
 *
 * ADR-0325 gave equipment a craft path, but the proposal asked for three
 * (`craft / drop / buy`). This is the drop half: a won fight can offer the
 * grade's own piece. Crafting stays the guaranteed route; a drop is the
 * roguelike find — the thing a run can stumble into.
 *
 * The roll is DETERMINISTIC and consumes no `Math.random`. It is seeded from
 * (mission seed, turn, node) — the same pattern `offeredCardIds` uses — so the
 * combat RNG stream, and therefore every recorded balance curve, is unchanged.
 */
import { clampGrade, missionGradeOf, missionSeedOf } from "../combat/ice_scaling";
import { makeMulberry32 } from "../dungeon/dungeon";
import type { GameState } from "../types";

/** Which piece each grade can drop. A grade without an entry drops nothing. */
export const EQUIPMENT_DROP_BY_GRADE: Readonly<Record<number, string>> = Object.freeze({
  1: "eyes_militech",
  2: "bodysuit_subdermal",
  3: "deck_militech",
  5: "deck_ghost",
  6: "deck_master",
});

/** Chance a mission of the drop's grade offers it. Placeholder — measured. */
export const EQUIPMENT_DROP_CHANCE = 0.4;

/** The piece a mission of this grade can drop, or null. */
export function equipmentDropForGrade(grade: number): string | null {
  return EQUIPMENT_DROP_BY_GRADE[clampGrade(grade)] ?? null;
}

type DropSource = Pick<GameState, "mission" | "droppedEquipment">;

/** FNV-1a over the mission id — mixes in a value that varies per mission, so
 *  the roll does not inherit `matrix_seed`'s clustering.
 *
 *  A third, deliberately unrelated hash: the dungeon seeds use `h * 31 + char`
 *  (`applyMissionIdSeed`, `createRng`) and this one is FNV-1a. Do not merge them
 *  — the value IS the design (refactor 2026-11-24). */
function hashString(s: string): number {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < s.length; i += 1) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619) >>> 0;
  }
  return h >>> 0;
}

/** The piece this mission offers at its loot stops, or null.
 *
 * One roll per MISSION, keyed on the mission seed + id — so the chance is
 * exactly `EQUIPMENT_DROP_CHANCE` (not once per fight), the same mission always
 * offers the same piece, and nothing is offered once the run has taken it. */
export function offeredEquipmentDrop(state: DropSource): string | null {
  const id = equipmentDropForGrade(missionGradeOf(state.mission));
  if (id === null) return null;
  if ((state.droppedEquipment ?? []).includes(id)) return null;
  const seed = (missionSeedOf(state.mission) ^ hashString(state.mission.id) ^ 0x9e3779b9) >>> 0;
  const rng = makeMulberry32(seed);
  return rng() < EQUIPMENT_DROP_CHANCE ? id : null;
}
