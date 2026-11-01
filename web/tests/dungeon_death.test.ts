import { describe, it, expect } from "vitest";
import { createDungeonCrawlerFromMission } from "../src/core/dungeon/dungeon_crawler";
import {
  EntityType,
  ItemType,
  MonsterType,
} from "../src/core/dungeon/dungeon_crawler_types";
import {
  attackEntity,
  playerTakeDamage,
  triggerTrap,
} from "../src/core/dungeon/dungeon_crawler_actions";
import { initializeDungeonState } from "../src/core/dungeon/dungeon_crawler_generation";

describe("DungeonCrawler death (Bug #5 regression: isGameOver on HP=0)", () => {
  it("isGameOver returns false at full HP", () => {
    const crawler = createDungeonCrawlerFromMission(null);
    expect(crawler.isGameOver()).toBe(false);
    expect(crawler.state.playerHp).toBe(100);
  });

  it("can detect game-over state by reading playerHp", () => {
    const crawler = createDungeonCrawlerFromMission(null);
    expect(crawler.isGameOver()).toBe(false);
    (crawler.state as { playerHp: number }).playerHp = 0;
    expect(crawler.isGameOver()).toBe(true);
  });
});

describe("terminal dungeon attempts", () => {
  it("reaches defeat through ordinary monster turns from full HP", () => {
    // Given: a real adjacent watchdog, with no HP assignment.
    const crawler = createDungeonCrawlerFromMission(null, 42);
    const { x, y } = crawler.getPlayerPosition();
    crawler.state.entities.splice(0, crawler.state.entities.length, {
      id: "watchdog",
      x: x + 1,
      y,
      type: EntityType.MONSTER,
      subtype: MonsterType.ICE_WATCHDOG,
      hp: 15,
      hostile: true,
    });
    // When: 34 ordinary AI turns deal 3 damage each.
    for (let turn = 0; turn < 34; turn++) crawler.processTurn();
    // Then: HP stays zero so the controller's defeat branch can end the attempt.
    expect(crawler.getPlayerStats().hp).toBe(0);
    expect(crawler.isGameOver()).toBe(true);
    expect(crawler.getPlayerStats().alarm).toBe(0);
  });

  it("keeps a defeated attempt frozen even when a healing pickup is underfoot", () => {
    // Given
    const crawler = createDungeonCrawlerFromMission(null, 42);
    const { x, y } = crawler.getPlayerPosition();
    crawler.state.entities.splice(0, crawler.state.entities.length, {
      id: "watchdog",
      x: x + 1,
      y,
      type: EntityType.MONSTER,
      subtype: MonsterType.ICE_WATCHDOG,
      hp: 15,
      hostile: true,
    });
    for (let turn = 0; turn < 34; turn++) crawler.processTurn();
    crawler.state.entities.push({
      id: "heal",
      x,
      y,
      type: EntityType.ITEM,
      subtype: ItemType.HEALTH_POTION,
      hp: 0,
    });
    const before = structuredClone(crawler.state);
    // When
    const moved = crawler.tryMovePlayer(0, 0);
    crawler.processTurn();
    // Then
    expect(moved).toBe(false);
    expect(crawler.state).toEqual(before);
    expect(crawler.isGameOver()).toBe(true);
  });

  it("ends an attempt on lethal retaliation rather than healing it", () => {
    // Given
    const state = initializeDungeonState(null);
    playerTakeDamage(state, 99);
    const monster = {
      id: "watchdog",
      x: 2,
      y: 1,
      type: EntityType.MONSTER,
      subtype: MonsterType.ICE_WATCHDOG,
      hp: 15,
      hostile: true,
    };
    // When
    attackEntity(state, () => 0, monster);
    // Then
    expect(state.playerHp).toBe(0);
    expect(state.playerAlarm).toBe(0);
  });

  it("ends an attempt on lethal trap damage", () => {
    // Given
    const state = initializeDungeonState(null);
    playerTakeDamage(state, 99);
    const trap = { id: "trap", x: 1, y: 1, type: EntityType.TRAP, hp: 0 };
    // When
    triggerTrap(
      state,
      () => 0,
      (min) => min,
      trap,
    );
    // Then
    expect(state.playerHp).toBe(0);
  });
});
