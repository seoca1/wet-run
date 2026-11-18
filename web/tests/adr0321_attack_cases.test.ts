/**
 * ADR-0321 — SRW-shaped attack resolution: several probabilistic cases per hit.
 *
 * Until this, **every attack landed**. The only probability in combat was the
 * crit roll, so the owner's ask was for Super Robot Wars' shape: a hit can MISS,
 * be GUARDED, or land, before anything else happens.
 *
 * The measurement is why the base odds ship at zero. A table of miss 6 / guard
 * 12 removes only ~12% of incoming damage on average, yet it moved the mission
 * curve to g3 93.8, g4 92.2, g5 46.9, g6 60.4 (from 84.5 / 84.4 / 27.1 / 34.4).
 * The variance is the point: at g5/g6 the runner dies inside a single fight, so
 * one dodged lethal hit is a run that lives. The cases are therefore a dial the
 * owner sets, with the ICE's damage raised against it.
 */
import { afterEach, describe, expect, it, vi } from "vitest";
import { loadProgramsCatalog } from "../src/core/data_loaders";
import { makeInitialState } from "../src/core/state/state";
import { applyCombatAction } from "../src/core/combat/state_actions_combat";
import { applyStatus } from "../src/core/status";
import {
  ATTACK_CASES,
  CASE_DAMAGE_MULTIPLIER,
  INCOMING_BASE_ODDS,
  PLAYER_ODDS,
  applyCase,
  caseNote,
  expectedDamageCut,
  incomingOddsFor,
  resolveAttackCase,
} from "../src/core/combat/attack_resolution";
import { playerEvasionPct } from "../src/core/combat/player_mitigation";
import type { GameState, Ice, Mission, Program } from "../src/core/types";
import programsJson from "../src/data/programs.json" with { type: "json" };

const programs = loadProgramsCatalog(programsJson);
const originalRandom = Math.random;
afterEach(() => {
  Math.random = originalRandom;
  vi.restoreAllMocks();
});

const mission = {
  id: "adr0321",
  title: "ADR 0321",
  fixer: "test",
  arc: 1,
  zone: "surface",
  grade_min: 1,
  grade_max: 1,
  rewards: { credits: 0, materials: {} },
} as unknown as Mission;

const strike = programs.strike as Program;

function combatState(withEvasion: boolean): GameState {
  const foe = {
    id: "watchdog",
    name: "Watchdog",
    hp: 500,
    maxHp: 500,
    armor: 0,
    tier: 1,
    personality: "aggressive",
    aggression: "passive",
  } as unknown as Ice;
  const base = makeInitialState(mission, foe, [strike]);
  const state: GameState = {
    ...base,
    phase: "combat",
    runPhase: "combat",
    player: { ...base.player, hp: 1000, maxHp: 1000 },
    iceRoster: [foe],
    activeIceIndex: 0,
    inventory: { credits: 0, materials: {}, programs: [] },
    dixiePlayerTurnsSinceAttack: 0,
  } as GameState;
  // duration first, then magnitude — the evasion percent is the magnitude.
  return withEvasion ? applyStatus(state, "player", "evasive", 99, 15) : state;
}

/** Play one card and return what the enemy turn did to the player. */
function enemyTurn(
  state: GameState,
  map: (n: number) => number,
): { damage: number; message: string; draws: number } {
  let n = 0;
  vi.spyOn(Math, "random").mockImplementation(() => {
    n += 1;
    return map(n);
  });
  const after = applyCombatAction(state, {
    type: "use_program",
    programId: strike.id,
  });
  return {
    damage: state.player.hp - after.player.hp,
    message: after.message,
    draws: n,
  };
}

