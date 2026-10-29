/** P13 — audio ducking + SFX rate/pitch + master volume.
 *
 * Covers the *pure* half of the feature so it can be verified without an
 * AudioContext (jsdom has no Web Audio implementation — `new Howl()` may
 * fail silently, so the runtime half is only observable in a browser).
 *
 * Pure surface under test:
 * - `composeBgmVolume` — master × bgm × track × duck
 * - `composeSfxVolume` — master × sfx
 * - `duckFactorFor` — the ducking envelope (attack / hold / release)
 * - `clampRate` — Howler playback-rate clamp
 * - `isCombatSfxId` — which SFX ids count as "combat" for ducking
 *
 * Plus the AudioManager state surface (master volume + duck bookkeeping),
 * which is deterministic and observable without audio hardware.
 */
import { describe, it, expect, beforeEach } from "vitest";
import {
  AudioManager,
  SFX_IDS,
  composeBgmVolume,
  composeSfxVolume,
  duckFactorFor,
  clampRate,
  isCombatSfxId,
  BGM_DUCK_FACTOR,
  BGM_DUCK_ATTACK_MS,
  BGM_DUCK_HOLD_MS,
  BGM_DUCK_RELEASE_MS,
  DEFAULT_MASTER_VOLUME,
} from "../src/audio/manager.js";

describe("composeBgmVolume", () => {
  it("multiplies master × bgm × track volume", () => {
    expect(composeBgmVolume(1, 0.5, 0.8)).toBeCloseTo(0.4, 10);
  });

  it("applies the duck factor as a multiplicative offset", () => {
    expect(composeBgmVolume(1, 0.5, 1, 0.8)).toBeCloseTo(0.4, 10);
  });

  it("returns 0 when master volume is 0", () => {
    expect(composeBgmVolume(0, 1, 1)).toBe(0);
  });

  it("returns 0 when bgm volume is 0", () => {
    expect(composeBgmVolume(1, 0, 1)).toBe(0);
  });

  it("clamps the result into [0,1]", () => {
    expect(composeBgmVolume(1, 1, 1)).toBe(1);
    expect(composeBgmVolume(2, 2, 2)).toBe(1);
  });

  it("returns 0 for NaN inputs", () => {
    expect(composeBgmVolume(Number.NaN, 1, 1)).toBe(0);
  });

  it("never exceeds 1 even with a duck factor > 1", () => {
    expect(composeBgmVolume(1, 1, 1, 4)).toBe(1);
  });
});

describe("composeSfxVolume", () => {
  it("multiplies master × sfx", () => {
    expect(composeSfxVolume(1, 0.6)).toBeCloseTo(0.6, 10);
  });

  it("scales with the master volume", () => {
    expect(composeSfxVolume(0.5, 0.6)).toBeCloseTo(0.3, 10);
  });

  it("returns 0 when master volume is 0", () => {
    expect(composeSfxVolume(0, 1)).toBe(0);
  });

  it("clamps the result into [0,1]", () => {
    expect(composeSfxVolume(1, 1)).toBe(1);
    expect(composeSfxVolume(2, 2)).toBe(1);
  });

  it("returns 0 for NaN inputs", () => {
    expect(composeSfxVolume(Number.NaN, 1)).toBe(0);
  });
});

describe("duckFactorFor", () => {
  it("is 1 (no ducking) before the attack starts", () => {
    expect(duckFactorFor(-1)).toBe(1);
  });

  it("is 1 when no combat sfx is active", () => {
    expect(duckFactorFor(0, 0)).toBe(1);
  });

  it("ramps down linearly during the attack", () => {
    const half = duckFactorFor(BGM_DUCK_ATTACK_MS / 2);
    expect(half).toBeGreaterThan(BGM_DUCK_FACTOR);
    expect(half).toBeLessThan(1);
  });

  it("reaches the full duck factor at the end of the attack", () => {
    expect(duckFactorFor(BGM_DUCK_ATTACK_MS)).toBeCloseTo(BGM_DUCK_FACTOR, 10);
  });

  it("holds the full duck factor through the hold window", () => {
    expect(
      duckFactorFor(BGM_DUCK_ATTACK_MS + BGM_DUCK_HOLD_MS - 1),
    ).toBeCloseTo(BGM_DUCK_FACTOR, 10);
  });

  it("ramps back up during the release", () => {
    const released = duckFactorFor(
      BGM_DUCK_ATTACK_MS + BGM_DUCK_HOLD_MS + BGM_DUCK_RELEASE_MS / 2,
    );
    expect(released).toBeGreaterThan(BGM_DUCK_FACTOR);
    expect(released).toBeLessThan(1);
  });

  it("is fully released after attack + hold + release", () => {
    expect(
      duckFactorFor(
        BGM_DUCK_ATTACK_MS + BGM_DUCK_HOLD_MS + BGM_DUCK_RELEASE_MS,
      ),
    ).toBe(1);
  });

  it("is monotonically non-increasing then non-decreasing", () => {
    const attack = duckFactorFor(BGM_DUCK_ATTACK_MS);
    const release = duckFactorFor(
      BGM_DUCK_ATTACK_MS + BGM_DUCK_HOLD_MS + BGM_DUCK_RELEASE_MS,
    );
    expect(attack).toBeLessThan(1);
    expect(release).toBe(1);
  });

  it("duck factor is strictly below 1 (BGM really gets quieter)", () => {
    expect(BGM_DUCK_FACTOR).toBeLessThan(1);
    expect(BGM_DUCK_FACTOR).toBeGreaterThan(0);
  });

  it("attack, hold and release windows are all positive", () => {
    expect(BGM_DUCK_ATTACK_MS).toBeGreaterThan(0);
    expect(BGM_DUCK_HOLD_MS).toBeGreaterThan(0);
    expect(BGM_DUCK_RELEASE_MS).toBeGreaterThan(0);
  });
});

