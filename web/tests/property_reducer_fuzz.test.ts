/**
 * Property-based fuzzing of the pure state reducer (`applyAction`).
 *
 * The rest of the suite pins *example* states and *example* action sequences.
 * This file takes the complementary approach: fast-check invents arbitrary
 * missions, ICE, decks, mutators and action sequences, the REAL reducer is
 * driven with them, and the invariants that must hold for *every* input are
 * asserted after every step.
 *
 * Method: inputs come from fast-check v4; no game logic is reimplemented —
 * only inputs are chosen and outputs are read. Nondeterminism is pinned
 * exactly like `scripts/balance_sim.ts`, because the reducer reads
 * `Math.random` (damage variance, crits, status procs) and `Date.now()` (the
 * `AUTO_ATTACK_INTERVAL_MS` auto-attack gate) at call time: both are replaced
 * with `mulberry32(seed)` / a manual clock and restored in a `finally` block,
 * and the clock advances by `AUTO_ATTACK_INTERVAL_MS` between steps.
 * Invariants are checked after every step, so a violation is reported at the
 * first step that breaks it rather than at the end of the sequence.
 *
 * When an invariant fails, fast-check shrinks the counterexample to a minimal
 * one; the violation is then pinned as `it.fails(...)` with the shrunk
 * counterexample recorded in a comment so the bug stays visible instead of
 * being silently weakened away.
 *
 * Run depth: `FUZZ_RUNS=5000 npm run fuzz` for a deep pass.
 */
import fc from "fast-check";
import { describe, expect, it } from "vitest";

import { mulberry32 } from "../scripts/balance_sim";
import { AUTO_ATTACK_INTERVAL_MS } from "../src/core/combat_engine";
import { loadIceCatalog, loadMissionsCatalog, loadProgramsCatalog } from "../src/core/data_loaders";
import type { RestartChoice } from "../src/core/death_cycle";
import { makeLoadout } from "../src/core/loadout";
import { pathLengthBetween } from "../src/core/matrix_navigation";
import { applyAction, makeInitialState } from "../src/core/state";
import type { GameAction, GameState, Ice, Mission, Program } from "../src/core/types";
import type { RunMutator } from "../src/core/run_mutators";

import iceTypesJson from "../src/data/ice_types.json";
import missionsJson from "../src/data/missions.json";
import programsJson from "../src/data/programs.json";

const missions = loadMissionsCatalog(missionsJson);
const iceCatalog = loadIceCatalog(iceTypesJson);
const allPrograms: ReadonlyArray<Program> = Object.values(loadProgramsCatalog(programsJson));
const allIce: ReadonlyArray<Ice> = Object.values(iceCatalog);

const NUM_RUNS = Number.parseInt(process.env.FUZZ_RUNS ?? "200", 10);
const CLOCK_ORIGIN_MS = 1_000_000;
const MUTATOR_IDS: ReadonlyArray<RunMutator> = [
  "low_hp", "double_alarm", "ice_x2", "no_heal", "stealth_only",
];
const RESTART_CHOICES: ReadonlyArray<RestartChoice> = [
  "new_jockey", "same_jockey", "hall_of_dead", "main_menu",
];
const ACTION_TYPES = [
  "move_north", "move_south", "move_east", "move_west",
  "use_program", "select_program", "confirm", "cancel",
  "jack_out", "cycle_target", "trigger_death", "select_restart",
  "view_hall_of_dead",
] as const;
const GAME_PHASES = ["menu", "approach", "combat", "victory", "defeat", "exit"] as const;
const RUN_PHASES = ["matrix", "combat", "loot", "ending", "dead"] as const;
const BOSS_PHASES = [0, 1, 2, 3, 4] as const;

/**
 * Deep-copy a state so two applications start from structurally equal input.
 *
 * `GameState` is NOT plain JSON: `grid` carries a `get()` method and
 * `equipmentLoadout` carries `totalStats()` / `equip()` methods, which a naive
 * `JSON.parse(JSON.stringify(state))` would drop — the reducer would then
 * throw on the clone, a harness artifact rather than a reducer bug. The grid
 * is shared by reference (immutable, never touched by the reducer) and the
 * loadout is rebuilt through the real `makeLoadout` factory.
 */
