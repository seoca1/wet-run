import { describe, expect, it } from "vitest";
import {
  ENCOUNTER_ICE_BY_GRADE,
  clampGrade,
  encounterIceIdForGrade,
  iceDmgBonusPctForGrade,
  iceHpForGrade,
  missionGradeOf,
  missionSeedOf,
} from "../src/core/ice_scaling";
import { generateProceduralMatrix, resolveMatrixRoster } from "../src/core/matrix";
import { loadIceCatalog } from "../src/core/data_loaders";
import type { Ice } from "../src/core/types";
import iceTypesJson from "../src/data/ice_types.json";

const catalog = loadIceCatalog(iceTypesJson);

describe("ice_scaling", () => {
  it("clamps grade to 1..6", () => {
    expect(clampGrade(0)).toBe(1);
    expect(clampGrade(9)).toBe(6);
    expect(clampGrade(3.4)).toBe(3);
  });

  it("maps grade to a tier-appropriate encounter ICE (no seed → legacy first id)", () => {
    expect(encounterIceIdForGrade(1)).toBe("watchdog");
    expect(encounterIceIdForGrade(2)).toBe("spider");
    expect(encounterIceIdForGrade(3)).toBe("black");
    expect(encounterIceIdForGrade(4)).toBe("goliath");
    expect(encounterIceIdForGrade(5)).toBe("neuromancer");
    expect(encounterIceIdForGrade(6)).toBe("neuromancer");
  });

  it("rotates deterministically by seed (same seed → same id)", () => {
    expect(encounterIceIdForGrade(1, 0)).toBe(encounterIceIdForGrade(1, 0));
    expect(encounterIceIdForGrade(1, 7)).toBe(encounterIceIdForGrade(1, 7));
    expect(encounterIceIdForGrade(3, 9999)).toBe(encounterIceIdForGrade(3, 9999));
  });

  it("covers every band id across a small seed range", () => {
    for (let g = 1; g <= 6; g += 1) {
      const band = ENCOUNTER_ICE_BY_GRADE[g] ?? [];
      const seen = new Set<string>();
      for (let s = 0; s < band.length * 4; s += 1) {
        seen.add(encounterIceIdForGrade(g, s));
      }
      for (const id of band) {
        expect(seen.has(id), `band ${g} missing id ${id}`).toBe(true);
      }
    }
  });

  it("treats negative seeds as well-defined (Math.abs modulo band length)", () => {
    const band = ENCOUNTER_ICE_BY_GRADE[1] ?? [];
    expect(encounterIceIdForGrade(1, -1)).toBe(band[1] ?? band[0]);
    expect(encounterIceIdForGrade(1, band.length)).toBe(band[0] ?? "watchdog");
  });

  it("clamps out-of-range grades to the 1..6 band", () => {
    expect(encounterIceIdForGrade(0, 0)).toBe(encounterIceIdForGrade(1, 0));
    expect(encounterIceIdForGrade(99, 0)).toBe(encounterIceIdForGrade(6, 0));
  });

  it("caps encounter HP at the per-grade curve (never above the ICE's own ramp)", () => {
    const ice = catalog["standard"] as Ice;
    const hp1 = iceHpForGrade(ice, 1);
    const hp4 = iceHpForGrade(ice, 4);
    expect(hp4).toBeGreaterThan(hp1);
    expect(hp1).toBeLessThanOrEqual(ice.hpBase ?? Number.POSITIVE_INFINITY);
    expect(hp4).toBeLessThanOrEqual((ice.hpBase ?? 0) + (ice.hpPerGrade ?? 0) * 3);
  });

  it("keeps HP monotonic non-decreasing across grades for every band id", () => {
    for (let g = 1; g < 6; g += 1) {
      const ids = ENCOUNTER_ICE_BY_GRADE[g] ?? [];
      for (const id of ids) {
        const ice = catalog[id];
        if (ice === undefined) continue;
        const lower = iceHpForGrade(ice, g);
        const upper = iceHpForGrade(ice, g + 1);
        expect(
          upper,
          `${id} grade ${g + 1} (${upper}) should be >= grade ${g} (${lower})`,
        ).toBeGreaterThanOrEqual(lower);
      }
    }
  });

  it("falls back to a finite HP when scaling fields are missing", () => {
    expect(iceHpForGrade({ id: "x", name: "X", hp: 77, armor: 0, tier: 1 }, 3)).toBe(77);
    expect(iceHpForGrade({ id: "x", name: "X", hp: Number.NaN, armor: 0, tier: 1 }, 3)).toBe(100);
  });

  it("applies a negative ICE dmg modifier at the g6 climax", () => {
    // The g6 band is tanky enough that the developed deck flatlined at the HP
    // cap; the climax needs an ICE dmg penalty (a higher cap is forbidden by
    // the HP monotonicity invariant) to stay attainable.
    expect(iceDmgBonusPctForGrade(6)).toBeLessThan(0);
    expect(iceDmgBonusPctForGrade(5)).toBe(0);
  });

  it("reads grade with the grade_max -> grade_min -> grade fallback", () => {
    expect(missionGradeOf({ grade_max: 5 })).toBe(5);
    expect(missionGradeOf({ grade_min: 3 })).toBe(3);
    expect(missionGradeOf({ grade: 2 })).toBe(2);
    expect(missionGradeOf({})).toBe(1);
  });

  it("reads the mission seed with matrix_seed → seed → 42 fallback", () => {
    expect(missionSeedOf({ matrix_seed: 7 })).toBe(7);
    expect(missionSeedOf({ seed: 11 })).toBe(11);
    expect(missionSeedOf({})).toBe(42);
    expect(missionSeedOf({ seed: 5, matrix_seed: 9 })).toBe(9);
  });
});

