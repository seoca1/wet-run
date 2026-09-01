/** Remote Sync Engine for Tier 3 Cloud Save Sync.
 *
 * Handles push/pull operations with Supabase, conflict resolution,
 * and integration with the local save system.
 */
import { compressSave, decompressSave } from "./compression.ts";
import type { SaveSlot } from "../core/types.ts";
import { getSyncConfig } from "./sync_types.ts";
import {
  getSupabaseClient,
  initAnonAuth,
  upsertSave,
  fetchSave,
  getAuthState,
} from "./supabase_client.ts";
import { save, load, listSlots } from "./storage.ts";

const STALE_THRESHOLD_MS = 5 * 60 * 1000; // 5 minutes
const MAX_RETRIES = 3;
const RETRY_DELAY_MS = 1000;

/** Sync engine state. */
interface SyncEngineState {
  readonly status: "idle" | "syncing" | "success" | "error" | "offline";
  readonly last_sync_at: string | null;
  readonly last_error: string | null;
  readonly pending_slots: Set<number>;
}

let engineState: SyncEngineState = {
  status: "idle",
  last_sync_at: null,
  last_error: null,
  pending_slots: new Set(),
};

/** Get current engine state (for UI). */
export function getEngineState(): Readonly<SyncEngineState> {
  return engineState;
}

/** Update engine state and persist to localStorage. */
function setEngineState(partial: Partial<SyncEngineState>): void {
  engineState = { ...engineState, ...partial };
  try {
    localStorage.setItem("wetrun_sync_state", JSON.stringify({
      status: engineState.status,
      last_sync_at: engineState.last_sync_at,
      last_error: engineState.last_error,
    }));
  } catch {
    // ignore
  }
}

/** Load persisted engine state. */
export function loadEngineState(): void {
  try {
    const stored = localStorage.getItem("wetrun_sync_state");
    if (stored) {
      const parsed = JSON.parse(stored);
      engineState = {
        ...engineState,
        status: parsed.status ?? "idle",
        last_sync_at: parsed.last_sync_at ?? null,
        last_error: parsed.last_error ?? null,
      };
    }
  } catch {
    // ignore
  }
}

/** Check if sync is enabled and configured. */
function isSyncEnabled(): boolean {
  return getSyncConfig().enabled;
}

/** Check if a slot needs push (local newer than last sync). */
async function needsPush(slot: number): Promise<boolean> {
  if (!isSyncEnabled()) return false;

  const local = await load(slot);
  if (!local) return false;

  // Check if we have a last_sync timestamp for this slot
  const lastSyncStr = localStorage.getItem(`wetrun_sync_last_push_${slot}`);
  if (!lastSyncStr) return true; // Never pushed

  const lastSync = new Date(lastSyncStr).getTime();
  const localUpdated = new Date(local.savedAt).getTime();
  return localUpdated > lastSync;
}

/** Check if a slot needs pull (remote newer than local). */
async function needsPull(slot: number): Promise<boolean> {
  if (!isSyncEnabled()) return false;

  const client = getSupabaseClient();
  if (!client) return false;

  const auth = getAuthState();
  if (!auth.user_id) return false;

  // Check if stale threshold exceeded
  const lastPullStr = localStorage.getItem(`wetrun_sync_last_pull_${slot}`);
  if (lastPullStr) {
    const lastPull = new Date(lastPullStr).getTime();
    if (Date.now() - lastPull < STALE_THRESHOLD_MS) return false;
  }

  // Fetch remote timestamp
  const { data: remote } = await fetchSave(auth.user_id, slot);
  if (!remote) return false;

  const local = await load(slot);
  if (!local) return true; // No local, need pull

  const remoteUpdated = new Date(remote.updated_at).getTime();
  const localUpdated = new Date(local.savedAt).getTime();
  return remoteUpdated > localUpdated;
}

/** Push a single slot to Supabase with retries. */
async function pushSlot(slot: number, attempt = 1): Promise<{ success: boolean; error?: string }> {
  if (!isSyncEnabled()) return { success: false, error: "Sync disabled" };

  const auth = getAuthState();
  if (!auth.user_id) {
    // Try to init auth
    const { user_id, error } = await initAnonAuth();
    if (error || !user_id) return { success: false, error: error ?? "No auth" };
  }

  const local = await load(slot);
  if (!local) return { success: false, error: "No local save" };

  const compressed = compressSave(JSON.stringify(local));
  const { success, error } = await upsertSave(auth.user_id!, slot, compressed, local.version);

  if (success) {
    localStorage.setItem(`wetrun_sync_last_push_${slot}`, local.savedAt);
  } else if (attempt < MAX_RETRIES) {
    await new Promise(r => setTimeout(r, RETRY_DELAY_MS * attempt));
    return pushSlot(slot, attempt + 1);
  }

  return { success, error };
}

/** Pull a single slot from Supabase with retries. */
async function pullSlot(slot: number, attempt = 1): Promise<{ success: boolean; error?: string }> {
  if (!isSyncEnabled()) return { success: false, error: "Sync disabled" };

  const auth = getAuthState();
  if (!auth.user_id) {
    const { user_id, error } = await initAnonAuth();
    if (error || !user_id) return { success: false, error: error ?? "No auth" };
  }

  const { data: remote, error } = await fetchSave(auth.user_id!, slot);
  if (error) {
    if (attempt < MAX_RETRIES) {
      await new Promise(r => setTimeout(r, RETRY_DELAY_MS * attempt));
      return pullSlot(slot, attempt + 1);
    }
    return { success: false, error };
  }

  if (!remote) return { success: false, error: "No remote save" };

  // Decompress and save locally
  try {
    const decompressed = decompressSave(remote.data);
    const parsed: SaveSlot = JSON.parse(decompressed);
    await save(slot, parsed);
    localStorage.setItem(`wetrun_sync_last_pull_${slot}`, remote.updated_at);
    return { success: true };
  } catch (e) {
    return { success: false, error: e instanceof Error ? e.message : "Decompression failed" };
  }
}

