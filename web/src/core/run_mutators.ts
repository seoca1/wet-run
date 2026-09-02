/** Run Mutators system (ADR-0163 port).
 *
 * 5 optional mutators applied at run start that change the rules per
 * playthrough. Mutators amplify Pillar 3 (death weight) and Pillar 4
 * (build variety).
 *
 *   - LOW_HP        — Start with 50% max HP. One bad run ends you.
 *   - DOUBLE_ALARM  — Alarm ticks 2x faster. ICE pursues.
 *   - ICE_X2        — Every encounter is 1v2 or 1v3. The grid is crowded.
 *   - NO_HEAL       — Cannot salvage HEAL from kills. No recovery.
 *   - STEALTH_ONLY  — Only stealth skills available. Silent runs.
 *
 * The mutator system operates on a {@link MutableRunState} target — a
 * mutable bag of fields the mutators can read and write. This mirrors
 * the Python ``apply_mutators(app_state, mutators)`` signature without
 * coupling to a specific app-state shape.
 */

/** All available mutator kinds. */
export type RunMutator =
  | "low_hp"
  | "double_alarm"
  | "ice_x2"
  | "no_heal"
  | "stealth_only";

/** Display info for a single mutator. */
export interface MutatorInfo {
  readonly id: RunMutator;
  readonly name: string;
  readonly description: string;
  readonly icon: string;
}

/**
 * Mutable run-state fields that mutators read/write.
 *
 * Mirrors the Python `AppState` fields touched by `apply_mutators` /
 * `clear_mutators`. The application constructs one of these from its
 * full state and passes it in; mutators never need to know about other
 * fields.
 */
export interface MutableRunState {
  /** Current player HP. Mutators clamp to `playerMaxHp` after a change. */
  playerHp: number;
  /** Player max HP. LOW_HP halves this on apply, doubles on clear. */
  playerMaxHp: number;
  /** Alarm tick multiplier (1.0 = normal, 2.0 = DOUBLE_ALARM). */
  alarmSpeedMultiplier: number;
  /** Per-encounter enemy count multiplier (1 = normal, 2 = ICE_X2). */
  encounterMultiplier: number;
  /** True when HEAL salvage is disabled (NO_HEAL mutator). */
  healDisabled: boolean;
  /** Active skill filter; null = no filter, "stealth_only" = STEALTH_ONLY. */
  skillFilter: string | null;
  /** The currently active mutators (frozen tuple equivalent). */
  activeMutators: ReadonlyArray<RunMutator>;
}

/** Full catalog of mutators and their display info. */
export const MUTATORS: Readonly<Record<RunMutator, MutatorInfo>> = Object.freeze({
  low_hp: Object.freeze({
    id: "low_hp",
    name: "FRAGILE WETWARE",
    description: "Start with 50% max HP. One bad run ends you.",
    icon: "low_hp",
  }),
  double_alarm: Object.freeze({
    id: "double_alarm",
    name: "HOT TRACE",
    description: "Alarm ticks 2x faster. ICE pursues.",
    icon: "double_alarm",
  }),
  ice_x2: Object.freeze({
    id: "ice_x2",
    name: "POPULATED GRID",
    description: "Every encounter is 1v2 or 1v3. The grid is *crowded*.",
    icon: "ice_x2",
  }),
  no_heal: Object.freeze({
    id: "no_heal",
    name: "DEAD MAN WALKING",
    description: "Cannot salvage HEAL from kills. No recovery.",
    icon: "no_heal",
  }),
  stealth_only: Object.freeze({
    id: "stealth_only",
    name: "GHOST PROTOCOL",
    description: "Only stealth skills available. Silent runs.",
    icon: "stealth_only",
  }),
});

/** All mutator IDs in declaration order. */
export const ALL_MUTATORS: ReadonlyArray<RunMutator> = Object.freeze([
  "low_hp",
  "double_alarm",
  "ice_x2",
  "no_heal",
  "stealth_only",
]);

