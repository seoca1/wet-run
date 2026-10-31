/** ADR-0237 §2: the dungeon screen sits in an inset Green Grid frame. */
import { describe, expect, it } from "vitest";
import type { Grid } from "../src/core/types";
import { createDungeonCrawlerFromMission } from "../src/core/dungeon/dungeon_crawler";
import { dungeonFrame, renderDungeonMap } from "../src/renderer/dungeon";
import { PALETTE } from "../src/renderer/palette";

const SEED = 1337;

function lines(grid: Grid): string[] {
  return grid.cells.map((row) => row.map((cell) => cell.char).join(""));
}

describe("dungeon screen frame (ADR-0237 §2)", () => {
  it("returns a frame inset by one cell from every canvas edge", () => {
    expect(dungeonFrame(80, 50)).toEqual({ x: 1, y: 1, width: 78, height: 48 });
  });

  it.each([
    [80, 50],
    [40, 60],
    [32, 50],
  ])(
    "draws the border glyphs at the inset corners on a %s×%s grid",
    (cols, rows) => {
      // Given
      const crawler = createDungeonCrawlerFromMission(null, SEED);
      // When
      const grid = renderDungeonMap(crawler, cols, rows);
      // Then
      expect(grid.get(1, 1)?.char).toBe("╔");
      expect(grid.get(cols - 2, 1)?.char).toBe("╗");
      expect(grid.get(1, rows - 2)?.char).toBe("╚");
      expect(grid.get(cols - 2, rows - 2)?.char).toBe("╝");
      expect(grid.get(1, 2)?.char).toBe("║");
      expect(grid.get(cols - 2, rows - 3)?.char).toBe("║");
      expect(grid.get(2, 1)?.char).toBe("═");
      expect(grid.get(1, 1)?.fg).toBe(PALETTE.GREEN_NEON);
    },
  );

  it("leaves the outermost row and column of the canvas blank", () => {
    // Given
    const crawler = createDungeonCrawlerFromMission(null, SEED);
    // When
    const text = lines(renderDungeonMap(crawler, 80, 50));
    // Then
    expect(text[0]?.trim()).toBe("");
    expect(text[49]?.trim()).toBe("");
    expect(text.every((line) => line[0] === " " && line[79] === " ")).toBe(
      true,
    );
  });

  it("centres the map inside the frame", () => {
    // Given
    const crawler = createDungeonCrawlerFromMission(null, SEED);
    crawler.updateFov();
    const { width, height, playerX, playerY } = crawler.state;
    // When
    const text = lines(renderDungeonMap(crawler, 80, 50));
    // Then — inner rect is x 2..77, y 2..47; the map is centred in it.
    const offsetX = 2 + Math.max(0, Math.floor((76 - width) / 2));
    const offsetY = 2 + Math.max(0, Math.floor((46 - height) / 2));
    expect(text[offsetY + playerY]?.[offsetX + playerX]).not.toBe(" ");
    for (let y = 2; y < 48; y++) {
      const content = text[y]?.slice(2, 78) ?? "";
      const first = content.search(/\S/);
      if (first === -1) continue;
      expect(y).toBeGreaterThanOrEqual(offsetY);
      expect(y).toBeLessThan(offsetY + height);
      expect(2 + first).toBeGreaterThanOrEqual(offsetX);
      expect(2 + content.trimEnd().length).toBeLessThanOrEqual(offsetX + width);
    }
  });

  it("clips a map larger than the frame so no tile lands on a rail", () => {
    // Given — inner area is 4×2, smaller than any generated level
    const crawler = createDungeonCrawlerFromMission(null, SEED);
    // When
    const text = lines(renderDungeonMap(crawler, 8, 6));
    // Then
    expect(text[0]).toBe("        ");
    expect(text[1]).toBe(" ╔════╗ ");
    expect(text[2]?.slice(0, 2)).toBe(" ║");
    expect(text[2]?.slice(6)).toBe("║ ");
    expect(text[3]?.slice(0, 2)).toBe(" ║");
    expect(text[3]?.slice(6)).toBe("║ ");
    expect(text[4]).toBe(" ╚════╝ ");
    expect(text[5]).toBe("        ");
  });
});
