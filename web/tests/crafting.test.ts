/** Unit tests for the crafting system (Info Market + recipe crafting).
 *
 * Run with: npx vitest run tests/crafting.test.ts
 */
import { describe, it, expect } from "vitest";

import {
  DISCOUNT_DENOM,
  MARKUP_DENOM,
  TIER_TO_MULTIPLIER,
  type Faction,
  type MarketItem,
  type Recipe,
  craftItem,
  discountedPrice,
  makeInfoMarket,
  makeInfoMarketFromData,
  makeMaterialsFromData,
  makeRecipesFromData,
  parseFaction,
  purchaseItem,
  reputationTier,
} from "../src/core/crafting.ts";

// =============================================================================
// Test fixtures — synthetic data the Python prototype loads from JSON
// =============================================================================

/** Synthetic market mirroring data/crafting/market.json. */
const SYNTHETIC_MARKET_RAW: Readonly<Record<string, unknown>> = Object.freeze({
  t1_program: {
    item_id: "t1_program",
    name: "T1 Program",
    price: 100,
    tier_level: 1,
    available: true,
    faction: "hosaka",
    examples: ["wisp", "shield", "probe"],
    description: "Basic street-grade ICE breaker. Hosaka starter.",
  },
  t2_program: {
    item_id: "t2_program",
    name: "T2 Program",
    price: 300,
    tier_level: 2,
    available: true,
    faction: "maas",
    examples: ["hammer", "virus", "worm"],
    description: "Mid-grade offensive tool. Maas custom firmware.",
  },
  t3_program: {
    item_id: "t3_program",
    name: "T3 Program",
    price: 800,
    tier_level: 3,
    available: true,
    faction: "sense_net",
    examples: ["goliath"],
    description: "Heavy combat program. Sense/Net research-grade.",
  },
  t4_program: {
    item_id: "t4_program",
    name: "T4 Program",
    price: 2000,
    tier_level: 4,
    available: true,
    faction: "ta",
    examples: ["wardrone"],
    description: "Corporate-grade ICE. Tessier-Ashpool contract work.",
  },
  t5_program: {
    item_id: "t5_program",
    name: "T5 Program (Kraken)",
    price: null,
    tier_level: 5,
    available: false,
    crafting_only: true,
    faction: "ta",
    note: "T5 programs are crafting only. The Kraken is not for sale.",
  },
});

const MARKET = makeInfoMarketFromData(SYNTHETIC_MARKET_RAW);

/** Recipe list mirroring data/crafting/recipes.json (with materials added). */
const SYNTHETIC_RECIPES_RAW: Readonly<Record<string, unknown>> = Object.freeze({
  _comment: "Test recipe fixture",
  recipes: [
    { item_id: "t1_program", name: "T1 Program", glyph: "·W·", ready: true, tier_level: 1, materials: { ice_shard: 2 } },
    { item_id: "t2_program", name: "T2 Program", glyph: ":H:", ready: false, tier_level: 2, materials: { ice_shard: 3, data_fragment: 1 } },
    { item_id: "t3_program", name: "T3 Program", glyph: "|G|", ready: false, tier_level: 3, materials: { ice_shard: 5, data_fragment: 3, wetware_chip: 1 } },
    { item_id: "t4_program", name: "T4 Program", glyph: "▓W▓", ready: false, tier_level: 4, materials: { data_fragment: 6, rom_echo: 4, biosoft_agent: 2 } },
    { item_id: "t5_kraken", name: "T5 Kraken", glyph: "★K★", ready: false, tier_level: 5, materials: { rom_echo: 5, biosoft_agent: 5, ice_shard: 10 } },
  ],
});

const RECIPES = makeRecipesFromData(SYNTHETIC_RECIPES_RAW);

/** Synthetic material registry mirroring materials.json. */
const SYNTHETIC_MATERIALS_RAW: Readonly<Record<string, unknown>> = Object.freeze({
  _comment: "Hub Materials panel data (ADR-0015).",
  materials: [
    { id: "ice_shard", name: "ICE Shard", need: 5 },
    { id: "data_fragment", name: "Data Fragment", need: 4 },
    { id: "rom_echo", name: "ROM Echo", need: 3 },
    { id: "wetware_chip", name: "Wetware Chip", need: 2 },
    { id: "biosoft_agent", name: "Biosoft Agent", need: 1 },
  ],
});

