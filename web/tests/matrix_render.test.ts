/** Unit tests for matrix renderer (Tier 5.5+ enhanced). */
import { describe, it, expect } from "vitest";
import { matrixLayout, renderMatrix } from "../src/renderer/matrix";
import { makeGrid } from "../src/core/grid";
import type { Matrix, Ice } from "../src/core/types";

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
      // ADR-0249: the card names the current and the targeted node; walking
      // the chain with each next node targeted shows every zone.
      const seen: string[] = [];
      for (let current = 0; current < 4; current++) {
        const grid = renderMatrix(sampleMatrix, current, [], 80, 50, null, current + 1);
        seen.push(findAllText(grid, 80, 50));
      }
      const text = seen.join("\n");
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
    it("current node shows @ marker (card and board)", () => {
      const grid = renderMatrix(sampleMatrix, 2, [], 80, 50);
      const text = findAllText(grid, 80, 50);
      // Find row containing "DEEP" — the card's current-node line carries @
      const lines = text.split("\n");
      const deepRow = lines.find((l) => l.includes("DEEP"));
      expect(deepRow).toMatch(/@/);
      const site = matrixLayout(makeGrid(80, 50), sampleMatrix).board.sites[2];
      expect(lines[site?.cy ?? 0]?.slice((site?.cx ?? 0) - 1, (site?.cx ?? 0) + 2)).toBe("#@#");
    });

    it("visited node shows ✓ marker", () => {
      const grid = renderMatrix(sampleMatrix, 3, [0, 1], 80, 50);
      const text = findAllText(grid, 80, 50);
      const lines = text.split("\n");
      // ADR-0249: SURFACE (N01) and MID (N02) rooms on the board carry ✓.
      const sites = matrixLayout(makeGrid(80, 50), sampleMatrix).board.sites;
      const room = (i: number) =>
        lines[sites[i]?.cy ?? 0]?.slice((sites[i]?.cx ?? 0) - 1, (sites[i]?.cx ?? 0) + 2);
      expect(room(0)).toMatch(/✓/);
      expect(room(1)).toMatch(/✓/);
      expect(room(2)).not.toMatch(/✓/);
    });

    it("unvisited adjacent node is offered as a route", () => {
      const grid = renderMatrix(sampleMatrix, 0, [], 80, 50);
      const text = findAllText(grid, 80, 50);
      // ADR-0249: node 1 (mid) is adjacent to current (0): a solid route
      // corridor joins them and the card names it among the routes.
      expect(text).toContain("ROUTES (1): N02");
      const sites = matrixLayout(makeGrid(80, 50), sampleMatrix).board.sites;
      const row = text.split("\n")[sites[0]?.cy ?? 0] ?? "";
      expect(row.slice((sites[0]?.cx ?? 0) + 2, (sites[1]?.cx ?? 0) - 1)).toMatch(/^─+$/);
      expect(row.slice((sites[1]?.cx ?? 0) - 1, (sites[1]?.cx ?? 0) + 2)).toBe("#·#");
    });
  });

  describe("footer messages", () => {
    it("shows ENTER when current node has adjacent (progression available)", () => {
      const grid = renderMatrix(sampleMatrix, 0, [], 80, 50);
      const text = findAllText(grid, 80, 50);
      expect(text).toContain("ENTER: enter");
    });

    it("keeps ICE engagement available at a boss with no adjacent routes", () => {
      const grid = renderMatrix(sampleMatrix, 4, [0, 1, 2, 3], 80, 50);
      const text = findAllText(grid, 80, 50);
      expect(text).toContain("ENTER: enter ICE");
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
