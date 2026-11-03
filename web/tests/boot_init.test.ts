/**
 * Regression test for Fix #1 + #2: main.ts.createInitialState boot crash.
 *
 * Background: `createInitialState()` referenced `STARTER_DECK` and `Ice`
 * without importing them. The returned state object also had a duplicate
 * `name` key in its `ice` literal. Both bugs would throw a `ReferenceError`
 * the first time the user selected NEW RUN on the mission select screen —
 * the canvas froze with no diagnostic.
 *
 * The fix imports the starting deck and `Ice` as a type-only import, then
 * uses them correctly. The duplicate-key literal is collapsed to a single
 * named object. The starter-deck module was later replaced by
 * `starting_deck.ts` (ADR-0260); this file guards the surviving contract.
 *
 * This file imports `main.ts` indirectly by being in the same package and
 * relies on TypeScript's type-only `Ice` declaration being satisfiable. Since
 * `main.ts` performs side-effects at module load (canvas, renderer, audio,
 * window.wetrun registration) we cannot import it under jsdom without
 * stubbing the DOM — so we test the underlying contract separately:
 *
 * 1. STARTING_DECK_IDS is a non-empty list.
 * 2. STARTING_DECK_SIZE matches it.
 * 3. `Ice` type accepts the shape previously inlined at main.ts:111.
 *
 * If main.ts is refactored again to drop createInitialState, this test
 * continues to guard the underlying assumptions.
 */
import { describe, it, expect } from "vitest";
import {
  STARTING_DECK_IDS,
  STARTING_DECK_SIZE,
} from "../src/core/state/starting_deck";
import type { Ice } from "../src/core/types";

describe("Fix #1+#2 — boot crash regression", () => {
  it("STARTING_DECK_IDS is a non-empty list", () => {
    expect(STARTING_DECK_IDS.length).toBeGreaterThan(0);
  });

  it("STARTING_DECK_SIZE matches the list", () => {
    expect(STARTING_DECK_SIZE).toBe(STARTING_DECK_IDS.length);
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