function cloneState(state: GameState): GameState {
  const copy = JSON.parse(
    JSON.stringify({ ...state, grid: undefined, equipmentLoadout: undefined }),
  ) as GameState;
  return {
    ...copy,
    grid: state.grid,
    equipmentLoadout: makeLoadout({ ...state.equipmentLoadout.equipment }),
  };
}

/**
 * Structural fingerprint of a state, used for the determinism invariant. The
 * `grid` is excluded: it is a large immutable cell matrix (up to 160x90 cells)
 * the reducer neither reads nor writes, so serializing it would dominate the
 * runtime without adding signal. Everything else is compared verbatim.
 */
function structuralJson(state: GameState): string {
  const { grid, ...rest } = state;
  void grid;
  return JSON.stringify(rest);
}

/**
 * Invariant 2 — no NaN / Infinity anywhere in the numeric surface. Walks the
 * state generically rather than listing every field by hand: any number
 * anywhere in the tree must be finite. The `grid` cell matrix is skipped (no
 * gameplay numbers, and it is huge).
 */
function assertAllNumbersFinite(state: GameState): void {
  const visit = (node: unknown, path: string): void => {
    if (typeof node === "number") {
      expect(Number.isFinite(node), `${path} must be finite (got ${String(node)})`).toBe(true);
      return;
    }
    if (Array.isArray(node)) {
      node.forEach((entry, index) => visit(entry, `${path}[${index}]`));
      return;
    }
    if (typeof node !== "object" || node === null) return;
    for (const [key, value] of Object.entries(node)) {
      if (path === "" && key === "grid") continue;
      visit(value, path === "" ? key : `${path}.${key}`);
    }
  };
  visit(state, "");
}

/** Invariants 3–7 — HP / alarm / turn / phase / index bounds. */
function assertBoundsHold(state: GameState): void {
  expect(state.player.hp, "player.hp must be >= 0").toBeGreaterThanOrEqual(0);
  expect(state.player.hp, "player.hp must be <= maxHp").toBeLessThanOrEqual(state.player.maxHp);
  for (const ice of state.iceRoster) {
    expect(ice.hp, `iceRoster[${ice.id}].hp must be >= 0`).toBeGreaterThanOrEqual(0);
    if (ice.maxHp !== undefined) {
      expect(ice.hp, `iceRoster[${ice.id}].hp must be <= maxHp`).toBeLessThanOrEqual(ice.maxHp);
    }
  }
  expect(state.player.alarm, "player.alarm must be >= 0").toBeGreaterThanOrEqual(0);
  expect(state.player.alarm, "player.alarm must be <= 100").toBeLessThanOrEqual(100);
  expect(state.alarmLevel, "alarmLevel must be >= 0").toBeGreaterThanOrEqual(0);
  expect(state.turnCount, "turnCount must be >= 0").toBeGreaterThanOrEqual(0);
  expect(GAME_PHASES, `phase '${state.phase}' must be a GamePhase`).toContain(state.phase);
  expect(RUN_PHASES, `runPhase '${state.runPhase}' must be a RunPhase`).toContain(state.runPhase);
  expect(BOSS_PHASES, `bossPhase '${state.bossPhase}' must be 0..4`).toContain(state.bossPhase);
  if (state.iceRoster.length > 0) {
    expect(state.activeIceIndex, "activeIceIndex must be >= 0").toBeGreaterThanOrEqual(0);
    expect(state.activeIceIndex, "activeIceIndex must be < iceRoster.length").toBeLessThan(
      state.iceRoster.length,
    );
  }
}

/**
 * Invariants 9–10 — matrix navigation stays graph-directed and in bounds.
 *
 * Invariant 9: a forward move (`move_south` / `move_east`) strictly
 * decreases the BFS distance to the boss, and a backward move
 * (`move_north` / `move_west`) strictly decreases the BFS distance to the
 * entry. A move that cannot improve the distance is a no-op, so the walk
 * always terminates at the objective.
 *
 * Invariant 10: `currentNodeIndex` always stays inside
 * `[0, matrix.nodes.length)`.
 */
