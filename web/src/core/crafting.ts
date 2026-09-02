/** Crafting system barrel — Info Market + recipe crafting flow.
 *
 * Re-exports the public API from `info_market.ts` (storefront,
 * faction-aware pricing) and `crafting_flow.ts` (recipe execution,
 * material consumption). The Python prototype only declares the
 * market + recipe JSON; this port adds the missing `craftItem`
 * flow so T5 programs (the Kraken) can be acquired by spending
 * materials.
 *
 * Module split keeps each file under the 250 LOC ceiling:
 * - info_market.ts   — pricing + market registry
 * - crafting_flow.ts — recipes + material consumption
 *
 * Pure data — no side effects. Tests pass synthetic markets via
 * `makeInfoMarketFromData` / `makeRecipesFromData` to keep scenarios
 * deterministic.
 */

export {
  DISCOUNT_DENOM,
  MARKUP_DENOM,
  TIER_TO_MULTIPLIER,
  discountedPrice,
  makeInfoMarket,
  makeInfoMarketFromData,
  parseFaction,
  purchaseItem,
  reputationTier,
  type Faction,
  type InfoMarket,
  type MarketItem,
  type PurchaseResult,
  type RawMarketEntry,
  type ReputationTier,
} from "./info_market.ts";

export {
  craftItem,
  makeMaterialsFromData,
  makeRecipesFromData,
  type CraftResult,
  type MaterialCosts,
  type MaterialDef,
  type RawMaterialEntry,
  type RawRecipeEntry,
  type Recipe,
} from "./crafting_flow.ts";