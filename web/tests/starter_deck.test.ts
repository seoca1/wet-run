/**
 * Tests for the starter deck constant used by main.ts.createInitialState.
 */
import { describe, it, expect } from "vitest";
import { STARTER_DECK, STARTER_HAND_SIZE } from "../src/core/starter_deck.ts";
import type { Program } from "../src/core/types.ts";

describe("starter_deck", () => {
  it("exports 8 frozen programs", () => {
    expect(STARTER_DECK).toHaveLength(8);
    expect(Object.isFrozen(STARTER_DECK)).toBe(true);
  });

  it("every entry satisfies the Program interface", () => {
    for (const p of STARTER_DECK) {
      const required: (keyof Program)[] = ["id", "name", "tier", "cost", "effect", "description", "aoe"];
      for (const key of required) {
        expect(p[key], `${p.id} missing ${String(key)}`).toBeDefined();
      }
      expect(typeof p.id).toBe("string");
      expect(p.id.length).toBeGreaterThan(0);
    }
  });

  it("ids are unique", () => {
    const ids = new Set(STARTER_DECK.map((p) => p.id));
    expect(ids.size).toBe(STARTER_DECK.length);
  });

  it("STARTER_HAND_SIZE is positive and not larger than the deck", () => {
    expect(STARTER_HAND_SIZE).toBeGreaterThan(0);
    expect(STARTER_HAND_SIZE).toBeLessThanOrEqual(STARTER_DECK.length);
  });

  it("tier 1 constraint (currently MVP scope)", () => {
    for (const p of STARTER_DECK) {
      expect(p.tier, `${p.id} tier`).toBe(1);
    }
  });
});
