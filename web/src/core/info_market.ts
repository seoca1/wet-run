/** Info Market — the fixer's storefront (faction-aware pricing).
 *
 * Ports wet_run/prototype/src/wet_run/crafting/info_market.py to
 * TypeScript. The market sells programs / ICE-breakers / data
 * fragments; reputation with the item's faction modifies the price
 * (ALLIED → up to 50% off, HOSTILE → up to 50% markup). T5
 * crafting-only items (the Kraken) are excluded from the storefront.
 *
 * The companion `crafting_flow.ts` module adds the recipe / material
 * consumption flow that the Python prototype only declares in JSON.
 */

export type Faction = "hosaka" | "maas" | "sense_net" | "ta";

export type ReputationTier =
  | "ALLIED"
  | "FRIENDLY"
  | "TRUSTED"
  | "NEUTRAL"
  | "HOSTILE"
  | "ENEMY"
  | "OUTCAST";

export const DISCOUNT_DENOM = 200;
export const MARKUP_DENOM = 200;

export const TIER_TO_MULTIPLIER: Readonly<Record<ReputationTier, number>> = Object.freeze({
  ALLIED: 0.5,
  FRIENDLY: 0.65,
  TRUSTED: 0.85,
  NEUTRAL: 1.0,
  HOSTILE: 1.15,
  ENEMY: 1.35,
  OUTCAST: 1.5,
});

export function reputationTier(score: number): ReputationTier {
  const s = Math.max(-100, Math.min(100, score));
  if (s >= 80) return "ALLIED";
  if (s >= 50) return "FRIENDLY";
  if (s >= 20) return "TRUSTED";
  if (s > -20) return "NEUTRAL";
  if (s > -50) return "HOSTILE";
  if (s > -80) return "ENEMY";
  return "OUTCAST";
}

export interface MarketItem {
  readonly itemId: string;
  readonly name: string;
  readonly basePrice: number | null;
  readonly tierLevel: number;
  readonly available: boolean;
  readonly faction: Faction | null;
  readonly examples: ReadonlyArray<string>;
  readonly description: string;
}

export interface RawMarketEntry {
  readonly item_id?: string;
  readonly name?: string;
  readonly price?: number | null;
  readonly tier_level?: number;
  readonly available?: boolean;
  readonly faction?: string | null;
  readonly examples?: ReadonlyArray<string> | null;
  readonly description?: string;
}

export function discountedPrice(
  item: Pick<MarketItem, "available" | "basePrice">,
  factionScore: number,
): number | null {
  if (!item.available || item.basePrice === null) return null;
  const tier = reputationTier(factionScore);
  const mult = TIER_TO_MULTIPLIER[tier];
  const adjusted = Math.round(item.basePrice * mult);
  return Math.max(1, adjusted);
}

export interface InfoMarket {
  readonly items: Readonly<Record<string, MarketItem>>;
  get(itemId: string): MarketItem | null;
  allItems(): ReadonlyArray<MarketItem>;
  availableItems(): ReadonlyArray<MarketItem>;
  priceFor(itemId: string, factionScores: Readonly<Record<string, number>>): number | null;
  canPurchase(itemId: string, factionScores: Readonly<Record<string, number>>, credits: number): boolean;
}

export type PurchaseResult =
  | { readonly ok: true; readonly newCredits: number; readonly itemId: string }
  | { readonly ok: false; readonly reason: "not_found" | "not_for_sale" | "insufficient_credits" };

export function purchaseItem(
  market: InfoMarket,
  itemId: string,
  factionScores: Readonly<Record<string, number>>,
  credits: number,
): PurchaseResult {
  const item = market.get(itemId);
  if (item === null) return { ok: false, reason: "not_found" };
  const price = market.priceFor(itemId, factionScores);
  if (price === null) return { ok: false, reason: "not_for_sale" };
  if (credits < price) return { ok: false, reason: "insufficient_credits" };
  return { ok: true, newCredits: credits - price, itemId };
}

export function makeInfoMarketFromData(raw: Readonly<Record<string, unknown>>): InfoMarket {
  const items: Record<string, MarketItem> = {};
  for (const [key, payload] of Object.entries(raw)) {
    if (key.startsWith("_")) continue;
    if (payload === null || typeof payload !== "object" || Array.isArray(payload)) continue;
    const entry = payload as RawMarketEntry;
    const faction = parseFaction(entry.faction);
    const basePrice =
      entry.price === null || entry.price === undefined
        ? null
        : Number.isFinite(entry.price)
          ? Math.trunc(entry.price)
          : null;
    const item: MarketItem = {
      itemId: String(entry.item_id ?? key),
      name: String(entry.name ?? key),
      basePrice,
      tierLevel: Number.isFinite(entry.tier_level) ? Math.trunc(entry.tier_level as number) : 1,
      available: entry.available === true,
      faction,
      examples: Array.isArray(entry.examples) ? entry.examples.map(String) : [],
      description: String(entry.description ?? ""),
    };
    items[item.itemId] = item;
  }
  return makeInfoMarket(items);
}

export function makeInfoMarket(items: Readonly<Record<string, MarketItem>>): InfoMarket {
  const lookup = Object.freeze({ ...items });
  const allItemsSnapshot = Object.freeze(Object.values(lookup));
  return Object.freeze({
    items: lookup,
    get(itemId: string): MarketItem | null {
      return lookup[itemId] ?? null;
    },
    allItems(): ReadonlyArray<MarketItem> {
      return allItemsSnapshot;
    },
    availableItems(): ReadonlyArray<MarketItem> {
      return Object.freeze(allItemsSnapshot.filter((it) => it.available));
    },
    priceFor(itemId: string, factionScores: Readonly<Record<string, number>>): number | null {
      const item = lookup[itemId];
      if (item === undefined) return null;
      if (item.faction === null) {
        if (!item.available || item.basePrice === null) return null;
        return Math.max(1, item.basePrice);
      }
      const score = factionScores[item.faction] ?? 0;
      return discountedPrice(item, score);
    },
    canPurchase(itemId: string, factionScores: Readonly<Record<string, number>>, credits: number): boolean {
      const price = this.priceFor(itemId, factionScores);
      return price !== null && credits >= price;
    },
  });
}

export function parseFaction(value: string | null | undefined): Faction | null {
  if (value === null || value === undefined) return null;
  switch (value) {
    case "hosaka":
    case "maas":
    case "sense_net":
    case "ta":
      return value;
    default:
      return null;
  }
}