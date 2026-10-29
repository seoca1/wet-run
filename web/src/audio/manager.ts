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
  COMBAT_BLOCK: "sounds/sfx/combat_block.wav",
  COMBAT_SKILL_STRIKE: "sounds/sfx/combat_skill_strike.wav",
  COMBAT_SKILL_BURST: "sounds/sfx/combat_skill_burst.wav",
  COMBAT_SKILL_GUARD: "sounds/sfx/combat_skill_guard.wav",
  COMBAT_SKILL_SUPPORT: "sounds/sfx/combat_skill_support.wav",
  MOVEMENT_STEP: "sounds/sfx/movement_step.wav",
  MOVEMENT_NODE: "sounds/sfx/movement_node.wav",
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

/** SFX ids that should duck the BGM while they sound.
 *
 * Only combat-impact sounds count — UI clicks and movement steps ducking
 * the music would feel like a stutter, not like emphasis.
 */
export const COMBAT_SFX_IDS: ReadonlySet<SoundEffectId> =
  new Set<SoundEffectId>([
    SFX_IDS.COMBAT_HIT,
    SFX_IDS.ATTACK,
    SFX_IDS.DAMAGE,
    SFX_IDS.ICE_BREAK,
    SFX_IDS.COMBAT_BLOCK,
    SFX_IDS.COMBAT_SKILL_STRIKE,
    SFX_IDS.COMBAT_SKILL_BURST,
    SFX_IDS.COMBAT_SKILL_GUARD,
    SFX_IDS.COMBAT_SKILL_SUPPORT,
  ]);

let instance: AudioManager | null = null;

const DEFAULT_BGM_VOLUME = 0.4;
const DEFAULT_SFX_VOLUME = 0.6;
export const DEFAULT_MASTER_VOLUME = 1.0;
const DEFAULT_CROSSFADE_MS = 800;

/** BGM volume multiplier while a combat SFX is sounding. */
export const BGM_DUCK_FACTOR = 0.8;
/** Time the BGM takes to reach the full duck factor. */
export const BGM_DUCK_ATTACK_MS = 60;
/** Time the BGM stays at the full duck factor. */
export const BGM_DUCK_HOLD_MS = 120;
/** Time the BGM takes to return to its normal (un-ducked) volume. */
export const BGM_DUCK_RELEASE_MS = 240;

/** Howler playback-rate bounds. */
const MIN_SFX_RATE = 0.5;
const MAX_SFX_RATE = 4.0;

const STORAGE_KEY_BGM = "wetrun_audio_bgm_volume";
const STORAGE_KEY_SFX = "wetrun_audio_sfx_volume";
const STORAGE_KEY_MASTER = "wetrun_audio_master_volume";

function clamp01(v: number): number {
  if (Number.isNaN(v)) return 0;
  if (v < 0) return 0;
  if (v > 1) return 1;
  return v;
}

/**
 * Compose the effective BGM volume.
 *
 * `duck` is a multiplicative offset (1 = no ducking) — it is never written
 * to storage, so a duck can not pollute the persisted BGM setting.
 */
export function composeBgmVolume(
  master: number,
  bgm: number,
  trackVolume: number,
  duck: number = 1,
): number {
  if (Number.isNaN(master) || Number.isNaN(bgm)) return 0;
  if (Number.isNaN(trackVolume) || Number.isNaN(duck)) return 0;
  return clamp01(master * bgm * trackVolume * duck);
}

/** Compose the effective SFX volume (master × sfx). */
export function composeSfxVolume(master: number, sfx: number): number {
  if (Number.isNaN(master) || Number.isNaN(sfx)) return 0;
  return clamp01(master * sfx);
}

/**
 * The BGM ducking envelope.
 *
 * `elapsedMs` is the time since the duck was armed; a negative value (or
 * a duration of 0) means nothing is playing and no ducking happens.
 * The envelope ramps down over the attack window, holds, then ramps back up.
 */
