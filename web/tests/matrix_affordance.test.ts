/** ADR-0249 affordance slice: the Matrix board states what to press.
 *
 * Owner play-test: the spatial board is preferred over the list, but "I can't
 * tell what to do". These tests pin the fix: the routes line maps each key
 * press to a destination, the at-rest prompt is the card's first line (and is
 * never a selection), and a one-time entry hint teaches the board once.
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { applyAction, makeInitialState } from "../src/core/state/state";
import { generateProceduralMatrix } from "../src/core/dungeon/matrix";
import { makeGrid } from "../src/core/grid";
import { matrixLayout, renderMatrix } from "../src/renderer/matrix";
import { renderRunScreen } from "../src/renderer/run_screen";
import {
  MATRIX_ROUTE_PROMPT,
  matrixNodeId,
} from "../src/renderer/matrix_nodes";
import {
  MATRIX_ENTRY_HINT_LINES,
  shouldShowMatrixEntryHint,
} from "../src/core/state/onboarding";
import type { GameState, Grid, Matrix } from "../src/core/types";

const LAYOUTS: ReadonlyArray<readonly [number, number]> = [
  [80, 50],
  [60, 40],
  [40, 60],
];

function lines(grid: Grid): string[] {
  return grid.cells.map((row) => row.map((cell) => cell.char).join(""));
}

/** Card text between the frame rails, trailing blanks trimmed. */
function inner(line: string): string {
  return [...line].slice(2, -2).join("").trim();
}

