/**
 * ADR-0323 — the material hoard outlives the run.
 *
 * The owner's decision: preserve what a run picked up, win or lose. That is the
 * precondition for any equipment goal — the crafting probe measured one run at
 * ~3 data_fragment and ~5 ice_shard, so a per-run reset would cap every recipe
 * at one run's yield.
 *
 * The subtle half is that what is preserved is what the run EARNED, not the
 * reward it was seeded with. Jacking out on the first frame must not mint the
 * mission's reward into the hoard.
 */
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import type { Inventory } from "../src/core/types";
import {
  addStacks,
  earnedMaterials,
  mergeRunIntoWallet,
  readWalletMaterials,
  seedRunWallet,
  writeWalletMaterials,
} from "../src/core/state/wallet";

const inv = (
  credits: number,
  materials: Readonly<Record<string, number>>,
): Inventory => ({ credits, materials, programs: [] });

describe("ADR-0323 · stacks and the seed", () => {
  it("adds stacks and drops anything that is not a positive count", () => {
    expect(addStacks({ a: 2 }, { a: 3, b: 1 })).toEqual({ a: 5, b: 1 });
    expect(addStacks({ a: 2 }, { a: -5, b: 0, c: Number.NaN })).toEqual({ a: 2 });
    expect(addStacks({}, {})).toEqual({});
  });

  it("seeds a run with the hoard PLUS the mission's reward", () => {
    const run = seedRunWallet(inv(120, { data_fragment: 4 }), {
      credits: 2000,
      materials: { upgrade_t3: 1 },
    });
    expect(run.credits).toBe(2120);
    expect(run.materials).toEqual({ data_fragment: 4, upgrade_t3: 1 });
  });

  it("never lets a negative hoard become a negative wallet", () => {
    const run = seedRunWallet(inv(-50, {}), { credits: -10, materials: {} });
    expect(run.credits).toBe(0);
  });
});

describe("ADR-0323 · earning is not inheriting", () => {
  it("reports only what the run gained", () => {
    const seed = { data_fragment: 4, ice_shard: 2 };
    const after = { data_fragment: 9, ice_shard: 2, rom_echo: 1 };
    expect(earnedMaterials(after, seed)).toEqual({ data_fragment: 5, rom_echo: 1 });
  });

  it("never reports a negative gain", () => {
    expect(earnedMaterials({ data_fragment: 1 }, { data_fragment: 6 })).toEqual({});
    expect(earnedMaterials({}, { data_fragment: 6 })).toEqual({});
  });
});

describe("ADR-0323 · the merge back into the hoard", () => {
  it("banks what the run earned", () => {
    const menu = inv(0, { data_fragment: 4 });
    const seed = seedRunWallet(menu, { credits: 0, materials: {} });
    const run = inv(0, { data_fragment: 11, ice_construct: 1 });
    const after = mergeRunIntoWallet(menu, run, seed);
    expect(after.materials).toEqual({ data_fragment: 11, ice_construct: 1 });
    expect(after.credits).toBe(0);
  });

  it("does not mint the mission reward when the run earns nothing", () => {
    // Jack out on frame one: the run's wallet is exactly the seed.
    const menu = inv(0, { data_fragment: 4 });
    const seed = seedRunWallet(menu, { credits: 5000, materials: { upgrade_t2: 1 } });
    const after = mergeRunIntoWallet(menu, seed, seed);
    expect(after.materials).toEqual({ data_fragment: 4 });
  });

  it("leaves the hoard untouched when there was no run", () => {
    const menu = inv(10, { ice_shard: 3 });
    expect(mergeRunIntoWallet(menu, null, null)).toBe(menu);
    expect(mergeRunIntoWallet(menu, null, menu)).toBe(menu);
  });

  it("keeps the hoard's credits (the run does not earn into them)", () => {
    const menu = inv(777, {});
    const seed = seedRunWallet(menu, { credits: 100, materials: {} });
    expect(mergeRunIntoWallet(menu, inv(9999, {}), seed).credits).toBe(777);
  });
});

describe("ADR-0323 · the hoard survives a reload", () => {
  let store: Map<string, string>;
  beforeEach(() => {
    store = new Map<string, string>();
    (globalThis as { localStorage?: unknown }).localStorage = {
      getItem: (k: string) => store.get(k) ?? null,
      setItem: (k: string, v: string) => void store.set(k, v),
      removeItem: (k: string) => void store.delete(k),
      clear: () => store.clear(),
    };
  });
  afterEach(() => {
    delete (globalThis as { localStorage?: unknown }).localStorage;
  });

  it("round-trips the hoard", () => {
    writeWalletMaterials({ data_fragment: 12, ice_shard: 5 });
    expect(readWalletMaterials()).toEqual({ data_fragment: 12, ice_shard: 5 });
  });

  it("degrades to empty on a malformed store", () => {
    store.set("wetrun_materials", "{not json");
    expect(readWalletMaterials()).toEqual({});
    store.set("wetrun_materials", '"data_fragment"');
    expect(readWalletMaterials()).toEqual({});
    store.set("wetrun_materials", '{"data_fragment":-3,"ice_shard":2}');
    expect(readWalletMaterials()).toEqual({ ice_shard: 2 });
  });

  it("does nothing when storage is unavailable", () => {
    delete (globalThis as { localStorage?: unknown }).localStorage;
    expect(readWalletMaterials()).toEqual({});
    expect(() => writeWalletMaterials({ a: 1 })).not.toThrow();
  });
});
