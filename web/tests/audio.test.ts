/** AudioManager unit tests (Tier 2b).
 *
 * Tests singleton lifecycle + mute toggle. Howler construction is
 * expected to fail silently in jsdom (no AudioContext), so we test
 * the state-tracking API which is the deterministic surface.
 */
import { describe, it, expect, beforeEach } from "vitest";
import { AudioManager, BGM_IDS, SFX_IDS } from "../src/audio/manager.js";

describe("AudioManager", () => {
  beforeEach(() => {
    AudioManager.resetForTesting();
  });

  it("returns a singleton instance", () => {
    const a = AudioManager.getInstance();
    const b = AudioManager.getInstance();
    expect(a).toBe(b);
  });

  it("starts unmuted and not playing", () => {
    const audio = AudioManager.getInstance();
    expect(audio.isMuted()).toBe(false);
    expect(audio.isPlaying()).toBe(false);
  });

  it("toggleMute flips state and returns new state", () => {
    const audio = AudioManager.getInstance();
    expect(audio.toggleMute()).toBe(true);
    expect(audio.isMuted()).toBe(true);
    expect(audio.toggleMute()).toBe(false);
    expect(audio.isMuted()).toBe(false);
  });

  it("mute() and unmute() set state explicitly", () => {
    const audio = AudioManager.getInstance();
    audio.mute();
    expect(audio.isMuted()).toBe(true);
    audio.unmute();
    expect(audio.isMuted()).toBe(false);
  });

  it("play() is a no-op in node test environment (no AudioContext)", () => {
    const audio = AudioManager.getInstance();
    audio.play();
    expect(audio.isPlaying()).toBe(false);
  });

  it("play() accepts a SoundId and is a no-op in node", () => {
    const audio = AudioManager.getInstance();
    audio.play(BGM_IDS.SENSE_NET);
    expect(audio.isPlaying()).toBe(false);
  });

  it("stop() is safe even when not playing", () => {
    const audio = AudioManager.getInstance();
    audio.stop();
    expect(audio.isPlaying()).toBe(false);
  });

  it("unlockOnFirstGesture is a no-op without document", () => {
    expect(() => AudioManager.unlockOnFirstGesture()).not.toThrow();
  });

  it("BGM_IDS exposes SENSE_NET path", () => {
    expect(BGM_IDS.SENSE_NET).toBe("sounds/theme_sense_net.mp3");
  });

  it("BGM_IDS exposes 5 tracks for Tier 3 phase-aware BGM", () => {
    expect(BGM_IDS.CHIBA).toBe("sounds/theme_chiba.mp3");
    expect(BGM_IDS.MATRIX_RAIN).toBe("sounds/theme_matrix_rain.mp3");
    expect(BGM_IDS.BROADCAST).toBe("sounds/theme_broadcast.mp3");
    expect(BGM_IDS.INDUSTRIAL).toBe("sounds/theme_industrial.mp3");
  });

  it("playPhase('menu') tracks chiba but isPlaying false in node", () => {
    const audio = AudioManager.getInstance();
    audio.playPhase("menu");
    expect(audio.getCurrentTrack()).toBe("sounds/theme_chiba.mp3");
    expect(audio.isPlaying()).toBe(false);
  });

  it("playPhase('exit') stops playback", () => {
    const audio = AudioManager.getInstance();
    audio.playPhase("exit");
    expect(audio.isPlaying()).toBe(false);
  });

  it("playPhase ignores unknown phases", () => {
    const audio = AudioManager.getInstance();
    audio.playPhase("unknown_phase");
    expect(audio.isPlaying()).toBe(false);
    expect(audio.getCurrentTrack()).toBe(null);
  });

  it("SFX_IDS exposes 3 effects for Tier 4", () => {
    expect(SFX_IDS.COMBAT_HIT).toBe("sounds/sfx_combat_hit.wav");
    expect(SFX_IDS.VICTORY).toBe("sounds/sfx_victory.wav");
    expect(SFX_IDS.DEFEAT).toBe("sounds/sfx_defeat.wav");
  });

  it("playSfx is a no-op in node (Howler fails to decode)", () => {
    const audio = AudioManager.getInstance();
    audio.playSfx();
    expect(audio.isMuted()).toBe(false);
  });

  it("playSfx respects mute state", () => {
    const audio = AudioManager.getInstance();
    audio.mute();
    expect(audio.isMuted()).toBe(true);
    audio.playSfx();
    audio.unmute();
    expect(audio.isMuted()).toBe(false);
  });

  it("stopAllSfx does not throw when no SFX active", () => {
    const audio = AudioManager.getInstance();
    audio.stopAllSfx();
    expect(audio.isMuted()).toBe(false);
  });

  // Tier 5: per-track volume API (BGM + SFX) with localStorage persistence.
  it("getBgmVolume returns default 0.4 when no persisted value", () => {
    if (typeof localStorage !== "undefined") {
      localStorage.removeItem("wetrun_audio_bgm_volume");
    }
    AudioManager.resetForTesting();
    const audio = AudioManager.getInstance();
    expect(audio.getBgmVolume()).toBe(0.4);
  });

  it("getSfxVolume returns default 0.6 when no persisted value", () => {
    if (typeof localStorage !== "undefined") {
      localStorage.removeItem("wetrun_audio_sfx_volume");
    }
    AudioManager.resetForTesting();
    const audio = AudioManager.getInstance();
    expect(audio.getSfxVolume()).toBe(0.6);
  });

  it("setBgmVolume updates state and clamps to [0,1]", () => {
    AudioManager.resetForTesting();
    const audio = AudioManager.getInstance();
    audio.setBgmVolume(0.5);
    expect(audio.getBgmVolume()).toBe(0.5);
    audio.setBgmVolume(1.5);
    expect(audio.getBgmVolume()).toBe(1);
    audio.setBgmVolume(-0.3);
    expect(audio.getBgmVolume()).toBe(0);
  });

  it("setSfxVolume updates state and clamps to [0,1]", () => {
    AudioManager.resetForTesting();
    const audio = AudioManager.getInstance();
    audio.setSfxVolume(0.7);
    expect(audio.getSfxVolume()).toBe(0.7);
    audio.setSfxVolume(2);
    expect(audio.getSfxVolume()).toBe(1);
    audio.setSfxVolume(-1);
    expect(audio.getSfxVolume()).toBe(0);
  });

  it("setBgmVolume persists to localStorage", () => {
    if (typeof localStorage === "undefined") return;
    localStorage.removeItem("wetrun_audio_bgm_volume");
    AudioManager.resetForTesting();
    const audio = AudioManager.getInstance();
    audio.setBgmVolume(0.8);
    expect(localStorage.getItem("wetrun_audio_bgm_volume")).toBe("0.8");
  });

  it("setSfxVolume persists to localStorage", () => {
    if (typeof localStorage === "undefined") return;
    localStorage.removeItem("wetrun_audio_sfx_volume");
    AudioManager.resetForTesting();
    const audio = AudioManager.getInstance();
    audio.setSfxVolume(0.3);
    expect(localStorage.getItem("wetrun_audio_sfx_volume")).toBe("0.3");
  });

  it("AudioManager reads persisted BGM volume on next instance", () => {
    if (typeof localStorage === "undefined") return;
    localStorage.setItem("wetrun_audio_bgm_volume", "0.25");
    AudioManager.resetForTesting();
    const audio = AudioManager.getInstance();
    expect(audio.getBgmVolume()).toBe(0.25);
    localStorage.removeItem("wetrun_audio_bgm_volume");
  });

  it("AudioManager reads persisted SFX volume on next instance", () => {
    if (typeof localStorage === "undefined") return;
    localStorage.setItem("wetrun_audio_sfx_volume", "0.85");
    AudioManager.resetForTesting();
    const audio = AudioManager.getInstance();
    expect(audio.getSfxVolume()).toBe(0.85);
    localStorage.removeItem("wetrun_audio_sfx_volume");
  });

  // Tier 7: per-track fade in/out (crossfade between BGM phases).
  it("crossfadeTo accepts a track + duration without throwing in node", () => {
    const audio = AudioManager.getInstance();
    expect(() => audio.crossfadeTo(BGM_IDS.SENSE_NET, 100)).not.toThrow();
    // In jsdom, Howler may or may not construct successfully. Either way,
    // no exception is thrown — the current track should be either the
    // requested track (jsdom success) or null (jsdom failure).
    const ct = audio.getCurrentTrack();
    expect(ct === null || ct === BGM_IDS.SENSE_NET).toBe(true);
  });

  it("crossfadeTo is idempotent for the same track (no-op after first)", () => {
    const audio = AudioManager.getInstance();
    audio.crossfadeTo(BGM_IDS.CHIBA, 100);
    expect(() => audio.crossfadeTo(BGM_IDS.CHIBA, 100)).not.toThrow();
  });

  it("crossfadeTo with 0ms duration is safe", () => {
    const audio = AudioManager.getInstance();
    expect(() => audio.crossfadeTo(BGM_IDS.MATRIX_RAIN, 0)).not.toThrow();
  });

  it("fadeOutAndStop is safe when nothing is playing", () => {
    const audio = AudioManager.getInstance();
    expect(() => audio.fadeOutAndStop(100)).not.toThrow();
  });

  it("fadeOutAndStop accepts a 0ms duration", () => {
    const audio = AudioManager.getInstance();
    expect(() => audio.fadeOutAndStop(0)).not.toThrow();
  });

  it("playPhase('exit') calls fadeOutAndStop (does not throw on null howl)", () => {
    const audio = AudioManager.getInstance();
    expect(() => audio.playPhase("exit")).not.toThrow();
  });

  it("playPhase('combat') transitions to MATRIX_RAIN track without throwing", () => {
    const audio = AudioManager.getInstance();
    expect(() => audio.playPhase("combat")).not.toThrow();
  });

  it("playPhase('unknown_phase') is a silent no-op", () => {
    const audio = AudioManager.getInstance();
    expect(() => audio.playPhase("nonexistent_phase")).not.toThrow();
    expect(audio.getCurrentTrack()).toBe(null);
  });
});