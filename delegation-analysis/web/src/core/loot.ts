/**
 * Loot drop system — rolls against ICE loot tables when enemies are defeated.
 *
 * Each ICE type in ice_types.json has a loot_table array with items and drop chances.
 * When an ICE is defeated, we roll against its loot_table to determine drops.
 */

/** Single loot table entry from ice_types.json. */
export interface LootEntry {
  readonly item: string;
  readonly chance: number; // 0.0-1.0
  readonly quantity: number;
}

/** Result of a loot roll. */
export interface LootDrop {
  readonly item: string;
  readonly quantity: number;
}

/**
 * Roll against a loot table and return dropped items.
 *
 * @param lootTable - Array of loot entries from ice_types.json
 * @param rng - Random number generator (0-1)
 * @returns Array of items that dropped
 */
export function rollLoot(
  lootTable: ReadonlyArray<LootEntry>,
  rng: () => number = Math.random,
): LootDrop[] {
  const drops: LootDrop[] = [];
  for (const entry of lootTable) {
    if (rng() < entry.chance) {
      drops.push({ item: entry.item, quantity: entry.quantity });
    }
  }
  return drops;
}

/**
 * Get loot table for an ICE type from the data.
 *
 * @param iceType - ICE type key (e.g., "standard", "watchdog")
 * @param iceTypesData - The full ice_types.json data
 * @returns Loot table array, or empty array if not found
 */
export function getLootTable(
  iceType: string,
  iceTypesData: Record<string, { loot_table?: LootEntry[] }>,
): LootEntry[] {
  return iceTypesData[iceType]?.loot_table ?? [];
}
