#!/usr/bin/env tsx
/**
 * Gear golden gate (ADR-0336).
 *
 * `npm run balance` goldens the BARE runner (EMPTY_LOADOUT). That leaves the
 * gear-worn curve — what the crafting system actually hands the player —
 * unmeasured by any gate, so a change to `equipment.ts` stats (ADR-0328) or the
 * defense step (ADR-0326) could move it silently. This records `gearCurve()`
 * once as a committed golden and diffs against it, the same way
 * `balance_baseline.ts` does for the bare curve.
 *
 * Usage:
 *   npm run gear:golden              # (re)record from current code
 *   npm run gear:check               # any drift fails
 *
 * Exit codes: 0 = matches, 1 = drift, 2 = error.
 */
import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import { gearCurve, type GearCurve } from "./gear_curve_probe";

const WEB_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const GOLDEN_PATH = path.join(WEB_ROOT, "scripts", "gear.golden.json");
/** Percent values are print-rounded; a hair of slack covers float noise. */
const TOLERANCE = 0.5;

function readGolden(): GearCurve {
  return JSON.parse(fs.readFileSync(GOLDEN_PATH, "utf8")) as GearCurve;
}

function diff(baseline: GearCurve, current: GearCurve): string[] {
  const lines: string[] = [];
  const cmp = (label: string, b: readonly number[], c: readonly number[]): void => {
    if (b.length !== c.length) {
      lines.push(`${label}: length changed ${b.length} -> ${c.length}`);
      return;
    }
    for (let i = 0; i < b.length; i += 1) {
      if (Math.abs((b[i] ?? 0) - (c[i] ?? 0)) > TOLERANCE) {
        lines.push(`${label} g${i + 1}: ${(b[i] ?? 0).toFixed(1)} -> ${(c[i] ?? 0).toFixed(1)}`);
      }
    }
  };
  for (let i = 0; i < baseline.encounter.length; i += 1) {
    const b = baseline.encounter[i];
    const c = current.encounter[i];
    if (b === undefined || c === undefined) {
      lines.push(`encounter row ${i}: missing`);
      continue;
    }
    cmp(`${b.set} win%`, b.winPct, c.winPct);
    cmp(`${b.set} hp%`, b.hpRemainPct, c.hpRemainPct);
  }
  for (let i = 0; i < baseline.mission.length; i += 1) {
    const b = baseline.mission[i];
    const c = current.mission[i];
    if (b === undefined || c === undefined) {
      lines.push(`mission row ${i}: missing`);
      continue;
    }
    cmp(`${b.set} mission%`, b.completionPct, c.completionPct);
  }
  return lines;
}

function main(): number {
  const argv = process.argv.slice(2);
  const write = argv.includes("--write");
  const check = argv.includes("--check");
  if (write === check) {
    console.error("usage: gear_baseline.ts --write | --check");
    return 2;
  }

  const current = gearCurve();
  for (const row of current.encounter) {
    console.log(`  enc ${row.set.padEnd(32)} ${row.winPct.map((w) => w.toFixed(0)).join(" ")}`);
  }
  for (const row of current.mission) {
    console.log(`  mis ${row.set.padEnd(32)} ${row.completionPct.map((c) => c.toFixed(0)).join(" ")}`);
  }

  if (write) {
    fs.writeFileSync(GOLDEN_PATH, JSON.stringify(current, null, 2) + "\n");
    console.log(`\nwrote golden: ${path.relative(WEB_ROOT, GOLDEN_PATH)}`);
    return 0;
  }
  if (!fs.existsSync(GOLDEN_PATH)) {
    console.error(`no golden at ${GOLDEN_PATH} — run: npm run gear:golden`);
    return 2;
  }
  const lines = diff(readGolden(), current);
  if (lines.length === 0) {
    console.log("\nOK: gear curve matches golden.");
    return 0;
  }
  console.log(`\nDRIFT (${lines.length}) vs gear golden:`);
  for (const line of lines) console.log("  " + line);
  console.log("\nIf intended, re-record: npm run gear:golden");
  return 1;
}

try {
  process.exit(main());
} catch (exc) {
  console.error(`gear_baseline error: ${exc instanceof Error ? exc.message : String(exc)}`);
  process.exit(2);
}
