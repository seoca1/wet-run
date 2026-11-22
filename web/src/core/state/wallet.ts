/** The material wallet, carried across runs (ADR-0323).
 *
 * The measured problem. A run's drops land in `state.inventory.materials`, and
 * the menu's wallet was REPLACED at jack-in (`this.inventory = initial.inventory`
 * — seeded from the mission's reward) and never written back. So the 28 loot
 * items accumulated inside a run and evaporated at its end: the drops existed to
 * be looked at.
 *
 * The owner's decision: **preserve them**, win or lose. That is what makes a
 * long-term equipment goal possible at all — with a per-run reset, no recipe can
 * ask for more than one run's yield, which the crafting probe measured at ~3
 * data_fragment and ~5 ice_shard.
 *
 * What is preserved is what the run EARNED, not the reward it was seeded with.
 * Jacking out immediately must not mint the mission's reward into the hoard, so
 * the merge subtracts the seed rather than assigning the run's wallet back.
 */
import type { Inventory, Program } from "../types";

/** Material stacks: add, dropping anything that nets to zero or less. */
export function addStacks(
  a: Readonly<Record<string, number>>,
  b: Readonly<Record<string, number>>,
): Record<string, number> {
  const out: Record<string, number> = {};
  for (const [k, v] of Object.entries(a)) {
    const n = Math.floor(Number(v));
    if (Number.isFinite(n) && n > 0) out[k] = n;
  }
  for (const [k, v] of Object.entries(b)) {
    const n = Math.floor(Number(v));
    if (!Number.isFinite(n) || n <= 0) continue;
    out[k] = (out[k] ?? 0) + n;
  }
  return out;
}

/** The wallet a run starts with: the hoard plus the mission's own reward.
 *
 * The hoard rides along so the run can see (and eventually spend) it; the seed
 * is remembered by the caller so the merge can tell earning from inheritance. */
export function seedRunWallet(
  menu: Inventory,
  reward: {
    readonly credits: number;
    readonly materials: Readonly<Record<string, number>>;
  },
): Inventory {
  return {
    credits: Math.max(0, Math.floor(menu.credits)) + Math.max(0, Math.floor(reward.credits)),
    materials: addStacks(menu.materials, reward.materials),
    programs: [...menu.programs],
  };
}

/** What a run's seed spans (ADR-0338): the sum of EVERY contract leg's reward,
 *  or the single mission's reward when there is no contract.
 *
 *  This lived inline in `main.ts` and was the one piece of the wallet math with
 *  no unit test — a mutation of the seed sum would have SURVIVED. Pulled out as
 *  a pure function so `tests/adr0338_run_seed.test.ts` can pin it. */
export function contractSeedMaterials(
  legs:
    | ReadonlyArray<{
        readonly mission: {
          readonly rewards: { readonly materials: Readonly<Record<string, number>> };
        };
      }>
    | undefined,
  missionRewardMaterials: Readonly<Record<string, number>>,
): Record<string, number> {
  if (legs === undefined || legs.length === 0) {
    return addStacks({}, missionRewardMaterials);
  }
  return legs.reduce<Record<string, number>>(
    (acc, leg) => addStacks(acc, leg.mission.rewards.materials),
    {},
  );
}

/** What a run EARNED, never negative: the run's stacks minus the seed's. */
export function earnedMaterials(
  run: Readonly<Record<string, number>>,
  seed: Readonly<Record<string, number>>,
): Record<string, number> {
  const out: Record<string, number> = {};
  for (const [k, v] of Object.entries(run)) {
    const gained = Math.floor(Number(v)) - Math.floor(Number(seed[k] ?? 0));
    if (Number.isFinite(gained) && gained > 0) out[k] = gained;
  }
  return out;
}

/** The hoard after a run: what it already held, plus what the run earned.
 *
 * ADR-0323: the merge subtracts the seed rather than assigning the run's wallet
 * back, so jacking out on frame one mints nothing.
 *
 * ADR-0330: the hoard is `menu + (run - seed)` PER MATERIAL, not
 * `menu + max(0, run - seed)`. The difference matters the moment a run can
 * SPEND a hoard item (a consumable): the clamping form cannot express a spend,
 * so the item would be consumed for free. Subtracting the seed first keeps both
 * halves — an inherited stack is not minted, and a spent one is gone.
 *
 * Credits are deliberately NOT merged: nothing earns into `inventory.credits`
 * during a run, and the mission's reward is not the run's to keep until the job
 * is done. Materials are the axis this decision is about. */
export function mergeRunIntoWallet(
  menu: Inventory,
  run: Inventory | null,
  seed: Inventory | null,
): Inventory {
  if (run === null || seed === null) return menu;
  const materials: Record<string, number> = {};
  const keys = new Set([
    ...Object.keys(menu.materials),
    ...Object.keys(run.materials),
    ...Object.keys(seed.materials),
  ]);
  for (const k of keys) {
    const n =
      Math.floor(Number(menu.materials[k] ?? 0)) +
      Math.floor(Number(run.materials[k] ?? 0)) -
      Math.floor(Number(seed.materials[k] ?? 0));
    if (Number.isFinite(n) && n > 0) materials[k] = n;
  }
  const programs: ReadonlyArray<Program> =
    run.programs.length > 0 ? [...run.programs] : [...menu.programs];
  return {
    credits: menu.credits,
    materials: Object.freeze(materials),
    programs,
  };
}

/** Where the hoard lives between sessions. */
const STORAGE_KEY = "wetrun_materials";

/** The stored hoard. An unreadable value degrades to empty, never throws. */
export function readWalletMaterials(): Readonly<Record<string, number>> {
  if (typeof localStorage === "undefined") return {};
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw === null) return {};
    const parsed: unknown = JSON.parse(raw);
    if (parsed === null || typeof parsed !== "object") return {};
    const out: Record<string, number> = {};
    for (const [k, v] of Object.entries(parsed as Record<string, unknown>)) {
      const n = Math.floor(Number(v));
      if (Number.isFinite(n) && n > 0) out[k] = n;
    }
    return out;
  } catch {
    return {};
  }
}

/** Persist the hoard. Storage is a convenience, so failure is silent. */
export function writeWalletMaterials(materials: Readonly<Record<string, number>>): void {
  if (typeof localStorage === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(addStacks(materials, {})));
  } catch {
    // Storage full or blocked.
  }
}
