/** ADR-0249 travel slice: a committed move is drawn as a short traversal.
 *
 * Owner play-test: the board can be traversed; the next step is making the
 * move *feel* like a move. These tests pin the contract that keeps the
 * animation purely visual:
 *  - the reducer still moves `@` synchronously, in the confirming action;
 *  - reduced motion (ADR-0236) makes the traversal instantaneous;
 *  - the animation consumes no `Math.random` draw (ADR-0239);
 *  - the animation state never reaches `GameState` or the save;
 *  - rule 8: one confirmed move is one route action, along the one corridor
 *    of that adjacency, with no default target afterwards.
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  applyAction,
  makeInitialState,
  stateToSaveSlot,
} from "../src/core/state/state";
import { generateProceduralMatrix } from "../src/core/dungeon/matrix";
import { makeGrid } from "../src/core/grid";
import { matrixLayout, renderMatrix } from "../src/renderer/matrix";
import { suppressMotion } from "../src/renderer/accessibility_modes";
import { PALETTE } from "../src/renderer/palette";
import {
  TRAVEL_ARRIVAL_MS,
  TRAVEL_TOTAL_MS,
  TRAVEL_TRANSIT_MS,
  beginMatrixTravel,
  matrixTravelFrame,
  travelPath,
  type MatrixTravelFrame,
} from "../src/renderer/matrix_travel";
import type { GameState, Grid, Matrix } from "../src/core/types";

const LAYOUTS: ReadonlyArray<readonly [number, number]> = [
  [80, 50],
  [60, 40],
  [40, 60],
];

function stateOn(matrix: Matrix, current: number): GameState {
  return {
    ...makeInitialState(
      {
        id: "move-fixture",
        title: "Move fixture",
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
    runPhase: "matrix",
    currentNodeIndex: current,
    visitedNodes: [current],
    // Cleared, so confirm travels instead of opening the encounter menu.
    clearedEncounterNodes: matrix.nodes.map((_, i) => i),
  };
}

/** Target the k-th neighbour (k+1 ArrowDown presses) and confirm. */
function commit(
  state: GameState,
  k: number,
): { armed: GameState; moved: GameState } {
  let armed = state;
  for (let i = 0; i <= k; i += 1)
    armed = applyAction(armed, { type: "move_south" });
  return { armed, moved: applyAction(armed, { type: "confirm" }) };
}

function countDraws(fn: () => void): number {
  const original = Math.random;
  let calls = 0;
  Math.random = () => {
    calls += 1;
    return 0.5;
  };
  try {
    fn();
  } finally {
    Math.random = original;
  }
  return calls;
}

function draw(
  state: GameState,
  cols: number,
  rows: number,
  frame: MatrixTravelFrame | null,
): Grid {
  return renderMatrix(
    state.matrix as Matrix,
    state.currentNodeIndex,
    state.visitedNodes,
    cols,
    rows,
    null,
    state.selectedMatrixNodeIndex ?? null,
    state.clearedEncounterNodes ?? [],
    false,
    frame,
  );
}

/** Characters inside the board rectangle only (the card also uses `@`). */
function boardText(grid: Grid, matrix: Matrix): string[] {
  const { rect } = matrixLayout(
    makeGrid(grid.width, grid.height),
    matrix,
  ).board;
  return grid.cells.slice(rect.y, rect.y + rect.height).map((row) =>
    row
      .slice(rect.x, rect.x + rect.width)
      .map((c) => c.char)
      .join(""),
  );
}

function atCells(grid: Grid, matrix: Matrix): Array<{ x: number; y: number }> {
  const { rect } = matrixLayout(
    makeGrid(grid.width, grid.height),
    matrix,
  ).board;
  const out: Array<{ x: number; y: number }> = [];
  for (let y = rect.y; y < rect.y + rect.height; y += 1)
    for (let x = rect.x; x < rect.x + rect.width; x += 1)
      if (grid.cells[y]?.[x]?.char === "@") out.push({ x, y });
  return out;
}

