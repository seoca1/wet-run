import { describe, expect, it } from "vitest";
import { matrixLayout, renderMatrix } from "../src/renderer/matrix";
import { makeGrid } from "../src/core/grid";
import { generateProceduralMatrix } from "../src/core/dungeon/matrix";
import type { Grid } from "../src/core/types";
import { matrixNodeId } from "../src/renderer/matrix_nodes";

function lines(grid: Grid): string[] {
  return grid.cells.map((row) => row.map((cell) => cell.char).join(""));
}

function room(text: string[], cx: number, cy: number): string {
  return [...(text[cy] ?? "")].slice(cx - 1, cx + 2).join("");
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
    const layout = matrixLayout(makeGrid(cols, rows), matrix);
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
    // Then — ADR-0249: offers are the rooms joined to @ by route corridors,
    // named in arrow order in the card; context rooms only by link corridors.
    const routes = text.find((line) => line.includes("ROUTES ("));
    expect(routes).toContain(
      `ROUTES (${adjacent.length}): ${adjacent.map((i, k) => `${k === 0 ? ">" : ""}${matrixNodeId(i)}`).join(" ")}`,
    );
    const offered = layout.corridors.corridors.filter(
      (c) => c.a === current || c.b === current,
    );
    expect(offered).toHaveLength(adjacent.length);
    for (const c of offered) {
      const other = c.a === current ? c.b : c.a;
      const glyphs = c.cells.map((cell) => [...(text[cell.y] ?? "")][cell.x]);
      expect(glyphs.join("")).toMatch(other === adjacent[0] ? /^[┃━┏┓┗┛╋]+$/ : /^[│─┌┐└┘┼]+$/);
    }
    for (const c of layout.corridors.corridors.filter((c) => !offered.includes(c))) {
      const own = c.cells.filter(
        (cell) => !offered.some((o) => o.cells.some((x) => x.x === cell.x && x.y === cell.y)),
      );
      for (const cell of own)
        expect("┆┄╭╮╰╯┼").toContain([...(text[cell.y] ?? "")][cell.x] ?? "?");
    }
    expect(text.join("\n")).not.toMatch(/\[\d+\]/);
    const below = text.slice(layout.legendY).join("\n");
    expect(below).toContain("◆ OBJECTIVE: BOSS");
    expect(below).toContain(
      `${matrixNodeId(matrix.bossNode)} CORE-DEEP · REACHABLE NOW`,
    );
    expect(text[rows - 3]).toContain("ENTER");
  });

  it.each([
    [80, 50],
    [60, 40],
    [40, 60],
  ])(
    "keeps the objective and every room visible from every node on %sx%s",
    (cols, rows) => {
      // Given
      const matrix = generateProceduralMatrix(3, 42);
      const sites = matrixLayout(makeGrid(cols, rows), matrix).board.sites;
      for (let current = 0; current < matrix.nodes.length; current++) {
        // When
        const text = lines(renderMatrix(matrix, current, [0], cols, rows));
        // Then — ADR-0249 replaced the depth groups with the board itself.
        expect(text.join("\n")).toContain("◆ OBJECTIVE: BOSS");
        expect(text.join("\n")).toContain(`${matrixNodeId(matrix.bossNode)} CORE-DEEP ·`);
        expect(sites).toHaveLength(matrix.nodes.length);
        for (const site of sites)
          expect(room(text, site.cx, site.cy)).toMatch(/^[[#>◆][@◆·✓+][\]#<◆]$/);
      }
    },
  );

  it("distinguishes a cleared retreat from a visited but uncleared encounter", () => {
    // Given
    const matrix = generateProceduralMatrix(3, 42);
    // When
    const retreat = lines(
      renderMatrix(matrix, 1, [0, 1], 40, 60, null, 0, [0]),
    ).join("\n");
    const boss = lines(
      renderMatrix(matrix, 1, [0, 1], 40, 60, null, matrix.bossNode, [0]),
    ).join("\n");
    // Then
    expect(retreat).toContain("@ ⚔ N02 SURFACE · SEEN");
    expect(retreat).toContain("> ⚔ N01 SURFACE · CLEAR");
    expect(boss).toContain("> ⚔ N07 CORE-DEEP (BOSS) · NEW");
    expect(retreat).toContain("◆ OBJECTIVE: BOSS · NEW");
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
    expect(text).toContain("ROUTES (0): none");
    expect(text).toContain("> no routes — ENTER: ICE");
    expect(text).toContain(`${matrixNodeId(matrix.bossNode)} CORE-DEEP · HERE`);
    expect(text).toContain("◆@◆");
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
