/** Equipment stat record + its two combinators (refactor 2026-11-24).
 *
 * These lived in `equipment.ts`, which meant `equipment_catalog.ts` and
 * `set_bonus.ts` could not import them without a runtime cycle (equipment.ts
 * imports the default catalog as a value). Both worked around it by
 * re-implementing the same 12-field merge — three copies of it, and two of
 * `addStats`. This module is a leaf, so the cycle is gone and there is one copy.
 *
 * `equipment.ts` still re-exports all three names; nothing else had to move.
 */

/** Aggregate stats a piece of equipment contributes.
 *
 * Mirrors Python `EquipStats` dataclass. `grantsSkillId` is nullable (most
 * gear grants no skill) and `extraEffect` is a free-form tag string.
 */
export interface EquipStats {
  readonly attackBonus: number;
  readonly critBonusPct: number;
  readonly damageBonusPct: number;
  readonly defense: number;
  readonly hpBonus: number;
  readonly shieldBonus: number;
  readonly apBonus: number;
  readonly apRegenBonusPct: number;
  readonly programPower: number;
  readonly iceResistance: number;
  readonly grantsSkillId: string | null;
  readonly extraEffect: string;
}

/** Construct an `EquipStats` record with sensible zero defaults. */
export function makeEquipStats(partial: Partial<EquipStats> = {}): EquipStats {
  return Object.freeze({
    attackBonus: partial.attackBonus ?? 0,
    critBonusPct: partial.critBonusPct ?? 0,
    damageBonusPct: partial.damageBonusPct ?? 0,
    defense: partial.defense ?? 0,
    hpBonus: partial.hpBonus ?? 0,
    shieldBonus: partial.shieldBonus ?? 0,
    apBonus: partial.apBonus ?? 0,
    apRegenBonusPct: partial.apRegenBonusPct ?? 0,
    programPower: partial.programPower ?? 0,
    iceResistance: partial.iceResistance ?? 0,
    grantsSkillId: partial.grantsSkillId ?? null,
    extraEffect: partial.extraEffect ?? "",
  });
}

/** Add two `EquipStats`. Port of Python `_add_stats`.
 *
 * `grantsSkillId` follows the OR-semantics from the Python source
 * (the first non-null id wins). `extraEffect` joins both fields
 * with ", " when both are non-empty.
 */
export function addStats(a: EquipStats, b: EquipStats): EquipStats {
  const effect = [a.extraEffect, b.extraEffect].filter((e) => e.length > 0).join(", ");
  return makeEquipStats({
    attackBonus: a.attackBonus + b.attackBonus,
    critBonusPct: a.critBonusPct + b.critBonusPct,
    damageBonusPct: a.damageBonusPct + b.damageBonusPct,
    defense: a.defense + b.defense,
    hpBonus: a.hpBonus + b.hpBonus,
    shieldBonus: a.shieldBonus + b.shieldBonus,
    apBonus: a.apBonus + b.apBonus,
    apRegenBonusPct: a.apRegenBonusPct + b.apRegenBonusPct,
    programPower: a.programPower + b.programPower,
    iceResistance: a.iceResistance + b.iceResistance,
    grantsSkillId: a.grantsSkillId ?? b.grantsSkillId,
    extraEffect: effect,
  });
}