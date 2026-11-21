/** Campaign survival — does a three-mission contract hold up (ADR-0318).
 *
 * The recorded curves are **per mission** (`npm run balance`, `npm run
 * survival`). ADR-0315 turned the run into a contract of three missions and
 * noted the hole itself: "the harness is mission-unit; without an N-mission
 * survival rate there is no way to check campaign balance" (open question d).
 * This is that metric.
 *
 * It plays what the game plays: the contract is built with the game's own
 * `contractFor`, and each leg carries what `startNextLeg` carries — credits,
 * the deck, the unique — and resets HP, COST and the board. `--fresh` turns the
 * carry off, which is the comparison ADR-0315 measured one mission at a time.
 *
 *   npm run campaign                      # 3 missions, 20 seeds x 33 starts
 *   npm run campaign -- --seeds 64
 *   npm run campaign -- --fresh           # no carry between legs
 *   npm run campaign -- --missions 2      # a shorter contract (the resolver's
 *                                         # liberation gate is 3, so 2 cannot
 *                                         # reach it — this is for probing)
 */
import { loadIceCatalog, loadMissionsCatalog, loadProgramsCatalog } from "../src/core/data_loaders";
import { missionGradeOf } from "../src/core/combat/ice_scaling";
import { resolveEnding } from "../src/core/combat/ending_resolver";
import { contractFor } from "../src/core/state/campaign";
import { missionIce } from "../src/core/state/mission_ice";
import { mulberry32, playRun } from "./play_policy";
import type { Ice, Mission, Program } from "../src/core/types";
import iceJson from "../src/data/ice_types.json" with { type: "json" };
import missionsJson from "../src/data/missions.json" with { type: "json" };
import programsJson from "../src/data/programs.json" with { type: "json" };

const seedArg = process.argv.indexOf("--seeds");
const SEEDS = seedArg >= 0 ? Number(process.argv[seedArg + 1]) || 20 : 20;
const missionsArg = process.argv.indexOf("--missions");
const CONTRACT = missionsArg >= 0 ? Number(process.argv[missionsArg + 1]) || 3 : 3;
/** Off: every leg starts as the game's fresh run does. On (default): the game's
 * `startNextLeg` carry. The gap is what carrying is worth. */
const FRESH = process.argv.includes("--fresh");
const cardsIdx = process.argv.indexOf("--cards");
const CARD_POLICY = cardsIdx >= 0 && process.argv[cardsIdx + 1] === "first" ? "first" : "best";
const lootIdx = process.argv.indexOf("--loot");
const LOOT_POLICY =
  lootIdx >= 0 && process.argv[lootIdx + 1] === "card" ? "card" : "value";
/** The same base and the same per-cell formula `mission_survival` uses
 * (ADR-0310), with the mission's index in the FULL catalog. Leg 1 is a fresh
 * mission, so it must reproduce that harness's cell — which is how this one is
 * checked against the metric it extends. */
const BASE_SEED = 20261106;

/** The recorded contract curve, by the START mission's grade (2026-11-17).
 *
 * These are **measured**, not chosen: the first run of this harness produced
 * them at 64 seeds with the carry on, and they are recorded so a change that
 * moves the campaign is caught. They are NOT a statement that the shape is
 * right — see the note in the output about g4/g5.
 *
 * ADR-0315's mission-unit targets (`GRADE_TARGETS`) read g1 100, g2 95, g3 80,
 * g4 50, g5 25, g6 30. A contract chains three missions, and the chain is what
 * used to collapse the top of the ladder. ADR-0318 (f) read that collapse as "a
 * grade is not a difficulty band": solo completion inside g4 spanned 1.6%
 * (`ta_heist`) to 100% (`mollys_razor`), because each mission's map is fixed by
 * its `matrix_seed`.
 *
 * ADR-0319 (a won fight heals the body to a floor) then split that finding in
 * two. Inside g4 the spread collapsed to 59%..100% — g4's difficulty was
 * ATTRITION, and a per-fight floor removes it (g4 contracts 2.5% -> 63.8%).
 * Inside g5 the spread did not move at all (1.6%..87.5%) — g5's difficulty is
 * the fight itself, and no between-fight recovery can reach it. The per-leg
 * table below is the measurement that shows which one a grade is. */
export const CONTRACT_TARGETS: Readonly<Record<number, number>> = {
  1: 1.0,
  2: 0.909,
  3: 0.509,
  4: 0.614,
  5: 0.031,
  6: 0.203,
};