/** Full sync: push all dirty slots, pull all stale slots. */
export async function fullSync(): Promise<{
  pushed: number;
  pulled: number;
  errors: string[];
}> {
  if (!isSyncEnabled()) {
    setEngineState({ status: "error", last_error: "Sync disabled" });
    return { pushed: 0, pulled: 0, errors: ["Sync disabled"] };
  }

  setEngineState({ status: "syncing", last_error: null });
  const errors: string[] = [];
  let pushed = 0;
  let pulled = 0;

  // Ensure auth
  const { user_id, error: authError } = await initAnonAuth();
  if (authError || !user_id) {
    setEngineState({ status: "error", last_error: authError ?? "Auth failed" });
    return { pushed: 0, pulled: 0, errors: [authError ?? "Auth failed"] };
  }

  const slots = await listSlots();

  // Push: iterate local slots that need push
  for (const slotInfo of slots) {
    if (await needsPush(slotInfo.slot)) {
      const result = await pushSlot(slotInfo.slot);
      if (result.success) pushed++;
      else errors.push(`Push slot ${slotInfo.slot}: ${result.error}`);
    }
  }

  // Pull: check all slots (0-3) for remote updates
  for (let slot = 0; slot <= 3; slot++) {
    if (await needsPull(slot)) {
      const result = await pullSlot(slot);
      if (result.success) pulled++;
      else errors.push(`Pull slot ${slot}: ${result.error}`);
    }
  }

  const finalStatus = errors.length > 0 ? "error" : "success";
  setEngineState({
    status: finalStatus,
    last_sync_at: new Date().toISOString(),
    last_error: errors.length > 0 ? errors.join("; ") : null,
  });

  return { pushed, pulled, errors };
}

/** Push only (for immediate save sync). */
export async function pushNow(slot: number): Promise<{ success: boolean; error?: string }> {
  if (!isSyncEnabled()) return { success: false, error: "Sync disabled" };

  const auth = getAuthState();
  if (!auth.user_id) {
    const { user_id, error } = await initAnonAuth();
    if (error || !user_id) return { success: false, error: error ?? "No auth" };
  }

  const result = await pushSlot(slot);
  if (result.success) {
    setEngineState({ status: "success", last_sync_at: new Date().toISOString() });
  } else {
    setEngineState({ status: "error", last_error: result.error });
  }
  return result;
}

/** Pull only (for manual refresh). */
export async function pullNow(slot: number): Promise<{ success: boolean; error?: string }> {
  if (!isSyncEnabled()) return { success: false, error: "Sync disabled" };

  const auth = getAuthState();
  if (!auth.user_id) {
    const { user_id, error } = await initAnonAuth();
    if (error || !user_id) return { success: false, error: error ?? "No auth" };
  }

  const result = await pullSlot(slot);
  if (result.success) {
    setEngineState({ status: "success", last_sync_at: new Date().toISOString() });
  } else {
    setEngineState({ status: "error", last_error: result.error });
  }
  return result;
}

/** Check sync status for a specific slot. */
export async function getSlotSyncStatus(slot: number): Promise<{
  local_exists: boolean;
  remote_exists: boolean;
  local_updated: string | null;
  remote_updated: string | null;
  needs_push: boolean;
  needs_pull: boolean;
}> {
  const local = await load(slot);
  const local_exists = local !== null;

  let remote_exists = false;
  let remote_updated: string | null = null;
  let needs_push = false;
  let needs_pull = false;

  if (isSyncEnabled()) {
    const auth = getAuthState();
    if (auth.user_id) {
      const { data: remote } = await fetchSave(auth.user_id, slot);
      remote_exists = remote !== null;
      remote_updated = remote?.updated_at ?? null;

      if (local_exists) {
        needs_push = await needsPush(slot);
        needs_pull = await needsPull(slot);
      } else if (remote_exists) {
        needs_pull = true;
      }
    }
  }

  return {
    local_exists,
    remote_exists,
    local_updated: local?.savedAt ?? null,
    remote_updated,
    needs_push,
    needs_pull,
  };
}

/** Initialize sync engine (call on app boot). */
export async function initSync(): Promise<void> {
  loadEngineState();

  if (!isSyncEnabled()) {
    setEngineState({ status: "offline" });
    return;
  }

  // Try to authenticate
  await initAnonAuth();

  // Background pull for stale slots
  try {
    await fullSync();
  } catch (e) {
    setEngineState({
      status: "error",
      last_error: e instanceof Error ? e.message : "Sync init failed",
    });
  }
}

/** Sign out and clear all sync data. */
export async function signOutSync(): Promise<void> {
  const { signOut } = await import("./supabase_client.ts");
  await signOut();
  engineState = {
    status: "idle",
    last_sync_at: null,
    last_error: null,
    pending_slots: new Set(),
  };
  // Clear sync metadata
  for (let i = 0; i <= 3; i++) {
    localStorage.removeItem(`wetrun_sync_last_push_${i}`);
    localStorage.removeItem(`wetrun_sync_last_pull_${i}`);
  }
  localStorage.removeItem("wetrun_sync_state");
  localStorage.removeItem("wetrun_sync_user_id");
}