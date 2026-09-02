/** Wetware augments — stacking logic for cybernetic bio-enhancements.
 *
 * Ports wet_run/prototype/src/wet_run/equipment/wetware_stacking.py +
 * the Phase 14 `data/equipment/sets.json` schema to TypeScript.
 *
 * Two related sub-systems share this module:
 *
 * 1. **Wetware stacking** — additive bonuses from multiple augments, with
 *    per-stat caps. Unknown augment ids are silently skipped.
 *
 * 2. **EquipmentSetV2** — the Phase 14 schema (ghost_set / architect_set)
 *    with set_bonus_2_piece / set_bonus_3_piece / set_bonus_4_piece.
 *    Coexists with the SET_BONUSES table in set_bonus.ts (which uses
 *    a different bonus shape).
 */

// =============================================================================
// Wetware Stacking (ADR-0193)
// =============================================================================

/** Result of stacking multiple wetware augments. */
export interface StackedWetware {
  readonly apRegen: number;
  readonly critChance: number;
  readonly critDamage: number;
  readonly dodge: number;
  readonly hpBonus: number;
  readonly healing: number;
  readonly shield: number;
  readonly speed: number;
  readonly mana: number;
  readonly armor: number;
  readonly focus: number;
  readonly augmentCount: number;
}

/** Per-stat caps applied during stacking. */
export const WETWARE_CAPS: Readonly<Record<string, number>> = Object.freeze({
  apRegen: 1.0,
  critChance: 0.95,
  critDamage: 1.0,
  dodge: 0.95,
  healing: 1.0,
  shield: 0.95,
  speed: 1.0,
  armor: 1.0,
  focus: 1.0,
});

/** Zero-initialized stacked wetware. */
export const EMPTY_STACKED_WETWARE: StackedWetware = Object.freeze({
  apRegen: 0,
  critChance: 0,
  critDamage: 0,
  dodge: 0,
  hpBonus: 0,
  healing: 0,
  shield: 0,
  speed: 0,
  mana: 0,
  armor: 0,
  focus: 0,
  augmentCount: 0,
});

/** JSON shape of one wetware augment in `data/equipment/wetware.json`. */
export interface RawWetwareAugment {
  readonly id?: string;
  readonly name?: string;
  readonly tier?: number;
  readonly type?: string;
  readonly description?: string;
  readonly ap_regen_bonus?: number;
  readonly crit_chance_bonus?: number;
  readonly crit_damage_bonus?: number;
  readonly dodge_bonus?: number;
  readonly hp_bonus?: number;
  readonly heal_bonus?: number;
  readonly shield_bonus?: number;
  readonly speed_bonus?: number;
  readonly mana_bonus?: number;
  readonly armor_bonus?: number;
  readonly focus_bonus?: number;
  readonly is_new_stat?: boolean;
  readonly associated_stats?: ReadonlyArray<string>;
}

/** Internal wetware augment record (after JSON normalization). */
export interface WetwareAugment {
  readonly id: string;
  readonly name: string;
  readonly tier: number;
  readonly type: string;
  readonly description: string;
  readonly isNewStat: boolean;
  readonly apRegenBonus: number;
  readonly critChanceBonus: number;
  readonly critDamageBonus: number;
  readonly dodgeBonus: number;
  readonly hpBonus: number;
  readonly healBonus: number;
  readonly shieldBonus: number;
  readonly speedBonus: number;
  readonly manaBonus: number;
  readonly armorBonus: number;
  readonly focusBonus: number;
}

/** Augment registry. Lookups are O(1) via the internal map. */
export interface WetwareRegistry {
  readonly all: ReadonlyArray<WetwareAugment>;
  readonly byId: Readonly<Record<string, WetwareAugment>>;
  get(augmentId: string): WetwareAugment | null;
  byType(augmentType: string): ReadonlyArray<WetwareAugment>;
  /** Count how many of the listed ids are tier 3. Unknown ids are 0. */
  countTier3(augmentIds: ReadonlyArray<string>): number;
}

