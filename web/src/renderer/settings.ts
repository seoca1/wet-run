/** Settings screen renderer (Tier 5, ADR-0207 follow-up + Tier 7 quota UI).
 *
 * Audio controls panel: BGM volume + SFX volume sliders + global mute toggle.
 * Language toggle (EN/KO) — persisted via localStorage. Drives the language
 * arg of the menu + Far Grid hub renderers (which already accept `language`).
 * Storage quota panel: IDB usage bar + percent + warning levels.
 * Volumes are persisted via AudioManager (localStorage). The renderer is
 * pure: it reads current values from the AudioManager instance and emits
 * a Grid; the main game loop handles input dispatch (Left/Right to
 * decrement/increment, M to toggle mute, ESC to back out).
 */
import type { Grid } from "../core/types.ts";
import { makeGrid, setText } from "../core/grid.ts";
import { PALETTE } from "./palette.ts";
import { AudioManager } from "../audio/manager.ts";
import {
  getStorageQuota,
  renderUsageBar,
  quotaLevel,
  summarizeQuota,
  type StorageQuota,
} from "../save/storage_quota.ts";
import { isLanguageSupported, t, type Language } from "../core/i18n.ts";
import { INITIAL_PWA_STATE, type PwaState } from "../core/pwa_manager.ts";

/** Default `pwa` slot for callers that don't have a live controller. */
export function defaultPwaState(): PwaState {
  return INITIAL_PWA_STATE;
}

/** localStorage key for the persisted UI language (EN/KO).
 *
 * Mirrors the `wetrun_*` key convention used by audio settings
 * (`wetrun_audio_off`, `wetrun_audio_bgm_volume`, …) and other persisted
 * toggles. Stored value is the bare language code ("en" or "ko"). Unknown
 * or malformed values are rejected at read time — see `loadPersistedLanguage`.
 */
export const LANGUAGE_STORAGE_KEY = "wetrun_language";

/** Read the persisted UI language. Returns "en" when missing/invalid. */
export function loadPersistedLanguage(): Language {
  if (typeof localStorage === "undefined") return "en";
  const raw = localStorage.getItem(LANGUAGE_STORAGE_KEY);
  if (raw !== null && isLanguageSupported(raw)) return raw;
  return "en";
}

/** Persist the UI language. No-op when localStorage is unavailable. */
export function persistLanguage(language: Language): void {
  if (typeof localStorage === "undefined") return;
  localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
}

/** Cycle the language to the next supported value (en → ko → en). */
export function cycleLanguage(current: Language): Language {
  return current === "en" ? "ko" : "en";
}

export type SettingsField =
  | "audio"
  | "bgm"
  | "sfx"
  | "mute"
  | "language"
  | "pwa_install"
  | "pwa_update";

export interface SettingsState {
  selectedField: SettingsField;
  audioEnabled: boolean;
  bgmVolume: number;
  sfxVolume: number;
  muted: boolean;
  language: Language;
  storageQuota: StorageQuota;
  /** Live PWA state — populated by `bootPwaController` in main.ts. */
  pwa: PwaState;
}

const VOLUME_STEP = 0.1;

/**
 * Synchronous version — uses an unavailable quota placeholder.
 * Use `getInitialSettingsStateAsync` from main.ts to fetch real quota.
 *
 * Pass an optional `pwa` snapshot from `bootPwaController().state` so the
 * PWA section reflects live install/update/offline status instead of
 * `INITIAL_PWA_STATE`.
 */
export function getInitialSettingsState(
  pwa: PwaState = defaultPwaState(),
): SettingsState {
  const language = loadPersistedLanguage();
  let audio: AudioManager;
  try {
    audio = AudioManager.getInstance();
  } catch {
    return {
      selectedField: "audio",
      audioEnabled: localStorage.getItem("wetrun_audio_off") !== "1",
      bgmVolume: 0.4,
      sfxVolume: 0.6,
      muted: false,
      language,
      storageQuota: { state: "unavailable", reason: "not yet fetched" },
      pwa,
    };
  }
  return {
    selectedField: "audio",
    audioEnabled: !audio.isMuted(),
    bgmVolume: audio.getBgmVolume(),
    sfxVolume: audio.getSfxVolume(),
    muted: audio.isMuted(),
    language,
    storageQuota: { state: "unavailable", reason: "not yet fetched" },
    pwa,
  };
}

/**
 * Async version that fetches the live storage quota via navigator.storage.estimate().
 * Returns a fully-populated SettingsState with real IDB usage stats.
 *
 * Pass the live `pwa` snapshot so the PWA section reflects install/update/offline.
 */
