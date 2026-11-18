import { describe, it, expect } from "vitest";
import { makeGrid, setCell, setText } from "../src/core/grid.ts";
import { PALETTE } from "../src/renderer/palette.ts";
import type { Cell } from "../src/core/types.ts";

describe("grid", () => {
  describe("makeGrid", () => {
    it("creates grid with correct dimensions", () => {
      const grid = makeGrid(10, 5);
      expect(grid.width).toBe(10);
      expect(grid.height).toBe(5);
    });

    it("fills grid with background cells", () => {
      const grid = makeGrid(3, 3);
      expect(grid.cells.length).toBe(3);
      expect(grid.cells[0]?.length).toBe(3);
    });

    it("each cell has space char by default", () => {
      const grid = makeGrid(2, 2);
      for (let y = 0; y < 2; y++) {
        for (let x = 0; x < 2; x++) {
          const cell = grid.get(x, y);
          expect(cell?.char).toBe(" ");
        }
      }
    });

    it("uses default background color", () => {
      const grid = makeGrid(2, 2);
      const cell = grid.get(0, 0);
      expect(cell?.bg).toBe(PALETTE.BACKGROUND);
    });

    it("creates frozen cell structure", () => {
      const grid = makeGrid(2, 2);
      expect(Array.isArray(grid.cells)).toBe(true);
    });
  });

  describe("Grid.get", () => {
    const grid = makeGrid(5, 5);

    it("returns cell at valid position", () => {
      const cell = grid.get(2, 2);
      expect(cell).not.toBe(null);
    });

    it("returns null for negative x", () => {
      expect(grid.get(-1, 2)).toBe(null);
    });

    it("returns null for negative y", () => {
      expect(grid.get(2, -1)).toBe(null);
    });

    it("returns null for x >= width", () => {
      expect(grid.get(5, 2)).toBe(null);
    });

    it("returns null for y >= height", () => {
      expect(grid.get(2, 5)).toBe(null);
    });

    it("returns correct cell at boundaries", () => {
      expect(grid.get(0, 0)).not.toBe(null);
      expect(grid.get(4, 4)).not.toBe(null);
    });
  });

  describe("setCell", () => {
    it("returns new grid instance", () => {
      const grid = makeGrid(5, 5);
      const cell: Cell = { char: "X", fg: "#fff", bg: "#000" };
      const newGrid = setCell(grid, { x: 2, y: 2 }, cell);
      expect(newGrid).not.toBe(grid);
    });

    it("updates cell at position", () => {
      const grid = makeGrid(5, 5);
      const cell: Cell = { char: "X", fg: "#fff", bg: "#000" };
      const newGrid = setCell(grid, { x: 2, y: 2 }, cell);
      const updated = newGrid.get(2, 2);
      expect(updated?.char).toBe("X");
    });

    it("does not mutate original grid", () => {
      const grid = makeGrid(5, 5);
      const orig = grid.get(2, 2);
      const cell: Cell = { char: "X", fg: "#fff", bg: "#000" };
      setCell(grid, { x: 2, y: 2 }, cell);
      expect(grid.get(2, 2)).toEqual(orig);
    });

    it("leaves other cells unchanged", () => {
      const grid = makeGrid(5, 5);
      const origCell = grid.get(1, 1);
      const cell: Cell = { char: "X", fg: "#fff", bg: "#000" };
      const newGrid = setCell(grid, { x: 2, y: 2 }, cell);
      expect(newGrid.get(1, 1)).toEqual(origCell);
    });

    it("returns original grid for out of bounds", () => {
      const grid = makeGrid(5, 5);
      const cell: Cell = { char: "X", fg: "#fff", bg: "#000" };
      const newGrid = setCell(grid, { x: 10, y: 10 }, cell);
      expect(newGrid).toBe(grid);
    });

    it("handles negative coordinates", () => {
      const grid = makeGrid(5, 5);
      const cell: Cell = { char: "X", fg: "#fff", bg: "#000" };
      const newGrid = setCell(grid, { x: -1, y: 2 }, cell);
      expect(newGrid).toBe(grid);
    });
  });

  describe("setText", () => {
    it("writes text to grid", () => {
      const grid = makeGrid(10, 5);
      const newGrid = setText(grid, 0, 0, "HI");
      expect(newGrid.get(0, 0)?.char).toBe("H");
      expect(newGrid.get(1, 0)?.char).toBe("I");
      expect(newGrid.get(0, 0)?.bg).toBe(PALETTE.BACKGROUND);
    });

    it("uses default green neon when no color specified", () => {
      const grid = makeGrid(10, 5);
      const newGrid = setText(grid, 0, 0, "X");
      expect(newGrid.get(0, 0)?.fg).toBe(PALETTE.GREEN_NEON);
    });

    it("truncates text at grid boundary", () => {
      const grid = makeGrid(5, 5);
      const newGrid = setText(grid, 3, 0, "HELLO");
      expect(newGrid.get(4, 0)?.char).toBe("E");
      expect(newGrid.get(5, 0)).toBe(null);
    });

    it("handles empty string", () => {
      const grid = makeGrid(5, 5);
      const newGrid = setText(grid, 0, 0, "");
      expect(newGrid.get(0, 0)?.char).toBe(" ");
    });

    it("writes at different positions", () => {
      const grid = makeGrid(10, 10);
      const g1 = setText(grid, 2, 3, "ABC");
      expect(g1.get(2, 3)?.char).toBe("A");
      expect(g1.get(3, 3)?.char).toBe("B");
      expect(g1.get(4, 3)?.char).toBe("C");
    });

    it("overwrites previous content", () => {
      const grid = makeGrid(10, 5);
      const g1 = setText(grid, 0, 0, "AAA");
      const g2 = setText(g1, 0, 0, "BBB");
      expect(g2.get(0, 0)?.char).toBe("B");
      expect(g2.get(0, 0)?.bg).toBe(PALETTE.BACKGROUND);
    });
  });

  describe("immutability", () => {
    it("setCell chain does not mutate", () => {
      const g0 = makeGrid(5, 5);
      const cell1: Cell = { char: "A", fg: "#fff", bg: "#000" };
      const cell2: Cell = { char: "B", fg: "#fff", bg: "#000" };
      const g1 = setCell(g0, { x: 1, y: 1 }, cell1);
      const g2 = setCell(g1, { x: 2, y: 2 }, cell2);
      expect(g0.get(1, 1)?.char).toBe(" ");
      expect(g1.get(2, 2)?.char).toBe(" ");
      expect(g2.get(1, 1)?.char).toBe("A");
      expect(g2.get(2, 2)?.char).toBe("B");
    });

    it("setText chain does not mutate", () => {
      const g0 = makeGrid(10, 5);
      const g1 = setText(g0, 0, 0, "A");
      const g2 = setText(g1, 1, 0, "B");
      expect(g0.get(0, 0)?.char).toBe(" ");
      expect(g1.get(0, 0)?.char).toBe("A");
      expect(g1.get(1, 0)?.char).toBe(" ");
      expect(g2.get(1, 0)?.char).toBe("B");
    });
  });

  describe("edge cases", () => {
    it("handles 1x1 grid", () => {
      const grid = makeGrid(1, 1);
      expect(grid.width).toBe(1);
      expect(grid.height).toBe(1);
      const cell = grid.get(0, 0);
      expect(cell).not.toBe(null);
    });

    it("handles large grid", () => {
      const grid = makeGrid(100, 100);
      expect(grid.width).toBe(100);
      expect(grid.height).toBe(100);
      expect(grid.get(99, 99)).not.toBe(null);
    });

    it("setText with long string at edge", () => {
      const grid = makeGrid(5, 5);
      const newGrid = setText(grid, 4, 0, "TOOLONG");
      expect(newGrid.get(4, 0)?.char).toBe("T");
      expect(newGrid.get(5, 0)).toBe(null);
    });

    it("setCell with position at exact boundary", () => {
      const grid = makeGrid(5, 5);
      const cell: Cell = { char: "X", fg: "#fff", bg: "#000" };
      const newGrid = setCell(grid, { x: 4, y: 4 }, cell);
      expect(newGrid.get(4, 4)?.char).toBe("X");
    });
  });
});
