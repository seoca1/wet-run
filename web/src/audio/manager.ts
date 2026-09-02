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

const DEFAULT_BGM_VOLUME = 0.4;
const DEFAULT_SFX_VOLUME = 0.6;
/** Default BGM crossfade duration in ms (Python: prototype/audio/bgm_manager.py DEFAULT_CROSSFADE_MS=500). */
const DEFAULT_CROSSFADE_MS = 800;

const STORAGE_KEY_BGM = "wetrun_audio_bgm_volume";
const STORAGE_KEY_SFX = "wetrun_audio_sfx_volume";

function clamp01(v: number): number {
  if (Number.isNaN(v)) return 0;
  if (v < 0) return 0;
  if (v > 1) return 1;
  return v;
}

function readPersistedVolume(key: string, fallback: number): number {
  if (typeof localStorage === "undefined") return fallback;
  try {
    const raw = localStorage.getItem(key);
    if (raw === null) return fallback;
    const parsed = parseFloat(raw);
    if (Number.isNaN(parsed)) return fallback;
    return clamp01(parsed);
  } catch {
    return fallback;
  }
}

function writePersistedVolume(key: string, value: number): void {
  if (typeof localStorage === "undefined") return;
  try {
    localStorage.setItem(key, String(clamp01(value)));
  } catch {
    // ignore — quota exceeded or storage disabled
  }
}

export class AudioManager {
  private howl: Howl | null = null;
  private currentTrack: SoundId | null = null;
  private _muted = false;
  private _started = false;
  private _bgmVolume: number;
  private _sfxVolume: number;
  private readonly sfxHowls: Map<SoundEffectId, Howl> = new Map();

  private constructor(bgmVolume: number, sfxVolume: number) {
    this._bgmVolume = readPersistedVolume(STORAGE_KEY_BGM, bgmVolume);
    this._sfxVolume = readPersistedVolume(STORAGE_KEY_SFX, sfxVolume);
  }

  /** Get or create the singleton. Safe to call repeatedly. */
  static getInstance(): AudioManager {
    if (instance === null) {
      instance = new AudioManager(DEFAULT_BGM_VOLUME, DEFAULT_SFX_VOLUME);
    }
    return instance;
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
        volume: this._bgmVolume,
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
      this.fadeOutAndStop(DEFAULT_CROSSFADE_MS);
      return;
    }
    // Phase 1: ensure current track starts at full volume (fade-in from 0 on first play).
    this.crossfadeTo(track, DEFAULT_CROSSFADE_MS);
  }

  /**
   * Crossfade from the current track to a new one (Tier 7 follow-up).
   * The old track fades out as the new track fades in over `durationMs`.
   * If the new track equals the current one, only a volume-restore happens
   * (idempotent).
   *
   * No-op when Howler construction fails (node test env).
   */
  crossfadeTo(track: SoundId, durationMs: number = DEFAULT_CROSSFADE_MS): void {
    if (track === this.currentTrack && this.howl !== null) {
      // Same track — restore volume if previously faded (e.g. by stop).
      if (!this._started) {
        try {
          this.howl.play();
          this.howl.volume(this._bgmVolume, 0);
          this._started = true;
        } catch {
          // ignore
        }
      } else {
        try {
          this.howl.volume(this._bgmVolume, durationMs);
        } catch {
          // ignore
        }
      }
      return;
    }
    const oldHowl = this.howl;
    const oldTrack = this.currentTrack;
    let newHowl: Howl | null = null;
    try {
      newHowl = new Howl({
        src: [track],
        loop: true,
        volume: 0,
        html5: false,
      });
    } catch {
      return;
    }
    this.howl = newHowl;
    this.currentTrack = track;
    try {
      newHowl.play();
      newHowl.volume(this._bgmVolume, durationMs);
    } catch {
      // ignore
    }
    this._started = true;
    if (oldHowl !== null) {
      const fadeMs = Math.max(0, durationMs);
      try {
        oldHowl.fade(oldHowl.volume(), 0, fadeMs);
      } catch {
        // ignore
      }
      const unloadAfter = (howl: Howl) => {
        try {
          howl.stop();
          howl.unload();
        } catch {
          // ignore
        }
      };
      const timer = setTimeout(() => unloadAfter(oldHowl), Math.max(50, fadeMs + 100));
      if (typeof timer === "object" && timer !== null && "unref" in timer && typeof (timer as { unref?: () => void }).unref === "function") {
        (timer as { unref: () => void }).unref();
      }
      void oldTrack;
    }
  }

  /**
   * Fade out the current BGM and stop playback. Safe no-op if nothing is playing.
   */
  fadeOutAndStop(durationMs: number = DEFAULT_CROSSFADE_MS): void {
    if (this.howl === null) return;
    const target = this.howl;
    try {
      target.fade(target.volume(), 0, Math.max(0, durationMs));
    } catch {
      // ignore
    }
    const timer = setTimeout(() => {
      try {
        target.stop();
      } catch {
        // ignore
      }
      if (this.howl === target) {
        this.howl = null;
        this.currentTrack = null;
        this._started = false;
      }
    }, Math.max(50, durationMs + 100));
    if (typeof timer === "object" && timer !== null && "unref" in timer && typeof (timer as { unref?: () => void }).unref === "function") {
      (timer as { unref: () => void }).unref();
    }
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

  /** BGM volume in 0..1 range. Persisted to localStorage. */
  getBgmVolume(): number {
    return this._bgmVolume;
  }

  /** Set BGM volume (0..1). Clamped. Persisted to localStorage. Applies to current Howl. */
  setBgmVolume(v: number): void {
    this._bgmVolume = clamp01(v);
    writePersistedVolume(STORAGE_KEY_BGM, this._bgmVolume);
    if (this.howl !== null) {
      try {
        this.howl.volume(this._bgmVolume);
      } catch {
        // ignore — Howler may be in a transient state
      }
    }
  }

  /** SFX volume in 0..1 range. Persisted to localStorage. */
  getSfxVolume(): number {
    return this._sfxVolume;
  }

  /** Set SFX volume (0..1). Clamped. Persisted to localStorage. Applies to all cached SFX. */
  setSfxVolume(v: number): void {
    this._sfxVolume = clamp01(v);
    writePersistedVolume(STORAGE_KEY_SFX, this._sfxVolume);
    for (const sfx of this.sfxHowls.values()) {
      try {
        sfx.volume(this._sfxVolume);
      } catch {
        // ignore
      }
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
          volume: this._sfxVolume,
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