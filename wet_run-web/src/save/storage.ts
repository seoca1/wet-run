/** Multi-slot save/load for wetrun-web (Tier 2a).
 *
 * Extends the single-slot MVP save to support 3 manual slots + 1 auto slot.
 * Slot 0 = autosave (overwritten on phase transitions); slots 1-3 = manual.
 *
 * Backward-compatible: if a legacy single-slot save exists (no slot suffix),
 * it is read as slot 0 (autosave) on first load and migrated.
 */
import type { SaveSlot } from "../core/types.ts";
import { idbGet, idbPut, idbDelete, idbIsAvailable } from "./storage_idb.ts";

const CURRENT_SCHEMA_VERSION = 1;
const MANUAL_SLOT_COUNT = 3;
const SLOT_COUNT = MANUAL_SLOT_COUNT + 1;
const MAX_SLOT_INDEX = MANUAL_SLOT_COUNT;

function key(slot: number): string {
  if (slot < 0 || slot > MAX_SLOT_INDEX) throw new Error(`Invalid save slot ${slot}`);
  return `wetrun_mvp_save_v1_slot_${slot}`;
}

const LEGACY_KEY = "wetrun_mvp_save_v1";

export async function save(slot: number, data: SaveSlot): Promise<void> {
  if (!(await idbIsAvailable())) {
    saveLegacy(slot, data);
    return;
  }
  try {
    await idbPut(slot, JSON.stringify(data));
  } catch (err) {
    if (err instanceof Error && err.message.startsWith("Invalid save slot")) throw err;
    console.warn(`IDB save failed slot ${slot}, falling back to localStorage:`, err);
    saveLegacy(slot, data);
  }
}

function saveLegacy(slot: number, data: SaveSlot): void {
  try {
    localStorage.setItem(key(slot), JSON.stringify(data));
  } catch (err) {
    if (err instanceof Error && err.message.startsWith("Invalid save slot")) throw err;
    console.warn(`Failed to save slot ${slot}:`, err);
  }
}

export async function load(slot: number): Promise<SaveSlot | null> {
  if (!(await idbIsAvailable())) {
    return loadLegacy(slot);
  }
  try {
    const raw = await idbGet(slot);
    if (raw) return parseSlot(raw);
    return await migrateFromLegacy(slot);
  } catch (err) {
    if (err instanceof Error && err.message.startsWith("Invalid save slot")) throw err;
    console.warn(`IDB load failed slot ${slot}, falling back to localStorage:`, err);
    return loadLegacy(slot);
  }
}

function loadLegacy(slot: number): SaveSlot | null {
  try {
    const raw = localStorage.getItem(key(slot));
    if (raw) return parseSlot(raw);
    if (slot === 0) {
      const legacy = localStorage.getItem(LEGACY_KEY);
      if (legacy) {
        const parsed = parseSlot(legacy);
        if (parsed) {
          localStorage.setItem(key(0), legacy);
          localStorage.removeItem(LEGACY_KEY);
          return parsed;
        }
      }
    }
    return null;
  } catch (err) {
    if (err instanceof Error && err.message.startsWith("Invalid save slot")) throw err;
    console.warn(`Failed to load slot ${slot}:`, err);
    return null;
  }
}

async function migrateFromLegacy(slot: number): Promise<SaveSlot | null> {
  const parsed = loadLegacy(slot);
  if (parsed === null) return null;
  try {
    await idbPut(slot, JSON.stringify(parsed));
    if (slot === 0) localStorage.removeItem(LEGACY_KEY);
    localStorage.removeItem(key(slot));
  } catch (err) {
    console.warn(`IDB migration copy failed slot ${slot}:`, err);
  }
  return parsed;
}


export async function clear(slot: number): Promise<void> {
  if (!(await idbIsAvailable())) {
    localStorage.removeItem(key(slot));
    return;
  }
  try {
    await idbDelete(slot);
  } catch (err) {
    console.warn(`Failed to clear slot ${slot}:`, err);
  }
}

export async function listSlots(): Promise<ReadonlyArray<{
  readonly slot: number;
  readonly savedAt: string;
  readonly missionId: string;
  readonly turnCount: number;
}>> {
  const out: { slot: number; savedAt: string; missionId: string; turnCount: number }[] = [];
  for (let s = 0; s <= MAX_SLOT_INDEX; s++) {
    const data = await load(s);
    if (data) {
      out.push({
        slot: s,
        savedAt: data.savedAt,
        missionId: data.missionId,
        turnCount: data.turnCount,
      });
    }
  }
  return out;
}

function parseSlot(raw: string): SaveSlot | null {
  try {
    const parsed: unknown = JSON.parse(raw);
    if (!isSaveSlot(parsed)) return null;
    if (parsed.version !== CURRENT_SCHEMA_VERSION) return null;
    return parsed;
  } catch {
    return null;
  }
}

function isSaveSlot(value: unknown): value is SaveSlot {
  if (typeof value !== "object" || value === null) return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.version === "number" &&
    typeof v.missionId === "string" &&
    typeof v.playerHp === "number" &&
    typeof v.playerMaxHp === "number" &&
    typeof v.playerAlarm === "number" &&
    typeof v.playerCredits === "number" &&
    typeof v.turnCount === "number" &&
    Array.isArray(v.deckIds) &&
    Array.isArray(v.discardIds) &&
    Array.isArray(v.drawIds) &&
    typeof v.savedAt === "string"
  );
}

export const SAVE_SLOT_LABELS: Readonly<Record<number, string>> = Object.freeze({
  0: "Autosave",
  1: "Slot 1",
  2: "Slot 2",
  3: "Slot 3",
});

export const SLOT_COUNT_TOTAL: number = SLOT_COUNT;
export const MAX_SAVE_SLOT: number = MAX_SLOT_INDEX;
export const MANUAL_SLOTS: ReadonlyArray<number> = [1, 2, 3];
