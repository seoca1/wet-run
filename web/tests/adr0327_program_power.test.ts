/** ADR-0327 — the deck's `programPower` bypasses a share of the ICE's armor.
 *
 * `programPower` was the last read-able equipment stat that nothing read: decks
 * whose identity is the deck itself (Ono-Sendai, Militech, Arasaka, the master
 * deck) contributed nothing to a fight. It is wired as an armor SHARE, so it
 * never rewrites a card's base damage (`tier * 5`) — the card-value contract
 * ADR-0320/0304 depends on.
 */
import { describe, expect, it } from "vitest";
import {
  PROGRAM_POWER_ARMOR_BYPASS_CAP_PCT,
  programPowerArmorBypassPct,
} from "../src/core/combat/combat_engine";
import { effectiveDamageFor } from "../src/core/combat/damage_preview";
import { equipOn, makeLoadout } from "../src/core/state/loadout";
import { makeEquipment, makeEquipStats, type Equipment } from "../src/core/state/equipment";
import type { GameState, Ice, Program } from "../src/core/types";

const deck = (programPower: number): Equipment =>
  makeEquipment({
    id: `deck_${programPower}`,
    name: "Test Deck",
    slot: "deck",
    category: "hardware",
    tier: "T1",
    stats: makeEquipStats({ programPower }),
    description: "",
  });

const state = (programPower: number): GameState =>
  ({
    playerCombo: 0,
    statusEffects: [],
    equipmentLoadout:
      programPower === 0
        ? makeLoadout()
        : equipOn(makeLoadout(), deck(programPower)).loadout,
  }) as unknown as GameState;

/** A plain damage card (no pierce / armor_ignore). */
const strike = { id: "exploitish", name: "Strike", tier: 3, cost: 1, effect: "damage" } as unknown as Program;
/** A plated ICE. */
const plated = { id: "plated", name: "Plated", hp: 50, maxHp: 50, armor: 8, tier: 3 } as unknown as Ice;

describe("programPowerArmorBypassPct", () => {
  it("is 0 for non-positive input", () => {
    expect(programPowerArmorBypassPct(0)).toBe(0);
    expect(programPowerArmorBypassPct(-5)).toBe(0);
    expect(programPowerArmorBypassPct(Number.NaN)).toBe(0);
  });

  it("is the programPower itself, up to the cap", () => {
    expect(programPowerArmorBypassPct(5)).toBe(5);
    expect(programPowerArmorBypassPct(35)).toBe(35);
    expect(programPowerArmorBypassPct(150)).toBe(PROGRAM_POWER_ARMOR_BYPASS_CAP_PCT);
  });
});

describe("programPower as armor bypass", () => {
  it("no deck leaves the armor untouched", () => {
    const bare = effectiveDamageFor(state(0), strike, plated);
    expect(bare.effectiveArmor).toBe(8);
    expect(bare.blocked).toBe(false);
  });

  it("a powered deck reduces the armor that applies", () => {
    // 60% of armor 8 → 3 effective.
    const powered = effectiveDamageFor(state(60), strike, plated);
    expect(powered.effectiveArmor).toBe(3);
    expect(powered.armor).toBe(8); // the ICE's own armor is unchanged
  });

  it("never ignores armor entirely (the cap)", () => {
    const maxed = effectiveDamageFor(state(999), strike, plated);
    expect(maxed.effectiveArmor).toBeGreaterThan(0);
    expect(maxed.effectiveArmor).toBe(
      Math.floor((8 * (100 - PROGRAM_POWER_ARMOR_BYPASS_CAP_PCT)) / 100),
    );
  });

  it("more armor bypass means more damage", () => {
    const bare = effectiveDamageFor(state(0), strike, plated);
    const powered = effectiveDamageFor(state(60), strike, plated);
    expect(powered.min).toBeGreaterThan(bare.min);
  });
});
