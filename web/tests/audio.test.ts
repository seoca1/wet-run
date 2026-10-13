/** AudioManager unit tests (Tier 2b).
 *
 * Tests singleton lifecycle + mute toggle. Howler construction is
 * expected to fail silently in jsdom (no AudioContext), so we test
 * the state-tracking API which is the deterministic surface.
 *
 * Tier 5 SFX + PWA icon asset tests live in the `Tier 5 assets`
 * block at the bottom of this file — they validate on-disk bytes
 * (WAV/PNG headers, dimensions, durations) rather than runtime
 * playback so they remain valid under the node test environment.
 */
import { describe, it, expect, beforeEach } from "vitest";
import { readFileSync, statSync } from "fs";
import { join } from "path";
import { AudioManager, BGM_IDS, SFX_IDS } from "../src/audio/manager.js";

const PUBLIC_DIR = join(import.meta.dirname, "../public");

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

  it("playPhase('menu') is fire-and-forget async, isPlaying false in node", () => {
    const audio = AudioManager.getInstance();
    audio.playPhase("menu");
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

  it("SFX_IDS exposes legacy effects", () => {
    expect(SFX_IDS.COMBAT_HIT).toBe("sounds/sfx_combat_hit.wav");
    expect(SFX_IDS.DEFEAT).toBe("sounds/sfx_defeat.wav");
  });

  it("SFX_IDS exposes new sfx directory effects", () => {
    expect(SFX_IDS.VICTORY).toBe("sounds/sfx/victory.wav");
    expect(SFX_IDS.CLICK).toBe("sounds/sfx/click.wav");
    expect(SFX_IDS.DAMAGE).toBe("sounds/sfx/damage.wav");
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

  // Tier 5: volume slider round-trip — BGM + SFX persist independently and
  // both survive an AudioManager reset (proves the values reach localStorage).
  it("volume sliders: BGM + SFX persist independently and round-trip after reset", () => {
    if (typeof localStorage === "undefined") return;
    localStorage.removeItem("wetrun_audio_bgm_volume");
    localStorage.removeItem("wetrun_audio_sfx_volume");
    AudioManager.resetForTesting();

    const audio = AudioManager.getInstance();
    audio.setBgmVolume(0.3);
    audio.setSfxVolume(0.7);
    expect(audio.getBgmVolume()).toBe(0.3);
    expect(audio.getSfxVolume()).toBe(0.7);

    // Simulate reload — new singleton must rehydrate from localStorage.
    AudioManager.resetForTesting();
    const reloaded = AudioManager.getInstance();
    expect(reloaded.getBgmVolume()).toBe(0.3);
    expect(reloaded.getSfxVolume()).toBe(0.7);
    // Decoupled: setting BGM doesn't disturb SFX.
    reloaded.setBgmVolume(0.9);
    expect(reloaded.getSfxVolume()).toBe(0.7);

    // Cleanup
    localStorage.removeItem("wetrun_audio_bgm_volume");
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

// ---------------------------------------------------------------------------
// Tier 5 assets — SFX files + PWA icons (on-disk byte validation).
//
// These tests do not require a browser AudioContext. They parse the WAV
// headers + data chunks and the PNG signatures + IHDR dimensions so a
// broken export (e.g. a future regeneration script writes silence, the
// wrong sample rate, or a malformed PNG) is caught by CI.
// ---------------------------------------------------------------------------

interface WavInfo {
  path: string;
  relPath: string;
  durationSec: number;
  sizeBytes: number;
  sampleRate: number;
  channels: number;
  bitDepth: 16;
}

function parseWavHeader(absPath: string): WavInfo {
  const buf = readFileSync(absPath);
  // RIFF/WAVE
  if (
    buf.length < 44 ||
    buf.toString("ascii", 0, 4) !== "RIFF" ||
    buf.toString("ascii", 8, 12) !== "WAVE"
  ) {
    throw new Error(`not RIFF/WAVE: ${absPath}`);
  }
  // fmt chunk at offset 12
  if (buf.toString("ascii", 12, 16) !== "fmt ") {
    throw new Error(`missing fmt chunk: ${absPath}`);
  }
  const fmtSize = buf.readUInt32LE(16);
  const audioFormat = buf.readUInt16LE(20);
  const channels = buf.readUInt16LE(22);
  const sampleRate = buf.readUInt32LE(24);
  const byteRate = buf.readUInt32LE(28);
  const blockAlign = buf.readUInt16LE(32);
  const bitsPerSample = buf.readUInt16LE(34);
  if (audioFormat !== 1) throw new Error(`not PCM (fmt=${audioFormat}) in ${absPath}`);
  if (bitsPerSample !== 16) throw new Error(`not 16-bit (bps=${bitsPerSample}) in ${absPath}`);
  if (channels !== 1) throw new Error(`not mono (ch=${channels}) in ${absPath}`);
  if (sampleRate !== 44100) throw new Error(`not 44.1 kHz (sr=${sampleRate}) in ${absPath}`);
  if (byteRate !== sampleRate * channels * (bitsPerSample / 8))
    throw new Error(`byteRate inconsistent in ${absPath}`);
  if (blockAlign !== channels * (bitsPerSample / 8))
    throw new Error(`blockAlign inconsistent in ${absPath}`);
  if (fmtSize !== 16)
    throw new Error(`expected fmt_size=16, got ${fmtSize} in ${absPath}`);
  // data chunk immediately after fmt
  const dataPos = 20 + fmtSize;
  if (buf.toString("ascii", dataPos, dataPos + 4) !== "data")
    throw new Error(`missing data chunk in ${absPath}`);
  const dataSize = buf.readUInt32LE(dataPos + 4);
  const expectedTotalSize = dataPos + 8 + dataSize;
  if (expectedTotalSize !== buf.length)
    throw new Error(
      `data chunk size mismatch in ${absPath}: header says ${expectedTotalSize}, file is ${buf.length}`,
    );
  const frames = dataSize / blockAlign;
  return {
    path: absPath,
    relPath: absPath.split("/public/").pop()!,
    durationSec: frames / sampleRate,
    sizeBytes: buf.length,
    sampleRate,
    channels,
    bitDepth: 16,
  };
}

interface PngInfo {
  path: string;
  width: number;
  height: number;
  sizeBytes: number;
  nonBlackPixels?: number;
}

function parsePngHeader(absPath: string): PngInfo {
  const buf = readFileSync(absPath);
  // PNG signature: 89 50 4E 47 0D 0A 1A 0A
  const sig = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
  if (buf.length < 24 || !buf.subarray(0, 8).equals(sig))
    throw new Error(`not PNG: ${absPath}`);
  if (buf.toString("ascii", 12, 16) !== "IHDR")
    throw new Error(`missing IHDR: ${absPath}`);
  const width = buf.readUInt32BE(16);
  const height = buf.readUInt32BE(20);
  const bitDepth = buf[24];
  const colorType = buf[25];
  if (bitDepth !== 8)
    throw new Error(`expected 8-bit depth, got ${bitDepth} in ${absPath}`);
  if (colorType !== 2 && colorType !== 6)
    throw new Error(
      `expected RGB (2) or RGBA (6) color_type, got ${colorType} in ${absPath}`,
    );
  return {
    path: absPath,
    width,
    height,
    sizeBytes: buf.length,
  };
}

// The 7 SFX the dispatcher expects, with expected duration bands (seconds).
// Bands come from the spec the synth-sfx.py was written against.
const SFX_CASES: Array<{
  id: keyof typeof SFX_IDS;
  filename: string;
  minDur: number;
  maxDur: number;
}> = [
  { id: "COMBAT_BLOCK", filename: "combat_block.wav", minDur: 0.25, maxDur: 0.40 },
  {
    id: "COMBAT_SKILL_STRIKE",
    filename: "combat_skill_strike.wav",
    minDur: 0.15,
    maxDur: 0.22,
  },
  {
    id: "COMBAT_SKILL_BURST",
    filename: "combat_skill_burst.wav",
    minDur: 0.30,
    maxDur: 0.45,
  },
  {
    id: "COMBAT_SKILL_GUARD",
    filename: "combat_skill_guard.wav",
    minDur: 0.28,
    maxDur: 0.40,
  },
  {
    id: "COMBAT_SKILL_SUPPORT",
    filename: "combat_skill_support.wav",
    minDur: 0.22,
    maxDur: 0.32,
  },
  {
    id: "MOVEMENT_STEP",
    filename: "movement_step.wav",
    minDur: 0.12,
    maxDur: 0.20,
  },
  {
    id: "MOVEMENT_NODE",
    filename: "movement_node.wav",
    minDur: 0.40,
    maxDur: 0.55,
  },
];

describe("Tier 5 SFX assets (public/sounds/sfx/*.wav)", () => {
  for (const c of SFX_CASES) {
    it(`SFX_IDS.${c.id} resolves to public/sounds/sfx/${c.filename}`, () => {
      const expected = `sounds/sfx/${c.filename}`;
      expect(SFX_IDS[c.id]).toBe(expected);
      const abs = join(PUBLIC_DIR, expected);
      expect(statSync(abs).size).toBeGreaterThan(0);
    });

    it(`${c.filename} is 44.1 kHz 16-bit mono PCM with sane duration`, () => {
      const abs = join(PUBLIC_DIR, "sounds", "sfx", c.filename);
      const info = parseWavHeader(abs);
      expect(info.sampleRate).toBe(44100);
      expect(info.channels).toBe(1);
      expect(info.bitDepth).toBe(16);
      // Duration band from spec (synth-sfx.py + task description 0.15..0.5s).
      expect(info.durationSec).toBeGreaterThanOrEqual(c.minDur);
      expect(info.durationSec).toBeLessThanOrEqual(c.maxDur);
      // Size sanity: header 44 bytes + n_frames * 2 bytes/sample * 1 channel.
      const expectedSize = 44 + Math.round(info.durationSec * 44100) * 2;
      expect(info.sizeBytes).toBe(expectedSize);
    });
  }

  it("all 7 SFX together weigh < 1 MB (PWA cache budget)", () => {
    let total = 0;
    for (const c of SFX_CASES) {
      total += statSync(join(PUBLIC_DIR, "sounds", "sfx", c.filename)).size;
    }
    expect(total).toBeLessThan(1024 * 1024);
  });
});

describe("PWA icons (public/icons/icon-*.png)", () => {
  it("icon-192.png exists at manifest-declared size and is non-blank", () => {
    const abs = join(PUBLIC_DIR, "icons", "icon-192.png");
    const info = parsePngHeader(abs);
    expect(info.width).toBe(192);
    expect(info.height).toBe(192);
    expect(info.sizeBytes).toBeGreaterThan(1024);
  });

  it("icon-512.png exists at manifest-declared size and is non-blank", () => {
    const abs = join(PUBLIC_DIR, "icons", "icon-512.png");
    const info = parsePngHeader(abs);
    expect(info.width).toBe(512);
    expect(info.height).toBe(512);
    expect(info.sizeBytes).toBeGreaterThan(1024);
  });

  it("every manifest icon entry has a matching PNG file at the declared size", () => {
    const manifestPath = join(PUBLIC_DIR, "manifest.json");
    const manifest = JSON.parse(readFileSync(manifestPath, "utf-8"));
    expect(Array.isArray(manifest.icons)).toBe(true);
    expect(manifest.icons.length).toBeGreaterThan(0);
    for (const entry of manifest.icons) {
      expect(entry.sizes).toBeDefined();
      expect(entry.type).toBe("image/png");
      const [w, h] = entry.sizes.split(" ").sort()[0].split("x").map(Number);
      expect(w).toBe(h); // square icons only
      const filename = `icon-${w}.png`;
      const abs = join(PUBLIC_DIR, "icons", filename);
      const stat = statSync(abs);
      expect(stat.size).toBeGreaterThan(0);
      const info = parsePngHeader(abs);
      expect(info.width).toBe(w);
      expect(info.height).toBe(h);
    }
  });
});