// =============================================================================
// Reputation tier boundaries (Python `reputation_tier` parity)
// =============================================================================

describe("reputationTier", () => {
  it("returns ALLIED for max positive score (>=80)", () => {
    expect(reputationTier(100)).toBe("ALLIED");
    expect(reputationTier(80)).toBe("ALLIED");
  });

  it("returns FRIENDLY for 50..79", () => {
    expect(reputationTier(79)).toBe("FRIENDLY");
    expect(reputationTier(50)).toBe("FRIENDLY");
  });

  it("returns TRUSTED for 20..49", () => {
    expect(reputationTier(49)).toBe("TRUSTED");
    expect(reputationTier(20)).toBe("TRUSTED");
  });

  it("returns NEUTRAL for -19..+19", () => {
    expect(reputationTier(19)).toBe("NEUTRAL");
    expect(reputationTier(0)).toBe("NEUTRAL");
    expect(reputationTier(-19)).toBe("NEUTRAL");
  });

  it("returns HOSTILE for -49..-20", () => {
    expect(reputationTier(-20)).toBe("HOSTILE");
    expect(reputationTier(-49)).toBe("HOSTILE");
  });

  it("returns ENEMY for -79..-50", () => {
    expect(reputationTier(-50)).toBe("ENEMY");
    expect(reputationTier(-79)).toBe("ENEMY");
  });

  it("returns OUTCAST for max negative score (<=-80)", () => {
    expect(reputationTier(-80)).toBe("OUTCAST");
    expect(reputationTier(-100)).toBe("OUTCAST");
  });

  it("clamps scores outside [-100, +100]", () => {
    expect(reputationTier(500)).toBe("ALLIED");
    expect(reputationTier(-500)).toBe("OUTCAST");
  });
});

// =============================================================================
// Tier multiplier table — frozen reference values
// =============================================================================

describe("TIER_TO_MULTIPLIER", () => {
  it("ALLIED gives 50% off", () => {
    expect(TIER_TO_MULTIPLIER.ALLIED).toBe(0.5);
  });

  it("NEUTRAL gives base price (1.0)", () => {
    expect(TIER_TO_MULTIPLIER.NEUTRAL).toBe(1.0);
  });

  it("OUTCAST gives 50% markup", () => {
    expect(TIER_TO_MULTIPLIER.OUTCAST).toBe(1.5);
  });

  it("matches Python source exactly (7 tiers)", () => {
    expect(Object.keys(TIER_TO_MULTIPLIER).sort()).toEqual([
      "ALLIED",
      "ENEMY",
      "FRIENDLY",
      "HOSTILE",
      "NEUTRAL",
      "OUTCAST",
      "TRUSTED",
    ]);
  });

  it("discount and markup denominators match Python", () => {
    expect(DISCOUNT_DENOM).toBe(200);
    expect(MARKUP_DENOM).toBe(200);
  });
});

// =============================================================================
// discountedPrice — pure pricing function
// =============================================================================

describe("discountedPrice", () => {
  const availableItem: MarketItem = {
    itemId: "test",
    name: "Test",
    basePrice: 100,
    tierLevel: 1,
    available: true,
    faction: "hosaka",
    examples: [],
    description: "",
  };

  it("returns null for crafting-only items", () => {
    expect(discountedPrice({ ...availableItem, available: false }, 0)).toBeNull();
  });

  it("returns null for items without a base price", () => {
    expect(discountedPrice({ ...availableItem, basePrice: null }, 0)).toBeNull();
  });

  it("applies NEUTRAL (no change) at score 0", () => {
    expect(discountedPrice(availableItem, 0)).toBe(100);
  });

  it("applies ALLIED 50% discount at score 100", () => {
    expect(discountedPrice(availableItem, 100)).toBe(50);
  });

  it("applies OUTCAST 50% markup at score -100", () => {
    expect(discountedPrice(availableItem, -100)).toBe(150);
  });

  it("rounds to the nearest integer", () => {
    const odd: MarketItem = { ...availableItem, basePrice: 333 };
    // 333 * 0.5 = 166.5 → 167 (Math.round)
    expect(discountedPrice(odd, 100)).toBe(167);
  });

  it("clamps the result to a minimum of 1 (never free)", () => {
    const penny: MarketItem = { ...availableItem, basePrice: 1 };
    expect(discountedPrice(penny, 100)).toBe(1); // 0.5 → round → 1 → clamp
  });
});

