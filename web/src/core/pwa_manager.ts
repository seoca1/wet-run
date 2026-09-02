/** PWA Manager — install prompt, update detection, offline status.
 *
 * Handles the beforeinstallprompt event, tracks online/offline state,
 * and detects when a new service worker version is available.
 */

export interface PwaState {
  readonly canInstall: boolean;
  readonly isInstalled: boolean;
  readonly isOffline: boolean;
  readonly hasUpdate: boolean;
  readonly deferredPrompt: unknown;
}

export const INITIAL_PWA_STATE: PwaState = Object.freeze({
  canInstall: false,
  isInstalled: false,
  isOffline: !navigator.onLine,
  hasUpdate: false,
  deferredPrompt: null,
});

/** Check if the app is running in standalone mode (installed). */
export function isStandalone(): boolean {
  return (
    window.matchMedia("(display-mode: standalone)").matches ||
    (window.navigator as unknown as Record<string, unknown>).standalone === true
  );
}

/** Check if a service worker is registered. */
export async function isServiceWorkerRegistered(): Promise<boolean> {
  if (!("serviceWorker" in navigator)) return false;
  const reg = await navigator.serviceWorker.getRegistration();
  return reg !== undefined;
}

/** Check if an update is waiting. */
export async function hasWaitingWorker(): Promise<boolean> {
  if (!("serviceWorker" in navigator)) return false;
  const reg = await navigator.serviceWorker.getRegistration();
  return reg?.waiting !== null && reg?.waiting !== undefined;
}

/** Attempt to install the PWA. Returns true if the prompt was shown. */
export async function promptInstall(prompt: unknown): Promise<boolean> {
  if (!prompt || typeof prompt !== "object" || !("prompt" in prompt)) return false;
  const p = prompt as { prompt: () => Promise<void>; userChoice: Promise<{ outcome: string }> };
  await p.prompt();
  const result = await p.userChoice;
  return result.outcome === "accepted";
}

/** Apply update by skipping waiting worker. */
export async function applyUpdate(): Promise<boolean> {
  if (!("serviceWorker" in navigator)) return false;
  const reg = await navigator.serviceWorker.getRegistration();
  if (!reg?.waiting) return false;
  reg.waiting.postMessage({ type: "SKIP_WAITING" });
  return true;
}

/** Get current online status. */
export function getOnlineStatus(): boolean {
  return navigator.onLine;
}
