import { describe, expect, it } from "vitest";
import type { Grid } from "../src/core/types";
import { makeGrid, setText } from "../src/core/grid";
import {
  SCREEN_FRAME_INSET,
  clipToInner,
  drawPanel,
  drawPanelSeparator,
  panelInnerRect,
  screenFrameRect,
  setInnerText,
  type PanelRect,
} from "../src/renderer/panel";
import {
  PALETTE,
  activeHighContrast,
  activePaletteMode,
  applyPaletteMode,
  paletteFor,
} from "../src/renderer/palette";

function lines(grid: Grid): string[] {
  return grid.cells.map((row) => row.map((cell) => cell.char).join(""));
}

describe("Green Grid panels", () => {
  it("draws all four borders when the frame is inset", () => {
    // Given
    const input = makeGrid(8, 6);
    const frame = { x: 1, y: 1, width: 6, height: 4 };
    // When
    const result = drawPanel(input, frame);
    // Then
    expect(lines(result.grid)).toEqual([
      "        ",
      " ╔════╗ ",
      " ║    ║ ",
      " ║    ║ ",
      " ╚════╝ ",
      "        ",
    ]);
    expect(result.inner).toEqual({ x: 2, y: 2, width: 4, height: 2 });
  });

  it("places the title in the top border when no status is supplied", () => {
    // Given
    const input = makeGrid(12, 3);
    // When
    const { grid } = drawPanel(
      input,
      { x: 0, y: 0, width: 12, height: 3 },
      { title: "DECK" },
    );
    // Then
    expect(lines(grid)[0]).toBe("╔═DECK═════╗");
    expect(grid.get(2, 0)).toEqual({
      char: "D",
      fg: PALETTE.GREEN_NEON,
      bg: PALETTE.BACKGROUND,
    });
  });

  it("right-aligns status when no title is supplied", () => {
    // Given
    const input = makeGrid(12, 3);
    // When
    const { grid } = drawPanel(
      input,
      { x: 0, y: 0, width: 12, height: 3 },
      { status: "OK" },
    );
    // Then
    expect(lines(grid)[0]).toBe("╔═══════OK═╗");
    expect(grid.get(8, 0)?.fg).toBe(PALETTE.GRAY_LIGHT);
  });

  it("truncates the title without colliding when status consumes header space", () => {
    // Given
    const input = makeGrid(12, 3);
    // When
    const { grid } = drawPanel(
      input,
      { x: 0, y: 0, width: 12, height: 3 },
      {
        title: "CONSTRUCT",
        status: "READY",
      },
    );
    // Then
    expect(lines(grid)[0]).toBe("╔═CO═READY═╗");
  });

  it("truncates status first when it is wider than the header", () => {
    // Given
    const input = makeGrid(8, 3);
    // When
    const { grid } = drawPanel(
      input,
      { x: 0, y: 0, width: 8, height: 3 },
      {
        title: "DECK",
        status: "SIGNAL",
      },
    );
    // Then
    expect(lines(grid)[0]).toBe("╔═SIGN═╗");
  });

  it("preserves the input, content and unrelated colours when drawing a border", () => {
    // Given
    const input = setText(
      makeGrid(8, 5, "#123456"),
      2,
      2,
      "ICE",
      PALETTE.FOREGROUND,
    );
    const original = lines(input);
    Object.freeze(input);
    input.cells.forEach(Object.freeze);
    Object.freeze(input.cells);
    // When
    const { grid } = drawPanel(input, { x: 1, y: 1, width: 6, height: 4 });
    // Then
    expect(lines(input)).toEqual(original);
    expect(grid).not.toBe(input);
    expect(grid.get(2, 2)).toEqual(input.get(2, 2));
    expect(grid.get(0, 0)).toEqual(input.get(0, 0));
    expect(grid.get(1, 1)).toEqual({
      char: "╔",
      fg: PALETTE.GREEN_NEON,
      bg: PALETTE.BACKGROUND,
    });
  });

  it.each([
    {
      frame: { x: -2, y: -1, width: 7, height: 5 },
      expected: ["    ║", "    ║", "    ║", "════╝"],
    },
    {
      frame: { x: 2, y: 1, width: 7, height: 5 },
      expected: ["     ", "  ╔══", "  ║  ", "  ║  "],
    },
    {
      frame: { x: -2, y: 0, width: 7, height: 4 },
      expected: ["════╗", "    ║", "    ║", "════╝"],
    },
    {
      frame: { x: 5, y: 4, width: 7, height: 5 },
      expected: ["     ", "     ", "     ", "     "],
    },
  ])(
    "crops original border positions when the frame is $frame",
    ({ frame, expected }) => {
      // Given
      const input = makeGrid(5, 4);
      // When
      const { grid } = drawPanel(input, frame);
      // Then
      expect(lines(grid)).toEqual(expected);
      expect(grid.cells.map((row) => row.length)).toEqual([5, 5, 5, 5]);
      expect(grid.get(-1, 0)).toBeNull();
      expect(grid.get(5, 0)).toBeNull();
    },
  );

  it("crops labels without reflow when their original start is outside the grid", () => {
    // Given
    const input = makeGrid(8, 3);
    // When
    const { grid } = drawPanel(
      input,
      { x: -4, y: 0, width: 12, height: 3 },
      { title: "DECK" },
    );
    // Then
    expect(lines(grid)[0]).toBe("CK═════╗");
  });

  it.each([
    [
      { x: 2, y: 1, width: 6, height: 5 },
      { x: 3, y: 2, width: 4, height: 3 },
    ],
    [
      { x: -3, y: -2, width: 8, height: 6 },
      { x: 0, y: 0, width: 4, height: 3 },
    ],
    [
      { x: 6, y: 4, width: 8, height: 6 },
      { x: 7, y: 5, width: 3, height: 1 },
    ],
    [
      { x: 20, y: 10, width: 8, height: 6 },
      { x: 10, y: 6, width: 0, height: 0 },
    ],
  ])("computes visible inner geometry for %o", (frame, expected) => {
    // Given
    const input = makeGrid(10, 6);
    // When
    const inner = panelInnerRect(input, frame);
    // Then
    expect(inner).toEqual(expected);
  });

  it.each([
    [0, 0],
    [0, 4],
    [4, 0],
    [1, 1],
    [1, 4],
    [4, 1],
    [-1, 4],
    [4, -1],
    [NaN, 4],
    [4, Infinity],
    [2.5, 4],
  ])("draws nothing when dimensions are %s by %s", (width, height) => {
    // Given
    const input = makeGrid(6, 5);
    // When
    const result = drawPanel(
      input,
      { x: 1, y: 1, width, height },
      { title: "DECK" },
    );
    // Then
    expect(result.grid).toBe(input);
    expect(result.inner.width * result.inner.height).toBe(0);
  });

  it.each([NaN, Infinity, 0.5])("rejects invalid origins when x is %s", (x) => {
    // Given
    const input = makeGrid(6, 5);
    // When
    const result = drawPanel(input, { x, y: 0, width: 5, height: 4 });
    // Then
    expect(result.grid).toBe(input);
    expect(result.inner).toEqual({ x: 0, y: 0, width: 0, height: 0 });
  });

  it.each([2, 3, 4])(
    "omits labels when a %s-column frame has no header space",
    (width) => {
      // Given
      const input = makeGrid(width, 2);
      // When
      const result = drawPanel(
        input,
        { x: 0, y: 0, width, height: 2 },
        {
          title: "DECK",
          status: "READY",
        },
      );
      // Then
      expect(lines(result.grid)).toEqual([
        `╔${"═".repeat(width - 2)}╗`,
        `╚${"═".repeat(width - 2)}╝`,
      ]);
      expect(result.inner).toEqual({ x: 1, y: 1, width: width - 2, height: 0 });
    },
  );

  it("returns empty content when the grid itself is empty", () => {
    // Given
    const input = makeGrid(0, 0);
    // When
    const result = drawPanel(input, { x: -1, y: -1, width: 5, height: 5 });
    // Then
    expect(lines(result.grid)).toEqual([]);
    expect(result.inner).toEqual({ x: 0, y: 0, width: 0, height: 0 });
  });

  it("produces the example frame when a separator divides its content", () => {
    // Given
    const frame: PanelRect = { x: 0, y: 0, width: 20, height: 5 };
    const panel = drawPanel(makeGrid(20, 5), frame, {
      title: "DECK",
      status: "READY",
    });
    const input = setText(panel.grid, panel.inner.x + 1, panel.inner.y, "ICE");
    // When
    const grid = drawPanelSeparator(input, frame, 2);
    // Then
    expect(lines(grid)).toEqual([
      "╔═DECK═══════READY═╗",
      "║ ICE              ║",
      "╠══════════════════╣",
      "║                  ║",
      "╚══════════════════╝",
    ]);
    expect(input.get(0, 2)?.char).toBe("║");
    expect(grid.get(0, 2)?.fg).toBe(PALETTE.GREEN_NEON);
  });

  it("clips the separator when both ends extend beyond the grid", () => {
    // Given
    const input = makeGrid(5, 3);
    // When
    const grid = drawPanelSeparator(
      input,
      { x: -2, y: 0, width: 9, height: 4 },
      1,
    );
    // Then
    expect(lines(grid)).toEqual(["     ", "═════", "     "]);
  });

  it.each([-1, 0, 3, 4, NaN, 1.5])(
    "preserves the frame when separator row %s is invalid",
    (y) => {
      // Given
      const frame = { x: 0, y: 0, width: 5, height: 4 };
      const { grid } = drawPanel(makeGrid(5, 4), frame);
      // When
      const result = drawPanelSeparator(grid, frame, y);
      // Then
      expect(result).toBe(grid);
    },
  );

  it.each(["deuteranopia", "none"] as const)(
    "reads current colours when mode is %s",
    (mode) => {
      // Given
      const previousMode = activePaletteMode();
      const previousContrast = activeHighContrast();
      const input = makeGrid(12, 3);
      applyPaletteMode(mode, mode === "none");
      const expected = paletteFor(mode, mode === "none");
      try {
        // When
        const { grid } = drawPanel(
          input,
          { x: 0, y: 0, width: 12, height: 3 },
          { status: "OK" },
        );
        // Then
        expect(grid.get(0, 0)).toEqual({
          char: "╔",
          fg: expected.GREEN_NEON,
          bg: expected.BACKGROUND,
        });
        expect(grid.get(8, 0)?.fg).toBe(expected.GRAY_LIGHT);
      } finally {
        applyPaletteMode(previousMode, previousContrast);
      }
    },
  );

  it("derives a one-cell inset screen frame from the grid size", () => {
    // Given
    const input = makeGrid(80, 50);
    // When
    const frame = screenFrameRect(input);
    // Then
    expect(SCREEN_FRAME_INSET).toBe(1);
    expect(frame).toEqual({ x: 1, y: 1, width: 78, height: 48 });
    expect(panelInnerRect(input, frame)).toEqual({
      x: 2,
      y: 2,
      width: 76,
      height: 46,
    });
  });

  it("leaves a blank gutter when the inset screen frame is drawn", () => {
    // Given
    const input = makeGrid(8, 6);
    // When
    const { grid } = drawPanel(input, screenFrameRect(input));
    // Then
    expect(lines(grid)).toEqual([
      "        ",
      " ╔════╗ ",
      " ║    ║ ",
      " ║    ║ ",
      " ╚════╝ ",
      "        ",
    ]);
  });

  it.each([
    [
      { width: 2, height: 2 },
      { x: 1, y: 1, width: 0, height: 0 },
    ],
    [
      { width: 0, height: 0 },
      { x: 1, y: 1, width: 0, height: 0 },
    ],
    [
      { width: 10, height: 6 },
      { x: 2, y: 2, width: 6, height: 2 },
    ],
  ])("clamps the inset frame for %o", (size, expected) => {
    // Given
    const inset = size.width === 10 ? 2 : SCREEN_FRAME_INSET;
    // When
    const frame = screenFrameRect(size, inset);
    // Then
    expect(frame).toEqual(expected);
  });

  it("draws nothing when the grid is too small for an inset frame", () => {
    // Given
    const input = makeGrid(3, 3);
    // When
    const result = drawPanel(input, screenFrameRect(input));
    // Then
    expect(result.grid).toBe(input);
  });

  it.each([
    [2, "abcdef", "abcd"],
    [3, "ab", "ab"],
    [6, "abc", ""],
    [9, "abc", ""],
  ])(
    "clips text from column %s to the inner rectangle",
    (x, text, expected) => {
      // Given
      const inner: PanelRect = { x: 2, y: 2, width: 4, height: 1 };
      // When
      const clipped = clipToInner(inner, x, text);
      // Then
      expect(clipped).toBe(expected);
    },
  );

  it("writes text only inside the inner rectangle", () => {
    // Given
    const input = makeGrid(8, 4);
    const inner: PanelRect = { x: 2, y: 1, width: 4, height: 2 };
    // When
    let grid = setInnerText(input, inner, 3, 1, "LONGTEXT", PALETTE.CYAN_LIGHT);
    grid = setInnerText(grid, inner, 2, 0, "ABOVE");
    grid = setInnerText(grid, inner, 2, 3, "BELOW");
    // Then
    expect(lines(grid)).toEqual([
      "        ",
      "   LON  ",
      "        ",
      "        ",
    ]);
    expect(grid.get(3, 1)?.fg).toBe(PALETTE.CYAN_LIGHT);
    expect(lines(input)).toEqual([
      "        ",
      "        ",
      "        ",
      "        ",
    ]);
  });
});
