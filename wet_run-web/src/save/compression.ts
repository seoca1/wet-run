/** Save compression using LZ-string (Tier 5).
 *
 * Compresses save JSON to reduce IndexedDB storage size.
 * Typical compression ratio: 50-70% for game state JSON.
 */
import { compressToUTF16, decompressFromUTF16 } from "lz-string";

/** Compress a JSON string using LZ-string UTF16 encoding. */
export function compressSave(json: string): string {
  return compressToUTF16(json);
}

/** Decompress a compressed save string back to JSON. */
export function decompressSave(compressed: string): string {
  return decompressFromUTF16(compressed);
}

/** Check if a string appears to be compressed (contains non-ASCII chars typical of LZ-string). */
export function isCompressed(str: string): boolean {
  // LZ-string UTF16 output contains chars outside ASCII range
  for (let i = 0; i < Math.min(str.length, 100); i++) {
    if (str.charCodeAt(i) > 127) return true;
  }
  return false;
}