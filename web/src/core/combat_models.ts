/**
 * Combat state models — TypeScript port of Python state_models.py.
 *
 * Contains pure data interfaces for combat system:
 *   - SkillEffect enum
 *   - Skill interface
 *   - StatusEffect interface
 *   - CombatStats interface
 *   - Combatant interface
 *   - CombatState interface
 */

export type SkillEffectKind =
  | "attack"
  | "heavy_attack"
  | "pierce"
  | "multi_hit"
  | "dot"
  | "shield"
  | "regen"
  | "heal"
  | "buff"
  | "debuff"
  | "detect"
  | "stun"
  | "stagger"
  | "counter"
  | "lifesteal"
  | "poison"
  | "silence"
  | "slow"
  | "vulnerable";

export type CombatantTeam = "player" | "enemy";
export type CombatOutcome = "ongoing" | "victory" | "defeat";
export type AggressionTier = "passive" | "standard" | "aggressive" | "boss";
export type PersonalityArchetype = "aggressive" | "defensive" | "stealth" | "support";

export interface Skill {
  readonly id: string;
  readonly name: string;
  readonly tier: number;
  readonly effect: SkillEffectKind;
  readonly apCost: number;
  readonly damage: number;
  readonly shield: number;
  readonly heal: number;
  readonly dotDamage: number;
  readonly dotDurationMs: number;
  readonly buffAmount: number;
  readonly buffDurationMs: number;
  readonly stunDurationMs: number;
  readonly hitCount: number;
  readonly cooldownMs: number;
  readonly critBonus: number;
  readonly role: string | null;
  readonly aoe: boolean;
  readonly effectColor: string;
  readonly effectGlyph: string;
}

export interface StatusEffect {
  readonly effectId: string;
  readonly remainingMs: number;
  readonly dotDamage: number;
  readonly healPerTick: number;
  readonly attackBonus: number;
  readonly defenseBonus: number;
  readonly isStunned: boolean;
  readonly isStaggered: boolean;
  readonly isShield: boolean;
  readonly slowPct: number;
  readonly isSilenced: boolean;
  readonly vulnerabilityPct: number;
}

export interface CombatStats {
  damageDealt: number;
  damageReceived: number;
  critsLanded: number;
  critsReceived: number;
  skillsUsed: number;
  maxComboReached: number;
  peakAlarmLevel: number;
  turnsElapsed: number;
}

export interface Combatant {
  readonly id: string;
  readonly name: string;
  readonly portrait: string;
  readonly color: string;
  hp: number;
  readonly maxHp: number;
  ap: number;
  readonly maxAp: number;
  readonly autoAttackDamage: number;
  readonly skills: ReadonlyArray<Skill>;
  readonly team: CombatantTeam;
  statuses: Array<StatusEffect>;
  readonly baseAttack: number;
  readonly baseDefense: number;
  readonly equipAttackBonus: number;
  readonly equipDefenseBonus: number;
  readonly equipHpBonus: number;
  readonly equipShieldBonus: number;
  readonly equipApBonus: number;
  readonly equipProgramPower: number;
  readonly equipIceResistance: number;
  readonly equipDamageBonusPct: number;
  readonly equipCritBonusPct: number;
  readonly equipGrantsSkillId: string | null;
  readonly iceKind: string | null;
  readonly iceResistance: number;
  readonly alarmSpeed: number;
  currentPhase: number;
  readonly aggression: AggressionTier;
  readonly personality: PersonalityArchetype;
}

export interface CombatState {
  player: Combatant;
  enemies: Array<Combatant>;
  targetIndex: number;
  tickMs: number;
  lastPlayerAttackMs: number;
  lastEnemyAttackMs: number;
  lastApRegenMs: number;
  shield: number;
  log: Array<string>;
  finished: boolean;
  outcome: CombatOutcome;
  lastSkillUsed: Skill | null;
  skillCooldowns: Map<string, number>;
  lastEvent: string;
  lastEventColor: string;
  lastEventTick: number;
  playerCombo: number;
  enemyCombo: number;
  deckSize: string;
  comboLastHitMs: number;
  alarmLevel: number;
  lastAlarmTickMs: number;
  stats: CombatStats;
  counterWindowOpenMs: number;
  dixieLastAttackMs: number;
  wardroneLastCounterMs: number;
  bossPhase4Mechanic: string | null;
  phaseChangeMs: number;
  phaseChangeColor: string;
  friendlyNodeHp: number;
}

