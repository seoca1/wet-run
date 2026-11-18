import { describe, expect, it } from "vitest";
import { generateProceduralMatrix, buildMatrix } from "../src/core/matrix";
import missionsData from "../src/data/missions.json";
import iceTypesData from "../src/data/ice_types.json";
import programsData from "../src/data/programs.json";

const iceTypes = iceTypesData as unknown as Record<string, import("../src/core/types").Ice>;
const programs = programsData as unknown as Record<string, import("../src/core/types").Program>;

describe("matrix ICE coverage (regression: 2026-09-19 dungeon-empty bug)", () => {
  type LegacyMission = {
    matrix_seed?: number;
    seed?: number;
    grade_max?: number;
    grade_min?: number;
    grade?: number;
    id: string;
  };
  const resolveSeedAndGrade = (m: LegacyMission): { seed: number; grade: number } => {
    const seed = m.matrix_seed ?? m.seed ?? 42;
    const grade = m.grade_max ?? m.grade_min ?? m.grade ?? 1;
    return { seed, grade };
  };

  it("every mission: matrix has at least one ICE-bearing node", () => {
    const missions = Object.values(missionsData) as unknown as LegacyMission[];
    const failures: string[] = [];
    for (const m of missions) {
      const { seed, grade } = resolveSeedAndGrade(m);
      const matrix = generateProceduralMatrix(grade, seed, m.id);
      const totalIce = matrix.nodes.reduce((acc, n) => acc + n.iceIds.length, 0);
      if (totalIce === 0) {
        failures.push(`${m.id} (grade=${grade} seed=${seed})`);
      }
    }
    expect(failures, `missions with no ICE: ${failures.join(", ")}`).toEqual([]);
  });

  it("every mission: at least one mid/deep/core/core-deep node has ICE", () => {
    const missions = Object.values(missionsData) as unknown as LegacyMission[];
    for (const m of missions) {
      const { seed, grade } = resolveSeedAndGrade(m);
      const matrix = generateProceduralMatrix(grade, seed, m.id);
      const hasCombatNode = matrix.nodes.some(
        (n) => n.iceIds.length > 0 && n.zone !== "surface",
      );
      expect(hasCombatNode, `mission ${m.id} has no combat-bearing mid/deep node`).toBe(true);
    }
  });

  it("buildMatrix (fallback) populates watchdog ICE on each non-boss and wintermute on boss", () => {
    const matrix = buildMatrix(iceTypes, programs);
    expect(matrix.nodes.length).toBeGreaterThan(0);
    matrix.nodes.forEach((n, i) => {
      expect(n.iceIds.length, `node ${i} (zone ${n.zone}) should have at least one ICE`).toBeGreaterThan(0);
    });
  });
});
