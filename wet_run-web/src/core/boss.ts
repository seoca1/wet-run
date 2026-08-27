/** Boss state machine (Tier 5, ADR-0149).
 *
 * 4-phase boss behavior:
 * - Phase 1: passive attack (boss HP > 75%)
 * - Phase 2: enrage (boss HP 50-75%, +damage)
 * - Phase 3: aoe + minion spawn (boss HP 25-50%)
 * - Phase 4: desperation (boss HP < 25%, frequent attacks)
 *
 * Phase transitions are HP-threshold based (per ADR-0149). At MVP scope we
 * only track the phase; the actual per-phase behavior is rendered into
 * the combat HUD message.
 */
import type { BossPhase } from "./types.ts";

export interface BossPhaseInfo {
  readonly phase: BossPhase;
  readonly label: string;
  readonly minHpPct: number;
  readonly maxHpPct: number;
}

export const BOSS_PHASE_TABLE: ReadonlyArray<BossPhaseInfo> = [
  { phase: 0, label: "—",        minHpPct: 0,    maxHpPct: 0    }, // no boss active
  { phase: 1, label: "Phase 1", minHpPct: 75,   maxHpPct: 100  },
  { phase: 2, label: "Phase 2", minHpPct: 50,   maxHpPct: 75   },
  { phase: 3, label: "Phase 3", minHpPct: 25,   maxHpPct: 50   },
  { phase: 4, label: "Phase 4", minHpPct: 0,    maxHpPct: 25   },
];

/** Compute current boss phase from HP percentage. */
export function bossPhaseFromHp(hpPercent: number): BossPhase {
  if (hpPercent >= 75) return 1;
  if (hpPercent >= 50) return 2;
  if (hpPercent >= 25) return 3;
  return 4;
}

/** True if the boss just transitioned (new phase differs from current). */
export function shouldTransition(currentPhase: BossPhase, hpPercent: number): boolean {
  const next = bossPhaseFromHp(hpPercent);
  return next !== currentPhase && next > currentPhase;
}

/** Phase label for display in combat HUD. */
export function bossPhaseLabel(phase: BossPhase): string {
  const info = BOSS_PHASE_TABLE[phase];
  return info?.label ?? "—";
}