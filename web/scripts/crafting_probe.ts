/** Crafting probe — does the drop economy support Manus's candidate recipes?
 *
 * `crafting-recipes-candidate.json` holds the cost table under test. The Manus
 * v1 table (lifted from `docs/design/crafting-and-equipment-proposal-2026-11-18.md`
 * with its equipment names mapped to the real catalog ids) was falsified by
 * measurement — 18/18 recipes at 0.0%. The file now holds the **v2** table
 * (ADR-0324), which this probe passes. It is still a CANDIDATE list: re-running
 * it after any economy change is the point.
 *
 * ADR-0322 / the Manus proposal (`docs/design/crafting-and-equipment-
 * proposal-2026-11-18.md`). Manus could not see the repo, so its recipe costs
 * are candidates. This replays existing deterministic seeds and measures:
 *
 *   1. what a run at each grade actually yields (materials + credits)
 *   2. `craftableAtTier`: P(afford the recipe after k runs at the recipe's own
 *      grade) — a gate is measured against the grade it gates, not a pool
 *      diluted by lower grades that never drop it
 *   3. `commonPileup`: are data_fragment / ice_shard earned faster than any
 *      recipe consumes them?
 *
 * Nothing is implemented — this only reads.
 *
 *   npx tsx scripts/crafting_probe.ts [--seeds 16] [--runs 3]
 */
import { loadIceCatalog, loadMissionsCatalog, loadProgramsCatalog } from "../src/core/data_loaders";
import { missionGradeOf } from "../src/core/combat/ice_scaling";
import { mulberry32, playRun } from "./play_policy";
import iceJson from "../src/data/ice_types.json" with { type: "json" };
import missionsJson from "../src/data/missions.json" with { type: "json" };
import programsJson from "../src/data/programs.json" with { type: "json" };
import recipesJson from "./crafting-recipes-candidate.json" with { type: "json" };

const arg = (name: string, dflt: number): number => {
  const i = process.argv.indexOf(name);
  const v = i >= 0 ? Number(process.argv[i + 1]) : Number.NaN;
  return Number.isFinite(v) && v > 0 ? v : dflt;
};
const SEEDS = arg("--seeds", 16);
const RUNS = arg("--runs", 3);

const ice = loadIceCatalog(iceJson);
const missions = loadMissionsCatalog(missionsJson);
const programs = loadProgramsCatalog(programsJson);
const ALL = Object.values(missions) as Array<{ id: string; source_universe?: string }>;
const BASE = 20261106;
const clockRef = { now: 1_700_000_000_000 };

type Recipe = {
  readonly id: string;
  readonly manusId: string;
  readonly tier: number;
  readonly path: string;
  readonly cost: Readonly<Record<string, number>>;
  readonly cost_?: Readonly<Record<string, number>>;
};
const RECIPES = (recipesJson as unknown as Recipe[]).filter((r) =>
  Object.keys(r.cost).length > 0,
);

/** One run's outcome: what it banked. */
interface Yield {
  readonly credits: number;
  readonly materials: Readonly<Record<string, number>>;
  readonly won: boolean;
}

function playOne(mission: unknown, seed: number): Yield {
  const idx = ALL.indexOf(mission as never);
  Math.random = mulberry32(BASE + seed * 7919 + idx * 31);
  clockRef.now += 60_000;
  const final = playRun(
    mission as never,
    ice,
    programs,
    clockRef,
    "novice",
    "best",
    "opening",
    "long",
    "value",
    0,
    0,
    0,
    "stim",
    0,
    12,
    false,
  );
  if (!final) return { credits: 0, materials: {}, won: false };
  return {
    credits: final.player.credits,
    materials: final.inventory.materials as Readonly<Record<string, number>>,
    won: final.runPhase === "ending",
  };
}

function addYield(a: Yield, b: Yield): Yield {
  const m: Record<string, number> = { ...a.materials };
  for (const [k, v] of Object.entries(b.materials)) m[k] = (m[k] ?? 0) + v;
  return { credits: a.credits + b.credits, materials: m, won: a.won || b.won };
}

const EMPTY: Yield = { credits: 0, materials: {}, won: false };
const median = (xs: readonly number[]): number => {
  if (xs.length === 0) return 0;
  const s = [...xs].sort((a, b) => a - b);
  const mid = Math.floor(s.length / 2);
  return s.length % 2 ? (s[mid] as number) : ((s[mid - 1] as number) + (s[mid] as number)) / 2;
};

