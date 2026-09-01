/** Sync types for Tier 3 Remote Sync (Supabase). */
import type { SaveSlot } from "../core/types.ts";

// Extend ImportMeta for Vite env variables
declare global {
  interface ImportMetaEnv {
    readonly VITE_SUPABASE_URL: string;
    readonly VITE_SUPABASE_ANON_KEY: string;
    readonly VITE_SYNC_ENABLED: string;
  }
  interface ImportMeta {
    readonly env: ImportMetaEnv;
  }
}

/** Supabase configuration from environment. */
export interface SyncConfig {
  readonly url: string;
  readonly anonKey: string;
  readonly enabled: boolean;
}

/** Remote save record (matches Supabase `saves` table). */
export interface RemoteSave {
  readonly user_id: string;
  readonly slot: number;
  readonly data: string; // compressed SaveSlot JSON
  readonly schema_version: number;
  readonly updated_at: string; // ISO timestamp from server
}

/** Local save with sync metadata. */
export interface LocalSaveWithMeta extends SaveSlot {
  readonly last_synced_at: string | null;
  readonly pending_push: boolean;
}

/** Result of a sync operation. */
export interface SyncResult {
  readonly success: boolean;
  readonly pushed: number;
  readonly pulled: number;
  readonly conflicts: ReadonlyArray<SyncConflict>;
  readonly error?: string;
}

/** Conflict between local and remote save. */
export interface SyncConflict {
  readonly slot: number;
  readonly local_updated: string;
  readonly remote_updated: string;
  readonly resolution: "local_wins" | "remote_wins" | "manual";
}

/** Sync status for UI display. */
export type SyncStatus =
  | "idle"
  | "syncing"
  | "success"
  | "error"
  | "offline";

/** Auth state for anonymous user. */
export interface SyncAuthState {
  readonly user_id: string | null;
  readonly is_anonymous: boolean;
  readonly session_expires_at: string | null;
}

/** Environment variable names. */
export const ENV = {
  SUPABASE_URL: "VITE_SUPABASE_URL",
  SUPABASE_ANON_KEY: "VITE_SUPABASE_ANON_KEY",
  SYNC_ENABLED: "VITE_SYNC_ENABLED",
} as const;

/** Default sync configuration (can be overridden by env). */
export function getSyncConfig(): SyncConfig {
  const url = import.meta.env.VITE_SUPABASE_URL as string | undefined;
  const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;
  const enabled = import.meta.env.VITE_SYNC_ENABLED === "true";

  return {
    url: url ?? "",
    anonKey: anonKey ?? "",
    enabled: enabled && !!url && !!anonKey,
  };
}