function assertNavigationHolds(
  before: GameState,
  after: GameState,
  action: GameAction,
): void {
  const matrix = before.matrix;
  if (!matrix) return;

  expect(
    after.currentNodeIndex,
    `currentNodeIndex ${after.currentNodeIndex} out of bounds for ${matrix.nodes.length} nodes`,
  ).toBeGreaterThanOrEqual(0);
  expect(
    after.currentNodeIndex,
    `currentNodeIndex ${after.currentNodeIndex} out of bounds for ${matrix.nodes.length} nodes`,
  ).toBeLessThan(matrix.nodes.length);

  const isForward = action.type === "move_south" || action.type === "move_east";
  const isBackward = action.type === "move_north" || action.type === "move_west";
  if (!isForward && !isBackward) return;
  if (after.currentNodeIndex === before.currentNodeIndex) return;

  const target = isForward ? matrix.bossNode : matrix.startNode;
  const distanceBefore = pathLengthBetween(
    matrix,
    before.currentNodeIndex,
    target,
  );
  const distanceAfter = pathLengthBetween(matrix, after.currentNodeIndex, target);
  if (distanceBefore < 0 || distanceAfter < 0) return;
  expect(
    distanceAfter,
    `'${action.type}' did not shorten the path to node ${target} (${distanceBefore} → ${distanceAfter})`,
  ).toBeLessThan(distanceBefore);
}

/**
 * A planned step: an action variant plus the payload it needs.
 *
 * `use_program` / `select_program` carry *indices* rather than ids so they can
 * be bound to the live hand at replay time (the hand shrinks as cards are
 * played, so a fixed id could become unreachable) while still shrinking
 * cleanly under fast-check. `burst` expands to several consecutive
 * `use_program` steps so a random sequence can actually kill an ICE.
 */
interface PlannedStep {
  readonly kind: (typeof ACTION_TYPES)[number] | "burst";
  readonly index: number;
  readonly slots?: ReadonlyArray<number>;
}

/** Expand a planned step into the concrete actions it stands for. */
function expandStep(step: PlannedStep, state: GameState): ReadonlyArray<GameAction> {
  const hand = state.deck;
  const pick = (slot: number): GameAction => {
    const program = hand.length === 0 ? undefined : hand[slot % hand.length];
    return { type: "use_program", programId: program?.id ?? "__no_hand__" };
  };
  switch (step.kind) {
    case "use_program":
      return [pick(step.index)];
    case "burst":
      return (step.slots ?? []).map(pick);
    case "select_program": {
      const index = hand.length === 0 ? 1 : 1 + (step.index % hand.length);
      return [{ type: "select_program", handIndex: index }];
    }
    case "select_restart":
      return [
        {
          type: "select_restart",
          choice: RESTART_CHOICES[step.index % RESTART_CHOICES.length] ?? "new_jockey",
        },
      ];
    default:
      return [{ type: step.kind }];
  }
}

/**
 * A burst of consecutive `use_program` steps. Purely random sequences almost
 * never play enough cards to kill the ICE, so the victory / loot / ending /
 * boss-phase branches would never be reached and the invariants guarding them
 * would be vacuous.
 */
const programBurstArb = fc.array(fc.nat({ max: 32 }), { minLength: 1, maxLength: 8 });

const plannedStepArb: fc.Arbitrary<PlannedStep> = fc.oneof(
  fc
    .record({ kind: fc.constantFrom(...ACTION_TYPES), index: fc.nat({ max: 32 }) })
    .map((r): PlannedStep => ({ kind: r.kind, index: r.index })),
  programBurstArb.map((slots): PlannedStep => ({ kind: "burst", index: 0, slots })),
);

const confirmBurst = (count: number): ReadonlyArray<PlannedStep> =>
  Array.from({ length: count }, (): PlannedStep => ({ kind: "confirm", index: 0 }));

