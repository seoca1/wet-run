/** ADR-0249: the Matrix operation board and its eight integrity rules. */
import { describe, expect, it } from "vitest";
import { applyAction, makeInitialState } from "../src/core/state/state";
import { generateProceduralMatrix } from "../src/core/dungeon/matrix";
import { makeGrid } from "../src/core/grid";
import { matrixLayout, renderMatrix } from "../src/renderer/matrix";
import type { GameState, Grid, Matrix } from "../src/core/types";

const LINK = new Set("┆┄╭╮╰╯┼");
const ROUTE = new Set("│─┌┐└┘┼");
const TARGET = new Set("┃━┏┓┗┛╋");
const CORRIDOR = new Set([...LINK, ...ROUTE, ...TARGET]);
const LAYOUTS: ReadonlyArray<readonly [number, number]> = [
  [80, 50],
  [60, 40],
  [40, 60],
];
const DIR: Readonly<Record<number, readonly [number, number]>> = {
  1: [0, -1],
  2: [1, 0],
  4: [0, 1],
  8: [-1, 0],
};

/** Independent oracle: undirected adjacency pairs straight from the matrix. */
function adjacencyPairs(matrix: Matrix): number[][] {
  const pairs = new Set<string>();
  matrix.nodes.forEach((node, a) => {
    for (const b of node.adjacent) if (b !== a && matrix.nodes[b]) pairs.add(a < b ? `${a},${b}` : `${b},${a}`);
  });
  return [...pairs].map((p) => p.split(",").map(Number));
}

function lines(grid: Grid): string[] {
  return grid.cells.map((row) => row.map((cell) => cell.char).join(""));
}

function token(text: string[], cx: number, cy: number): string {
  return [...(text[cy] ?? "")].slice(cx - 1, cx + 2).join("");
}

function corridorCells(matrix: Matrix, cols: number, rows: number) {
  const layout = matrixLayout(makeGrid(cols, rows), matrix);
  return new Set(
    layout.corridors.corridors.flatMap((c) => c.cells.map((cell) => `${cell.x},${cell.y}`)),
  );
}

function stateOn(matrix: Matrix, current: number): GameState {
  return {
    ...makeInitialState(
      {
        id: "board",
        title: "Board",
        fixer: "test",
        arc: 1,
        grade_min: 1,
        grade_max: 1,
        zone: "surface",
        rewards: { credits: 0, materials: {} },
      },
      { id: "watchdog", name: "Watchdog", hp: 50, armor: 0, tier: 1 },
      [],
    ),
    matrix,
    currentNodeIndex: current,
    visitedNodes: [current],
  };
}

