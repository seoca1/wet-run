/** ADR-0241 — the `critical_hit` VFX spawns iff the player's hit is a real crit.
 *
 * Before ADR-0241 the flash was gated on `damage >= 10`, so a high-tier
 * non-crit always showed "CRIT" and a low-tier crit never did. These tests
 * drive `use_program` with a scripted `Math.random` stream so the crit roll
 * inside `calculateDamage` is controlled, then assert the spawn follows
 * `isCrit` in both directions and independently of the damage amount.
 */
import { describe, it, expect } from "vitest";
import { applyAction, makeInitialState } from "../src/core/state/state";
import {
  CRIT_CHANCE,
  ROLE_CRIT_BONUSES,
} from "../src/core/combat/combat_engine";
import type { GameState, Ice, Mission, Program } from "../src/core/types";

const mission: Mission = {
  id: "test",
  title: "T",
  fixer: "x",
  arc: 1,
  zone: "test",
  grade_min: 1,
  grade_max: 1,
  rewards: { credits: 0, materials: {} },
};
const ICE_HP = 500;
const ice: Ice = { id: "ice1", name: "ICE", hp: ICE_HP, armor: 0, tier: 1 };

/** Tier 3 burst → base damage 15: a non-crit hit lands at 12..17 (>= 10). */
const burst3 = {
  id: "burst3",
  name: "BURST",
  tier: 3,
  cost: 10,
  effect: "e",
  description: "",
  aoe: false,
  role: "burst",
} as Program;

/** Tier 1, no role → base damage 5: even a crit stays below 10. */
const probe1 = {
  id: "probe1",
  name: "PROBE",
  tier: 1,
  cost: 1,
  effect: "e",
  description: "",
  aoe: false,
} as Program;

function combatState(program: Program): GameState {
  const base = makeInitialState(mission, ice, [program]);
  return {
    ...base,
    runPhase: "combat",
    phase: "combat",
    iceRoster: [{ ...ice }],
    activeIceIndex: 0,
    vfxInstances: [],
    dixieLastAttackMs: Date.now(),
  };
}

/** Run `fn` with `Math.random` returning `values` in order, then 0.99. */
function withRandom<T>(values: ReadonlyArray<number>, fn: () => T): T {
  const original = Math.random;
  let i = 0;
  Math.random = () => values[i++] ?? 0.99;
  try {
    return fn();
  } finally {
    Math.random = original;
  }
}

/** Play `program` once under the scripted stream; report the outcome. */
function play(
  program: Program,
  stream: ReadonlyArray<number>,
): { crits: number; damage: number } {
  const next = withRandom(stream, () =>
    applyAction(combatState(program), {
      type: "use_program",
      programId: program.id,
    }),
  );
  const crits = next.vfxInstances.filter(
    (v) => v.kind === "critical_hit",
  ).length;
  const damage = ICE_HP - (next.iceRoster[0]?.hp ?? ICE_HP);
  return { crits, damage };
}

// calculateDamage draw order: variance, crit check, [crit multiplier].
const CRIT = [0, 0, 0];
const NON_CRIT = [0.99, 0.99];

describe("ADR-0241 critical_hit VFX follows isCrit", () => {
  it("spawns critical_hit on a crit", () => {
    const { crits, damage } = play(burst3, CRIT);
    expect(crits).toBe(1);
    // Tier 3 burst, variance 0.8, crit x1.8 → floor(12 * 1.8) = 21.
    expect(damage).toBe(21);
  });

  it("does not spawn critical_hit on a non-crit hit of damage >= 10", () => {
    const { crits, damage } = play(burst3, NON_CRIT);
    // Guard: the old `damage >= 10` gate would have fired here.
    expect(damage).toBeGreaterThanOrEqual(10);
    expect(crits).toBe(0);
  });

  it("spawns critical_hit on a crit below the old damage >= 10 threshold", () => {
    const { crits, damage } = play(probe1, CRIT);
    // Guard: the old `damage >= 10` gate would have stayed silent here.
    expect(damage).toBeLessThan(10);
    expect(crits).toBe(1);
  });

  it("spawns iff the crit roll passes, across the whole roll range", () => {
    const burstCritChance = CRIT_CHANCE + (ROLE_CRIT_BONUSES.burst ?? 0);
    for (let step = 0; step < 20; step++) {
      // Offset by 0.01 so no roll sits exactly on the crit boundary.
      const roll = step / 20 + 0.01;
      const { crits } = play(burst3, [0.5, roll, 0.5]);
      expect({ roll, crits }).toEqual({
        roll,
        crits: roll < burstCritChance ? 1 : 0,
      });
    }
  });
});
