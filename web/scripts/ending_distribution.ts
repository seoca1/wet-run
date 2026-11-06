/** Ending distribution — deterministic full runs across the mission list.
 *
 * ADR-0279 changed two things a balance table cannot see:
 *   1. the mission reward is paid once (on the fight that ends the mission)
 *      instead of on every encounter win, and
 *   2. the ending resolver reads `player.credits` (what the run earned, and
 *      what the ending screen prints) instead of `inventory.credits` (the
 *      mission's base reward, seeded for crafting and never grown by combat).
 *
 * The soak plays real key presses with an unseeded clock, so its ending counts
 * move between sweeps. This walks the same policy in-process with a seeded
 * `Math.random` and a controlled `Date.now`, so a distribution can be compared
 * before and after a change.
 *
 *   npm run endings                 # every mission, greedy policy
 *   npm run endings -- --verbose    # one line per run
 *   npm run endings -- --credits inventory   # resolve from the OLD source
 *
 * The policy is the soak's "expensive": the highest-tier affordable card,
 * BREACH over BYPASS, take the first offered reward. A plausible player.
 */
import { loadIceCatalog, loadMissionsCatalog, loadProgramsCatalog } from "../src/core/data_loaders";
import { applyAction, makeInitialState } from "../src/core/state/state";
import { startingDeck } from "../src/core/state/starting_deck";
import { AUTO_ATTACK_INTERVAL_MS } from "../src/core/combat/combat_engine";
import { offeredCardIds } from "../src/core/state/card_reward";
import { isTerminalNode } from "../src/core/state/run_end";
import { resolveEnding } from "../src/core/combat/ending_resolver";
import { missionGradeOf } from "../src/core/combat/ice_scaling";
import type { GameState, Mission } from "../src/core/types";
import iceJson from "../src/data/ice_types.json" with { type: "json" };
import missionsJson from "../src/data/missions.json" with { type: "json" };
import programsJson from "../src/data/programs.json" with { type: "json" };

const VERBOSE = process.argv.includes("--verbose");
const creditsIdx = process.argv.indexOf("--credits");
const CREDITS_SOURCE: "player" | "inventory" =
  creditsIdx >= 0 && process.argv[creditsIdx + 1] === "inventory"
    ? "inventory"
    : "player";
const SEED = Number(
  process.argv[process.argv.indexOf("--seed") + 1] ?? 20261105,
) || 20261105;
/**
 * Enemy ticks per action. `1` is the balance harness's convention (one enemy
 * phase per played action) — the project's own time model. `0` disables the
 * enemy phase entirely, which is the optimistic bound: `processEnemyTurns`
 * returns early inside `AUTO_ATTACK_INTERVAL_MS`, so combat costs almost no HP.
 *
 * Neither is "real play": a human deliberating on a card spends ~1-3s, i.e.
 * roughly one tick per action, while a scripted key press is ~20ms and gates
 * the enemy off. Report both so an HP reading cannot be mistaken for a fact.
 */
const TICK_EVERY = (() => {
  const i = process.argv.indexOf("--tick-every");
  const raw = i >= 0 ? Number(process.argv[i + 1]) : 1;
  return Number.isFinite(raw) && raw >= 0 ? raw : 1;
})();
const COST_LIMIT = 100;
const MAX_STEPS = 600;

function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Shortest-path first step from `from` to `to` on the matrix. */
function nextStep(state: GameState, from: number, to: number): number | null {
  const nodes = state.matrix?.nodes ?? [];
  const prev = new Map<number, number>();
  const seen = new Set<number>([from]);
  const queue: number[] = [from];
  while (queue.length > 0) {
    const at = queue.shift() as number;
    if (at === to) {
      let step = to;
      while ((prev.get(step) ?? from) !== from) step = prev.get(step) as number;
      return step;
    }
    for (const nx of nodes[at]?.adjacent ?? []) {
      if (seen.has(nx)) continue;
      seen.add(nx);
      prev.set(nx, at);
      queue.push(nx);
    }
  }
  return null;
}

/** The first node that still holds an unresolved encounter, or the boss. */
function objective(state: GameState): number | null {
  const nodes = state.matrix?.nodes ?? [];
  const cleared = new Set(state.clearedEncounterNodes ?? []);
  const bypassed = new Set(state.bypassedEncounterNodes ?? []);
  const boss = state.matrix?.bossNode ?? -1;
  for (let i = 0; i < nodes.length; i += 1) {
    if (cleared.has(i) || bypassed.has(i)) continue;
    if (nodes[i].isBoss) return i;
  }
  for (let i = 0; i < nodes.length; i += 1) {
    if (cleared.has(i) || bypassed.has(i)) continue;
    if (nodes[i].iceIds.length > 0) return i;
  }
  return boss >= 0 ? boss : null;
}

