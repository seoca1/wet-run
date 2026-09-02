/** Set Bonuses — equipment set bonus lookup + integration helpers.
 *
 * Ports wet_run/prototype/src/wet_run/equipment/set_bonus_integration.py
 * to TypeScript. Composes with `EquipmentLoadout` from equipment.ts:
 * the loadout owns its slot state, this module provides aggregation.
 */

import { type EquipStats } from "./equipment.ts";

/** Map of set_id → { threshold → bonus stats }. */
export type SetBonusesByThreshold = Readonly<Record<number, EquipStats>>;

function makeStats(p: {
  attackBonus?: number;
  critBonusPct?: number;
  damageBonusPct?: number;
  defense?: number;
  hpBonus?: number;
  shieldBonus?: number;
  apBonus?: number;
  apRegenBonusPct?: number;
  programPower?: number;
  iceResistance?: number;
  grantsSkillId?: string | null;
  extraEffect?: string;
}): EquipStats {
  return Object.freeze({
    attackBonus: p.attackBonus ?? 0,
    critBonusPct: p.critBonusPct ?? 0,
    damageBonusPct: p.damageBonusPct ?? 0,
    defense: p.defense ?? 0,
    hpBonus: p.hpBonus ?? 0,
    shieldBonus: p.shieldBonus ?? 0,
    apBonus: p.apBonus ?? 0,
    apRegenBonusPct: p.apRegenBonusPct ?? 0,
    programPower: p.programPower ?? 0,
    iceResistance: p.iceResistance ?? 0,
    grantsSkillId: p.grantsSkillId ?? null,
    extraEffect: p.extraEffect ?? "",
  });
}

/** Direct port of Python `SET_BONUSES`. */
export const SET_BONUSES: Readonly<Record<string, SetBonusesByThreshold>> = Object.freeze({
  ono_sendai: Object.freeze({
    2: makeStats({
      programPower: 10,
      critBonusPct: 5,
      extraEffect: "Ono-Sendai resonance (2pc): deck runs cooler",
    }),
    3: makeStats({
      programPower: 25,
      apRegenBonusPct: 10,
      extraEffect: "Ono-Sendai sync (3pc): jack in 1 turn faster",
    }),
  }),
  militech: Object.freeze({
    2: makeStats({
      attackBonus: 5,
      critBonusPct: 10,
      extraEffect: "Militech targeting (2pc): +hit chance",
    }),
    3: makeStats({
      attackBonus: 15,
      critBonusPct: 25,
      shieldBonus: 2,
      extraEffect: "Militech apex (3pc): +25% crit, +shield regen",
    }),
  }),
  arasaka: Object.freeze({
    2: makeStats({
      defense: 8,
      iceResistance: 15,
      extraEffect: "Arasaka wards (2pc): corporate-grade shields",
    }),
    3: makeStats({
      defense: 20,
      hpBonus: 30,
      iceResistance: 30,
      extraEffect: "Arasaka Onikiri (3pc): +30 hp, ICE deals 30% less damage",
    }),
  }),
});

/** Return the highest applicable set bonus for `piecesEquipped` items. */
export function getSetBonus(setId: string | null, piecesEquipped: number): EquipStats | null {
  if (setId === null) return null;
  const thresholds = SET_BONUSES[setId];
  if (thresholds === undefined) return null;
  const sorted = Object.keys(thresholds)
    .map((k) => Number(k))
    .filter((n) => Number.isFinite(n))
    .sort((a, b) => b - a);
  for (const threshold of sorted) {
    if (piecesEquipped >= threshold) {
      return thresholds[threshold] ?? null;
    }
  }
  return null;
}

/** Read-only view of `SET_BONUSES`. */
export function getSetBonusDefinitions(): Readonly<Record<string, SetBonusesByThreshold>> {
  return SET_BONUSES;
}

// =============================================================================
// Set Bonus Integration — composes with EquipmentLoadout
// =============================================================================

import type { EquipmentLoadout } from "./equipment.ts";

function addStatsLocal(a: EquipStats, b: EquipStats): EquipStats {
  const effect = [a.extraEffect, b.extraEffect].filter((e) => e.length > 0).join(", ");
  return Object.freeze({
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

const zeroStats: EquipStats = makeStats({});

/** Summary of active set bonuses on a loadout. */
export interface SetBonusSummary {
  readonly activeSetIds: ReadonlyArray<string>;
  readonly setCount: Readonly<Record<string, number>>;
  readonly totalBonus: EquipStats;
}

export function calculateSetBonus(loadout: EquipmentLoadout): SetBonusSummary {
  const counts = loadout.setCounts();
  let total: EquipStats = zeroStats;
  for (const [setId, count] of Object.entries(counts)) {
    const bonus = getSetBonus(setId, count);
    if (bonus !== null) total = addStatsLocal(total, bonus);
  }
  return Object.freeze({
    activeSetIds: Object.freeze(Object.keys(counts)),
    setCount: Object.freeze(counts),
    totalBonus: total,
  });
}

export function getActiveSetIds(loadout: EquipmentLoadout): ReadonlyArray<string> {
  return Object.freeze(Object.keys(loadout.setCounts()));
}

export function getSetCount(loadout: EquipmentLoadout, setId: string): number {
  return loadout.setCounts()[setId] ?? 0;
}

export function getBestSetBonusFor(loadout: EquipmentLoadout, setId: string): EquipStats | null {
  const count = getSetCount(loadout, setId);
  if (count === 0) return null;
  return getSetBonus(setId, count);
}

export function getAllSetBonuses(loadout: EquipmentLoadout): ReadonlyArray<EquipStats> {
  return loadout.setBonuses();
}

/** Apply all active set bonuses to a base stat block. */
export function applySetBonusesToStats(base: EquipStats, loadout: EquipmentLoadout): EquipStats {
  let result = base;
  for (const bonus of loadout.setBonuses()) {
    result = addStatsLocal(result, bonus);
  }
  return result;
}