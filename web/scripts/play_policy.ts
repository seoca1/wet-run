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
import { fewestFightsNextHop } from "../src/core/dungeon/route_preview";
import { LOOT_REPAIR_SLOT } from "../src/core/state/loot_choice";
import { prepHpBonus } from "../src/core/state/prep";
import { programEffect } from "../src/core/combat/program_effects";
import { deckForGrade } from "./balance_sim";
import { missionGradeOf } from "../src/core/combat/ice_scaling";
import { rewardProgram } from "../src/core/state/card_reward";
import type { GameState, Ice, Mission, Program } from "../src/core/types";

export const COST_LIMIT = 100;
export const MAX_STEPS = 600;

/** How the runner picks from a card offer (ADR-0281 probe).
 *
 * `first` is the soak's original policy — take whatever is offered, which is
 * what a player who does not read the offer does. `best` spends the choice: the
 * offer pool is not tier-gated, so a grade-1 mission can be offered a tier-5
 * program, and taking the strongest one is how a run is supposed to scale.
 */
export type CardPolicy = "first" | "best";

/** How the runner picks routes (ADR-0281 measurement).
 *
 * `long` takes every unresolved encounter (nearest first) -- the run the design
 * assumes. `short` walks the fewest-fights line to the boss, which is the choice
 * the route card now prices: fewer fights, a thinner deck, a shorter mission. */
export type RoutePolicy = "long" | "short";

/** How the runner spends a loot stop (ADR-0282).
 *
 * `card` grows the deck and never repairs — the old automatic heal meant this
 * was free. `repair` always takes the HP. `smart` repairs below half health,
 * which is what the choice is for. */
export type LootPolicy = "card" | "repair" | "smart";

/** Higher is better: armour answers first, then tier (damage is tier * 5). */
function cardScore(p: Program): number {
  const effect = programEffect(p);
  const armorAnswer =
    effect.kind === "armor_ignore" ? 2 : effect.kind === "pierce" ? 1 : 0;
  return armorAnswer * 100 + p.tier;
}

/** The hand slot (1-based) the policy picks from an offer. */
export function pickRewardIndex(
  offers: ReadonlyArray<Program | undefined>,
  policy: CardPolicy,
): number {
  if (policy === "first") return 1;
  let bestIdx = 1;
  let bestScore = -1;
  for (let i = 0; i < offers.length; i += 1) {
    const p = offers[i];
    if (!p) continue;
    const score = cardScore(p);
    if (score > bestScore) {
      bestScore = score;
      bestIdx = i + 1;
    }
  }
  return bestIdx;
}

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

/** Card lookup for the reward policy (name shadows nothing here). */
function cardOf(id: string): Program | undefined {
  return rewardProgram(id);
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

/** The nearest node that still holds an unresolved encounter.
 *
 * This used to route straight for the boss, and BFS happily found an ICE-free
 * path: `first_jack` is `0 -> 2 -> 5` with the only normal encounter at node 1,
 * so the runner skipped it. That made every measurement a **boss-only** run --
 * no normal fight, therefore no card reward, therefore no deck growth, which
 * hid the very build-up the run is built around.
 *
 * The policy now walks to the closest unresolved encounter, which is what
 * playing the mission means.
 */
function objective(
  state: GameState,
  routePolicy: RoutePolicy = "long",
): number | null {
  const nodes = state.matrix?.nodes ?? [];
  if (nodes.length === 0) return null;
  if (routePolicy === "short") {
    // Fewest fights to the boss: skip what can be walked past.
    return fewestFightsNextHop(
      state.matrix as never,
      state.clearedEncounterNodes ?? [],
      state.bypassedEncounterNodes ?? [],
      state.currentNodeIndex,
    );
  }
  const cleared = new Set(state.clearedEncounterNodes ?? []);
  const bypassed = new Set(state.bypassedEncounterNodes ?? []);
  const blocked = (i: number): boolean =>
    cleared.has(i) ||
    bypassed.has(i) ||
    (nodes[i]?.iceIds.length ?? 0) === 0;
  if (blocked(state.currentNodeIndex) === false)
    return state.currentNodeIndex; // standing on one
  const seen = new Set<number>([state.currentNodeIndex]);
  const queue: number[] = [state.currentNodeIndex];
  while (queue.length > 0) {
    const at = queue.shift() as number;
    for (const nx of nodes[at]?.adjacent ?? []) {
      if (seen.has(nx)) continue;
      seen.add(nx);
      if (!blocked(nx)) return nx;
      queue.push(nx);
    }
  }
  return state.matrix?.bossNode ?? null;
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
  cardPolicy: CardPolicy = "first",
  deckMode: "opening" | "ppl" = "opening",
  routePolicy: RoutePolicy = "long",
  lootPolicy: LootPolicy = "card",
  hpBonus = 0,
  handBonus = 0,
): GameState | null {
  const fallback = Object.values(catalog)[0];
  if (!fallback) return null;
  // `ppl` = the grade-appropriate deck `balance_sim.deckForGrade` builds (every
  // program of tier <= grade, strongest five). Used to test whether a stronger
  // STARTING deck is the lever, as opposed to cards earned during the run.
  const deck =
    deckMode === "ppl"
      ? deckForGrade(programCatalog, mission.grade ?? 1)
      : startingDeck(programCatalog, jockeyId);
  let state = makeInitialState(mission, fallback, deck);
  // ADR-0283 (C'): prep buys CAPACITY, not cards -- extra max HP is the most
  // local form of it. Applied here so the lever can be measured before any
  // screen is built (the card-prep shop was built first and then rejected).
  // ADR-0283 (C'): a bigger hand is the other way to add capacity -- it raises
  // the damage a turn can deliver instead of the HP it can absorb.
  if (handBonus > 0) {
    state = {
      ...state,
      player: { ...state.player, handSize: state.player.handSize + handBonus },
    };
  }
  const prepBonus =
    hpBonus > 0 ? hpBonus : prepHpBonus(missionGradeOf(mission));
  if (prepBonus > 0) {
    const maxHp = state.player.maxHp + prepBonus;
    state = {
      ...state,
      player: { ...state.player, maxHp, hp: maxHp },
    };
  }
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
        const goal = objective(state, routePolicy);
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
          const wantRepair =
            lootPolicy === "repair" ||
            (lootPolicy === "smart" &&
              state.player.hp < Math.floor(state.player.maxHp * 0.5));
          const offers = ids.map((id) => cardOf(id));
          state = applyAction(state, {
            type: "select_program",
            handIndex: wantRepair
              ? LOOT_REPAIR_SLOT
              : pickRewardIndex(offers, cardPolicy),
          });
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
