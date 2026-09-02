/** Settings screen renderer (Tier 5, ADR-0207 follow-up + Tier 7 quota UI).
 *
 * Audio controls panel: BGM volume + SFX volume sliders + global mute toggle.
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

export type SettingsField = "bgm" | "sfx" | "mute";

export interface SettingsState {
  selectedField: SettingsField;
  bgmVolume: number;
  sfxVolume: number;
  muted: boolean;
  storageQuota: StorageQuota;
}

const VOLUME_STEP = 0.1;

/**
 * Synchronous version — uses an unavailable quota placeholder.
 * Use `getInitialSettingsStateAsync` from main.ts to fetch real quota.
 */
export function getInitialSettingsState(): SettingsState {
  const audio = AudioManager.getInstance();
  return {
    selectedField: "bgm",
    bgmVolume: audio.getBgmVolume(),
    sfxVolume: audio.getSfxVolume(),
    muted: audio.isMuted(),
    storageQuota: { state: "unavailable", reason: "not yet fetched" },
  };
}

/**
 * Async version that fetches the live storage quota via navigator.storage.estimate().
 * Returns a fully-populated SettingsState with real IDB usage stats.
 */
export async function getInitialSettingsStateAsync(): Promise<SettingsState> {
  const audio = AudioManager.getInstance();
  const storageQuota = await getStorageQuota();
  return {
    selectedField: "bgm",
    bgmVolume: audio.getBgmVolume(),
    sfxVolume: audio.getSfxVolume(),
    muted: audio.isMuted(),
    storageQuota,
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
  const percent = Math.round(value * 100).toString().padStart(3, " ");
  let out = setText(grid, 4, row, label, labelFg);
  out = setText(out, 4, row + 1, `[${bar}] ${percent}%`, selected ? PALETTE.GREEN_NEON : PALETTE.GRAY_MID);
  return out;
}

export function renderSettingsScreen(state: SettingsState, cols: number, rows: number): Grid {
  let grid = makeGrid(cols, rows);

  grid = setText(grid, Math.max(2, Math.floor((cols - 14) / 2)), 1, "WET RUN — Settings", PALETTE.GREEN_NEON);
  grid = setText(grid, 2, 3, "─".repeat(Math.min(cols - 4, 50)), PALETTE.GRAY_MID);

  grid = setText(grid, 4, 5, "AUDIO", PALETTE.CYAN_LIGHT);

  grid = renderSlider(grid, "BGM Volume", state.bgmVolume, state.selectedField === "bgm", 7);

  grid = renderSlider(grid, "SFX Volume", state.sfxVolume, state.selectedField === "sfx", 11);

  const muteLabel = state.muted ? "[X] MUTE ALL" : "[ ] MUTE ALL";
  const muteFg = state.selectedField === "mute"
    ? PALETTE.YELLOW_AMBER
    : (state.muted ? PALETTE.RED_BRIGHT : PALETTE.GRAY_LIGHT);
  grid = setText(grid, 4, 16, muteLabel, muteFg);

  // Tier 7: storage quota section.
  grid = renderStorageQuota(grid, state.storageQuota, cols, 18);

  const hint = state.selectedField === "mute"
    ? "ENTER: toggle mute | ESC: back"
    : "←/→: adjust volume | TAB: switch | ESC: back";
  grid = setText(grid, 2, rows - 3, hint, PALETTE.GRAY_DARK);
  grid = setText(grid, 2, rows - 2, "Volumes persist via localStorage", PALETTE.GRAY_DARK);

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
    out = setText(out, 4, row + 1, `[ Storage API unavailable ]`, PALETTE.GRAY_DARK);
    out = setText(out, 4, row + 2, quota.reason.slice(0, Math.max(0, cols - 6)), PALETTE.GRAY_DARK);
    return out;
  }
  const level = quotaLevel(quota.percent);
  const barColor = level === "critical"
    ? PALETTE.RED_BRIGHT
    : level === "warning"
      ? PALETTE.YELLOW_AMBER
      : PALETTE.GREEN_NEON;
  const bar = renderUsageBar(quota.percent, 20);
  const summary = summarizeQuota(quota);
  out = setText(out, 4, row + 1, `[${bar}] ${quota.percent}%`, barColor);
  out = setText(out, 4, row + 2, summary, barColor);
  if (level === "warning") {
    out = setText(out, 4, row + 3, "! Storage filling up — clear old saves", PALETTE.YELLOW_AMBER);
  } else if (level === "critical") {
    out = setText(out, 4, row + 3, "!! Quota nearly full — save may fail", PALETTE.RED_BRIGHT);
  }
  return out;
}

/** Async getter for quota re-fetch (called when user revisits Settings). */
export async function refreshStorageQuota(): Promise<StorageQuota> {
  return getStorageQuota();
}