function stateOn(matrix: Matrix, current: number): GameState {
  return {
    ...makeInitialState(
      {
        id: "afford",
        title: "Afford",
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
  };
}

function press(state: GameState, times: number): GameState {
  let out = state;
  for (let i = 0; i < times; i += 1)
    out = applyAction(out, { type: "move_south" });
  return out;
}

/** The ROUTES block: the `ROUTES (n):` row plus its indented continuation. */
function routesBlock(text: string[]): string {
  const start = text.findIndex((l) => l.includes("ROUTES ("));
  const first = inner(text[start] ?? "");
  const next = inner(text[start + 1] ?? "");
  return /^(↓\d+ N\d\d|>N\d\d)/.test(next) ? `${first}  ${next}` : first;
}

/** `↓k Nxx` claims parsed from the ROUTES block. */
function claims(block: string): Array<{ presses: number; id: string }> {
  return [...block.matchAll(/↓(\d+) (N\d\d)/g)].map((m) => ({
    presses: Number(m[1]),
    id: m[2] ?? "",
  }));
}

describe("Matrix affordance — the routes line maps each key press to a destination", () => {
  const matrix = generateProceduralMatrix(3, 42);
  const branch = 1; // four routes: exercises the 40-column wrap

  it.each(LAYOUTS)(
    "at rest, ↓k names exactly the room k ArrowDowns target (%sx%s)",
    (cols, rows) => {
      // Given
      const state = stateOn(matrix, branch);
      const adjacent = matrix.nodes[branch]?.adjacent ?? [];
      // When
      const block = routesBlock(
        lines(
          renderMatrix(matrix, branch, [0, 1], cols, rows, null, null, [0]),
        ),
      );
      // Then: one claim per route, numbered 1..n, each honoured by the reducer.
      expect(block.startsWith(`ROUTES (${adjacent.length}): ↓1 `)).toBe(true);
      const parsed = claims(block);
      expect(parsed.map((c) => c.presses)).toEqual(
        adjacent.map((_, k) => k + 1),
      );
      for (const { presses, id } of parsed) {
        const selected = press(state, presses).selectedMatrixNodeIndex;
        expect(
          selected === null || selected === undefined
            ? "none"
            : matrixNodeId(selected),
        ).toBe(id);
      }
    },
  );

  it.each(LAYOUTS)(
    "with a target, ↓k counts presses from the target and the target reads >Nxx (%sx%s)",
    (cols, rows) => {
      const adjacent = matrix.nodes[branch]?.adjacent ?? [];
      for (let slot = 0; slot < adjacent.length; slot += 1) {
        // Given: the player pressed ↓ slot+1 times.
        const state = press(stateOn(matrix, branch), slot + 1);
        const target = state.selectedMatrixNodeIndex ?? -1;
        // When
        const block = routesBlock(
          lines(
            renderMatrix(matrix, branch, [0, 1], cols, rows, null, target, [0]),
          ),
        );
        // Then
        expect(block).toContain(`>${matrixNodeId(target)}`);
        const parsed = claims(block);
        expect(parsed).toHaveLength(adjacent.length - 1);
        for (const { presses, id } of parsed) {
          const next = press(state, presses).selectedMatrixNodeIndex ?? -1;
          expect(matrixNodeId(next)).toBe(id);
        }
      }
    },
  );

  it("states the mapping for every node of every generated matrix at every layout, unclipped", () => {
    let cases = 0;
    for (let grade = 1; grade <= 6; grade++)
      for (let seed = 0; seed < 10; seed++) {
        const m = generateProceduralMatrix(grade, seed);
        for (const [cols, rows] of LAYOUTS)
          for (let current = 0; current < m.nodes.length; current++) {
            const adjacent = m.nodes[current]?.adjacent ?? [];
            const text = lines(renderMatrix(m, current, [current], cols, rows));
            const block = routesBlock(text);
            const expected = adjacent
              .map((i, k) => `↓${k + 1} ${matrixNodeId(i)}`)
              .join("  ");
            expect(block).toBe(
              `ROUTES (${adjacent.length}): ${expected || "none"}`,
            );
            if (adjacent.length > 0)
              expect(text.join("\n")).toContain(MATRIX_ROUTE_PROMPT);
            for (let y = 2; y < rows - 2; y++) {
              expect(text[y]?.[1]).toBe("║");
              expect([...(text[y] ?? "")][cols - 2]).toBe("║");
            }
            cases++;
          }
      }
    expect(cases).toBe(3132);
  });
});

describe("Matrix affordance — the prompt is primary and is never a selection", () => {
  const matrix = generateProceduralMatrix(3, 42);

  it.each(LAYOUTS)(
    "at rest the prompt is the card's first line, above @, with no target anywhere (%sx%s)",
    (cols, rows) => {
      // Given: a fresh run on the board — the reducer has selected nothing.
      const state = stateOn(matrix, matrix.startNode);
      expect(state.selectedMatrixNodeIndex ?? null).toBeNull();
      // When
      const text = lines(
        renderRunScreen(state, cols, rows)?.grid ?? makeGrid(cols, rows),
      );
      const layout = matrixLayout(makeGrid(cols, rows), matrix);
      // Then
      expect(inner(text[layout.cardY] ?? "")).toBe(MATRIX_ROUTE_PROMPT);
      expect(inner(text[layout.cardY + 1] ?? "")).toMatch(/^@ /);
      expect(MATRIX_ROUTE_PROMPT).not.toMatch(/N\d\d/); // names no room
      // no target token on the board (the legend's sample row is excluded)
      expect(text.slice(0, layout.legendY).join("\n")).not.toMatch(/>.</);
      expect(text.some((l) => inner(l).startsWith("> "))).toBe(false); // no target line in the card
      // ADR-0250: the start node has no ICE, so at rest ENTER does nothing;
      // the footer offers the route pick instead of promising an ICE.
      expect(text.join("\n")).toContain(
        cols < 44 ? "↑↓ pick route" : "↑↓: pick route",
      );
    },
  );

  it.each(LAYOUTS)(
    "once a target exists the prompt is gone and the footer says travel (%sx%s)",
    (cols, rows) => {
      // Given
      const state = press(stateOn(matrix, matrix.startNode), 1);
      // When
      const text = lines(
        renderRunScreen(state, cols, rows)?.grid ?? makeGrid(cols, rows),
      );
      const layout = matrixLayout(makeGrid(cols, rows), matrix);
      // Then
      const target = matrixNodeId(state.selectedMatrixNodeIndex ?? -1);
      expect(text.join("\n")).not.toContain(MATRIX_ROUTE_PROMPT);
      expect(inner(text[layout.cardY] ?? "")).toMatch(
        new RegExp(`^> . ${target} `),
      );
      expect(text.join("\n")).toContain(
        cols < 44 ? "ENTER travel" : "ENTER: travel",
      );
    },
  );

  it("keeps the no-default-target rule: arrival, prompt and hint never select", () => {
    // Given / When: a fresh state, a travel, and a hinted render.
    const fresh = stateOn(matrix, matrix.startNode);
    const arrived = applyAction(press(fresh, 1), { type: "confirm" });
    // Then
    expect(fresh.selectedMatrixNodeIndex ?? null).toBeNull();
    expect(arrived.currentNodeIndex).not.toBe(matrix.startNode);
    expect(arrived.selectedMatrixNodeIndex).toBeNull();
    const hintedRows = lines(
      renderMatrix(matrix, matrix.startNode, [], 80, 50, null, null, [], true),
    );
    const { legendY } = matrixLayout(makeGrid(80, 50), matrix);
    expect(hintedRows.slice(0, legendY).join("\n")).not.toMatch(/>.</);
    const hinted = hintedRows.join("\n");
    expect(hinted).toContain(MATRIX_ROUTE_PROMPT);
  });
});

describe("Matrix affordance — one-time entry hint (reuses the ADR-0235 onboarding pattern)", () => {
  const matrix = generateProceduralMatrix(3, 42);
  const mainSource = readFileSync(
    fileURLToPath(new URL("../src/main.ts", import.meta.url)),
    "utf-8",
  ).replace(/\s+/g, "");

  it("shows only on the matrix board with a route, before it has been shown", () => {
    const board = stateOn(matrix, matrix.startNode);
    expect(shouldShowMatrixEntryHint(false, board)).toBe(true);
    expect(shouldShowMatrixEntryHint(true, board)).toBe(false); // later visits
    expect(
      shouldShowMatrixEntryHint(false, { ...board, runPhase: "combat" }),
    ).toBe(false);
    expect(
      shouldShowMatrixEntryHint(false, {
        ...board,
        encounterDecision: { selectedVerb: null, probed: false },
      }),
    ).toBe(false);
    const island: Matrix = {
      ...matrix,
      nodes: matrix.nodes.map((n) => ({ ...n, adjacent: [] })),
    };
    expect(shouldShowMatrixEntryHint(false, { ...board, matrix: island })).toBe(
      false,
    );
    expect(shouldShowMatrixEntryHint(false, null)).toBe(false);
  });

  it.each(LAYOUTS)(
    "draws the hint in full below the card without covering it, rails intact (%sx%s)",
    (cols, rows) => {
      for (let grade = 1; grade <= 6; grade++)
        for (let seed = 0; seed < 10; seed++) {
          const m = generateProceduralMatrix(grade, seed);
          const plain = lines(renderMatrix(m, m.startNode, [], cols, rows));
          const text = lines(
            renderMatrix(m, m.startNode, [], cols, rows, null, null, [], true),
          );
          const layout = matrixLayout(makeGrid(cols, rows), m);
          const rowsWithHint = MATRIX_ENTRY_HINT_LINES.map((line) =>
            text.findIndex((l) => inner(l) === line),
          );
          for (const y of rowsWithHint) {
            expect(y).toBeGreaterThanOrEqual(layout.cardY + 8);
            expect(y).toBeLessThan(layout.footerY);
          }
          // Everything except the hint rows is identical to the unhinted board.
          text.forEach((l, y) => {
            if (!rowsWithHint.includes(y)) expect(l).toBe(plain[y]);
          });
        }
    },
  );

  it("is absent unless asked for", () => {
    const text = lines(renderMatrix(matrix, matrix.startNode, [], 80, 50)).join(
      "\n",
    );
    for (const line of MATRIX_ENTRY_HINT_LINES)
      expect(text).not.toContain(line);
    const viaScreen = lines(
      renderRunScreen(stateOn(matrix, matrix.startNode), 80, 50, true)?.grid ??
        makeGrid(80, 50),
    ).join("\n");
    for (const line of MATRIX_ENTRY_HINT_LINES)
      expect(viaScreen).toContain(line);
  });

  it("main.ts shows it once: gated by its flag, dismissed by the first input on the board", () => {
    expect(mainSource).toContain("privatematrixEntryHintShown=false;");
    expect(mainSource).toMatch(
      /renderRunScreen\(this\.state,this\.layout\.cols,this\.layout\.rows,shouldShowMatrixEntryHint\(this\.matrixEntryHintShown,this\.state\),?\)/,
    );
    expect(mainSource).toMatch(
      /if\(shouldShowMatrixEntryHint\(this\.matrixEntryHintShown,this\.state\)\)this\.matrixEntryHintShown=true;[\s\S]{0,200}this\.state=applyAction\(this\.state,resolved\)/,
    );
  });
});
