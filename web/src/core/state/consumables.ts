/** Consumables the runner can use (ADR-0330).
 *
 * The proposal's material sheet named `maas_neuropozyne_dose` a "consumable
 * candidate" and left its numbers to the harness. This is the mechanic: a
 * material the run carries can be spent at the loot stop for a one-off effect.
 *
 * The first one grants a player SHIELD POOL — the absorbing pool `applyPrep`
 * already hands out for its "ice" option — so a dose buys survivability for the
 * next fight. It is deliberately NOT a heal: the repair slot already owns HP,
 * and a consumable that duplicated it would just be a second repair.
 *
 * Numbers are placeholders, measured like every other balance value.
 */
import type { Inventory } from "../types";

export interface Consumable {
  readonly id: string;
  readonly name: string;
  /** Shield pool granted, as a percent of max HP. */
  readonly shieldPct: number;
}

export const CONSUMABLES: ReadonlyArray<Consumable> = Object.freeze([
  Object.freeze({
    id: "maas_neuropozyne_dose",
    name: "Maas Neuropozyne Dose",
    shieldPct: 25,
  }),
]);

/** The consumable with this material id, or null. */
export function consumableFor(id: string): Consumable | null {
  return CONSUMABLES.find((c) => c.id === id) ?? null;
}

/** The first consumable the run is carrying, or null. */
export function carriedConsumable(
  materials: Inventory["materials"],
): Consumable | null {
  for (const c of CONSUMABLES) {
    if ((materials[c.id] ?? 0) > 0) return c;
  }
  return null;
}
