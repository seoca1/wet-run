/**
 * Balance harness — prints a per-grade win-rate / turns-to-kill report.
 *
 * Usage:
 *   npm run balance              # default: 100 runs per mission
 *   npm run balance -- --runs 500
 *
 * The numbers come from the real reducer (see balance_sim.ts), so a constant
 * change in combat_engine.ts / boss_phases.ts shows up here immediately.
 */
import { loadIceCatalog, loadMissionsCatalog, loadProgramsCatalog } from "../src/core/data_loaders";
import { missionGradeOf } from "../src/core/ice_scaling";
import type { Mission, Program } from "../src/core/types";
import { deckForGrade, runSuite } from "./balance_sim";
import { installLocalStoragePolyfill } from "./node_polyfills";

import missionsJson from "../src/data/missions.json" with { type: "json" };
import iceTypesJson from "../src/data/ice_types.json" with { type: "json" };
import programsJson from "../src/data/programs.json" with { type: "json" };

function parseRuns(argv: ReadonlyArray<string>): number {
  const idx = argv.indexOf("--runs");
  const raw = idx >= 0 ? argv[idx + 1] : undefined;
  const parsed = raw === undefined ? Number.NaN : Number.parseInt(raw, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 100;
}

function parseDeck(argv: ReadonlyArray<string>): "opening" | "ppl" {
  const idx = argv.indexOf("--deck");
  return idx >= 0 && argv[idx + 1] === "ppl" ? "ppl" : "opening";
}

/** Same opening hand the game builds on NEW RUN (see main.ts loadDeck). */
function openingDeck(catalog: Readonly<Record<string, Program>>, size = 5): Program[] {
  return Object.keys(catalog)
    .sort()
    .slice(0, size)
    .map((id) => catalog[id])
    .filter((p): p is Program => p !== undefined);
}

function pct(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function pad(value: string, width: number): string {
  return value.padStart(width);
}

function main(): void {
  installLocalStoragePolyfill();
  const argv = process.argv.slice(2);
  const runs = parseRuns(argv);
  const deckMode = parseDeck(argv);
  const missions = loadMissionsCatalog(missionsJson);
  const iceCatalog = loadIceCatalog(iceTypesJson);
  const programCatalog = loadProgramsCatalog(programsJson);
  const deck = openingDeck(programCatalog);

  const byGrade = new Map<number, Mission[]>();
  for (const m of missions) {
    const grade = m.grade ?? 1;
    const bucket = byGrade.get(grade);
    if (bucket === undefined) byGrade.set(grade, [m]);
    else bucket.push(m);
  }

  console.log(
    deckMode === "ppl"
      ? "Balance harness — PPL deck (grade-appropriate: tier <= grade, top 5)"
      : `Balance harness — opening deck [${deck.map((p) => p.id).join(", ")}]`,
  );
  console.log(`Missions: ${missions.length}, ICE types: ${Object.keys(iceCatalog).length}, runs/mission: ${runs}\n`);
  console.log("grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95");

  for (const grade of [...byGrade.keys()].sort((a, b) => a - b)) {
    const bucket = byGrade.get(grade) ?? [];
    let wins = 0;
    let stalls = 0;
    let turns = 0;
    let hp = 0;
    let p5 = 0;
    let p95 = 0;

    for (const mission of bucket) {
      const deckForMission =
        deckMode === "ppl" ? deckForGrade(programCatalog, missionGradeOf(mission)) : deck;
      const stats = runSuite(mission, iceCatalog, deckForMission, runs, 1);
      wins += stats.wins;
      stalls += stats.stalls;
      turns += stats.meanTurns;
      hp += stats.meanHpEnd;
      p5 += stats.hpEndP5;
      p95 += stats.hpEndP95;
    }

    const count = bucket.length;
    const totalRuns = count * runs;
    console.log(
      `${pad(String(grade), 5)}  ${pad(String(count), 8)}  ${pad(pct(wins / totalRuns), 8)}  ` +
        `${pad(pct(stalls / totalRuns), 7)}  ${pad((turns / count).toFixed(1), 10)}  ` +
        `${pad((hp / count).toFixed(1), 11)}  ${pad(String(Math.round(p5 / count)), 3)}/${Math.round(p95 / count)}`,
    );
  }
}

main();