/** Does `wallet` cover `cost`? */
function affords(wallet: Readonly<Record<string, number>>, cost: Readonly<Record<string, number>>): boolean {
  for (const [k, v] of Object.entries(cost)) if ((wallet[k] ?? 0) < v) return false;
  return true;
}

function main(): void {
  // For each grade: k independent runs, summed (the menu-preservation model).
  const byGrade = new Map<number, Yield[]>();
  const materialKeys = new Set<string>();
  let runs = 0;
  for (const grade of [1, 2, 3, 4, 5, 6]) {
    const bucket = ALL.filter(
      (m) => m.source_universe !== "far-grid" && missionGradeOf(m as never) === grade,
    );
    const totals: Yield[] = [];
    for (let s = 0; s < SEEDS; s += 1) {
      for (const mission of bucket) {
        let acc: Yield = EMPTY;
        for (let k = 0; k < RUNS; k += 1) {
          acc = addYield(acc, playOne(mission, s * 131 + k * 17));
          runs += 1;
        }
        totals.push(acc);
        for (const key of Object.keys(acc.materials)) materialKeys.add(key);
      }
    }
    byGrade.set(grade, totals);
  }

  console.log(
    `crafting probe — ${SEEDS} seeds x ${RUNS} runs, carry-on, policy best/value, ${runs} runs total`,
  );
  console.log("");

  // 1. what a grade banks over RUNS runs
  const KEY_MATS = ["data_fragment", "ice_shard", "combat_module", "construct_shard", "ice_construct", "rom_echo", "loa_chip", "upgrade_t2", "upgrade_t4", "t4_program", "t5_program", "t6_program"];
  console.log(`median banked over ${RUNS} run(s), by grade`);
  console.log(`grade  credits  ${KEY_MATS.map((k) => k.slice(0, 8).padStart(8)).join("")}`);
  for (const grade of [1, 2, 3, 4, 5, 6]) {
    const totals = byGrade.get(grade) ?? [];
    const cells = KEY_MATS.map((k) =>
      median(totals.map((t) => t.materials[k] ?? 0)).toFixed(0).padStart(8),
    );
    console.log(
      `  ${grade}    ${median(totals.map((t) => t.credits)).toFixed(0).padStart(6)}  ${cells.join("")}`,
    );
  }
  console.log("");

  // 2. reach: can a run at this grade (or below) afford the recipe?
  console.log("recipe reach — P(afford) after this many runs at the recipe's own tier");
  console.log("item                    tier  P@runs  n  (cost)");
  for (const recipe of RECIPES) {
    // Judge a tier-T recipe against grade-T runs. The previous model pooled
    // every grade <= T, which made a rare, grade-localized gate (e.g. the
    // g6-only `t6_program`) mathematically unreachable — the pool was diluted
    // by low grades that never drop it. A gate is meaningful only against the
    // grade it is meant to gate. (Owner decision 2026-11-18.)
    const pool = byGrade.get(recipe.tier) ?? [];
    const reach = pool.length === 0 ? 0 : pool.filter((t) => affords(t.materials, recipe.cost)).length / pool.length;
    const cost = Object.entries(recipe.cost)
      .map(([k, v]) => `${k}x${v}`)
      .join(" ");
    console.log(
      `  ${recipe.id.padEnd(22)}${String(recipe.tier).padStart(3)}  ${(reach * 100).toFixed(1).padStart(6)}%  ${String(pool.length).padStart(3)}  ${cost}`,
    );
  }
  console.log("");

  // 3. pileup: earned vs what a full 18-item craft plan consumes
  const consumed: Record<string, number> = {};
  for (const r of RECIPES) {
    for (const [k, v] of Object.entries(r.cost)) consumed[k] = (consumed[k] ?? 0) + v;
  }
  console.log("common pileup — median banked at g3-g6 (3 runs) vs the whole 18-item craft plan");
  for (const k of ["data_fragment", "ice_shard", "combat_module", "construct_shard"]) {
    const pool: Yield[] = [];
    for (const grade of [3, 4, 5, 6]) pool.push(...(byGrade.get(grade) ?? []));
    const banked = median(pool.map((t) => t.materials[k] ?? 0));
    const need = consumed[k] ?? 0;
    console.log(
      `  ${k.padEnd(16)} banked ${banked.toFixed(1).padStart(7)}   craft-plan needs ${String(need).padStart(4)}   ${banked >= need ? "enough" : "SHORT"}`,
    );
  }
  console.log("");
  console.log("NOTE: materials reset every mission today (`startNextLeg` rebuilds the");
  console.log("inventory from the leg's reward) and never reach the menu wallet. This");
  console.log("model assumes the Manus proposal — a preserved wallet across runs.");
}

main();