const matrix = generateProceduralMatrix(3, 42);
const start = stateOn(matrix, 1);
const frames = (from: number, to: number): MatrixTravelFrame[] => {
  const travel = { from, to, startedMs: 1000 };
  const out: MatrixTravelFrame[] = [];
  for (let t = 0; t < TRAVEL_TOTAL_MS; t += 10) {
    const f = matrixTravelFrame(travel, 1000 + t);
    if (f) out.push(f);
  }
  return out;
};

describe("the state change is immediate; the animation is purely visual", () => {
  it("one confirm moves @ in the same action, and the travel describes that move", () => {
    for (let k = 0; k < (matrix.nodes[1]?.adjacent.length ?? 0); k += 1) {
      const { armed, moved } = commit(start, k);
      const target = armed.selectedMatrixNodeIndex;
      expect(target).toBe(matrix.nodes[1]?.adjacent[k]);
      expect(moved.currentNodeIndex).toBe(target);
      expect(moved.visitedNodes).toContain(target);
      expect(moved.turnCount).toBe(armed.turnCount + 1);
      const travel = beginMatrixTravel(armed, moved, 0, false);
      expect(travel).toEqual({ from: 1, to: target, startedMs: 0 });
      // Beginning or drawing a travel never touches the state.
      const snapshot = JSON.stringify(moved);
      for (const f of frames(1, target as number))
        for (const [cols, rows] of LAYOUTS) draw(moved, cols, rows, f);
      expect(JSON.stringify(moved)).toBe(snapshot);
    }
  });

  it("the traversal is bounded by the wall clock alone and ends by itself", () => {
    const travel = { from: 1, to: 8, startedMs: 500 };
    expect(TRAVEL_TRANSIT_MS + TRAVEL_ARRIVAL_MS).toBe(TRAVEL_TOTAL_MS);
    expect(TRAVEL_TOTAL_MS).toBeGreaterThanOrEqual(150);
    expect(TRAVEL_TOTAL_MS).toBeLessThanOrEqual(250);
    expect(matrixTravelFrame(travel, 500)?.phase).toBe("transit");
    expect(matrixTravelFrame(travel, 500 + TRAVEL_TRANSIT_MS)?.phase).toBe(
      "arrival",
    );
    expect(matrixTravelFrame(travel, 500 + TRAVEL_TOTAL_MS)).toBeNull();
    // A frozen clock (fake timers) holds a frame; it never changes state.
    expect(matrixTravelFrame(travel, 500)).toEqual(
      matrixTravelFrame(travel, 500),
    );
    expect(matrixTravelFrame(null, 0)).toBeNull();
  });
});

describe("reduced motion (ADR-0236) makes the traversal instantaneous", () => {
  const { armed, moved } = commit(start, 2);

  it("the travel motion kind is gated by suppressMotion", () => {
    expect(suppressMotion("travel", true)).toBe(true);
    expect(suppressMotion("travel", false)).toBe(false);
  });

  it("no travel starts when motion is suppressed; one starts otherwise", () => {
    expect(beginMatrixTravel(armed, moved, 0, true)).toBeNull();
    expect(beginMatrixTravel(armed, moved, 0, false)).not.toBeNull();
  });

  it("without a travel the board is exactly the static board: no intermediate frame", () => {
    for (const [cols, rows] of LAYOUTS) {
      const legacy = renderMatrix(
        matrix,
        moved.currentNodeIndex,
        moved.visitedNodes,
        cols,
        rows,
        null,
        null,
        moved.clearedEncounterNodes ?? [],
        false,
      );
      expect(draw(moved, cols, rows, null).cells).toEqual(legacy.cells);
    }
  });

  it("main.ts starts every travel through the controller's reduced-motion flag", () => {
    const src = readFileSync(
      fileURLToPath(new URL("../src/main.ts", import.meta.url)),
      "utf8",
    );
    expect(src).toMatch(
      /this\.matrixTravel = beginMatrixTravel\(\s*previous,\s*this\.state,\s*performance\.now\(\),\s*this\.reducedMotion,?\s*\)/,
    );
    expect(src).toContain("resolveReducedMotion(loadReducedMotionOverride())");
  });
});

