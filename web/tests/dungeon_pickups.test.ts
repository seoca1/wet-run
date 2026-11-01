import { describe, expect, it } from "vitest";
import { addItem } from "../src/core/dungeon/dungeon_crawler_entities";
import { checkForEntityInteractions } from "../src/core/dungeon/dungeon_crawler_actions";
import { initializeDungeonState } from "../src/core/dungeon/dungeon_crawler_generation";
import { ItemType } from "../src/core/dungeon/dungeon_crawler_types";

describe("dungeon rewards", () => {
  it.each([
    [0, ItemType.HEALTH_POTION, 75, 30],
    [0.399999, ItemType.HEALTH_POTION, 75, 30],
    [0.4, ItemType.ENERGY_CELL, 50, 15],
    [0.699999, ItemType.ENERGY_CELL, 50, 15],
    [0.7, ItemType.DATA_CHIP, 60, 30],
    [0.899999, ItemType.DATA_CHIP, 60, 30],
  ])(
    "roll %s spawns a consumable that actually changes crawler stats",
    (roll, subtype, hp, alarm) => {
      // Given: below both resource caps, so effects cannot be hidden by clamping.
      const state = initializeDungeonState(null);
      state.playerHp = 50;
      state.playerAlarm = 30;
      addItem(state, () => roll, state.playerX, state.playerY);
      expect(state.entities.map((item) => item.subtype)).toEqual([subtype]);
      // When: use the same interaction path as movement.
      checkForEntityInteractions(
        state,
        () => 0,
        (min) => min,
      );
      // Then
      expect([state.playerHp, state.playerAlarm]).toEqual([hp, alarm]);
      expect(state.entities).toHaveLength(0);
    },
  );

  it.each([0.9, 0.949999, 0.95, 0.999999])(
    "roll %s leaves no inert reward available to pick up",
    (roll) => {
      // Given
      const state = initializeDungeonState(null);
      let draws = 0;
      // When: both generation and monster drops use this spawn seam.
      addItem(
        state,
        () => {
          draws++;
          return roll;
        },
        state.playerX,
        state.playerY,
      );
      // Then: former weapon/armor rolls are no-drop, not pretend equipment.
      expect(state.entities).toHaveLength(0);
      expect(draws).toBe(1);
    },
  );
});
