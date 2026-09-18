/** Immutable grid construction.
 *
 * wet_run uses a mutable console that updates cell-by-cell. For the
 * web MVP, we use an immutable Grid (Cells[][]) so each frame is a
 * pure function of GameState. This enables easy save/restore and
 * eliminates render-order bugs.
 */
import type { Cell, Position } from "./types.ts";
import { PALETTE } from "../renderer/palette.ts";

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

/** Render a static text block. */
export function setText(
  grid: Grid,
  x: number,
  y: number,
  text: string,
  fg: string = PALETTE.GREEN_NEON,
): Grid {
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

export function drawRect(grid: Grid, x: number, y: number, w: number, h: number, color: string): Grid {
  let g = grid;
  for (let dy = 0; dy < h; dy++) {
    for (let dx = 0; dx < w; dx++) {
      const px = x + dx;
      const py = y + dy;
      if (px >= 0 && px < grid.width && py >= 0 && py < grid.height) {
        g = setText(g, px, py, "█", color);
      }
    }
  }
  return g;
}

export function drawLine(grid: Grid, x0: number, y0: number, x1: number, y1: number, color: string): Grid {
  let g = grid;
  const dx = Math.abs(x1 - x0);
  const dy = Math.abs(y1 - y0);
  const sx = x0 < x1 ? 1 : -1;
  const sy = y0 < y1 ? 1 : -1;
  let err = dx - dy;
  let x = x0;
  let y = y0;

  while (true) {
    if (x >= 0 && x < grid.width && y >= 0 && y < grid.height) {
      g = setText(g, x, y, "·", color);
    }
    if (x === x1 && y === y1) break;
    const e2 = 2 * err;
    if (e2 > -dy) { err -= dy; x += sx; }
    if (e2 < dx) { err += dx; y += sy; }
  }
  return g;
}