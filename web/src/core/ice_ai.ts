/**
 * ICE AI system — aggression tiers + personality archetypes + skill selection.
 *
 * TypeScript port of Python:
 *   - combat/depth/aggression.py (ADR-0148)
 *   - combat/depth/personality.py (ADR-0161)
 *
 * Two orthogonal dimensions:
 *   1. **Aggression tier** — per-tick probability the ICE casts a skill
 *      instead of auto-attacking (passive/standard/aggressive/boss).
 *   2. **Personality archetype** — modifies behavior: skill preference,
 *      crit bonus, alarm speed, defensive threshold, ally targeting
 *      (aggressive/defensive/stealth/support).
 *
 * The personality `selectSkillByPersonality` IS the production hot path:
 * `state_actions_combat.ts` calls it to pick the enemy's skill each tick,
 * gated by `enemyShouldUseSkill`. `chooseSkill` (uniform random) remains
 * exported as the Python-prototype port of `Combatant.choose_skill()`.
 */

import type {
  AggressionTier,
  Combatant,
  PersonalityArchetype,
  Skill,
  SkillEffectKind,
} from "./combat_models.ts";

// ============================================================================
//  Aggression tiers — per-tick skill-use probability
// ============================================================================

/** Per-tick probability of ICE choosing to cast a skill (ADR-0148). */
export const AGGRESSION_PROBABILITY: Readonly<Record<AggressionTier, number>> =
  {
    passive: 0.05,
    standard: 0.15,
    aggressive: 0.35,
    boss: 0.5,
  } as const;

/** Valid aggression values for coercion guards. */
const VALID_AGGRESSION: ReadonlySet<string> = new Set<string>([
  "passive",
  "standard",
  "aggressive",
  "boss",
]);

/** Valid personality values for coercion guards. */
const VALID_PERSONALITY: ReadonlySet<string> = new Set<string>([
  "aggressive",
  "defensive",
  "stealth",
  "support",
]);

/**
 * Safe coercion: returns the aggression tier if valid, else "standard".
 * Mirrors Python `_combatant_aggression()` guard.
 */
export function coerceAggression(value: unknown): AggressionTier {
  if (typeof value === "string" && VALID_AGGRESSION.has(value)) {
    return value as AggressionTier;
  }
  return "standard";
}

/**
 * Safe coercion: returns the personality if valid, else "aggressive".
 * Mirrors Python `_combatant_personality()` guard.
 */
export function coercePersonality(value: unknown): PersonalityArchetype {
  if (typeof value === "string" && VALID_PERSONALITY.has(value)) {
    return value as PersonalityArchetype;
  }
  return "aggressive";
}

/**
 * Minimal surface for skill-use decisions. Implemented by both the full
 * `Combatant` engine type and the lightweight `Ice` roster type, so the
 * boss-phase tick loop can call these helpers without type suppression.
 */
export interface SkillUser {
  readonly hp: number;
  readonly aggression?: unknown;
  readonly personality?: unknown;
}

/** Minimal skill surface for personality matching (id/effect/damage). */
export interface UsableSkill {
  readonly id: string;
  readonly effect: string;
  readonly damage: number;
}

/**
 * Gate: should this ICE attempt to use a skill this tick?
 *
 * Returns false if the combatant has no skills or is dead.
 * Otherwise rolls against the aggression tier's probability.
 * Called every AUTO_ATTACK_INTERVAL_MS (2000ms) for each alive enemy.
 */
export function enemyShouldUseSkill(
  combatant: SkillUser & { readonly skills?: ReadonlyArray<unknown> },
  rng: () => number,
): boolean {
  if ((combatant.skills ?? []).length === 0 || combatant.hp <= 0) {
    return false;
  }
  const tier = coerceAggression(combatant.aggression);
  const prob = AGGRESSION_PROBABILITY[tier] ?? AGGRESSION_PROBABILITY.standard;
  return rng() < prob;
}

// ============================================================================
//  Skill selection — uniform random (production)
// ============================================================================

/**
 * Pick a skill at uniform random from the combatant's equipped skills.
 * Mirrors Python `Combatant.choose_skill()`.
 *
 * @returns A randomly selected skill, or null if no skills are equipped.
 */
export function chooseSkill(
  combatant: Combatant,
  rng: () => number,
): Skill | null {
  if (combatant.skills.length === 0) {
    return null;
  }
  const idx = Math.floor(rng() * combatant.skills.length);
  return combatant.skills[idx] ?? null;
}

// ============================================================================
//  Personality system — skill preference + stat modifiers
// ============================================================================

/**
 * Skill preference table per personality archetype.
 * Priority-ordered list of SkillEffectKind — the first matching effect
 * wins. Mirrors Python `PERSONALITY_SKILL_PREFERENCE`.
 *
 * The table is **deliberately not trimmed** of its non-damaging entries
 * (`shield`/`heal`/`regen`/`buff`/`detect`). Those entries are
 * forward-looking design intent: the combat path cannot fire a
 * non-damaging skill today, but if non-damaging effects are ever
 * implemented (ADR-0219 Option A) they become meaningful immediately.
 * Filtering at selection time (see `selectSkillByPersonality`) keeps the
 * table and the code honest without discarding that intent; trimming the
 * table would throw the intent away and collapse `defensive`/`support`
 * into "a weaker aggressive".
 */
