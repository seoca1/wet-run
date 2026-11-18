/** Save compression layer (Tier 7).
 *
 * Wraps save payloads in a versioned envelope so we can compress/decompress
 * transparently without breaking older save files. The envelope embeds the
 * format version + a `c` flag for compressed + the raw data string.
 *
 *   v1: plain JSON string (legacy)
 *   v2: { v: 2, c: boolean, d: string }
 *       - c=true  → d is lz-string compressedToEncodedURIComponent JSON
 *       - c=false → d is plain JSON (used when payload is too small to benefit)
 *
 * Threshold: payloads under COMPRESSION_THRESHOLD_BYTES are stored as plain
 * JSON (the lz-string overhead exceeds savings for short strings).
 *
 * Backward compatibility: v1 saves load without modification. v2 plain
 * saves (c=false) parse identically to v1. v2 compressed saves transparently
 * decompress on load.
 */
import LZString from "lz-string";

/** Minimum payload size for compression to be worth it (lz-string overhead). */
export const COMPRESSION_THRESHOLD_BYTES = 512;

export type SaveEnvelope =
  | { readonly v: 2; readonly c: false; readonly d: string }
  | { readonly v: 2; readonly c: true; readonly d: string };

/** Heuristic — returns true if payload should be compressed. */
export function shouldCompress(jsonPayload: string): boolean {
  return jsonPayload.length >= COMPRESSION_THRESHOLD_BYTES;
}

/** Encode a JSON string into a v2 envelope, optionally compressing. */
export function encodeEnvelope(jsonPayload: string): SaveEnvelope {
  if (!shouldCompress(jsonPayload)) {
    return { v: 2, c: false, d: jsonPayload };
  }
  const compressed = LZString.compressToEncodedURIComponent(jsonPayload);
  return { v: 2, c: true, d: compressed };
}

/** Decode a stored value into the original JSON string.
 *
 * Accepts three formats:
 *  - v2 envelope with c=false (plain):  `{"v":2,"c":false,"d":"<json>"}`
 *  - v2 envelope with c=true  (compressed): same shape, d is lz-string
 *  - legacy v1 plain SaveSlot JSON: object without a `v` field at root
 *
 * Returns null on malformed input. Detection rule: parse the JSON; if
 * `v === 2` → v2 envelope path; if `v` is absent → legacy v1 (return
 * the original string); if `v` is present but not 2 → malformed (null).
 */
export function decodeEnvelope(stored: string): string | null {
  if (!stored.trimStart().startsWith("{")) return null;
  let parsed: Record<string, unknown>;
  try {
    parsed = JSON.parse(stored) as Record<string, unknown>;
  } catch {
    return null;
  }
  if (parsed["v"] === 2) {
    return decodeV2(parsed);
  }
  if (parsed["v"] === undefined) {
    // Legacy v1: stored JSON is the raw SaveSlot object itself.
    return stored;
  }
  // `v` present but not 2 → malformed envelope.
  return null;
}

function decodeV2(parsed: Record<string, unknown>): string | null {
  const c = parsed["c"];
  const d = parsed["d"];
  if (typeof d !== "string") return null;
  if (c === false) return d;
  if (c === true) {
    try {
      const decompressed = LZString.decompressFromEncodedURIComponent(d);
      return decompressed ?? null;
    } catch {
      return null;
    }
  }
  return null;
}

/**
 * Type guard: parse a stored string into a SaveEnvelope.
 * Returns null for malformed input.
 */
export function parseEnvelope(stored: string): SaveEnvelope | null {
  if (!stored.trimStart().startsWith("{")) return null;
  try {
    const parsed = JSON.parse(stored) as Record<string, unknown>;
    if (parsed["v"] !== 2) return null;
    const c = parsed["c"];
    const d = parsed["d"];
    if (typeof d !== "string") return null;
    if (c === true) return { v: 2, c: true, d };
    if (c === false) return { v: 2, c: false, d };
    return null;
  } catch {
    return null;
  }
}
