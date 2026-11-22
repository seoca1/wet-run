#!/usr/bin/env tsx
/**
 * Mutation spike (ADR-0333).
 *
 * The test suite is the project's real verification, so "all green" only means
 * something if the tests can actually fail. This flips a few load-bearing
 * constants in the combat engine one at a time and runs the focused tests that
 * claim to cover them. A mutation the tests do NOT catch (SURVIVED) is a hole
 * in the safety net, not a bug in this script.
 *
 * Usage:
 *   npm run mutation                 # default mutation set + focused tests
 *   npm run mutation -- --tests tests/combat_engine.test.ts
 *
 * Exit codes: 0 = every mutation killed, 1 = at least one survived, 2 = error.
 */
import { execFileSync } from "node:child_process";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { fileURLToPath } from "node:url";

const WEB_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

const COMBAT = "src/core/combat/combat_engine.ts";
const ENDING = "src/core/combat/ending_resolver.ts";
const WALLET = "src/core/state/wallet.ts";
const STATE = "src/core/state/state.ts";
const MATRIX = "src/core/dungeon/matrix.ts";
const MATRIX_NAV = "src/core/dungeon/matrix_navigation.ts";
const LAYOUT = "src/core/dungeon/dungeon_layout.ts";

interface Mutation {
  readonly id: string;
  readonly file: string;
  readonly find: string;
  readonly replace: string;
}

const MUTATIONS: readonly Mutation[] = [
  { id: "crit-off", file: COMBAT, find: "CRIT_CHANCE = 0.15;", replace: "CRIT_CHANCE = 0.0;" },
  { id: "crit-mult-identity", file: COMBAT, find: "CRIT_MULTIPLIER = 2.0;", replace: "CRIT_MULTIPLIER = 1.0;" },
  { id: "variance-floor-up", file: COMBAT, find: "DAMAGE_VARIANCE_MIN = 0.8;", replace: "DAMAGE_VARIANCE_MIN = 1.2;" },
  { id: "variance-ceil-down", file: COMBAT, find: "DAMAGE_VARIANCE_MAX = 1.2;", replace: "DAMAGE_VARIANCE_MAX = 0.8;" },
  { id: "alarm-cap-lower", file: COMBAT, find: "ALARM_MAX_LEVEL = 5;", replace: "ALARM_MAX_LEVEL = 3;" },
  { id: "autoattack-interval-half", file: COMBAT, find: "AUTO_ATTACK_INTERVAL_MS = 2000;", replace: "AUTO_ATTACK_INTERVAL_MS = 1000;" },
  { id: "combo-window-zero", file: COMBAT, find: "COMBO_WINDOW_MS = 3500;", replace: "COMBO_WINDOW_MS = 0;" },
  { id: "armor-bypass-off", file: COMBAT, find: "PROGRAM_POWER_ARMOR_BYPASS_CAP_PCT = 60;", replace: "PROGRAM_POWER_ARMOR_BYPASS_CAP_PCT = 0;" },
  { id: "stagger-zero", file: COMBAT, find: "STAGGER_DURATION_MS = 1500;", replace: "STAGGER_DURATION_MS = 0;" },
  { id: "alarm-tick-fast", file: COMBAT, find: "ALARM_TICK_INTERVAL_MS = 10000;", replace: "ALARM_TICK_INTERVAL_MS = 1000;" },
  // ADR-0337 (endings): the control gate. These were added THIS session, so a
  // survivor here means the fix is untested.
  { id: "control-wealth-zero", file: ENDING, find: "export const CONTROL_WEALTH = 18000;", replace: "export const CONTROL_WEALTH = 0;" },
  { id: "liberation-never", file: ENDING, find: "if (ctx.missionsCompleted >= 3) {", replace: "if (ctx.missionsCompleted >= 4) {" },
  // Economy (ADR-0323/0338): the hoard math and the leg carry.
  { id: "merge-mints-seed", file: WALLET, find: "Math.floor(Number(run.materials[k] ?? 0)) -", replace: "Math.floor(Number(run.materials[k] ?? 0)) +" },
  { id: "earned-keeps-seed", file: WALLET, find: "const gained = Math.floor(Number(v)) - Math.floor(Number(seed[k] ?? 0));", replace: "const gained = Math.floor(Number(v)) - 0;" },
  { id: "carry-drops-materials", file: STATE, find: "materials: addStacks(previous.inventory.materials, fresh.inventory.materials),", replace: "materials: fresh.inventory.materials," },
  // Matrix / dungeon topology (ADR-0333 rubric: does the suite see the board?).
  { id: "matrix-nodes-short", file: MATRIX, find: "export const NUM_NODES = 5;", replace: "export const NUM_NODES = 4;" },
  { id: "nohop-zero", file: MATRIX_NAV, find: "export const NO_HOP = -1;", replace: "export const NO_HOP = 0;" },
  { id: "grid-g4-shrunk", file: LAYOUT, find: "4: [13, 8],", replace: "4: [9, 6]," },
  // The run seed (ADR-0338), now a pure function (`contractSeedMaterials`).
  { id: "seed-ignores-contract", file: WALLET, find: "(acc, leg) => addStacks(acc, leg.mission.rewards.materials),", replace: "(acc, _leg) => acc," },
];