export function duckFactorFor(
  elapsedMs: number,
  durationMs: number = BGM_DUCK_ATTACK_MS +
    BGM_DUCK_HOLD_MS +
    BGM_DUCK_RELEASE_MS,
): number {
  if (durationMs <= 0) return 1;
  if (Number.isNaN(elapsedMs) || elapsedMs < 0) return 1;
  if (elapsedMs >= durationMs) return 1;
  if (elapsedMs < BGM_DUCK_ATTACK_MS) {
    const t = elapsedMs / BGM_DUCK_ATTACK_MS;
    return 1 + (BGM_DUCK_FACTOR - 1) * t;
  }
  const holdEnd = BGM_DUCK_ATTACK_MS + BGM_DUCK_HOLD_MS;
  if (elapsedMs < holdEnd) return BGM_DUCK_FACTOR;
  const releaseT = (elapsedMs - holdEnd) / BGM_DUCK_RELEASE_MS;
  return BGM_DUCK_FACTOR + (1 - BGM_DUCK_FACTOR) * releaseT;
}

/** Clamp a playback rate into the range Howler accepts. */
export function clampRate(rate: number): number {
  if (Number.isNaN(rate)) return 1;
  if (rate < MIN_SFX_RATE) return MIN_SFX_RATE;
  if (rate > MAX_SFX_RATE) return MAX_SFX_RATE;
  return rate;
}

/** Whether the given SFX id should duck the BGM. */
export function isCombatSfxId(id: SoundEffectId): boolean {
  return COMBAT_SFX_IDS.has(id);
}

