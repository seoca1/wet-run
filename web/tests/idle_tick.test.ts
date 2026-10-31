import { afterEach, describe, expect, it, vi } from "vitest";
import { applyAction, makeInitialState } from "../src/core/state/state";
import { idleAlarmAction } from "../src/core/combat/idle_alarm";
import type { GameState, Ice, Mission, Program } from "../src/core/types";

const mission: Mission = {
  id: "idle_test",
  title: "Idle test",
  fixer: "test",
  arc: 1,
  zone: "test",
  grade_min: 3,
  grade_max: 3,
  grade: 3,
  rewards: { credits: 0, materials: {} },
};
const card: Program = {
  id: "probe",
  name: "Probe",
  tier: 1,
  cost: 1,
  effect: "attack",
  description: "Probe",
  aoe: false,
};
const enemy: Ice = {
  id: "test",
  name: "Test ICE",
  tier: 3,
  hp: 1000,
  maxHp: 1000,
  armor: 20,
  personality: "defensive",
  aggression: "standard",
};
const origin = 1_000_000;

function combat(ice: Ice = enemy): GameState {
  const base = makeInitialState(mission, ice, [card]);
  return {
    ...base,
    runPhase: "combat",
    phase: "combat",
    player: { ...base.player, hp: 1000, maxHp: 1000 },
    dixieLastAttackMs: Number.MAX_SAFE_INTEGER,
  };
}

function raisedAlarm(state: GameState, levels: number): GameState {
  let result = state;
  for (let level = 1; level <= levels; level++) {
    vi.spyOn(Date, "now").mockReturnValue(origin + level * 10_000);
    result = applyAction(result, { type: "idle_tick", idleSinceMs: origin });
  }
  return result;
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("ADR-0240 idle tick", () => {
  it("writes alarm and tick time through applyAction without damage, cards or RNG", () => {
    // Given
    const state = Object.freeze(combat());
    const random = vi.spyOn(Math, "random");
    vi.spyOn(Date, "now").mockReturnValue(origin + 10_000);
    // When
    const result = applyAction(state, {
      type: "idle_tick",
      idleSinceMs: origin,
    });
    // Then
    expect(result.alarmLevel).toBe(1);
    expect(result.lastAlarmTickMs).toBe(origin + 10_000);
    expect(state.alarmLevel).toBe(0);
    expect(result.player).toBe(state.player);
    expect(result.deck).toBe(state.deck);
    expect(result.lastEnemyAttackMs).toBe(state.lastEnemyAttackMs);
    expect(random).not.toHaveBeenCalled();
  });

  it("never ticks during active play even after a minute of elapsed time", () => {
    // Given
    const state = combat();
    // When
    const results = Array.from({ length: 30 }, (_, index) => {
      const now = origin + (index + 1) * 2000;
      vi.spyOn(Date, "now").mockReturnValue(now);
      expect(idleAlarmAction(state, now - 2000, now)).toBeNull();
      return applyAction(state, { type: "idle_tick", idleSinceMs: now - 2000 });
    });
    // Then
    expect(results.every((result) => result === state)).toBe(true);
  });

  it("does not bank pre-input time into the next idle period", () => {
    // Given
    const state = raisedAlarm(combat(), 1);
    vi.spyOn(Date, "now").mockReturnValue(origin + 25_999);
    // When
    const result = applyAction(state, {
      type: "idle_tick",
      idleSinceMs: origin + 16_000,
    });
    // Then
    expect(result).toBe(state);
  });

  it("honors the 10-second interval and caps at five without repeated writes", () => {
    // Given
    const state = raisedAlarm(combat(), 5);
    vi.spyOn(Date, "now").mockReturnValue(origin + 60_000);
    // When
    const result = applyAction(state, {
      type: "idle_tick",
      idleSinceMs: origin,
    });
    // Then
    expect(result).toBe(state);
    expect(result.alarmLevel).toBe(5);
    expect(result.lastAlarmTickMs).toBe(origin + 50_000);
  });

  it("ignores duplicate ticks in the same interval", () => {
    // Given
    const state = raisedAlarm(combat(), 1);
    vi.spyOn(Date, "now").mockReturnValue(origin + 19_999);
    // When
    const result = applyAction(state, {
      type: "idle_tick",
      idleSinceMs: origin,
    });
    // Then
    expect(result).toBe(state);
  });

  it.each(["matrix", "loot", "ending", "dead"] as const)(
    "ignores ticks in %s",
    (runPhase) => {
      // Given
      const state = { ...combat(), runPhase };
      vi.spyOn(Date, "now").mockReturnValue(origin + 60_000);
      // When
      const result = applyAction(state, {
        type: "idle_tick",
        idleSinceMs: origin,
      });
      // Then
      expect(result).toBe(state);
    },
  );

  it.each([false, true])(
    "increases enemy damage after idle (skill=%s)",
    (skill) => {
      // Given
      const ice: Ice = skill
        ? {
            ...enemy,
            skills: [
              {
                id: "hit",
                name: "Hit",
                damage: 100,
                cooldownMs: 0,
                effect: "attack",
              },
            ],
          }
        : enemy;
      const baseline = combat(ice);
      const alarmed = raisedAlarm(baseline, 5);
      vi.spyOn(Math, "random").mockReturnValue(0.1);
      // When
      const activeResult = applyAction(baseline, {
        type: "use_program",
        programId: card.id,
      });
      const idleResult = applyAction(alarmed, {
        type: "use_program",
        programId: card.id,
      });
      // Then
      expect(idleResult.player.hp).toBeLessThan(activeResult.player.hp);
    },
  );

  it("increases aggression by promoting the same roll from auto-attack to skill", () => {
    // Given
    const ice: Ice = {
      ...enemy,
      skills: [
        {
          id: "hit",
          name: "Hit",
          damage: 100,
          cooldownMs: 0,
          effect: "attack",
        },
      ],
    };
    const baseline = combat(ice);
    const alarmed = raisedAlarm(baseline, 1);
    vi.spyOn(Math, "random").mockReturnValue(0.151);
    // When
    const activeResult = applyAction(baseline, {
      type: "use_program",
      programId: card.id,
    });
    const idleResult = applyAction(alarmed, {
      type: "use_program",
      programId: card.id,
    });
    // Then
    expect(activeResult.skillCooldowns["test_hit"]).toBeUndefined();
    expect(idleResult.skillCooldowns["test_hit"]).toBe(0);
    expect(idleResult.player.hp).toBeLessThan(activeResult.player.hp);
  });
});
