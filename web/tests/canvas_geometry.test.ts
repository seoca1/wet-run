import { describe, expect, it } from "vitest";
import { layoutForViewport } from "../src/core/layout";
import { canvasGeometry } from "../src/renderer/canvas_geometry";

describe("viewport-first canvas geometry", () => {
  it.each([
    [1440, 900],
    [390, 844],
  ] as const)(
    "fills %i×%i without changing the default breakpoint shape",
    (width, height) => {
      const base = layoutForViewport(width, height > width);

      const geometry = canvasGeometry(base, { width, height, dpr: 1 });

      expect(geometry.layout).toEqual(base);
      expect([geometry.cssWidth, geometry.cssHeight]).toEqual([width, height]);
      expect(geometry.cellWidth * (base.cols + base.hudCols)).toBeCloseTo(
        width,
      );
      expect(geometry.cellHeight * base.rows).toBeCloseTo(height);
    },
  );

  it.each([
    [1440, 900],
    [390, 844],
  ] as const)(
    "increases effective cell and glyph size at %i×%i when text scale increases",
    (width, height) => {
      const base = layoutForViewport(width, height > width);
      const viewport = { width, height, dpr: 2 };
      const medium = canvasGeometry(base, viewport);

      const large = canvasGeometry(base, viewport, 1.25);

      expect(large.cellWidth / medium.cellWidth).toBeGreaterThanOrEqual(1.25);
      expect(large.cellHeight / medium.cellHeight).toBeCloseTo(1.25);
      expect(large.layout.cols).toBeLessThan(medium.layout.cols);
      expect(large.layout.rows).toBeLessThan(medium.layout.rows);
      expect([large.cssWidth, large.cssHeight]).toEqual([width, height]);
    },
  );

  it.each([0.85, 1, 1.25])(
    "keeps cells at least 6×12 at scale %f on short screens",
    (scale) => {
      const base = layoutForViewport(844, false);

      const geometry = canvasGeometry(
        base,
        { width: 844, height: 390, dpr: 1 },
        scale,
      );

      expect(geometry.cellWidth).toBeGreaterThanOrEqual(6);
      expect(geometry.cellHeight).toBeGreaterThanOrEqual(12);
      expect(geometry.cssHeight).toBe(390);
    },
  );

  it.each([1, 1.25, 2, 3])(
    "changes only backing resolution at DPR %f",
    (dpr) => {
      const base = layoutForViewport(390, true);

      const geometry = canvasGeometry(base, { width: 390, height: 844, dpr });

      expect([geometry.cssWidth, geometry.cssHeight]).toEqual([390, 844]);
      expect([geometry.backingWidth, geometry.backingHeight]).toEqual([
        Math.round(390 * dpr),
        Math.round(844 * dpr),
      ]);
      expect(geometry.cellWidth).toBeCloseTo(390 / 56);
      expect(geometry.cellHeight).toBeCloseTo(844 / 60);
    },
  );

  it.each([0, -1, Number.NaN, Number.POSITIVE_INFINITY])(
    "uses default scale for %s",
    (scale) => {
      const base = layoutForViewport(1440, false);
      const viewport = { width: 1440, height: 900, dpr: 1 };

      const geometry = canvasGeometry(base, viewport, scale);

      expect(geometry).toEqual(canvasGeometry(base, viewport));
    },
  );
});
