/**
 * Combat damage calculation engine.
 * Pure functions for damage calc, combo timeout, and alarm tick.
 * Ported from Python wet_run combat system.
 */

// ========== CONSTANTS ==========

export const TICK_MS = 100;
export const AUTO_ATTACK_INTERVAL_MS = 2000;
export const AP_REGEN_INTERVAL_MS = 2000;
export const DAMAGE_VARIANCE_MIN = 0.8;
export const DAMAGE_VARIANCE_MAX = 1.2;
export const CRIT_CHANCE = 0.15;
export const CRIT_MULTIPLIER = 2.0;
export const CRIT_MULTIPLIER_MIN = 1.8;
export const CRIT_MULTIPLIER_MAX = 2.2;
export const STAGGER_DURATION_MS = 1500;
export const COMBO_WINDOW_MS = 3500;
export const ALARM_TICK_INTERVAL_MS = 10000;
export const ALARM_MAX_LEVEL = 5;
export const DEFAULT_WEAKNESS_MULTIPLIER = 1.0;
export const DEFAULT_ALARM_SPEED = 1.0;

// ========== LOOKUP TABLES ==========

export const WEAKNESS_BY_ICE: Readonly<Record<string, Readonly<Record<string, number>>>> = {
  standard: { strike: 1.5, burst: 1.2, guard: 1.0, utility: 1.0, sustain: 0.8 },
  watchdog: { burst: 1.5, strike: 1.2, guard: 1.0, utility: 0.8, sustain: 0.6 },
  goliath: { sustain: 1.5, utility: 1.0, strike: 1.0, guard: 0.9, burst: 0.7 },
  black: { burst: 1.5, strike: 1.0, utility: 0.8, guard: 0.7, sustain: 0.6 },
  construct: { utility: 1.5, strike: 1.0, burst: 1.0, guard: 1.0, sustain: 0.8 },
  wintermute: { strike: 1.5, guard: 1.0, utility: 1.0, sustain: 1.0, burst: 0.6 },
  ta_construct_prime: { burst: 1.5, strike: 0.8, guard: 0.8, utility: 0.8, sustain: 0.8 },
};

export const ROLE_SYNERGY_BONUSES: Readonly<Record<number, number>> = {
  1: 1.0,
  2: 1.15,
  3: 1.30,
  4: 1.50,
  5: 1.75,
};

export const COMBO_BONUSES: Readonly<Record<number, number>> = {
  1: 1.0,
  2: 1.0,
  3: 1.2,
  4: 1.5,
  5: 2.0,
  6: 3.0,
};

export const ROLE_CRIT_BONUSES: Readonly<Record<string, number>> = {
  strike: 0.05,
  burst: 0.10,
  guard: 0.0,
  utility: 0.05,
  sustain: 0.0,
};

export const ALARM_SPEED_BY_ICE: Readonly<Record<string, number>> = {
  standard: 1.0,
  watchdog: 1.3,
  goliath: 0.7,
  black: 2.0,
  construct: 0.5,
  wintermute: 2.5,
  ta_construct_prime: 3.0,
};

// ========== TYPES ==========

export interface DamageContext {
  readonly baseDamage: number;
  readonly attackerTeam: "player" | "enemy";
  readonly attackerAttackBonus: number;
  readonly attackerCritBonusPct: number;
  readonly defenderDefenseBonus: number;
  readonly defenderIceResistance: number;
  readonly defenderIceKind: string | null;
  readonly lastSkillRole: string | null;
  readonly lastSkillCritBonus: number;
  readonly playerCombo: number;
  readonly roleSynergyCount: number;
  readonly defenderVulnerabilityPct: number;
  readonly defenderSlowReductionPct: number;
  readonly rng: () => number;
}

export interface DamageResult {
  readonly damage: number;
  readonly isCrit: boolean;
}

export interface AlarmTickResult {
  readonly alarmLevel: number;
  readonly lastAlarmTickMs: number;
  readonly message: string | null;
}