export function createCombatStats(): CombatStats {
  return {
    damageDealt: 0,
    damageReceived: 0,
    critsLanded: 0,
    critsReceived: 0,
    skillsUsed: 0,
    maxComboReached: 0,
    peakAlarmLevel: 0,
    turnsElapsed: 0,
  };
}

export function createCombatant(overrides: Partial<Combatant> & Pick<Combatant, "id" | "name" | "hp" | "maxHp">): Combatant {
  return {
    portrait: "",
    color: "#ffffff",
    ap: 0,
    maxAp: 6,
    autoAttackDamage: 5,
    skills: [],
    team: "enemy",
    statuses: [],
    baseAttack: 0,
    baseDefense: 0,
    equipAttackBonus: 0,
    equipDefenseBonus: 0,
    equipHpBonus: 0,
    equipShieldBonus: 0,
    equipApBonus: 0,
    equipProgramPower: 0,
    equipIceResistance: 0,
    equipDamageBonusPct: 0,
    equipCritBonusPct: 0,
    equipGrantsSkillId: null,
    iceKind: null,
    iceResistance: 0,
    alarmSpeed: 1,
    currentPhase: 1,
    aggression: "standard",
    personality: "aggressive",
    ...overrides,
  };
}

export function createCombatState(player: Combatant, enemies: Combatant[]): CombatState {
  return {
    player,
    enemies,
    targetIndex: 0,
    tickMs: 0,
    lastPlayerAttackMs: -2000,
    lastEnemyAttackMs: -2000,
    lastApRegenMs: 0,
    shield: 0,
    log: [],
    finished: false,
    outcome: "ongoing",
    lastSkillUsed: null,
    skillCooldowns: new Map(),
    lastEvent: "",
    lastEventColor: "#ffffff",
    lastEventTick: 0,
    playerCombo: 0,
    enemyCombo: 0,
    deckSize: "standard",
    comboLastHitMs: 0,
    alarmLevel: 0,
    lastAlarmTickMs: 0,
    stats: createCombatStats(),
    counterWindowOpenMs: 0,
    dixieLastAttackMs: -2000,
    wardroneLastCounterMs: -5000,
    bossPhase4Mechanic: null,
    phaseChangeMs: 0,
    phaseChangeColor: "#ffff00",
    friendlyNodeHp: 100,
  };
}

export function getTarget(state: CombatState): Combatant | null {
  if (state.enemies.length === 0) return null;
  return state.enemies[state.targetIndex] ?? null;
}

export function pushLog(state: CombatState, msg: string): void {
  state.log.push(msg);
  if (state.log.length > 6) {
    state.log.shift();
  }
}

export function isAlive(combatant: Combatant): boolean {
  return combatant.hp > 0;
}

export function isStunned(combatant: Combatant): boolean {
  return combatant.statuses.some((s) => s.isStunned);
}

export function isStaggered(combatant: Combatant): boolean {
  return combatant.statuses.some((s) => s.isStaggered);
}

export function consumeStagger(combatant: Combatant): void {
  combatant.statuses = combatant.statuses.filter((s) => !s.isStaggered);
}

export function getAttackBonus(combatant: Combatant): number {
  const buffs = combatant.statuses.reduce((sum, s) => sum + s.attackBonus, 0);
  return buffs + combatant.equipAttackBonus;
}

export function getDefenseBonus(combatant: Combatant): number {
  const buffs = combatant.statuses.reduce((sum, s) => sum + s.defenseBonus, 0);
  return buffs + combatant.equipDefenseBonus;
}

export function getTotalAttack(combatant: Combatant): number {
  return combatant.autoAttackDamage + getAttackBonus(combatant);
}