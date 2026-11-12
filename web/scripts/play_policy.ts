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
import { offeredCardIds, UNIQUE_PROGRAMS, uniqueChoicesFor } from "../src/core/state/card_reward";
import { isTerminalNode } from "../src/core/state/run_end";
import { fewestFightsNextHop } from "../src/core/dungeon/route_preview";
import { bossGateNeed } from "../src/core/combat/ice_scaling";
import {
  LOOT_BURN_SLOT,
  LOOT_INTEL_SLOT,
  LOOT_RECOVER_SLOT,
  canRecover,
  LOOT_REPAIR_SLOT,
  LOOT_VENT_SLOT,
  lootRepairAmount,
  ventHpPrice,
} from "../src/core/state/loot_choice";
import { burnTarget } from "../src/core/state/state_actions_phases";
import { prepGrantFor, type PrepChoice } from "../src/core/state/prep";
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
export type RoutePolicy = "long" | "short" | "intel" | "picky" | "blind";

/** "Beatable" threshold for `picky`: tier + armour, the ADR-0287 measure.
 *
 * 12 is above the grade-3 band (8-9) and below the grade-4/5 apexes (11-14), so
 * the policy fights what the opening deck can crack and walks past what it
 * cannot. The point of the experiment is that this judgement needs the ICE, not
 * the count. */
export const DEFAULT_ICE_LIMIT = 12;

/** How the runner spends a loot stop (ADR-0282).
 *
 * `card` grows the deck and never repairs — the old automatic heal meant this
 * was free. `repair` always takes the HP. `smart` repairs below half health,
 * which is what the choice is for. */
export type LootPolicy =
  | "card"
  | "repair"
  | "smart"
  | "intel"
  | "smartintel"
  | "smartvent"
  | "smartburn"
  | "smartcombo"
  | "smartrecover"
  | "value"
  | "valueunique"
  | "valuecard";

