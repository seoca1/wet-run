/** Set Bonuses — equipment set bonus lookup + integration helpers.
 *
 * Ports wet_run/prototype/src/wet_run/equipment/set_bonus_integration.py
 * to TypeScript. Composes with `EquipmentLoadout` from equipment.ts:
 * the loadout owns its slot state, this module provides aggregation.
 */

import type { EquipStats } from "./equip_stats";
import { addStats, makeEquipStats } from "./equip_stats";

/** Map of set_id → { threshold → bonus stats }. */
export type SetBonusesByThreshold = Readonly<Record<number, EquipStats>>;


/** Direct port of Python `SET_BONUSES`. */
export const SET_BONUSES: Readonly<Record<string, SetBonusesByThreshold>> = Object.freeze({
  ono_sendai: Object.freeze({
    2: makeEquipStats({ critBonusPct: 1, extraEffect: "Ono-Sendai resonance (2pc): deck runs cooler" }),
    3: makeEquipStats({
      programPower: 1,
      apRegenBonusPct: 10,
      extraEffect: "Ono-Sendai sync (3pc): jack in 1 turn faster",
    }),
  }),
  militech: Object.freeze({
    2: makeEquipStats({ critBonusPct: 1, extraEffect: "Militech targeting (2pc): +hit chance" }),
    3: makeEquipStats({ critBonusPct: 1, extraEffect: "Militech apex (3pc): sharper targeting" }),
  }),
  arasaka: Object.freeze({
    2: makeEquipStats({
      defense: 1,
      iceResistance: 1,
      extraEffect: "Arasaka wards (2pc): corporate-grade shields",
    }),
    3: makeEquipStats({
      defense: 1,
      hpBonus: 1,
      iceResistance: 1,
      extraEffect: "Arasaka Onikiri (3pc): corporate-grade plating",
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

import type { EquipmentLoadout } from "./equipment";


const zeroStats: EquipStats = makeEquipStats({});

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
    if (bonus !== null) total = addStats(total, bonus);
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
    result = addStats(result, bonus);
  }
  return result;
}
