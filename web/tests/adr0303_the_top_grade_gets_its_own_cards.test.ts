/**
 * ADR-0303 — the top grade gets cards of its own.
 *
 * ADR-0302 measured the skill gap (how much better the run goes when the choices
 * are used) and read +40pp at g3-g4 but only +2.8 at g6. The reason was visible
 * in the data: every program in the catalog is tier 5 or below, so at g6 the drop
 * weighting (ADR-0292) had no distance left to exploit and the offer was the same
 * as anywhere else.
 *
 * Three tier-6 programs are the g6 axis. They are not bigger versions of each
 * other -- all three hit for 30 -- they are three answers to the same hit: armor,
 * body, or the hit itself. Picking one is picking what the deck cannot do, and
 * since ADR-0296 burns the strongest card for capacity, a g6 runner now has
 * something worth burning.
 *
 * Two measurements shaped them:
 *  - at the same weight as everything else they flooded the offer and completion
 *    at g6 fell 9.7 -> 6.9; a unique is a find, not a flood, so it is weighted
 *    0.35;
 *  - at 4 COST they were unusable, because the trace (ADR-0294) is what binds at
 *    g6. At 2 COST the skill gap there goes +5.6 (no uniques) -> +9.7.
 */
import { describe, expect, it } from "vitest";
import {
  UNIQUE_MIN_ICE_TIER,
  UNIQUE_PROGRAMS,
  offeredCardIds,
  rewardProgram,
} from "../src/core/state/card_reward";
import { programEffect } from "../src/core/combat/program_effects";
import type { RewardSource } from "../src/core/state/card_reward";
import { deckForGrade } from "../scripts/balance_sim";
import { loadProgramsCatalog } from "../src/core/data_loaders";
import programsJson from "../src/data/programs.json" with { type: "json" };

const programs = loadProgramsCatalog(programsJson);

function source(tier: number): RewardSource {
  return {
    deck: [],
    drawPile: [],
    discardPile: [],
    mission: { id: "t", seed: 42 } as never,
    turnCount: 5,
    currentNodeIndex: 3,
    cardRewardTaken: null,
    iceRoster: [{ tier }],
  };
}

describe("ADR-0303 · g6-only programs", () => {
  it("never drops below the top grade", () => {
    // Given / When: every offer a g1-g5 fight can produce.
    for (const tier of [1, 2, 3, 4, 5]) {
      for (let node = 1; node <= 40; node += 1) {
        const offers = offeredCardIds({ ...source(tier), currentNodeIndex: node });
        for (const id of offers) expect(UNIQUE_PROGRAMS.has(id)).toBe(false);
      }
    }

    // Then: the gate is the top-band ICE tier.
    expect(UNIQUE_MIN_ICE_TIER).toBe(6);
  });

  it("can drop from a tier-6 fight", () => {
    // Given / When: enough g6 offers that the 0.35 weight must surface one.
    let sawUnique = false;
    for (let node = 1; node <= 200 && !sawUnique; node += 1) {
      const offers = offeredCardIds({ ...source(6), currentNodeIndex: node });
      sawUnique = offers.some((id) => UNIQUE_PROGRAMS.has(id));
    }

    // Then
    expect(sawUnique).toBe(true);
  });

  it("gives each unique a real mechanic, not a bigger number", () => {
    // Given / When / Then: all three hit for the same 30, so the difference has to
    // be the effect — armor, body, or the hit itself.
    const kinds = new Set<string>();
    for (const id of UNIQUE_PROGRAMS) {
      const card = rewardProgram(id);
      expect(card).toBeDefined();
      expect(card?.tier).toBe(6);
      expect(programEffect({ id }).kind).not.toBe("damage");
      kinds.add(programEffect({ id }).kind);
    }
    expect(kinds.size).toBe(UNIQUE_PROGRAMS.size);
  });

  it("keeps the uniques out of the reference decks", () => {
    // Given / When: the grade-appropriate deck the balance harness builds.
    for (const grade of [1, 2, 3, 4, 5, 6]) {
      const deck = deckForGrade(programs, grade);

      // Then: a unique is a find, never a starting card.
      for (const card of deck) expect(UNIQUE_PROGRAMS.has(card.id)).toBe(false);
    }
  });
});
