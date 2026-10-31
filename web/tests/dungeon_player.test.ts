/** The dungeon screen draws the player `@` from the crawler's player position. */
import { describe, expect, it, vi } from "vitest";
import {
  createDungeonCrawlerFromMission,
  EntityType,
  MonsterType,
  type DungeonCrawler,
} from "../src/core/dungeon/dungeon_crawler";
import { renderDungeonMap } from "../src/renderer/dungeon";
import { PALETTE } from "../src/renderer/palette";

const SEED = 1337;
const COLS = 100;
const ROWS = 60;

/** Screen cell of the player: the map is centred in the inner rect (x/y 2..). */
function playerCell(crawler: DungeonCrawler): { x: number; y: number } {
  const { width, height } = crawler.state;
  const { x, y } = crawler.getPlayerPosition();
  const innerW = COLS - 4;
  const innerH = ROWS - 4;
  return {
    x: 2 + Math.max(0, Math.floor((innerW - width) / 2)) + x,
    y: 2 + Math.max(0, Math.floor((innerH - height) / 2)) + y,
  };
}

function stubHp(crawler: DungeonCrawler, hp: number, maxHp: number): void {
  const real = crawler.getPlayerStats();
  vi.spyOn(crawler, "getPlayerStats").mockReturnValue({ ...real, hp, maxHp });
}

describe("dungeon player glyph", () => {
  it("draws the player @ at its screen cell in GREEN_NEON at full HP", () => {
    // Given
    const crawler = createDungeonCrawlerFromMission(null, SEED);
    const cell = playerCell(crawler);
    // When
    const grid = renderDungeonMap(crawler, COLS, ROWS);
    // Then
    expect(grid.get(cell.x, cell.y)?.char).toBe("@");
    expect(grid.get(cell.x, cell.y)?.fg).toBe(PALETTE.GREEN_NEON);
    expect(grid.get(cell.x, cell.y)?.bg).toBe(PALETTE.BACKGROUND);
  });

  it.each([
    [10, 20, PALETTE.YELLOW_AMBER],
    [5, 20, PALETTE.RED_BRIGHT],
  ])("colours the @ by HP ratio (%s/%s)", (hp, maxHp, expected) => {
    // Given
    const crawler = createDungeonCrawlerFromMission(null, SEED);
    stubHp(crawler, hp, maxHp);
    const cell = playerCell(crawler);
    // When
    const grid = renderDungeonMap(crawler, COLS, ROWS);
    // Then
    expect(grid.get(cell.x, cell.y)?.char).toBe("@");
    expect(grid.get(cell.x, cell.y)?.fg).toBe(expected);
  });

  it("draws exactly one @, never on the frame rails or the gutter", () => {
    // Given
    const crawler = createDungeonCrawlerFromMission(null, SEED);
    const cell = playerCell(crawler);
    // When
    const grid = renderDungeonMap(crawler, COLS, ROWS);
    // Then
    const ats: Array<[number, number]> = [];
    grid.cells.forEach((row, y) =>
      row.forEach((c, x) => {
        if (c.char === "@") ats.push([x, y]);
      }),
    );
    expect(ats).toEqual([[cell.x, cell.y]]);
    for (let x = 0; x < COLS; x++) {
      expect(grid.get(x, 0)?.char).toBe(" ");
      expect(grid.get(x, ROWS - 1)?.char).toBe(" ");
    }
    for (let y = 0; y < ROWS; y++) {
      expect(grid.get(0, y)?.char).toBe(" ");
      expect(grid.get(COLS - 1, y)?.char).toBe(" ");
    }
    expect(grid.get(1, 1)?.char).toBe("╔");
    expect(grid.get(COLS - 2, 1)?.char).toBe("╗");
    expect(grid.get(1, ROWS - 2)?.char).toBe("╚");
    expect(grid.get(COLS - 2, ROWS - 2)?.char).toBe("╝");
    for (let x = 2; x < COLS - 2; x++) {
      expect(grid.get(x, 1)?.char).toBe("═");
      expect(grid.get(x, ROWS - 2)?.char).toBe("═");
    }
    for (let y = 2; y < ROWS - 2; y++) {
      expect(grid.get(1, y)?.char).toBe("║");
      expect(grid.get(COLS - 2, y)?.char).toBe("║");
    }
  });

  it("draws the @ over a monster standing on the player's tile", () => {
    // Given
    const crawler = createDungeonCrawlerFromMission(null, SEED);
    const { x, y } = crawler.getPlayerPosition();
    crawler.state.entities.push({
      id: "test_monster",
      x,
      y,
      type: EntityType.MONSTER,
      subtype: MonsterType.ICE_GOLIATH,
      hp: 10,
      maxHp: 10,
      hostile: true,
    });
    const cell = playerCell(crawler);
    // When
    const grid = renderDungeonMap(crawler, COLS, ROWS);
    // Then
    expect(grid.get(cell.x, cell.y)?.char).toBe("@");
  });

  it("clips the @ when the player falls outside a tiny viewport", () => {
    // Given — inner area 4×2 holds only the map's top-left corner
    const crawler = createDungeonCrawlerFromMission(null, SEED);
    const { x, y } = crawler.getPlayerPosition();
    // When
    const grid = renderDungeonMap(crawler, 8, 6);
    // Then
    const text = grid.cells.map((row) => row.map((c) => c.char).join(""));
    const inside = x < 4 && y < 2;
    expect(text.join("").includes("@")).toBe(inside);
    expect(text[1]).toBe(" ╔════╗ ");
    expect(text[4]).toBe(" ╚════╝ ");
  });
});
