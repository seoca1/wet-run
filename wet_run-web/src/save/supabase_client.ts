/** Supabase client for Tier 3 Remote Sync.
 *
 * Handles anonymous authentication and provides a typed client
 * for the `saves` table operations.
 */
import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import { getSyncConfig } from "./sync_types.ts";
import type { RemoteSave } from "./sync_types.ts";

let supabaseInstance: SupabaseClient | null = null;
let authState: { user_id: string | null; is_anonymous: boolean; session_expires_at: string | null } = {
  user_id: null,
  is_anonymous: false,
  session_expires_at: null,
};

/** Get or create the Supabase client singleton. */
export function getSupabaseClient(): SupabaseClient | null {
  const config = getSyncConfig();
  if (!config.enabled || !config.url || !config.anonKey) {
    return null;
  }

  if (supabaseInstance === null) {
    supabaseInstance = createClient(config.url, config.anonKey, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: false,
      },
    });
  }
  return supabaseInstance;
}

/** Initialize anonymous authentication.
 *
 * Creates an anonymous user if none exists, or restores existing session.
 * The user_id is persisted in localStorage for cross-session continuity.
 */
export async function initAnonAuth(): Promise<{ user_id: string | null; error?: string }> {
  const client = getSupabaseClient();
  if (!client) {
    return { user_id: null, error: "Supabase not configured" };
  }

  // Check for existing session
  const { data: { session } } = await client.auth.getSession();
  if (session?.user) {
    authState = {
      user_id: session.user.id,
      is_anonymous: session.user.is_anonymous ?? true,
      session_expires_at: session.expires_at ? new Date(session.expires_at * 1000).toISOString() : null,
    };
    return { user_id: authState.user_id };
  }

  // Check for stored anonymous user ID
  const storedUserId = localStorage.getItem("wetrun_sync_user_id");
  if (storedUserId) {
    // Try to recover session with stored user (may not work if session expired)
    // Fall through to create new anon user
  }

  // Sign in anonymously
  const { data, error } = await client.auth.signInAnonymously();
  if (error) {
    return { user_id: null, error: error.message };
  }

  if (data.user) {
    authState = {
      user_id: data.user.id,
      is_anonymous: true,
      session_expires_at: data.session?.expires_at
        ? new Date(data.session.expires_at * 1000).toISOString()
        : null,
    };
    localStorage.setItem("wetrun_sync_user_id", data.user.id);
    return { user_id: data.user.id };
  }

  return { user_id: null, error: "Anonymous sign-in returned no user" };
}

/** Get current auth state. */
export function getAuthState(): Readonly<typeof authState> {
  return authState;
}

/** Check if user is authenticated (has valid session). */
export async function isAuthenticated(): Promise<boolean> {
  const client = getSupabaseClient();
  if (!client) return false;

  const { data: { session } } = await client.auth.getSession();
  if (session?.user) {
    authState = {
      user_id: session.user.id,
      is_anonymous: session.user.is_anonymous ?? true,
      session_expires_at: session.expires_at ? new Date(session.expires_at * 1000).toISOString() : null,
    };
    return true;
  }
  return false;
}

/** Sign out and clear local auth state. */
export async function signOut(): Promise<void> {
  const client = getSupabaseClient();
  if (client) {
    await client.auth.signOut();
  }
  authState = { user_id: null, is_anonymous: false, session_expires_at: null };
  localStorage.removeItem("wetrun_sync_user_id");
}

/** Upsert a save slot to Supabase. */
export async function upsertSave(
  userId: string,
  slot: number,
  compressedData: string,
  schemaVersion: number = 1
): Promise<{ success: boolean; error?: string }> {
  const client = getSupabaseClient();
  if (!client) return { success: false, error: "Supabase not configured" };

  const { error } = await client
    .from("saves")
    .upsert({
      user_id: userId,
      slot,
      data: compressedData,
      schema_version: schemaVersion,
      updated_at: new Date().toISOString(),
    }, { onConflict: "user_id,slot" });

  if (error) return { success: false, error: error.message };
  return { success: true };
}

/** Fetch a save slot from Supabase. */
export async function fetchSave(
  userId: string,
  slot: number
): Promise<{ data: RemoteSave | null; error?: string }> {
  const client = getSupabaseClient();
  if (!client) return { data: null, error: "Supabase not configured" };

  const { data, error } = await client
    .from("saves")
    .select("*")
    .eq("user_id", userId)
    .eq("slot", slot)
    .single();

  if (error) {
    if (error.code === "PGRST116") return { data: null, error: undefined }; // Not found
    return { data: null, error: error.message };
  }
  return { data: data as RemoteSave, error: undefined };
}

/** Fetch all save slots for a user. */
export async function fetchAllSaves(userId: string): Promise<{ data: RemoteSave[]; error?: string }> {
  const client = getSupabaseClient();
  if (!client) return { data: [], error: "Supabase not configured" };

  const { data, error } = await client
    .from("saves")
    .select("*")
    .eq("user_id", userId)
    .order("slot", { ascending: true });

  if (error) return { data: [], error: error.message };
  return { data: (data as RemoteSave[]) ?? [], error: undefined };
}

/** Delete a save slot from Supabase. */
export async function deleteSave(userId: string, slot: number): Promise<{ success: boolean; error?: string }> {
  const client = getSupabaseClient();
  if (!client) return { success: false, error: "Supabase not configured" };

  const { error } = await client
    .from("saves")
    .delete()
    .eq("user_id", userId)
    .eq("slot", slot);

  if (error) return { success: false, error: error.message };
  return { success: true };
}

/** Subscribe to realtime changes for a user's saves (optional, for future live sync). */
export function subscribeToSaves(userId: string, callback: (payload: { eventType: string; new: RemoteSave | null; old: RemoteSave | null }) => void): () => void {
  const client = getSupabaseClient();
  if (!client) return () => {};

  const channel = client
    .channel(`saves:${userId}`)
    .on("postgres_changes", { event: "*", schema: "public", table: "saves", filter: `user_id=eq.${userId}` }, (payload) => {
      callback({
        eventType: payload.eventType,
        new: payload.new as RemoteSave | null,
        old: payload.old as RemoteSave | null,
      });
    })
    .subscribe();

  return () => {
    client.removeChannel(channel);
  };
}