/** One full run with the greedy policy. Returns the final state or null.
 *
 * `clock` advances by one enemy tick per action, exactly as `balance_sim.ts`
 * does. Without it the enemy phase is gated off (`processEnemyTurns` returns
 * early inside `AUTO_ATTACK_INTERVAL_MS`), combat costs almost no HP, and any
 * HP-based reading would be a fiction.
 */
function playRun(mission: Mission, catalog: ReturnType<typeof loadIceCatalog>): GameState | null {
  const fallback = Object.values(catalog)[0];
  if (!fallback) return null;
  let state = makeInitialState(mission, fallback, startingDeck(programs, "novice"));
  for (let step = 0; step < MAX_STEPS; step += 1) {
    if (state.runPhase === "ending" || state.runPhase === "dead") return state;
    const before = state;
    if (TICK_EVERY > 0) clock += AUTO_ATTACK_INTERVAL_MS * TICK_EVERY;

    if (state.runPhase === "matrix") {
      if (state.encounterDecision) {
        // Cycle the verb list to BREACH, then commit.
        for (let i = 0; i < 8; i += 1) {
          if (state.encounterDecision?.selectedVerb === "BREACH") break;
          state = applyAction(state, { type: "move_south" });
        }
        if (state.encounterDecision?.selectedVerb !== "BREACH") {
          // BREACH unavailable — JACK OUT would end the run, so travel on.
          state = applyAction(state, { type: "move_north" });
          continue;
        }
        state = applyAction(state, { type: "confirm" });
      } else {
        const goal = objective(state);
        const step_ =
          goal === null || goal === state.currentNodeIndex
            ? null
            : nextStep(state, state.currentNodeIndex, goal);
        if (step_ !== null) {
          // Press forward until the target is highlighted (the selector starts
          // unset, so the first press lands on neighbour 0). Capped by the
          // neighbour count + 1, exactly as the soak does.
          const neighbours = state.matrix?.nodes[state.currentNodeIndex]?.adjacent ?? [];
          for (let i = 0; i < neighbours.length + 1; i += 1) {
            if (state.selectedMatrixNodeIndex === step_) break;
            state = applyAction(state, { type: "move_south" });
          }
        }
        state = applyAction(state, { type: "confirm" });
      }
    } else if (state.phase === "approach") {
      state = applyAction(state, { type: "confirm" });
    } else if (state.phase === "combat") {
      const affordable = state.deck
        .map((p, i) => ({ p, slot: i + 1 }))
        .filter(({ p }) => state.player.alarm + p.cost <= COST_LIMIT)
        .sort((a, b) => b.p.tier - a.p.tier || a.p.cost - b.p.cost);
      const best = affordable[0];
      if (best) state = applyAction(state, { type: "use_program", programId: best.p.id });
      else state = applyAction(state, { type: "confirm" });
    } else if (state.runPhase === "loot") {
      const terminal = isTerminalNode(state);
      if (!terminal) {
        const ids = offeredCardIds(state);
        if (state.cardRewardTaken === null && ids.length > 0) {
          state = applyAction(state, { type: "select_program", handIndex: 1 });
        }
      }
      state = applyAction(state, { type: "confirm" });
    } else {
      break;
    }

    if (state === before) return state; // frozen
  }
  return state;
}

const ice = loadIceCatalog(iceJson);
const programs = loadProgramsCatalog(programsJson);
const missions = loadMissionsCatalog(missionsJson);

const originalRandom = Math.random;
const originalNow = Date.now;
let clock = 1_700_000_000_000;
Math.random = mulberry32(SEED);
Date.now = () => clock;

const rows: Array<{
  id: string;
  grade: number;
  ending: string;
  credits: number;
  baseCredits: number;
  hp: number;
  maxHp: number;
}> = [];

