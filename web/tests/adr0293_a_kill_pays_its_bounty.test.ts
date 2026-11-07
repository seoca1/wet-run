/**
 * ADR-0293 — a kill pays its own bounty.
 *
 * ADR-0292 made a drop worth its ICE, which gave the middle grades a reason to
 * pick one fight over another. It could not do that at g6: every card there is
 * already high tier, so "this fight drops better cards" had nothing left to say.
 * The top grade still had room on one axis — money — and money is legible in the
 * fiction: a Neuromancer is worth more than a Watchdog.
 *
 * Credits are not a power lever in combat, so the fitted per-encounter curve is
 * untouched; they buy prep capacity between runs and intel inside one.
 */
import { describe, expect, it } from "vitest";
import { BOUNTY_BY_TIER, bountyFor } from "../src/core/combat/victory";

describe("ADR-0293 · a kill pays its bounty", () => {
  it("pays more for a higher-tier ICE", () => {
    // Given / When / Then: strictly increasing with tier, and a tier-6 kill is
    // worth several routine kills.
    for (let tier = 1; tier < BOUNTY_BY_TIER.length - 1; tier += 1) {
      expect(bountyFor({ tier: tier + 1 })).toBeGreaterThan(
        bountyFor({ tier }),
      );
    }
    expect(bountyFor({ tier: 6 })).toBeGreaterThanOrEqual(
      bountyFor({ tier: 1 }) * 4,
    );
  });

  it("never pays a kill whose tier is unknown or below 1", () => {
    // Given / When / Then: hand-built ICE without a tier cannot mint credits.
    expect(bountyFor({ tier: 0 })).toBe(0);
    expect(bountyFor({ tier: -3 })).toBe(0);
  });

  it("clamps a tier above the table instead of returning undefined", () => {
    // Given / When / Then: a data row with an out-of-range tier still pays.
    expect(bountyFor({ tier: 99 })).toBe(BOUNTY_BY_TIER[BOUNTY_BY_TIER.length - 1]);
  });
});
