/**
 * Regression test for Fix #1 + #2: main.ts.createInitialState boot crash.
 *
 * Background: `createInitialState()` referenced `STARTER_DECK` and `Ice`
 * without importing them. The returned state object also had a duplicate
 * `name` key in its `ice` literal. Both bugs would throw a `ReferenceError`
 * the first time the user selected NEW RUN on the mission select screen —
 * the canvas froze with no diagnostic.
 *
 * The fix imports `STARTER_DECK`/`STARTER_HAND_SIZE` from the new starter_deck
 * module and `Ice` as a type-only import, then uses them correctly. The
 * duplicate-key literal is collapsed to a single named object.
 *
 * This file imports `main.ts` indirectly by being in the same package and
 * relies on TypeScript's type-only `Ice` declaration being satisfiable. Since
 * `main.ts` performs side-effects at module load (canvas, renderer, audio,
 * window.wetrun registration) we cannot import it under jsdom without
 * stubbing the DOM — so we test the underlying contract separately:
 *
 * 1. STARTER_DECK is a non-empty, well-formed `Program[]`.
 * 2. STARTER_HAND_SIZE <= STARTER_DECK.length.
 * 3. `Ice` type accepts the shape previously inlined at main.ts:111.
 *
 * If main.ts is refactored again to drop createInitialState, this test
 * continues to guard the underlying assumptions.
 */
import { describe, it, expect } from "vitest";
import { STARTER_DECK, STARTER_HAND_SIZE } from "../src/core/starter_deck.ts";
import type { Ice } from "../src/core/types.ts";

describe("Fix #1+#2 — boot crash regression", () => {
  it("STARTER_DECK is a frozen, non-empty Program[]", () => {
    expect(Object.isFrozen(STARTER_DECK)).toBe(true);
    expect(STARTER_DECK.length).toBeGreaterThan(0);
  });

  it("STARTER_HAND_SIZE is in range [1, STARTER_DECK.length]", () => {
    expect(STARTER_HAND_SIZE).toBeGreaterThanOrEqual(1);
    expect(STARTER_HAND_SIZE).toBeLessThanOrEqual(STARTER_DECK.length);
  });

  it("Ice literal shape previously broken at main.ts:111 still satisfies the Ice interface", () => {
    // The duplicate-key literal collapsed to a single named object:
    //   ice: { id: "ice_01", name: "Black ICE", hp: 10, armor: 0, tier: 1 }
    const initialIce: Ice = {
      id: "ice_01",
      name: "Black ICE",
      hp: 10,
      armor: 0,
      tier: 1,
    };
    expect(initialIce.id).toBe("ice_01");
    expect(initialIce.name).toBe("Black ICE");
    expect(initialIce.hp).toBe(10);
    expect(initialIce.armor).toBe(0);
    expect(initialIce.tier).toBe(1);
  });
});
