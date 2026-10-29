/** P10 — text scale at the cell/font level (renderer/canvas.ts).
 *
 * The default scale is 1.0 — the cell geometry and font size must be
 * byte-identical to the pre-P10 renderer.
 */
// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from "vitest";
import { AsciiRenderer } from "../src/renderer/canvas";
import { PALETTE } from "../src/renderer/palette";
import type { Grid } from "../src/core/types";

function emptyGrid(width = 10, height = 10): Grid {
  const cells: { char: string; fg: string; bg: string }[][] = [];
  for (let y = 0; y < height; y++) {
    const row: { char: string; fg: string; bg: string }[] = [];
    for (let x = 0; x < width; x++) {
      row.push({ char: " ", fg: PALETTE.FOREGROUND, bg: PALETTE.BACKGROUND });
    }
    cells.push(row);
  }
  return { width, height, cells, get: () => cells[0]?.[0] ?? null };
}
/** jsdom has no 2D context — a class-based stub that records the canvas size
 * and every `font` assignment. */
class FakeCtx {
  font = "";
  _textBaseline = "";
  fillRect = (): void => {};
  fillText = (): void => {};
  setTransform = (): void => {};
  save = (): void => {};
  restore = (): void => {};
  translate = (): void => {};
  get textBaseline(): string {
    return this._textBaseline;
  }
  set textBaseline(v: string) {
    this._textBaseline = v;
  }
  get fillStyle(): string {
    return "";
  }
  set fillStyle(_v: string) {}
}

function makeCanvas(width = 400, height = 400): {
  canvas: HTMLCanvasElement;
  fonts: string[];
  ctx: FakeCtx;
} {
  const fonts: string[] = [];
  const ctx = new FakeCtx();
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  vi.spyOn(canvas, "getContext").mockReturnValue(
    ctx as unknown as CanvasRenderingContext2D,
  );
  Object.defineProperty(ctx, "font", {
    get: () => "",
    set: (v: string) => {
      fonts.push(v);
    },
  });
  return { canvas, fonts, ctx };
}

describe("AsciiRenderer text scale", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("default scale leaves the canvas geometry unchanged", () => {
    const { canvas } = makeCanvas();
    const renderer = new AsciiRenderer(canvas);
    renderer.resizeGrid(80, 50, 28, "landscape", "large");
    // standard_landscape is 8x16 in landscape/large → 108 cols * 8 = 864.
    expect(canvas.style.width).toBe("864px");
    expect(canvas.style.height).toBe("800px");
  });

  it("a scale of 1.0 is identical to no scale at all", () => {
    const plain = makeCanvas();
    const scaled = makeCanvas();
    const a = new AsciiRenderer(plain.canvas);
    const b = new AsciiRenderer(scaled.canvas, { textScale: 1.0 });
    a.resizeGrid(80, 50, 28, "landscape", "large");
    b.resizeGrid(80, 50, 28, "landscape", "large");
    expect(scaled.canvas.style.width).toBe(plain.canvas.style.width);
    expect(scaled.canvas.style.height).toBe(plain.canvas.style.height);
    expect(scaled.fonts[scaled.fonts.length - 1]).toBe(
      plain.fonts[plain.fonts.length - 1],
    );
  });

  it("a scale > 1 enlarges the cells and the font", () => {
    const { canvas, fonts } = makeCanvas();
    const renderer = new AsciiRenderer(canvas, { textScale: 2 });
    renderer.resizeGrid(80, 50, 28, "landscape", "large");
    expect(canvas.style.width).toBe("1728px");
    expect(canvas.style.height).toBe("1600px");
    expect(fonts[fonts.length - 1]).toContain("32px");
  });

  it("a scale < 1 shrinks the cells and the font", () => {
    const { canvas, fonts } = makeCanvas();
    const renderer = new AsciiRenderer(canvas, { textScale: 0.5 });
    renderer.resizeGrid(80, 50, 28, "landscape", "large");
    expect(canvas.style.width).toBe("432px");
    expect(canvas.style.height).toBe("400px");
    expect(fonts[fonts.length - 1]).toContain("8px");
  });

  it("setTextScale applies the new factor to a live renderer", () => {
    const { canvas } = makeCanvas();
    const renderer = new AsciiRenderer(canvas);
    renderer.resizeGrid(80, 50, 28, "landscape", "large");
    const before = canvas.style.width;
    renderer.setTextScale(2);
    renderer.resizeGrid(80, 50, 28, "landscape", "large");
    expect(canvas.style.width).toBe(`${parseInt(before, 10) * 2}px`);
  });

  it("setTextScale(1) restores the default geometry", () => {
    const { canvas } = makeCanvas();
    const renderer = new AsciiRenderer(canvas);
    renderer.resizeGrid(80, 50, 28, "landscape", "large");
    const base = canvas.style.width;
    renderer.setTextScale(2);
    renderer.setTextScale(1);
    renderer.resizeGrid(80, 50, 28, "landscape", "large");
    expect(canvas.style.width).toBe(base);
  });

  it("rejects a non-positive or NaN scale (falls back to 1.0)", () => {
    const { canvas } = makeCanvas();
    const renderer = new AsciiRenderer(canvas, { textScale: 0 });
    renderer.resizeGrid(80, 50, 28, "landscape", "large");
    expect(canvas.style.width).toBe("864px");
  });

  it("rejects a NaN scale (falls back to 1.0)", () => {
    const { canvas } = makeCanvas();
    const renderer = new AsciiRenderer(canvas, { textScale: Number.NaN });
    renderer.resizeGrid(80, 50, 28, "landscape", "large");
    expect(canvas.style.width).toBe("864px");
  });

  it("renders a grid without error at a scaled size", () => {
    const { canvas } = makeCanvas();
    const renderer = new AsciiRenderer(canvas, { textScale: 1.5 });
    renderer.resizeGrid(20, 10, 12, "landscape", "medium");
    expect(() => renderer.render(emptyGrid(20, 10), ["HUD"])).not.toThrow();
  });
});
