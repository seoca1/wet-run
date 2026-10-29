/**
 * ICE archetype crit wiring — ADR-0161's `aggressive` +5% crit bonus.
 *
 * `ice_ai.ts` documented four archetype behaviors. Three were audited:
 *
 *   - `shouldDefensiveAct` — already wired by ADR-0226 (the two-regime rule
 *     inside `selectSkillByPersonality`, same `DEFENSIVE_HP_THRESHOLD`).
 *   - `shouldTargetAlly` — not wired: no per-target skill resolution exists
 *     in the enemy path.
 *   - `getAlarmMultiplier` — not wired: no alarm accrual loop exists in the
 *     web build (`tickAlarm` has no production caller).
 *   - `getCritBonus` — **wired** by this change.
 *
 * These tests drive the **production reducer** (`applyCombatAction`), not the
 * helper in isolation, so they fail if the wiring is reverted.
 */
import { describe, it, expect, vi, afterEach } from "vitest";
import { applyCombatAction } from "../src/core/state_actions.ts";
import { makeInitialState } from "../src/core/state.ts";
import { AGGRESSIVE_CRIT_BONUS } from "../src/core/ice_ai.ts";
import { rollIceCrit } from "../src/core/ice_crit.ts";
import {
  CRIT_MULTIPLIER_MAX,
  CRIT_MULTIPLIER_MIN,
} from "../src/core/combat_engine.ts";
import type { GameState, Ice, Mission, Program } from "../src/core/types.ts";

const mockMission: Mission = {
  id: "ice_crit_test",
  title: "Crit Test",
  fixer: "fixer",
  arc: 1,
  zone: "test",
  grade_min: 1,
  grade_max: 1,
  rewards: { credits: 100, materials: {} },
};

const strikeProgram: Program = {
  id: "strike",
  name: "Strike",
  tier: 1,
  cost: 1,
  effect: "attack",
  description: "Basic attack",
  aoe: false,
};

/** Base auto-attack of the test ICE: `tier * 3 + armor` = 1 * 3 + 0.
 *
 * The grade-1 auto-attack bonus (+50%, ADR-0211) then raises it to
 * `floor(3 * 1.5)` = 4 — that is the ICE's baseline damage before the crit.
 */
const BASE_AUTO_ATTACK = Math.floor(3 * 1.5);

/** Base skill damage of the test ICE: `damage + tier * 2` = 10 + 2 = 12.
 *
 * The grade damage bonus applies to auto-attacks only, not skill damage.
 */
const BASE_SKILL_DAMAGE = 12;

function makeIce(overrides: Partial<Ice> = {}): Ice {
  return {
    id: "watchdog",
    name: "Watchdog",
    hp: 500,
    maxHp: 500,
    armor: 0,
    tier: 1,
    personality: "aggressive",
    aggression: "passive",
    ...overrides,
  };
}

/** A combat state with a single ICE of the given archetype.
 *
 * `aggression: "passive"` keeps the enemy from casting a skill (5% chance),
 * so the auto-attack path is exercised deterministically. Dixie is suppressed
 * by parking `dixieLastAttackMs` far in the future — she would otherwise
 * attack in the same turn and contaminate the damage measurement.
 */
function makePreState(ice: Ice): GameState {
  const base = makeInitialState(mockMission, ice, [strikeProgram]);
  return {
    ...base,
    phase: "combat",
    runPhase: "combat",
    player: { ...base.player, hp: 1000, maxHp: 1000 },
    iceRoster: [ice],
    activeIceIndex: 0,
    inventory: { credits: 0, materials: {}, programs: [] },
    dixieLastAttackMs: Number.MAX_SAFE_INTEGER,
  };
}

/** Drive one enemy turn and return the damage the player took. */
function enemyTurnDamage(ice: Ice): { damage: number; message: string } {
  const pre = makePreState(ice);
  const result = applyCombatAction(pre, {
    type: "use_program",
    programId: strikeProgram.id,
  });
  const damage = pre.player.hp - result.player.hp;
  return { damage, message: result.message };
}

