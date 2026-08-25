/** localStorage-backed save/load for wetrun-web MVP.
 *
 * Tier 1: localStorage JSON. Tier 2: IndexedDB for larger saves (cloud sync
 * explicitly out of scope per ADR-0199).
 *
 * Save schema version is bumped on breaking changes; old saves are
 * silently dropped (the user re-starts the mission).
 */
import type { SaveSlot } from "../core/types.ts";

const SAVE_KEY = "wetrun_mvp_save_v1";
const CURRENT_SCHEMA_VERSION = 1;

export function save(slot: SaveSlot): void {
  try {
    localStorage.setItem(SAVE_KEY, JSON.stringify(slot));
  } catch (err) {
    // QuotaExceededError or SecurityError — log and continue (game still playable).
    console.warn("Failed to save game:", err);
  }
}

export function load(): SaveSlot | null {
  try {
    const raw = localStorage.getItem(SAVE_KEY);
    if (!raw) return null;
    const parsed: unknown = JSON.parse(raw);
    if (!isSaveSlot(parsed)) return null;
    if (parsed.version !== CURRENT_SCHEMA_VERSION) return null; // Future-proof: drop old saves.
    return parsed;
  } catch (err) {
    console.warn("Failed to load save:", err);
    return null;
  }
}

export function clear(): void {
  try {
    localStorage.removeItem(SAVE_KEY);
  } catch (err) {
    console.warn("Failed to clear save:", err);
  }
}

/** Runtime type guard — defends against tampered localStorage. */
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