// ========== DAMAGE CALCULATION ==========

export function calculateDamage(ctx: DamageContext): DamageResult {
  const variance = ctx.rng() * (DAMAGE_VARIANCE_MAX - DAMAGE_VARIANCE_MIN) + DAMAGE_VARIANCE_MIN;
  let dmg = ctx.baseDamage * variance;

  if (ctx.defenderIceResistance > 0.0) {
    dmg *= 1.0 - ctx.defenderIceResistance;
  }

  if (
    ctx.attackerTeam === "player" &&
    ctx.lastSkillRole !== null &&
    ctx.defenderIceKind !== null
  ) {
    const weaknessMap = WEAKNESS_BY_ICE[ctx.defenderIceKind];
    const weakness = weaknessMap?.[ctx.lastSkillRole] ?? DEFAULT_WEAKNESS_MULTIPLIER;
    dmg *= weakness;
  }

  if (ctx.attackerTeam === "player" && ctx.lastSkillRole !== null) {
    const synergyMult = ROLE_SYNERGY_BONUSES[ctx.roleSynergyCount] ?? 1.0;
    dmg *= synergyMult;
  }

  if (ctx.attackerTeam === "player") {
    const comboMult = COMBO_BONUSES[ctx.playerCombo] ?? 1.0;
    dmg *= comboMult;
  }

  dmg = Math.floor(dmg * (1.0 + ctx.defenderVulnerabilityPct / 100));

  dmg += ctx.attackerAttackBonus;

  dmg = Math.max(0, dmg - ctx.defenderDefenseBonus);

  let isCrit = false;
  let critChance = CRIT_CHANCE;
  critChance += ctx.attackerCritBonusPct / 100;
  critChance += ctx.lastSkillCritBonus;
  if (ctx.lastSkillRole !== null) {
    critChance += ROLE_CRIT_BONUSES[ctx.lastSkillRole] ?? 0.0;
  }

  if (ctx.rng() < critChance) {
    const critMult =
      ctx.rng() * (CRIT_MULTIPLIER_MAX - CRIT_MULTIPLIER_MIN) + CRIT_MULTIPLIER_MIN;
    dmg = Math.floor(dmg * critMult);
    isCrit = true;
  }

  return {
    damage: Math.max(1, Math.floor(dmg)),
    isCrit,
  };
}

// ========== COMBO TICK ==========

export function tickCombo(
  playerCombo: number,
  comboLastHitMs: number,
  currentTickMs: number,
): number {
  if (playerCombo > 0 && currentTickMs - comboLastHitMs > COMBO_WINDOW_MS) {
    return 0;
  }
  return playerCombo;
}

// ========== ALARM TICK ==========

export function tickAlarm(
  currentAlarmLevel: number,
  lastAlarmTickMs: number,
  currentTickMs: number,
  iceAlarmSpeed: number,
): AlarmTickResult {
  const tickInterval = ALARM_TICK_INTERVAL_MS / Math.max(0.01, iceAlarmSpeed);

  if (currentTickMs - lastAlarmTickMs >= tickInterval) {
    const newLevel = Math.min(currentAlarmLevel + 1, ALARM_MAX_LEVEL);
    return {
      alarmLevel: newLevel,
      lastAlarmTickMs: currentTickMs,
      message: `TRACE WARNING: alarm level ${newLevel}/${ALARM_MAX_LEVEL}`,
    };
  }

  return {
    alarmLevel: currentAlarmLevel,
    lastAlarmTickMs,
    message: null,
  };
}

// ========== ROLE SYNERGY COUNTER ==========

export function countRoleSynergy(
  lastSkillRole: string | null,
  playerSkills: ReadonlyArray<{ readonly role: string | null }>,
): number {
  if (lastSkillRole === null) {
    return 0;
  }
  return playerSkills.filter((s) => s.role === lastSkillRole).length;
}
