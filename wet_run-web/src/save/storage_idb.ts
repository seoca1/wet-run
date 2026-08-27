/** IndexedDB backend for wetrun-web save (Tier 3 literal: cloud save sync).
 *
 * Replaces the localStorage backend in `storage.ts` while preserving the
 * same public API surface (save/load/delete/list/migrate). Migration
 * happens lazily on the first read so that existing localStorage data
 * is copied into IndexedDB on first load.
 */
const DB_NAME = "wetrun_save_v1";
const DB_VERSION = 2; // bumped 2026-08-27: fix keyPath conflict (idbPut DataError)
const STORE = "slots";

interface SlotValue {
  readonly name: string;
  readonly slot: number;
  readonly json: string;
}

let dbPromise: Promise<IDBDatabase> | null = null;

function isBrowser(): boolean {
  return typeof indexedDB !== "undefined" && typeof window !== "undefined";
}

function openDb(): Promise<IDBDatabase> {
  if (!isBrowser()) return Promise.reject(new Error("IndexedDB unavailable"));
  if (dbPromise !== null) return dbPromise;
  dbPromise = new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE, { keyPath: "name" });
      }
      // Migration: bump DB_VERSION 1→2 clears stale store + recreates fresh
      // (old records may have been written with keyPath conflict; safe reset).
      else if ((req as unknown as { oldVersion: number }).oldVersion < 2) {
        db.deleteObjectStore(STORE);
        db.createObjectStore(STORE, { keyPath: "name" });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
  return dbPromise;
}

function slotKeyName(slot: number): string {
  return `slot_${slot}`;
}

export async function idbGet(slot: number): Promise<string | null> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readonly");
    const store = tx.objectStore(STORE);
    const req = store.get(slotKeyName(slot));
    req.onsuccess = () => {
      const v = req.result as SlotValue | undefined;
      resolve(v === undefined ? null : v.json);
    };
    req.onerror = () => reject(req.error);
  });
}

export async function idbPut(slot: number, json: string): Promise<void> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    const store = tx.objectStore(STORE);
    // keyPath: "name" — must embed the key in the value, not pass as 2nd arg.
    // Passing both throws DataError ("in-line keys and the key parameter was provided").
    const value: SlotValue = { name: slotKeyName(slot), slot, json };
    const req = store.put(value);
    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error);
  });
}

export async function idbDelete(slot: number): Promise<void> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    const store = tx.objectStore(STORE);
    const req = store.delete(slotKeyName(slot));
    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error);
  });
}

export async function idbKeys(): Promise<number[]> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readonly");
    const store = tx.objectStore(STORE);
    const req = store.getAllKeys();
    req.onsuccess = () => {
      const keys = req.result as IDBValidKey[];
      const slots: number[] = [];
      for (const k of keys) {
        const match = /^slot_(\d+)$/.exec(String(k));
        if (match) slots.push(Number(match[1]));
      }
      slots.sort();
      resolve(slots);
    };
    req.onerror = () => reject(req.error);
  });
}

export async function idbIsAvailable(): Promise<boolean> {
  try {
    await openDb();
    return true;
  } catch {
    return false;
  }
}
