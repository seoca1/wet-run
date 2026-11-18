/** ADR-0330 — consumables, and the spend the hoard merge used to swallow.
 *
 * The dose grants shield pool for the next fight. The other half is a wallet
 * fix: `mergeRunIntoWallet` was `menu + max(0, run - seed)`, which cannot
 * express a SPEND — a run that used a hoard item left the hoard untouched.
 */
import { describe, expect, it } from "vitest";
import {
  CONSUMABLES,
  carriedConsumable,
  consumableFor,
} from "../src/core/state/consumables";
import { LOOT_ITEM_SLOT, lootSlotChoice } from "../src/core/state/loot_choice";
import {
  mergeRunIntoWallet,
  seedRunWallet,
} from "../src/core/state/wallet";
import { applyAction } from "../src/core/state/state";
import { playerShieldPool } from "../src/core/combat/player_mitigation";
import { runState } from "./view_fixtures";
import type { Inventory } from "../src/core/types";

const inv = (
  credits: number,
  materials: Readonly<Record<string, number>>,
): Inventory => ({ credits, materials, programs: [] });

const DOSE = "maas_neuropozyne_dose";

describe("consumables (ADR-0330)", () => {
  it("registers the neuropozyne dose as the first consumable", () => {
    expect(consumableFor(DOSE)?.id).toBe(DOSE);
    expect(CONSUMABLES.length).toBeGreaterThan(0);
    expect(consumableFor("data_fragment")).toBeNull();
  });

  it("carriedConsumable finds what the run holds", () => {
    expect(carriedConsumable({})).toBeNull();
    expect(carriedConsumable({ data_fragment: 9 })).toBeNull();
    expect(carriedConsumable({ [DOSE]: 1 })?.id).toBe(DOSE);
  });

  it("slot 10 is the item slot", () => {
    expect(LOOT_ITEM_SLOT).toBe(10);
    expect(lootSlotChoice(LOOT_ITEM_SLOT)).toBe("item");
  });
});

describe("the hoard merge now records a spend", () => {
  it("a spent hoard item is decremented", () => {
    const menu = inv(0, { [DOSE]: 2 });
    const seed = seedRunWallet(menu, { credits: 0, materials: {} });
    const run = { ...seed, materials: { [DOSE]: 1 } }; // one used
    expect(mergeRunIntoWallet(menu, run, seed).materials).toEqual({ [DOSE]: 1 });
  });

  it("still does not mint the reward on an immediate jack-out", () => {
    const menu = inv(0, { data_fragment: 4 });
    const seed = seedRunWallet(menu, {
      credits: 5000,
      materials: { upgrade_t2: 1 },
    });
    expect(mergeRunIntoWallet(menu, seed, seed).materials).toEqual({
      data_fragment: 4,
    });
  });

  it("still adds what the run earned", () => {
    const menu = inv(0, { data_fragment: 4 });
    const seed = seedRunWallet(menu, { credits: 0, materials: {} });
    const run = { ...seed, materials: { data_fragment: 9, ice_shard: 2 } };
    expect(mergeRunIntoWallet(menu, run, seed).materials).toEqual({
      data_fragment: 9,
      ice_shard: 2,
    });
  });
});

describe("using the dose at the loot stop", () => {
  const lootWithDose = () => {
    const base = runState({ runPhase: "loot", message: "x" });
    return {
      ...base,
      inventory: { ...base.inventory, materials: { [DOSE]: 1 } },
    };
  };

  it("spends the dose and grants shield pool", () => {
    const before = lootWithDose();
    const after = applyAction(before, {
      type: "select_program",
      handIndex: LOOT_ITEM_SLOT,
    });
    expect(after.inventory.materials[DOSE]).toBeUndefined();
    expect(playerShieldPool(after)).toBe(
      Math.floor(before.player.maxHp * 0.25),
    );
  });

  it("does nothing when the run carries no consumable", () => {
    const base = runState({ runPhase: "loot", message: "x" });
    const after = applyAction(base, {
      type: "select_program",
      handIndex: LOOT_ITEM_SLOT,
    });
    expect(playerShieldPool(after)).toBe(0);
    expect(after.message).toBe("Nothing to use.");
  });
});
