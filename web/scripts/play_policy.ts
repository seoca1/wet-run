/** Shared run policy — one "plausible player", one deterministic driver.
 *
 * The soak (`e2e/soak_playthrough.spec.ts`) drives real keys against the real
 * build, which is the browser evidence but is slow and (before ADR-0280) moved
 * with the wall clock. These in-process runners walk the *same policy* through
 * the reducer with a seeded `Math.random`, so a distribution can be compared
 * before and after a change, and measured over many seeds.
 *
 * The policy is the soak's "expensive": the highest-tier affordable card,
 * BREACH over BYPASS, take the first offered reward. A plausible player, not an
 * optimiser.
 */
import { applyAction, makeInitialState } from "../src/core/state/state";
import { startingDeck } from "../src/core/state/starting_deck";
import { offeredCardIds } from "../src/core/state/card_reward";
import { isTerminalNode } from "../src/core/state/run_end";
import type { GameState, Ice, Mission, Program } from "../src/core/types";

export const COST_LIMIT = 100;
export const MAX_STEPS = 600;

/** Mulberry32 — the same PRNG the balance harness uses. */
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

/** The first node that still holds an unresolved encounter, preferring the boss. */
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

/** One full run with the greedy policy. Returns the final state.
 *
 * `clock` is advanced so `Date.now()`-reading helpers (death summaries, entity
 * ids) stay deterministic; the enemy phase no longer reads a clock.
 */
export function playRun(
  mission: Mission,
  catalog: Readonly<Record<string, Ice>>,
  programCatalog: Readonly<Record<string, Program>>,
  clockRef: { now: number },
  jockeyId = "novice",
): GameState | null {
  const fallback = Object.values(catalog)[0];
  if (!fallback) return null;
  let state = makeInitialState(
    mission,
    fallback,
    startingDeck(programCatalog, jockeyId),
  );
  for (let step = 0; step < MAX_STEPS; step += 1) {
    if (state.runPhase === "ending" || state.runPhase === "dead") return state;
    const before = state;
    clockRef.now += 50;

    if (state.runPhase === "matrix") {
      if (state.encounterDecision) {
        for (let i = 0; i < 8; i += 1) {
          if (state.encounterDecision?.selectedVerb === "BREACH") break;
          state = applyAction(state, { type: "move_south" });
        }
        if (state.encounterDecision?.selectedVerb !== "BREACH") {
          state = applyAction(state, { type: "move_north" });
          continue;
        }
        state = applyAction(state, { type: "confirm" });
      } else {
        const goal = objective(state);
        const hop =
          goal === null || goal === state.currentNodeIndex
            ? null
            : nextStep(state, state.currentNodeIndex, goal);
        if (hop !== null) {
          const neighbours =
            state.matrix?.nodes[state.currentNodeIndex]?.adjacent ?? [];
          for (let i = 0; i < neighbours.length + 1; i += 1) {
            if (state.selectedMatrixNodeIndex === hop) break;
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
      if (best) {
        state = applyAction(state, { type: "use_program", programId: best.p.id });
      } else {
        state = applyAction(state, { type: "confirm" });
      }
    } else if (state.runPhase === "loot") {
      if (!isTerminalNode(state)) {
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
