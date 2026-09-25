import { describe, expect, it } from "vitest";
import {
  clampGrade,
  encounterIceIdForGrade,
  iceHpForGrade,
  missionGradeOf,
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

  it("maps grade to a tier-appropriate encounter ICE", () => {
    expect(encounterIceIdForGrade(1)).toBe("watchdog");
    expect(encounterIceIdForGrade(5)).toBe("neuromancer");
    expect(encounterIceIdForGrade(6)).toBe("neuromancer");
  });

  it("caps encounter HP at the per-grade curve (never above the ICE's own ramp)", () => {
    const ice = catalog["standard"] as Ice;
    const hp1 = iceHpForGrade(ice, 1);
    const hp4 = iceHpForGrade(ice, 4);
    expect(hp4).toBeGreaterThan(hp1);
    expect(hp1).toBeLessThanOrEqual(ice.hpBase ?? Number.POSITIVE_INFINITY);
    expect(hp4).toBeLessThanOrEqual((ice.hpBase ?? 0) + (ice.hpPerGrade ?? 0) * 3);
  });

  it("falls back to a finite HP when scaling fields are missing", () => {
    expect(iceHpForGrade({ id: "x", name: "X", hp: 77, armor: 0, tier: 1 }, 3)).toBe(77);
    expect(iceHpForGrade({ id: "x", name: "X", hp: Number.NaN, armor: 0, tier: 1 }, 3)).toBe(100);
  });

  it("reads grade with the grade_max -> grade_min -> grade fallback", () => {
    expect(missionGradeOf({ grade_max: 5 })).toBe(5);
    expect(missionGradeOf({ grade_min: 3 })).toBe(3);
    expect(missionGradeOf({ grade: 2 })).toBe(2);
    expect(missionGradeOf({})).toBe(1);
  });
});

describe("grade-driven encounters in the procedural matrix", () => {
  it("places the grade-appropriate ICE and returns grade-scaled HP", () => {
    const matrix = generateProceduralMatrix(5, 42);
    const idx = matrix.nodes.findIndex((n) => n.iceIds.length > 0 && !n.isBoss);
    expect(idx).toBeGreaterThanOrEqual(0);
    const roster = resolveMatrixRoster(matrix, idx, catalog);
    const ice = roster.ice[0] as Ice;
    expect(ice.id).toBe("neuromancer");
    expect(roster.hp[0]).toBe(iceHpForGrade(ice, 5));
  });

  it("uses weaker ICE for low grades", () => {
    const matrix = generateProceduralMatrix(1, 42);
    const idx = matrix.nodes.findIndex((n) => n.iceIds.length > 0 && !n.isBoss);
    expect(idx).toBeGreaterThanOrEqual(0);
    const roster = resolveMatrixRoster(matrix, idx, catalog);
    expect(roster.ice[0]?.id).toBe("watchdog");
  });
});
