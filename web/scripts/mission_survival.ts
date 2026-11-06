/** Mission survival — the metric the grade curve is tuned against (ADR-0280).
 *
 * The project's recorded curve (`npm run balance`) is **per encounter**. A
 * mission is not one encounter: it averages 4.4 (max 10). So a grade sitting at
 * 47% per encounter reads as "hard fight" and behaves as "the mission is 96%
 * fatal" — and that gap stayed invisible while the enemy phase was gated by a
 * wall clock, because recorded play never matched the harness's time model.
 *
 * This measures the unit that matters: **did the runner finish the mission**.
 * Per grade, over many seeds, with the same policy the soak uses.
 *
 *   npm run survival                      # 20 seeds x 53 missions
 *   npm run survival -- --seeds 40
 *   npm run survival -- --by-grade        # one row per grade with targets
 *
 * Targets live in `GRADE_TARGETS` below and are what ADR-0280 tunes to.
 */
import { loadIceCatalog, loadMissionsCatalog, loadProgramsCatalog } from "../src/core/data_loaders";
import { missionGradeOf } from "../src/core/combat/ice_scaling";
import { mulberry32, playRun } from "./play_policy";
import type { Mission } from "../src/core/types";
import iceJson from "../src/data/ice_types.json" with { type: "json" };
import missionsJson from "../src/data/missions.json" with { type: "json" };
import programsJson from "../src/data/programs.json" with { type: "json" };

/** Target **mission completion** by grade (ADR-0280). The recorded per-encounter
 * curve cannot express this: it says nothing about how many fights a mission is. */
export const GRADE_TARGETS: Readonly<Record<number, number>> = {
  1: 1.0,
  2: 0.95,
  3: 0.8,
  4: 0.5,
  5: 0.25,
  6: 0.1,
};

/** Tolerance around a target before the sweep reports a miss. */
const TOLERANCE_PP = 8;

const seedArg = process.argv.indexOf("--seeds");
const SEEDS = seedArg >= 0 ? Number(process.argv[seedArg + 1]) || 20 : 20;
const BY_GRADE = process.argv.includes("--by-grade");
const BASE_SEED = 20261106;

const ice = loadIceCatalog(iceJson);
const programs = loadProgramsCatalog(programsJson);
const missions = loadMissionsCatalog(missionsJson);

const originalRandom = Math.random;
const originalNow = Date.now;

type Cell = { completed: number; runs: number };
const byGrade = new Map<number, Cell>();
const byGradeMission = new Map<string, Cell>();

try {
  for (let s = 0; s < SEEDS; s += 1) {
    const seed = BASE_SEED + s * 7919;
    Math.random = mulberry32(seed);
    const clockRef = { now: 1_700_000_000_000 + s * 100_000 };
    Date.now = () => clockRef.now;

    for (const mission of Object.values(missions) as Mission[]) {
      const grade = missionGradeOf(mission);
      const final = playRun(mission, ice, programs, clockRef);
      const completed = final?.runPhase === "ending" ? 1 : 0;
      const g = byGrade.get(grade) ?? { completed: 0, runs: 0 };
      g.completed += completed;
      g.runs += 1;
      byGrade.set(grade, g);
      const key = `${grade}|${mission.id}`;
      const m = byGradeMission.get(key) ?? { completed: 0, runs: 0 };
      m.completed += completed;
      m.runs += 1;
      byGradeMission.set(key, m);
    }
  }
} finally {
  Math.random = originalRandom;
  Date.now = originalNow;
}

console.log(
  `mission survival — ${SEEDS} seeds x ${Object.keys(missions).length} missions, policy "expensive", jockey "novice"`,
);
console.log("");
console.log("grade  missions  runs  completed  rate    target  delta");
let worst = 0;
for (const grade of [...byGrade.keys()].sort((a, b) => a - b)) {
  const cell = byGrade.get(grade) as Cell;
  const rate = cell.completed / cell.runs;
  const target = GRADE_TARGETS[grade] ?? 0;
  const delta = (rate - target) * 100;
  if (Math.abs(delta) > worst) worst = Math.abs(delta);
  const mark = Math.abs(delta) > TOLERANCE_PP ? "  <-- MISS" : "";
  const missionCount = [...byGradeMission.keys()].filter((k) =>
    k.startsWith(`${grade}|`),
  ).length;
  console.log(
    `  ${grade}      ${String(missionCount).padStart(2)}     ${String(cell.runs).padStart(4)}   ${String(cell.completed).padStart(4)}      ${(rate * 100).toFixed(1).padStart(5)}%  ${(target * 100).toFixed(0).padStart(4)}%  ${delta >= 0 ? "+" : ""}${delta.toFixed(1)}${mark}`,
  );
}
console.log("");
console.log(`worst miss: ${worst.toFixed(1)}pp (tolerance ${TOLERANCE_PP}pp)`);
console.log("invariant (ADR-0229): rates must be monotonic non-increasing by grade");

if (BY_GRADE) {
  console.log("");
  console.log("per mission (completed / runs):");
  for (const key of [...byGradeMission.keys()].sort()) {
    const [grade, id] = key.split("|");
    const cell = byGradeMission.get(key) as Cell;
    console.log(
      `  g${grade} ${id.padEnd(28)} ${(cell.completed / cell.runs * 100).toFixed(0).padStart(3)}%  (${cell.completed}/${cell.runs})`,
    );
  }
}
