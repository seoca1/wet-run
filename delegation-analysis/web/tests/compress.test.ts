/** Save compression layer tests (Tier 7).
 *
 * Verifies the v2 envelope round-trip, threshold gate, and legacy v1
 * fallback. Uses real lz-string compression — no mocks.
 */
import { describe, it, expect } from "vitest";
import {
  encodeEnvelope,
  decodeEnvelope,
  parseEnvelope,
  shouldCompress,
  COMPRESSION_THRESHOLD_BYTES,
} from "../src/save/compress.js";

describe("shouldCompress (threshold gate)", () => {
  it("returns false for payloads under threshold", () => {
    expect(shouldCompress("")).toBe(false);
    expect(shouldCompress("a".repeat(COMPRESSION_THRESHOLD_BYTES - 1))).toBe(false);
  });

  it("returns true for payloads at or above threshold", () => {
    expect(shouldCompress("a".repeat(COMPRESSION_THRESHOLD_BYTES))).toBe(true);
    expect(shouldCompress("a".repeat(COMPRESSION_THRESHOLD_BYTES + 100))).toBe(true);
  });
});

describe("encodeEnvelope + decodeEnvelope (round-trip)", () => {
  it("round-trips a small JSON payload (plain envelope, no compression)", () => {
    const json = '{"missionId":"m1","playerHp":80}';
    const envelope = encodeEnvelope(json);
    expect(envelope.v).toBe(2);
    expect(envelope.c).toBe(false);
    expect(envelope.d).toBe(json);
    expect(decodeEnvelope(JSON.stringify(envelope))).toBe(json);
  });

  it("round-trips a large JSON payload (compressed envelope)", () => {
    const json = JSON.stringify({
      missionId: "mission_with_very_long_name_for_compression_testing",
      playerHp: 80,
      playerMaxHp: 100,
      deckIds: Array.from({ length: 20 }, (_, i) => `prog_${i.toString().padStart(3, "0")}`),
      discardIds: Array.from({ length: 20 }, (_, i) => `prog_${(i + 20).toString().padStart(3, "0")}`),
      drawIds: Array.from({ length: 20 }, (_, i) => `prog_${(i + 40).toString().padStart(3, "0")}`),
    });
    expect(shouldCompress(json)).toBe(true);
    const envelope = encodeEnvelope(json);
    expect(envelope.v).toBe(2);
    expect(envelope.c).toBe(true);
    expect(envelope.d.length).toBeLessThan(json.length);
    expect(decodeEnvelope(JSON.stringify(envelope))).toBe(json);
  });

  it("preserves special characters (quotes, unicode, escapes)", () => {
    const json = JSON.stringify({ text: "He said \"hello\" — 日本語 🎮" });
    const encoded = encodeEnvelope(json);
    const decoded = decodeEnvelope(JSON.stringify(encoded));
    expect(decoded).toBe(json);
    expect(JSON.parse(decoded ?? "{}")).toEqual({ text: "He said \"hello\" — 日本語 🎮" });
  });

  it("preserves nested objects + arrays", () => {
    const json = JSON.stringify({
      matrix: { nodes: Array.from({ length: 10 }, (_, i) => ({ id: i, zone: "core" })) },
      effects: ["attack", "heal", "stun"],
    });
    const encoded = encodeEnvelope(json);
    const decoded = decodeEnvelope(JSON.stringify(encoded));
    expect(JSON.parse(decoded ?? "{}")).toEqual(JSON.parse(json));
  });
});

describe("decodeEnvelope (legacy v1 + malformed fallback)", () => {
  it("loads legacy v1 plain JSON without envelope", () => {
    const legacyV1 = '{"missionId":"legacy","playerHp":50}';
    expect(decodeEnvelope(legacyV1)).toBe(legacyV1);
  });

  it("returns null for non-JSON garbage", () => {
    expect(decodeEnvelope("this is not json at all")).toBeNull();
    expect(decodeEnvelope("")).toBeNull();
    expect(decodeEnvelope("12345")).toBeNull();
  });

  it("treats envelope-shape object missing v field as legacy v1", () => {
    // No `v` field at root → legacy v1 fallback (returns raw string).
    const input = '{"c":false,"d":"x"}';
    expect(decodeEnvelope(input)).toBe(input);
  });

  it("returns null for envelope with wrong v value", () => {
    expect(decodeEnvelope('{"v":1,"c":false,"d":"x"}')).toBeNull();
    expect(decodeEnvelope('{"v":3,"c":false,"d":"x"}')).toBeNull();
  });

  it("returns null for envelope with non-string d field", () => {
    expect(decodeEnvelope('{"v":2,"c":false,"d":42}')).toBeNull();
    expect(decodeEnvelope('{"v":2,"c":true,"d":null}')).toBeNull();
  });

  it("returns null for compressed envelope with corrupted data", () => {
    expect(decodeEnvelope('{"v":2,"c":true,"d":"!!not-valid-lz!!"}')).toBeNull();
  });

  it("returns null for envelope with non-boolean c field", () => {
    expect(decodeEnvelope('{"v":2,"c":"maybe","d":"x"}')).toBeNull();
  });
});

describe("parseEnvelope (strict parser)", () => {
  it("returns envelope object for valid v2 input", () => {
    const env = parseEnvelope('{"v":2,"c":false,"d":"plain"}');
    expect(env).toEqual({ v: 2, c: false, d: "plain" });
  });

  it("returns null for legacy v1 input (use decodeEnvelope for v1 fallback)", () => {
    expect(parseEnvelope('{"missionId":"x"}')).toBeNull();
  });

  it("returns null for malformed input", () => {
    expect(parseEnvelope("not json")).toBeNull();
    expect(parseEnvelope('{"v":2,"c":false}')).toBeNull();
  });
});

describe("size reduction for typical save payloads", () => {
  it("small save (< threshold) gets plain envelope — no net savings", () => {
    const small = JSON.stringify({
      version: 1,
      missionId: "first_jack",
      playerHp: 80,
      playerMaxHp: 100,
      playerAlarm: 30,
      playerCredits: 1500,
      turnCount: 5,
      deckIds: ["strike", "probe"],
      discardIds: ["shield"],
      drawIds: ["hammer"],
      savedAt: "2026-08-31T00:00:00.000Z",
    });
    expect(small.length).toBeLessThan(COMPRESSION_THRESHOLD_BYTES);
    const env = encodeEnvelope(small);
    expect(env.c).toBe(false);
    // Envelope adds ~15 bytes overhead; not worth compressing.
    const stored = JSON.stringify(env);
    expect(stored.length).toBeGreaterThan(small.length);
  });

  it("large save (with many programs) gets compressed — net savings", () => {
    // Build a realistic large save with 30 programs (deck + discard + draw).
    const programs = Array.from({ length: 30 }, (_, i) => `program_${i.toString().padStart(3, "0")}_with_long_name`);
    const large = JSON.stringify({
      version: 1,
      missionId: "deep_core_infiltration",
      playerHp: 75,
      playerMaxHp: 100,
      playerAlarm: 45,
      playerCredits: 12500,
      turnCount: 142,
      deckIds: programs,
      discardIds: programs,
      drawIds: programs,
      savedAt: "2026-08-31T00:00:00.000Z",
    });
    expect(large.length).toBeGreaterThan(COMPRESSION_THRESHOLD_BYTES);
    const env = encodeEnvelope(large);
    expect(env.c).toBe(true);
    const stored = JSON.stringify(env);
    // Compressed + envelope should be smaller than original.
    expect(stored.length).toBeLessThan(large.length);
  });
});