const DEFAULT_TESTS = [
  "tests/combat_engine.test.ts",
  "tests/ending_resolver.test.ts",
  "tests/adr0315_campaign_chain.test.ts",
  "tests/adr0323_the_hoard_outlives_the_run.test.ts",
  "tests/adr0338_run_seed.test.ts",
  "tests/matrix_structure.test.ts",
  "tests/matrix.test.ts",
  "tests/matrix_navigation.test.ts",
  "tests/dungeon_layout.test.ts",
  "tests/exploration.test.ts",
  "tests/ice_crit.test.ts",
  "tests/ice_alarm_multiplier.test.ts",
  "tests/crit_vfx_link.test.ts",
  "tests/design_conformance.test.ts",
  "tests/property_reducer_fuzz.test.ts",
  "tests/adr0320_effective_damage.test.ts",
  "tests/status.test.ts",
  "tests/combat_status_feedback.test.ts",
  "tests/idle_tick.test.ts",
  "tests/adr0327_program_power.test.ts",
];

/** Run vitest over `tests` and return the failure count from the JSON report. */
function runTests(tests: readonly string[]): { failed: number; total: number; ran: boolean } {
  const outFile = path.join(os.tmpdir(), `wetrun_mutation_${process.pid}_${Date.now()}.json`);
  fs.rmSync(outFile, { force: true });
  try {
    execFileSync(
      "npx",
      ["vitest", "run", ...tests, "--reporter=json", `--outputFile=${outFile}`],
      { cwd: WEB_ROOT, stdio: "pipe", encoding: "utf8" },
    );
  } catch {
    // A non-zero exit is expected when a mutation is killed.
  }
  try {
    const data = JSON.parse(fs.readFileSync(outFile, "utf8")) as {
      numFailedTests?: number;
      numTotalTests?: number;
    };
    return { failed: data.numFailedTests ?? 0, total: data.numTotalTests ?? 0, ran: true };
  } catch {
    return { failed: 0, total: 0, ran: false };
  } finally {
    fs.rmSync(outFile, { force: true });
  }
}

function applyMutation(m: Mutation): string {
  const abs = path.join(WEB_ROOT, m.file);
  const original = fs.readFileSync(abs, "utf8");
  const occurrences = original.split(m.find).length - 1;
  if (occurrences !== 1) {
    throw new Error(`mutation ${m.id}: pattern occurs ${occurrences}x in ${m.file} (want 1)`);
  }
  fs.writeFileSync(abs, original.replace(m.find, m.replace));
  return original;
}

function main(): number {
  const argv = process.argv.slice(2);
  const idx = argv.indexOf("--tests");
  const tests = idx >= 0 ? argv.slice(idx + 1) : DEFAULT_TESTS;
  if (tests.length === 0) {
    console.error("mutation_spike: --tests requires at least one path");
    return 2;
  }

  console.log(`Mutation spike — ${MUTATIONS.length} mutations, tests: ${tests.join(" ")}\n`);
  console.log("mutation                    failed  total  verdict");
  let survived = 0;
  for (const m of MUTATIONS) {
    const original = applyMutation(m);
    let result: { failed: number; total: number; ran: boolean };
    try {
      result = runTests(tests);
    } finally {
      fs.writeFileSync(path.join(WEB_ROOT, m.file), original);
    }
    let verdict: string;
    if (!result.ran) {
      verdict = "ERROR (no report)";
      survived += 1;
    } else if (result.failed > 0) {
      verdict = "KILLED";
    } else {
      verdict = "SURVIVED";
      survived += 1;
    }
    console.log(
      `${m.id.padEnd(28)}${String(result.failed).padStart(5)}  ` +
        `${String(result.total).padStart(5)}  ${verdict}`,
    );
  }

  console.log(
    `\n${MUTATIONS.length - survived}/${MUTATIONS.length} killed` +
      (survived > 0 ? ` — ${survived} survived (add a test that pins the behaviour)` : ""),
  );
  return survived > 0 ? 1 : 0;
}

try {
  process.exit(main());
} catch (exc) {
  console.error(`mutation_spike error: ${exc instanceof Error ? exc.message : String(exc)}`);
  process.exit(2);
}
