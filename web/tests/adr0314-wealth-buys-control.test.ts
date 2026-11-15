/**
 * ADR-0314 — wealth alone buys control.
 *
 * The control branch required `hp > 75% AND credits > 5000`. Measured on 2330
 * endings (per-cell, 64 seeds, optimal policy): credits > 5000 in 260 endings,
 * hp > 75% in 419, and BOTH in **0**. The two are anti-correlated by
 * construction — credits come from fighting, fighting costs HP — so the branch
 * was structurally dead and the `control` ending never appeared.
 *
 * These tests pin the new gate (wealth alone) and keep the old boundary
 * honest: a poor run still falls through to status_quo.
 */
import { describe, expect, it } from "vitest";
import { resolveEnding } from "../src/core/combat/ending_resolver";

function endingAt(credits: number, hp: number, maxHp = 100) {
  return resolveEnding({
    arc: 4,
    hp,
    maxHp,
    credits,
    missionsCompleted: 1,
    totalDeaths: 0,
    factionScores: {},
    choices: [],
  });
}

describe("ADR-0314 · wealth decides control", () => {
  it("a rich run gets control even when it is hurt", () => {
    // Given: 6,000cr but only 40% HP — the shape every real rich run has.
    const ending = endingAt(6000, 40);

    // Then: control, not the status_quo fallback.
    expect(ending.category).toBe("control");
  });

  it("a poor run at full HP still falls through", () => {
    expect(endingAt(2000, 100).category).toBe("status_quo");
  });

  it("the threshold is exclusive at 5,000", () => {
    expect(endingAt(5000, 40).category).toBe("status_quo");
    expect(endingAt(5001, 40).category).toBe("control");
  });
});
