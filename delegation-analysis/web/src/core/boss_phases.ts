/**
 * Boss Phase Transition System
 *
 * Manages multi-phase boss fights where each phase triggers at specific HP
 * thresholds and modifies boss behavior (damage multipliers, special mechanics).
 *
 * Ported from Python wet_run combat system:
 * - state_transitions.py: _check_boss_phase_transition (lines 75-98)
 * - state_models.py: CombatState boss fields (lines 155, 281-292)
 * - boss.py: BossProfile and PhaseProfile dataclasses
 */

/** Boss phase definition — one of 4 phases in a boss fight. */
export interface BossPhaseDefinition {
  readonly phase: 1 | 2 | 3 | 4;
  readonly hpThreshold: number; // 0.0-1.0, triggers when hp/maxHp <= threshold
  readonly damageMultiplier: number; // boss deals this × damage in this phase
  readonly label: string; // e.g. "Berserk", "Overclocked", "Terminal"
  readonly color: string; // hex color for phase badge flash
  readonly mechanic?: string; // phase 4 special mechanic id (optional)
}

/** Boss profile — full definition of a boss's phases. */
export interface BossProfile {
  readonly id: string;
  readonly name: string;
  readonly phases: ReadonlyArray<BossPhaseDefinition>;
}

/** Runtime tracker for boss phase transitions during combat. */
export interface BossPhaseTrackerState {
  readonly bossProfile: BossProfile | null;
  readonly currentPhase: number; // 0 = no boss, 1-4 = active phase
  readonly phaseChangeMs: number; // tick_ms of last transition (for UI flash)
  readonly phaseChangeColor: string; // color of last transition
}

/**
 * Standard 4-phase boss profile matching Python WINTERMUTE/TA_CONSTRUCT pattern.
 *
 * Phase thresholds:
 * - Phase 1: 100% HP (always active at start)
 * - Phase 2: ≤75% HP
 * - Phase 3: ≤50% HP
 * - Phase 4: ≤25% HP (desperation mechanic)
 */
export const DEFAULT_BOSS_PROFILE: BossProfile = {
  id: "boss_standard",
  name: "ICE Juggernaut",
  phases: [
    {
      phase: 1,
      hpThreshold: 1.0,
      damageMultiplier: 1.0,
      label: "Standard",
      color: "#ffffff",
    },
    {
      phase: 2,
      hpThreshold: 0.75,
      damageMultiplier: 1.25,
      label: "Alert",
      color: "#ffff00",
    },
    {
      phase: 3,
      hpThreshold: 0.5,
      damageMultiplier: 1.5,
      label: "Berserk",
      color: "#ff8800",
    },
    {
      phase: 4,
      hpThreshold: 0.25,
      damageMultiplier: 2.0,
      label: "Terminal",
      color: "#ff0000",
      mechanic: "desperation",
    },
  ],
};

/**
 * Create initial boss phase tracker state.
 *
 * @param profile - Boss profile to track, or null for non-boss combat
 * @returns Initial tracker state with phase 1 active (or 0 if no profile)
 */
export function createBossTracker(
  profile: BossProfile | null,
): BossPhaseTrackerState {
  return {
    bossProfile: profile,
    currentPhase: profile !== null ? 1 : 0,
    phaseChangeMs: 0,
    phaseChangeColor: "#ffffff",
  };
}

/**
 * Check if boss should transition to next phase based on current HP.
 *
 * Logic (from state_transitions.py lines 75-98):
 * 1. Calculate HP fraction: targetHp / targetMaxHp
 * 2. Find highest phase whose hpThreshold >= hpFraction
 * 3. If that phase > currentPhase → transition with timestamp + color
 * 4. Otherwise → no change
 *
 * @param tracker - Current phase tracker state
 * @param targetHp - Current boss HP
 * @param targetMaxHp - Boss max HP
 * @param tickMs - Current game tick (milliseconds) for transition timestamp
 * @returns Updated tracker if phase changed, unchanged tracker otherwise
 */
export function checkPhaseTransition(
  tracker: BossPhaseTrackerState,
  targetHp: number,
  targetMaxHp: number,
  tickMs: number,
): BossPhaseTrackerState {
  const { bossProfile, currentPhase } = tracker;

  if (bossProfile === null || currentPhase >= 4 || targetMaxHp <= 0) {
    return tracker;
  }

  const hpFraction = targetHp / targetMaxHp;

  let targetPhase = currentPhase;
  let transitionColor = tracker.phaseChangeColor;

  for (const phaseDef of bossProfile.phases) {
    if (hpFraction <= phaseDef.hpThreshold && phaseDef.phase > targetPhase) {
      targetPhase = phaseDef.phase;
      transitionColor = phaseDef.color;
    }
  }

  if (targetPhase > currentPhase) {
    return {
      ...tracker,
      currentPhase: targetPhase,
      phaseChangeMs: tickMs,
      phaseChangeColor: transitionColor,
    };
  }

  return tracker;
}

/**
 * Get damage multiplier for current boss phase.
 *
 * @param tracker - Current phase tracker state
 * @returns Damage multiplier (1.0-3.0), or 1.0 if no boss profile
 */
export function getPhaseDamageMultiplier(
  tracker: BossPhaseTrackerState,
): number {
  const { bossProfile, currentPhase } = tracker;

  if (bossProfile === null || currentPhase === 0) {
    return 1.0;
  }

  const phaseDef = bossProfile.phases.find((p) => p.phase === currentPhase);
  return phaseDef?.damageMultiplier ?? 1.0;
}

/**
 * Get phase label for UI display.
 *
 * @param tracker - Current phase tracker state
 * @returns Phase label string, or empty string if no boss
 */
export function getPhaseLabel(tracker: BossPhaseTrackerState): string {
  const { bossProfile, currentPhase } = tracker;

  if (bossProfile === null || currentPhase === 0) {
    return "";
  }

  const phaseDef = bossProfile.phases.find((p) => p.phase === currentPhase);
  return phaseDef?.label ?? "";
}

/**
 * Get special mechanic ID for current phase (typically phase 4 only).
 *
 * @param tracker - Current phase tracker state
 * @returns Mechanic ID string, or undefined if no mechanic
 */
export function getPhaseMechanic(
  tracker: BossPhaseTrackerState,
): string | undefined {
  const { bossProfile, currentPhase } = tracker;

  if (bossProfile === null || currentPhase === 0) {
    return undefined;
  }

  const phaseDef = bossProfile.phases.find((p) => p.phase === currentPhase);
  return phaseDef?.mechanic;
}

/**
 * Get phase color for UI effects.
 *
 * @param tracker - Current phase tracker state
 * @returns Hex color string, or white if no boss
 */
export function getPhaseColor(tracker: BossPhaseTrackerState): string {
  const { bossProfile, currentPhase } = tracker;

  if (bossProfile === null || currentPhase === 0) {
    return "#ffffff";
  }

  const phaseDef = bossProfile.phases.find((p) => p.phase === currentPhase);
  return phaseDef?.color ?? "#ffffff";
}