describe("clampRate", () => {
  it("returns 1 for the default rate", () => {
    expect(clampRate(1)).toBe(1);
  });

  it("passes through rates inside the Howler range", () => {
    expect(clampRate(0.92)).toBe(0.92);
    expect(clampRate(1.08)).toBe(1.08);
  });

  it("clamps below the Howler minimum (0.5)", () => {
    expect(clampRate(0.1)).toBe(0.5);
  });

  it("clamps above the Howler maximum (4.0)", () => {
    expect(clampRate(10)).toBe(4);
  });

  it("returns 1 for NaN", () => {
    expect(clampRate(Number.NaN)).toBe(1);
  });
});

describe("isCombatSfxId", () => {
  it("treats the combat impact sounds as combat sfx", () => {
    expect(isCombatSfxId(SFX_IDS.COMBAT_HIT)).toBe(true);
    expect(isCombatSfxId(SFX_IDS.ATTACK)).toBe(true);
    expect(isCombatSfxId(SFX_IDS.ICE_BREAK)).toBe(true);
    expect(isCombatSfxId(SFX_IDS.DAMAGE)).toBe(true);
    expect(isCombatSfxId(SFX_IDS.COMBAT_BLOCK)).toBe(true);
    expect(isCombatSfxId(SFX_IDS.COMBAT_SKILL_STRIKE)).toBe(true);
    expect(isCombatSfxId(SFX_IDS.COMBAT_SKILL_BURST)).toBe(true);
    expect(isCombatSfxId(SFX_IDS.COMBAT_SKILL_GUARD)).toBe(true);
    expect(isCombatSfxId(SFX_IDS.COMBAT_SKILL_SUPPORT)).toBe(true);
  });

  it("treats UI / menu sounds as non-combat", () => {
    expect(isCombatSfxId(SFX_IDS.CLICK)).toBe(false);
    expect(isCombatSfxId(SFX_IDS.CONFIRM)).toBe(false);
    expect(isCombatSfxId(SFX_IDS.BACK)).toBe(false);
    expect(isCombatSfxId(SFX_IDS.EQUIP)).toBe(false);
    expect(isCombatSfxId(SFX_IDS.HEAL)).toBe(false);
    expect(isCombatSfxId(SFX_IDS.MOVEMENT_STEP)).toBe(false);
    expect(isCombatSfxId(SFX_IDS.MOVEMENT_NODE)).toBe(false);
  });
});

describe("AudioManager master volume", () => {
  beforeEach(() => {
    AudioManager.resetForTesting();
    if (typeof localStorage !== "undefined") {
      localStorage.removeItem("wetrun_audio_master_volume");
    }
  });

  it("defaults to 1.0 when nothing is persisted", () => {
    expect(AudioManager.getInstance().getMasterVolume()).toBe(
      DEFAULT_MASTER_VOLUME,
    );
    expect(DEFAULT_MASTER_VOLUME).toBe(1);
  });

  it("setMasterVolume updates the state", () => {
    const audio = AudioManager.getInstance();
    audio.setMasterVolume(0.5);
    expect(audio.getMasterVolume()).toBe(0.5);
  });

  it("setMasterVolume clamps to [0,1]", () => {
    const audio = AudioManager.getInstance();
    audio.setMasterVolume(1.5);
    expect(audio.getMasterVolume()).toBe(1);
    audio.setMasterVolume(-0.5);
    expect(audio.getMasterVolume()).toBe(0);
  });

  it("setMasterVolume persists to localStorage", () => {
    if (typeof localStorage === "undefined") return;
    const audio = AudioManager.getInstance();
    audio.setMasterVolume(0.35);
    expect(localStorage.getItem("wetrun_audio_master_volume")).toBe("0.35");
  });

  it("reads the persisted master volume on the next instance", () => {
    if (typeof localStorage === "undefined") return;
    localStorage.setItem("wetrun_audio_master_volume", "0.2");
    AudioManager.resetForTesting();
    expect(AudioManager.getInstance().getMasterVolume()).toBe(0.2);
    localStorage.removeItem("wetrun_audio_master_volume");
  });

  it("master volume is independent from the BGM / SFX volumes", () => {
    const audio = AudioManager.getInstance();
    audio.setBgmVolume(0.3);
    audio.setSfxVolume(0.7);
    audio.setMasterVolume(0.9);
    expect(audio.getBgmVolume()).toBe(0.3);
    expect(audio.getSfxVolume()).toBe(0.7);
    expect(audio.getMasterVolume()).toBe(0.9);
  });
});

