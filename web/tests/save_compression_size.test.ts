/** Save compression byte-measurement tests (Tier 5 carry-over).
 *
 * Tier 5 README scope: "save compression (payload shrink for localStorage/IDB).
 * Additive (detect + decompress old saves; write compressed new).
 * Measure + report byte sizes before/after on a real save fixture."
 *
 * These tests build real SaveSlot payloads at three realistic sizes
 * (small/mid/large) and round-trip them through `save` → `load`
 * to verify the v2 envelope path:
 *   - legacy v1 plain JSON loads transparently (backward-compat)
 *   - v2 plain envelope (small payload under threshold) loads
 *   - v2 compressed envelope (large payload over threshold) loads
 *
 * Byte measurements are reported on `console.info` so the Tier 5 summary can
 * quote them. The test assertions pin the wire-size contract (compressed
 * must be ≤ uncompressed) and the round-trip correctness contract.
 */
// @vitest-environment jsdom

import { describe, it, expect, beforeEach } from "vitest";
import {
  save,
  load,
  clear,
  MAX_SAVE_SLOT,
} from "../src/save/storage.ts";
import {
  encodeEnvelope,
  decodeEnvelope,
  COMPRESSION_THRESHOLD_BYTES,
} from "../src/save/compress.ts";
import type { SaveSlot } from "../src/core/types.ts";

/** Build a SaveSlot with the requested number of programs in deck/discard/draw. */
function buildSlot(
  id: string,
  programCount: number,
  opts: { readonly graphicNovel?: boolean } = {},
): SaveSlot {
  const programs = Array.from({ length: programCount }, (_, i) =>
    `program_${i.toString().padStart(3, "0")}_with_long_name`,
  );
  return {
    version: 1,
    missionId: id,
    playerHp: 75,
    playerMaxHp: 100,
    playerAlarm: 45,
    playerCredits: 12500,
    turnCount: 142,
    deckIds: programs,
    discardIds: programs,
    drawIds: programs,
    savedAt: "2026-08-31T00:00:00.000Z",
    graphicNovelProgress: opts.graphicNovel
      ? { chainId: "prologue_case", sceneIndex: 2, dialogueIndex: 5 }
      : null,
  };
}

/** Approximate byte length of a UTF-16 string (jsdom localStorage/IDB round
 * trips may treat length differently from byte size; this gives a stable
 * "characters" measure that's proportional to wire size). */
function approxBytes(str: string): number {
  return str.length;
}

describe("save compression byte measurement (Tier 5)", () => {
  beforeEach(async () => {
    for (let s = 0; s <= MAX_SAVE_SLOT; s++) {
      await clear(s);
    }
  });

  it("measures wire size at three realistic tiers + reports reductions", () => {
    const sizes: ReadonlyArray<{
      readonly label: string;
      readonly programCount: number;
    }> = [
      { label: "small (3 programs)", programCount: 3 },
      { label: "mid (15 programs)", programCount: 15 },
      { label: "large (30 programs)", programCount: 30 },
    ];

    const report: Array<{
      readonly label: string;
      readonly programCount: number;
      readonly rawBytes: number;
      readonly envelopeBytes: number;
      readonly compressed: boolean;
      readonly reductionPct: number;
    }> = [];

    for (const { label, programCount } of sizes) {
      const slot = buildSlot(`mission_${programCount}`, programCount);
      const rawJson = JSON.stringify(slot);
      const env = encodeEnvelope(rawJson);
      const stored = JSON.stringify(env);
      const rawBytes = approxBytes(rawJson);
      const envelopeBytes = approxBytes(stored);
      const reductionPct = Math.round(
        ((rawBytes - envelopeBytes) / rawBytes) * 1000,
      ) / 10;
      const compressed = env.c === true;
      report.push({
        label,
        programCount,
        rawBytes,
        envelopeBytes,
        compressed,
        reductionPct,
      });
    }

    console.info("[Tier 5] save compression byte measurement:");
    console.info(
      `  ${"Tier".padEnd(22)} ${"Raw".padStart(7)} ${"Stored".padStart(7)} │ compressed │ reduction`,
    );
    for (const r of report) {
      console.info(
        `  ${r.label.padEnd(22)} ${String(r.rawBytes).padStart(7)} ${String(r.envelopeBytes).padStart(7)} │     ${r.compressed ? "yes" : " no"}    │  ${r.reductionPct.toFixed(1)}%`,
      );
    }

    // Wire-size contract: compressed (large) MUST be smaller than raw.
    const large = report.find((r) => r.programCount === 30);
    expect(large).toBeDefined();
    if (large) {
      expect(large.compressed).toBe(true);
      expect(large.envelopeBytes).toBeLessThan(large.rawBytes);
    }
    // Small payload (under threshold) → no compression (envelope overhead
    // would exceed savings).
    const small = report.find((r) => r.programCount === 3);
    expect(small).toBeDefined();
    if (small) {
      expect(small.compressed).toBe(false);
    }
  });

  it("small payload falls under COMPRESSION_THRESHOLD_BYTES", () => {
    const slot = buildSlot("small", 3);
    const raw = JSON.stringify(slot);
    expect(raw.length).toBeLessThan(COMPRESSION_THRESHOLD_BYTES);
  });

  it("large payload (30 programs) exceeds COMPRESSION_THRESHOLD_BYTES", () => {
    const slot = buildSlot("large", 30);
    const raw = JSON.stringify(slot);
    expect(raw.length).toBeGreaterThan(COMPRESSION_THRESHOLD_BYTES);
  });
});

