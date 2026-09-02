/** Equipment Sets V2 — Phase 14 set schema (ADR-0193).
 *
 * Ports `data/equipment/sets.json` to TypeScript. The Python prototype
 * uses a different bonus schema (`set_bonus_2_piece`, `_3_piece`,
 * `_4_piece`) than the equipment.py set bonuses. This module keeps
 * that schema distinct (`SetBonusV2`) so both can coexist with the
 * SET_BONUSES table in set_bonus.ts.
 *
 * Split from wetware.ts to keep each file under the 250 LOC ceiling.
 */

/** Set bonus definition for the Phase-14 set schema. */
export interface SetBonusV2 {
  readonly name: string;
  readonly type: string;
  readonly description: string;
  readonly fields: Readonly<Record<string, number>>;
}

/** A Phase-14 equipment set (ghost_set / architect_set). */
export interface EquipmentSetV2 {
  readonly setId: string;
  readonly setName: string;
  readonly theme: string;
  readonly description: string;
  readonly tier: number;
  readonly role: string;
  readonly characterAffinity: ReadonlyArray<string>;
  readonly bonuses: Readonly<Record<2 | 3 | 4, SetBonusV2>>;
}

/** JSON shape of one Phase-14 set in `sets.json`. */
export interface RawEquipmentSet {
  readonly set_id?: string;
  readonly set_name?: string;
  readonly theme?: string;
  readonly description?: string;
  readonly tier?: number;
  readonly role?: string;
  readonly character_affinity?: ReadonlyArray<string>;
  readonly set_bonus_2_piece?: RawSetBonus;
  readonly set_bonus_3_piece?: RawSetBonus;
  readonly set_bonus_4_piece?: RawSetBonus;
}

export interface RawSetBonus {
  readonly name?: string;
  readonly type?: string;
  readonly description?: string;
  readonly [key: string]: unknown;
}

/** Build the equipment-set registry from raw JSON. */
export function makeEquipmentSetsFromData(
  raw: Readonly<Record<string, unknown>>,
): Readonly<Record<string, EquipmentSetV2>> {
  const out: Record<string, EquipmentSetV2> = {};
  for (const [key, value] of Object.entries(raw)) {
    if (key.startsWith("_")) continue;
    if (value === null || typeof value !== "object" || Array.isArray(value)) continue;
    const r = value as RawEquipmentSet;
    const setId = typeof r.set_id === "string" ? r.set_id : key;
    const bonuses: Partial<Record<2 | 3 | 4, SetBonusV2>> = {};
    if (r.set_bonus_2_piece !== undefined) bonuses[2] = normalizeSetBonus(r.set_bonus_2_piece);
    if (r.set_bonus_3_piece !== undefined) bonuses[3] = normalizeSetBonus(r.set_bonus_3_piece);
    if (r.set_bonus_4_piece !== undefined) bonuses[4] = normalizeSetBonus(r.set_bonus_4_piece);
    out[setId] = Object.freeze({
      setId,
      setName: typeof r.set_name === "string" ? r.set_name : setId,
      theme: typeof r.theme === "string" ? r.theme : "",
      description: typeof r.description === "string" ? r.description : "",
      tier: Number.isFinite(r.tier) ? Math.trunc(r.tier as number) : 1,
      role: typeof r.role === "string" ? r.role : "",
      characterAffinity: Array.isArray(r.character_affinity)
        ? Object.freeze(r.character_affinity.map(String))
        : Object.freeze([]),
      bonuses: Object.freeze(bonuses as Record<2 | 3 | 4, SetBonusV2>),
    });
  }
  return Object.freeze(out);
}

function normalizeSetBonus(raw: RawSetBonus): SetBonusV2 {
  const fields: Record<string, number> = {};
  for (const [k, v] of Object.entries(raw)) {
    if (k === "name" || k === "type" || k === "description") continue;
    if (typeof v === "number" && Number.isFinite(v)) fields[k] = v;
  }
  return Object.freeze({
    name: typeof raw.name === "string" ? raw.name : "",
    type: typeof raw.type === "string" ? raw.type : "",
    description: typeof raw.description === "string" ? raw.description : "",
    fields: Object.freeze(fields),
  });
}