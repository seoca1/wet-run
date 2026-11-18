/** Gear curve probe — what the ADR-0326 stats do once a runner wears them.
 *
 * `npm run balance` measures the BARE runner (EMPTY_LOADOUT), so the recorded
 * curve is untouched by the defense step by design. This probe answers the
 * other question: the gear the crafting system now hands out. It replays the
 * same deterministic seeds through the real reducer (`simulateCombat`) with a
 * loadout, one non-boss encounter per mission.
 *
 * Report: `win% / HP remaining %`. Paired seeds mean the delta is the gear.
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
import { deckForGrade, simulateCombat } from "./balance_sim";
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

const SEEDS = 40;

console.log("gear curve probe — paired seeds, one non-boss encounter per mission");
console.log("set                              g1    g2    g3    g4    g5    g6   (win% / HP remaining %)");
for (const set of SETS) {
  const cells: string[] = [];
  for (const grade of [1, 2, 3, 4, 5, 6]) {
    const bucket = ALL.filter(
      (m) => m.source_universe !== "far-grid" && missionGradeOf(m) === grade,
    );
    const deck = deckForGrade(programs, grade);
    let wins = 0;
    let n = 0;
    let remain = 0;
    for (const mission of bucket) {
      for (let i = 0; i < SEEDS; i += 1) {
        const o = simulateCombat(mission, ice, deck, { seed: 1000 + i * 31 + grade }, set.loadout);
        n += 1;
        if (o.won) wins += 1;
        remain += o.hpEnd / Math.max(1, o.hpStart);
      }
    }
    cells.push(
      `${((wins / Math.max(1, n)) * 100).toFixed(0).padStart(3)}/${((remain / Math.max(1, n)) * 100).toFixed(0).padStart(3)}`,
    );
  }
  console.log(`  ${set.name.padEnd(32)}${cells.join(" ")}`);
}
