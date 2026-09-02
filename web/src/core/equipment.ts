/** Equipment system (cyberpunk gear) — types, catalog, registry, loadout.
 *
 * Ports wet_run/prototype/src/wet_run/equipment/equipment.py to TypeScript.
 * Set bonus + wetware modules live in adjacent files:
 *
 * - set_bonus.ts   — SET_BONUSES, getSetBonus, integration helpers
 * - wetware.ts     — wetware augments + Phase 14 equipment sets
 * - loadout.ts     — EquipmentLoadout + equip/unequip mutators
 *
 * Pure data — no side effects. Tests construct registries via
 * `makeEquipmentRegistry(equipment[])` to keep scenarios deterministic.
 */

import { DEFAULT_EQUIPMENT } from "./equipment_catalog.ts";

/** Body locations for cyberpunk gear.
 *
 * 8 slots total. The Python `EquipSlot` StrEnum serializes to its
 * `value`; we keep the same string identifiers so save data round-trips.
 */
export type EquipSlot =
  | "deck"
  | "headware"
  | "eyeware"
  | "bodysuit"
  | "gloves"
  | "boots"
  | "implant"
  | "trodes";

/** Ordered slot list. Mirrors Python `EquipSlot` enum iteration order. */
export const EQUIP_SLOTS: ReadonlyArray<EquipSlot> = Object.freeze([
  "deck",
  "headware",
  "eyeware",
  "bodysuit",
  "gloves",
  "boots",
  "implant",
  "trodes",
] as const);

/** Type of equipment (material / technology). */
export type EquipCategory =
  | "cybernetic"
  | "software"
  | "bioware"
  | "nanoware"
  | "wetware"
  | "hardware"
  | "icebreaker"
  | "daemon";

/** Quality / rarity tiers. T0 = starting gear, T6 = master-tier finale. */
export type EquipTier = "T0" | "T1" | "T2" | "T3" | "T4" | "T5" | "T6";

/** Stats provided by an equipment piece.
 *
 * Numeric fields default to 0. `grantsSkillId` and `extraEffect`
 * are semantic strings — they describe side effects the renderer
 * or combat engine reads; the port treats them as opaque payloads.
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

/** A piece of cyberpunk gear.
 *
 * Port of Python `Equipment` dataclass (frozen, slots). Fields are
 * `readonly`; everything is structurally immutable so the equipment
 * registry can be safely shared across consumers.
 */
export interface Equipment {
  readonly id: string;
  readonly name: string;
  readonly slot: EquipSlot;
  readonly category: EquipCategory;
  readonly tier: EquipTier;
  readonly stats: EquipStats;
  readonly description: string;
  readonly asciiGlyph: string;
  readonly asciiColor: readonly [number, number, number];
  readonly upgradeSlots: number;
  readonly requiredMaterials: Readonly<Record<string, number>>;
  readonly setId: string | null;
}

/** Build an `Equipment` with default values for the cosmetic / metadata fields. */
export function makeEquipment(
  partial: Pick<Equipment, "id" | "name" | "slot" | "category" | "tier" | "stats" | "description"> & Partial<Equipment>,
): Equipment {
  return Object.freeze({
    id: partial.id,
    name: partial.name,
    slot: partial.slot,
    category: partial.category,
    tier: partial.tier,
    stats: partial.stats,
    description: partial.description,
    asciiGlyph: partial.asciiGlyph ?? "?",
    asciiColor: partial.asciiColor ?? ([200, 200, 200] as const),
    upgradeSlots: partial.upgradeSlots ?? 0,
    requiredMaterials: partial.requiredMaterials ?? {},
    setId: partial.setId ?? null,
  });
}

/** True if this piece has at least one upgrade slot. */
export function isUpgradable(equip: Equipment): boolean {
  return equip.upgradeSlots > 0;
}

/** True if this piece is tier 1 (street) or higher (excludes T0 starter gear). */
export function isT1OrBetter(equip: Equipment): boolean {
  return equip.tier !== "T0";
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

// =============================================================================
// Default catalog import
// =============================================================================
//
// The 18-piece Gibson-inspired catalog lives in equipment_catalog.ts
// (pure data, size-OK). Re-export the array + individual pieces through
// equipment.ts so downstream consumers keep their existing import paths.

export {
  STARTER_DECK,
  STARTER_HEADWARE,
  STREET_DECK,
  MILITECH_EYES,
  CHROME_GLOVES,
  CORPORATE_DECK,
  SUBDERMAL,
  MILITECH_DECK,
  TACTICAL_BODY,
  ARASAKA_DECK,
  KEREZNIKOV,
  GHOST_DECK,
  MASTER_DECK,
  MASTER_BODY,
  ZION_TRODES,
  NANO_HIVE,
  TRODES_NINJA,
  BOOTS_GHOST,
  DEFAULT_EQUIPMENT,
} from "./equipment_catalog.ts";


// =============================================================================
// Equipment Registry
// =============================================================================

/** Lookup table for equipment by id. Port of Python `EquipmentRegistry`. */
export interface EquipmentRegistry {
  readonly all: ReadonlyArray<Equipment>;
  get(equipId: string): Equipment | null;
  bySlot(slot: EquipSlot): ReadonlyArray<Equipment>;
}

/** Build a registry from an explicit equipment array. */
export function makeEquipmentRegistry(equipment: ReadonlyArray<Equipment>): EquipmentRegistry {
  const map: Record<string, Equipment> = {};
  for (const e of equipment) {
    map[e.id] = e;
  }
  const all = Object.freeze(equipment.slice());
  return Object.freeze({
    all,
    get(equipId: string): Equipment | null {
      return map[equipId] ?? null;
    },
    bySlot(slot: EquipSlot): ReadonlyArray<Equipment> {
      return Object.freeze(all.filter((e) => e.slot === slot));
    },
  });
}

/** The default Gibson-inspired equipment registry. */
export const DEFAULT_REGISTRY: EquipmentRegistry = makeEquipmentRegistry(DEFAULT_EQUIPMENT);



// =============================================================================
// Loadout re-export
// =============================================================================
//
// The Loadout interface + mutators live in loadout.ts (keeps this
// file focused on types + registry + factory helpers). Re-exported
// here so existing imports of `makeLoadout`, `EquipmentLoadout`, etc.
// from `./equipment.ts` keep working.

export {
  EMPTY_LOADOUT,
  equipOn,
  makeLoadout,
  unequipFrom,
  type EquipResult,
  type EquipmentLoadout,
  type UnequipResult,
} from "./loadout.ts";

// =============================================================================
// Re-exports — backwards-compat surface for tests + downstream callers.
// The implementation lives in the adjacent modules below.
// =============================================================================

export {
  SET_BONUSES,
  getActiveSetIds,
  getAllSetBonuses,
  getBestSetBonusFor,
  getSetBonus,
  getSetBonusDefinitions,
  getSetCount,
  applySetBonusesToStats,
  calculateSetBonus,
  type SetBonusSummary,
  type SetBonusesByThreshold,
} from "./set_bonus.ts";

export {
  EMPTY_STACKED_WETWARE,
  MAX_AP_REGEN,
  WETWARE_CAPS,
  getNewStatAugments,
  isTier3,
  makeWetwareRegistry,
  stackWetware,
  validateStacking,
  type RawWetwareAugment,
  type StackedWetware,
  type WetwareAugment,
  type WetwareRegistry,
} from "./wetware.ts";

export {
  makeEquipmentSetsFromData,
  type EquipmentSetV2,
  type RawEquipmentSet,
  type RawSetBonus,
  type SetBonusV2,
} from "./equipment_sets.ts";