describe("AudioManager SFX rate + ducking state", () => {
  beforeEach(() => {
    AudioManager.resetForTesting();
    if (typeof localStorage !== "undefined") {
      localStorage.removeItem("wetrun_audio_master_volume");
    }
  });

  it("playSfx accepts an explicit rate without throwing", () => {
    const audio = AudioManager.getInstance();
    expect(
      () => void audio.playSfx(SFX_IDS.COMBAT_HIT, { rate: 0.95 }),
    ).not.toThrow();
  });

  it("playSfx accepts a rate of 1 (explicit identity)", () => {
    const audio = AudioManager.getInstance();
    expect(
      () => void audio.playSfx(SFX_IDS.COMBAT_HIT, { rate: 1 }),
    ).not.toThrow();
  });

  it("playSfx clamps an out-of-range rate without throwing", () => {
    const audio = AudioManager.getInstance();
    expect(
      () => void audio.playSfx(SFX_IDS.COMBAT_HIT, { rate: 99 }),
    ).not.toThrow();
    expect(
      () => void audio.playSfx(SFX_IDS.COMBAT_HIT, { rate: 0 }),
    ).not.toThrow();
  });

  it("playSfx without options still works (back-compat)", () => {
    const audio = AudioManager.getInstance();
    expect(() => void audio.playSfx(SFX_IDS.CLICK)).not.toThrow();
  });

  it("isDucking is false right after construction", () => {
    expect(AudioManager.getInstance().isDucking()).toBe(false);
  });

  it("a combat sfx arms the duck envelope", async () => {
    const audio = AudioManager.getInstance();
    await audio.playSfx(SFX_IDS.COMBAT_HIT);
    expect(audio.isDucking()).toBe(true);
  });

  it("a non-combat sfx does not arm the duck envelope", async () => {
    const audio = AudioManager.getInstance();
    await audio.playSfx(SFX_IDS.CLICK);
    expect(audio.isDucking()).toBe(false);
  });

  it("the duck factor is applied to the composed BGM volume", async () => {
    const audio = AudioManager.getInstance();
    audio.setBgmVolume(1);
    audio.setMasterVolume(1);
    await audio.playSfx(SFX_IDS.COMBAT_HIT);
    // The manager's own view of the BGM volume must be ducked relative to
    // the un-ducked composition.
    expect(audio.getEffectiveBgmVolume()).toBeLessThan(
      composeBgmVolume(1, 1, 1),
    );
  });

  it("ducking never rewrites the persisted BGM volume", async () => {
    if (typeof localStorage === "undefined") return;
    const audio = AudioManager.getInstance();
    audio.setBgmVolume(0.4);
    await audio.playSfx(SFX_IDS.COMBAT_HIT);
    expect(localStorage.getItem("wetrun_audio_bgm_volume")).toBe("0.4");
    expect(audio.getBgmVolume()).toBe(0.4);
  });

  it("the duck envelope releases back to 1 after the window", async () => {
    const audio = AudioManager.getInstance();
    await audio.playSfx(SFX_IDS.COMBAT_HIT);
    // Advance the internal clock past attack + hold + release.
    audio.advanceDuckingClock(
      BGM_DUCK_ATTACK_MS + BGM_DUCK_HOLD_MS + BGM_DUCK_RELEASE_MS + 1,
    );
    expect(audio.getDuckFactor()).toBe(1);
    expect(audio.isDucking()).toBe(false);
  });

  it("stopAllSfx clears the duck envelope", async () => {
    const audio = AudioManager.getInstance();
    await audio.playSfx(SFX_IDS.COMBAT_HIT);
    expect(audio.isDucking()).toBe(true);
    audio.stopAllSfx();
    expect(audio.isDucking()).toBe(false);
  });
});
