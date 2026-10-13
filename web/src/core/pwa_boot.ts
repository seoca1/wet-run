/** PWA controller — boots the browser event listeners that feed `PwaState`.
 *
 * The pure helpers in `core/pwa_manager.ts` (isStandalone, promptInstall,
 * applyUpdate, hasWaitingWorker, getOnlineStatus, isServiceWorkerRegistered)
 * stay as-is; this module is the *consumer* that wires them to the live DOM.
 *
 * Responsibilities:
 *   - Capture `beforeinstallprompt` so the settings screen can fire the prompt
 *     on a real user gesture (browser policy forbids auto-prompting).
 *   - Track `controllerchange` → set `hasUpdate` so a newer worker controls
 *     the page (next load will pick it up after SKIP_WAITING).
 *   - Track `online`/`offline` to flip `isOffline`.
 *   - Re-check `hasWaitingWorker` after registration updates so the update
 *     row lights up when a worker is waiting.
 *   - Probe `navigator.onLine` once at boot for the initial `isOffline`.
 *   - Probe `isStandalone()` once at boot for the initial `isInstalled`.
 *
 * SSR/test safety: every side-effect is guarded by `typeof window`. Calling
 * `boot()` from a non-browser environment returns a no-op disposer.
 */

import {
  getOnlineStatus,
  hasWaitingWorker,
  isStandalone,
  INITIAL_PWA_STATE,
  promptInstall,
  applyUpdate,
  type PwaState,
} from "./pwa_manager.ts";

export type PwaListener = (state: PwaState) => void;

/** Internal helpers — only used by this controller. */
function hasWindow(): boolean {
  return typeof window !== "undefined";
}

function hasNavigator(): boolean {
  return typeof navigator !== "undefined";
}

function hasServiceWorkerApi(): boolean {
  return (
    hasNavigator() &&
    "serviceWorker" in (navigator as { serviceWorker?: unknown })
  );
}

/** Wrap hasWaitingWorker in a try/catch — jsdom + partial stubs can throw. */
async function probeWaitingWorker(): Promise<boolean> {
  try {
    return await hasWaitingWorker();
  } catch {
    return false;
  }
}

/** Public surface of the PWA controller. */
export interface PwaController {
  /** Current frozen PwaState snapshot. Safe to read at any time. */
  readonly state: PwaState;
  /** Subscribe to state changes. Returns an unsubscribe function. */
  subscribe(listener: PwaListener): () => void;
  /** Trigger the captured install prompt (must be a user gesture). */
  tryPromptInstall(): Promise<boolean>;
  /** SKIP_WAITING on the waiting worker (reloads page to activate). */
  tryApplyUpdate(): Promise<boolean>;
  /** Detach all listeners. Idempotent. No-op when SSR/no-window. */
  dispose(): void;
}

/** Build a fresh frozen `PwaState` with the runtime-probed values. */
function buildInitialState(): PwaState {
  const offline = hasNavigator() ? !getOnlineStatus() : INITIAL_PWA_STATE.isOffline;
  const installed = hasWindow() ? isStandalone() : INITIAL_PWA_STATE.isInstalled;
  return Object.freeze({
    canInstall: INITIAL_PWA_STATE.canInstall,
    isInstalled: installed,
    isOffline: offline,
    hasUpdate: INITIAL_PWA_STATE.hasUpdate,
    deferredPrompt: INITIAL_PWA_STATE.deferredPrompt,
  });
}

/**
 * Boot the PWA controller. Wires all listeners + returns a handle.
 *
 * Calling this from a non-browser environment returns a stub whose `state`
 * mirrors `INITIAL_PWA_STATE` and whose mutators all return `false`.
 * Tests can use this directly with synthetic events because jsdom does
 * provide `window`/`navigator`.
 */
export function bootPwaController(): PwaController {
  const listeners = new Set<PwaListener>();
  let state: PwaState = buildInitialState();
  let booted = false;

  const setState = (patch: Partial<PwaState>): void => {
    // Frozen immutable update: spread + freeze.
    state = Object.freeze({ ...state, ...patch });
    for (const l of listeners) l(state);
  };

  if (!hasWindow()) {
    // SSR / no-window environment: return a stub. All mutators are safe no-ops.
    return {
      get state(): PwaState {
        return state;
      },
      subscribe(listener: PwaListener): () => void {
        listeners.add(listener);
        return () => listeners.delete(listener);
      },
      async tryPromptInstall(): Promise<boolean> {
        return false;
      },
      async tryApplyUpdate(): Promise<boolean> {
        return false;
      },
      dispose(): void {
        listeners.clear();
      },
    };
  }

  const w = window as unknown as {
    addEventListener: (
      type: string,
      listener: (ev: Event) => void,
      options?: AddEventListenerOptions | boolean,
    ) => void;
    removeEventListener: (
      type: string,
      listener: (ev: Event) => void,
      options?: AddEventListenerOptions | boolean,
    ) => void;
  };

  const onBeforeInstallPrompt = (ev: Event): void => {
    // Browser convention: preventDefault so Chrome suppresses the mini-infobar
    // and we can fire it on our own user gesture later.
    const e = ev as { preventDefault?: () => void };
    e.preventDefault?.();
    setState({ canInstall: true, deferredPrompt: ev });
  };

  const onControllerChange = (): void => {
    // A new worker has taken control. The page should reload to use it.
    setState({ hasUpdate: true });
    // Best-effort refresh; result lands in a follow-up tick (fire and forget).
    if (hasServiceWorkerApi()) {
      void probeWaitingWorker().then((waiting) => {
        if (waiting) setState({ hasUpdate: true });
      });
    }
  };

  const onOnline = (): void => {
    setState({ isOffline: false });
  };

  const onOffline = (): void => {
    setState({ isOffline: true });
  };

  w.addEventListener("beforeinstallprompt", onBeforeInstallPrompt);
  w.addEventListener("controllerchange", onControllerChange);
  w.addEventListener("online", onOnline);
  w.addEventListener("offline", onOffline);
  booted = true;

  // Initial waiting-worker probe (best-effort). If a worker is already waiting
  // when the page boots (e.g. user reloaded without applying), light up the row.
  if (hasServiceWorkerApi()) {
    void probeWaitingWorker().then((waiting) => {
      if (waiting) setState({ hasUpdate: true });
    });
  }

  return {
    get state(): PwaState {
      return state;
    },
    subscribe(listener: PwaListener): () => void {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
    async tryPromptInstall(): Promise<boolean> {
      const accepted = await promptInstall(state.deferredPrompt);
      if (accepted) {
        // After install, canInstall flips false (no second prompt) and the
        // event is cleared so we don't fire it again.
        setState({ canInstall: false, deferredPrompt: null });
      }
      return accepted;
    },
    async tryApplyUpdate(): Promise<boolean> {
      const applied = await applyUpdate();
      if (applied) setState({ hasUpdate: false });
      return applied;
    },
    dispose(): void {
      if (!booted) return;
      booted = false;
      w.removeEventListener(
        "beforeinstallprompt",
        onBeforeInstallPrompt as unknown as (ev: Event) => void,
      );
      w.removeEventListener(
        "controllerchange",
        onControllerChange as unknown as (ev: Event) => void,
      );
      w.removeEventListener(
        "online",
        onOnline as unknown as (ev: Event) => void,
      );
      w.removeEventListener(
        "offline",
        onOffline as unknown as (ev: Event) => void,
      );
      listeners.clear();
    },
  };
}