try {
  for (const mission of Object.values(missions)) {
    clock += AUTO_ATTACK_INTERVAL_MS;
    const finalState = playRun(mission, ice);
    if (finalState === null || finalState.endingChoice === null) {
      rows.push({
        id: mission.id,
        grade: missionGradeOf(mission),
        ending: `(${finalState?.runPhase ?? "no-state"})`,
        credits: finalState?.player.credits ?? 0,
        baseCredits: finalState?.inventory.credits ?? 0,
        hp: finalState?.player.hp ?? 0,
        maxHp: finalState?.player.maxHp ?? 0,
      });
      continue;
    }
    // Resolve from the chosen credit source, so a distribution can be compared
    // across the ADR-0279 change without re-running.
    const ctx = {
      arc: (mission.arc ?? 1) as 1,
      hp: finalState.player.hp,
      maxHp: finalState.player.maxHp,
      credits:
        CREDITS_SOURCE === "player"
          ? finalState.player.credits
          : finalState.inventory.credits,
      missionsCompleted: 1,
      totalDeaths: finalState.totalDeaths,
      factionScores: finalState.factionScores,
      choices: [],
    };
    rows.push({
      id: mission.id,
      grade: missionGradeOf(mission),
      ending: resolveEnding(ctx).id,
      credits: finalState.player.credits,
      baseCredits: finalState.inventory.credits,
      hp: finalState.player.hp,
      maxHp: finalState.player.maxHp,
    });
  }
} finally {
  Math.random = originalRandom;
  Date.now = originalNow;
}

const counts = new Map<string, number>();
for (const r of rows) counts.set(r.ending, (counts.get(r.ending) ?? 0) + 1);
const died = rows.filter((r) => r.ending === "(dead)").length;
const earned = rows.reduce((a, r) => a + r.credits, 0);
const base = rows.reduce((a, r) => a + r.baseCredits, 0);

console.log(
  `ending distribution — ${rows.length} missions, seed ${SEED}, policy "expensive", resolver credits=${CREDITS_SOURCE}, tick-every=${TICK_EVERY}`,
);
console.log("");
console.log("ending                    n   share");
for (const [id, n] of [...counts.entries()].sort((a, b) => b[1] - a[1])) {
  console.log(
    `${id.padEnd(24)} ${String(n).padStart(3)}   ${((n / rows.length) * 100).toFixed(1)}%`,
  );
}
console.log("");
console.log(
  `mean earned (player.credits): ${(earned / rows.length).toFixed(0)}  ·  mean mission base: ${(base / rows.length).toFixed(0)}`,
);
const over = rows.filter((r) => r.credits > 5000).length;
console.log(`runs with player.credits > 5000: ${over}/${rows.length}`);

// ADR-0279 open question (a): how often does the `control` branch's HP gate
// actually hold? The loot heal is 15%, so "full HP at the ending" is not a
// given. Report the gate's two halves separately and together.
const withHp = rows.filter((r) => r.maxHp > 0);
const hpOk = withHp.filter((r) => r.hp / r.maxHp > 0.75).length;
const both = withHp.filter((r) => r.hp / r.maxHp > 0.75 && r.credits > 5000).length;
const controlEndings = rows.filter((r) => r.ending.includes("control")).length;
console.log("");
console.log(`hp > 75% at the ending: ${hpOk}/${withHp.length}`);
console.log(`hp > 75% AND credits > 5000 (the control gate): ${both}/${withHp.length}`);
console.log(`control endings actually resolved: ${controlEndings}/${rows.length}`);
console.log(`runs that flatlined before the ending: ${died}/${rows.length}`);
const hpHist = new Map<string, number>();
for (const r of withHp) {
  const pct = r.maxHp > 0 ? (r.hp / r.maxHp) * 100 : 0;
  const bucket =
    pct >= 100 ? "100%" : pct >= 76 ? "76-99%" : pct >= 51 ? "51-75%" : pct >= 26 ? "26-50%" : "0-25%";
  hpHist.set(bucket, (hpHist.get(bucket) ?? 0) + 1);
}
console.log("hp at the ending:");
for (const b of ["100%", "76-99%", "51-75%", "26-50%", "0-25%"]) {
  console.log(`  ${b.padEnd(7)} ${hpHist.get(b) ?? 0}`);
}

if (VERBOSE) {
  console.log("");
  for (const r of rows.sort((a, b) => a.grade - b.grade || a.id.localeCompare(b.id))) {
    console.log(
      `  g${r.grade} ${r.id.padEnd(28)} ${r.ending.padEnd(24)} hp ${r.hp}/${r.maxHp} cr ${r.credits} (base ${r.baseCredits})`,
    );
  }
}
