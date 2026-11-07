/**
 * ADR-0292 — a drop is worth the ICE that dropped it.
 *
 * ADR-0291 closed the information question with an uncomfortable answer: bought
 * intel was worth about zero, because every encounter in a grade dropped from the
 * same pool, so knowing WHICH fight was ahead changed nothing. The fix is not to
 * sell more information — it is to give the information something to say.
 *
 * The reward pool is now weighted toward the tier of the ICE that was beaten:
 * `1 / (1 + |cardTier - iceTier|^2)`. A rare fight is worth more than a routine
 * one, which is the thing a runner can now choose between.
 */
import { describe, expect, it } from "vitest";
import { offeredCardIds, rewardProgram } from "../src/core/state/card_reward";
import { loadProgramsCatalog } from "../src/core/data_loaders";
import type { RewardSource } from "../src/core/state/card_reward";
import programsJson from "../src/data/programs.json" with { type: "json" };

const programs = loadProgramsCatalog(programsJson);

function source(tier: number, node = 3, turn = 5): RewardSource {
  return {
    deck: [],
    drawPile: [],
    discardPile: [],
    mission: { id: "t", seed: 42 } as never,
    turnCount: turn,
    currentNodeIndex: node,
    cardRewardTaken: null,
    iceRoster: [{ tier }],
  };
}

function meanTier(ids: readonly string[]): number {
  const tiers = ids.map((id) => rewardProgram(id)?.tier ?? 1);
  return tiers.reduce((a, b) => a + b, 0) / Math.max(1, tiers.length);
}

describe("ADR-0292 · a drop is worth its ICE", () => {
  it("offers stronger programs for a stronger ICE", () => {
    // Given: the same run, the same node, the same seed.
    // When / Then: a tier-5 fight averages a higher card tier than a tier-1 one
    // across several nodes, so the effect is not one lucky offer.
    let weightedHigher = 0;
    for (const node of [1, 2, 3, 4, 5]) {
      const weak = meanTier(offeredCardIds(source(1, node)));
      const strong = meanTier(offeredCardIds(source(5, node)));
      if (strong > weak) weightedHigher += 1;
      expect(strong).toBeGreaterThanOrEqual(weak);
    }
    expect(weightedHigher).toBeGreaterThanOrEqual(3);
  });

  it("stays deterministic and does not re-roll a taken card", () => {
    // Given: a reward frame.
    const frame = source(4, 7, 11);

    // When: it is asked twice.
    const first = offeredCardIds(frame);
    const second = offeredCardIds(frame);

    // Then: the same three cards come back — a reload cannot farm the offer.
    expect(second).toEqual(first);
    expect(first).toHaveLength(3);
    expect(new Set(first).size).toBe(3);
  });

  it("never offers a program the run already holds", () => {
    // Given: a deck holding one card.
    const held = Object.keys(programs).sort()[0] as string;
    const frame = { ...source(3), deck: [programs[held] as never] };

    // When
    const offers = offeredCardIds(frame);

    // Then
    expect(offers).not.toContain(held);
  });

  it("falls back to a neutral tier when no roster is present", () => {
    // Given: a hand-built state (tests, old saves) with no roster.
    const { iceRoster: _omitted, ...frame } = source(5);

    // When / Then: it still produces a legal offer rather than throwing.
    const offers = offeredCardIds(frame as RewardSource);
    expect(offers).toHaveLength(3);
  });
});
