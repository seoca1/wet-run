/** AudioManager unit tests (Tier 2b).
 *
 * Tests singleton lifecycle + mute toggle. Howler construction is
 * expected to fail silently in jsdom (no AudioContext), so we test
 * the state-tracking API which is the deterministic surface.
 */
import { describe, it, expect, beforeEach } from "vitest";
import { AudioManager, SOUND_IDS } from "../src/audio/manager.js";

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
    audio.play(SOUND_IDS.SENSE_NET);
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

  it("SOUND_IDS exposes SENSE_NET path", () => {
    expect(SOUND_IDS.SENSE_NET).toBe("sounds/theme_sense_net.mp3");
  });
});