describe("no RNG draw (ADR-0239)", () => {
  it("animating a move consumes zero Math.random draws beyond the reducer's own", () => {
    const reducerOnly = countDraws(() => commit(start, 2));
    let drawn = 0;
    const withAnimation = countDraws(() => {
      const { armed, moved } = commit(start, 2);
      const travel = beginMatrixTravel(armed, moved, 0, false);
      for (let t = 0; t <= TRAVEL_TOTAL_MS; t += 5) {
        const f = matrixTravelFrame(travel, t);
        if (f) drawn += 1;
        for (const [cols, rows] of LAYOUTS) draw(moved, cols, rows, f);
      }
    });
    // Non-vacuous: the traversal really produced animation frames.
    expect(drawn).toBeGreaterThan(10);
    expect(withAnimation).toBe(reducerOnly);
    const { armed, moved } = commit(start, 2);
    const animationOnly = countDraws(() => {
      const travel = beginMatrixTravel(armed, moved, 0, false);
      for (let t = 0; t <= TRAVEL_TOTAL_MS; t += 5) {
        const f = matrixTravelFrame(travel, t);
        for (const [cols, rows] of LAYOUTS) draw(moved, cols, rows, f);
      }
    });
    expect(animationOnly).toBe(0);
  });
});

describe("the animation state is transient and unsaved", () => {
  it("is absent from GameState and from the serialized save", () => {
    const { armed, moved } = commit(start, 2);
    expect(beginMatrixTravel(armed, moved, 0, false)).not.toBeNull();
    expect(Object.keys(moved).filter((key) => /travel/i.test(key))).toEqual([]);
    const slot = stateToSaveSlot(moved);
    expect(JSON.stringify(slot)).not.toMatch(/travel|startedMs/i);
    expect(slot.currentNodeIndex).toBe(moved.currentNodeIndex);
  });
});

