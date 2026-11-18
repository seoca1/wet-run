/** Gear curve probe — what the ADR-0326 stats do once a runner wears them.
 *
 * `npm run balance` / `npm run survival` measure the BARE runner
 * (EMPTY_LOADOUT), so the recorded curve is untouched by the defense step by
 * design. This probe answers the other question: the gear the crafting system
 * now hands out. Paired seeds, so the delta is the gear, not the dice.
 *
 * Two views:
 *   - encounter — one non-boss encounter per mission, through `simulateCombat`
 *   - mission   — the whole mission, through `playRun` (the policy `survival`
 *                 uses), reported as mission completion % per grade
 *
 *   npm run gear
 */
import { missionGradeOf } from "../src/core/combat/ice_scaling";
import { EMPTY_LOADOUT, equipOn, makeLoadout } from "../src/core/state/loadout";
import {
  ARASAKA_DECK,
  BOOTS_GHOST,
  CHROME_GLOVES,
  CORPORATE_DECK,
  MASTER_BODY,
  MILITECH_EYES,
  STREET_DECK,
  SUBDERMAL,
  TACTICAL_BODY,
  TRODES_NINJA,
  ZION_TRODES,
  type Equipment,
} from "../src/core/state/equipment";
import { loadIceCatalog, loadMissionsCatalog, loadProgramsCatalog } from "../src/core/data_loaders";
import { deckForGrade, mulberry32, simulateCombat } from "./balance_sim";
import { playRun } from "./play_policy";
import iceJson from "../src/data/ice_types.json" with { type: "json" };
import missionsJson from "../src/data/missions.json" with { type: "json" };
import programsJson from "../src/data/programs.json" with { type: "json" };
import type { Mission } from "../src/core/types";

const ice = loadIceCatalog(iceJson);
const missions = loadMissionsCatalog(missionsJson);
const programs = loadProgramsCatalog(programsJson);
const ALL = Object.values(missions) as Array<Mission & { source_universe?: string }>;

const gear = (...items: Equipment[]) =>
  items.reduce((l, e) => equipOn(l, e).loadout, makeLoadout());

const SETS: ReadonlyArray<{ name: string; loadout: ReturnType<typeof makeLoadout> }> = [
  { name: "bare (recorded baseline)", loadout: EMPTY_LOADOUT },
  { name: "T1 street+eyes+gloves", loadout: gear(STREET_DECK, MILITECH_EYES, CHROME_GLOVES) },
  { name: "T2 corp+subdermal+ninja+boots", loadout: gear(CORPORATE_DECK, SUBDERMAL, TRODES_NINJA, BOOTS_GHOST) },
  { name: "T4 arasaka+body", loadout: gear(ARASAKA_DECK, TACTICAL_BODY) },
  { name: "T6 master+zion", loadout: gear(MASTER_BODY, ZION_TRODES) },
];

const GRADES = [1, 2, 3, 4, 5, 6];
const pad = (n: number, w = 3): string => n.toFixed(0).padStart(w);

const ENC_SEEDS = 40;
/** Matches `npm run survival -- --seeds 64` so the bare row reads as the
 *  recorded baseline (per-cell seed: `seed + missionIndex * 31`). */
const MIS_SEEDS = 64;

function gradeBuckets(): Array<[number, Mission[]]> {
  // No far-grid filter: `mission_survival` iterates the whole catalog, so the
  // bare row can be read against the recorded baseline.
  return GRADES.map((g) => [
    g,
    ALL.filter((m) => missionGradeOf(m) === g),
  ]);
}

console.log("gear curve probe — paired seeds, non-boss encounter / whole mission");
console.log("");

console.log("A) encounter — win% / HP remaining %");
console.log("set                              g1    g2    g3    g4    g5    g6");
for (const set of SETS) {
  const cells: string[] = [];
  for (const [grade, bucket] of gradeBuckets()) {
    const deck = deckForGrade(programs, grade);
    let wins = 0;
    let n = 0;
    let remain = 0;
    for (const mission of bucket) {
      for (let i = 0; i < ENC_SEEDS; i += 1) {
        const o = simulateCombat(mission, ice, deck, { seed: 1000 + i * 31 + grade }, set.loadout);
        n += 1;
        if (o.won) wins += 1;
        remain += o.hpEnd / Math.max(1, o.hpStart);
      }
    }
    cells.push(`${pad((wins / Math.max(1, n)) * 100)}/${pad((remain / Math.max(1, n)) * 100)}`);
  }
  console.log(`  ${set.name.padEnd(32)}${cells.join(" ")}`);
}

console.log("");
console.log("B) mission completion % (playRun policy, same seeds as `survival`)");
console.log("set                              g1    g2    g3    g4    g5    g6");
const originalRandom = Math.random;
const originalNow = Date.now;
try {
  for (const set of SETS) {
    const cells: string[] = [];
    for (const [, bucket] of gradeBuckets()) {
      let done = 0;
      let n = 0;
      for (let s = 0; s < MIS_SEEDS; s += 1) {
        const seed = 20261106 + s * 7919;
        for (const mission of bucket) {
          // Per-cell seed keyed on the FULL-catalog index, as `survival` does.
          const mi = ALL.indexOf(mission);
          const clockRef = { now: 1_700_000_000_000 + s * 100_000 };
          Math.random = mulberry32(seed + mi * 31);
          Date.now = () => clockRef.now;
          const final = playRun(
            mission,
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
            undefined,
            set.loadout,
          );
          n += 1;
          if (final?.runPhase === "ending") done += 1;
        }
      }
      cells.push(pad((done / Math.max(1, n)) * 100));
    }
    console.log(`  ${set.name.padEnd(32)}${cells.join(" ")}`);
  }
} finally {
  Math.random = originalRandom;
  Date.now = originalNow;
}
