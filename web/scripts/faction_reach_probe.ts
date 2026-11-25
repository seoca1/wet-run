/** Faction reachability probe — can a contract push a faction score to the
 * FRIENDLY gate (50)?
 *
 * `resolveEnding`'s second gate needs a faction score >= 50 to fire
 * (`ending_resolver.ts:376-381`). No ending declares `requiresFaction` today
 * (tracked by the `it.fails` test in `tests/design_conformance.test.ts:188`),
 * so the branch is dead by *data*. This probe answers the question that decides
 * whether adding that data would revive anything: **is 50 reachable inside one
 * run at all?**
 *
 * It is deterministic — faction deltas depend only on mission and ICE ids, not
 * on play — so this is an enumeration, not a simulation.
 *
 * Rules (both small and pure):
 *   +10  a completed mission of that faction  (`MISSION_REWARD_MAP`)
 *    -5  each ICE killed of that faction      (`KILL_PENALTY_MAP`)
 * Mission faction: replicated from `getMissionFaction`
 * (`state_actions_phases.ts:757-763`) because it is not exported; ICE faction
 * from the exported `iceFactionOf` (`combat/victory.ts:43`).
 *
 *   npm run faction-reach
 */
import missionsData from "../src/data/missions.json" with { type: "json" };
import iceTypesData from "../src/data/ice_types.json" with { type: "json" };
import { loadMissionsCatalog, loadIceCatalog } from "../src/core/data_loaders";
import { filterMissionsByUniverse } from "../src/core/missions_filter";
import { contractFor, CONTRACT_LENGTH } from "../src/core/state/campaign";
import { missionIce } from "../src/core/state/mission_ice";
import { iceFactionOf } from "../src/core/combat/victory";
import {
  DEFAULT_FACTION_SCORES,
  KILL_PENALTY_MAP,
  MISSION_REWARD_MAP,
  TIER_THRESHOLDS,
  type FactionId,
  type FactionScores,
} from "../src/core/state/faction_reputation";
import type { Mission, Ice } from "../src/core/types";

const MISSIONS: ReadonlyArray<Mission> = loadMissionsCatalog(missionsData);
const ICE_TYPES: Readonly<Record<string, Ice>> = loadIceCatalog(iceTypesData);

/** Mirrors `getMissionFaction` (not exported) — same substring rule, same order. */
function missionFactionOf(missionId: string): FactionId | null {
  if (missionId.includes("hosaka")) return "hosaka";
  if (missionId.includes("maas")) return "maas";
  if (missionId.includes("sense") || missionId.includes("net")) return "sense_net";
  if (missionId.includes("ta")) return "ta";
  return null;
}

const FRIENDLY = TIER_THRESHOLDS.find((t) => t.tier === "FRIENDLY")?.min ?? 50;

function main(): void {
  const starts = filterMissionsByUniverse(MISSIONS, "sprawl");
  const best: { score: number; start: string; trace: string }[] = [];
  let maxSeen = 0;
  const perFactionMax: Record<string, number> = {};

  for (const start of starts) {
    const contract = contractFor(start, MISSIONS, (m) => missionIce(m, ICE_TYPES));
    let scores: FactionScores = DEFAULT_FACTION_SCORES;
    const trace: string[] = [];

    for (const leg of contract.legs) {
      const mf = missionFactionOf(leg.mission.id);
      if (mf) {
        scores = {
          ...scores,
          [mf]: (scores[mf] ?? 0) + (MISSION_REWARD_MAP[mf] ?? 10),
        };
      }
      const iceFaction = iceFactionOf(leg.ice.id);
      if (iceFaction) {
        scores = {
          ...scores,
          [iceFaction]: (scores[iceFaction] ?? 0) + (KILL_PENALTY_MAP[iceFaction] ?? -5),
        };
      }
      trace.push(`${leg.mission.id}[${mf ?? "-"}] ice=${leg.ice.id}[${iceFaction ?? "-"}]`);
    }

    for (const [faction, score] of Object.entries(scores)) {
      perFactionMax[faction] = Math.max(perFactionMax[faction] ?? -999, score);
      maxSeen = Math.max(maxSeen, score);
    }
    const top = Math.max(...Object.values(scores));
    best.push({ score: top, start: start.id, trace: trace.join(" → ") });
  }

  console.log(
    `faction reach over ${starts.length} contracts (CONTRACT_LENGTH=${CONTRACT_LENGTH}), ` +
      `FRIENDLY gate = ${FRIENDLY}\n`,
  );
  console.log("per-faction best score at the end of leg 3:");
  for (const [faction, score] of Object.entries(perFactionMax).sort((a, b) => b[1] - a[1])) {
    console.log(`  ${faction.padEnd(10)} ${String(score).padStart(4)}`);
  }
  console.log(`\nbest single score reached by any contract: ${maxSeen}  (gate ${FRIENDLY})`);
  console.log(
    maxSeen >= FRIENDLY
      ? "→ the gate IS reachable inside one contract"
      : "→ the gate is NOT reachable inside one contract",
  );

  const top3 = best.sort((a, b) => b.score - a.score).slice(0, 3);
  console.log("\nthe three contracts that come closest:");
  for (const t of top3) console.log(`  ${String(t.score).padStart(3)}  ${t.start}: ${t.trace}`);

  const net = Object.entries(MISSION_REWARD_MAP).map(
    ([f, v]) => `${f} +${v}/mission ${KILL_PENALTY_MAP[f as FactionId] ?? 0}/kill`,
  );
  console.log(`\nper-event rules: ${net.join(" · ")}`);
  console.log(
    `maximum possible in ${CONTRACT_LENGTH} legs (all same faction, no kills of it): ` +
      `${(MISSION_REWARD_MAP.hosaka ?? 10) * CONTRACT_LENGTH}`,
  );
}

main();