/** Overall contract completion, recorded the same way.
 *
 * Re-recorded after ADR-0321 turned `cloak`'s evasion from a flat damage cut
 * into a MISS roll: the seeded stream moved, so the campaign moved with it
 * (overall 47.4% -> 46.4%, worst grade -4.0pp). Before that, ADR-0319's
 * per-fight recovery re-recorded it once already (30.3% -> 47.4%, g4 2.5% ->
 * 63.8%) — the recovery is worth most where the contract's difficulty was
 * attrition, and g5 barely moves because it loses a single fight.
 */
export const CONTRACT_TARGET = 0.464;

/** Tolerance before a sweep reports a miss, in percentage points. */
const TOLERANCE_PP = 8;

const ice = loadIceCatalog(iceJson) as Readonly<Record<string, Ice>>;
const programs = loadProgramsCatalog(programsJson);
const missions = loadMissionsCatalog(missionsJson);
const ALL = Object.values(missions) as Mission[];
const SPRAWL = ALL.filter((m) => m.source_universe !== "far-grid");
const iceFor = (m: Mission): Ice => missionIce(m, ice);

/** One contract's outcome. */
interface LegStat {
  reached: number;
  completed: number;
}
interface Result {
  readonly legs: LegStat[];
  readonly contracts: number;
  readonly finished: number;
  /** Finished contracts that would have read as `control` under the order
   * ADR-0318 replaced — the number that says whether the reorder mattered. */
  readonly wouldBeControl: number;
  readonly creditsAtEnd: number[];
  /** Ending category the CURRENT resolver returns at each mission completion
   * (the game resolves at every leg, with missionsCompleted = completed + 1). */
  readonly endings: Record<string, number>;
}

function playContract(start: Mission, sweepSeed: number, index: number): Result {
  const legs: LegStat[] = Array.from({ length: CONTRACT }, () => ({
    reached: 0,
    completed: 0,
  }));
  const contract = contractFor(start, missions, iceFor);
  const clockRef = { now: 1_700_000_000_000 + sweepSeed * 100_000 };
  let carry: {
    deck?: ReadonlyArray<Program>;
    credits?: number;
    uniquePickDone?: boolean;
  } = {};
  let finished = 0;
  let wouldBeControl = 0;
  const creditsAtEnd: number[] = [];
  const endings: Record<string, number> = {};

  for (let leg = 0; leg < contract.legs.length && leg < CONTRACT; leg += 1) {
    const mission = contract.legs[leg]?.mission;
    if (!mission) break;
    legs[leg]!.reached += 1;
    // A leg owns its dice and its clock, so a cell is reproducible on its own.
    Math.random = mulberry32(BASE_SEED + sweepSeed * 7919 + index * 31 + leg * 13);
    // `index` is the mission's position in the FULL catalog, so a leg-1 cell is
    // the cell `mission_survival` measures for the same mission and seed.
    clockRef.now += 60_000;
    const final = playRun(
      mission,
      ice,
      programs,
      clockRef,
      "novice",
      CARD_POLICY,
      "opening",
      "long",
      LOOT_POLICY,
      0,
      0,
      0,
      "stim",
      0,
      12,
      false,
      FRESH
        ? undefined
        : {
            ...(carry.deck ? { deck: carry.deck } : {}),
            ...(carry.credits !== undefined ? { credits: carry.credits } : {}),
            ...(carry.uniquePickDone ? { uniquePickDone: true } : {}),
          },
    );
    if (!final || final.runPhase !== "ending") {
      // Died mid-contract — the shown ending is `sacrifice`.
      endings["sacrifice"] = (endings["sacrifice"] ?? 0) + 1;
      break;
    }
    legs[leg]!.completed += 1;
    const credits = final.player.credits;
    creditsAtEnd.push(credits);
    // Only the FINAL leg's resolution is SHOWN. `state.ts:200` replaces an
    // intermediate leg's ending with the next leg (`startNextLeg`), so leg1/leg2
    // resolutions are swallowed and never reach the player. Tally the shown one.
    if (leg === contract.legs.length - 1) {
      finished += 1;
      const ending = resolveEnding({
        arc: (mission.arc as 1) || 1,
        hp: final.player.hp,
        maxHp: final.player.maxHp,
        credits,
        missionsCompleted: leg + 1,
        totalDeaths: 0,
        factionScores: {},
        choices: [],
      });
      endings[ending.category] = (endings[ending.category] ?? 0) + 1;
      // Under the order ADR-0318 replaced, `credits > 5000` came first.
      if (credits > 5000 && final.player.hp > 0) wouldBeControl += 1;
    }
    carry = {
      deck: [...final.deck, ...final.drawPile, ...final.discardPile],
      credits,
      uniquePickDone: final.uniquePickDone === true,
    };
  }
  return {
    legs,
    contracts: 1,
    finished,
    wouldBeControl,
    creditsAtEnd,
    endings,
  };
}

