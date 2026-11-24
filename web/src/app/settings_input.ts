/** Settings-screen key handling.
 *
 * Extracted from `Game.handlePreGameInput`'s `screen === "settings"` branch
 * (refactoring Stage 3a-1a, 2026-11-24). That branch was ~185 lines — the
 * largest single piece of the pre-game input ladder — and it works the same
 * whether a run is live or not, so it earns its own home.
 *
 * The host interface is structural: `Game` already has every member, so the
 * controller passes `this` and owns no constructor. Only the pre-game path
 * reaches this module today; the run-time `handleSettingsInput` stub is a
 * different route (the run state is live behind it).
 *
 * Behaviour is preserved exactly, including the two quirks worth naming:
 * - the whole handler is gated on the audio module loading; with audio off
 *   (`wetrun_audio_off=1`) the keys do nothing.
 * - the volume "defaults" are persisted on the first visit by re-applying the
 *   manager's own current values, which is what writes the localStorage keys.
 */
import type { GameAction, ScreenKind } from "../core/types";
import type { PwaController } from "../core/pwa_boot";
import {
  adjustVolume,
  cycleLanguage,
  getInitialSettingsState,
  persistLanguage,
  type SettingsField,
  type SettingsState,
} from "../renderer/settings";
import {
  nextColorblindMode,
  nextTextScale,
  persistColorblindMode,
  persistHighContrastOverride,
  persistReducedMotionOverride,
  persistTextScale,
  previousTextScale,
  textScaleFactor,
  type ColorblindMode,
  type TextScaleStep,
} from "../renderer/accessibility_modes";
import { applyPaletteMode } from "../renderer/palette";

/** The settings rows, in the order the Up/Down cursor walks them. */
const SETTINGS_FIELDS: ReadonlyArray<SettingsField> = [
  "audio",
  "master",
  "bgm",
  "sfx",
  "mute",
  "language",
  "pwa_install",
  "pwa_update",
  "reduced_motion",
  "high_contrast",
  "colorblind",
  "text_scale",
];

/** What the settings handler needs from the game controller. */
export interface SettingsInputHost {
  screen: ScreenKind;
  settingsState: SettingsState | null;
  textScale: TextScaleStep;
  reducedMotion: boolean;
  highContrast: boolean;
  colorblindMode: ColorblindMode;
  pwaController: PwaController | null;
  renderer: { setTextScale(scale: number): void };
  draw(): void;
  resizeRenderer(): void;
  /** Lazy audio module, or null when audio is switched off. */
  loadAudio(): Promise<typeof import("../audio/manager") | null>;
}

