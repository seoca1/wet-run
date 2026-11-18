import { describe, it, expect } from "vitest";
import {
  reputationTier,
  discountedPrice,
  purchaseItem,
  makeInfoMarket,
  makeInfoMarketFromData,
  parseFaction,
  TIER_TO_MULTIPLIER,
  DISCOUNT_DENOM,
  MARKUP_DENOM,
  type MarketItem,
} from "../src/core/info_market.ts";

const sampleMarketData = {
  ice_breaker_basic: {
    item_id: "ice_breaker_basic",
    name: "Basic ICE Breaker",
    price: 100,
    tier_level: 1,
    available: true,
    faction: "hosaka",
    description: "Entry level breaker",
  },
  ice_breaker_advanced: {
    item_id: "ice_breaker_advanced",
    name: "Advanced ICE Breaker",
    price: 500,
    tier_level: 3,
    available: true,
    faction: "maas",
    description: "High-end breaker",
  },
  data_fragment: {
    item_id: "data_fragment",
    name: "Data Fragment",
    price: 50,
    tier_level: 1,
    available: true,
    faction: null,
    description: "Raw data",
  },
  kraken_core: {
    item_id: "kraken_core",
    name: "Kraken Core",
    price: null,
    tier_level: 5,
    available: false,
    faction: "ta",
    description: "Crafting only",
  },
};

