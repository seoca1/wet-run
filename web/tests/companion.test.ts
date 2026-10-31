import { afterEach, describe, it, expect, vi } from "vitest";
import { applyAction, makeInitialState } from "../src/core/state/state";
import type { GameState, Ice, Mission, Program } from "../src/core/types";
import { useProgram } from "../src/core/combat/state_actions_programs";

function makeCombatState(overrides: Partial<GameState> = {}): GameState {
  const mockMission: Mission = {
    id: "test",
    title: "Test",
    fixer: "test",
    arc: 1,
    zone: "test",
    grade_min: 1,
    grade_max: 1,
    rewards: { credits: 10, materials: {} },
  };
  const mockProgram: Program = {
    id: "p1",
    name: "Atk",
    tier: 1,
    cost: 0,
    effect: "damage",
    description: "test",
    aoe: false,
  };
  const mockIce: Ice = {
    id: "enemy1",
    name: "Enemy",
    tier: 1,
    hp: 50,
    maxHp: 50,
    armor: 0,
    personality: "aggressive",
    aggression: "standard",
    skills: [],
  };
  const state = makeInitialState(mockMission, mockIce, [mockProgram]);
  return {
    ...state,
    iceRoster: [mockIce],
    activeIceIndex: 0,
    phase: "combat" as const,
    runPhase: "combat" as const,
    lastEnemyAttackMs: 0,
    dixieLastAttackMs: 0,
    skillCooldowns: {},
    ...overrides,
  };
}

describe("Dixie companion", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("deals the same damage from the same state at different wall-clock times", () => {
    // Given: both clocks permit an enemy turn, but straddle the old Dixie gate.
    const state = makeCombatState({ dixieLastAttackMs: 1000 });
    vi.spyOn(Math, "random").mockReturnValue(0.99);
    const clock = vi.spyOn(Date, "now");
    // When
    const results = [3000, 4000].map((now) => {
      clock.mockReturnValue(now);
      return applyAction(state, { type: "use_program", programId: "p1" });
    });
    // Then: timestamps may differ, but combat damage and the companion action may not.
    expect(results[0].iceRoster).toEqual(results[1].iceRoster);
    expect(results[0].player.hp).toBe(results[1].player.hp);
    expect(results[0].message).toBe(results[1].message);
  });

  it("Dixie attacks on the first player turn", () => {
    const state = makeCombatState({
      dixieLastAttackMs: 0,
    });
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    expect(result.message).toContain("Dixie attacks");
  });

  it("Dixie damage increases with combo count", () => {
    const state = makeCombatState({
      dixieLastAttackMs: 0,
      playerCombo: 5,
    });
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    expect(result.iceRoster[0].hp).toBeLessThanOrEqual(50 - 23);
  });

  it("Dixie does not attack before enough player turns", () => {
    const state = makeCombatState({
      dixiePlayerTurnsSinceAttack: 0,
    });
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    expect(result.message).not.toContain("Dixie attacks");
  });

  it("fires on player turns 1, 3 and 5 with exactly 8 + combo*3 damage", () => {
    // Given
    const state = makeCombatState({
      iceRoster: [{ ...makeCombatState().iceRoster[0], hp: 1000, maxHp: 1000 }],
    });
    vi.spyOn(Math, "random").mockReturnValue(0.99);
    vi.spyOn(Date, "now").mockReturnValue(10_000);
    const companionDamage: number[] = [];
    // When: one-card hand recycles each time; no extra enemy turns are due.
    const states = Array.from({ length: 5 }).reduce<GameState[]>((turns) => {
      const previous = turns[turns.length - 1] ?? state;
      const programOnly = useProgram(previous, "p1");
      const next = applyAction(previous, {
        type: "use_program",
        programId: "p1",
      });
      companionDamage.push(programOnly.iceRoster[0].hp - next.iceRoster[0].hp);
      turns.push(next);
      return turns;
    }, []);
    // Then
    expect(companionDamage).toEqual([11, 0, 17, 0, 23]);
    expect(states.map((s) => s.dixiePlayerTurnsSinceAttack)).toEqual([
      0, 1, 0, 1, 0,
    ]);
  });

  it("does not count rejected programs, target changes, selection or idle ticks", () => {
    // Given
    const state = makeCombatState({ dixiePlayerTurnsSinceAttack: 0 });
    // When
    const results = [
      applyAction(state, { type: "use_program", programId: "missing" }),
      applyAction(state, { type: "cycle_target" }),
      applyAction(state, { type: "select_program", handIndex: 1 }),
      applyAction(state, { type: "idle_tick", idleSinceMs: 0 }),
    ];
    // Then
    expect(results.map((s) => s.dixiePlayerTurnsSinceAttack)).toEqual([
      0, 0, 0, 0,
    ]);
  });

  it("Dixie targets first living enemy", () => {
    const roster: Ice[] = [
      {
        id: "dead",
        name: "Dead",
        tier: 1,
        hp: 0,
        maxHp: 50,
        armor: 0,
        personality: "aggressive",
        aggression: "standard",
        skills: [],
      },
      {
        id: "alive",
        name: "Alive",
        tier: 1,
        hp: 50,
        maxHp: 50,
        armor: 0,
        personality: "aggressive",
        aggression: "standard",
        skills: [],
      },
    ];
    const state = makeCombatState({
      iceRoster: roster,
      dixieLastAttackMs: 0,
    });
    const result = applyAction(state, { type: "use_program", programId: "p1" });
    expect(result.iceRoster[0].hp).toBe(0);
    expect(result.iceRoster[1].hp).toBeLessThan(50);
  });
});
