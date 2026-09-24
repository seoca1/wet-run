/** AudioManager — wet_run-web BGM playback (Tier 2b).
 *
 * Wraps Howler.js with a singleton API. Howler is dynamically imported
 * on first use so the module is import-safe in node/jsdom test environments
 * and doesn't trigger the HTML5 audio pool creation on bigme Chrome.
 */

import type { Howl as HowlType } from "howler";

export const BGM_IDS = {
  TITLE: "sounds/bgm/title.wav",
  MENU: "sounds/bgm/menu.wav",
  EXPLORATION: "sounds/bgm/exploration.wav",
  COMBAT_NORMAL: "sounds/bgm/combat_normal.wav",
  COMBAT_BOSS: "sounds/bgm/combat_boss.wav",
  COMBAT_MULTI: "sounds/bgm/combat_multi.wav",
  SHOP: "sounds/bgm/shop.wav",
  ENDING_GOOD: "sounds/bgm/ending_good.wav",
  ENDING_BAD: "sounds/bgm/ending_bad.wav",
  ENDING_NEUTRAL: "sounds/bgm/ending_neutral.wav",
  DEATH: "sounds/bgm/death.wav",
  VICTORY: "sounds/bgm/victory.wav",
  EVENT_SPECIAL: "sounds/bgm/event_special.wav",
  AMBIENT_LOW: "sounds/bgm/ambient_low.wav",
  AMBIENT_HIGH: "sounds/bgm/ambient_high.wav",
  CHIBA: "sounds/theme_chiba.mp3",
  SENSE_NET: "sounds/theme_sense_net.mp3",
  MATRIX_RAIN: "sounds/theme_matrix_rain.mp3",
  BROADCAST: "sounds/theme_broadcast.mp3",
  INDUSTRIAL: "sounds/theme_industrial.mp3",
} as const;

export const SFX_IDS = {
  CLICK: "sounds/sfx/click.wav",
  CONFIRM: "sounds/sfx/confirm.wav",
  BACK: "sounds/sfx/back.wav",
  EQUIP: "sounds/sfx/equip.wav",
  HEAL: "sounds/sfx/heal.wav",
  DAMAGE: "sounds/sfx/damage.wav",
  ATTACK: "sounds/sfx/attack.wav",
  ICE_BREAK: "sounds/sfx/ice_break.wav",
  LOOT_DROP: "sounds/sfx/loot_drop.wav",
  CREDIT_GAIN: "sounds/sfx/credit_gain.wav",
  CREDIT_SPEND: "sounds/sfx/credit_spend.wav",
  DEATH: "sounds/sfx/death.wav",
  VICTORY: "sounds/sfx/victory.wav",
  BOSS_INTRO: "sounds/sfx/boss_intro.wav",
  PHASE_CHANGE: "sounds/sfx/phase_change.wav",
  COMBAT_HIT: "sounds/sfx_combat_hit.wav",
  DEFEAT: "sounds/sfx_defeat.wav",
} as const;

export type SoundId = (typeof BGM_IDS)[keyof typeof BGM_IDS];
export type SoundEffectId = (typeof SFX_IDS)[keyof typeof SFX_IDS];

const PHASE_TO_SOUND: Readonly<Record<string, SoundId | null>> = {
  menu: BGM_IDS.MENU,
  approach: BGM_IDS.EXPLORATION,
  combat: BGM_IDS.COMBAT_NORMAL,
  victory: BGM_IDS.VICTORY,
  defeat: BGM_IDS.DEATH,
  exit: null,
};

let instance: AudioManager | null = null;

const DEFAULT_BGM_VOLUME = 0.4;
const DEFAULT_SFX_VOLUME = 0.6;
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

// Lazy-loaded Howl constructor
let HowlCtor: typeof HowlType | null = null;

async function getHowl(): Promise<typeof HowlType> {
  if (HowlCtor) return HowlCtor;
  const mod = await import("howler");
  HowlCtor = mod.Howl;
  return HowlCtor;
}

// Lazy-loaded sound_system module
let soundSystemModule: typeof import("../core/sound_system.ts") | null = null;

async function getSoundSystem(): Promise<typeof import("../core/sound_system.ts")> {
  if (soundSystemModule) return soundSystemModule;
  soundSystemModule = await import("../core/sound_system.ts");
  return soundSystemModule;
}

export class AudioManager {
  private howl: HowlType | null = null;
  private currentTrack: SoundId | null = null;
  private _muted = false;
  private _started = false;
  private _bgmVolume: number;
  private _sfxVolume: number;
  private readonly sfxHowls: Map<SoundEffectId, HowlType> = new Map();

