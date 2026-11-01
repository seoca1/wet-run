import { describe, expect, it } from "vitest";
import { renderMatrix } from "../src/renderer/matrix";
import { generateProceduralMatrix } from "../src/core/dungeon/matrix";
import type { Grid } from "../src/core/types";
import { matrixNodeId } from "../src/renderer/matrix_nodes";

function lines(grid: Grid): string[] {
  return grid.cells.map((row) => row.map((cell) => cell.char).join(""));
}

describe("Matrix legibility", () => {
  it.each([
    [80, 50],
    [60, 40],
    [40, 60],
  ])("separates every frontier offer from context on %sx%s", (cols, rows) => {
    // Given
    const matrix = generateProceduralMatrix(3, 42);
    const current = 1;
    const adjacent = matrix.nodes[current]?.adjacent ?? [];
    // When
    const text = lines(
      renderMatrix(
        matrix,
        current,
        [0, 1],
        cols,
        rows,
        null,
        adjacent[0] ?? null,
        [0],
      ),
    );
    // Then
    const top = text.findIndex((line) => line.includes("┌─ REACHABLE NOW"));
    const bottom = text.findIndex((line, i) => i > top && line.includes("└─"));
    const frontier = text.slice(top + 1, bottom).join("\n");
    expect(top).toBeGreaterThan(
      text.findIndex((line) => line.includes("YOU ARE HERE")),
    );
    expect(bottom).toBeGreaterThan(top);
    expect(frontier.match(/[>→] ⚔ N\d+/g)).toHaveLength(adjacent.length);
    for (const i of adjacent) {
      expect(frontier).toContain(
        `${matrixNodeId(i)} ${matrix.nodes[i]?.zone.toUpperCase()}`,
      );
    }
    expect(frontier).not.toContain(`${matrixNodeId(current)} `);
    expect(text.join("\n")).not.toMatch(/\[\d+\]/);
    expect(text.slice(bottom + 1).join("\n")).toContain("◆ OBJECTIVE: BOSS");
    expect(text.slice(bottom + 1).join("\n")).toContain(
      `${matrixNodeId(matrix.bossNode)} CORE-DEEP · REACHABLE NOW`,
    );
    expect(text[rows - 3]).toContain("ENTER");
  });

  it.each([
    [80, 50],
    [60, 40],
    [40, 60],
  ])(
    "keeps the objective and every depth group visible from every node on %sx%s",
    (cols, rows) => {
      // Given
      const matrix = generateProceduralMatrix(3, 42);
      for (let current = 0; current < matrix.nodes.length; current++) {
        // When
        const text = lines(renderMatrix(matrix, current, [0], cols, rows)).join(
          "\n",
        );
        // Then
        expect(text).toContain("◆ OBJECTIVE: BOSS");
        expect(text).toContain(`${matrixNodeId(matrix.bossNode)} CORE-DEEP ·`);
        const map = text.slice(text.indexOf("DEPTH / ZONES"));
        const zones = [...new Set(matrix.nodes.map((node) => node.zone))];
        for (const zone of zones)
          expect(map).toContain(`${zone.toUpperCase()} (`);
      }
    },
  );

  it("distinguishes a cleared retreat from a visited but uncleared encounter", () => {
    // Given
    const matrix = generateProceduralMatrix(3, 42);
    // When
    const text = lines(
      renderMatrix(matrix, 1, [0, 1], 40, 60, null, 0, [0]),
    ).join("\n");
    // Then
    expect(text).toContain("▸ ⚔ N02 SURFACE · SEEN");
    expect(text).toContain("> ⚔ N01 SURFACE · CLEAR");
    expect(text).toContain("→ ⚔ N07 CORE-DEEP (BOSS) · NEW");
  });

  it("shows a labelled empty frontier at a terminal node without losing the boss", () => {
    // Given
    const matrix = generateProceduralMatrix(3, 42);
    const terminal = {
      ...matrix,
      nodes: matrix.nodes.map((node) => ({ ...node, adjacent: [] })),
    };
    // When
    const text = lines(
      renderMatrix(terminal, matrix.bossNode, [], 40, 60),
    ).join("\n");
    // Then
    expect(text).toContain("REACHABLE NOW (0)");
    expect(text).toContain("No routes — ENTER: ICE");
    expect(text).toContain(`${matrixNodeId(matrix.bossNode)} CORE-DEEP · HERE`);
  });

  it("does not mutate the graph or visit state while presenting it", () => {
    // Given
    const matrix = generateProceduralMatrix(3, 42);
    const visited = [0, 1];
    const cleared = [0];
    const before = JSON.stringify({ matrix, visited, cleared });
    // When
    renderMatrix(matrix, 1, visited, 60, 40, null, 0, cleared);
    // Then
    expect(JSON.stringify({ matrix, visited, cleared })).toBe(before);
  });
});
