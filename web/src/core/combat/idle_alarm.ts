/** ADR-0240 tuning: idle pressure only; active play consumes no alarm ticks.
 * Damage is a relative multiplier; aggression adds probability points to the
 * authored tier's skill-use chance. Measured together, not per-ICE calibration.
 */
import {
  ALARM_MAX_LEVEL,
  ALARM_TICK_INTERVAL_MS,
  tickAlarm,
} from "./combat_engine";
import type { GameAction, GameState } from "../types";
import { getAlarmMultiplier } from "./ice_ai";

export const IDLE_ALARM_TUNING = {
  idleThresholdMs: 10_000,
  damagePerLevel: 0.05,
  aggressionPerLevel: 0.01,
} as const;

/** Shared dispatch gate for the browser, fake-clock harness and reducer.
 * Rebase the tick clock on the latest input: active time never carries over.
 */
export function idleAlarmAction(
  state: Readonly<GameState>,
  idleSinceMs: number,
  currentMs: number,
): Extract<GameAction, { readonly type: "idle_tick" }> | null {
  const firstTickMs = idleSinceMs + IDLE_ALARM_TUNING.idleThresholdMs;
  if (
    state.runPhase !== "combat" ||
    state.phase !== "combat" ||
    state.alarmLevel >= ALARM_MAX_LEVEL ||
    currentMs < firstTickMs ||
    currentMs - state.lastAlarmTickMs < ALARM_TICK_INTERVAL_MS
  )
    return null;
  return { type: "idle_tick", idleSinceMs };
}

/** Keep alarm-zero arithmetic identical, including non-integer base damage. */
export function alarmDamage(damage: number, alarmLevel: number): number {
  return alarmLevel === 0
    ? damage
    : Math.floor(damage * (1 + alarmLevel * IDLE_ALARM_TUNING.damagePerLevel));
}

export function applyIdleAlarmTick(
  state: Readonly<GameState>,
  idleSinceMs: number,
  currentMs: number,
): GameState {
  if (idleAlarmAction(state, idleSinceMs, currentMs) === null) return state;
  // ADR-0242: living roster minimum, recomputed each tick; stealth never stacks.
  const iceAlarmSpeed = state.iceRoster.reduce(
    (speed, ice) =>
      ice.hp > 0 ? Math.min(speed, getAlarmMultiplier(ice)) : speed,
    1,
  );
  const result = tickAlarm(
    state.alarmLevel,
    Math.max(
      state.lastAlarmTickMs,
      idleSinceMs + IDLE_ALARM_TUNING.idleThresholdMs - ALARM_TICK_INTERVAL_MS,
    ),
    currentMs,
    iceAlarmSpeed,
  );
  return {
    ...state,
    alarmLevel: result.alarmLevel,
    lastAlarmTickMs: result.lastAlarmTickMs,
    message: result.message ?? state.message,
  };
}