// =============================================================================
// parseFaction — defensive schema normalization
// =============================================================================

describe("parseFaction", () => {
  it("accepts all four known factions", () => {
    expect(parseFaction("hosaka")).toBe("hosaka");
    expect(parseFaction("maas")).toBe("maas");
    expect(parseFaction("sense_net")).toBe("sense_net");
    expect(parseFaction("ta")).toBe("ta");
  });

  it("returns null for unknown strings", () => {
    expect(parseFaction("ziggurat")).toBeNull();
    expect(parseFaction("")).toBeNull();
  });

  it("returns null for null / undefined input", () => {
    expect(parseFaction(null)).toBeNull();
    expect(parseFaction(undefined)).toBeNull();
  });
});

// =============================================================================
// makeInfoMarketFromData — JSON normalization
// =============================================================================

describe("makeInfoMarketFromData", () => {
  it("loads all 5 items from synthetic fixture", () => {
    expect(MARKET.allItems()).toHaveLength(5);
  });

  it("marks T5 as crafting-only (available=false, price=null)", () => {
    const t5 = MARKET.get("t5_program");
    expect(t5?.available).toBe(false);
    expect(t5?.basePrice).toBeNull();
  });

  it("exposes only available items via availableItems()", () => {
    const available = MARKET.availableItems();
    expect(available).toHaveLength(4);
    expect(available.every((it) => it.available)).toBe(true);
    expect(available.some((it) => it.itemId === "t5_program")).toBe(false);
  });

  it("skips malformed entries without throwing", () => {
    const dirty = makeInfoMarketFromData({
      good: { item_id: "good", name: "Good", price: 50, tier_level: 1, available: true, faction: "hosaka" },
      not_an_object: "garbage",
      null_value: null,
      bad_faction: { item_id: "bad", name: "Bad", price: 10, tier_level: 1, available: true, faction: "ziggurat" },
    });
    expect(dirty.get("good")?.basePrice).toBe(50);
    expect(dirty.get("bad")?.faction).toBeNull();
  });

  it("skips _comment-style metadata keys", () => {
    const withComment = makeInfoMarketFromData({
      _comment: "ignored",
      real: { item_id: "real", name: "Real", price: 10, tier_level: 1, available: true, faction: "maas" },
    });
    expect(withComment.allItems()).toHaveLength(1);
    expect(withComment.get("real")?.name).toBe("Real");
  });

  it("returns empty market for empty input", () => {
    const empty = makeInfoMarketFromData({});
    expect(empty.allItems()).toHaveLength(0);
  });
});

// =============================================================================
// InfoMarket.priceFor — faction-aware pricing
// =============================================================================

describe("InfoMarket.priceFor", () => {
  const NEUTRAL: Readonly<Record<string, number>> = Object.freeze({ hosaka: 0, maas: 0, sense_net: 0, ta: 0 });
  const ALLIED_HOSAKA: Readonly<Record<string, number>> = Object.freeze({ hosaka: 100, maas: 0, sense_net: 0, ta: 0 });
  const HOSTILE_TA: Readonly<Record<string, number>> = Object.freeze({ hosaka: 0, maas: 0, sense_net: 0, ta: -100 });

  it("returns base price when no faction has reputation", () => {
    expect(MARKET.priceFor("t1_program", {})).toBe(100);
  });

  it("returns NEUTRAL price when faction score is 0", () => {
    expect(MARKET.priceFor("t1_program", NEUTRAL)).toBe(100);
  });

  it("applies ALLIED discount on the matching faction", () => {
    // t1_program (hosaka, base 100) at score 100 → 50
    expect(MARKET.priceFor("t1_program", ALLIED_HOSAKA)).toBe(50);
  });

  it("applies OUTCAST markup on the matching faction", () => {
    // t4_program (ta, base 2000) at score -100 → 3000
    expect(MARKET.priceFor("t4_program", HOSTILE_TA)).toBe(3000);
  });

  it("returns null for crafting-only items", () => {
    expect(MARKET.priceFor("t5_program", NEUTRAL)).toBeNull();
  });

  it("returns null for unregistered item ids", () => {
    expect(MARKET.priceFor("nonexistent", NEUTRAL)).toBeNull();
  });
});