describe("ADR-0321 · the case table", () => {
  it("names the cases in band order", () => {
    expect([...ATTACK_CASES]).toEqual(["miss", "guard", "hit"]);
  });

  it("reads the bands top to bottom", () => {
    const odds = { missPct: 20, guardPct: 30 };
    expect(resolveAttackCase(0.0, odds)).toBe("miss");
    expect(resolveAttackCase(0.199, odds)).toBe("miss");
    expect(resolveAttackCase(0.2, odds)).toBe("guard");
    expect(resolveAttackCase(0.499, odds)).toBe("guard");
    expect(resolveAttackCase(0.5, odds)).toBe("hit");
    expect(resolveAttackCase(0.999, odds)).toBe("hit");
  });

  it("is a hit when there is nothing to roll", () => {
    expect(resolveAttackCase(0, PLAYER_ODDS)).toBe("hit");
    expect(resolveAttackCase(0.99, PLAYER_ODDS)).toBe("hit");
  });

  it("clamps a roll outside [0, 1)", () => {
    const odds = { missPct: 10, guardPct: 10 };
    expect(resolveAttackCase(-5, odds)).toBe("miss");
    expect(resolveAttackCase(7, odds)).toBe("hit");
    expect(resolveAttackCase(Number.NaN, odds)).toBe("miss");
  });

  it("applies the multipliers, never below 1 on a landed hit", () => {
    expect(CASE_DAMAGE_MULTIPLIER.miss).toBe(0);
    expect(applyCase(40, "miss")).toBe(0);
    expect(applyCase(40, "guard")).toBe(20);
    expect(applyCase(40, "hit")).toBe(40);
    // A landed hit keeps the engine's own floor.
    expect(applyCase(1, "guard")).toBe(1);
    expect(applyCase(0, "hit")).toBe(0);
  });

  it("says nothing for an ordinary hit", () => {
    expect(caseNote("hit")).toBe("");
    expect(caseNote("miss")).toBe(" [MISS]");
    expect(caseNote("guard")).toBe(" [GUARD]");
  });
});

describe("ADR-0321 · where the odds come from", () => {
  it("ships the base table at zero, so nothing moves by default", () => {
    expect(INCOMING_BASE_ODDS.missPct).toBe(0);
    expect(INCOMING_BASE_ODDS.guardPct).toBe(0);
    expect(PLAYER_ODDS.missPct).toBe(0);
    expect(PLAYER_ODDS.guardPct).toBe(0);
  });

  it("turns `cloak`'s evasion into a MISS chance", () => {
    expect(incomingOddsFor(0).missPct).toBe(0);
    expect(incomingOddsFor(15).missPct).toBe(15);
    expect(incomingOddsFor(15).guardPct).toBe(0);
    // A non-finite or negative evasion cannot make the runner easier to hit.
    expect(incomingOddsFor(-5).missPct).toBe(0);
    expect(incomingOddsFor(Number.NaN).missPct).toBe(0);
  });

  it("reports the mean damage a table removes", () => {
    expect(expectedDamageCut({ missPct: 0, guardPct: 0 })).toBe(0);
    expect(expectedDamageCut({ missPct: 10, guardPct: 0 })).toBeCloseTo(0.1);
    expect(expectedDamageCut({ missPct: 0, guardPct: 10 })).toBeCloseTo(0.05);
    // The table that was measured at +42pp on g4 removed only 12% on average.
    expect(expectedDamageCut({ missPct: 6, guardPct: 12 })).toBeCloseTo(0.12);
  });
});

describe("ADR-0321 · the reducer honours the cases", () => {
  it("consumes no draw when there is nothing to roll", () => {
    // The byte-identity claim: with the base at 0 and no evasion the enemy's
    // case roll does not exist, so the seeded stream is what it always was (the
    // `balance_sim` baseline row is the end-to-end proof). Evasion is what puts
    // the roll back — exactly one draw, and only then.
    const quiet = enemyTurn(combatState(false), () => 0.99);
    const evasive = enemyTurn(combatState(true), () => 0.99);
    expect(quiet.message).not.toContain("[MISS]");
    expect(evasive.draws).toBe(quiet.draws + 1);
  });

  it("misses the runner when the case roll lands in the miss band", () => {
    // Player draws are 1-4 (variance, crit check, burn, slow); the ICE's case
    // roll is draw 5 and its crit roll draw 6.
    const state = combatState(true);
    expect(playerEvasionPct(state)).toBe(15);
    const missed = enemyTurn(state, (n) => (n === 5 ? 0.0 : 0.99));
    expect(missed.message).toContain("[MISS]");
    expect(missed.damage).toBe(0);
    // Outside the 15% band the attack lands as before.
    const landed = enemyTurn(combatState(true), (n) => (n === 5 ? 0.5 : 0.99));
    expect(landed.message).not.toContain("[MISS]");
    expect(landed.damage).toBeGreaterThan(0);
  });
});
