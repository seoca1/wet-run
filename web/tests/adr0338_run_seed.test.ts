/** ADR-0338 — the run's wallet seed spans the WHOLE contract.
 *
 * The seed lived inline in `main.ts`, which has no unit tests, so it was the one
 * piece of the wallet math a mutation could not reach (ADR-0345 found the hole).
 * It is now `contractSeedMaterials` in `wallet.ts`, pinned here: the seed is the
 * sum of every leg's reward (or the single mission's, with no contract), which
 * is what lets `mergeRunIntoWallet` bank earnings and never mint a reward.
 */
import { describe, expect, it } from "vitest";
import type { Inventory } from "../src/core/types";
import {
  addStacks,
  contractSeedMaterials,
  mergeRunIntoWallet,
  seedRunWallet,
} from "../src/core/state/wallet";

const inv = (materials: Readonly<Record<string, number>>): Inventory => ({
  credits: 0,
  materials,
  programs: [],
});
const leg = (materials: Readonly<Record<string, number>>) => ({
  mission: { rewards: { credits: 0, materials } },
});

describe("ADR-0338 · the run seed spans the whole contract", () => {
  it("no contract: the seed is the single mission's reward", () => {
    expect(contractSeedMaterials(undefined, { data_fragment: 5 })).toEqual({
      data_fragment: 5,
    });
  });

  it("a contract: the seed sums EVERY leg's reward", () => {
    const mats = contractSeedMaterials(
      [leg({ data_fragment: 5 }), leg({ data_fragment: 3, ice_shard: 1 }), leg({ ice_shard: 2 })],
      { data_fragment: 999 }, // ignored when a contract exists
    );
    expect(mats).toEqual({ data_fragment: 8, ice_shard: 3 });
  });

  it("jacking out on frame one mints nothing (the seed spans the rewards)", () => {
    const hoard = inv({ data_fragment: 4 });
    const legs = [leg({ data_fragment: 5 }), leg({ data_fragment: 3, ice_shard: 1 })];
    const seed = seedRunWallet(hoard, {
      credits: 0,
      materials: contractSeedMaterials(legs, {}),
    });
    // The run ends holding exactly the seed (jack out immediately).
    const after = mergeRunIntoWallet(hoard, seed, seed);
    expect(after.materials).toEqual({ data_fragment: 4 });
  });

  it("a run that earns banks only the earnings", () => {
    const hoard = inv({ data_fragment: 4 });
    const legs = [leg({ data_fragment: 5 }), leg({ data_fragment: 3 })];
    const seed = seedRunWallet(hoard, {
      credits: 0,
      materials: contractSeedMaterials(legs, {}),
    });
    const run = { ...seed, materials: addStacks(seed.materials, { data_fragment: 7 }) };
    const after = mergeRunIntoWallet(hoard, run, seed);
    expect(after.materials).toEqual({ data_fragment: 11 }); // 4 hoard + 7 earned
  });
});