export async function getInitialSettingsStateAsync(
  pwa: PwaState = defaultPwaState(),
): Promise<SettingsState> {
  const audio = AudioManager.getInstance();
  const storageQuota = await getStorageQuota();
  return {
    selectedField: "audio",
    audioEnabled: !audio.isMuted(),
    bgmVolume: audio.getBgmVolume(),
    sfxVolume: audio.getSfxVolume(),
    muted: audio.isMuted(),
    language: loadPersistedLanguage(),
    storageQuota,
    pwa,
  };
}

export function clampVolume(v: number): number {
  if (Number.isNaN(v)) return 0;
  if (v < 0) return 0;
  if (v > 1) return 1;
  return v;
}

export function adjustVolume(v: number, direction: "inc" | "dec"): number {
  const delta = direction === "inc" ? VOLUME_STEP : -VOLUME_STEP;
  return clampVolume(Math.round((v + delta) * 10) / 10);
}

function renderSlider(
  grid: Grid,
  label: string,
  value: number,
  selected: boolean,
  row: number,
): Grid {
  const labelFg = selected ? PALETTE.YELLOW_AMBER : PALETTE.GRAY_LIGHT;
  const width = 20;
  const filledCells = Math.round(value * width);
  const bar = "█".repeat(filledCells) + "░".repeat(width - filledCells);
  const percent = Math.round(value * 100)
    .toString()
    .padStart(3, " ");
  let out = setText(grid, 4, row, label, labelFg);
  out = setText(
    out,
    4,
    row + 1,
    `[${bar}] ${percent}%`,
    selected ? PALETTE.GREEN_NEON : PALETTE.GRAY_MID,
  );
  return out;
}

export function renderSettingsScreen(
  state: SettingsState,
  cols: number,
  rows: number,
): Grid {
  let grid = makeGrid(cols, rows);

  grid = setText(
    grid,
    Math.max(2, Math.floor((cols - 14) / 2)),
    1,
    "WET RUN — Settings",
    PALETTE.GREEN_NEON,
  );
  grid = setText(
    grid,
    2,
    3,
    "─".repeat(Math.min(cols - 4, 50)),
    PALETTE.GRAY_MID,
  );

  const audioLabel = state.audioEnabled
    ? "[X] AUDIO ENABLED"
    : "[ ] AUDIO ENABLED";
  const audioFg =
    state.selectedField === "audio"
      ? PALETTE.YELLOW_AMBER
      : state.audioEnabled
        ? PALETTE.GREEN_NEON
        : PALETTE.RED_BRIGHT;
  grid = setText(grid, 4, 5, "AUDIO", PALETTE.CYAN_LIGHT);
  grid = setText(grid, 4, 7, audioLabel, audioFg);

  grid = renderSlider(
    grid,
    "BGM Volume",
    state.bgmVolume,
    state.selectedField === "bgm",
    9,
  );

  grid = renderSlider(
    grid,
    "SFX Volume",
    state.sfxVolume,
    state.selectedField === "sfx",
    13,
  );

  const muteLabel = state.muted ? "[X] MUTE ALL" : "[ ] MUTE ALL";
  const muteFg =
    state.selectedField === "mute"
      ? PALETTE.YELLOW_AMBER
      : state.muted
        ? PALETTE.RED_BRIGHT
        : PALETTE.GRAY_LIGHT;
  grid = setText(grid, 4, 18, muteLabel, muteFg);

  grid = setText(grid, 4, 20, t("settings.language", state.language), PALETTE.CYAN_LIGHT);
  const languageLabel = state.language === "ko" ? "[X] KO" : "[ ] EN";
  const languageFg =
    state.selectedField === "language"
      ? PALETTE.YELLOW_AMBER
      : state.language === "ko"
        ? PALETTE.GREEN_NEON
        : PALETTE.GRAY_LIGHT;
  grid = setText(grid, 4, 22, languageLabel, languageFg);

  grid = setText(grid, 4, 24, "STORAGE", PALETTE.CYAN_LIGHT);
  if (state.storageQuota.state === "unavailable") {
    grid = setText(
      grid,
      4,
      25,
      `[ Storage API unavailable ]`,
      PALETTE.GRAY_DARK,
    );
  } else {
    const level = quotaLevel(state.storageQuota.percent);
    const barColor =
      level === "critical"
        ? PALETTE.RED_BRIGHT
        : level === "warning"
          ? PALETTE.YELLOW_AMBER
          : PALETTE.GREEN_NEON;
    const bar = renderUsageBar(state.storageQuota.percent, 20);
    grid = setText(
      grid,
      4,
      25,
      `[${bar}] ${state.storageQuota.percent}%`,
      barColor,
    );
  }

  // PWA section: install row, update row, offline status line.
  // Always rendered (uses live `state.pwa` from bootPwaController) — never
  // hidden, so the player can always see the current status.
  grid = setText(grid, 4, 27, t("settings.pwa", state.language), PALETTE.CYAN_LIGHT);

  const pwa = state.pwa;
  // Install row: [ ] when not installable, [X] INSTALLED when standalone,
  // [ ] INSTALL APP otherwise (will be selectable only when canInstall).
  let installLabel: string;
  let installFg: string;
  if (pwa.isInstalled) {
    installLabel = `[X] ${t("settings.pwa_installed", state.language)}`;
    installFg = PALETTE.GREEN_NEON;
  } else if (pwa.canInstall) {
    installLabel = `[ ] ${t("settings.pwa_install", state.language)}`;
    installFg =
      state.selectedField === "pwa_install"
        ? PALETTE.YELLOW_AMBER
        : PALETTE.GRAY_LIGHT;
  } else {
    installLabel = `[ ] ${t("settings.pwa_unavailable", state.language)}`;
    installFg =
      state.selectedField === "pwa_install"
        ? PALETTE.YELLOW_AMBER
        : PALETTE.GRAY_DARK;
  }
  grid = setText(grid, 4, 29, installLabel, installFg);

  // Update row: lights up when the controller has detected a waiting worker
  // or a `controllerchange` event fired.
  const updateLabel = pwa.hasUpdate
    ? `[X] ${t("settings.pwa_update_available", state.language)}`
    : `[ ] ${t("settings.pwa_update", state.language)}`;
  const updateFg =
    state.selectedField === "pwa_update"
      ? PALETTE.YELLOW_AMBER
      : pwa.hasUpdate
        ? PALETTE.GREEN_NEON
        : PALETTE.GRAY_LIGHT;
  grid = setText(grid, 4, 31, updateLabel, updateFg);

  // Offline status line (informational only — not selectable).
  const offlineLabel = pwa.isOffline
    ? t("settings.pwa_offline", state.language)
    : t("settings.pwa_online", state.language);
  const offlineFg = pwa.isOffline ? PALETTE.YELLOW_AMBER : PALETTE.GRAY_DARK;
  grid = setText(grid, 4, 33, offlineLabel, offlineFg);

  const hint =
    state.selectedField === "audio"
      ? "ENTER: toggle audio | TAB: switch | ESC: back"
      : state.selectedField === "mute"
        ? "ENTER: toggle mute | TAB: switch | ESC: back"
        : state.selectedField === "language"
          ? "ENTER: toggle language | TAB: switch | ESC: back"
          : state.selectedField === "pwa_install"
            ? "ENTER: install app | ESC: back"
            : state.selectedField === "pwa_update"
              ? "ENTER: apply update | ESC: back"
              : "←/→: adjust volume | TAB: switch | ESC: back";
  grid = setText(grid, 2, rows - 2, hint, PALETTE.GRAY_DARK);
  grid = setText(
    grid,
    2,
    rows - 1,
    "Volumes persist via localStorage",
    PALETTE.GRAY_DARK,
  );

  return grid;
}