  private constructor(bgmVolume: number, sfxVolume: number) {
    this._bgmVolume = readPersistedVolume(STORAGE_KEY_BGM, bgmVolume);
    this._sfxVolume = readPersistedVolume(STORAGE_KEY_SFX, sfxVolume);
    if (typeof localStorage !== "undefined") {
      if (localStorage.getItem(STORAGE_KEY_BGM) === null) {
        writePersistedVolume(STORAGE_KEY_BGM, this._bgmVolume);
      }
      if (localStorage.getItem(STORAGE_KEY_SFX) === null) {
        writePersistedVolume(STORAGE_KEY_SFX, this._sfxVolume);
      }
    }
  }

  static getInstance(): AudioManager {
    if (instance === null) {
      instance = new AudioManager(DEFAULT_BGM_VOLUME, DEFAULT_SFX_VOLUME);
    }
    return instance;
  }

  static resetForTesting(): void {
    if (instance !== null && instance.howl !== null) {
      try {
        instance.howl.unload();
      } catch {
        // ignore
      }
    }
    instance = null;
  }

  /**
   * Begin BGM playback for the given track. Howler is dynamically imported on first call.
   */
  async play(track: SoundId = BGM_IDS.MENU): Promise<void> {
    const [Howl, ss] = await Promise.all([getHowl(), getSoundSystem()]);
    const trackInfo = ss.TRACKS[track as keyof typeof ss.TRACKS];
    const finalVolume = trackInfo
      ? ss.calculateVolume(track as Parameters<typeof ss.calculateVolume>[0], this._bgmVolume)
      : this._bgmVolume;

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
        loop: trackInfo?.loop ?? true,
        volume: finalVolume,
        html5: false,
      });
      this.currentTrack = track;
    } catch {
      return;
    }

    if (!this._started) {
      try {
        this.howl.play();
        this._started = true;
      } catch {
        // ignore
      }
    }
  }

  async playPhase(phase: string): Promise<void> {
    const track = PHASE_TO_SOUND[phase];
    if (track === undefined) return;
    if (track === null) {
      this.fadeOutAndStop(DEFAULT_CROSSFADE_MS);
      return;
    }
    await this.crossfadeTo(track, DEFAULT_CROSSFADE_MS);
  }

  async crossfadeTo(track: SoundId, durationMs: number = DEFAULT_CROSSFADE_MS): Promise<void> {
    if (track === this.currentTrack && this.howl !== null) {
      if (!this._started) {
        try {
          this.howl.play();
          this.howl.volume(this._bgmVolume);
          this._started = true;
        } catch {
          // ignore
        }
      } else {
        try {
          this.howl.fade(this.howl.volume(), this._bgmVolume, durationMs);
        } catch {
          // ignore
        }
      }
      return;
    }

    const Howl = await getHowl();
    const oldHowl = this.howl;

    let newHowl: HowlType | null = null;
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
      newHowl.fade(0, this._bgmVolume, durationMs);
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
      setTimeout(() => {
        try {
          oldHowl.stop();
          oldHowl.unload();
        } catch {
          // ignore
        }
      }, fadeMs + 100);
    }
  }

  fadeOutAndStop(durationMs: number = DEFAULT_CROSSFADE_MS): void {
    if (this.howl === null) return;
    const target = this.howl;
    try {
      target.fade(target.volume(), 0, Math.max(0, durationMs));
    } catch {
      // ignore
    }
    setTimeout(() => {
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
    }, durationMs + 100);
  }

  getCurrentTrack(): SoundId | null {
    return this.currentTrack;
  }

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

  getBgmVolume(): number {
    return this._bgmVolume;
  }

  setBgmVolume(v: number): void {
    this._bgmVolume = clamp01(v);
    writePersistedVolume(STORAGE_KEY_BGM, this._bgmVolume);
    if (this.howl !== null) {
      try {
        this.howl.volume(this._bgmVolume);
      } catch {
        // ignore
      }
    }
  }

  getSfxVolume(): number {
    return this._sfxVolume;
  }

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

  async playSfx(id: SoundEffectId = SFX_IDS.CLICK): Promise<void> {
    const Howl = await getHowl();
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

  stopAllSfx(): void {
    for (const sfx of this.sfxHowls.values()) {
      try {
        sfx.stop();
      } catch {
        // ignore
      }
    }
  }

  static unlockOnFirstGesture(onUnlock?: () => void): void {
    if (typeof document === "undefined") return;
    const events: Array<keyof DocumentEventMap> = ["click", "keydown", "touchstart"];
    const handler = (): void => {
      events.forEach((e) => document.removeEventListener(e, handler));
      if (onUnlock) onUnlock();
    };
    events.forEach((e) => document.addEventListener(e, handler, { once: true }));
  }

  async playBgmForEvent(event: string): Promise<string | null> {
    const ss = await getSoundSystem();
    type BgmTrackId = Parameters<typeof ss.shouldTransition>[0];
    const currentTrack = this.currentTrack as BgmTrackId;
    const transition = ss.shouldTransition(currentTrack, event);
    if (transition) {
      await this.crossfadeTo(transition.track as SoundId);
      return transition.track as string;
    }
    return this.currentTrack as string | null;
  }
}
