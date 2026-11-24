/** Immutable grid construction.
 *
 * wet_run uses a mutable console that updates cell-by-cell. For the
 * web MVP, we use an immutable Grid (Cells[][]) so each frame is a
 * pure function of GameState. This enables easy save/restore and
 * eliminates render-order bugs.
 */
import type { Cell, Position } from "./types";
import { PALETTE } from "../renderer/palette";

/** A 2D grid of cells with immutable operations. */
export interface Grid {
  readonly width: number;
  readonly height: number;
  readonly cells: ReadonlyArray<ReadonlyArray<Cell>>;
  get(x: number, y: number): Cell | null;
  readonly [x: number]: ReadonlyArray<Cell> | undefined;
}

/** Get a cell at position, or null if out of bounds. */
export function getCell(
  cells: ReadonlyArray<ReadonlyArray<Cell>>,
  width: number,
  height: number,
  x: number,
  y: number,
): Cell | null {
  if (x < 0 || y < 0 || x >= width || y >= height) return null;
  return cells[y]?.[x] ?? null;
}

/** Build an empty grid filled with background cells. */
export function makeGrid(width: number, height: number, bgColor = PALETTE.BACKGROUND): Grid {
  const cells: Cell[][] = [];
  for (let y = 0; y < height; y++) {
    const row: Cell[] = [];
    for (let x = 0; x < width; x++) {
      row.push({ char: " ", fg: PALETTE.FOREGROUND, bg: bgColor });
    }
    cells.push(row);
  }
  return {
    width,
    height,
    cells,
    get(x: number, y: number): Cell | null {
      return getCell(cells, width, height, x, y);
    },
  };
}

/** Pure function: write a cell into a new grid (returns new instance). */
export function setCell(grid: Grid, pos: Position, cell: Cell): Grid {
  if (pos.x < 0 || pos.y < 0 || pos.x >= grid.width || pos.y >= grid.height) {
    return grid;
  }
  const newCells = grid.cells.map((row, y) =>
    y === pos.y ? row.map((c, x) => (x === pos.x ? cell : c)) : row,
  );
  return makeGridFromCells(grid.width, grid.height, newCells);
}

/** Strings a renderer had to drop or cut since the last drain (ADR-0300).
 *
 * Two ways a screen loses text, and both are silent without this record:
 *
 * - **Horizontal.** The loot screen shipped twice with prices clipped mid-number
 *   because a line can only be checked against a width at the moment it is
 *   drawn.
 * - **Vertical.** The encounter screen's ICE voice pushed "ESC: jack out" off
 *   the bottom of the panel (2026-11-16). Nothing failed: the line was simply
 *   never drawn, so a guard that only checked width saw nothing wrong.
 *
 * A test renders every screen at every layout and asserts the list is empty, so
 * either kind of loss fails the build instead of quietly dropping digits or a
 * key hint.
 *
 * Bounded so a pathological frame cannot grow it without limit.
 */
let clipped: string[] = [];
const CLIPPED_CAP = 64;

/** The strings dropped or cut since the last call, and clears the record. */
export function takeClippedText(): readonly string[] {
  const out = clipped;
  clipped = [];
  return out;
}

/** Record a string that had to be dropped or cut, so panel-clipped and
 * off-grid text is caught by the same ADR-0300 guard as `setText` overflow.
 * `setInnerText` truncates or drops before it reaches `setText`, so without
 * this a panel could lose its right edge or its last line silently. */
export function recordClippedText(text: string): void {
  if (clipped.length < CLIPPED_CAP) clipped.push(text);
}

/** Render a static text block. */
export function setText(
  grid: Grid,
  x: number,
  y: number,
  text: string,
  fg: string = PALETTE.GREEN_NEON,
): Grid {
  // Off-grid text is dropped whole — the same loss as a cut, so the same record.
  if (x + text.length > grid.width || y < 0 || y >= grid.height) {
    recordClippedText(text);
  }
  let current = grid;
  for (let i = 0; i < text.length && x + i < grid.width; i++) {
    const ch = text[i];
    if (ch === undefined) break;
    const cell: Cell = { char: ch, fg, bg: PALETTE.BACKGROUND };
    current = setCell(current, { x: x + i, y }, cell);
  }
  return current;
}

function makeGridFromCells(
  width: number,
  height: number,
  cells: ReadonlyArray<ReadonlyArray<Cell>>,
): Grid {
  return {
    width,
    height,
    cells,
    get(x: number, y: number): Cell | null {
      return getCell(cells, width, height, x, y);
    },
  };
}
