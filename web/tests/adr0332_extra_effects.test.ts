/** ADR-0332 — the equipment `extraEffect` whitelist.
 *
 * `extraEffect` is authored free text. The proposal's rule is that it is never
 * executed: it resolves through a whitelist, and anything not named there is
 * inert. These tests pin the whitelist and the two wired behaviours' triggers.
 */
import { describe, expect, it } from "vitest";
import {
  NANO_REGEN_HP,
  REVIVE_HP_PCT,
  hasExtraEffect,
  loadoutHasEffect,
  resolveExtraEffects,
} from "../src/core/state/extra_effects";
import { equipOn, makeLoadout } from "../src/core/state/loadout";
import {
  MASTER_BODY,
  NANO_HIVE,
  STARTER_DECK,
} from "../src/core/state/equipment_catalog";
import type { GameState } from "../src/core/types";

const state = (over: Partial<GameState> = {}): GameState =>
  ({ equipmentLoadout: makeLoadout(), ...over }) as unknown as GameState;

describe("resolveExtraEffects — the whitelist", () => {
  it("resolves nothing from empty or unknown text", () => {
    expect(resolveExtraEffects("")).toEqual([]);
    expect(resolveExtraEffects("drop table; delete everything")).toEqual([]);
    expect(resolveExtraEffects("+25% crit")).toEqual([]);
  });

  it("resolves the authored strings", () => {
    expect(resolveExtraEffects("Immune to flatline (one revive per run)")).toEqual([
      "revive_once",
    ]);
    expect(resolveExtraEffects("Heals 2 HP per turn (poison immune)")).toEqual([
      "nano_regen",
    ]);
    expect(resolveExtraEffects("Sees through all ICE. Love is the algorithm.")).toEqual([
      "ice_omniscience",
    ]);
  });

  it("resolves several when the effects were joined", () => {
    const joined =
      "Immune to flatline (one revive per run), +Stealth in Matrix";
    expect([...resolveExtraEffects(joined)].sort()).toEqual([
      "matrix_stealth",
      "revive_once",
    ]);
  });

  it("hasExtraEffect is the membership test", () => {
    expect(hasExtraEffect("Immune to flatline (one revive per run)", "revive_once")).toBe(true);
    expect(hasExtraEffect("Immune to flatline (one revive per run)", "nano_regen")).toBe(false);
  });
});

describe("loadoutHasEffect", () => {
  it("reads the equipped pieces", () => {
    const revive = state({
      equipmentLoadout: equipOn(makeLoadout(), MASTER_BODY).loadout,
    });
    expect(loadoutHasEffect(revive, "revive_once")).toBe(true);
    expect(loadoutHasEffect(revive, "nano_regen")).toBe(false);

    const regen = state({
      equipmentLoadout: equipOn(makeLoadout(), NANO_HIVE).loadout,
    });
    expect(loadoutHasEffect(regen, "nano_regen")).toBe(true);
  });

  it("is false for a loadout with no effects", () => {
    const bare = state({
      equipmentLoadout: equipOn(makeLoadout(), STARTER_DECK).loadout,
    });
    expect(loadoutHasEffect(bare, "revive_once")).toBe(false);
    expect(loadoutHasEffect(bare, "nano_regen")).toBe(false);
  });
});

describe("the wired numbers", () => {
  it("are the authored placeholders", () => {
    expect(NANO_REGEN_HP).toBe(2);
    expect(REVIVE_HP_PCT).toBeGreaterThan(0);
    expect(REVIVE_HP_PCT).toBeLessThanOrEqual(100);
  });
});
