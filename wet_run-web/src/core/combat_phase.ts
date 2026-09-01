/** Combat Phase State Machine (Tier 5).
 *
 * Manages the combat turn flow with explicit phases for animation timing.
 * Each phase gates what actions are allowed and what systems run.
 *
 * Phase flow (per combat turn):
 *   idle → turn_start → player_act → animating → ice_turn → resolving → (idle | loot | ending)
 *
 * Boss transitions inject a boss_transition phase between resolving and next turn_start.
 *
 * IMPORTANT: The phase machine is advanced synchronously within useProgram.
 * The draw loop only ticks VFX and checks isInputBlocked().
 */

/** All possible combat phases. */
export type CombatPhaseType =
  | "idle"              // Waiting for player input (program selection)
  | "turn_start"        // Tick status effects, apply burn DoT, check stun/silence
  | "player_act"        // Player selects/uses a program, resolve attack + VFX
  | "animating"         // VFX playing (card_use → card_hit → ice_hit); input blocked
  | "ice_turn"          // ICE counter-attack (if alive and not stunned)
  | "resolving"         // Check victory/defeat, advance boss phase, transition
  | "boss_transition";  // Boss phase advance VFX playing; input blocked

/** Combat phase metadata attached to GameState. */
export interface CombatPhaseState {
  readonly phase: CombatPhaseType;
  /** For animating/boss_transition: number of VFX instances still playing. */
  readonly vfxRemaining: number;
  /** For player_act: the program ID that was used (for VFX trigger). */
  readonly lastProgramId?: string;
  /** For ice_turn: whether ICE is stunned this turn. */
  readonly iceStunned?: boolean;
  /** For ice_turn: whether ICE is silenced this turn. */
  readonly iceSilenced?: boolean;
  /** For turn_start: whether player is stunned this turn. */
  readonly playerStunned?: boolean;
  /** For turn_start: whether player is silenced this turn. */
  readonly playerSilenced?: boolean;
}

/** Initial combat phase state. */
export const INITIAL_COMBAT_PHASE: CombatPhaseState = {
  phase: "idle",
  vfxRemaining: 0,
};

/** Check if input should be blocked for the current combat phase. */
export function isInputBlocked(cp: CombatPhaseState): boolean {
  return cp.phase === "animating" || cp.phase === "boss_transition";
}

/** Check if the combat phase allows program selection. */
export function canSelectProgram(cp: CombatPhaseState): boolean {
  return cp.phase === "idle" || cp.phase === "player_act";
}

/** Create a new combat phase state for program use (called from applyCombatAction). */
export function onProgramUsed(
  combatPhase: CombatPhaseState,
  programId: string,
): CombatPhaseState {
  return {
    ...combatPhase,
    phase: "turn_start",
    lastProgramId: programId,
  };
}

/** Create combat phase state for boss phase transition (called when bossPhase advances). */
export function onBossPhaseAdvanced(combatPhase: CombatPhaseState): CombatPhaseState {
  return {
    ...combatPhase,
    phase: "boss_transition",
    vfxRemaining: 1,
  };
}