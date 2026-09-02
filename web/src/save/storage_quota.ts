/** Storage quota helper (Tier 7).
 *
 * Wraps `navigator.storage.estimate()` (standard browser Storage API) so
 * the Settings screen can show the player how much IDB space their saves
 * consume and warn when they're approaching the browser quota.
 *
 * Browser support: StorageManager.estimate() is available in Chrome 61+,
 * Firefox 53+, Safari 15+. Older browsers and node/jsdom return
 * `unsupported` — callers must render the UI accordingly.
 *
 * Reference: MDN StorageManager.estimate()
 * https://developer.mozilla.org/en-US/docs/Web/API/StorageManager/estimate
 */

export type StorageQuota =
  | { readonly state: "ok"; readonly usageBytes: number; readonly quotaBytes: number; readonly percent: number }
  | { readonly state: "unavailable"; readonly reason: string };

export const STORAGE_QUOTA_WARNING_PERCENT = 80;
export const STORAGE_QUOTA_CRITICAL_PERCENT = 95;

/** Read the current storage usage + quota. Safe to call in any env. */
export async function getStorageQuota(): Promise<StorageQuota> {
  const sm = (typeof navigator !== "undefined" ? navigator.storage : undefined) as
    | { estimate?: () => Promise<{ usage?: number; quota?: number }> }
    | undefined;
  if (!sm || typeof sm.estimate !== "function") {
    return { state: "unavailable", reason: "StorageManager.estimate not supported" };
  }
  try {
    const estimate = await sm.estimate();
    const usage = Math.max(0, estimate.usage ?? 0);
    const quota = Math.max(0, estimate.quota ?? 0);
    if (quota === 0) {
      return { state: "unavailable", reason: "Browser reported zero quota" };
    }
    const percent = Math.min(100, Math.round((usage / quota) * 100));
    return { state: "ok", usageBytes: usage, quotaBytes: quota, percent };
  } catch (err) {
    const reason = err instanceof Error ? err.message : "unknown error";
    return { state: "unavailable", reason };
  }
}

/** Format bytes for display: 0 B / 1.5 KB / 12 MB / 1.2 GB. */
export function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes < 0) return "0 B";
  if (bytes < 1024) return `${Math.round(bytes)} B`;
  const kb = bytes / 1024;
  if (kb < 1024) return `${kb.toFixed(kb < 10 ? 2 : 1)} KB`;
  const mb = kb / 1024;
  if (mb < 1024) return `${mb.toFixed(mb < 10 ? 2 : 1)} MB`;
  const gb = mb / 1024;
  return `${gb.toFixed(gb < 10 ? 2 : 1)} GB`;
}

/** Render a 20-cell bar: █ for filled, ░ for empty. */
export function renderUsageBar(percent: number, cells: number = 20): string {
  const clamped = Math.max(0, Math.min(100, Math.round(percent)));
  const filled = Math.round((clamped / 100) * cells);
  return "█".repeat(filled) + "░".repeat(cells - filled);
}

/** Tier of warning state for UI color hint. */
export type StorageQuotaLevel = "ok" | "warning" | "critical" | "unavailable";

export function quotaLevel(percent: number): StorageQuotaLevel {
  if (percent >= STORAGE_QUOTA_CRITICAL_PERCENT) return "critical";
  if (percent >= STORAGE_QUOTA_WARNING_PERCENT) return "warning";
  return "ok";
}

/** Compose a one-line summary suitable for footer/hint areas. */
export function summarizeQuota(quota: StorageQuota): string {
  if (quota.state === "unavailable") return `Storage: ${quota.reason}`;
  return `Storage: ${formatBytes(quota.usageBytes)} / ${formatBytes(quota.quotaBytes)} (${quota.percent}%)`;
}