describe("save compression backward-compat (Tier 5)", () => {
  beforeEach(async () => {
    for (let s = 0; s <= MAX_SAVE_SLOT; s++) {
      await clear(s);
    }
  });

  it("legacy v1 plain JSON loads through decodeEnvelope (returns raw string)", () => {
    const legacyV1 = JSON.stringify({
      version: 1,
      missionId: "legacy_first_jack",
      playerHp: 80,
      playerMaxHp: 100,
      playerAlarm: 10,
      playerCredits: 100,
      turnCount: 5,
      deckIds: ["strike"],
      discardIds: [],
      drawIds: ["shield"],
      savedAt: "2026-08-30T00:00:00.000Z",
    });
    const decoded = decodeEnvelope(legacyV1);
    expect(decoded).toBe(legacyV1);
  });

  it("legacy v1 save in localStorage round-trips via save layer", async () => {
    const legacySlot: SaveSlot = {
      version: 1,
      missionId: "legacy_v1_mission",
      playerHp: 80,
      playerMaxHp: 100,
      playerAlarm: 10,
      playerCredits: 100,
      turnCount: 5,
      deckIds: ["strike"],
      discardIds: [],
      drawIds: ["shield"],
      savedAt: "2026-08-30T00:00:00.000Z",
    };
    // Simulate legacy v1 (no envelope) sitting in localStorage.
    if (typeof localStorage !== "undefined") {
      localStorage.setItem(
        "wetrun_mvp_save_v1_slot_0",
        JSON.stringify(legacySlot),
      );
    }
    const loaded = await load(0);
    expect(loaded).not.toBeNull();
    expect(loaded?.missionId).toBe("legacy_v1_mission");
    expect(loaded?.turnCount).toBe(5);
  });

  it("v2 compressed envelope round-trips through save layer", async () => {
    const large = buildSlot("deep_core_infiltration", 30);
    await save(1, large);
    const loaded = await load(1);
    expect(loaded).not.toBeNull();
    expect(loaded?.missionId).toBe("deep_core_infiltration");
    expect(loaded?.deckIds.length).toBe(30);
    expect(loaded?.discardIds.length).toBe(30);
    expect(loaded?.drawIds.length).toBe(30);
  });

  it("v2 plain envelope (small payload) round-trips through save layer", async () => {
    const small = buildSlot("first_jack", 3);
    await save(2, small);
    const loaded = await load(2);
    expect(loaded).not.toBeNull();
    expect(loaded?.missionId).toBe("first_jack");
  });
});