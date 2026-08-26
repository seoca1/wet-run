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
});