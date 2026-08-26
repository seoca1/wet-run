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

/** Available BGM tracks. Tier 2b uses only SENSE_NET. */
export const SOUND_IDS = {
  SENSE_NET: "sounds/theme_sense_net.mp3",
} as const;

export type SoundId = (typeof SOUND_IDS)[keyof typeof SOUND_IDS];

/** Singleton state. Lazily initialized on first getInstance() call. */
let instance: AudioManager | null = null;

/** AudioManager singleton. Audio playback for wet_run-web. */
export class AudioManager {
  private howl: Howl | null = null;
  private _muted = false;
  private _started = false;
  private readonly volume: number;

  private constructor(volume: number) {
    this.volume = volume;
  }

  /** Get or create the singleton. Safe to call repeatedly. */
  static getInstance(): AudioManager {
    if (instance === null) {
      instance = new AudioManager(0.4);
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
   * Begin BGM playback. Lazy-creates the Howl instance on first call.
   * No-op in non-browser environments (jsdom test).
   */
  play(track: SoundId = SOUND_IDS.SENSE_NET): void {
    if (this.howl === null) {
      try {
        this.howl = new Howl({
          src: [track],
          loop: true,
          volume: this.volume,
          html5: false,
        });
      } catch {
        // Howler construction failed (likely node test env). Mark unavailable.
        return;
      }
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