/**
 * Trailing `confirm` steps. After the ICE dies the reducer sits in the `loot`
 * run phase; another `confirm` advances the run, and a `confirm` on the boss
 * node completes the mission and moves the run to `ending`. Without this tail
 * the `ending` branch (and its `factionScores` / `endingChoice` writes) is
 * never reached.
 */
const advanceBurst = confirmBurst(6);
/** Two `confirm`s: leave the entry room and enter the encounter. */
const engageBurst = confirmBurst(2);

const scenarioArb = fc.record({
  mission: fc.constantFrom(...missions),
  ice: fc.constantFrom(...allIce),
  deck: fc.subarray([...allPrograms], { minLength: 1 }).map((cards) => cards.slice(0, 5)),
  drawPile: fc.subarray([...allPrograms], { minLength: 0, maxLength: 6 }),
  mutators: fc.subarray([...MUTATOR_IDS], { minLength: 0, maxLength: 3 }),
  actions: fc.array(plannedStepArb, { minLength: 1, maxLength: 40 }),
  seed: fc.integer({ min: 0, max: 0xffff }),
});

/** Apply one action with a freshly seeded RNG and a frozen clock. */
function applyWithEntropy(
  state: GameState,
  action: GameAction,
  seed: number,
  clock: number,
): GameState {
  Math.random = mulberry32(seed);
  Date.now = () => clock;
  return applyAction(state, action);
}

/** Run one scenario, asserting every invariant after every step. */
function runScenario(scenario: {
  readonly mission: Mission;
  readonly ice: Ice;
  readonly deck: ReadonlyArray<Program>;
  readonly drawPile: ReadonlyArray<Program>;
  readonly mutators: ReadonlyArray<RunMutator>;
  readonly actions: ReadonlyArray<PlannedStep>;
  readonly seed: number;
}): void {
  const originalRandom = Math.random;
  const originalNow = Date.now;
  let clock = CLOCK_ORIGIN_MS;
  Math.random = mulberry32(scenario.seed);
  Date.now = () => clock;

  try {
    let state = makeInitialState(
      scenario.mission,
      scenario.ice,
      scenario.deck,
      scenario.drawPile,
      scenario.mutators,
    );
    assertAllNumbersFinite(state);
    assertBoundsHold(state);

    for (const step of [...engageBurst, ...scenario.actions, ...advanceBurst]) {
      for (const action of expandStep(step, state)) {
        // Invariant 1 — the reducer never throws.
        let next: GameState | undefined;
        expect(() => {
          next = applyAction(state, action);
        }, `applyAction threw for action '${action.type}'`).not.toThrow();
        if (next === undefined) return;
        assertAllNumbersFinite(next);
        assertBoundsHold(next);
        assertNavigationHolds(state, next, action);

        // Invariant 8 — determinism: the same action on a structurally equal
        // state yields a structurally equal state (same RNG + same clock).
        const first = applyWithEntropy(cloneState(state), action, scenario.seed, clock);
        const second = applyWithEntropy(cloneState(state), action, scenario.seed, clock);
        expect(
          structuralJson(first),
          `applyAction is not deterministic for action '${action.type}'`,
        ).toBe(structuralJson(second));

        state = next;
        clock += AUTO_ATTACK_INTERVAL_MS;
      }
    }
  } finally {
    Math.random = originalRandom;
    Date.now = originalNow;
  }
}

describe("property reducer fuzz", () => {
  it("never throws and preserves every state invariant", () => {
    fc.assert(fc.property(scenarioArb, runScenario), { numRuns: NUM_RUNS });
  });

  it("covers all 13 GameAction variants across the generated sequences", () => {
    const seen = new Set<string>();
    fc.assert(
      fc.property(
        fc.array(plannedStepArb, { minLength: 1, maxLength: 40 }),
        (steps) => {
          for (const step of steps) {
            seen.add(step.kind === "burst" ? "use_program" : step.kind);
          }
        },
      ),
      { numRuns: 50 },
    );
    expect([...seen].sort()).toEqual([...ACTION_TYPES].sort());
  });
});
