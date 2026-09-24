/**
 * Balance simulation core.
 *
 * Drives the REAL combat reducer (`applyAction`) so a balance change can be
 * evaluated quantitatively instead of by feel. Nothing here reimplements
 * combat — it chooses inputs and reads outcomes, which is what makes the
 * numbers trustworthy.
 *
 * Two globals are controlled, because the reducer reads both at call time:
 *   - `Math.random` — combat variance, crits, status procs, enemy skill choice
 *   - `Date.now()`  — combat is time-gated by `AUTO_ATTACK_INTERVAL_MS`
 *
 * Combat is capped by hand size: `use_program` discards from hand and nothing
 * ever draws from `drawPile`, so a run that cannot kill within its opening hand
 * stalls. That is recorded as `stalled` rather than papered over.
 */
import { AUTO_ATTACK_INTERVAL_MS } from "../src/core/combat_engine";
import { resolveMatrixRoster } from "../src/core/matrix";
import { applyAction, makeInitialState } from "../src/core/state";
import type { GameState, Ice, Mission, Program } from "../src/core/types";

/** Deterministic PRNG (mulberry32) — same seed always yields the same stream. */
export function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export interface SimConfig {
  readonly seed: number;
  readonly maxTurns?: number;
}

export interface CombatOutcome {
  readonly won: boolean;
  readonly stalled: boolean;
  readonly turns: number;
  readonly hpStart: number;
  readonly hpEnd: number;
}

const DEFAULT_MAX_TURNS = 100;
const CLOCK_ORIGIN_MS = 1_000_000;

function isFighting(s: GameState): boolean {
  return s.runPhase === "combat" && s.phase === "combat";
}

/**
 * Run one encounter to completion through the real reducer.
 *
 * Navigation is skipped by placing the runner on the first node that holds
 * ICE: this measures the fight, not the pathing.
 */
export function simulateCombat(
  mission: Mission,
  iceCatalog: Readonly<Record<string, Ice>>,
  deck: ReadonlyArray<Program>,
  config: SimConfig,
): CombatOutcome {
  const maxTurns = config.maxTurns ?? DEFAULT_MAX_TURNS;
  const originalRandom = Math.random;
  const originalNow = Date.now;
  let clock = CLOCK_ORIGIN_MS;
  Math.random = mulberry32(config.seed);
  Date.now = () => clock;

  try {
    const fallback = Object.values(iceCatalog)[0];
    if (fallback === undefined) throw new Error("balance_sim: empty ICE catalog");

    const probe = makeInitialState(mission, fallback, deck);
    // Measure the mission's normal encounter: skip boss rooms so a boss spike
    // does not decide the reported win-rate. Falls back to any ICE node if no
    // non-boss encounter exists.
    const nodes = probe.matrix?.nodes ?? [];
    const encounterIdx = nodes.findIndex((n) => n.iceIds.length > 0 && !n.isBoss);
    const nodeIndex = encounterIdx >= 0 ? encounterIdx : nodes.findIndex((n) => n.iceIds.length > 0);
    const roster =
      nodeIndex >= 0 && probe.matrix !== null
        ? resolveMatrixRoster(probe.matrix, nodeIndex, iceCatalog)
        : null;
    const base = roster?.ice[0] ?? fallback;
    const hp = roster?.hp[0] ?? base.hp;
    const template = hp === base.hp ? base : { ...base, hp, maxHp: hp };

    let s = makeInitialState(mission, template, deck);
    if (nodeIndex >= 0) s = { ...s, currentNodeIndex: nodeIndex };

    clock += AUTO_ATTACK_INTERVAL_MS;
    s = applyAction(s, { type: "confirm" });
    clock += AUTO_ATTACK_INTERVAL_MS;
    s = applyAction(s, { type: "confirm" });

    const hpStart = s.player.hp;
    let turns = 0;
    let stalled = false;

    while (isFighting(s) && turns < maxTurns) {
      const card = s.deck[0];
      if (card === undefined) {
        stalled = true;
        break;
      }
      clock += AUTO_ATTACK_INTERVAL_MS;
      s = applyAction(s, { type: "use_program", programId: card.id });
      turns += 1;
    }

    return {
      won: s.runPhase === "loot" || s.runPhase === "ending",
      stalled,
      turns,
      hpStart,
      hpEnd: s.player.hp,
    };
  } finally {
    Math.random = originalRandom;
    Date.now = originalNow;
  }
}

export interface SuiteStats {
  readonly runs: number;
  readonly wins: number;
  readonly winRate: number;
  readonly stalls: number;
  readonly meanTurns: number;
  readonly meanHpEnd: number;
  readonly hpEndP5: number;
  readonly hpEndP95: number;
}

function percentile(sorted: ReadonlyArray<number>, p: number): number {
  if (sorted.length === 0) return 0;
  const idx = Math.min(sorted.length - 1, Math.max(0, Math.round((p / 100) * (sorted.length - 1))));
  return sorted[idx] ?? 0;
}

/** Run `runs` seeded encounters and aggregate the outcomes. */
export function runSuite(
  mission: Mission,
  iceCatalog: Readonly<Record<string, Ice>>,
  deck: ReadonlyArray<Program>,
  runs: number,
  baseSeed = 1,
  maxTurns?: number,
): SuiteStats {
  let wins = 0;
  let stalls = 0;
  let turnSum = 0;
  let hpSum = 0;
  const hpEnds: number[] = [];

  for (let i = 0; i < runs; i++) {
    const outcome = simulateCombat(mission, iceCatalog, deck, { seed: baseSeed + i, maxTurns });
    if (outcome.won) wins += 1;
    if (outcome.stalled) stalls += 1;
    turnSum += outcome.turns;
    hpSum += outcome.hpEnd;
    hpEnds.push(outcome.hpEnd);
  }

  hpEnds.sort((a, b) => a - b);
  return {
    runs,
    wins,
    winRate: runs === 0 ? 0 : wins / runs,
    stalls,
    meanTurns: runs === 0 ? 0 : turnSum / runs,
    meanHpEnd: runs === 0 ? 0 : hpSum / runs,
    hpEndP5: percentile(hpEnds, 5),
    hpEndP95: percentile(hpEnds, 95),
  };
}
