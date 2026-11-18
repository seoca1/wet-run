/** Which gear the runner owns (ADR-0325).
 *
 * The catalog (18 pieces) and the craft recipes (16) existed, but nothing tied
 * them together: crafting pushed a throwaway `Program` and the EQUIPMENT menu
 * equipped whatever the registry listed first, owned or not. So equipment had
 * no acquisition path — measured: 18 pieces, 0 obtainable.
 *
 * This is the missing ownership axis. A piece is owned when it is a tier-0
 * starter (given, never crafted) or was crafted. The EQUIPMENT menu equips only
 * what is owned, so crafting finally buys something the player can wear.
 *
 * Storage mirrors `wallet.ts` / `equipment_store.ts`: one localStorage key,
 * tolerant reads (a malformed value is empty, never a throw), and no save-schema
 * change. Ownership is monotonic — nothing removes a piece.
 */
import { DEFAULT_REGISTRY } from "./equipment";

const STORAGE_KEY = "wetrun_owned_equipment";

/** Tier-0 gear is given with the deck, so it is owned without being crafted.
 *  Derived from the catalog (the `tier` field is the single source). */
export const STARTING_OWNED: ReadonlyArray<string> = Object.freeze(
  DEFAULT_REGISTRY.all.filter((e) => e.tier === "T0").map((e) => e.id),
);

/** The owned ids, as a set-shaped record (JSON-friendly, like the wallet). */
export type OwnedSet = Readonly<Record<string, true>>;

/** The owned ids on disk. An unreadable value degrades to empty, never throws. */
export function readOwnedIds(): OwnedSet {
  if (typeof localStorage === "undefined") return {};
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw === null) return {};
    const parsed: unknown = JSON.parse(raw);
    if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
      return {};
    }
    const out: Record<string, true> = {};
    for (const [k, v] of Object.entries(parsed as Record<string, unknown>)) {
      if (v === true) out[k] = true;
    }
    return Object.freeze(out);
  } catch {
    return {};
  }
}

/** Persist ownership. Storage is a convenience, so failure is silent. */
export function writeOwnedIds(owned: OwnedSet): void {
  if (typeof localStorage === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(owned));
  } catch {
    // Storage full or blocked.
  }
}

/** True when the piece is owned — a starter, or crafted and recorded. */
export function isOwned(owned: OwnedSet, id: string): boolean {
  return owned[id] === true || STARTING_OWNED.includes(id);
}

/** Ownership after crafting `id`. Idempotent; returns the same record when it
 *  already holds the piece, so callers can cheaply skip a write. */
export function ownEquipment(owned: OwnedSet, id: string): OwnedSet {
  if (isOwned(owned, id)) return owned;
  return Object.freeze({ ...owned, [id]: true });
}

/** Every owned id, starters first. Stable order for deterministic UI. */
export function ownedIds(owned: OwnedSet): ReadonlyArray<string> {
  const crafted = Object.keys(owned)
    .filter((id) => !STARTING_OWNED.includes(id))
    .sort();
  return Object.freeze([...STARTING_OWNED, ...crafted]);
}
