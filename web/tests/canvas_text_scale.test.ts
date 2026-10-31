/** ADR-0237: the viewport stays fixed while text scale changes presentation density. */
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

function makeCanvas(
  width = 400,
  height = 400,
): {
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
    Object.defineProperty(window, "innerWidth", {
      value: 1440,
      configurable: true,
    });
    Object.defineProperty(window, "innerHeight", {
      value: 900,
      configurable: true,
    });
    Object.defineProperty(window, "devicePixelRatio", {
      value: 1,
      configurable: true,
    });
    document.body.style.padding = "0px";
  });

  it("default scale fills the viewport instead of choosing fixed pixel cells", () => {
    const { canvas } = makeCanvas();
    const renderer = new AsciiRenderer(canvas);
    renderer.resizeGrid(80, 50, 28, "landscape", "large");
    expect(canvas.style.width).toBe("1440px");
    expect(canvas.style.height).toBe("900px");
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
    const layout = renderer.resizeGrid(80, 50, 28, "landscape", "large");
    expect(canvas.style.width).toBe("1440px");
    expect(canvas.style.height).toBe("900px");
    expect(layout.rows).toBe(25);
    expect(fonts[fonts.length - 1]).toContain("36px");
  });

  it("a scale < 1 shrinks cells only as far as the legible minimum", () => {
    const { canvas, fonts } = makeCanvas();
    const renderer = new AsciiRenderer(canvas, { textScale: 0.5 });
    const layout = renderer.resizeGrid(80, 50, 28, "landscape", "large");
    expect(canvas.style.width).toBe("1440px");
    expect(canvas.style.height).toBe("900px");
    expect(layout.rows).toBe(75);
    expect(fonts[fonts.length - 1]).toContain("12px");
  });

  it("setTextScale applies the new factor to a live renderer", () => {
    const { canvas, fonts } = makeCanvas();
    const renderer = new AsciiRenderer(canvas);
    renderer.resizeGrid(80, 50, 28, "landscape", "large");
    const before = parseFloat(fonts[fonts.length - 1] ?? "0");
    renderer.setTextScale(2);
    renderer.resizeGrid(80, 50, 28, "landscape", "large");
    expect(parseFloat(fonts[fonts.length - 1] ?? "0")).toBe(before * 2);
    expect(canvas.style.width).toBe("1440px");
  });

  it("setTextScale(1) restores the default geometry", () => {
    const { canvas, fonts } = makeCanvas();
    const renderer = new AsciiRenderer(canvas);
    renderer.resizeGrid(80, 50, 28, "landscape", "large");
    const base = fonts[fonts.length - 1];
    renderer.setTextScale(2);
    renderer.setTextScale(1);
    renderer.resizeGrid(80, 50, 28, "landscape", "large");
    expect(fonts[fonts.length - 1]).toBe(base);
  });

  it("rejects a non-positive or NaN scale (falls back to 1.0)", () => {
    const { canvas } = makeCanvas();
    const renderer = new AsciiRenderer(canvas, { textScale: 0 });
    renderer.resizeGrid(80, 50, 28, "landscape", "large");
    expect(canvas.style.width).toBe("1440px");
  });

  it("rejects a NaN scale (falls back to 1.0)", () => {
    const { canvas } = makeCanvas();
    const renderer = new AsciiRenderer(canvas, { textScale: Number.NaN });
    renderer.resizeGrid(80, 50, 28, "landscape", "large");
    expect(canvas.style.width).toBe("1440px");
  });

  it("renders a grid without error at a scaled size", () => {
    const { canvas } = makeCanvas();
    const renderer = new AsciiRenderer(canvas, { textScale: 1.5 });
    renderer.resizeGrid(20, 10, 12, "landscape", "medium");
    expect(() => renderer.render(emptyGrid(20, 10), ["HUD"])).not.toThrow();
  });

  it("subtracts safe-area padding and refreshes DPR when resizing", () => {
    const { canvas, ctx } = makeCanvas();
    const renderer = new AsciiRenderer(canvas);
    document.body.style.padding = "10px 20px";
    Object.defineProperty(window, "devicePixelRatio", {
      value: 2,
      configurable: true,
    });
    const transform = vi.spyOn(ctx, "setTransform");

    renderer.resizeGrid(100, 60, 28, "landscape", "xlarge");

    expect([canvas.style.width, canvas.style.height]).toEqual([
      "1400px",
      "880px",
    ]);
    expect([canvas.width, canvas.height]).toEqual([2800, 1760]);
    expect(transform).toHaveBeenCalledWith(2, 0, 0, 2, 0, 0);
  });

  it("draws the HUD inside its allocated columns when large text reduces the grid", () => {
    const { canvas, ctx } = makeCanvas();
    const renderer = new AsciiRenderer(canvas, { textScale: 1.25 });
    const layout = renderer.resizeGrid(100, 60, 28, "landscape", "xlarge");
    const text = vi.spyOn(ctx, "fillText");

    renderer.render(emptyGrid(layout.cols, layout.rows), ["HUD"]);

    expect(text).toHaveBeenLastCalledWith(
      "HUD",
      expect.closeTo(1143.5294117647),
      18.75,
      expect.closeTo(296.4705882353),
    );
  });
});