// =============================================================================
// Purchase flow — credits decrement + atomic failure modes
// =============================================================================

describe("purchaseItem", () => {
  const NEUTRAL: Readonly<Record<string, number>> = Object.freeze({ hosaka: 0, maas: 0, sense_net: 0, ta: 0 });

  it("returns ok=true with new credit balance on success", () => {
    const result = purchaseItem(MARKET, "t1_program", NEUTRAL, 500);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.newCredits).toBe(400);
      expect(result.itemId).toBe("t1_program");
    }
  });

  it("refuses unknown item ids", () => {
    const result = purchaseItem(MARKET, "t7_phantom", NEUTRAL, 5000);
    expect(result).toEqual({ ok: false, reason: "not_found" });
  });

  it("refuses crafting-only items", () => {
    const result = purchaseItem(MARKET, "t5_program", NEUTRAL, 50000);
    expect(result).toEqual({ ok: false, reason: "not_for_sale" });
  });

  it("refuses insufficient credits (exact amount = ok; one less = fail)", () => {
    const ok = purchaseItem(MARKET, "t1_program", NEUTRAL, 100);
    expect(ok.ok).toBe(true);
    const fail = purchaseItem(MARKET, "t1_program", NEUTRAL, 99);
    expect(fail).toEqual({ ok: false, reason: "insufficient_credits" });
  });

  it("canPurchase matches purchase decision", () => {
    expect(MARKET.canPurchase("t1_program", NEUTRAL, 100)).toBe(true);
    expect(MARKET.canPurchase("t1_program", NEUTRAL, 99)).toBe(false);
    expect(MARKET.canPurchase("t5_program", NEUTRAL, 1_000_000)).toBe(false);
    expect(MARKET.canPurchase("nonexistent", NEUTRAL, 1_000_000)).toBe(false);
  });

  it("applies reputation discount to the purchase (cheaper when allied)", () => {
    const ALLIED_HOSAKA: Readonly<Record<string, number>> = Object.freeze({
      hosaka: 100,
      maas: 0,
      sense_net: 0,
      ta: 0,
    });
    // t1 (100 base, ALLIED hosaka → 50). 49 credits → fails (insufficient).
    expect(purchaseItem(MARKET, "t1_program", ALLIED_HOSAKA, 49)).toEqual({
      ok: false,
      reason: "insufficient_credits",
    });
    // 50 credits → succeeds, leaving 0.
    expect(purchaseItem(MARKET, "t1_program", ALLIED_HOSAKA, 50)).toEqual({
      ok: true,
      newCredits: 0,
      itemId: "t1_program",
    });
  });
});

// =============================================================================
// makeRecipesFromData — recipe normalization
// =============================================================================

describe("makeRecipesFromData", () => {
  it("loads 5 tier recipes from fixture", () => {
    expect(RECIPES).toHaveLength(5);
  });

  it("preserves recipe names + glyphs", () => {
    expect(RECIPES[0]?.name).toBe("T1 Program");
    expect(RECIPES[0]?.glyph).toBe("·W·");
  });

  it("exposes material costs on each recipe", () => {
    const t3 = RECIPES.find((r) => r.itemId === "t3_program");
    expect(t3?.materials).toEqual({ ice_shard: 5, data_fragment: 3, wetware_chip: 1 });
  });

  it("reflects `ready` flag from JSON", () => {
    expect(RECIPES[0]?.ready).toBe(true);
    expect(RECIPES[1]?.ready).toBe(false);
  });

  it("derives item_id from slugified name when JSON omits it", () => {
    const data = makeRecipesFromData({
      recipes: [{ name: "Foo Bar Baz", glyph: "?", ready: false, tier_level: 1, materials: {} }],
    });
    expect(data[0]?.itemId).toBe("foo_bar_baz");
  });
});

