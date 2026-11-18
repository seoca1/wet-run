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

/** jsdom does not implement HTMLCanvasElement.getContext. Provide a class-based
 * stub with explicit field-backed accessor to record every fillStyle set. */
function makeCanvas(width = 200, height = 200): { canvas: HTMLCanvasElement; fills: string[] } {
  const fills: string[] = [];
  let currentFillStyle = "";
  class FakeCtx {
    font = "";
    _textBaseline = "";
    _fillStyle = "";
    fillRect = (): void => {};
    fillText = (): void => {};
    setTransform = (): void => {};
    get textBaseline(): string { return this._textBaseline; }
    set textBaseline(v: string) { this._textBaseline = v; }
    get fillStyle(): string { return currentFillStyle; }
    set fillStyle(v: string) {
      currentFillStyle = v;
      fills.push(v);
    }
  }
  const ctx = new FakeCtx();
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  vi.spyOn(canvas, "getContext").mockReturnValue(ctx as unknown as CanvasRenderingContext2D);
  return { canvas, fills };
}

function hudColors(fills: ReadonlyArray<string>, hudLineCount: number): string[] {
  return fills.slice(-hudLineCount);
}

describe("AsciiRenderer hudColorFor (alarm 100% visual cue)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders all HUD lines with default GREEN_NEON when no colorFor is passed", () => {
    const { canvas, fills } = makeCanvas();
    const renderer = new AsciiRenderer(canvas);
    const lines = ["WET", "LVE: 01", "HP: 50/100", "ALM: 25%"];
    renderer.render(emptyGrid(), lines);
    const hud = hudColors(fills, lines.length);
    expect(hud.length).toBe(lines.length);
    for (const color of hud) {
      expect(color).toBe(PALETTE.GREEN_NEON);
    }
  });

  it("colors alarm line red when alarm is 100 (CRITICAL)", () => {
    const { canvas, fills } = makeCanvas();
    const renderer = new AsciiRenderer(canvas);
    const lines = ["WET", "HP: 80/100", "ALM: 100%"];
    const colorFor = (line: string): string | undefined => {
      if (!line.startsWith("ALM:")) return undefined;
      if (line.includes("100%")) return PALETTE.RED_BRIGHT;
      return PALETTE.YELLOW_AMBER;
    };
    renderer.render(emptyGrid(), lines, colorFor);
    const hud = hudColors(fills, lines.length);
    expect(hud[0]).toBe(PALETTE.GREEN_NEON);
    expect(hud[1]).toBe(PALETTE.GREEN_NEON);
    expect(hud[2]).toBe(PALETTE.RED_BRIGHT);
  });

  it("colors alarm line amber (YELLOW_AMBER) at 75-99% range", () => {
    const { canvas, fills } = makeCanvas();
    const renderer = new AsciiRenderer(canvas);
    const lines = ["WET", "ALM: 80%"];
    const colorFor = (line: string): string | undefined => {
      if (!line.startsWith("ALM:")) return undefined;
      return PALETTE.YELLOW_AMBER;
    };
    renderer.render(emptyGrid(), lines, colorFor);
    const hud = hudColors(fills, lines.length);
    expect(hud[0]).toBe(PALETTE.GREEN_NEON);
    expect(hud[1]).toBe(PALETTE.YELLOW_AMBER);
  });

  it("leaves non-alarm lines at default GREEN_NEON when colorFor returns undefined", () => {
    const { canvas, fills } = makeCanvas();
    const renderer = new AsciiRenderer(canvas);
    const lines = ["WET", "HP: 50/100"];
    const colorFor = (): string | undefined => undefined;
    renderer.render(emptyGrid(), lines, colorFor);
    const hud = hudColors(fills, lines.length);
    for (const color of hud) {
      expect(color).toBe(PALETTE.GREEN_NEON);
    }
  });
});
