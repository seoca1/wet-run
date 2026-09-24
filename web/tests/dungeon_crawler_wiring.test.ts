import { describe, it, expect } from "vitest";
import { createDungeonCrawlerFromMission } from "../src/core/dungeon_crawler";

describe("dungeon crawler (D7+D8 wiring)", () => {
  it("factory creates a DungeonCrawler with non-empty exploredMap around start", () => {
    const crawler = createDungeonCrawlerFromMission(null);
    // Player starts at (1,1); FOV should have revealed at least the player's tile.
    expect(crawler.isTileExplored(1, 1)).toBe(true);
    // Some tiles within the visible radius should also be explored.
    let exploredCount = 0;
    for (let y = 0; y < crawler.state.height; y++) {
      for (let x = 0; x < crawler.state.width; x++) {
        if (crawler.isTileExplored(x, y)) exploredCount++;
      }
    }
    expect(exploredCount, "FOV must reveal some tiles at start").toBeGreaterThan(1);
  });

  it("player can attempt movement on tile without crashing", () => {
    const crawler = createDungeonCrawlerFromMission(null);
    const before = { x: crawler.state.playerX, y: crawler.state.playerY };
    crawler.tryMovePlayer(0, 0);
    expect(crawler.state.playerX).toBe(before.x);
    expect(crawler.state.playerY).toBe(before.y);
    // processTurn is now called by handleDungeonInput; ensure no crash.
    crawler.processTurn();
    // turnCount advances on tryMovePlayer (1 call from testMovePlayer + extra
    // increments may happen via attackEntity/playerTakeDamage chains when monsters
    // are adjacent — assert the call incremented at least once, not exact value).
    expect(crawler.state.turnCount).toBeGreaterThanOrEqual(1);
  });

  it("processTurn advances turnCount after player moves", () => {
    const crawler = createDungeonCrawlerFromMission(null);
    // Which neighbour of the start tile is open depends on the procedural
    // layout, so probe until a move is accepted instead of assuming south.
    const directions: ReadonlyArray<readonly [number, number]> = [
      [0, 1],
      [0, -1],
      [1, 0],
      [-1, 0],
    ];
    let moved = false;
    for (const [dx, dy] of directions) {
      if (crawler.tryMovePlayer(dx, dy)) {
        moved = true;
        break;
      }
    }
    expect(moved, "start tile must have at least one passable neighbour").toBe(true);
    crawler.processTurn();
    expect(crawler.state.turnCount).toBeGreaterThanOrEqual(1);
  });
});