/** Return display info for a mutator (throws if the ID is unknown). */
export function getMutatorInfo(mutator: RunMutator): MutatorInfo {
  return MUTATORS[mutator];
}

/** HP multiplier for a mutator (LOW_HP = 0.5, others = 1.0). */
export function hpMultiplier(mutator: RunMutator): number {
  return mutator === "low_hp" ? 0.5 : 1.0;
}

/** Apply mutators to a run state (idempotent — clears previous first). */
export function applyMutators(
  state: MutableRunState,
  mutators: ReadonlyArray<RunMutator>,
): void {
  clearMutators(state);
  for (const mutator of mutators) {
    switch (mutator) {
      case "low_hp":
        // Guard against playerMaxHp = 0 default: if 0, initialize to 100
        // baseline before halving so the player actually has HP.
        if (state.playerMaxHp <= 0) state.playerMaxHp = 100;
        state.playerMaxHp = Math.floor(state.playerMaxHp / 2);
        state.playerHp = Math.min(state.playerHp, state.playerMaxHp);
        break;
      case "double_alarm":
        state.alarmSpeedMultiplier = 2.0;
        break;
      case "ice_x2":
        state.encounterMultiplier = 2;
        break;
      case "no_heal":
        state.healDisabled = true;
        break;
      case "stealth_only":
        state.skillFilter = "stealth_only";
        break;
    }
  }
  state.activeMutators = Object.freeze(mutators.slice());
}

/** Clear all mutator effects from a run state. */
export function clearMutators(state: MutableRunState): void {
  for (const mutator of state.activeMutators) {
    switch (mutator) {
      case "low_hp":
        // Only restore if currently halved (not zero).
        if (state.playerMaxHp > 0) state.playerMaxHp = state.playerMaxHp * 2;
        break;
      case "double_alarm":
        state.alarmSpeedMultiplier = 1.0;
        break;
      case "ice_x2":
        state.encounterMultiplier = 1;
        break;
      case "no_heal":
        state.healDisabled = false;
        break;
      case "stealth_only":
        state.skillFilter = null;
        break;
    }
  }
  state.activeMutators = Object.freeze([]);
}

/** True if the given mutator is currently active. */
export function isMutatorActive(state: MutableRunState, mutator: RunMutator): boolean {
  return state.activeMutators.includes(mutator);
}

/** Return the active mutators list (defensive copy). */
export function getActiveMutators(
  state: MutableRunState,
): ReadonlyArray<RunMutator> {
  return state.activeMutators.slice();
}

/** Current alarm speed multiplier (1.0 = normal, 2.0 = DOUBLE_ALARM). */
export function getAlarmMultiplier(state: MutableRunState): number {
  return state.alarmSpeedMultiplier;
}

/** Current encounter count multiplier (1 = normal, 2 = ICE_X2). */
export function getEncounterMultiplier(state: MutableRunState): number {
  return state.encounterMultiplier;
}

/** True if HEAL salvage is disabled (NO_HEAL mutator). */
export function isHealDisabled(state: MutableRunState): boolean {
  return state.healDisabled;
}

/** True if only stealth skills are available (STEALTH_ONLY mutator). */
export function isStealthOnly(state: MutableRunState): boolean {
  return state.skillFilter === "stealth_only";
}

/**
 * Construct a fresh, default {@link MutableRunState}.
 *
 * Mirrors the Python baseline (`player_max_hp = 100`, alarm ×1, encounter
 * ×1, heal enabled, no skill filter, no active mutators).
 */
export function makeDefaultMutableRunState(): MutableRunState {
  return {
    playerHp: 100,
    playerMaxHp: 100,
    alarmSpeedMultiplier: 1.0,
    encounterMultiplier: 1,
    healDisabled: false,
    skillFilter: null,
    activeMutators: Object.freeze([]),
  };
}