describe("rule 8: one confirmed move is one route action", () => {
  it("leaves no default target, during or after the traversal", () => {
    const { moved } = commit(start, 2);
    expect(moved.selectedMatrixNodeIndex).toBeNull();
    const settled = boardText(draw(moved, 80, 50, null), matrix).join("\n");
    const arrival = frames(1, moved.currentNodeIndex).find(
      (f) => f.phase === "arrival",
    );
    expect(arrival).toBeDefined();
    const arrived = boardText(
      draw(moved, 80, 50, arrival ?? null),
      matrix,
    ).join("\n");
    for (const text of [settled, arrived]) expect(text).not.toMatch(/>.</u);
  });

  it("only a confirmed one-edge move animates", () => {
    const { armed, moved } = commit(start, 2);
    // The confirmed one-edge move itself does animate (positive control).
    expect(beginMatrixTravel(armed, moved, 0, false)).not.toBeNull();
    // Targeting alone is not a move.
    expect(beginMatrixTravel(start, armed, 0, false)).toBeNull();
    // A jump that is not one adjacency (e.g. CONTINUE) is not a traversal.
    const far = matrix.nodes.findIndex(
      (_, i) => i !== 1 && !(matrix.nodes[1]?.adjacent ?? []).includes(i),
    );
    expect(
      beginMatrixTravel(armed, { ...moved, currentNodeIndex: far }, 0, false),
    ).toBeNull();
    // Leaving the board is not a traversal.
    expect(
      beginMatrixTravel(armed, { ...moved, runPhase: "combat" }, 0, false),
    ).toBeNull();
  });

  it("walks exactly the one corridor of that adjacency, never through a room", () => {
    for (const [cols, rows] of LAYOUTS) {
      const layout = matrixLayout(makeGrid(cols, rows), matrix);
      for (const [a, node] of matrix.nodes.entries()) {
        for (const b of node.adjacent) {
          const path = travelPath(layout.corridors, a, b);
          const corridor = layout.corridors.corridors.find(
            (c) => (c.a === a && c.b === b) || (c.a === b && c.b === a),
          );
          expect(corridor).toBeDefined();
          expect(path.length).toBe(corridor?.cells.length);
          const rooms = new Set(
            layout.board.sites.flatMap((s) =>
              [-1, 0, 1].map((dx) => `${s.cx + dx},${s.cy}`),
            ),
          );
          for (const p of path) expect(rooms.has(`${p.x},${p.y}`)).toBe(false);
          const from = layout.board.sites[a];
          const first = path[0];
          // Oriented from the origin: the first cell touches the origin room.
          if (from && first)
            expect(
              Math.abs(first.x - from.cx) + Math.abs(first.y - from.cy),
            ).toBeLessThanOrEqual(2);
        }
      }
    }
  });

  it("every frame shows exactly one @ that advances toward the destination", () => {
    for (let k = 0; k < (matrix.nodes[1]?.adjacent.length ?? 0); k += 1) {
      const { moved } = commit(start, k);
      const to = moved.currentNodeIndex;
      for (const [cols, rows] of LAYOUTS) {
        const layout = matrixLayout(makeGrid(cols, rows), matrix);
        const path = travelPath(layout.corridors, 1, to);
        expect(path.length).toBeGreaterThan(0);
        expect(frames(1, to).some((f) => f.phase === "transit")).toBe(true);
        let previousStep = -1;
        for (const f of frames(1, to)) {
          const at = atCells(draw(moved, cols, rows, f), matrix);
          expect(at).toHaveLength(1);
          const cell = at[0] as { x: number; y: number };
          if (f.phase === "transit") {
            const step = path.findIndex(
              (p) => p.x === cell.x && p.y === cell.y,
            );
            expect(step).toBeGreaterThanOrEqual(previousStep);
            previousStep = step;
          } else {
            const site = layout.board.sites[to];
            expect(cell).toEqual({ x: site?.cx, y: site?.cy });
          }
        }
        expect(previousStep).toBe(path.length - 1);
      }
    }
  });

  it("the card agrees with the board: origin `@` in transit, destination `@` from arrival", () => {
    const { moved } = commit(start, 1);
    const to = moved.currentNodeIndex;
    const cardAt = (f: MatrixTravelFrame | null): string => {
      const text = draw(moved, 80, 50, f).cells.map((r) =>
        r.map((c) => c.char).join(""),
      );
      return text.find((l) => /║\s+@ /u.test(l) && /N\d\d/.test(l)) ?? "";
    };
    const id = (i: number) => `N${String(i + 1).padStart(2, "0")}`;
    const transit = frames(1, to).filter((f) => f.phase === "transit");
    expect(transit.length).toBeGreaterThan(0);
    for (const f of transit) expect(cardAt(f)).toContain(id(1));
    const arrival = frames(1, to).find((f) => f.phase === "arrival") ?? null;
    expect(cardAt(arrival)).toContain(id(to));
    expect(cardAt(null)).toContain(id(to));
  });

  it("the destination visibly receives the marker on arrival", () => {
    const { moved } = commit(start, 2);
    const to = moved.currentNodeIndex;
    const arrival = frames(1, to).find((f) => f.phase === "arrival") ?? null;
    const layout = matrixLayout(makeGrid(80, 50), matrix);
    const site = layout.board.sites[to];
    const grid = draw(moved, 80, 50, arrival);
    for (const dx of [-1, 0, 1]) {
      const cell = grid.cells[site?.cy ?? 0]?.[(site?.cx ?? 0) + dx];
      expect(cell?.bg).toBe(PALETTE.GREEN_NEON);
      expect(cell?.fg).toBe(PALETTE.BACKGROUND);
    }
    // Settled: the flash is gone and the board is the static board.
    const settled = draw(moved, 80, 50, null);
    expect(settled.cells[site?.cy ?? 0]?.[site?.cx ?? 0]?.bg).toBe(
      PALETTE.BACKGROUND,
    );
  });

  it("input during a traversal ends it: main.ts re-derives the travel on every action", () => {
    const src = readFileSync(
      fileURLToPath(new URL("../src/main.ts", import.meta.url)),
      "utf8",
    );
    const apply = src.indexOf(
      "this.state = applyAction(this.state, resolved);",
    );
    const begin = src.indexOf("this.matrixTravel = beginMatrixTravel(");
    expect(apply).toBeGreaterThan(0);
    expect(begin).toBeGreaterThan(apply);
    // The travel never feeds back into the reducer.
    expect(src).not.toMatch(/applyAction\([^)]*matrixTravel/);
  });
});
