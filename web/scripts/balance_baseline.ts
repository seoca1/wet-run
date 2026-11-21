#!/usr/bin/env tsx
/**
 * Balance baseline gate (ADR-0333).
 *
 * Why this exists: the balance harness is deterministic (fixed seed stream, no
 * RNG from the clock), so a shipping change that moves a win-rate must move it
 * in a *known* way. Before this, the "balance is byte-identical" claim was
 * checked by a human reading two terminal outputs, and `balance:compare` — the
 * tool meant to automate it — parsed a format the harness never printed, so it
 * reported "no regression" for every change. This records the curve once as a
 * committed golden (`balance.golden.json`) and diffs against it.
 *
 * Usage:
 *   npm run balance:golden              # (re)record the golden from current code
 *   npm run balance:check               # strict: any drift fails
 *   npm run balance:check -- --allow-improvement   # only a drop fails
 *   npm run balance:check -- --runs 500
 *
 * Exit codes: 0 = matches, 1 = drift found, 2 = script error.
 */
import { execFileSync } from "node:child_process";
import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";

const WEB_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const GOLDEN_PATH = path.join(WEB_ROOT, "scripts", "balance.golden.json");
/** CI's PR comment step reads this file (the old `balance_compare` wrote it). */
const SUMMARY_PATH = path.join(WEB_ROOT, "test-results", "balance-summary.txt");

/** The same three decks the CI balance job measures. */
const DECKS = ["opening", "veteran", "heretic"] as const;
const DEFAULT_RUNS = 100;
/** Win-rates print to 0.1%; floats (turns/HP) are allowed a hair of slack so a
 *  cross-platform rounding difference is not read as a balance change. */
const FLOAT_TOLERANCE = 0.05;

interface GradeRow {
  readonly grade: number;
  readonly winRate: number;
  readonly stalled: number;
  readonly meanTurns: number;
  readonly meanHpEnd: number;
}

interface Golden {
  readonly runs: number;
  readonly decks: Record<string, GradeRow[]>;
}

/** The harness's numeric table row:
 *  `    1         4    100.0%     0.0%         3.0         87.0   86/90` */
const ROW = /^\s*(\d+)\s+(\d+)\s+([\d.]+)%\s+([\d.]+)%\s+([\d.]+)\s+([\d.]+)\s+(\d+)\/(\d+)\s*$/;

function parseCurve(output: string): GradeRow[] {
  const rows: GradeRow[] = [];
  for (const line of output.split("\n")) {
    const m = ROW.exec(line);
    if (m === null) continue;
    rows.push({
      grade: Number.parseInt(m[1]!, 10),
      winRate: Number.parseFloat(m[3]!),
      stalled: Number.parseFloat(m[4]!),
      meanTurns: Number.parseFloat(m[5]!),
      meanHpEnd: Number.parseFloat(m[6]!),
    });
  }
  if (rows.length === 0) {
    throw new Error(
      "balance_baseline: no grade rows parsed — did the harness output format change?",
    );
  }
  return rows;
}

function measureDeck(deck: string, runs: number): GradeRow[] {
  const output = execFileSync(
    "npm",
    ["run", "balance", "--", "--deck", deck, "--runs", String(runs)],
    { cwd: WEB_ROOT, encoding: "utf8" },
  );
  return parseCurve(output);
}

function measure(runs: number): Golden {
  const decks: Record<string, GradeRow[]> = {};
  for (const deck of DECKS) decks[deck] = measureDeck(deck, runs);
  return { runs, decks };
}

function readGolden(): Golden {
  return JSON.parse(fs.readFileSync(GOLDEN_PATH, "utf8")) as Golden;
}

