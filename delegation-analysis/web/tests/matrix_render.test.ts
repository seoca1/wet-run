/** Unit tests for matrix renderer (Tier 5.5+ enhanced). */
import { describe, it, expect } from "vitest";
import { renderMatrix } from "../src/renderer/matrix.ts";
import type { Matrix, Ice } from "../src/core/types.ts";

const sampleIce: Ice = {
  id: "watchdog",
  name: "Watchdog",
  hp: 100,
  armor: 0,
  tier: 1,
};

const sampleMatrix: Matrix = {
  nodes: [
    {
      id: 0, zone: "surface", iceIds: ["watchdog"], iceHp: [100],
      reward: { credits: 50 }, isBoss: false, adjacent: [1],
    },
    {
      id: 1, zone: "mid", iceIds: ["watchdog"], iceHp: [120],
      reward: { credits: 75 }, isBoss: false, adjacent: [2],
    },
    {
      id: 2, zone: "deep", iceIds: ["hellhound"], iceHp: [150],
      reward: { credits: 100 }, isBoss: false, adjacent: [3],
    },
    {
      id: 3, zone: "core", iceIds: ["ta_prime"], iceHp: [180],
      reward: { credits: 125 }, isBoss: false, adjacent: [4],
    },
    {
      id: 4, zone: "core-deep", iceIds: ["wintermute"], iceHp: [200],
      reward: { credits: 200 }, isBoss: true, adjacent: [],
    },
  ],
  startNode: 0,
  bossNode: 4,
};

function findAllText(grid: ReturnType<typeof renderMatrix>, cols: number, rows: number): string {
  const lines: string[] = [];
  for (let y = 0; y < rows; y++) {
    let line = "";
    for (let x = 0; x < cols; x++) {
      const cell = grid.get(x, y);
      if (cell) line += cell.char;
    }
    lines.push(line);
  }
  return lines.join("\n");
}

describe("matrix renderer (Tier 5.5+ enhanced)", () => {
  describe("zone color coding", () => {
    it("renders zone names in uppercase", () => {
      const grid = renderMatrix(sampleMatrix, 0, [], 80, 50);
      const text = findAllText(grid, 80, 50);
      expect(text).toContain("SURFACE");
      expect(text).toContain("MID");
      expect(text).toContain("DEEP");
      expect(text).toContain("CORE");
      expect(text).toContain("CORE-DEEP");
    });

    it("marks boss node distinctly (BOSS suffix)", () => {
      const grid = renderMatrix(sampleMatrix, 0, [], 80, 50);
      const text = findAllText(grid, 80, 50);
      expect(text).toContain("BOSS");
    });

    it("renders event glyphs (⚔ ★ ✦ ◆ ♨ ⌘)", () => {
      const grid = renderMatrix(sampleMatrix, 0, [], 80, 50);
      const text = findAllText(grid, 80, 50);
      // Combat nodes (default) show ⚔
      expect(text).toContain("⚔");
    });
  });

  describe("ICE preview (current node info panel)", () => {
    it("renders ICE name in current node preview", () => {
      const grid = renderMatrix(sampleMatrix, 0, [], 80, 50, sampleIce);
      const text = findAllText(grid, 80, 50);
      expect(text).toContain("Watchdog");
    });

    it("renders HP value from preview", () => {
      const grid = renderMatrix(sampleMatrix, 0, [], 80, 50, sampleIce);
      const text = findAllText(grid, 80, 50);
      expect(text).toContain("HP:");
      expect(text).toContain("100");
    });

    it("omits preview panel when no icePreview passed", () => {
      const grid = renderMatrix(sampleMatrix, 0, [], 80, 50);
      const text = findAllText(grid, 80, 50);
      // No "CURRENT NODE" header when no preview
      expect(text).not.toContain("CURRENT NODE");
    });

    it("does not render preview on small grids (< 50 cols)", () => {
      const grid = renderMatrix(sampleMatrix, 0, [], 40, 30, sampleIce);
      const text = findAllText(grid, 40, 30);
      // Preview suppressed on small screens (portrait phones)
      expect(text).not.toContain("Watchdog");
    });
  });

  describe("node state markers (current / visited / adjacent)", () => {
    it("current node shows ▸ marker", () => {
      const grid = renderMatrix(sampleMatrix, 2, [], 80, 50);
      const text = findAllText(grid, 80, 50);
      // Find row containing "DEEP" — should have ▸ marker
      const lines = text.split("\n");
      const deepRow = lines.find((l) => l.includes("DEEP"));
      expect(deepRow).toMatch(/▸/);
    });

    it("visited node shows ✓ marker", () => {
      const grid = renderMatrix(sampleMatrix, 3, [0, 1], 80, 50);
      const text = findAllText(grid, 80, 50);
      const lines = text.split("\n");
      const surfaceRow = lines.find((l) => l.includes("SURFACE"));
      const midRow = lines.find((l) => l.includes("MID"));
      expect(surfaceRow).toMatch(/✓/);
      expect(midRow).toMatch(/✓/);
    });

    it("unvisited non-current node shows space or adjacent →", () => {
      const grid = renderMatrix(sampleMatrix, 0, [], 80, 50);
      const text = findAllText(grid, 80, 50);
      const lines = text.split("\n");
      // Node 1 (mid) is adjacent to current (0). Should have → marker.
      const midRow = lines.find((l) => l.includes("MID"));
      expect(midRow).toMatch(/→/);
    });
  });

  describe("footer messages", () => {
    it("shows ENTER when current node has adjacent (progression available)", () => {
      const grid = renderMatrix(sampleMatrix, 0, [], 80, 50);
      const text = findAllText(grid, 80, 50);
      expect(text).toContain("ENTER: enter");
    });

    it("shows only ESC when current node has no adjacent (boss/boss cleared)", () => {
      const grid = renderMatrix(sampleMatrix, 4, [0, 1, 2, 3], 80, 50);
      const text = findAllText(grid, 80, 50);
      expect(text).not.toContain("ENTER: enter");
      expect(text).toContain("ESC");
    });
  });

  describe("grid dimensions", () => {
    it("matches requested cols/rows", () => {
      const grid = renderMatrix(sampleMatrix, 0, [], 80, 50);
      expect(grid.width).toBe(80);
      expect(grid.height).toBe(50);
    });

    it("handles portrait grid (40×60)", () => {
      const grid = renderMatrix(sampleMatrix, 0, [], 40, 60);
      expect(grid.width).toBe(40);
      expect(grid.height).toBe(60);
    });
  });
});