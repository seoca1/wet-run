/** Equipment Loadout — slot state + equip/unequip mutators.
 *
 * Ports the OOP-style `EquipmentLoadout` from
 * `prototype/src/wet_run/equipment/equipment.py` to TypeScript.
 *
 * Split out from `equipment.ts` to keep the core types file under
 * the 250 LOC ceiling. The loadout mutates in place (matching the
 * Python `equip()` / `unequip()` semantics) so callers can write
 * the obvious imperative code. For a pure-functional alternative,
 * use `equipOn` / `unequipFrom` from this same module.
 */

import {
  EQUIP_SLOTS,
  type EquipSlot,
  type EquipStats,
  type Equipment,
  addStats,
  makeEquipStats,
} from "./equipment.ts";
import { getSetBonus } from "./set_bonus.ts";

/** Player's currently equipped gear. */
export interface EquipmentLoadout {
  readonly equipment: Readonly<Record<EquipSlot, Equipment>>;
  equip(equipment: Equipment): Equipment | null;
  unequip(slot: EquipSlot): Equipment | null;
  get(slot: EquipSlot): Equipment | null;
  allSlotsFilled(): ReadonlyArray<EquipSlot>;
  emptySlots(): ReadonlyArray<EquipSlot>;
  isComplete(): boolean;
  setCounts(): Readonly<Record<string, number>>;
  setBonuses(): ReadonlyArray<EquipStats>;
  totalStats(): EquipStats;
}

/** Result of a `equip` call. The previous occupant + the new loadout. */
export interface EquipResult {
  readonly loadout: EquipmentLoadout;
  readonly previous: Equipment | null;
}

/** Pure equip function — returns a new loadout with the item placed. */
export function equipOn(loadout: EquipmentLoadout, equipment: Equipment): EquipResult {
  const previous = loadout.equipment[equipment.slot] ?? null;
  return {
    previous,
    loadout: makeLoadout({ ...loadout.equipment, [equipment.slot]: equipment }),
  };
}

/** Pure unequip function — returns a new loadout and the removed item. */
export interface UnequipResult {
  readonly loadout: EquipmentLoadout;
  readonly removed: Equipment | null;
}

export function unequipFrom(loadout: EquipmentLoadout, slot: EquipSlot): UnequipResult {
  const removed = loadout.equipment[slot] ?? null;
  if (removed === null) return { loadout, removed: null };
  const next: Record<string, Equipment> = { ...loadout.equipment };
  delete next[slot];
  return { removed, loadout: makeLoadout(next as Record<EquipSlot, Equipment>) };
}

/** Construct a loadout from a slot → equipment map. */
export function makeLoadout(equipment: Readonly<Partial<Record<EquipSlot, Equipment>>> = {}): EquipmentLoadout {
  const map: Record<EquipSlot, Equipment> = {} as Record<EquipSlot, Equipment>;
  for (const slot of EQUIP_SLOTS) {
    const piece = equipment[slot];
    if (piece !== undefined) map[slot] = piece;
  }

  const loadout: EquipmentLoadout = {
    get equipment(): Readonly<Record<EquipSlot, Equipment>> {
      return map;
    },
    equip(item: Equipment): Equipment | null {
      const previous = map[item.slot];
      map[item.slot] = item;
      return previous ?? null;
    },
    unequip(slot: EquipSlot): Equipment | null {
      const removed = map[slot];
      delete map[slot];
      return removed ?? null;
    },
    get(slot: EquipSlot): Equipment | null {
      return map[slot] ?? null;
    },
    allSlotsFilled(): ReadonlyArray<EquipSlot> {
      return Object.freeze(Object.keys(map) as EquipSlot[]);
    },
    emptySlots(): ReadonlyArray<EquipSlot> {
      return Object.freeze(EQUIP_SLOTS.filter((s) => map[s] === undefined));
    },
    isComplete(): boolean {
      return EQUIP_SLOTS.every((s) => map[s] !== undefined);
    },
    setCounts(): Readonly<Record<string, number>> {
      const counts: Record<string, number> = {};
      for (const equip of Object.values(map)) {
        if (equip.setId === null) continue;
        counts[equip.setId] = (counts[equip.setId] ?? 0) + 1;
      }
      return Object.freeze(counts);
    },
    setBonuses(): ReadonlyArray<EquipStats> {
      const counts = this.setCounts();
      const bonuses: EquipStats[] = [];
      for (const [setId, count] of Object.entries(counts)) {
        const bonus = getSetBonus(setId, count);
        if (bonus !== null) bonuses.push(bonus);
      }
      return Object.freeze(bonuses);
    },
    totalStats(): EquipStats {
      let total = makeEquipStats();
      for (const equip of Object.values(map)) {
        total = addStats(total, equip.stats);
      }
      for (const bonus of this.setBonuses()) {
        total = addStats(total, bonus);
      }
      return total;
    },
  };
  return loadout;
}

/** Empty loadout — useful as a starting state for tests. */
export const EMPTY_LOADOUT: EquipmentLoadout = makeLoadout();