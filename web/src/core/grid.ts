/** Immutable grid construction.
 *
 * wet_run uses a mutable console that updates cell-by-cell. For the
 * web MVP, we use an immutable Grid (Cells[][]) so each frame is a
 * pure function of GameState. This enables easy save/restore and
 * eliminates render-order bugs.
 */
import type { Cell, Grid, Position } from "./types.ts";
import { PALETTE } from "../renderer/palette.ts";

function getCell(cells: ReadonlyArray<ReadonlyArray<Cell>>, width: number, height: number, x: number, y: number): Cell | null {
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
