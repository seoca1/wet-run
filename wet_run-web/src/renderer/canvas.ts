/** Canvas2D ASCII grid renderer — Gibson-flavored.
 *
 * Renders Cell[][] to canvas. Uses monospace font (JetBrains Mono or
 * system fallback). Cell size is 8x16 px (1:1 with desktop grid).
 *
 * ADR-0199 §4.3: this is the foundation for "Gibson tone" validation
 * in Commit 2. Visual fidelity matters more than performance here.
 */
import type { Cell, Grid } from "../core/types.ts";
import { PALETTE } from "./palette.ts";

export interface AsciiRendererOptions {
  readonly cellWidth?: number; // default 8
  readonly cellHeight?: number; // default 16
  readonly fontFamily?: string; // default 'JetBrains Mono, monospace'
}

export class AsciiRenderer {
  private ctx: CanvasRenderingContext2D;
  private cellWidth: number;
  private cellHeight: number;
  private fontSize: number;
  private fontFamily: string;

  constructor(
    private readonly canvas: HTMLCanvasElement,
    options: AsciiRendererOptions = {},
  ) {
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      throw new Error("Failed to acquire 2D rendering context");
    }
    this.ctx = ctx;
    this.cellWidth = options.cellWidth ?? 8;
    this.cellHeight = options.cellHeight ?? 16;
    this.fontSize = this.cellHeight;
    this.fontFamily = options.fontFamily ?? '"JetBrains Mono", monospace';
    ctx.font = `${this.fontSize}px ${this.fontFamily}`;
    ctx.textBaseline = "top";
  }

  /** Resize canvas to fit a (cols × rows) grid plus HUD width. */
  resizeGrid(cols: number, rows: number, hudCols = 28): void {
    const totalCols = cols + hudCols;
    this.canvas.width = totalCols * this.cellWidth;
    this.canvas.height = rows * this.cellHeight;
  }

  /** Clear + render a complete frame. */
  render(grid: Grid, hudLines: ReadonlyArray<string>): void {
    this.clear();
    this.drawGrid(grid);
    this.drawHud(grid, hudLines);
  }

  private clear(): void {
    this.ctx.fillStyle = PALETTE.BACKGROUND;
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
  }

  private drawGrid(grid: Grid): void {
    for (let y = 0; y < grid.height; y++) {
      const row = grid.cells[y];
      if (!row) continue;
      for (let x = 0; x < grid.width; x++) {
        const cell = row[x];
        if (!cell) continue;
        this.drawCell(x, y, cell);
      }
    }
  }

  private drawCell(x: number, y: number, cell: Cell): void {
    const px = x * this.cellWidth;
    const py = y * this.cellHeight;
    this.ctx.fillStyle = cell.bg;
    this.ctx.fillRect(px, py, this.cellWidth, this.cellHeight);
    this.ctx.fillStyle = cell.fg;
    this.ctx.fillText(cell.char, px, py);
  }

  private drawHud(grid: Grid, lines: ReadonlyArray<string>): void {
    const hudX = (grid.width + 1) * this.cellWidth;
    let hudY = this.cellHeight; // 1 row padding
    for (const line of lines) {
      this.ctx.fillStyle = PALETTE.GREEN_NEON;
      this.ctx.fillText(line, hudX, hudY);
      hudY += this.cellHeight;
    }
  }

  /** Render a single character at (x, y) — for debug overlays. */
  debugChar(x: number, y: number, char: string, color = PALETTE.GRAY_DARK): void {
    this.ctx.fillStyle = color;
    this.ctx.fillText(char, x * this.cellWidth, y * this.cellHeight);
  }
}
