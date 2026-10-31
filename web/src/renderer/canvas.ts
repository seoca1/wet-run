/** Canvas2D ASCII grid renderer — Gibson-flavored.
 *
 * Renders Cell[][] to canvas. Uses monospace font (JetBrains Mono or
 * system fallback). Cells fill the available viewport without CSS downscaling.
 *
 * ADR-0199 §4.3: this is the foundation for "Gibson tone" validation
 * in Commit 2. Visual fidelity matters more than performance here.
 */
import type { Cell, Grid } from "../core/types";
import type { Layout } from "../core/layout";
import { canvasGeometry, sanitizeTextScale } from "./canvas_geometry";
import { PALETTE } from "./palette";

export interface AsciiRendererOptions {
  readonly cellWidth?: number;
  readonly cellHeight?: number;
  readonly fontFamily?: string;
  /** Cell/font multiplier; larger text reduces presentation rows and columns. */
  readonly textScale?: number;
}

export class AsciiRenderer {
  private ctx: CanvasRenderingContext2D;
  private cellWidth: number;
  private cellHeight: number;
  private fontSize: number;
  private fontFamily: string;
  private dpr: number;
  private textScale: number;
  private hudCols = 28;

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
    this.dpr = typeof window !== "undefined" ? window.devicePixelRatio || 1 : 1;
    this.textScale = sanitizeTextScale(options.textScale ?? 1);
    ctx.font = `${this.fontSize}px ${this.fontFamily}`;
    ctx.textBaseline = "top";
  }

  /** Apply scale on the next resize; callers use its returned presentation layout. */
  setTextScale(scale: number): void {
    this.textScale = sanitizeTextScale(scale);
  }

  /** The current text scale multiplier. */
  getTextScale(): number {
    return this.textScale;
  }

  /** Fill the safe viewport and return the grid dimensions that actually fit.
   * Always pass the unscaled breakpoint preset to avoid cumulative scaling.
   */
  resizeGrid(
    cols: number,
    rows: number,
    hudCols = 28,
    orientation: Layout["orientation"] = "landscape",
    breakpoint: Layout["breakpoint"] = "large",
  ): Layout {
    const baseLayout = { cols, rows, hudCols, orientation, breakpoint };
    const padding = getComputedStyle(document.body);
    const horizontalInset =
      (parseFloat(padding.paddingLeft) || 0) +
      (parseFloat(padding.paddingRight) || 0);
    const verticalInset =
      (parseFloat(padding.paddingTop) || 0) +
      (parseFloat(padding.paddingBottom) || 0);
    this.dpr = window.devicePixelRatio || 1;
    const geometry = canvasGeometry(
      baseLayout,
      {
        width: window.innerWidth - horizontalInset,
        height: window.innerHeight - verticalInset,
        dpr: this.dpr,
      },
      this.textScale,
    );
    this.cellWidth = geometry.cellWidth;
    this.cellHeight = geometry.cellHeight;
    this.hudCols = geometry.layout.hudCols;
    this.fontSize = this.cellHeight;
    this.canvas.width = geometry.backingWidth;
    this.canvas.height = geometry.backingHeight;
    this.canvas.style.width = `${geometry.cssWidth}px`;
    this.canvas.style.height = `${geometry.cssHeight}px`;
    this.ctx.setTransform(
      geometry.backingWidth / geometry.cssWidth,
      0,
      0,
      geometry.backingHeight / geometry.cssHeight,
      0,
      0,
    );
    this.ctx.font = `${this.fontSize}px ${this.fontFamily}`;
    this.ctx.textBaseline = "top";
    return geometry.layout;
  }

  /** Clear + render a complete frame.
   *
   * `hudColorFor` (optional) lets callers tint individual HUD lines (e.g.
   * alarm = 100% shown in amber instead of green) without breaking the existing
   * ReadonlyArray<string> contract.
   *
   * `offset` (optional) shifts the WHOLE canvas in CSS pixels. This is the
   * P1 screen shake: the grid characters and the HUD move together, so the
   * shake reads as the viewport moving rather than as the ASCII art jittering
   * inside a static frame.
   */
  render(
    grid: Grid,
    hudLines: ReadonlyArray<string>,
    hudColorFor?: (line: string, index: number) => string | undefined,
    offset?: { readonly x: number; readonly y: number },
  ): void {
    this.clear();
    if (offset !== undefined && (offset.x !== 0 || offset.y !== 0)) {
      this.ctx.save();
      this.ctx.translate(offset.x, offset.y);
      this.drawGrid(grid);
      this.drawHud(grid, hudLines, hudColorFor);
      this.ctx.restore();
      return;
    }
    this.drawGrid(grid);
    this.drawHud(grid, hudLines, hudColorFor);
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
    this.ctx.fillText(cell.char, px, py, this.cellWidth);
  }

  private drawHud(
    grid: Grid,
    lines: ReadonlyArray<string>,
    colorFor?: (line: string, index: number) => string | undefined,
  ): void {
    const hudX = (grid.width + 1) * this.cellWidth;
    let hudY = this.cellHeight;
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i] ?? "";
      const override = colorFor?.(line, i);
      this.ctx.fillStyle = override ?? PALETTE.GREEN_NEON;
      this.ctx.fillText(
        line,
        hudX,
        hudY,
        Math.max(1, this.hudCols - 1) * this.cellWidth,
      );
      hudY += this.cellHeight;
    }
  }

  /** Render a single character at (x, y) — for debug overlays. */
  debugChar(
    x: number,
    y: number,
    char: string,
    color = PALETTE.GRAY_DARK,
  ): void {
    this.ctx.fillStyle = color;
    this.ctx.fillText(char, x * this.cellWidth, y * this.cellHeight);
  }
}
