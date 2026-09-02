/** Crafting flow — recipe execution + material consumption.
 *
 * Ports the recipe / material registry JSON from
 * `prototype/data/crafting/recipes.json` + `materials.json` to a
 * deterministic TypeScript API. The Python prototype only declares
 * recipe metadata for the HUD; this port adds `craftItem` so the
 * Kraken (and any T5 program) can be acquired by consuming
 * materials from the player's inventory.
 *
 * Companion: `info_market.ts` (the storefront side).
 */

export interface Recipe {
  readonly itemId: string;
  readonly name: string;
  readonly tierLevel: number;
  readonly glyph: string;
  readonly materials: Readonly<Record<string, number>>;
  readonly ready: boolean;
}

export type MaterialCosts = Readonly<Record<string, number>>;

export interface RawRecipeEntry {
  readonly item_id?: string;
  readonly name?: string;
  readonly glyph?: string;
  readonly ready?: boolean;
  readonly tier_level?: number;
  readonly materials?: Readonly<Record<string, number>>;
}

export type CraftResult =
  | {
      readonly ok: true;
      readonly newInventory: Readonly<Record<string, number>>;
      readonly consumedMaterials: Readonly<Record<string, number>>;
      readonly craftedItemId: string;
    }
  | { readonly ok: false; readonly reason: "unknown_recipe" | "missing_materials"; readonly missing?: Readonly<Record<string, number>> };

export function craftItem(
  recipes: ReadonlyArray<Recipe>,
  itemId: string,
  inventory: Readonly<Record<string, number>>,
): CraftResult {
  const recipe = recipes.find((r) => r.itemId === itemId);
  if (recipe === undefined) return { ok: false, reason: "unknown_recipe" };

  const missing: Record<string, number> = {};
  for (const [mat, need] of Object.entries(recipe.materials)) {
    const have = inventory[mat] ?? 0;
    const deficit = need - have;
    if (deficit > 0) missing[mat] = deficit;
  }
  if (Object.keys(missing).length > 0) {
    return { ok: false, reason: "missing_materials", missing };
  }

  const newInventory: Record<string, number> = { ...inventory };
  const consumed: Record<string, number> = {};
  for (const [mat, need] of Object.entries(recipe.materials)) {
    const have = newInventory[mat] ?? 0;
    const newCount = have - need;
    if (newCount > 0) {
      newInventory[mat] = newCount;
    } else {
      delete newInventory[mat];
    }
    consumed[mat] = need;
  }
  return {
    ok: true,
    newInventory: Object.freeze(newInventory),
    consumedMaterials: Object.freeze(consumed),
    craftedItemId: recipe.itemId,
  };
}

export function makeRecipesFromData(raw: Readonly<Record<string, unknown>>): ReadonlyArray<Recipe> {
  const list = Array.isArray(raw["recipes"]) ? raw["recipes"] : [];
  const recipes: Recipe[] = [];
  for (const entry of list) {
    if (entry === null || typeof entry !== "object" || Array.isArray(entry)) continue;
    const r = entry as RawRecipeEntry;
    const name = typeof r.name === "string" ? r.name : null;
    if (name === null) continue;
    const itemId = typeof r.item_id === "string" ? r.item_id : slugify(name);
    const tierLevel = Number.isFinite(r.tier_level) ? Math.trunc(r.tier_level as number) : 1;
    const glyph = typeof r.glyph === "string" ? r.glyph : "";
    const ready = r.ready === true;
    const materials: Record<string, number> = {};
    if (r.materials !== null && typeof r.materials === "object" && !Array.isArray(r.materials)) {
      for (const [k, v] of Object.entries(r.materials)) {
        if (Number.isFinite(v)) materials[k] = Math.max(0, Math.trunc(v as number));
      }
    }
    recipes.push(
      Object.freeze({
        itemId,
        name,
        tierLevel,
        glyph: Object.freeze(glyph),
        materials: Object.freeze(materials),
        ready: Object.freeze(ready),
      }) as Recipe,
    );
  }
  return Object.freeze(recipes);
}

export interface MaterialDef {
  readonly id: string;
  readonly name: string;
  readonly need: number;
}

export interface RawMaterialEntry {
  readonly id?: string;
  readonly name?: string;
  readonly need?: number;
}

export function makeMaterialsFromData(
  raw: Readonly<Record<string, unknown>>,
): ReadonlyArray<MaterialDef> {
  const list = Array.isArray(raw["materials"]) ? raw["materials"] : [];
  const out: MaterialDef[] = [];
  for (const entry of list) {
    if (entry === null || typeof entry !== "object" || Array.isArray(entry)) continue;
    const m = entry as RawMaterialEntry;
    if (typeof m.id !== "string" || typeof m.name !== "string") continue;
    if (!Number.isFinite(m.need)) continue;
    out.push(
      Object.freeze({
        id: m.id,
        name: m.name,
        need: Math.max(0, Math.trunc(m.need as number)),
      }) as MaterialDef,
    );
  }
  return Object.freeze(out);
}

function slugify(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}