/** Returns human-readable drift lines plus the count of drops. */
function diff(
  baseline: Golden,
  current: Golden,
  allowImprovement: boolean,
): { lines: string[]; regressions: number; drifts: number } {
  const lines: string[] = [];
  let regressions = 0;
  let drifts = 0;
  for (const deck of DECKS) {
    const base = baseline.decks[deck] ?? [];
    const curr = current.decks[deck] ?? [];
    if (base.length !== curr.length) {
      lines.push(`${deck}: grade count changed ${base.length} -> ${curr.length}`);
      regressions += 1;
      drifts += 1;
      continue;
    }
    for (let i = 0; i < base.length; i += 1) {
      const b = base[i]!;
      const c = curr[i]!;
      const winDelta = c.winRate - b.winRate;
      const floatDrift =
        Math.abs(c.meanTurns - b.meanTurns) > FLOAT_TOLERANCE ||
        Math.abs(c.meanHpEnd - b.meanHpEnd) > FLOAT_TOLERANCE ||
        Math.abs(c.stalled - b.stalled) > FLOAT_TOLERANCE;
      if (Math.abs(winDelta) < 0.0001 && !floatDrift) continue;
      const dir = winDelta < 0 ? "REGRESSION" : winDelta > 0 ? "improvement" : "drift";
      if (winDelta < -0.0001) regressions += 1;
      drifts += 1;
      const material = winDelta < -0.0001 || !allowImprovement;
      lines.push(
        `${material ? "✗" : "·"} ${deck} g${c.grade}: ` +
          `${b.winRate.toFixed(1)}% -> ${c.winRate.toFixed(1)}% ` +
          `(${winDelta >= 0 ? "+" : ""}${winDelta.toFixed(1)}pp, ${dir})`,
      );
    }
  }
  return { lines, regressions, drifts };
}

function parseArgs(argv: string[]): {
  write: boolean;
  check: boolean;
  allowImprovement: boolean;
  runs: number;
} {
  const runsIdx = argv.indexOf("--runs");
  const raw = runsIdx >= 0 ? argv[runsIdx + 1] : undefined;
  const parsed = raw === undefined ? Number.NaN : Number.parseInt(raw, 10);
  return {
    write: argv.includes("--write"),
    check: argv.includes("--check"),
    allowImprovement: argv.includes("--allow-improvement"),
    runs: Number.isFinite(parsed) && parsed > 0 ? parsed : DEFAULT_RUNS,
  };
}

function printCurve(label: string, curve: GradeRow[]): void {
  console.log(`  ${label}: ` + curve.map((r) => `g${r.grade}=${r.winRate.toFixed(1)}%`).join(" "));
}

function writeSummary(lines: string[]): void {
  fs.mkdirSync(path.dirname(SUMMARY_PATH), { recursive: true });
  fs.writeFileSync(SUMMARY_PATH, lines.join("\n") + "\n");
}

function main(): number {
  const args = parseArgs(process.argv.slice(2));
  if (args.write === args.check) {
    console.error("usage: balance_baseline.ts --write | --check [--allow-improvement] [--runs N]");
    return 2;
  }

  const current = measure(args.runs);
  for (const deck of DECKS) printCurve(deck, current.decks[deck]!);

  if (args.write) {
    fs.writeFileSync(GOLDEN_PATH, JSON.stringify(current, null, 2) + "\n");
    console.log(`\nwrote golden: ${path.relative(WEB_ROOT, GOLDEN_PATH)}`);
    return 0;
  }

  if (!fs.existsSync(GOLDEN_PATH)) {
    console.error(`no golden at ${GOLDEN_PATH} — run: npm run balance:golden`);
    return 2;
  }
  const baseline = readGolden();
  if (baseline.runs !== current.runs) {
    console.error(
      `golden was recorded at --runs ${baseline.runs}, this check used ${current.runs} — rerun with --runs ${baseline.runs}`,
    );
    return 2;
  }

  const { lines, regressions, drifts } = diff(baseline, current, args.allowImprovement);
  if (drifts === 0) {
    console.log(`\nOK: balance matches golden (${DECKS.length} decks).`);
    writeSummary([`OK: balance matches golden (${DECKS.length} decks, runs=${current.runs}).`]);
    return 0;
  }
  console.log(`\nDRIFT (${drifts}) vs golden:`);
  for (const line of lines) console.log("  " + line);
  if (args.allowImprovement && regressions === 0) {
    console.log("\nOK: no regression (improvements/drift allowed).");
    writeSummary([`OK: no regression (${drifts} improvement/drift allowed, runs=${current.runs}).`]);
    return 0;
  }
  writeSummary([`FAIL: ${drifts} drift(s), ${regressions} regression(s) vs golden.`].concat(lines.map((l) => "  " + l)));
  console.log(
    `\nFAIL: ${drifts} drift(s), ${regressions} regression(s). ` +
      `If intended, re-record: npm run balance:golden`,
  );
  return 1;
}

try {
  process.exit(main());
} catch (exc) {
  console.error(`balance_baseline error: ${exc instanceof Error ? exc.message : String(exc)}`);
  process.exit(2);
}
