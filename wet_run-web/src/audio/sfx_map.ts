/** SFX mapping for programs and game events.
 *
 * Centralizes which sound effect plays for each program type and event.
 * Keeps audio logic out of the core state reducer.
 */

import { SFX_IDS } from "./manager.ts";

/** Map program effect strings to SFX IDs. */
const PROGRAM_SFX_MAP: Readonly<Record<string, keyof typeof SFX_IDS>> = {
  strike: "SKILL_STRIKE",
  hammer: "SKILL_HAMMER",
  virus: "SKILL_VIRUS",
  wardrone: "SKILL_WARDRONE",
  // Default fallback
  default: "COMBAT_HIT",
} as const;

/** Get the SFX ID for a program effect. */
export function getSfxForProgram(effect: string): keyof typeof SFX_IDS {
  return PROGRAM_SFX_MAP[effect] ?? PROGRAM_SFX_MAP.default;
}

/** Play SFX for a program use (called from main.ts after state update). */
export function playProgramSfx(effect: string): void {
  const sfxKey = getSfxForProgram(effect);
  // AudioManager imported lazily to avoid circular deps
  import("./manager.ts").then(({ AudioManager }) => {
    AudioManager.getInstance().playSfx(SFX_IDS[sfxKey]);
  });
}

/** Play UI navigation SFX. */
export function playUiSelect(): void {
  import("./manager.ts").then(({ AudioManager, SFX_IDS }) => {
    AudioManager.getInstance().playSfx(SFX_IDS.UI_SELECT);
  });
}

/** Play UI confirm SFX. */
export function playUiConfirm(): void {
  import("./manager.ts").then(({ AudioManager, SFX_IDS }) => {
    AudioManager.getInstance().playSfx(SFX_IDS.UI_CONFIRM);
  });
}

/** Play UI cancel/back SFX. */
export function playUiCancel(): void {
  import("./manager.ts").then(({ AudioManager, SFX_IDS }) => {
    AudioManager.getInstance().playSfx(SFX_IDS.UI_CANCEL);
  });
}

/** Play movement SFX (matrix node transition). */
export function playMovement(): void {
  import("./manager.ts").then(({ AudioManager, SFX_IDS }) => {
    AudioManager.getInstance().playSfx(SFX_IDS.MOVEMENT_NODE);
  });
}

/** Play alarm increase SFX. */
export function playAlarmTick(): void {
  import("./manager.ts").then(({ AudioManager, SFX_IDS }) => {
    AudioManager.getInstance().playSfx(SFX_IDS.ALARM_TICK);
  });
}

/** Play burn damage SFX. */
export function playBurnTick(): void {
  import("./manager.ts").then(({ AudioManager, SFX_IDS }) => {
    AudioManager.getInstance().playSfx(SFX_IDS.BURN_TICK);
  });
}

/** Play combat block SFX (armor mitigated damage). */
export function playCombatBlock(): void {
  import("./manager.ts").then(({ AudioManager, SFX_IDS }) => {
    AudioManager.getInstance().playSfx(SFX_IDS.COMBAT_BLOCK);
  });
}