describe("info_market", () => {
  describe("constants", () => {
    it("DISCOUNT_DENOM is defined", () => {
      expect(DISCOUNT_DENOM).toBe(200);
    });

    it("MARKUP_DENOM is defined", () => {
      expect(MARKUP_DENOM).toBe(200);
    });

    it("TIER_TO_MULTIPLIER is frozen", () => {
      expect(Object.isFrozen(TIER_TO_MULTIPLIER)).toBe(true);
    });

    it("TIER_TO_MULTIPLIER has all tiers", () => {
      expect(TIER_TO_MULTIPLIER.ALLIED).toBe(0.5);
      expect(TIER_TO_MULTIPLIER.FRIENDLY).toBe(0.65);
      expect(TIER_TO_MULTIPLIER.TRUSTED).toBe(0.85);
      expect(TIER_TO_MULTIPLIER.NEUTRAL).toBe(1.0);
      expect(TIER_TO_MULTIPLIER.HOSTILE).toBe(1.15);
      expect(TIER_TO_MULTIPLIER.ENEMY).toBe(1.35);
      expect(TIER_TO_MULTIPLIER.OUTCAST).toBe(1.5);
    });
  });

  describe("reputationTier", () => {
    it("returns ALLIED for score >= 80", () => {
      expect(reputationTier(80)).toBe("ALLIED");
      expect(reputationTier(100)).toBe("ALLIED");
    });

    it("returns FRIENDLY for score 50-79", () => {
      expect(reputationTier(50)).toBe("FRIENDLY");
      expect(reputationTier(79)).toBe("FRIENDLY");
    });

    it("returns TRUSTED for score 20-49", () => {
      expect(reputationTier(20)).toBe("TRUSTED");
      expect(reputationTier(49)).toBe("TRUSTED");
    });

    it("returns NEUTRAL for score -19 to 19", () => {
      expect(reputationTier(0)).toBe("NEUTRAL");
      expect(reputationTier(19)).toBe("NEUTRAL");
      expect(reputationTier(-19)).toBe("NEUTRAL");
    });

    it("returns HOSTILE for score -20 to -49", () => {
      expect(reputationTier(-20)).toBe("HOSTILE");
      expect(reputationTier(-49)).toBe("HOSTILE");
    });

    it("returns ENEMY for score -50 to -79", () => {
      expect(reputationTier(-50)).toBe("ENEMY");
      expect(reputationTier(-79)).toBe("ENEMY");
    });

    it("returns OUTCAST for score <= -80", () => {
      expect(reputationTier(-80)).toBe("OUTCAST");
      expect(reputationTier(-100)).toBe("OUTCAST");
    });

    it("clamps extreme values", () => {
      expect(reputationTier(200)).toBe("ALLIED");
      expect(reputationTier(-200)).toBe("OUTCAST");
    });
  });

  describe("parseFaction", () => {
    it("returns valid factions", () => {
      expect(parseFaction("hosaka")).toBe("hosaka");
      expect(parseFaction("maas")).toBe("maas");
      expect(parseFaction("sense_net")).toBe("sense_net");
      expect(parseFaction("ta")).toBe("ta");
    });

    it("returns null for invalid values", () => {
      expect(parseFaction("unknown")).toBe(null);
      expect(parseFaction("")).toBe(null);
    });

    it("returns null for null/undefined", () => {
      expect(parseFaction(null)).toBe(null);
      expect(parseFaction(undefined)).toBe(null);
    });
  });

  describe("discountedPrice", () => {
    const item: MarketItem = {
      itemId: "test",
      name: "Test",
      basePrice: 100,
      tierLevel: 1,
      available: true,
      faction: "hosaka",
      description: "",
      examples: [],
    };

    it("returns null when not available", () => {
      const unavail = { ...item, available: false };
      expect(discountedPrice(unavail, 0)).toBe(null);
    });

    it("returns null when basePrice is null", () => {
      const noprice = { ...item, basePrice: null };
      expect(discountedPrice(noprice, 0)).toBe(null);
    });

    it("applies ALLIED discount", () => {
      const price = discountedPrice(item, 80);
      expect(price).toBe(50);
    });

    it("applies NEUTRAL multiplier", () => {
      const price = discountedPrice(item, 0);
      expect(price).toBe(100);
    });

    it("applies HOSTILE markup", () => {
      const price = discountedPrice(item, -20);
      expect(price).toBe(115);
    });

    it("applies OUTCAST markup", () => {
      const price = discountedPrice(item, -80);
      expect(price).toBe(150);
    });

    it("rounds price correctly", () => {
      const item2 = { ...item, basePrice: 73 };
      const price = discountedPrice(item2, 80);
      expect(price).toBeGreaterThan(0);
      expect(Number.isInteger(price)).toBe(true);
    });

    it("returns at least 1 credit", () => {
      const cheap = { ...item, basePrice: 1 };
      const price = discountedPrice(cheap, 80);
      expect(price).toBeGreaterThanOrEqual(1);
    });
  });

  describe("makeInfoMarketFromData", () => {
    const market = makeInfoMarketFromData(sampleMarketData);

    it("creates market with items", () => {
      expect(market.allItems().length).toBe(4);
    });

    it("parses item correctly", () => {
      const item = market.get("ice_breaker_basic");
      expect(item?.name).toBe("Basic ICE Breaker");
      expect(item?.basePrice).toBe(100);
      expect(item?.faction).toBe("hosaka");
    });

    it("handles null faction", () => {
      const item = market.get("data_fragment");
      expect(item?.faction).toBe(null);
    });

    it("handles null price", () => {
      const item = market.get("kraken_core");
      expect(item?.basePrice).toBe(null);
    });

    it("handles unavailable items", () => {
      const item = market.get("kraken_core");
      expect(item?.available).toBe(false);
    });

    it("skips underscore keys", () => {
      const data = { _metadata: { version: 1 }, item1: { item_id: "item1", available: true } };
      const m = makeInfoMarketFromData(data);
      expect(m.get("_metadata")).toBe(null);
    });

    it("skips invalid entries", () => {
      const data = { valid: { item_id: "valid" }, invalid: null, invalid2: "string" };
      const m = makeInfoMarketFromData(data);
      expect(m.allItems().length).toBe(1);
    });
  });

  describe("InfoMarket.get", () => {
    const market = makeInfoMarketFromData(sampleMarketData);

    it("returns item by id", () => {
      const item = market.get("ice_breaker_basic");
      expect(item?.itemId).toBe("ice_breaker_basic");
    });

    it("returns null for unknown id", () => {
      expect(market.get("unknown")).toBe(null);
    });
  });

  describe("InfoMarket.allItems", () => {
    const market = makeInfoMarketFromData(sampleMarketData);

    it("returns all items", () => {
      expect(market.allItems().length).toBe(4);
    });

    it("returns frozen array", () => {
      expect(Object.isFrozen(market.allItems())).toBe(true);
    });
  });

  describe("InfoMarket.availableItems", () => {
    const market = makeInfoMarketFromData(sampleMarketData);

    it("filters available items", () => {
      const available = market.availableItems();
      expect(available.length).toBe(3);
      expect(available.every((i) => i.available)).toBe(true);
    });

    it("excludes unavailable", () => {
      const available = market.availableItems();
      expect(available.some((i) => i.itemId === "kraken_core")).toBe(false);
    });

    it("returns frozen array", () => {
      expect(Object.isFrozen(market.availableItems())).toBe(true);
    });
  });

  describe("InfoMarket.priceFor", () => {
    const market = makeInfoMarketFromData(sampleMarketData);

    it("returns null for unknown item", () => {
      expect(market.priceFor("unknown", {})).toBe(null);
    });

    it("returns null for unavailable item", () => {
      expect(market.priceFor("kraken_core", {})).toBe(null);
    });

    it("returns base price for null faction item", () => {
      const price = market.priceFor("data_fragment", {});
      expect(price).toBe(50);
    });

    it("applies faction discount", () => {
      const price = market.priceFor("ice_breaker_basic", { hosaka: 80 });
      expect(price).toBe(50);
    });

    it("uses 0 when faction score missing", () => {
      const price = market.priceFor("ice_breaker_basic", {});
      expect(price).toBe(100);
    });

    it("applies different faction multipliers", () => {
      const neutral = market.priceFor("ice_breaker_basic", { hosaka: 0 });
      const hostile = market.priceFor("ice_breaker_basic", { hosaka: -20 });
      expect(hostile).toBeGreaterThan(neutral ?? 0);
    });
  });

  describe("InfoMarket.canPurchase", () => {
    const market = makeInfoMarketFromData(sampleMarketData);

    it("returns false for unknown item", () => {
      expect(market.canPurchase("unknown", {}, 1000)).toBe(false);
    });

    it("returns false when insufficient credits", () => {
      expect(market.canPurchase("ice_breaker_basic", {}, 50)).toBe(false);
    });

    it("returns true when enough credits", () => {
      expect(market.canPurchase("ice_breaker_basic", {}, 100)).toBe(true);
    });

    it("returns false for unavailable item", () => {
      expect(market.canPurchase("kraken_core", {}, 9999)).toBe(false);
    });

    it("accounts for faction discount", () => {
      expect(market.canPurchase("ice_breaker_basic", { hosaka: 80 }, 50)).toBe(true);
      expect(market.canPurchase("ice_breaker_basic", { hosaka: 80 }, 40)).toBe(false);
    });
  });

  describe("purchaseItem", () => {
    const market = makeInfoMarketFromData(sampleMarketData);

    it("returns not_found for unknown item", () => {
      const result = purchaseItem(market, "unknown", {}, 1000);
      expect(result.ok).toBe(false);
      if (!result.ok) expect(result.reason).toBe("not_found");
    });

    it("returns not_for_sale for unavailable", () => {
      const result = purchaseItem(market, "kraken_core", {}, 1000);
      expect(result.ok).toBe(false);
      if (!result.ok) expect(result.reason).toBe("not_for_sale");
    });

    it("returns insufficient_credits when too poor", () => {
      const result = purchaseItem(market, "ice_breaker_basic", {}, 50);
      expect(result.ok).toBe(false);
      if (!result.ok) expect(result.reason).toBe("insufficient_credits");
    });

    it("succeeds when enough credits", () => {
      const result = purchaseItem(market, "ice_breaker_basic", {}, 100);
      expect(result.ok).toBe(true);
      if (result.ok) {
        expect(result.newCredits).toBe(0);
        expect(result.itemId).toBe("ice_breaker_basic");
      }
    });

    it("deducts correct amount", () => {
      const result = purchaseItem(market, "data_fragment", {}, 200);
      expect(result.ok).toBe(true);
      if (result.ok) expect(result.newCredits).toBe(150);
    });

    it("applies faction discount in purchase", () => {
      const result = purchaseItem(market, "ice_breaker_basic", { hosaka: 80 }, 50);
      expect(result.ok).toBe(true);
      if (result.ok) expect(result.itemId).toBe("ice_breaker_basic");
    });
  });

  describe("edge cases", () => {
    it("handles empty market data", () => {
      const market = makeInfoMarketFromData({});
      expect(market.allItems().length).toBe(0);
      expect(market.get("any")).toBe(null);
    });

    it("handles item with missing fields", () => {
      const data = { minimal: { item_id: "minimal" } };
      const market = makeInfoMarketFromData(data);
      const item = market.get("minimal");
      expect(item?.name).toBe("minimal");
      expect(item?.basePrice).toBe(null);
      expect(item?.tierLevel).toBe(1);
    });

    it("handles extreme reputation scores", () => {
      expect(reputationTier(999)).toBe("ALLIED");
      expect(reputationTier(-999)).toBe("OUTCAST");
    });

    it("price never goes below 1", () => {
      const market = makeInfoMarket({
        cheap: {
          itemId: "cheap",
          name: "Cheap",
          basePrice: 2,
          tierLevel: 1,
          available: true,
          faction: "hosaka",
          description: "",
          examples: [],
        },
      });
      const price = market.priceFor("cheap", { hosaka: 100 });
      expect(price).toBeGreaterThanOrEqual(1);
    });
  });
});
