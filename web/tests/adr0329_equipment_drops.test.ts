/** ADR-0329 — equipment drops at the loot stop.
 *
 * ADR-0325 gave gear a craft path; this is the drop half the proposal asked for
 * (`craft / drop / buy`). The roll is deterministic and consumes no
 * `Math.random`, so the combat stream and the recorded curve are unchanged.
 */
import { describe, expect, it } from "vitest";
import {
  EQUIPMENT_DROP_BY_GRADE,
  EQUIPMENT_DROP_CHANCE,
  equipmentDropForGrade,
  offeredEquipmentDrop,
} from "../src/core/state/equipment_drops";
import { LOOT_GEAR_SLOT, lootSlotChoice } from "../src/core/state/loot_choice";
import type { GameState } from "../src/core/types";

const state = (grade: number, over: Record<string, unknown> = {}): GameState =>
  ({
    mission: { id: "m", grade_max: grade, rewards: { credits: 0, materials: {} } },
    turnCount: 3,
    currentNodeIndex: 2,
    droppedEquipment: [],
    ...over,
  }) as unknown as GameState;

describe("equipment drops (ADR-0329)", () => {
  it("maps each grade to its own piece", () => {
    expect(equipmentDropForGrade(1)).toBe("eyes_militech");
    expect(equipmentDropForGrade(2)).toBe("bodysuit_subdermal");
    expect(equipmentDropForGrade(3)).toBe("deck_militech");
    expect(equipmentDropForGrade(5)).toBe("deck_ghost");
    expect(equipmentDropForGrade(6)).toBe("deck_master");
    // Every entry names a real catalog id (the drops are gear, not materials).
    expect(Object.keys(EQUIPMENT_DROP_BY_GRADE).length).toBe(5);
  });

  it("a grade with no entry drops nothing", () => {
    expect(equipmentDropForGrade(4)).toBeNull();
    expect(offeredEquipmentDrop(state(4))).toBeNull();
  });

  it("never offers a piece the run already took", () => {
    const taken = state(1, { droppedEquipment: ["eyes_militech"] });
    expect(offeredEquipmentDrop(taken)).toBeNull();
  });

  it("is deterministic and consumes no Math.random", () => {
    const s = state(1);
    const original = Math.random;
    let calls = 0;
    Math.random = () => {
      calls += 1;
      return 0;
    };
    try {
      const a = offeredEquipmentDrop(s);
      const b = offeredEquipmentDrop(s);
      expect(a).toBe(b);
      expect(calls).toBe(0);
    } finally {
      Math.random = original;
    }
  });

  it("fires sometimes, and not always", () => {
    let hits = 0;
    const N = 400;
    for (let s = 0; s < N; s += 1) {
      const m = state(1, {
        mission: { id: `m${s}`, grade_max: 1, matrix_seed: s + 1, rewards: { credits: 0, materials: {} } },
      });
      if (offeredEquipmentDrop(m) !== null) hits += 1;
    }
    expect(hits).toBeGreaterThan(0);
    expect(hits).toBeLessThan(N);
    // Loose sanity: within ~10pp of the authored chance.
    expect(Math.abs(hits / N - EQUIPMENT_DROP_CHANCE)).toBeLessThan(0.1);
  });

  it("slot 9 is the gear slot", () => {
    expect(LOOT_GEAR_SLOT).toBe(9);
    expect(lootSlotChoice(LOOT_GEAR_SLOT)).toBe("gear");
    expect(lootSlotChoice(1)).toBe("program");
  });
});