/** Handle one key on the settings screen. No-op until the audio module loads. */
export function handleSettingsInput(host: SettingsInputHost, action: GameAction): void {
  void host.loadAudio().then(async (audio) => {
    if (!audio) return;
    const manager = audio.AudioManager.getInstance();
    // Ensure defaults are persisted
    if (localStorage.getItem("wetrun_audio_bgm_volume") === null) {
      manager.setBgmVolume(manager.getBgmVolume());
    }
    if (localStorage.getItem("wetrun_audio_sfx_volume") === null) {
      manager.setSfxVolume(manager.getSfxVolume());
    }
    if (host.settingsState === null) {
      host.settingsState = getInitialSettingsState();
    }
    if (host.settingsState.audioEnabled === undefined) {
      host.settingsState = {
        ...host.settingsState,
        audioEnabled: localStorage.getItem("wetrun_audio_off") !== "1",
      };
    }
    const fields = SETTINGS_FIELDS;
    const idx = fields.indexOf(host.settingsState.selectedField);
    if (
      action.type === "cycle_target" ||
      action.type === "move_south" ||
      action.type === "move_north"
    ) {
      const direction = action.type === "move_north" ? -1 : 1;
      const nextIdx = (idx + direction + fields.length) % fields.length;
      const nextField = fields[nextIdx] ?? fields[0];
      if (nextField)
        host.settingsState = {
          ...host.settingsState,
          selectedField: nextField,
        };
      host.draw();
    } else if (action.type === "move_east") {
      if (host.settingsState.selectedField === "master") {
        const v = adjustVolume(host.settingsState.masterVolume ?? 1, "inc");
        host.settingsState = { ...host.settingsState, masterVolume: v };
        manager.setMasterVolume(v);
      } else if (host.settingsState.selectedField === "bgm") {
        const v =
          host.settingsState.bgmVolume + 0.1 > 1
            ? 1
            : Math.round((host.settingsState.bgmVolume + 0.1) * 10) / 10;
        host.settingsState = { ...host.settingsState, bgmVolume: v };
        manager.setBgmVolume(v);
      } else if (host.settingsState.selectedField === "sfx") {
        const v =
          host.settingsState.sfxVolume + 0.1 > 1
            ? 1
            : Math.round((host.settingsState.sfxVolume + 0.1) * 10) / 10;
        host.settingsState = { ...host.settingsState, sfxVolume: v };
        manager.setSfxVolume(v);
      } else if (host.settingsState.selectedField === "text_scale") {
        const next = nextTextScale(host.textScale);
        persistTextScale(next);
        host.textScale = next;
        host.renderer.setTextScale(textScaleFactor(next));
        host.resizeRenderer();
        host.settingsState = { ...host.settingsState, textScale: next };
      }
      host.draw();
    } else if (action.type === "move_west") {
      if (host.settingsState.selectedField === "master") {
        const v = adjustVolume(host.settingsState.masterVolume ?? 1, "dec");
        host.settingsState = { ...host.settingsState, masterVolume: v };
        manager.setMasterVolume(v);
      } else if (host.settingsState.selectedField === "bgm") {
        const v =
          host.settingsState.bgmVolume - 0.1 < 0
            ? 0
            : Math.round((host.settingsState.bgmVolume - 0.1) * 10) / 10;
        host.settingsState = { ...host.settingsState, bgmVolume: v };
        manager.setBgmVolume(v);
      } else if (host.settingsState.selectedField === "sfx") {
        const v =
          host.settingsState.sfxVolume - 0.1 < 0
            ? 0
            : Math.round((host.settingsState.sfxVolume - 0.1) * 10) / 10;
        host.settingsState = { ...host.settingsState, sfxVolume: v };
        manager.setSfxVolume(v);
      } else if (host.settingsState.selectedField === "text_scale") {
        const next = previousTextScale(host.textScale);
        persistTextScale(next);
        host.textScale = next;
        host.renderer.setTextScale(textScaleFactor(next));
        host.resizeRenderer();
        host.settingsState = { ...host.settingsState, textScale: next };
      }
      host.draw();
    } else if (action.type === "confirm") {
      if (host.settingsState.selectedField === "audio") {
        const newEnabled = !host.settingsState.audioEnabled;
        if (newEnabled) {
          localStorage.removeItem("wetrun_audio_off");
        } else {
          localStorage.setItem("wetrun_audio_off", "1");
        }
        host.settingsState = {
          ...host.settingsState,
          audioEnabled: newEnabled,
        };
      } else if (host.settingsState.selectedField === "mute") {
        const muted = manager.toggleMute();
        host.settingsState = { ...host.settingsState, muted };
      } else if (host.settingsState.selectedField === "language") {
        const next = cycleLanguage(host.settingsState.language);
        persistLanguage(next);
        host.settingsState = { ...host.settingsState, language: next };
      } else if (host.settingsState.selectedField === "pwa_install") {
        // ENTER fires the install prompt (user gesture). Only effective
        // when canInstall is true; the controller also clears the
        // deferredPrompt after a successful install.
        if (host.pwaController) {
          void host.pwaController.tryPromptInstall();
        }
      } else if (host.settingsState.selectedField === "pwa_update") {
        // ENTER triggers SKIP_WAITING. Controller sets hasUpdate=false on
        // success; the page should be reloaded to activate the new worker.
        if (host.pwaController) {
          void host.pwaController.tryApplyUpdate();
        }
      } else if (host.settingsState.selectedField === "reduced_motion") {
        // P10 — toggle reduced motion. The override wins over the OS
        // media query in both directions.
        const next = !host.reducedMotion;
        persistReducedMotionOverride(next);
        host.reducedMotion = next;
        host.settingsState = {
          ...host.settingsState,
          reducedMotion: next,
        };
      } else if (host.settingsState.selectedField === "high_contrast") {
        // P10 — toggle the high-contrast palette overrides.
        const next = !host.highContrast;
        persistHighContrastOverride(next);
        host.highContrast = next;
        applyPaletteMode(host.colorblindMode, next);
        host.settingsState = {
          ...host.settingsState,
          highContrast: next,
        };
      } else if (host.settingsState.selectedField === "colorblind") {
        // P10 — cycle the ADR-0196 4-mode colorblind palette.
        const next = nextColorblindMode(host.colorblindMode);
        persistColorblindMode(next);
        host.colorblindMode = next;
        applyPaletteMode(next, host.highContrast);
        host.settingsState = {
          ...host.settingsState,
          colorblindMode: next,
        };
      } else if (host.settingsState.selectedField === "text_scale") {
        // P10 — cycle the text scale and re-derive the cell geometry.
        const next = nextTextScale(host.textScale);
        persistTextScale(next);
        host.textScale = next;
        host.renderer.setTextScale(textScaleFactor(next));
        host.resizeRenderer();
        host.settingsState = {
          ...host.settingsState,
          textScale: next,
        };
      }
      host.draw();
    } else if (action.type === "jack_out") {
      host.screen = "menu";
      host.draw();
    }
  });
}
