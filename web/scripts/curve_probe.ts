/** Curve probe — both difficulty metrics in one pass (ADR-0280).
 *
 * The per-encounter curve and the mission-completion curve are different
 * measurements of the same tuning:
 *
 *   p(g)  per-encounter win rate, the balance harness's metric. It starts every
 *         encounter at FULL HP and stops at the win, so it cannot see damage
 *         carried forward.
 *   m(g)  mission completion, i.e. whether the runner finishes the whole mission.
 *
 * Tuning to `m` alone is what produced an INVERTED per-encounter curve in
 * ADR-0280 §5 (g4 7.2% while g6 sat at 99.3%). This probe exists so a search can
 * enforce `p` monotonic non-increasing while optimising `m`, which is the
 * experiment the Manus review ranked first and that had not actually been run.
 *
 *   npx tsx scripts/curve_probe.ts            # both metrics, all grades
 *   npx tsx scripts/curve_probe.ts --csv      # machine-readable for a driver
 */
import { loadIceCatalog, loadMissionsCatalog, loadProgramsCatalog } from "../src/core/data_loaders";
import { runSuite } from "./balance_sim";
import { startingDeck } from "../src/core/state/starting_deck";
import { mulberry32, playRun } from "./play_policy";
import type { Mission } from "../src/core/types";
import iceJson from "../src/data/ice_types.json" with { type: "json" };
import missionsJson from "../src/data/missions.json" with { type: "json" };
import programsJson from "../src/data/programs.json" with { type: "json" };

const CSV = process.argv.includes("--csv");
const runsIdx = process.argv.indexOf("--runs");
const PER_ENCOUNTER_RUNS = runsIdx >= 0 ? Number(process.argv[runsIdx + 1]) || 100 : 100;
const SEEDS = Number(
  process.argv[process.argv.indexOf("--seeds") + 1] ?? 14,
) || 14;

const ice = loadIceCatalog(iceJson);
const programs = loadProgramsCatalog(programsJson);
const missions = loadMissionsCatalog(missionsJson);
const openingDeck = startingDeck(programs, "novice");

// Mirror `balance_harness.ts`: bucket by `mission.grade`, aggregate wins.
const byGrade = new Map<number, Mission[]>();
for (const m of missions) {
  const grade = m.grade ?? 1;
  const bucket = byGrade.get(grade);
  if (bucket === undefined) byGrade.set(grade, [m]);
  else bucket.push(m);
}

const rows: Array<{ grade: number; missions: number; p: number; m: number }> = [];

for (const grade of [...byGrade.keys()].sort((a, b) => a - b)) {
  const bucket = byGrade.get(grade) ?? [];
  let wins = 0;
  let runs = 0;
  for (const mission of bucket) {
    const stats = runSuite(
      mission,
      ice,
      openingDeck,
      PER_ENCOUNTER_RUNS,
      1,
      undefined,
      0,
    );
    wins += stats.wins;
    runs += stats.runs;
  }
  const p = runs > 0 ? wins / runs : 0;

  let completed = 0;
  let missionRuns = 0;
  const originalRandom = Math.random;
  const originalNow = Date.now;
  try {
    for (let s = 0; s < SEEDS; s += 1) {
      Math.random = mulberry32(20261106 + s * 7919 + grade);
      const clockRef = { now: 1_700_000_000_000 + s * 100_000 + grade };
      Date.now = () => clockRef.now;
      for (const mission of bucket) {
        const final = playRun(mission, ice, programs, clockRef);
        if (final?.runPhase === "ending") completed += 1;
        missionRuns += 1;
      }
    }
  } finally {
    Math.random = originalRandom;
    Date.now = originalNow;
  }
  const m = missionRuns > 0 ? completed / missionRuns : 0;

  rows.push({ grade, missions: bucket.length, p, m });
}

if (CSV) {
  console.log("grade,missions,p,m");
  for (const r of rows) {
    console.log(
      `${r.grade},${r.missions},${(r.p * 100).toFixed(1)},${(r.m * 100).toFixed(1)}`,
    );
  }
} else {
  console.log(
    `curve probe — ${SEEDS} seeds/mission, ${PER_ENCOUNTER_RUNS} runs/encounter`,
  );
  console.log("");
  console.log("grade  missions   p (per encounter)   m (mission)   target m");
  const targets: Record<number, number> = {
    1: 100, 2: 95, 3: 80, 4: 50, 5: 25, 6: 10,
  };
  for (const r of rows) {
    const target = targets[r.grade] ?? 0;
    console.log(
      `  ${r.grade}      ${String(r.missions).padStart(2)}        ${(r.p * 100).toFixed(1).padStart(5)}%            ${(r.m * 100).toFixed(1).padStart(5)}%        ${String(target).padStart(4)}%`,
    );
  }
  const ps = rows.map((r) => r.p);
  const monotone = ps.every((v, i) => i === 0 || ps[i - 1] >= v);
  console.log("");
  console.log(
    `p monotonic non-increasing: ${monotone ? "yes" : "NO -- ADR-0229 violated"}`,
  );
}