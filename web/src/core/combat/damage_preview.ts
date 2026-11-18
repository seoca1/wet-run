/** What a program will actually take off the ICE — the damage AFTER armor.
 *
 * The measurement that motivated this (ADR-0320): the ICE's armor is a flat
 * subtraction (`combat_engine.ts`), and the card's damage is `tier * 5`, so the
 * same card is worth wildly different amounts depending on what it is hitting:
 *
 *   strike (t1)      armor 0 -> 4-5     armor 9 -> 1
 *   exploit (t3)     armor 9 -> 8-13    (ignores half the armor)
 *   goliath (t3)     armor 9 -> 3-8
 *   kraken (t5)      armor 9 -> 11-20   combo 5 -> 31-50
 *   unique (t6)      armor 9 -> 15-26
 *
 * None of that was on screen. The player saw `COST +1` and `TARGET ICE`, played
 * the cheap card, and learned nothing from the 1 damage it did — so the deck's
 * growth was invisible and armor was a rule nobody could see.
 *
 * This mirrors the reducer's deterministic path (`state_actions_programs.ts`)
 * and returns a RANGE, because the roll is real: `calculateDamage` multiplies by
 * a 0.8-1.2 variance. Crit is deliberately NOT in the range — it is a separate
 * event with its own feedback, and folding a 15% spike into the number would
 * make the common case look like a lie.
 *
 * ADR-0251 rule 5 forbids a KILL prediction; a damage range is not one (it says
 * how hard the card hits, not that it finishes the fight).
 */
import type { GameState, Ice, Program } from "../types";
import {
  COMBO_BONUSES,
  DAMAGE_VARIANCE_MAX,
  DAMAGE_VARIANCE_MIN,
  ROLE_SYNERGY_BONUSES,
} from "./combat_engine";
import { programEffect } from "./program_effects";

/** The damage a card will do to one ICE, as the range the roll can produce. */
export interface EffectiveDamage {
  /** Lowest roll (variance floor), after armor. */
  readonly min: number;
  /** Highest roll (variance ceiling), after armor. */
  readonly max: number;
  /** The ICE's own armor. */
  readonly armor: number;
  /** The armor that actually applied, after pierce / armor_ignore. */
  readonly effectiveArmor: number;
  /** True when armor has reduced the card to the `1` floor — a wasted play. */
  readonly blocked: boolean;
}

/** The status/equipment bonuses the reducer reads for a player attack. */
function playerBonuses(state: GameState): {
  readonly attackBonus: number;
  readonly vulnerabilityPct: number;
} {
  const powered = state.statusEffects
    .filter((e) => e.kind === "powered" && e.target === "player")
    .reduce((sum, e) => sum + (e.attackBonus ?? 0), 0);
  const vulnerable = state.statusEffects
    .filter((e) => e.kind === "vulnerable" && e.target === "ice")
    .reduce((sum, e) => sum + e.magnitude, 0);
  const equip = state.equipmentLoadout.totalStats();
  return {
    attackBonus: powered + equip.attackBonus,
    vulnerabilityPct: vulnerable + equip.damageBonusPct,
  };
}

/** The armor a card actually has to get through (ADR-0255 / ADR-0277).
 *
 * `backdoor` removes armor POINTS; `exploit` keeps a SHARE of it. Same order as
 * the reducer, so the preview cannot disagree with the play. */
function effectiveArmorAgainst(program: Program, ice: Ice): number {
  const effect = programEffect(program);
  const piercePoints = effect.kind === "pierce" ? effect.amount : 0;
  const armorKeptPct = effect.kind === "armor_ignore" ? 100 - effect.amount : 100;
  const armor = ice.armor ?? 0;
  return Math.floor((Math.max(0, armor - piercePoints) * armorKeptPct) / 100);
}

/**
 * The damage range for one program against one ICE.
 *
 * `combo` defaults to the combo the play WOULD make (the reducer increments
 * before it multiplies), so the number shown is the number the next play gets.
 */
export function effectiveDamageFor(
  state: Pick<
    GameState,
    "playerCombo" | "statusEffects" | "equipmentLoadout"
  >,
  program: Program,
  ice: Ice,
): EffectiveDamage {
  const armor = ice.armor ?? 0;
  const effectiveArmor = effectiveArmorAgainst(program, ice);
  const { attackBonus, vulnerabilityPct } = playerBonuses(
    state as GameState,
  );
  const comboMult = COMBO_BONUSES[state.playerCombo + 1] ?? 1.0;
  const synergyMult = ROLE_SYNERGY_BONUSES[0] ?? 1.0;
  const base = program.tier * 5;

  const roll = (variance: number): number => {
    let dmg = base * variance;
    dmg *= synergyMult;
    dmg *= comboMult;
    dmg = Math.floor(dmg * (1 + vulnerabilityPct / 100));
    dmg += attackBonus;
    dmg = Math.max(0, dmg - effectiveArmor);
    // `calculateDamage` floors at 1, so armor can never make a play a no-op.
    return Math.max(1, Math.floor(dmg));
  };

  const min = roll(DAMAGE_VARIANCE_MIN);
  const max = roll(DAMAGE_VARIANCE_MAX);
  return {
    min,
    max,
    armor,
    effectiveArmor,
    // The floor is 1, so "the armor ate it" is exactly "the best roll is 1".
    blocked: max <= 1,
  };
}

/** The damage column for a hand row: `7`, `4-6`, or `1`. */
export function formatDamageRange(d: Pick<EffectiveDamage, "min" | "max">): string {
  return d.min === d.max ? `${d.min}` : `${d.min}-${d.max}`;
}