describe("grade-driven encounters in the procedural matrix", () => {
  it("places a band ICE from the grade-5 set and returns grade-scaled HP", () => {
    const matrix = generateProceduralMatrix(5, 42);
    const idx = matrix.nodes.findIndex((n) => n.iceIds.length > 0 && !n.isBoss);
    expect(idx).toBeGreaterThanOrEqual(0);
    const roster = resolveMatrixRoster(matrix, idx, catalog);
    const ice = roster.ice[0] as Ice;
    const grade5Band = ENCOUNTER_ICE_BY_GRADE[5] ?? [];
    expect(grade5Band).toContain(ice.id);
    // HP is bounded by the encounter cap regardless of which band id was chosen
    // — this is the variety-vs-budget invariant. The grade-5 cap is 165 (same
    // as g4) so `ENCOUNTER_HP_BY_GRADE` stays monotonically non-decreasing
    // (tested by `keeps HP monotonic non-decreasing across grades for every
    // band id` above); the g6 dmg penalty in `ice_scaling.ts` — not a higher
    // cap — is what lets the PPL deck hit its 25-45% target at g6.
    expect(roster.hp[0]).toBe(iceHpForGrade(ice, 5));
    expect(roster.hp[0]).toBeLessThanOrEqual(165);
    expect(roster.hp[0]).toBeGreaterThanOrEqual(50);
  });

  it("uses a band ICE (tier-1 catalog) for low grades", () => {
    const matrix = generateProceduralMatrix(1, 42);
    const idx = matrix.nodes.findIndex((n) => n.iceIds.length > 0 && !n.isBoss);
    expect(idx).toBeGreaterThanOrEqual(0);
    const roster = resolveMatrixRoster(matrix, idx, catalog);
    const id = roster.ice[0]?.id;
    const grade1Band = ENCOUNTER_ICE_BY_GRADE[1] ?? [];
    expect(grade1Band, "grade-1 band must exist").not.toEqual([]);
    expect(grade1Band).toContain(id);
    expect(catalog[id ?? ""]?.tier).toBeLessThanOrEqual(1);
  });

  it("rotates band pick with the seed (different seeds → at least one different pick)", () => {
    const grade1Band = ENCOUNTER_ICE_BY_GRADE[1] ?? [];
    const ids = new Set<string>();
    for (let s = 0; s < grade1Band.length; s += 1) {
      const matrix = generateProceduralMatrix(1, s);
      const idx = matrix.nodes.findIndex((n) => n.iceIds.length > 0 && !n.isBoss);
      if (idx < 0) continue;
      const roster = resolveMatrixRoster(matrix, idx, catalog);
      const id = roster.ice[0]?.id;
      if (id !== undefined) ids.add(id);
    }
    expect(ids.size).toBeGreaterThan(1);
  });

  it("keeps boss rooms on wintermute (does not rotate boss ICE)", () => {
    const matrix = generateProceduralMatrix(5, 42);
    const boss = matrix.nodes[matrix.bossNode];
    expect(boss).toBeDefined();
    expect(boss?.iceIds[0]).toBe("wintermute");
  });
});
