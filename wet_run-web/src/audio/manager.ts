/** AudioManager — wet_run-web BGM playback (Tier 2b).
 *
 * Wraps Howler.js with a singleton API. Lazy-loads Howl on first use so the
 * module is import-safe in node/jsdom test environments (where `Howl`
 * would fail to construct because the audio element is browser-only).
 *
 * Browser auto-unlock: Howler requires a user gesture before playback.
 * `unlockOnFirstGesture()` attaches one-shot listeners on the document
 * that will resume audio after the first click/keydown/touchstart.
 *
 * Scope (Tier 2b Minimal MVP):
 * - Single BGM (theme_sense_net) played during menu + combat phases
 * - Mute toggle via M key (caller-side keybinding)
 * - Default volume 0.4 (Gibson atmosphere, not intrusive)
 *
 * Out of scope (Tier 3+ candidates):
 * - Phase-based track switching (menu vs combat)
 * - SFX (combat_hit, victory, defeat)
 * - Volume slider UI
 * - Per-track fade in/out
 * - Audio sprite optimization
 *
 * See ADR-0201 for the decision rationale.
 */

import { Howl } from "howler";

export const BGM_IDS = {
  CHIBA: "sounds/theme_chiba.mp3",
  SENSE_NET: "sounds/theme_sense_net.mp3",
  MATRIX_RAIN: "sounds/theme_matrix_rain.mp3",
  BROADCAST: "sounds/theme_broadcast.mp3",
  INDUSTRIAL: "sounds/theme_industrial.mp3",
} as const;

export const SFX_IDS = {
  COMBAT_HIT: "sounds/sfx_combat_hit.wav",
  VICTORY: "sounds/sfx_victory.wav",
  DEFEAT: "sounds/sfx_defeat.wav",
  COMBAT_BLOCK: "sounds/sfx_combat_block.wav",
  SKILL_STRIKE: "sounds/sfx_skill_strike.wav",
  SKILL_HAMMER: "sounds/sfx_skill_hammer.wav",
  SKILL_VIRUS: "sounds/sfx_skill_virus.wav",
  SKILL_WARDRONE: "sounds/sfx_skill_wardrone.wav",
  MOVEMENT_NODE: "sounds/sfx_movement.wav",
  UI_SELECT: "sounds/sfx_ui_select.wav",
  UI_CONFIRM: "sounds/sfx_ui_confirm.wav",
  UI_CANCEL: "sounds/sfx_ui_cancel.wav",
  ALARM_TICK: "sounds/sfx_alarm.wav",
  BURN_TICK: "sounds/sfx_burn.wav",
} as const;

export type SoundId = (typeof BGM_IDS)[keyof typeof BGM_IDS];
export type SoundEffectId = (typeof SFX_IDS)[keyof typeof SFX_IDS];

const PHASE_TO_SOUND: Readonly<Record<string, SoundId | null>> = {
  menu: BGM_IDS.CHIBA,
  approach: BGM_IDS.SENSE_NET,
  combat: BGM_IDS.MATRIX_RAIN,
  victory: BGM_IDS.BROADCAST,
  defeat: BGM_IDS.INDUSTRIAL,
  exit: null,
};

let instance: AudioManager | null = null;

export class AudioManager {
  private howl: Howl | null = null;
  private currentTrack: SoundId | null = null;
  private _muted = false;
  private _started = false;
  private _volume: number;
  private _masterVolume: number;
  private readonly sfxHowls: Map<SoundEffectId, Howl> = new Map();
  private _sfxVolume: number;

  private constructor(volume: number, sfxVolume: number, masterVolume: number) {
    this._volume = volume;
    this._sfxVolume = sfxVolume;
    this._masterVolume = masterVolume;
  }

  /** Get or create the singleton. Safe to call repeatedly. */
  static getInstance(): AudioManager {
    if (instance === null) {
      // Load persisted volumes or use defaults
      let bgmVol = 0.4;
      let sfxVol = 0.6;
      let masterVol = 1.0;
      if (typeof window !== "undefined") {
        try {
          const saved = localStorage.getItem("wetrun_audio_volumes");
          if (saved) {
            const parsed = JSON.parse(saved);
            bgmVol = parsed.bgmVolume ?? 0.4;
            sfxVol = parsed.sfxVolume ?? 0.6;
            masterVol = parsed.masterVolume ?? 1.0;
          }
        } catch {
          // ignore localStorage errors
        }
      }
      instance = new AudioManager(bgmVol, sfxVol, masterVol);
    }
    return instance;
  }

  /** Get current BGM volume (0.0 - 1.0). */
  getBgmVolume(): number {
    return this._volume;
  }

  /** Set BGM volume (0.0 - 1.0), applies to current Howl if playing. */
  setBgmVolume(v: number): void {
    const clamped = Math.max(0, Math.min(1, v));
    this._volume = clamped;
    if (this.howl !== null) {
      try {
        this.howl.volume(clamped * this._masterVolume);
      } catch {
        // ignore
      }
    }
    this.persistVolumes();
  }

  /** Get current SFX volume (0.0 - 1.0). */
  getSfxVolume(): number {
    return this._sfxVolume;
  }

  /** Set SFX volume (0.0 - 1.0), applies to all cached SFX Howls. */
  setSfxVolume(v: number): void {
    const clamped = Math.max(0, Math.min(1, v));
    this._sfxVolume = clamped;
    for (const sfx of this.sfxHowls.values()) {
      try {
        sfx.volume(clamped * this._masterVolume);
      } catch {
        // ignore
      }
    }
    this.persistVolumes();
  }

  /** Get current master volume (0.0 - 1.0). */
  getMasterVolume(): number {
    return this._masterVolume;
  }

