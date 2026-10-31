import { afterEach, describe, expect, it, vi } from "vitest";
import { ALARM_TICK_INTERVAL_MS } from "../src/core/combat/combat_engine";
import * as iceAi from "../src/core/combat/ice_ai";
import { applyIdleAlarmTick } from "../src/core/combat/idle_alarm";
import * as runMutators from "../src/core/state/run_mutators";
import { makeInitialState } from "../src/core/state/state";
import type { GameState, Ice, Mission } from "../src/core/types";

const mission: Mission = {
  id: "archetype_alarm",
  title: "Archetype alarm",
  fixer: "test",
  arc: 1,
  zone: "test",
  grade_min: 1,
  grade_max: 1,
  grade: 1,
  rewards: { credits: 0, materials: {} },
};
const ordinary: Ice = {
  id: "ordinary",
  name: "Ordinary ICE",
  tier: 1,
  hp: 100,
  armor: 0,
  personality: "defensive",
};
const stealth: Ice = { ...ordinary, id: "stealth", personality: "stealth" };
const origin = 1_000_000;
const interval = ALARM_TICK_INTERVAL_MS;

function combat(roster: readonly Ice[]): GameState {
  return {
    ...makeInitialState(mission, ordinary, []),
    runPhase: "combat",
    phase: "combat",
    iceRoster: roster,
    lastAlarmTickMs: origin,
  };
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("ADR-0242 ICE archetype alarm rate", () => {
  it.each([interval, interval / 0.5 - 1, interval / 0.5])(
    "uses a doubled tick interval for stealth at elapsed %i ms",
    (elapsed) => {
      // Given
      const state = combat([stealth]);
      // When
      const result = applyIdleAlarmTick(state, origin, origin + elapsed);
      // Then
      expect(result.alarmLevel).toBe(elapsed >= interval / 0.5 ? 1 : 0);
      expect(result.lastAlarmTickMs).toBe(
        elapsed >= interval / 0.5 ? origin + elapsed : origin,
      );
    },
  );

  it.each(["aggressive", "defensive", "support", undefined] as const)(
    "preserves the ADR-0240 interval for personality %s",
    (personality) => {
      // Given
      const state = combat([{ ...ordinary, personality }]);
      // When
      const result = applyIdleAlarmTick(state, origin, origin + interval);
      // Then
      expect(result.alarmLevel).toBe(1);
      expect(result.lastAlarmTickMs).toBe(origin + interval);
    },
  );

  it.each([interval / 0.5 - 1, interval / 0.5])(
    "keeps subsequent stealth ticks at 20 seconds at elapsed %i ms",
    (elapsed) => {
      // Given
      const state = { ...combat([stealth]), alarmLevel: 1 };
      // When
      const result = applyIdleAlarmTick(
        state,
        origin - interval,
        origin + elapsed,
      );
      // Then
      expect(result.alarmLevel).toBe(elapsed >= interval / 0.5 ? 2 : 1);
    },
  );

  it.each(
    [
      [ordinary, stealth],
      [stealth, ordinary],
      [stealth, { ...stealth, id: "second_stealth" }],
    ].flatMap((roster) =>
      [interval, interval / 0.5].map((elapsed) => ({
        roster,
        elapsed,
      })),
    ),
  )(
    "uses the alive roster minimum without stacking ($roster, $elapsed ms)",
    ({ roster, elapsed }) => {
      // Given
      const state = combat(roster);
      // When
      const result = applyIdleAlarmTick(state, origin, origin + elapsed);
      // Then
      expect(result.alarmLevel).toBe(elapsed >= interval / 0.5 ? 1 : 0);
      expect(result.lastAlarmTickMs).toBe(
        elapsed >= interval / 0.5 ? origin + elapsed : origin,
      );
    },
  );

  it("stops slowing on the next tick after the last stealth ICE dies", () => {
    // Given
    const delayed = applyIdleAlarmTick(
      combat([ordinary, stealth]),
      origin,
      origin + interval,
    );
    const state = {
      ...delayed,
      ice: stealth,
      activeIceIndex: 1,
      iceRoster: [ordinary, { ...stealth, hp: 0 }],
    };
    // When
    const result = applyIdleAlarmTick(state, origin, origin + interval + 1);
    // Then
    expect(result.alarmLevel).toBe(1);
    expect(result.lastAlarmTickMs).toBe(origin + interval + 1);
  });

  it("uses the neutral rate when the roster is empty", () => {
    // Given
    const state = { ...combat([]), ice: stealth };
    // When
    const result = applyIdleAlarmTick(state, origin, origin + interval);
    // Then
    expect(result.alarmLevel).toBe(1);
  });

  it("calls ice_ai's multiplier, never the same-named run-mutator function", () => {
    // Given
    const archetypeMultiplier = vi.spyOn(iceAi, "getAlarmMultiplier");
    const runMultiplier = vi.spyOn(runMutators, "getAlarmMultiplier");
    const state = combat([stealth, { ...stealth, hp: 0 }]);
    // When
    const result = applyIdleAlarmTick(state, origin, origin + interval);
    // Then
    expect(archetypeMultiplier).toHaveBeenCalledTimes(1);
    expect(archetypeMultiplier).toHaveBeenCalledWith(stealth);
    expect(archetypeMultiplier).toHaveReturnedWith(0.5);
    expect(runMultiplier).not.toHaveBeenCalled();
    expect(result.alarmLevel).toBe(0);
  });
});
