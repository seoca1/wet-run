/** ADR-0326 — the player's defense step, and the survival stats at run start.
 *
 * Before this, an ICE hit went raw → shield pool → HP: the equipment's
 * `defense` and `iceResistance` were numbers nobody read, and `hpBonus` /
 * `shieldBonus` never left the catalog. The order is fixed (resistance →
 * defense → shield → HP) so defense and the card's armor path stay separate.
 *
 * These use SYNTHETIC pieces with known stats, not catalog values — the catalog
 * is re-tuned against the curve (ADR-0328), and this test is about the wiring.
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
  makeEquipment,
  makeEquipStats,
  type Equipment,
} from "../src/core/state/equipment";
import type { GameState } from "../src/core/types";

let n = 0;
const piece = (
  stats: Parameters<typeof makeEquipStats>[0],
  slot: Equipment["slot"] = "gloves",
): Equipment => {
  n += 1;
  return makeEquipment({
    id: `test_${n}`,
    name: `Test ${n}`,
    slot,
    category: "cybernetic",
    tier: "T1",
    stats: makeEquipStats(stats),
    description: "",
  });
};

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
    const s = state({
      equipmentLoadout: withGear(piece({ iceResistance: 10, defense: 8 })),
    });
    expect(playerDefense(s)).toEqual({ iceResistance: 10, defense: 8 });
  });

  it("caps resistance so gear can never grant immunity", () => {
    const s = state({
      equipmentLoadout: withGear(piece({ iceResistance: 500 })),
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
    // resistance 10% → 18, defense 8 → 10, shield 4 → 6 HP.
    const s = state({
      equipmentLoadout: withGear(piece({ iceResistance: 10, defense: 8 })),
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
    const s = state({ equipmentLoadout: withGear(piece({ defense: 20 })) });
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
    const next = applyEquipmentSurvival(state(), withGear(piece({ hpBonus: 20 })));
    expect(next.player.maxHp).toBe(120);
    expect(next.player.hp).toBe(120);
  });

  it("adds a player shield pool from shieldBonus", () => {
    const next = applyEquipmentSurvival(
      state(),
      withGear(piece({ hpBonus: 50, shieldBonus: 10 })),
    );
    expect(next.player.maxHp).toBe(150);
    expect(playerShieldPool(next)).toBe(10);
  });

  it("gear without hp/shield leaves the pool alone", () => {
    const next = applyEquipmentSurvival(state(), withGear(piece({ defense: 3 })));
    expect(next.player.maxHp).toBe(100);
    expect(playerShieldPool(next)).toBe(0);
  });
});