// =============================================================================
// craftItem — material consumption flow
// =============================================================================

describe("craftItem", () => {
  it("consumes materials and returns updated inventory", () => {
    const inventory = { ice_shard: 5, data_fragment: 5 };
    const result = craftItem(RECIPES, "t1_program", inventory);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.newInventory).toEqual({ ice_shard: 3, data_fragment: 5 });
      expect(result.consumedMaterials).toEqual({ ice_shard: 2 });
      expect(result.craftedItemId).toBe("t1_program");
    }
  });

  it("removes materials when count hits zero", () => {
    const inventory = { ice_shard: 2 };
    const result = craftItem(RECIPES, "t1_program", inventory);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.newInventory).not.toHaveProperty("ice_shard");
      expect(result.newInventory.ice_shard).toBeUndefined();
    }
  });

  it("refuses unknown recipes", () => {
    expect(craftItem(RECIPES, "nonexistent", {})).toEqual({ ok: false, reason: "unknown_recipe" });
  });

  it("reports missing materials with full deficit breakdown", () => {
    const inventory = { ice_shard: 1, data_fragment: 5 };
    const result = craftItem(RECIPES, "t2_program", inventory);
    expect(result.ok).toBe(false);
    if (!result.ok && result.reason === "missing_materials") {
      // Need 3 ice_shard, have 1 → deficit 2
      expect(result.missing).toEqual({ ice_shard: 2 });
    } else {
      expect.fail("expected missing_materials failure");
    }
  });

  it("treats empty inventory as zero for every material", () => {
    const result = craftItem(RECIPES, "t1_program", {});
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.reason).toBe("missing_materials");
  });

  it("leaves other materials untouched (surgical deduction)", () => {
    const inventory = { ice_shard: 5, data_fragment: 5, rom_echo: 3, wetware_chip: 2 };
    const result = craftItem(RECIPES, "t1_program", inventory);
    if (result.ok) {
      expect(result.newInventory.data_fragment).toBe(5);
      expect(result.newInventory.rom_echo).toBe(3);
      expect(result.newInventory.wetware_chip).toBe(2);
    } else {
      expect.fail("expected successful craft");
    }
  });

  it("consumes multiple materials in one shot", () => {
    const inventory = { ice_shard: 5, data_fragment: 3, wetware_chip: 1 };
    const result = craftItem(RECIPES, "t3_program", inventory);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.newInventory).toEqual({});
      expect(result.consumedMaterials).toEqual({ ice_shard: 5, data_fragment: 3, wetware_chip: 1 });
    }
  });

  it("is deterministic — no randomness, no clock", () => {
    const inventory = { ice_shard: 5 };
    const a = craftItem(RECIPES, "t1_program", inventory);
    const b = craftItem(RECIPES, "t1_program", inventory);
    expect(a).toEqual(b);
  });
});

// =============================================================================
// Material registry
// =============================================================================

describe("makeMaterialsFromData", () => {
  it("loads all 5 canonical materials", () => {
    const materials = makeMaterialsFromData(SYNTHETIC_MATERIALS_RAW);
    expect(materials).toHaveLength(5);
    expect(materials.map((m) => m.id).sort()).toEqual([
      "biosoft_agent",
      "data_fragment",
      "ice_shard",
      "rom_echo",
      "wetware_chip",
    ]);
  });

  it("preserves `need` field per material", () => {
    const materials = makeMaterialsFromData(SYNTHETIC_MATERIALS_RAW);
    const ice = materials.find((m) => m.id === "ice_shard");
    expect(ice?.need).toBe(5);
  });

  it("skips malformed entries", () => {
    const materials = makeMaterialsFromData({
      materials: [
        { id: "good", name: "Good", need: 3 },
        null,
        "garbage",
        { id: "missing_name", need: 1 },
        { id: "missing_need", name: "M" },
      ],
    });
    expect(materials).toHaveLength(1);
    expect(materials[0]?.id).toBe("good");
  });
});

// =============================================================================
// Pure functional sanity — InfoMarket immutability
// =============================================================================

