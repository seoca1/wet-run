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
import {
  mulberry32,
  playRun,
  type CardPolicy,
  type LootPolicy,
  type RoutePolicy,
} from "./play_policy";
import type { PrepChoice } from "../src/core/state/prep";
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
/** Where losses happen: the exit room (the apex ICE) or a normal encounter.
 * ADR-0280 found the boss was the whole loss mode once, so this is the first
 * thing to look at when a grade misses its target. */
const SHOW_DEATHS = process.argv.includes("--deaths");
/** Card-offer policy: `first` (take anything) or `best` (spend the choice). */
const limitIdx = process.argv.indexOf("--ice-limit");
/** ADR-0287: what `picky` is willing to fight (tier + armour). */
const ICE_LIMIT = limitIdx >= 0 ? Number(process.argv[limitIdx + 1]) || 12 : 12;
const hpIdx = process.argv.indexOf("--hp");
/** ADR-0283 (C'): extra starting max HP from prep. */
const HP_BONUS = hpIdx >= 0 ? Number(process.argv[hpIdx + 1]) || 0 : 0;
const walletIdx = process.argv.indexOf("--wallet");
/** ADR-0284: the prep stockpile's balance, for measuring its curve impact. */
const WALLET = walletIdx >= 0 ? Number(process.argv[walletIdx + 1]) || 0 : 0;
const prepIdx = process.argv.indexOf("--prep");
/** ADR-0283 C''': which prep option the advance buys. */
const PREP_CHOICE: PrepChoice =
  prepIdx >= 0 && process.argv[prepIdx + 1] === "ice" ? "ice" : "stim";
const shieldIdx = process.argv.indexOf("--shield");
/** ADR-0283 (C''): starting shield pool from prep. */
const SHIELD_BONUS = shieldIdx >= 0 ? Number(process.argv[shieldIdx + 1]) || 0 : 0;
const handIdx = process.argv.indexOf("--hand");
/** ADR-0283 (C'): extra hand slots from prep. */
const HAND_BONUS = handIdx >= 0 ? Number(process.argv[handIdx + 1]) || 0 : 0;
const lootIdx = process.argv.indexOf("--loot");
const LOOT_POLICY: LootPolicy =
  lootIdx >= 0 &&
  ["card", "repair", "smart", "intel"].includes(process.argv[lootIdx + 1] ?? "")
    ? (process.argv[lootIdx + 1] as LootPolicy)
    : "card";
const routeIdx = process.argv.indexOf("--route");
const ROUTE_POLICY: RoutePolicy =
  routeIdx >= 0 &&
  ["short", "intel", "picky"].includes(process.argv[routeIdx + 1] ?? "")
    ? (process.argv[routeIdx + 1] as RoutePolicy)
    : "long";
const deckIdx = process.argv.indexOf("--deck");
const DECK_MODE: "opening" | "ppl" =
  deckIdx >= 0 && process.argv[deckIdx + 1] === "ppl" ? "ppl" : "opening";
const cardsIdx = process.argv.indexOf("--cards");
const CARD_POLICY: CardPolicy =
  cardsIdx >= 0 && process.argv[cardsIdx + 1] === "best" ? "best" : "first";
/** Restrict the sweep to one grade — a probe for tuning, ~1s instead of ~15. */
const onlyIdx = process.argv.indexOf("--grade");
const ONLY_GRADE = onlyIdx >= 0 ? Number(process.argv[onlyIdx + 1]) : null;
const BASE_SEED = 20261106;

const ice = loadIceCatalog(iceJson);
const programs = loadProgramsCatalog(programsJson);
const missions = loadMissionsCatalog(missionsJson);

const originalRandom = Math.random;
const originalNow = Date.now;

type Cell = { completed: number; runs: number };
const byGrade = new Map<number, Cell>();
const byGradeMission = new Map<string, Cell>();
const deaths = new Map<string, number>();

try {
  for (let s = 0; s < SEEDS; s += 1) {
    const seed = BASE_SEED + s * 7919;
    Math.random = mulberry32(seed);
    const clockRef = { now: 1_700_000_000_000 + s * 100_000 };
    Date.now = () => clockRef.now;

    for (const mission of Object.values(missions) as Mission[]) {
      const grade = missionGradeOf(mission);
      if (ONLY_GRADE !== null && grade !== ONLY_GRADE) continue;
      const final = playRun(
        mission,
        ice,
        programs,
        clockRef,
        "novice",
        CARD_POLICY,
        DECK_MODE,
        ROUTE_POLICY,
        LOOT_POLICY,
        HP_BONUS,
        HAND_BONUS,
        SHIELD_BONUS,
        PREP_CHOICE,
        WALLET,
        ICE_LIMIT,
      );
      const completed = final?.runPhase === "ending" ? 1 : 0;
      const g = byGrade.get(grade) ?? { completed: 0, runs: 0 };
      g.completed += completed;
      g.runs += 1;
      byGrade.set(grade, g);
      const atBoss = final?.matrix?.nodes[final.currentNodeIndex]?.isBoss === true;
      const where = completed === 1 ? "finished" : atBoss ? "boss" : "normal";
      deaths.set(`${grade}|${where}`, (deaths.get(`${grade}|${where}`) ?? 0) + 1);
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
  `mission survival — ${SEEDS} seeds x ${Object.keys(missions).length} missions, policy "expensive", cards "${CARD_POLICY}", deck "${DECK_MODE}", route "${ROUTE_POLICY}", loot "${LOOT_POLICY}", hp +${HP_BONUS}, hand +${HAND_BONUS}, prep "${PREP_CHOICE}", wallet ${WALLET}, jockey "novice"`,
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

if (SHOW_DEATHS) {
  console.log("");
  console.log("where losses happen:");
  console.log("grade  finished  lost:boss  lost:normal  boss share");
  for (const grade of [...byGrade.keys()].sort((a, b) => a - b)) {
    const f = deaths.get(`${grade}|finished`) ?? 0;
    const b = deaths.get(`${grade}|boss`) ?? 0;
    const n = deaths.get(`${grade}|normal`) ?? 0;
    const share = b + n > 0 ? `${((b / (b + n)) * 100).toFixed(0)}%` : "-";
    console.log(
      `  ${grade}      ${String(f).padStart(4)}      ${String(b).padStart(4)}       ${String(n).padStart(4)}        ${share}`,
    );
  }
}

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
