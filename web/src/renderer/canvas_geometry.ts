/** Viewport-first presentation geometry (ADR-0237 §3–4). No DOM or game state. */
import type { Layout } from "../core/layout";

export interface CanvasViewport {
  readonly width: number;
  readonly height: number;
  readonly dpr: number;
}

export interface CanvasGeometry {
  readonly layout: Layout;
  readonly cssWidth: number;
  readonly cssHeight: number;
  readonly backingWidth: number;
  readonly backingHeight: number;
  readonly cellWidth: number;
  readonly cellHeight: number;
}

/** Invalid persisted/embedded scale values must not collapse the surface. */
export function sanitizeTextScale(scale: number): number {
  return Number.isFinite(scale) && scale > 0 ? scale : 1;
}

/** Preserve the breakpoint preset at 1× whenever its cells meet the 6×12 floor.
 * Larger text consumes more space, so fewer presentation cells fit. Distribute
 * columns between the grid and HUD in the original proportion; the HUD includes
 * its existing one-column gutter. Only a viewport smaller than one minimum cell
 * overflows (never shrink the font through CSS).
 */
export function canvasGeometry(
  base: Layout,
  viewport: CanvasViewport,
  textScale = 1,
): CanvasGeometry {
  const scale = sanitizeTextScale(textScale);
  const cssWidth = Math.max(12, viewport.width);
  const cssHeight = Math.max(12, viewport.height);
  const baseColumns = base.cols + base.hudCols;
  const totalColumns = Math.max(
    2,
    Math.min(Math.floor(baseColumns / scale), Math.floor(cssWidth / 6)),
  );
  const hudCols = Math.max(
    1,
    Math.round((totalColumns * base.hudCols) / baseColumns),
  );
  const rows = Math.max(
    1,
    Math.min(Math.floor(base.rows / scale), Math.floor(cssHeight / 12)),
  );
  const layout: Layout = {
    ...base,
    cols: totalColumns - hudCols,
    hudCols,
    rows,
  };
  const dpr =
    Number.isFinite(viewport.dpr) && viewport.dpr > 0 ? viewport.dpr : 1;
  return {
    layout,
    cssWidth,
    cssHeight,
    backingWidth: Math.round(cssWidth * dpr),
    backingHeight: Math.round(cssHeight * dpr),
    cellWidth: cssWidth / totalColumns,
    cellHeight: cssHeight / rows,
  };
}