/** Higher is better: armour answers first, then tier (damage is tier * 5). */
function cardScore(p: Program): number {
  const effect = programEffect(p);
  const armorAnswer =
    effect.kind === "armor_ignore" ? 2 : effect.kind === "pierce" ? 1 : 0;
  // ADR-0303: COST is the run's scarcest resource after the trace (ADR-0294), so
  // a card that cannot be paid for is not a card. Ignoring cost made the policy
  // grab every expensive program and then sit on it, which is wrong play and a
  // broken instrument — it under-reported what a cost-efficient card is worth.
  //
  // ADR-0304: the second axis is damage per COST, not raw damage. A big card the
  // run cannot afford is not a card (ADR-0303 found that the hard way), so the
  // instrument now prices the two together.
  //
  // A deck-awareness term (discount a third copy of the same effect) was tried
  // first and measured as INERT: +0.2pp on the mean, and the coefficient did not
  // matter (1.0 / 0.5 / 0.25 all identical). The offers rarely repeat a kind, so
  // there was nothing to discount. It was removed rather than left in as a
  // plausible-looking knob.
  // sqrt, not a straight division: a linear penalty over-rewards the cheapest
  // card and cost g3 4.9pp in the sweep (its COST budget is not tight), while
  // sqrt held every grade's gain. Measured mean +26.4pp against +24.5 linear and
  // +22.1 for the old cost-blind score.
  const perCost = (p.tier * 5) / Math.sqrt(Math.max(1, p.cost));
  return armorAnswer * 60 + perCost * 6;
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
/** The nearest unresolved encounter — the "fight everything" objective.
 *
 * The boss is not a *nearest encounter* while the core is sealed (ADR-0290): it
 * is adjacency-first in most graphs, so treating it as one makes the policy walk
 * into the seal and stop there. Once the seal is open the boss is a fine
 * destination, and standing on it ends the walk by returning the current node.
 */
function nearestObjective(state: GameState): number | null {
  const nodes = state.matrix?.nodes ?? [];
  if (nodes.length === 0) return null;
  const boss = state.matrix?.bossNode ?? null;
  const cleared = new Set(state.clearedEncounterNodes ?? []);
  const bypassed = new Set(state.bypassedEncounterNodes ?? []);
  const sealed = (state.clearedEncounterNodes ?? []).length < bossGateNeed(state);
  const target = (i: number): boolean => {
    const n = nodes[i];
    if (!n || n.iceIds.length === 0) return false;
    if (cleared.has(i) || bypassed.has(i)) return false;
    return !(sealed && i === boss);
  };
  if (target(state.currentNodeIndex)) return state.currentNodeIndex;
  const seen = new Set<number>([state.currentNodeIndex]);
  const queue: number[] = [state.currentNodeIndex];
  while (queue.length > 0) {
    const at = queue.shift() as number;
    for (const nx of nodes[at]?.adjacent ?? []) {
      if (seen.has(nx)) continue;
      seen.add(nx);
      if (target(nx)) return nx;
      queue.push(nx);
    }
  }
  return boss;
}

/** Where to head next, given the route policy (ADR-0281 / ADR-0287). */
/** Is the apex closed until more encounters are cleared? (ADR-0290) */
function bossSealed(state: GameState): boolean {
  return (state.clearedEncounterNodes ?? []).length < bossGateNeed(state);
}

function objective(
  state: GameState,
  routePolicy: RoutePolicy = "long",
  catalog: Readonly<Record<string, Ice>> = {},
  iceLimit = DEFAULT_ICE_LIMIT,
): number | null {
  const nodes = state.matrix?.nodes ?? [];
  if (nodes.length === 0) return null;
  const cleared = new Set(state.clearedEncounterNodes ?? []);
  const bypassed = new Set(state.bypassedEncounterNodes ?? []);

  if (routePolicy === "intel") {
    // ADR-0287: walk toward the WEAKEST revealed encounter (lowest tier +
    // armour). That is what bought information is for. Without intel there is
    // nothing to read, so it falls back to the nearest.
    const intel = new Set(state.intelNodes ?? []);
    const candidates = [...intel].filter((i) => {
      const n = nodes[i];
      return n && n.iceIds.length > 0 && !cleared.has(i) && !bypassed.has(i);
    });
    if (candidates.length === 0) return nearestObjective(state);
    const strength = (i: number): number => {
      const id = nodes[i]?.iceIds[0];
      const ice = id ? catalog[id] : undefined;
      return (ice?.tier ?? 1) + (ice?.armor ?? 0);
    };
    const weakest = [...candidates].sort(
      (a, b) => strength(a) - strength(b) || a - b,
    )[0];
    return weakest ?? nearestObjective(state);
  }

  if (routePolicy === "picky") {
    // Fight only what the hand can crack. Without bought intel this policy has
    // no ICE to read, so it degrades to "fight everything" — which is exactly
    // the comparison the experiment needs.
    const intel = new Set(state.intelNodes ?? []);
    const strength = (i: number): number => {
      const id = nodes[i]?.iceIds[0];
      const ice = id ? catalog[id] : undefined;
      return (ice?.tier ?? 1) + (ice?.armor ?? 0);
    };
    const open = [...intel].filter((i) => {
      const n = nodes[i];
      return n && n.iceIds.length > 0 && !cleared.has(i) && !bypassed.has(i);
    });
    const beatable = open.filter((i) => strength(i) <= iceLimit);
    if (beatable.length > 0) {
      const target = [...beatable].sort(
        (a, b) => strength(a) - strength(b) || a - b,
      )[0];
      return target ?? nearestObjective(state);
    }
    // Nothing worth fighting: head for the end — unless the core is sealed
    // (ADR-0290), in which case something has to fall.
    if (bossSealed(state)) return nearestObjective(state);
    return state.matrix?.bossNode ?? null;
  }

  if (routePolicy === "blind") {
    // ADR-0290 (d): the honest test of what bought intel is worth.
    //
    // Every other policy reads `matrix.nodes` straight out of the state, so it
    // knows the ICE on a route whether or not the runner paid for it -- which
    // makes information worthless to it by construction, and is exactly why
    // ADR-0287 could not price the sink.
    //
    // `blind` refuses to look. With no bought intel it takes the nearest
    // unresolved encounter, the way a player who knows nothing does. With intel
    // it takes the WEAKEST revealed one. Same runner, same board, same gate --
    // the only difference is whether the information was paid for, so the
    // difference in completion IS the value of the information.
    if (!bossSealed(state)) return state.matrix?.bossNode ?? null;
    const intel = new Set(state.intelNodes ?? []);
    if (intel.size === 0) return nearestObjective(state);
    const strength = (i: number): number => {
      const id = nodes[i]?.iceIds[0];
      const ice = id ? catalog[id] : undefined;
      return (ice?.tier ?? 1) + (ice?.armor ?? 0);
    };
    const known = [...intel].filter((i) => {
      const n = nodes[i];
      return n && !n.isBoss && n.iceIds.length > 0 && !cleared.has(i) && !bypassed.has(i);
    });
    if (known.length === 0) return nearestObjective(state);
    // ADR-0292: a drop is worth its ICE's tier, so the best use of bought intel
    // is the STRONGEST encounter the hand can still crack — not the weakest.
    // Falling back to the weakest keeps the policy sane when everything on the
    // board is above the line.
    const beatable = known.filter((i) => strength(i) <= iceLimit);
    const pool = beatable.length > 0 ? beatable : known;
    const cmp = (a: number, b: number): number =>
      beatable.length > 0
        ? strength(b) - strength(a) || a - b
        : strength(a) - strength(b) || a - b;
    return [...pool].sort(cmp)[0] ?? nearestObjective(state);
  }

  if (routePolicy === "short") {
    return fewestFightsNextHop(
      state.matrix as never,
      state.clearedEncounterNodes ?? [],
      state.bypassedEncounterNodes ?? [],
      state.currentNodeIndex,
    );
  }
  return nearestObjective(state);
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
  shieldBonus = 0,
  prepChoice: PrepChoice = "stim",
  walletBalance = 0,
  iceLimit = DEFAULT_ICE_LIMIT,
  intelFree = false,
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
  // ADR-0283 (C''): a starting shield pool is the second capacity lever -- it
  // absorbs the opening hits instead of widening the pool. `remaining` is
  // nominal: the pool drains by absorbing damage (applyPlayerMitigation), and a
  // plain (non-enemy-tick) shield is only decremented by `tickStatus`, so it is
  // given a lifetime longer than any run.
  if (shieldBonus > 0) {
    state = {
      ...state,
      statusEffects: [
        ...state.statusEffects,
        {
          kind: "shield" as const,
          target: "player" as const,
          magnitude: shieldBonus,
          remaining: 9999,
        },
      ],
    };
  }
  // ADR-0283 C''': the prep CHOICE. `--prep ice` takes the shield instead of
  // the pool, which is the decision the screen offers.
  // ADR-0290 (d): measurement-only. Isolates what the INFORMATION is worth from
  // what the loot stop costs -- the two are conflated when intel is bought with
  // a stop, and the stop is worth more than the information at most grades.
  if (intelFree && state.matrix) {
    const nodes = state.matrix.nodes;
    state = {
      ...state,
      intelNodes: nodes
        .map((n, i) => (!n.isBoss && n.iceIds.length > 0 ? i : -1))
        .filter((i) => i >= 0),
    };
  }
  const grade = missionGradeOf(mission);
  const grant = prepGrantFor(grade, prepChoice, walletBalance);
  if (prepChoice === "ice") {
    const pool = shieldBonus > 0 ? shieldBonus : grant.total;
    if (pool > 0) {
      state = {
        ...state,
        statusEffects: [
          ...state.statusEffects,
          {
            kind: "shield" as const,
            target: "player" as const,
            magnitude: pool,
            remaining: 9999,
          },
        ],
      };
    }
  }
  const prepBonus =
    prepChoice === "ice" ? 0 : hpBonus > 0 ? hpBonus : grant.total;
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
        const goal = objective(state, routePolicy, catalog, iceLimit);
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
      const lootUniques = isTerminalNode(state) ? [] : uniqueChoicesFor(state);
      if (lootUniques.length > 0) {
        // ADR-0311: the free pick comes first; the stop is handled next pass.
        state = applyAction(state, {
          type: "select_program",
          handIndex: pickRewardIndex(
            lootUniques.map((id) => cardOf(id)),
            cardPolicy,
          ),
        });
      } else if (!isTerminalNode(state)) {
        const ids = offeredCardIds(state);
        const offersNow = ids.map((id) => cardOf(id));
        // ADR-0291: buying intel ALWAYS is the worst case for it -- it trades a
        // card or a repair for names. A player spends the stop on intel when the
        // stop has nothing worth taking, so `smartintel` does exactly that: only
        // when every offered card is tier 1 and the runner is not hurt.
        // ADR-0295: vent when the budget, not the body, is what will kill it.
        // ADR-0296: burn growth, not body, when the budget is what will kill it.
        // ADR-0305: the value model, calibrated against a measurement rather than
        // a guess. Repairing a stop is worth far more than a card there:
        //
        //   grade  card-only  repair-only
        //     g3     48.1       97.7
        //     g5     10.6       65.7
        //     g6      9.7       25.0
        //
        // So the stop is spent on HP unless HP is nearly full (a repair that
        // overflows is the only wasted one). The vent/burn/syphon purchases are
        // NOT part of this policy: layered on top of repair-heavy play they
        // measurably hurt (g6 30.6 -> 15.3), because each spends the resource the
        // repair just bought.
        const hpPressure = 1 - state.player.hp / Math.max(1, state.player.maxHp);
        const costPressure = state.player.alarm / COST_LIMIT;
        if (
          lootPolicy === "value" ||
          lootPolicy === "valueunique" ||
          lootPolicy === "valuecard"
        ) {
          // One rule, measured: a repair restores 70-100% of max HP and a card is
          // worth far less than that here (g5 65.7% repairing vs 10.6% taking
          // cards; g3 97.7 vs 48.1). The only wasted repair is one that is mostly
          // overflow, so the stop goes to HP whenever it can restore a quarter of
          // the pool, and to the card otherwise.
          // ADR-0305: the exchange rate, measured. A repair and a card are worth
          // about the same when the repair restores ~5-6% of the pool (g3 48.1 vs
          // 50.4, g5 10.6 vs 16.2), so the stop goes to HP only when the repair
          // clears that bar AND there is something to heal.
          const healable = state.player.maxHp - state.player.hp;
          const gain = Math.min(healable, lootRepairAmount(state.player.maxHp, grade));
          const gainPct = (gain / Math.max(1, state.player.maxHp)) * 100;
          const CARD_HP_EQUIV_PCT = 6;
          const cardIdx = pickRewardIndex(ids.map((id) => cardOf(id)), cardPolicy);
          const worthRepair = hpPressure > 0.15 && gainPct >= CARD_HP_EQUIV_PCT;
          // ADR-0307 (a) measurement: is a unique worth the repair it displaces?
          const topIsUnique =
            cardIdx >= 1 && UNIQUE_PROGRAMS.has(ids[cardIdx - 1] as string);

          if (lootPolicy === "valuecard") {
            // Option 2: the loot screen is split, so the card no longer competes
            // with the repair. Both are taken.
            state = applyAction(state, {
              type: "select_program",
              handIndex: cardIdx,
            });
            if (worthRepair) {
              state = applyAction(state, {
                type: "select_program",
                handIndex: LOOT_REPAIR_SLOT,
              });
            }
          } else {
            const takeUnique = lootPolicy === "valueunique" && topIsUnique;
            state = applyAction(state, {
              type: "select_program",
              handIndex: !takeUnique && worthRepair ? LOOT_REPAIR_SLOT : cardIdx,
            });
          }
        } else {
        const valued = false;
        const wantBurn =
          (lootPolicy === "smartburn" ||
            lootPolicy === "smartcombo" ||
            (valued && costPressure >= 0.6 && hpPressure < costPressure)) &&
          state.player.alarm >= 70 &&
          burnTarget(state) !== null;
        // ADR-0298: spend spare capacity on body when the body is what is short.
        const wantRecover =
          (lootPolicy === "smartrecover" ||
            // ADR-0305: a repair is worth far more than a card (measured: g5
            // 67.6% repairing vs 10.6% taking cards), so the stop should be
            // spent on HP whenever HP is not already full. Only overflow makes
            // it a waste.
            (valued && hpPressure > 0.45)) &&
          canRecover(state) &&
          state.player.hp < Math.floor(state.player.maxHp * 0.6);
        // ADR-0297: the combination -- both prices at once, for a deep hole.
        const wantComboVent =
          lootPolicy === "smartcombo" &&
          state.player.alarm >= 85 &&
          state.player.hp > ventHpPrice(state.player.maxHp) * 2;
        const wantVent =
          (lootPolicy === "smartvent" ||
            wantComboVent ||
            (valued && false)) &&
          state.player.alarm >= 70 &&
          state.player.hp > ventHpPrice(state.player.maxHp) * 2;
        const wantIntel =
          (lootPolicy === "intel" && (state.intelNodes ?? []).length === 0) ||
          (lootPolicy === "smartintel" &&
            (state.intelNodes ?? []).length === 0 &&
            offersNow.every((c) => (c?.tier ?? 9) <= 2) &&
            state.player.hp >= Math.floor(state.player.maxHp * 0.5));
        if (state.cardRewardTaken === null && ids.length > 0) {
          const wantRepair =
            lootPolicy === "repair" ||
            ((lootPolicy === "smart" ||
              lootPolicy === "intel" ||
              lootPolicy === "smartintel" ||
              lootPolicy === "smartvent" ||
              lootPolicy === "smartburn" ||
              lootPolicy === "smartcombo" ||
              lootPolicy === "smartrecover" ||
              (valued && hpPressure > 0.45)) &&
              state.player.hp < Math.floor(state.player.maxHp * 0.5));
          const offers = ids.map((id) => cardOf(id));
          if (wantVent) {
            state = applyAction(state, {
              type: "select_program",
              handIndex: LOOT_VENT_SLOT,
            });
          }
          if (wantBurn) {
            state = applyAction(state, {
              type: "select_program",
              handIndex: LOOT_BURN_SLOT,
            });
          }
          if (wantRecover) {
            state = applyAction(state, {
              type: "select_program",
              handIndex: LOOT_RECOVER_SLOT,
            });
          }
          state = applyAction(state, {
            type: "select_program",
            handIndex:
              wantIntel
                ? LOOT_INTEL_SLOT
                : wantRepair
                  ? LOOT_REPAIR_SLOT
                  : pickRewardIndex(offers, cardPolicy),
          });
        }
        }
      }
      if (lootUniques.length === 0) {
        state = applyAction(state, { type: "confirm" });
      }
    } else {
      break;
    }

    if (state === before) return state; // frozen
  }
  return state;
}
