/** ADR-0331 — the material market: credits buy materials during a run.
 *
 * Credits had no sink (the ending resolver was the only reader), so this is the
 * first thing money can actually do. It lives at the loot stop because ADR-0323
 * does not merge credits into the menu wallet.
 */
import { describe, expect, it } from "vitest";
import {
  MATERIAL_OFFERS,
  materialOfferForGrade,
} from "../src/core/state/material_market";
import { LOOT_BUY_SLOT, lootSlotChoice } from "../src/core/state/loot_choice";
import { applyAction } from "../src/core/state/state";
import { runState } from "./view_fixtures";
import type { GameState } from "../src/core/types";

const lootState = (credits: number): GameState => {
  const base = runState({ runPhase: "loot", message: "x" });
  return { ...base, player: { ...base.player, credits } };
};

describe("material market (ADR-0331)", () => {
  it("offers a material per grade band", () => {
    expect(materialOfferForGrade(1)?.materialId).toBe("data_fragment");
    expect(materialOfferForGrade(2)?.materialId).toBe("data_fragment");
    expect(materialOfferForGrade(3)?.materialId).toBe("ice_shard");
    expect(materialOfferForGrade(5)?.materialId).toBe("combat_module");
    expect(materialOfferForGrade(6)?.materialId).toBe("combat_module");
  });

  it("every offer is a real material with a positive price", () => {
    expect(MATERIAL_OFFERS.length).toBeGreaterThan(0);
    for (const o of MATERIAL_OFFERS) {
      expect(o.quantity).toBeGreaterThan(0);
      expect(o.price).toBeGreaterThan(0);
    }
  });

  it("slot 11 is the buy slot", () => {
    expect(LOOT_BUY_SLOT).toBe(11);
    expect(lootSlotChoice(LOOT_BUY_SLOT)).toBe("buy");
  });

  it("buys the grade's offer with the run's credits", () => {
    const offer = materialOfferForGrade(1)!;
    const before = lootState(1000);
    const after = applyAction(before, {
      type: "select_program",
      handIndex: LOOT_BUY_SLOT,
    });
    expect(after.player.credits).toBe(1000 - offer.price);
    expect(after.inventory.materials[offer.materialId]).toBe(offer.quantity);
  });

  it("refuses when the run cannot afford it", () => {
    const offer = materialOfferForGrade(1)!;
    const before = lootState(offer.price - 1);
    const after = applyAction(before, {
      type: "select_program",
      handIndex: LOOT_BUY_SLOT,
    });
    expect(after.player.credits).toBe(offer.price - 1);
    expect(after.inventory.materials[offer.materialId]).toBeUndefined();
    expect(after.message).toContain("costs");
  });

  it("stacks repeat purchases", () => {
    const offer = materialOfferForGrade(1)!;
    const once = applyAction(lootState(1000), {
      type: "select_program",
      handIndex: LOOT_BUY_SLOT,
    });
    const twice = applyAction(once, {
      type: "select_program",
      handIndex: LOOT_BUY_SLOT,
    });
    expect(twice.inventory.materials[offer.materialId]).toBe(offer.quantity * 2);
    expect(twice.player.credits).toBe(1000 - offer.price * 2);
  });
});