function main(): void {
  // A mutable accumulator; `Result` describes one contract, not the sweep.
  const totals = {
    legs: Array.from({ length: CONTRACT }, () => ({ reached: 0, completed: 0 })),
    contracts: 0,
    finished: 0,
    wouldBeControl: 0,
    creditsAtEnd: [] as number[],
    endings: {} as Record<string, number>,
  };
  const byGrade = new Map<number, { contracts: number; finished: number }>();
  const finals: number[] = [];
  // The per-leg rates by START grade. The aggregate leg table above mixes every
  // grade together; this is the one that shows a contract's legs are not equal,
  // which is what rules out the "coin flip three times" reading of (e).
  const legByGrade = new Map<number, { reached: number; completed: number }[]>();
  const originalRandom = Math.random;

  try {
    for (let s = 0; s < SEEDS; s += 1) {
      SPRAWL.forEach((start) => {
        const result = playContract(start, s, ALL.indexOf(start));
        totals.contracts += result.contracts;
        totals.finished += result.finished;
        totals.wouldBeControl += result.wouldBeControl;
        totals.creditsAtEnd.push(...result.creditsAtEnd);
        for (const [cat, n] of Object.entries(result.endings)) {
          totals.endings[cat] = (totals.endings[cat] ?? 0) + n;
        }
        if (result.finished === 1 && result.creditsAtEnd.length > 0) {
          finals.push(result.creditsAtEnd[result.creditsAtEnd.length - 1] ?? 0);
        }
        result.legs.forEach((leg, i) => {
          totals.legs[i]!.reached += leg.reached;
          totals.legs[i]!.completed += leg.completed;
        });
        const grade = missionGradeOf(start);
        const legCell =
          legByGrade.get(grade) ??
          Array.from({ length: CONTRACT }, () => ({ reached: 0, completed: 0 }));
        result.legs.forEach((leg, i) => {
          legCell[i]!.reached += leg.reached;
          legCell[i]!.completed += leg.completed;
        });
        legByGrade.set(grade, legCell);
        const g = byGrade.get(grade) ?? { contracts: 0, finished: 0 };
        g.contracts += result.contracts;
        g.finished += result.finished;
        byGrade.set(grade, g);
      });
    }
  } finally {
    Math.random = originalRandom;
  }

  const pct = (n: number, d: number): string =>
    d === 0 ? "  n/a" : `${((n / d) * 100).toFixed(1)}%`.padStart(6);
  const mean = (xs: number[]): number =>
    xs.length === 0 ? 0 : xs.reduce((a, b) => a + b, 0) / xs.length;
  const quantile = (xs: number[], q: number): number => {
    if (xs.length === 0) return 0;
    const sorted = [...xs].sort((a, b) => a - b);
    const idx = Math.min(sorted.length - 1, Math.max(0, Math.round(q * (sorted.length - 1))));
    return sorted[idx] ?? 0;
  };

  console.log(
    `campaign survival — ${CONTRACT}-mission contracts, ${SEEDS} seeds x ${SPRAWL.length} start missions, ` +
      `carry ${FRESH ? "OFF (--fresh)" : "on"}, cards "${CARD_POLICY}", loot "${LOOT_POLICY}"`,
  );
  console.log("");
  console.log("leg   reached   completed    of those reached");
  totals.legs.forEach((leg, i) => {
    console.log(
      `  ${i + 1}   ${String(leg.reached).padStart(7)}   ${String(leg.completed).padStart(9)}   ${pct(leg.completed, leg.reached)}`,
    );
  });
  console.log("");
  // The per-leg rate is CONDITIONAL on reaching that leg, so a later leg reads
  // higher than an earlier one: its population is the contracts that survived
  // the earlier legs, which are the easier ones. The unconditional number is
  // the contract completion below.
  console.log("(per-leg rate is conditional on reaching that leg — later legs look");
  console.log(" easier because their population is the survivors, not the whole set)");
  console.log(
    `contract finished (${CONTRACT}/${CONTRACT}): ${totals.finished}/${totals.contracts} = ${pct(totals.finished, totals.contracts)}`,
  );
  console.log(
    `mean credits at the end of a finished contract: ${Math.round(mean(totals.creditsAtEnd))}`,
  );
  // The control gate is read off the credits at the FINAL resolution, so the
  // distribution that matters is the finished contract's last-leg wallet.
  console.log(
    `credits at a finished contract's end — p50 ${quantile(finals, 0.5)} · p75 ${quantile(finals, 0.75)} · ` +
      `p90 ${quantile(finals, 0.9)} · p95 ${quantile(finals, 0.95)} · max ${finals.length ? Math.max(...finals) : 0}`,
  );
  // ADR-0318 moved the campaign's ending ahead of wealth. This is how many
  // finished contracts the old order would have read as "you got rich".
  console.log(
    `finished contracts the OLD order would have called control: ${totals.wouldBeControl}/${totals.finished} = ${pct(totals.wouldBeControl, totals.finished)}`,
  );
  const totalEndings = Object.values(totals.endings).reduce((a, b) => a + b, 0);
  console.log("");
  console.log(`endings resolved under the CURRENT order (every leg, ${totalEndings} resolutions):`);
  for (const [cat, n] of Object.entries(totals.endings).sort((a, b) => b[1] - a[1])) {
    console.log(`  ${cat.padEnd(14)} ${String(n).padStart(5)}   ${pct(n, totalEndings)}`);
  }
  console.log("");
  console.log("leg completion by START grade (conditional on reaching that leg)");
  for (const grade of [...legByGrade.keys()].sort((a, b) => a - b)) {
    const cells = legByGrade.get(grade)!;
    console.log(
      `  g${grade}   ` +
        cells
          .map((c, i) => `leg${i + 1} ${pct(c.completed, c.reached)}`)
          .join("   "),
    );
  }
  console.log("(legs within a grade are equal when the grade's difficulty is attrition");
  console.log(" (g4), and unequal when it is the fight itself (g5) — ADR-0319)");
  console.log("");
  console.log("by start grade (contract completion)");
  console.log("grade  contracts  finished  rate   target  delta");
  let worst = 0;
  for (const grade of [...byGrade.keys()].sort((a, b) => a - b)) {
    const g = byGrade.get(grade)!;
    const rate = (g.finished / g.contracts) * 100;
    const target = (CONTRACT_TARGETS[grade] ?? 0) * 100;
    const delta = rate - target;
    if (Math.abs(delta) > Math.abs(worst)) worst = delta;
    console.log(
      `  ${grade}      ${String(g.contracts).padStart(7)}  ${String(g.finished).padStart(8)}  ${pct(g.finished, g.contracts)}   ${target.toFixed(1).padStart(5)}%  ${delta >= 0 ? "+" : ""}${delta.toFixed(1)}`,
    );
  }
  const overall = (totals.finished / totals.contracts) * 100;
  const overallDelta = overall - CONTRACT_TARGET * 100;
  console.log("");
  console.log(
    `overall vs recorded target: ${overall.toFixed(1)}% vs ${(CONTRACT_TARGET * 100).toFixed(1)}% ` +
      `(${overallDelta >= 0 ? "+" : ""}${overallDelta.toFixed(1)}pp, tolerance ${TOLERANCE_PP}pp)`,
  );
  const misses = Math.abs(worst) > TOLERANCE_PP ? ` — worst grade misses by ${worst.toFixed(1)}pp` : "";
  console.log(`worst grade delta: ${worst >= 0 ? "+" : ""}${worst.toFixed(1)}pp${misses}`);
  console.log("");
  // Recorded, not endorsed. ADR-0318 chose the contract's shape; this is what
  // that shape does at the top of the ladder, and it is the owner's call.
  // Cite the LIVE numbers, not literals: this note went stale the moment a
  // balance change moved the curve (ADR-0321 did), and a note that disagrees
  // with the table above it is worse than no note.
  const rateOf = (g: number): string =>
    byGrade.get(g) === undefined
      ? "n/a"
      : pct(byGrade.get(g)!.finished, byGrade.get(g)!.contracts).trim();
  console.log(`NOTE (see ADR-0318 (e)/(f), ADR-0319, ADR-0321): g4 contracts complete ${rateOf(4)}`);
  console.log(` and g5 ${rateOf(5)}, while g3 completes ${rateOf(3)}. ADR-0319's recovery moved g4 —`);
  console.log(" its difficulty was attrition, and a floor removes it. g5 barely moves,");
  console.log(" because it loses a single fight. The top of the ladder is therefore an OPEN");
  console.log(" question: g4 reads easier than g3, and g5 is untouched.");
}

main();
