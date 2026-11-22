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
const OWNED = "src/core/state/owned_equipment.ts";
const EFFECTS = "src/core/combat/program_effects.ts";
const FACTION = "src/core/state/faction_reputation.ts";
const COMPRESS = "src/save/compress.ts";
const QUOTA = "src/save/storage_quota.ts";
const STORAGE = "src/save/storage.ts";
const AUDIO = "src/audio/manager.ts";
const I18N = "src/core/i18n.ts";
const PWA = "src/core/pwa_manager.ts";
const GN_TEXT = "src/core/graphic_novel/graphic_novel_text.ts";
const GN_PLAYER = "src/core/graphic_novel/graphic_novel_player.ts";
const CRAWLER_TYPES = "src/core/dungeon/dungeon_crawler_types.ts";
const ACHIEVEMENTS = "src/core/state/achievements.ts";

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
  // The run-end gear merge (ADR-0329), now a pure function (ADR-0347).
  { id: "drops-ignored", file: OWNED, find: "for (const id of droppedIds) next = ownEquipment(next, id);", replace: "for (const id of droppedIds) next = next;" },
  // Card value and faction reputation (wider gameplay surface).
  { id: "base-damage-4", file: EFFECTS, find: "return program.tier * 5;", replace: "return program.tier * 4;" },
  { id: "allied-threshold", file: FACTION, find: "{ tier: \"ALLIED\", min: 80 },", replace: "{ tier: \"ALLIED\", min: 70 }," },
  { id: "allied-multiplier", file: FACTION, find: "ALLIED: 0.5,", replace: "ALLIED: 0.9," },
  // Save pipeline: compression threshold, quota bands, slot count, schema.
  { id: "compress-threshold", file: COMPRESS, find: "export const COMPRESSION_THRESHOLD_BYTES = 512;", replace: "export const COMPRESSION_THRESHOLD_BYTES = 1024;" },
  { id: "quota-warn-band", file: QUOTA, find: "export const STORAGE_QUOTA_WARNING_PERCENT = 80;", replace: "export const STORAGE_QUOTA_WARNING_PERCENT = 70;" },
  { id: "slot-count", file: STORAGE, find: "const MANUAL_SLOT_COUNT = 3;", replace: "const MANUAL_SLOT_COUNT = 2;" },
  { id: "schema-version", file: STORAGE, find: "const CURRENT_SCHEMA_VERSION = 1;", replace: "const CURRENT_SCHEMA_VERSION = 2;" },
  // Audio ducking, default language, PWA boot state.
  { id: "bgm-duck-factor", file: AUDIO, find: "export const BGM_DUCK_FACTOR = 0.8;", replace: "export const BGM_DUCK_FACTOR = 0.5;" },
  { id: "i18n-default-lang", file: I18N, find: "language: \"en\",", replace: "language: \"ko\"," },
  { id: "pwa-can-install", file: PWA, find: "canInstall: false,", replace: "canInstall: true," },
  // Graphic novel: pagination, typing speed, save version.
  { id: "gn-lines-per-page", file: GN_TEXT, find: "export const DEFAULT_LINES_PER_PAGE = 20;", replace: "export const DEFAULT_LINES_PER_PAGE = 15;" },
  { id: "gn-ms-per-char", file: GN_TEXT, find: "export const MS_PER_CHAR = 30;", replace: "export const MS_PER_CHAR = 60;" },
  { id: "gn-save-version", file: GN_PLAYER, find: "export const GN_SAVE_VERSION = \"1.2.0\";", replace: "export const GN_SAVE_VERSION = \"9.9.9\";" },
  // Dungeon crawler glyphs (string enums) — a rendering contract.
  { id: "crawler-floor", file: CRAWLER_TYPES, find: "FLOOR = \".\",", replace: "FLOOR = \",\"," },
  { id: "crawler-monster", file: CRAWLER_TYPES, find: "MONSTER = \"M\",", replace: "MONSTER = \"m\"," },
  { id: "crawler-goliath", file: CRAWLER_TYPES, find: "ICE_GOLIATH = \"g\",", replace: "ICE_GOLIATH = \"G\"," },
  // Achievement thresholds (functional module).
  { id: "ach-centurion-101", file: ACHIEVEMENTS, find: "getProgress(\"centurion_progress\") >= 100", replace: "getProgress(\"centurion_progress\") >= 101" },
  { id: "ach-flawless-51", file: ACHIEVEMENTS, find: "getProgress(\"flawless_progress\") >= 50", replace: "getProgress(\"flawless_progress\") >= 51" },
  { id: "ach-undefeated-11", file: ACHIEVEMENTS, find: "getProgress(\"undefeated_progress\") >= 10", replace: "getProgress(\"undefeated_progress\") >= 11" },
];