describe("Matrix operation board — integrity rules (ADR-0249)", () => {
  const matrix = generateProceduralMatrix(3, 42);

  it("rule 1: knowledge state never hides topology — every adjacency is drawn when all is NEW", () => {
    // Given
    const all = matrix.nodes.map((_, i) => i);
    for (const [cols, rows] of LAYOUTS) {
      // When
      const fog = lines(renderMatrix(matrix, 0, [], cols, rows));
      const known = lines(renderMatrix(matrix, 0, all, cols, rows, null, null, all));
      const cells = corridorCells(matrix, cols, rows);
      // Then
      expect(cells.size).toBeGreaterThan(0);
      for (const key of cells) {
        const [x, y] = key.split(",").map(Number) as [number, number];
        expect(CORRIDOR.has([...(fog[y] ?? "")][x] ?? "")).toBe(true);
        expect(CORRIDOR.has([...(known[y] ?? "")][x] ?? "")).toBe(true);
      }
    }
  });

  it("rule 2: the whole topology fits one screen and the boss is a persistent ◆", () => {
    for (const [cols, rows] of LAYOUTS) {
      const layout = matrixLayout(makeGrid(cols, rows), matrix);
      for (let current = 0; current < matrix.nodes.length; current++) {
        // When
        const text = lines(renderMatrix(matrix, current, [current], cols, rows));
        // Then
        for (const site of layout.board.sites) {
          expect(site.cx - 1).toBeGreaterThanOrEqual(layout.inner.x);
          expect(site.cx + 1).toBeLessThan(layout.inner.x + layout.inner.width);
          expect(site.cy).toBeLessThan(layout.legendY);
        }
        const boss = layout.board.sites[matrix.bossNode];
        expect(boss).toBeDefined();
        expect(token(text, boss?.cx ?? 0, boss?.cy ?? 0)).toContain("◆");
        const diamonds = layout.board.sites.filter((s) => token(text, s.cx, s.cy).includes("◆"));
        expect(diamonds.map((s) => s.index)).toEqual([matrix.bossNode]);
      }
    }
  });

  it("rule 3: nothing is preselected; arrows highlight exactly the reducer's choice", () => {
    // Given
    const branch = 1;
    const neighbours = matrix.nodes[branch]?.adjacent ?? [];
    let state = stateOn(matrix, branch);
    const layout = matrixLayout(makeGrid(80, 50), matrix);
    // When
    const idle = lines(renderMatrix(matrix, branch, [branch], 80, 50));
    // Then
    for (const site of layout.board.sites) expect(token(idle, site.cx, site.cy)).not.toMatch(/[<>]/);
    expect(idle.join("").split("").some((ch) => TARGET.has(ch))).toBe(false);
    for (const [slot, expected] of neighbours.entries()) {
      // When
      state = applyAction(state, { type: "move_south" });
      const text = lines(renderMatrix(matrix, branch, [branch], 80, 50, null, state.selectedMatrixNodeIndex ?? null));
      // Then
      expect(state.selectedMatrixNodeIndex).toBe(neighbours[slot]);
      const targeted = layout.board.sites.filter((s) => /^>.<$/.test(token(text, s.cx, s.cy)));
      expect(targeted.map((s) => s.index)).toEqual([expected]);
      expect(state.currentNodeIndex).toBe(branch);
    }
  });

  it("rule 4: arriving draws no target; the arrival opens the verb overlay (ADR-0250) with none preselected", () => {
    // Given: a node without ICE next to a non-boss ICE node.
    const ice = (j: number): boolean => (matrix.nodes[j]?.iceIds.length ?? 0) > 0 && !matrix.nodes[j]?.isBoss;
    const from = matrix.nodes.findIndex((n, i) => n.iceIds.length === 0 && n.adjacent.some((j) => j !== i && ice(j)));
    const to = matrix.nodes[from]?.adjacent.find(ice) ?? -1;
    const slot = matrix.nodes[from]?.adjacent.indexOf(to) ?? -1;
    let state = stateOn(matrix, from);
    for (let i = 0; i <= slot; i++) state = applyAction(state, { type: "move_south" });
    // When
    const arrived = applyAction(state, { type: "confirm" });
    const text = lines(renderMatrix(matrix, arrived.currentNodeIndex, arrived.visitedNodes, 80, 50, null, arrived.selectedMatrixNodeIndex ?? null));
    const layout = matrixLayout(makeGrid(80, 50), matrix);
    // Then
    expect(arrived.currentNodeIndex).toBe(to);
    expect(arrived.encounterDecision).toEqual({ selectedVerb: null, probed: false });
    for (const site of layout.board.sites) expect(token(text, site.cx, site.cy)).not.toMatch(/^>.<$/);
    const site = layout.board.sites[to];
    expect(token(text, site?.cx ?? 0, site?.cy ?? 0)).toBe("#@#");
    const asked = applyAction(arrived, { type: "confirm" });
    expect(asked.encounterDecision?.selectedVerb).toBeNull();
    expect(asked.runPhase).toBe(arrived.runPhase);
  });

  it("rule 5: the board is the only map — every room appears once and the depth stack is gone", () => {
    for (const [cols, rows] of LAYOUTS) {
      // When
      const text = lines(renderMatrix(matrix, 1, [0, 1], cols, rows, null, 0, [0]));
      const tokens = text.flatMap((line) => [...line.matchAll(/[[#>◆][@◆·✓+][\]#<◆]/g)].map((m) => m[0]));
      // Then: one token per room plus the two legend samples.
      expect(tokens).toHaveLength(matrix.nodes.length + 2);
      expect(text.join("\n")).not.toContain("DEPTH / ZONES");
      expect(text.join("\n")).not.toContain("REACHABLE NOW (");
    }
  });

  it("rule 6: MatrixNode.adjacent is authoritative — one contiguous corridor per adjacency, nothing else", () => {
    for (const [cols, rows] of LAYOUTS) {
      // Given
      const layout = matrixLayout(makeGrid(cols, rows), matrix);
      const rooms = new Map<string, number>();
      for (const s of layout.board.sites) for (let dx = -1; dx <= 1; dx++) rooms.set(`${s.cx + dx},${s.cy}`, s.index);
      // When
      const text = lines(renderMatrix(matrix, 1, [0, 1], cols, rows, null, 0, [0]));
      // Then
      expect(layout.corridors.unrouted).toEqual([]);
      expect(layout.corridors.corridors.map((c) => [c.a, c.b]).sort()).toEqual(adjacencyPairs(matrix).sort());
      for (const c of layout.corridors.corridors) {
        c.cells.forEach((cell, k) => {
          expect(rooms.has(`${cell.x},${cell.y}`)).toBe(false);
          for (const bit of [1, 2, 4, 8]) {
            if ((cell.links & bit) === 0) continue;
            const [dx, dy] = DIR[bit] ?? [0, 0];
            const room = rooms.get(`${cell.x + dx},${cell.y + dy}`);
            const next = c.cells[k + 1];
            const prev = c.cells[k - 1];
            const toNeighbour =
              (next && next.x === cell.x + dx && next.y === cell.y + dy) ||
              (prev && prev.x === cell.x + dx && prev.y === cell.y + dy);
            if (toNeighbour) continue;
            // A link that is not to the next cell must enter an endpoint room.
            expect(room === c.a && k === 0 ? true : room === c.b && k === c.cells.length - 1).toBe(true);
          }
        });
      }
      const drawn = new Set(layout.corridors.corridors.flatMap((c) => c.cells.map((cell) => `${cell.x},${cell.y}`)));
      const { rect } = layout.board;
      for (let y = layout.inner.y; y < layout.footerY; y++)
        for (let x = layout.inner.x; x < layout.inner.x + layout.inner.width; x++) {
          const ch = [...(text[y] ?? "")][x] ?? " ";
          const onBoard = x >= rect.x && x < rect.x + rect.width && y >= rect.y && y < rect.y + rect.height;
          if (onBoard && CORRIDOR.has(ch)) expect(drawn.has(`${x},${y}`)).toBe(true);
          if (drawn.has(`${x},${y}`)) expect(CORRIDOR.has(ch)).toBe(true);
        }
    }
  });

  it("rule 7: colour never carries meaning alone — position, boss, target and route read from glyphs", () => {
    // Given
    const current = 1;
    const selected = 0;
    const frontier = matrix.nodes[current]?.adjacent ?? [];
    for (const [cols, rows] of LAYOUTS) {
      const layout = matrixLayout(makeGrid(cols, rows), matrix);
      // When: characters only, no colour.
      const text = lines(renderMatrix(matrix, current, [0, 1], cols, rows, null, selected, [0]));
      // Then
      const at = layout.board.sites.filter((s) => token(text, s.cx, s.cy).includes("@"));
      expect(at.map((s) => s.index)).toEqual([current]);
      const sel = layout.board.sites[selected];
      expect(token(text, sel?.cx ?? 0, sel?.cy ?? 0)).toBe(">+<");
      const counts = new Map<string, number>();
      for (const c of layout.corridors.corridors) for (const cell of c.cells) counts.set(`${cell.x},${cell.y}`, (counts.get(`${cell.x},${cell.y}`) ?? 0) + 1);
      for (const c of layout.corridors.corridors) {
        const other = c.a === current ? c.b : c.b === current ? c.a : null;
        const style = other === selected ? TARGET : other !== null && frontier.includes(other) ? ROUTE : LINK;
        const own = c.cells.filter((cell) => counts.get(`${cell.x},${cell.y}`) === 1);
        expect(own.length).toBeGreaterThan(0);
        for (const cell of own) expect(style.has([...(text[cell.y] ?? "")][cell.x] ?? "")).toBe(true);
      }
      expect(text.join("\n")).toMatch(/· NEW ✓ SEEN \+ CLEAR/);
    }
  });

  it("rule 8: one confirmed move is one route action, and the board stays put while @ moves", () => {
    // Given
    const start = stateOn(matrix, 1);
    const before = matrixLayout(makeGrid(80, 50), matrix);
    // When
    const selected = applyAction(start, { type: "move_south" });
    const moved = applyAction(selected, { type: "confirm" });
    const after = matrixLayout(makeGrid(80, 50), matrix);
    const text = lines(renderMatrix(matrix, moved.currentNodeIndex, moved.visitedNodes, 80, 50));
    // Then
    expect(moved.currentNodeIndex).toBe(matrix.nodes[1]?.adjacent[0]);
    expect(moved.turnCount).toBe(start.turnCount + 1);
    expect(after.board.sites).toEqual(before.board.sites);
    expect(after.corridors).toEqual(before.corridors);
    const site = after.board.sites[moved.currentNodeIndex];
    expect(token(text, site?.cx ?? 0, site?.cy ?? 0)).toMatch(/@/);
    const old = after.board.sites[1];
    expect(token(text, old?.cx ?? 0, old?.cy ?? 0)).toBe("[✓]");
  });
});

describe("Matrix board — selected-node detail card (ADR-0249)", () => {
  const matrix = generateProceduralMatrix(3, 42);

  it.each(LAYOUTS)("details each targeted neighbour before travel on %sx%s", (cols, rows) => {
    const current = 1;
    for (const i of matrix.nodes[current]?.adjacent ?? []) {
      // When
      const text = lines(renderMatrix(matrix, current, [0, 1], cols, rows, null, i, [0])).join("\n");
      const node = matrix.nodes[i];
      const id = `N${String(i + 1).padStart(2, "0")}`;
      // Then
      expect(text).toMatch(new RegExp(`> ⚔ ${id} ${node?.zone.toUpperCase()}( \\(BOSS\\))? · (NEW|SEEN|CLEAR)`));
      expect(text).toContain(`${node?.iceIds.length} ICE · ${node?.reward.credits}cr · COMBAT`);
      expect(text).toContain(node?.site?.label ?? "missing label");
      expect(text).toContain(`ROUTES (${matrix.nodes[current]?.adjacent.length}):`);
      expect(text).toContain("◆ OBJECTIVE: BOSS");
    }
  });

  it("lays out a matrix without room geometry deterministically (legacy / hand-built)", () => {
    // Given
    const bare: Matrix = { ...matrix, nodes: matrix.nodes.map(({ site: _site, ...rest }) => rest) };
    // When
    const a = matrixLayout(makeGrid(60, 40), bare);
    const b = matrixLayout(makeGrid(60, 40), { ...bare, nodes: [...bare.nodes] });
    // Then
    expect(a.board.source).toBe("fallback");
    expect(a.board.sites).toEqual(b.board.sites);
    expect(a.corridors.unrouted).toEqual([]);
    expect(new Set(a.board.sites.map((s) => `${s.cx},${s.cy}`)).size).toBe(bare.nodes.length);
  });
});

describe("Matrix board — layout stress (grades 1–6 × seeds 0–9 × every node × 3 layouts)", () => {
  it("keeps every adjacency, the objective and the selection visible with rails intact", () => {
    let cases = 0;
    let maxNodes = 0;
    let maxFrontier = 0;
    for (let grade = 1; grade <= 6; grade++)
      for (let seed = 0; seed < 10; seed++) {
        const matrix = generateProceduralMatrix(grade, seed);
        maxNodes = Math.max(maxNodes, matrix.nodes.length);
        for (const [cols, rows] of LAYOUTS) {
          const layout = matrixLayout(makeGrid(cols, rows), matrix);
          expect(layout.corridors.unrouted).toEqual([]);
          expect(layout.board.rect.y + layout.board.rect.height).toBeLessThanOrEqual(layout.legendY);
          for (const c of layout.corridors.corridors)
            for (const cell of c.cells) {
              expect(cell.x).toBeGreaterThanOrEqual(layout.inner.x);
              expect(cell.x).toBeLessThan(layout.inner.x + layout.inner.width);
              expect(cell.y).toBeGreaterThanOrEqual(layout.inner.y);
            }
          for (let current = 0; current < matrix.nodes.length; current++) {
            cases++;
            const frontier = matrix.nodes[current]?.adjacent ?? [];
            maxFrontier = Math.max(maxFrontier, frontier.length);
            const selected = frontier[0] ?? null;
            const text = lines(renderMatrix(matrix, current, [current], cols, rows, null, selected));
            expect(text[1]).toBe(` ╔${"═".repeat(cols - 4)}╗ `);
            expect(text[rows - 2]).toBe(` ╚${"═".repeat(cols - 4)}╝ `);
            for (let y = 2; y < rows - 2; y++) {
              expect(text[y]?.[1]).toBe("║");
              expect([...(text[y] ?? "")][cols - 2]).toBe("║");
              expect([...(text[y] ?? "")]).toHaveLength(cols);
            }
            const all = text.join("\n");
            expect(all).toContain("◆ OBJECTIVE: BOSS");
            expect(all).toContain(`ROUTES (${frontier.length}):`);
            const boss = layout.board.sites[matrix.bossNode];
            expect(token(text, boss?.cx ?? 0, boss?.cy ?? 0)).toContain("◆");
            const here = layout.board.sites[current];
            expect(token(text, here?.cx ?? 0, here?.cy ?? 0)).toContain("@");
            if (selected !== null) {
              const target = layout.board.sites[selected];
              expect(token(text, target?.cx ?? 0, target?.cy ?? 0)).toMatch(/^>.<$/);
            }
          }
        }
      }
    expect(cases).toBe(3132);
    expect(maxNodes).toBe(33);
    expect(maxFrontier).toBe(5);
  });
});