describe("ICE archetype crit — rollIceCrit", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("never crits and never consumes RNG for a non-aggressive archetype", () => {
    const rng = vi.fn(() => 0);
    const result = rollIceCrit({ personality: "defensive" }, 10, rng);
    expect(result.isCrit).toBe(false);
    expect(result.damage).toBe(10);
    expect(rng).not.toHaveBeenCalled();
  });

  it("never crits for any non-aggressive archetype", () => {
    for (const personality of ["defensive", "stealth", "support"] as const) {
      const result = rollIceCrit({ personality }, 10, () => 0);
      expect(result.isCrit).toBe(false);
      expect(result.damage).toBe(10);
    }
  });

  it("crits an aggressive ICE when the roll lands inside the bonus", () => {
    const result = rollIceCrit({ personality: "aggressive" }, 10, () => 0);
    expect(result.isCrit).toBe(true);
    expect(result.damage).toBeGreaterThanOrEqual(
      Math.floor(10 * CRIT_MULTIPLIER_MIN),
    );
    expect(result.damage).toBeLessThanOrEqual(
      Math.floor(10 * CRIT_MULTIPLIER_MAX),
    );
  });

  it("does not crit an aggressive ICE when the roll misses the bonus", () => {
    // AGGRESSIVE_CRIT_BONUS is 0.05, so 0.99 is outside the window.
    const result = rollIceCrit({ personality: "aggressive" }, 10, () => 0.99);
    expect(result.isCrit).toBe(false);
    expect(result.damage).toBe(10);
  });

  it("crits just inside the AGGRESSIVE_CRIT_BONUS boundary", () => {
    const result = rollIceCrit(
      { personality: "aggressive" },
      10,
      () => AGGRESSIVE_CRIT_BONUS - 0.0001,
    );
    expect(result.isCrit).toBe(true);
  });
});

describe("ICE archetype crit — production reducer", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("applies the crit bonus to an aggressive ICE auto-attack", () => {
    // rng() = 0 is inside the 5% window, so the roll crits; the multiplier
    // roll also returns 0, landing on CRIT_MULTIPLIER_MIN.
    vi.spyOn(Math, "random").mockReturnValue(0);
    const { damage, message } = enemyTurnDamage(makeIce());
    expect(message).toContain("CRITICAL");
    expect(damage).toBe(
      Math.max(1, Math.floor(BASE_AUTO_ATTACK * CRIT_MULTIPLIER_MIN)),
    );
    expect(damage).toBeGreaterThan(BASE_AUTO_ATTACK);
  });

  it("does not apply the crit bonus to a non-aggressive ICE", () => {
    vi.spyOn(Math, "random").mockReturnValue(0);
    for (const personality of ["defensive", "stealth", "support"] as const) {
      const { damage, message } = enemyTurnDamage(makeIce({ personality }));
      expect(message).not.toContain("CRITICAL");
      expect(damage).toBe(BASE_AUTO_ATTACK);
    }
  });

  it("keeps an aggressive ICE's damage unchanged when the crit misses", () => {
    // rng() = 0.99 is outside the 5% window.
    vi.spyOn(Math, "random").mockReturnValue(0.99);
    const { damage, message } = enemyTurnDamage(makeIce());
    expect(message).not.toContain("CRITICAL");
    expect(damage).toBe(BASE_AUTO_ATTACK);
  });

  it("applies the crit bonus to an aggressive ICE skill hit", () => {
    vi.spyOn(Math, "random").mockReturnValue(0);
    const ice = makeIce({
      aggression: "standard",
      skills: [
        {
          id: "hit",
          name: "Hit",
          effect: "attack",
          cooldownMs: 0,
          damage: 10,
        },
      ],
    });
    const { damage, message } = enemyTurnDamage(ice);
    expect(message).toContain("uses Hit");
    expect(message).toContain("CRITICAL");
    expect(damage).toBe(
      Math.max(1, Math.floor(BASE_SKILL_DAMAGE * CRIT_MULTIPLIER_MIN)),
    );
  });

  it("does not crit a non-aggressive ICE skill hit", () => {
    vi.spyOn(Math, "random").mockReturnValue(0);
    const ice = makeIce({
      aggression: "standard",
      personality: "support",
      skills: [
        {
          id: "hit",
          name: "Hit",
          effect: "attack",
          cooldownMs: 0,
          damage: 10,
        },
      ],
    });
    const { damage, message } = enemyTurnDamage(ice);
    expect(message).not.toContain("CRITICAL");
    expect(damage).toBe(BASE_SKILL_DAMAGE);
  });
});