const DEFAULT_TESTS = [
  "tests/combat_engine.test.ts",
  "tests/ending_resolver.test.ts",
  "tests/adr0315_campaign_chain.test.ts",
  "tests/adr0323_the_hoard_outlives_the_run.test.ts",
  "tests/adr0338_run_seed.test.ts",
  "tests/owned_equipment.test.ts",
  "tests/program_effects.test.ts",
  "tests/program_catalog_text.test.ts",
  "tests/faction_reputation.test.ts",
  "tests/compress.test.ts",
  "tests/save_compression_size.test.ts",
  "tests/storage_quota.test.ts",
  "tests/storage.test.ts",
  "tests/state_save.test.ts",
  "tests/audio_ducking.test.ts",
  "tests/i18n.test.ts",
  "tests/pwa_manager.test.ts",
  "tests/graphic_novel_text.test.ts",
  "tests/graphic_novel_player.test.ts",
  "tests/graphic_novel_save.test.ts",
  "tests/graphic_novel.test.ts",
  "tests/dungeon_crawler_wiring.test.ts",
  "tests/dungeon_crawler_types.test.ts",
  "tests/achievements.test.ts",
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

/** The mutation currently written to disk, so an interrupted run can restore it.
 *  A SIGINT/SIGPIPE/SIGKILL otherwise leaves a source file mutated — on
 *  2026-11-22 a killed run left `combat_engine.ts` and `graphic_novel_text.ts`
 *  mutated and we had to `git checkout` them. */
let active: { readonly abs: string; readonly original: string } | null = null;

function applyMutation(m: Mutation): string {
  const abs = path.join(WEB_ROOT, m.file);
  const original = fs.readFileSync(abs, "utf8");
  const occurrences = original.split(m.find).length - 1;
  if (occurrences !== 1) {
    throw new Error(`mutation ${m.id}: pattern occurs ${occurrences}x in ${m.file} (want 1)`);
  }
  const mutated = original.replace(m.find, m.replace);
  active = { abs, original };
  fs.writeFileSync(abs, mutated);
  return original;
}

/** Restore whatever file is currently mutated, if any. Idempotent. */
function revertActive(): void {
  if (active !== null) {
    fs.writeFileSync(active.abs, active.original);
    active = null;
  }
}

for (const sig of ["SIGINT", "SIGTERM", "SIGHUP", "SIGPIPE"] as const) {
  try {
    process.on(sig, () => {
      revertActive();
      process.exit(130);
    });
  } catch {
    // Signal not supported on this platform; the finally path still covers throws.
  }
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

  // Preflight: every pattern must be present and unique BEFORE any file is
  // written, so a tree left mutated by an interrupted run fails fast (with the
  // fix) instead of half-applying.
  const stale = MUTATIONS.filter((m) => {
    const text = fs.readFileSync(path.join(WEB_ROOT, m.file), "utf8");
    return text.split(m.find).length - 1 !== 1;
  }).map((m) => m.id);
  if (stale.length > 0) {
    console.error(
      `mutation_spike: tree is not at the expected baseline — pattern missing for: ${stale.join(", ")}`,
    );
    console.error("A previous run was interrupted and left a file mutated. Restore: git checkout -- web/src");
    return 2;
  }

  console.log("mutation                    failed  total  verdict");
  let survived = 0;
  for (const m of MUTATIONS) {
    applyMutation(m);
    let result: { failed: number; total: number; ran: boolean };
    try {
      result = runTests(tests);
    } finally {
      revertActive();
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
  revertActive();
  console.error(`mutation_spike error: ${exc instanceof Error ? exc.message : String(exc)}`);
  process.exit(2);
}