export const PERSONALITY_SKILL_PREFERENCE: Readonly<
  Record<PersonalityArchetype, ReadonlyArray<SkillEffectKind>>
> = {
  aggressive: ["heavy_attack", "pierce", "multi_hit", "attack", "lifesteal"],
  defensive: ["shield", "heal", "regen", "buff", "attack"],
  stealth: ["dot", "poison", "debuff", "silence", "slow"],
  support: ["heal", "regen", "shield", "debuff", "detect"],
} as const;

/**
 * Personality-based skill selection (production hot path).
 *
 * Matches the combatant's personality preference against available skills'
 * effects. Returns the first skill whose effect matches a preference.
 *
 * **Contract (ADR-0219 Option B — consistency-only):** the preference match
 * is restricted to skills the combat path can actually fire. The combat
 * path only fires a skill when `damage > 0`
 * (`state_actions_combat.ts`: `selectedSkill.damage > 0`); anything else
 * falls through to a plain auto-attack. So the candidate pool is computed
 * once, up front:
 *
 *   - if any skill is usable (`damage > 0`), the pool is the usable skills
 *     and both the preference loop and the fallback draw from it — the
 *     function therefore always returns a skill the combat path can fire;
 *   - if no skill is usable, the pool is every available skill and behavior
 *     is unchanged from before (the combat path auto-attacks anyway);
 *   - an empty skill list yields `null`.
 *
 * @returns The selected skill, or null when `availableSkills` is empty.
 */
export function selectSkillByPersonality<S extends UsableSkill>(
  combatant: SkillUser,
  availableSkills: ReadonlyArray<S>,
): S | null {
  if (availableSkills.length === 0) {
    return null;
  }
  const personality = coercePersonality(combatant.personality);
  const prefs = PERSONALITY_SKILL_PREFERENCE[personality];

  // Candidate pool, computed once: prefer skills the combat path can fire.
  // When nothing is usable the pool is every available skill, so the
  // no-usable-skill case behaves exactly as it did before.
  const usable = availableSkills.filter((skill) => skill.damage > 0);
  const pool = usable.length > 0 ? usable : availableSkills;

  // Build effect → first matching skill index for O(n*m) but small n
  for (const effect of prefs) {
    for (let i = 0; i < pool.length; i++) {
      if (pool[i].effect === effect) {
        return pool[i];
      }
    }
  }

  // Fallback: first entry of the pool. With a usable skill present this is
  // the first *usable* skill (ADR-0218 behavior); with none usable it is the
  // first available skill, which the combat path will turn into an
  // auto-attack — unchanged from before.
  return pool[0] ?? null;
}

// ============================================================================
//  Personality stat modifiers
// ============================================================================

/** DEFENSIVE personality HP threshold for defensive behavior (50%). */
export const DEFENSIVE_HP_THRESHOLD = 0.5;

/** AGGRESSIVE personality bonus to crit chance (+5%). */
export const AGGRESSIVE_CRIT_BONUS = 0.05;

/** STEALTH personality alarm speed multiplier (50% slower). */
export const STEALTH_ALARM_MULTIPLIER = 0.5;

/**
 * Should this ICE use defensive behavior? True when personality is
 * DEFENSIVE and HP is below 50% of max.
 */
export function shouldDefensiveAct(combatant: Combatant): boolean {
  const personality = coercePersonality(combatant.personality);
  if (personality !== "defensive") return false;
  if (combatant.maxHp <= 0) return false;
  return combatant.hp / combatant.maxHp < DEFENSIVE_HP_THRESHOLD;
}

/**
 * Returns the alarm speed multiplier for this ICE's personality.
 * STEALTH personality halves alarm tick rate; all others return 1.0.
 */
export function getAlarmMultiplier(combatant: Combatant): number {
  const personality = coercePersonality(combatant.personality);
  return personality === "stealth" ? STEALTH_ALARM_MULTIPLIER : 1.0;
}

/**
 * Returns the crit chance bonus for this ICE's personality.
 * AGGRESSIVE personality adds +5% crit chance; all others return 0.
 */
export function getCritBonus(combatant: Combatant): number {
  const personality = coercePersonality(combatant.personality);
  return personality === "aggressive" ? AGGRESSIVE_CRIT_BONUS : 0;
}

/**
 * Should this ICE target an ally? True when personality is SUPPORT
 * and a wounded ally (HP < 70% of max) exists in the combat state.
 * Used for heal/buff targeting in multi-enemy combat.
 */
export function shouldTargetAlly(
  combatant: Combatant,
  allies: ReadonlyArray<Combatant>,
): boolean {
  const personality = coercePersonality(combatant.personality);
  if (personality !== "support") return false;

  return allies.some((ally) => {
    if (ally.id === combatant.id) return false; // don't target self
    if (ally.hp <= 0) return false;
    if (ally.maxHp <= 0) return false;
    return ally.hp / ally.maxHp < 0.7;
  });
}