/** Build a registry from raw JSON parsed from `wetware.json`. */
export function makeWetwareRegistry(raw: Readonly<Record<string, unknown>>): WetwareRegistry {
  const byId: Record<string, WetwareAugment> = {};
  const all: WetwareAugment[] = [];
  for (const [key, value] of Object.entries(raw)) {
    if (key.startsWith("_")) continue;
    if (value === null || typeof value !== "object" || Array.isArray(value)) continue;
    const r = value as RawWetwareAugment;
    const id = typeof r.id === "string" ? r.id : key;
    if (id.length === 0) continue;
    const aug: WetwareAugment = Object.freeze({
      id,
      name: typeof r.name === "string" ? r.name : id,
      tier: Number.isFinite(r.tier) ? Math.trunc(r.tier as number) : 0,
      type: typeof r.type === "string" ? r.type : "",
      description: typeof r.description === "string" ? r.description : "",
      isNewStat: r.is_new_stat === true,
      apRegenBonus: numOrZero(r.ap_regen_bonus),
      critChanceBonus: numOrZero(r.crit_chance_bonus),
      critDamageBonus: numOrZero(r.crit_damage_bonus),
      dodgeBonus: numOrZero(r.dodge_bonus),
      hpBonus: numOrZero(r.hp_bonus),
      healBonus: numOrZero(r.heal_bonus),
      shieldBonus: numOrZero(r.shield_bonus),
      speedBonus: numOrZero(r.speed_bonus),
      manaBonus: numOrZero(r.mana_bonus),
      armorBonus: numOrZero(r.armor_bonus),
      focusBonus: numOrZero(r.focus_bonus),
    });
    byId[id] = aug;
    all.push(aug);
  }
  const frozenAll = Object.freeze(all);
  const frozenMap = Object.freeze({ ...byId });
  return Object.freeze({
    all: frozenAll,
    byId: frozenMap,
    get(augmentId: string): WetwareAugment | null {
      return frozenMap[augmentId] ?? null;
    },
    byType(augmentType: string): ReadonlyArray<WetwareAugment> {
      return Object.freeze(frozenAll.filter((a) => a.type === augmentType));
    },
    countTier3(augmentIds: ReadonlyArray<string>): number {
      let n = 0;
      for (const id of augmentIds) {
        const aug = frozenMap[id];
        if (aug !== undefined && aug.tier === 3) n += 1;
      }
      return n;
    },
  });
}

/** Stack wetware augments into a single `StackedWetware` summary. */
export function stackWetware(
  registry: WetwareRegistry,
  augmentIds: ReadonlyArray<string>,
): StackedWetware {
  let stacked: StackedWetware = { ...EMPTY_STACKED_WETWARE, augmentCount: augmentIds.length };

  for (const id of augmentIds) {
    const aug = registry.byId[id];
    if (aug === undefined) continue;
    stacked = {
      apRegen: cap(stacked.apRegen + aug.apRegenBonus, WETWARE_CAPS.apRegen),
      critChance: cap(stacked.critChance + aug.critChanceBonus, WETWARE_CAPS.critChance),
      critDamage: cap(stacked.critDamage + aug.critDamageBonus, WETWARE_CAPS.critDamage),
      dodge: cap(stacked.dodge + aug.dodgeBonus, WETWARE_CAPS.dodge),
      hpBonus: stacked.hpBonus + Math.trunc(aug.hpBonus),
      healing: cap(stacked.healing + aug.healBonus, WETWARE_CAPS.healing),
      shield: cap(stacked.shield + aug.shieldBonus, WETWARE_CAPS.shield),
      speed: cap(stacked.speed + aug.speedBonus, WETWARE_CAPS.speed),
      mana: stacked.mana + Math.trunc(aug.manaBonus),
      armor: cap(stacked.armor + aug.armorBonus, WETWARE_CAPS.armor),
      focus: cap(stacked.focus + aug.focusBonus, WETWARE_CAPS.focus),
      augmentCount: stacked.augmentCount,
    };
  }
  return Object.freeze(stacked);
}

/** Augments that introduce new stats (mana, armor, focus). */
export function getNewStatAugments(registry: WetwareRegistry): ReadonlyArray<WetwareAugment> {
  return Object.freeze(registry.all.filter((a) => a.isNewStat));
}

/** Maximum AP regen if all three ap_regen augments are stacked. */
export const MAX_AP_REGEN = 0.5;

/** True when every id resolves to an augment in the registry. */
export function validateStacking(
  registry: WetwareRegistry,
  augmentIds: ReadonlyArray<string>,
): boolean {
  for (const id of augmentIds) {
    if (registry.byId[id] === undefined) return false;
  }
  return true;
}

/** True when an augment id is registered AND tier 3. */
export function isTier3(registry: WetwareRegistry, augmentId: string): boolean {
  const aug = registry.byId[augmentId];
  return aug !== undefined && aug.tier === 3;
}

function cap(value: number, maxValue: number): number {
  return Math.min(value, maxValue);
}

function numOrZero(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

// =============================================================================
// Re-export Sets V2 from the dedicated module.
// =============================================================================

export {
  makeEquipmentSetsFromData,
  type EquipmentSetV2,
  type RawEquipmentSet,
  type RawSetBonus,
  type SetBonusV2,
} from "./equipment_sets.ts";