/**
 * Render the storage quota section: label + usage bar + percent + warning hint.
 * Tier 7 — gives the player visibility into IDB usage before hitting quota.
 */
export function renderStorageQuota(
  grid: Grid,
  quota: StorageQuota,
  cols: number,
  row: number,
): Grid {
  let out = setText(grid, 4, row, "STORAGE", PALETTE.CYAN_LIGHT);
  if (quota.state === "unavailable") {
    out = setText(
      out,
      4,
      row + 1,
      `[ Storage API unavailable ]`,
      PALETTE.GRAY_DARK,
    );
    out = setText(
      out,
      4,
      row + 2,
      quota.reason.slice(0, Math.max(0, cols - 6)),
      PALETTE.GRAY_DARK,
    );
    return out;
  }
  const level = quotaLevel(quota.percent);
  const barColor =
    level === "critical"
      ? PALETTE.RED_BRIGHT
      : level === "warning"
        ? PALETTE.YELLOW_AMBER
        : PALETTE.GREEN_NEON;
  const bar = renderUsageBar(quota.percent, 20);
  const summary = summarizeQuota(quota);
  out = setText(out, 4, row + 1, `[${bar}] ${quota.percent}%`, barColor);
  out = setText(out, 4, row + 2, summary, barColor);
  if (level === "warning") {
    out = setText(
      out,
      4,
      row + 3,
      "! Storage filling up — clear old saves",
      PALETTE.YELLOW_AMBER,
    );
  } else if (level === "critical") {
    out = setText(
      out,
      4,
      row + 3,
      "!! Quota nearly full — save may fail",
      PALETTE.RED_BRIGHT,
    );
  }
  return out;
}

/** Async getter for quota re-fetch (called when user revisits Settings). */
export async function refreshStorageQuota(): Promise<StorageQuota> {
  return getStorageQuota();
}