describe("InfoMarket immutability", () => {
  it("items lookup is frozen (cannot mutate registry in-place)", () => {
    expect(Object.isFrozen(MARKET.items)).toBe(true);
  });

  it("availableItems() returns a frozen array", () => {
    expect(Object.isFrozen(MARKET.availableItems())).toBe(true);
  });

  it("purchaseItem is pure (does not mutate market state)", () => {
    const NEUTRAL: Readonly<Record<string, number>> = Object.freeze({ hosaka: 0, maas: 0, sense_net: 0, ta: 0 });
    const before = MARKET.priceFor("t1_program", NEUTRAL);
    purchaseItem(MARKET, "t1_program", NEUTRAL, 1000);
    const after = MARKET.priceFor("t1_program", NEUTRAL);
    expect(after).toBe(before);
  });
});

// =============================================================================
// Faction round-trip — every item has a known faction
// =============================================================================

describe("faction coverage in synthetic fixture", () => {
  it.each(["hosaka", "maas", "sense_net", "ta"] as const)(
    "recognizes faction %s",
    (f: Faction) => {
      const items = MARKET.allItems().filter((it) => it.faction === f);
      expect(items.length).toBeGreaterThanOrEqual(1);
    },
  );
});

// =============================================================================
// Recipe→Market link — every craftable item should match a market entry
// =============================================================================

describe("recipe↔market consistency", () => {
  it("T1..T4 recipes map to available market items", () => {
    for (const recipe of RECIPES) {
      if (recipe.itemId === "t5_kraken") continue; // crafting-only by design
      const marketItem = MARKET.get(recipe.itemId);
      expect(marketItem, `market missing ${recipe.itemId}`).not.toBeNull();
      expect(marketItem?.tierLevel).toBe(recipe.tierLevel);
    }
  });

  it("T5 Kraken has no market sale (the canonical crafting-only case)", () => {
    const t5 = MARKET.get("t5_kraken");
    if (t5 !== null) {
      expect(t5.available).toBe(false);
    }
    expect(t5?.available ?? false).toBe(false);
  });
});

// =============================================================================
// Recipe declaration sanity — covers t1..t5 with growing material cost
// =============================================================================

describe("recipe material escalation", () => {
  it("higher-tier recipes demand more total materials", () => {
    const totalFor = (id: string): number =>
      Object.values(RECIPES.find((r) => r.itemId === id)?.materials ?? {}).reduce((a, b) => a + b, 0);
    expect(totalFor("t1_program")).toBeLessThan(totalFor("t2_program"));
    expect(totalFor("t2_program")).toBeLessThan(totalFor("t3_program"));
    expect(totalFor("t3_program")).toBeLessThan(totalFor("t4_program"));
    expect(totalFor("t4_program")).toBeLessThan(totalFor("t5_kraken"));
  });

  it("T1 is the only recipe flagged ready in the default fixture", () => {
    const ready = RECIPES.filter((r) => r.ready);
    expect(ready.map((r) => r.itemId)).toEqual(["t1_program"]);
  });
});

// =============================================================================
// makeInfoMarket — direct construction for tests
// =============================================================================

describe("makeInfoMarket", () => {
  it("exposes provided items", () => {
    const sample: Record<string, MarketItem> = {
      a: {
        itemId: "a",
        name: "A",
        basePrice: 10,
        tierLevel: 1,
        available: true,
        faction: null,
        examples: [],
        description: "",
      },
    };
    const m = makeInfoMarket(sample);
    expect(m.get("a")?.name).toBe("A");
    expect(m.allItems()).toHaveLength(1);
  });

  it("returns null for unknown lookups", () => {
    const m = makeInfoMarket({});
    expect(m.get("anything")).toBeNull();
  });
});

// =============================================================================
// Recipe declaration through Recipe type — construction shape
// =============================================================================

describe("Recipe shape", () => {
  it("round-trips a manually constructed Recipe", () => {
    const custom: Recipe = {
      itemId: "x",
      name: "X",
      tierLevel: 2,
      glyph: "*",
      materials: { ice_shard: 1 },
      ready: true,
    };
    const result = craftItem([custom], "x", { ice_shard: 1 });
    expect(result.ok).toBe(true);
  });
});