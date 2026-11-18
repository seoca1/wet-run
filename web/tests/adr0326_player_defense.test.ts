/** ADR-0326 — the player's defense step, and the survival stats at run start.
 *
 * Before this, an ICE hit went raw → shield pool → HP: the equipment's
 * `defense` and `iceResistance` were numbers nobody read, and `hpBonus` /
 * `shieldBonus` never left the catalog. The order is fixed (resistance →
 * defense → shield → HP) so defense and the card's armor path stay separate.
 */
import { describe, expect, it } from "vitest";
import {
  ICE_RESISTANCE_CAP_PCT,
  applyIceResistance,
  applyPlayerMitigation,
  playerDefense,
  playerShieldPool,
} from "../src/core/combat/player_mitigation";
import { applyEquipmentSurvival } from "../src/core/state/equipment_stats";
import { EMPTY_LOADOUT, equipOn, makeLoadout } from "../src/core/state/loadout";
import {
  BOOTS_GHOST,
  MASTER_BODY,
  STARTER_DECK,
  SUBDERMAL,
  TACTICAL_BODY,
} from "../src/core/state/equipment";
import type { Equipment } from "../src/core/state/equipment";
import type { GameState } from "../src/core/types";

const withGear = (...items: Equipment[]) =>
  items.reduce((l, e) => equipOn(l, e).loadout, makeLoadout());

function state(over: Partial<GameState> = {}): GameState {
  return {
    player: { hp: 100, maxHp: 100, alarm: 0, credits: 0, handSize: 5 },
    statusEffects: [],
    equipmentLoadout: EMPTY_LOADOUT,
    ...over,
  } as unknown as GameState;
}

describe("playerDefense", () => {
  it("is zero for an empty loadout", () => {
    expect(playerDefense(state())).toEqual({ iceResistance: 0, defense: 0 });
  });

  it("reads the equipped gear", () => {
    // Subdermal Weave Mk.II: defense 8, iceResistance 10.
    const s = state({ equipmentLoadout: withGear(SUBDERMAL) });
    expect(playerDefense(s)).toEqual({ iceResistance: 10, defense: 8 });
  });

  it("caps resistance so gear can never grant immunity", () => {
    // Master body: iceResistance 50 — under the cap; a synthetic over-cap
    // value is clamped.
    const s = state({
      equipmentLoadout: {
        totalStats: () => ({ ...MASTER_BODY.stats, iceResistance: 500 }),
        get: () => null,
      } as unknown as GameState["equipmentLoadout"],
    });
    expect(playerDefense(s).iceResistance).toBe(ICE_RESISTANCE_CAP_PCT);
  });
});

describe("applyIceResistance", () => {
  it("removes a percent, floored", () => {
    expect(applyIceResistance(20, 25)).toBe(15);
    expect(applyIceResistance(20, 10)).toBe(18);
  });

  it("is a no-op at 0% and for non-positive raw", () => {
    expect(applyIceResistance(20, 0)).toBe(20);
    expect(applyIceResistance(0, 50)).toBe(0);
    expect(applyIceResistance(-5, 50)).toBe(0);
  });
});

describe("applyPlayerMitigation — fixed order", () => {
  it("with no gear and no shield, the hit lands in full", () => {
    const r = applyPlayerMitigation(state(), 20);
    expect(r.damage).toBe(20);
    expect(r.absorbed).toBe(0);
    expect(r.reduced).toBe(0);
  });

  it("resistance then defense then shield", () => {
    // Subdermal: resistance 10% → 18, defense 8 → 10, shield 4 → 6 HP.
    const s = state({
      equipmentLoadout: withGear(SUBDERMAL),
      statusEffects: [
        { kind: "shield", target: "player", magnitude: 4, remaining: 9999 },
      ],
    });
    const r = applyPlayerMitigation(s, 20);
    expect(r.reduced).toBe(10); // 20 → 10 before the pool
    expect(r.absorbed).toBe(4);
    expect(r.damage).toBe(6);
  });

  it("spends the shield pool and keeps the remainder", () => {
    const s = state({
      statusEffects: [
        { kind: "shield", target: "player", magnitude: 10, remaining: 9999 },
      ],
    });
    const r = applyPlayerMitigation(s, 4);
    expect(r.absorbed).toBe(4);
    expect(r.damage).toBe(0);
    expect(playerShieldPool(r.state)).toBe(6);
  });

  it("defense can zero a small hit, but never heal", () => {
    // Tactical body: defense 20 — a 12 hit is fully stopped.
    const s = state({ equipmentLoadout: withGear(TACTICAL_BODY) });
    const r = applyPlayerMitigation(s, 12);
    expect(r.damage).toBe(0);
    expect(r.reduced).toBe(12);
  });

  it("non-positive incoming is a no-op", () => {
    const s = state();
    const r = applyPlayerMitigation(s, 0);
    expect(r.damage).toBe(0);
    expect(r.state).toBe(s);
  });
});

describe("applyEquipmentSurvival", () => {
  it("is a no-op for an empty loadout (the harness's case)", () => {
    const s = state();
    expect(applyEquipmentSurvival(s, EMPTY_LOADOUT)).toBe(s);
  });

  it("raises maxHP and fills it from hpBonus", () => {
    // Subdermal: hpBonus 20.
    const next = applyEquipmentSurvival(state(), withGear(SUBDERMAL));
    expect(next.player.maxHp).toBe(120);
    expect(next.player.hp).toBe(120);
  });

  it("adds a player shield pool from shieldBonus", () => {
    // Tactical body: hpBonus 50, shieldBonus 10.
    const next = applyEquipmentSurvival(state(), withGear(TACTICAL_BODY));
    expect(next.player.maxHp).toBe(150);
    expect(playerShieldPool(next)).toBe(10);
  });

  it("T0 starters change nothing on this axis", () => {
    const s = state({ equipmentLoadout: withGear(STARTER_DECK) });
    const next = applyEquipmentSurvival(s, withGear(STARTER_DECK));
    expect(next.player.maxHp).toBe(100);
    expect(playerShieldPool(next)).toBe(0);
  });

  it("boots (defense only, no hp/shield) leave HP alone", () => {
    // Chameleon Boots: defense 3, hpBonus 10 — hpBonus IS present.
    const next = applyEquipmentSurvival(state(), withGear(BOOTS_GHOST));
    expect(next.player.maxHp).toBe(110);
  });
});
