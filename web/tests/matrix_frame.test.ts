/** ADR-0237 §2: the matrix screen sits in an inset Green Grid frame. */
import { describe, expect, it } from "vitest";
import type { Grid, Ice, Matrix } from "../src/core/types";
import { matrixLayout, renderMatrix } from "../src/renderer/matrix";
import { makeGrid } from "../src/core/grid";
import { PALETTE } from "../src/renderer/palette";

const ICE: Ice = {
  id: "watchdog",
  name: "Watchdog",
  hp: 100,
  armor: 0,
  tier: 1,
};

function node(
  id: number,
  zone: Matrix["nodes"][number]["zone"],
  adjacent: number[],
) {
  return {
    id,
    zone,
    iceIds: ["watchdog"],
    iceHp: [100],
    reward: { credits: 50 },
    isBoss: false,
    adjacent,
  };
}

const MATRIX: Matrix = {
  nodes: [node(0, "surface", [1]), node(1, "mid", [2]), node(2, "deep", [])],
  startNode: 0,
  bossNode: 2,
};

function lines(grid: Grid): string[] {
  return grid.cells.map((row) => row.map((cell) => cell.char).join(""));
}

describe("matrix screen frame (ADR-0237 §2)", () => {
  it.each([
    [80, 50],
    [40, 60],
    [60, 40],
  ])("draws the frame inset by one cell on a %s×%s grid", (cols, rows) => {
    // Given / When
    const grid = renderMatrix(MATRIX, 0, [], cols, rows, ICE);
    // Then
    expect(grid.get(1, 1)?.char).toBe("╔");
    expect(grid.get(cols - 2, 1)?.char).toBe("╗");
    expect(grid.get(1, rows - 2)?.char).toBe("╚");
    expect(grid.get(cols - 2, rows - 2)?.char).toBe("╝");
    expect(grid.get(1, Math.floor(rows / 2))?.char).toBe("║");
    expect(grid.get(cols - 2, Math.floor(rows / 2))?.char).toBe("║");
    expect(grid.get(Math.floor(cols / 2), 1)?.char).toBe("═");
    expect(grid.get(Math.floor(cols / 2), rows - 2)?.char).toBe("═");
    expect(grid.get(1, 1)?.fg).toBe(PALETTE.GREEN_NEON);
  });

  it("leaves the outermost row and column of the canvas blank", () => {
    // Given / When
    const text = lines(renderMatrix(MATRIX, 1, [0], 80, 50, ICE));
    // Then
    expect(text[0]?.trim()).toBe("");
    expect(text[49]?.trim()).toBe("");
    expect(text.every((line) => line[0] === " " && line[79] === " ")).toBe(
      true,
    );
  });

  it("keeps the border rows and columns free of content", () => {
    // Given / When
    const text = lines(renderMatrix(MATRIX, 0, [], 80, 50, ICE));
    // Then
    expect(text[1]).toBe(` ╔${"═".repeat(76)}╗ `);
    expect(text[48]).toBe(` ╚${"═".repeat(76)}╝ `);
    for (let y = 2; y < 48; y++) {
      expect(text[y]?.[1]).toBe("║");
      expect(text[y]?.[78]).toBe("║");
    }
  });

  it("composes the node list and node details away from the top-left", () => {
    // Given
    const layout = matrixLayout(makeGrid(80, 50), MATRIX);
    // When
    const text = lines(renderMatrix(MATRIX, 0, [], 80, 50, ICE));
    // Then — the list is centred with the CURRENT NODE column, and the block
    // is centred vertically, so neither hugs the frame's top-left corner.
    expect(layout.listX).toBeGreaterThan(10);
    expect(layout.titleY).toBeGreaterThan(10);
    expect(layout.previewX).not.toBeNull();
    expect(text[layout.listY]?.indexOf("▸ ⚔ [1] SURFACE")).toBe(layout.listX);
    expect(text[layout.listY]?.indexOf("── CURRENT NODE ──")).toBe(
      layout.previewX,
    );
    expect(text[layout.listY + 1]?.indexOf("1 ICE · 50cr")).toBe(
      layout.listX + 4,
    );
    expect(text[layout.titleY]).toContain("MATRIX — CYBERSPACE");
    expect(
      text[layout.progressY]?.slice(2, 78).trimEnd().endsWith("0/3 nodes"),
    ).toBe(true);
  });

  it("puts the controls footer on the last inner row", () => {
    // Given / When
    const text = lines(renderMatrix(MATRIX, 0, [], 80, 50));
    // Then
    expect(text[47]?.slice(2)).toMatch(/^ ENTER: enter ICE \| ↑↓: route \| ESC: back/);
  });

  it("does not let a long node list or long event label reach a rail", () => {
    // Given — far more nodes than fit, on a short grid
    const many: Matrix = {
      nodes: Array.from({ length: 30 }, (_, i) => node(i, "core", [i + 1])),
      startNode: 0,
      bossNode: 29,
    };
    // When
    const text = lines(renderMatrix(many, 0, [], 60, 24, ICE));
    // Then
    expect(text[1]).toBe(` ╔${"═".repeat(56)}╗ `);
    expect(text[22]).toBe(` ╚${"═".repeat(56)}╝ `);
    for (let y = 2; y < 22; y++) {
      expect(text[y]?.[1]).toBe("║");
      expect(text[y]?.[58]).toBe("║");
    }
    // A blank row separates the last node detail from the footer.
    expect(text[20]?.slice(2, 58).trim()).toBe("");
    expect(text[21]).toContain("ENTER: enter ICE");
  });

  it("clips overlong labels at the rail instead of spilling into the gutter", () => {
    // Given — a grid narrower than the node labels and the footer
    const cols = 20;
    // When
    const text = lines(renderMatrix(MATRIX, 0, [], cols, 30));
    // Then
    for (let y = 2; y < 28; y++) {
      expect(text[y]?.[0]).toBe(" ");
      expect(text[y]?.[1]).toBe("║");
      expect(text[y]?.[cols - 2]).toBe("║");
      expect(text[y]?.[cols - 1]).toBe(" ");
    }
  });
});