/** Options accepted by {@link AudioManager.playSfx}. */
export interface PlaySfxOptions {
  /** Playback rate / pitch multiplier (Howler `rate()`). 1 = unchanged. */
  readonly rate?: number;
  /** Set to false to skip the BGM duck for this sound. Defaults to true. */
  readonly duck?: boolean;
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

async function getSoundSystem(): Promise<
  typeof import("../core/sound_system.ts")
> {
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
  private _masterVolume: number;
  private readonly sfxHowls: Map<SoundEffectId, HowlType> = new Map();
  private _duckArmed = false;
  private _duckElapsedMs = 0;
  private _duckStartedAtMs = 0;
  private _duckDurationMs =
    BGM_DUCK_ATTACK_MS + BGM_DUCK_HOLD_MS + BGM_DUCK_RELEASE_MS;

  private constructor(
    bgmVolume: number,
    sfxVolume: number,
    masterVolume: number,
  ) {
    this._bgmVolume = readPersistedVolume(STORAGE_KEY_BGM, bgmVolume);
    this._sfxVolume = readPersistedVolume(STORAGE_KEY_SFX, sfxVolume);
    this._masterVolume = readPersistedVolume(STORAGE_KEY_MASTER, masterVolume);
    if (typeof localStorage !== "undefined") {
      if (localStorage.getItem(STORAGE_KEY_BGM) === null) {
        writePersistedVolume(STORAGE_KEY_BGM, this._bgmVolume);
      }
      if (localStorage.getItem(STORAGE_KEY_SFX) === null) {
        writePersistedVolume(STORAGE_KEY_SFX, this._sfxVolume);
      }
      if (localStorage.getItem(STORAGE_KEY_MASTER) === null) {
        writePersistedVolume(STORAGE_KEY_MASTER, this._masterVolume);
      }
    }
  }

  static getInstance(): AudioManager {
    if (instance === null) {
      instance = new AudioManager(
        DEFAULT_BGM_VOLUME,
        DEFAULT_SFX_VOLUME,
        DEFAULT_MASTER_VOLUME,
      );
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
      ? composeBgmVolume(
          this._masterVolume,
          this._bgmVolume,
          trackInfo.volume,
          this.getDuckFactor(),
        )
      : composeBgmVolume(
          this._masterVolume,
          this._bgmVolume,
          1,
          this.getDuckFactor(),
        );

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

  async crossfadeTo(
    track: SoundId,
    durationMs: number = DEFAULT_CROSSFADE_MS,
  ): Promise<void> {
    if (track === this.currentTrack && this.howl !== null) {
      const currentVolume = this.getEffectiveBgmVolume();
      if (!this._started) {
        try {
          this.howl.play();
          this.howl.volume(currentVolume);
          this._started = true;
        } catch {
          // ignore
        }
      } else {
        try {
          this.howl.fade(this.howl.volume(), currentVolume, durationMs);
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
      newHowl.fade(0, this.getEffectiveBgmVolume(), durationMs);
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
    this.applyBgmVolume();
  }

  getSfxVolume(): number {
    return this._sfxVolume;
  }

  setSfxVolume(v: number): void {
    this._sfxVolume = clamp01(v);
    writePersistedVolume(STORAGE_KEY_SFX, this._sfxVolume);
    this.applySfxVolumes();
  }

  getMasterVolume(): number {
    return this._masterVolume;
  }

  setMasterVolume(v: number): void {
    this._masterVolume = clamp01(v);
    writePersistedVolume(STORAGE_KEY_MASTER, this._masterVolume);
    this.applyBgmVolume();
    this.applySfxVolumes();
  }

  /** The BGM volume actually applied to Howler (master × bgm × track × duck). */
  getEffectiveBgmVolume(): number {
    const trackVolume = this.getCurrentTrackVolume();
    return composeBgmVolume(
      this._masterVolume,
      this._bgmVolume,
      trackVolume,
      this.getDuckFactor(),
    );
  }

  /** The SFX volume actually applied to Howler (master × sfx). */
  getEffectiveSfxVolume(): number {
    return composeSfxVolume(this._masterVolume, this._sfxVolume);
  }

  /** The current ducking multiplier (1 = BGM at its normal level). */
  getDuckFactor(): number {
    if (!this._duckArmed) return 1;
    const elapsed = this.duckElapsedMs();
    if (elapsed >= this._duckDurationMs) return 1;
    return duckFactorFor(elapsed);
  }

  /** Whether the BGM is currently ducked by a combat SFX. */
  isDucking(): boolean {
    return this.getDuckFactor() < 1;
  }

  /**
   * Advance the ducking clock by `deltaMs` and re-apply the BGM volume.
   * The game loop calls this each frame so the duck envelope releases
   * without needing a timer.
   */
  advanceDuckingClock(deltaMs: number): void {
    if (!this._duckArmed) return;
    this._duckElapsedMs += Math.max(0, deltaMs);
    if (this._duckElapsedMs >= this._duckDurationMs) {
      this.clearDuck();
      return;
    }
    this.applyBgmVolume();
  }

  private duckElapsedMs(): number {
    const wall = this.now() - this._duckStartedAtMs;
    return Math.max(this._duckElapsedMs, wall);
  }

  private now(): number {
    if (
      typeof performance !== "undefined" &&
      typeof performance.now === "function"
    ) {
      return performance.now();
    }
    return Date.now();
  }

  private getCurrentTrackVolume(): number {
    const track = this.currentTrack;
    if (track === null) return 1;
    const ss = soundSystemModule;
    if (ss === null) return 1;
    const info = ss.TRACKS[track as keyof typeof ss.TRACKS];
    return info?.volume ?? 1;
  }

  private applyBgmVolume(): void {
    if (this.howl === null) return;
    const volume = this.getEffectiveBgmVolume();
    try {
      this.howl.volume(volume);
    } catch {
      // ignore
    }
  }

  private applySfxVolumes(): void {
    const volume = this.getEffectiveSfxVolume();
    for (const sfx of this.sfxHowls.values()) {
      try {
        sfx.volume(volume);
      } catch {
        // ignore
      }
    }
  }

  private armDuck(): void {
    this._duckArmed = true;
    this._duckStartedAtMs = this.now();
    this._duckElapsedMs = 0;
    this.applyBgmVolume();
  }

  private clearDuck(): void {
    if (!this._duckArmed) return;
    this._duckArmed = false;
    this._duckElapsedMs = 0;
    this._duckStartedAtMs = 0;
    this.applyBgmVolume();
  }

  async playSfx(
    id: SoundEffectId = SFX_IDS.CLICK,
    options?: PlaySfxOptions,
  ): Promise<void> {
    const Howl = await getHowl();
    const rate = clampRate(options?.rate ?? 1);
    let howl = this.sfxHowls.get(id);
    if (howl === undefined) {
      try {
        howl = new Howl({
          src: [id],
          loop: false,
          volume: this.getEffectiveSfxVolume(),
          html5: false,
        });
        this.sfxHowls.set(id, howl);
      } catch {
        return;
      }
    }
    try {
      howl.rate(rate);
      howl.volume(this.getEffectiveSfxVolume());
      howl.play();
      if (this._muted) {
        howl.mute(true);
      }
    } catch {
      // ignore
    }
    const shouldDuck = options?.duck ?? true;
    if (shouldDuck && isCombatSfxId(id)) {
      this.armDuck();
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
    this.clearDuck();
  }

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
    events.forEach((e) =>
      document.addEventListener(e, handler, { once: true }),
    );
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
