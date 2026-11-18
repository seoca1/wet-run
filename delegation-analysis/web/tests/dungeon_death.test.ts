import { describe, it, expect } from "vitest";
import { createDungeonCrawlerFromMission } from "../src/core/dungeon_crawler";

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

