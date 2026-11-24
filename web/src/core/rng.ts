/** Seeded PRNG — the single implementation (refactor 2026-11-24).
 *
 * mulberry32 had been copy-pasted into six modules, in two bit conventions:
 * `seed | 0` in the dungeon/event code and `seed >>> 0` in the harnesses. The two
 * are behaviourally identical — every later use of the state goes through a
 * bitwise operation, which reinterprets the same 32 bits — so the streams agree
 * for every seed, negative ones included. The balance and gear goldens are the
 * proof the move did not change any stream: they are byte-identical after it.
 *
 * This module is a leaf (no imports), so both `src/**` and `scripts/**` can use it.
 */

/** A function returning a float in [0, 1). */
export type Rng = () => number;

/** A function returning an int in [min, max] (inclusive). */
export type RngInt = (min: number, max: number) => number;

/** Mulberry32 — small, fast, deterministic 32-bit RNG. */
export function mulberry32(seed: number): Rng {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Build a paired (rng, int) helper from a base rng. */
export function withInt(rng: Rng): RngInt {
  return (min, max) => {
    if (max < min) {
      throw new RangeError(`rngInt: max (${max}) < min (${min})`);
    }
    return min + Math.floor(rng() * (max - min + 1));
  };
}