  /** Set master volume (0.0 - 1.0), applies to both BGM and SFX. */
  setMasterVolume(v: number): void {
    const clamped = Math.max(0, Math.min(1, v));
    this._masterVolume = clamped;
    if (this.howl !== null) {
      try {
        this.howl.volume(this._volume * clamped);
      } catch {
        // ignore
      }
    }
    for (const sfx of this.sfxHowls.values()) {
      try {
        sfx.volume(this._sfxVolume * clamped);
      } catch {
        // ignore
      }
    }
    this.persistVolumes();
  }

  /** Persist volumes to localStorage. */
  private persistVolumes(): void {
    if (typeof window !== "undefined") {
      try {
        localStorage.setItem("wetrun_audio_volumes", JSON.stringify({
          bgmVolume: this._volume,
          sfxVolume: this._sfxVolume,
          masterVolume: this._masterVolume,
        }));
      } catch {
        // ignore localStorage errors
      }
    }
  }

  /** Test-only: reset singleton between tests. */
  static resetForTesting(): void {
    if (instance !== null && instance.howl !== null) {
      try {
        instance.howl.unload();
      } catch {
        // ignore — Howler may already be disposed
      }
    }
    instance = null;
  }

  /**
   * Begin BGM playback for the given track. If the track differs from
   * the current one, the previous Howl is unloaded and a new one is
   * created. Lazy-creates Howl on first call. No-op in jsdom/node.
   */
  play(track: SoundId = BGM_IDS.SENSE_NET): void {
    if (this.currentTrack === track && this.howl !== null) {
      if (!this._started) {
        try {
          this.howl.play();
          this._started = true;
        } catch {
          // ignore
        }
      }
      return;
    }
    if (this.howl !== null) {
      try {
        this.howl.unload();
      } catch {
        // ignore
      }
      this.howl = null;
      this._started = false;
    }
    try {
      this.howl = new Howl({
        src: [track],
        loop: true,
        volume: this._volume * this._masterVolume,
        html5: false,
      });
      this.currentTrack = track;
    } catch {
      // Howler construction failed (likely node test env). Mark unavailable.
      return;
    }
    if (!this._started) {
      try {
        const soundId = this.howl.play();
        this._started = true;
        void soundId;
      } catch {
        // ignore — browser audio unlock may still be pending
      }
    }
  }

  /**
   * Play BGM matching a GamePhase value. No-op when the same phase
   * is already active. "exit" phase stops playback.
   */
  playPhase(phase: string): void {
    const track = PHASE_TO_SOUND[phase];
    if (track === undefined) {
      return;
    }
    if (track === null) {
      this.stop();
      return;
    }
    this.play(track);
  }

  getCurrentTrack(): SoundId | null {
    return this.currentTrack;
  }

  /** Pause playback but keep the Howl loaded. */
  stop(): void {
    if (this.howl !== null && this._started) {
      try {
        this.howl.pause();
      } catch {
        // ignore
      }
    }
    this._started = false;
  }

  /** Mute without stopping. BGM continues at volume 0. */
  mute(): void {
    this._muted = true;
    if (this.howl !== null) {
      try {
        this.howl.mute(true);
      } catch {
        // ignore
      }
    }
    for (const sfx of this.sfxHowls.values()) {
      try {
        sfx.mute(true);
      } catch {
        // ignore
      }
    }
  }

  /** Unmute and restore prior volume. */
  unmute(): void {
    this._muted = false;
    if (this.howl !== null) {
      try {
        this.howl.mute(false);
      } catch {
        // ignore
      }
    }
    for (const sfx of this.sfxHowls.values()) {
      try {
        sfx.mute(false);
      } catch {
        // ignore
      }
    }
  }

  /** Toggle mute state. Returns the new muted state. */
  toggleMute(): boolean {
    if (this._muted) {
      this.unmute();
    } else {
      this.mute();
    }
    return this._muted;
  }

  isMuted(): boolean {
    return this._muted;
  }

  isPlaying(): boolean {
    if (this.howl === null) return false;
    try {
      return this.howl.playing();
    } catch {
      return false;
    }
  }

  /**
   * Play a one-shot sound effect. Howler instances are cached per
   * SoundEffectId so repeated calls reuse the same buffer. Multiple
   * plays of the same id overlap (Howler internal mix). Respects mute.
   */
  playSfx(id: SoundEffectId = SFX_IDS.COMBAT_HIT): void {
    let howl = this.sfxHowls.get(id);
    if (howl === undefined) {
      try {
        howl = new Howl({
          src: [id],
          loop: false,
          volume: this._sfxVolume * this._masterVolume,
          html5: false,
        });
        this.sfxHowls.set(id, howl);
      } catch {
        return;
      }
    }
    try {
      howl.play();
      if (this._muted) {
        howl.mute(true);
      }
    } catch {
      // ignore
    }
  }

  /** Stop every active SFX. */
  stopAllSfx(): void {
    for (const sfx of this.sfxHowls.values()) {
      try {
        sfx.stop();
      } catch {
        // ignore
      }
    }
  }

  /**
   * Browser audio unlock — Howler requires a user gesture before playback
   * is allowed. Call this once on app boot; it will attach one-shot
   * listeners that fire on the first click/keydown/touchstart and then
   * detach themselves.
   */
  static unlockOnFirstGesture(onUnlock?: () => void): void {
    if (typeof document === "undefined") return;
    const events: Array<keyof DocumentEventMap> = [
      "click",
      "keydown",
      "touchstart",
    ];
    const handler = (): void => {
      events.forEach((e) => document.removeEventListener(e, handler));
      if (onUnlock) onUnlock();
    };
    events.forEach((e) => document.addEventListener(e, handler, { once: true }));
  }
}