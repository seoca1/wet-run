/** Where the runner's equipped gear lives between sessions (ADR-0322).
 *
 * The EQUIPMENT menu was **inert**: it edited a `Game`-level loadout
 * (`main.ts`), and a run read `state.equipmentLoadout`, which `makeInitialState`
 * builds as `EMPTY_LOADOUT` and nothing ever filled. So equipping a deck or a
 * set of trodes changed no number, and the gear was lost on reload besides.
 *
 * This is the missing half: the menu's loadout is persisted, and the run is
 * handed it at jack-in. Stored as slot → equipment id, rehydrated against the
 * registry, so a renamed or removed id degrades to "not equipped" instead of
 * producing a half-built loadout.
 *
 * Storage model mirrors `prep_wallet.ts` and `far_grid_gate.ts`: localStorage,
 * a single key, tolerant reads (a malformed value is treated as empty rather
 * than thrown), and no save-schema change.
 */
import type { EquipSlot, Equipment } from "./equipment";
import { EQUIP_SLOTS } from "./equipment";
import { makeLoadout, equipOn, type EquipmentLoadout } from "./loadout";

const STORAGE_KEY = "wetrun_equipment";

/** Minimal registry shape this module needs (a real one is `EquipmentRegistry`). */
export interface LoadoutRegistry {
  readonly all: ReadonlyArray<Equipment>;
}

/** The equipped ids, by slot. Empty when storage is unavailable or malformed. */
export function readEquippedIds(): Readonly<Record<string, string>> {
  if (typeof localStorage === "undefined") return {};
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw === null) return {};
    const parsed: unknown = JSON.parse(raw);
    if (parsed === null || typeof parsed !== "object") return {};
    const out: Record<string, string> = {};
    for (const slot of EQUIP_SLOTS) {
      const value = (parsed as Record<string, unknown>)[slot];
      if (typeof value === "string" && value !== "") out[slot] = value;
    }
    return out;
  } catch {
    return {};
  }
}

/** Persist what is equipped. Unknown slots are dropped, so the key stays small. */
export function writeEquippedIds(loadout: EquipmentLoadout): void {
  if (typeof localStorage === "undefined") return;
  try {
    const ids: Record<string, string> = {};
    for (const slot of EQUIP_SLOTS) {
      const item = loadout.get(slot);
      if (item !== null) ids[slot] = item.id;
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
  } catch {
    // Storage full or blocked — the loadout is a convenience, never a gate.
  }
}

/** Build a loadout from stored ids, skipping anything the registry no longer has. */
export function hydrateLoadout(
  registry: LoadoutRegistry,
  ids: Readonly<Record<string, string>>,
): EquipmentLoadout {
  let loadout = makeLoadout();
  for (const slot of EQUIP_SLOTS) {
    const id = ids[slot];
    if (id === undefined) continue;
    const item = registry.all.find((e) => e.id === id && e.slot === slot);
    if (item === undefined) continue;
    loadout = equipOn(loadout, item).loadout;
  }
  return loadout;
}

/** True when nothing is equipped — the run then keeps `EMPTY_LOADOUT`. */
export function isEmptyLoadout(loadout: EquipmentLoadout): boolean {
  return EQUIP_SLOTS.every((slot) => loadout.get(slot) === null);
}

/** Every slot the loadout can hold, for callers that iterate it. */
export const LOADOUT_SLOTS: ReadonlyArray<EquipSlot> = EQUIP_SLOTS;
