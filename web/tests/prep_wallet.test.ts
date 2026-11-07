/**
 * ADR-0284 — credits finally have somewhere to go, and it is bounded.
 *
 * ADR-0282's loot `SALVAGE` slot paid credits into the run ledger, and the prep
 * budget (ADR-0283) comes from the mission's advance, so credits bought nothing:
 * salvage was strictly worse than a card or a repair. Those credits now bank
 * into a persistent stockpile the NEXT run's prep can draw on.
 *
 * The bound is the point. At a 50% share of the table a full stockpile moved
 * grade 5 from 31.9% to 51.4% and grade 6 from 18.8% to 29.2% -- it broke the
 * curve ADR-0283 tuned, because those tables are already fitted to their targets
 * and have no headroom. So the stockpile does not stack on a tuned grant: it
 * fills the grades the advance skips, where "nothing offered" used to be.
 */
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
  addPrepWallet,
  PREP_WALLET_BANK_SHARE,
  PREP_WALLET_FLOOR_HP,
  prepWalletContribution,
  readPrepWallet,
  spendPrepWallet,
} from "../src/core/state/prep_wallet";
import { prepGrantFor, PREP_HP_BY_GRADE, PREP_SHIELD_BY_GRADE } from "../src/core/state/prep";

const KEY = "wetrun_prep_wallet";

describe("ADR-0284 · the prep stockpile", () => {
  beforeEach(() => localStorage.removeItem(KEY));
  afterEach(() => localStorage.removeItem(KEY));

  it("starts empty and banks, spends, and floors at zero", () => {
    // Given / When / Then
    expect(readPrepWallet()).toBe(0);
    expect(addPrepWallet(120)).toBe(120);
    expect(readPrepWallet()).toBe(120);
    expect(spendPrepWallet(50)).toBe(70);
    expect(spendPrepWallet(999)).toBe(0);
    expect(readPrepWallet()).toBe(0);
  });

  it("ignores a malformed or negative stored value", () => {
    // Given
    localStorage.setItem(KEY, "not a number");
    expect(readPrepWallet()).toBe(0);
    localStorage.setItem(KEY, "-40");
    expect(readPrepWallet()).toBe(0);
  });

  it("never stacks on a grade the advance already covers", () => {
    // Given: grade 5, whose stim table is 270 and whose target is already fitted.
    const table = PREP_HP_BY_GRADE[4];
    expect(table).toBeGreaterThan(0);

    // When / Then: a huge stockpile adds nothing there.
    expect(prepWalletContribution(table, 100000, PREP_WALLET_FLOOR_HP)).toBe(0);
  });

  it("fills the grades the advance skips, up to the floor", () => {
    // Given: grade 1, where the table is zero ("nothing offered").
    expect(PREP_HP_BY_GRADE[0]).toBe(0);

    // When / Then: the stockpile supplies the floor, and no more than it holds.
    expect(prepWalletContribution(0, 50, PREP_WALLET_FLOOR_HP)).toBe(
      PREP_WALLET_FLOOR_HP,
    );
    expect(prepWalletContribution(0, 4, PREP_WALLET_FLOOR_HP)).toBe(4);
    expect(prepWalletContribution(0, 0, PREP_WALLET_FLOOR_HP)).toBe(0);
  });

  it("does not move the tuned grades (measured: full stockpile leaves g4-g6 identical)", () => {
    // Given / When: each grade with and without a full stockpile.
    for (const grade of [4, 5, 6]) {
      const base = prepGrantFor(grade, "stim", 0);
      const banked = prepGrantFor(grade, "stim", 100000);

      // Then
      expect(banked.total).toBe(base.total);
      expect(banked.fromWallet).toBe(0);
    }
  });

  it("gives a returning runner something on the grades that offered nothing", () => {
    // Given / When
    const cold = prepGrantFor(1, "stim", 0);
    const warm = prepGrantFor(1, "stim", 100);

    // Then: it is the difference between "nothing offered" and a small grant.
    expect(cold.total).toBe(0);
    expect(warm.total).toBeGreaterThan(0);
    expect(warm.fromWallet).toBe(warm.total);
  });

  it("bank is half of a salvage payout and the shield tables are still sized", () => {
    // Then
    expect(PREP_WALLET_BANK_SHARE).toBe(0.5);
    expect(PREP_SHIELD_BY_GRADE).toHaveLength(6);
  });
});
