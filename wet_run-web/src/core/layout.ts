/** Responsive layout — single source of truth for grid sizing.
 *
 * Decides canvas + HUD dimensions based on viewport orientation + size.
 * Used by main.ts to build the grid and by canvas.ts to size the surface.
 *
 * Two presets:
 * - Landscape: 80 cols × 50 rows + 28-col HUD on the right (current desktop).
 * - Portrait:  50 cols × 80 rows + 20-col HUD on the right (vertical phones).
 *
 * Breakpoints (viewport width):
 * - < 480px (compact phones): portrait 40×60 + 16 HUD
 * - 480-768px (tablets, large phones landscape): landscape 80×50 + 28 HUD
 * - ≥ 768px (desktop): landscape 80×50 + 28 HUD
 */

export interface Layout {
  readonly cols: number;
  readonly rows: number;
  readonly hudCols: number;
  readonly orientation: "portrait" | "landscape";
}

/** Width breakpoint below which we use compact portrait layout. */
const COMPACT_WIDTH = 480;

function isPortraitViewport(): boolean {
  if (typeof window === "undefined") return false;
  // matchMedia is the canonical API; falls back to aspect ratio for older browsers.
  if (typeof window.matchMedia === "function") {
    return window.matchMedia("(orientation: portrait)").matches;
  }
  return window.innerHeight > window.innerWidth;
}

/** Decide layout from current viewport. Pure-ish (reads window at call time). */
export function getLayout(): Layout {
  const portrait = isPortraitViewport();
  const width = typeof window !== "undefined" ? window.innerWidth : 1280;
  const compact = width < COMPACT_WIDTH;
  if (portrait && compact) {
    return { cols: 40, rows: 60, hudCols: 16, orientation: "portrait" };
  }
  if (portrait) {
    return { cols: 50, rows: 80, hudCols: 20, orientation: "portrait" };
  }
  return { cols: 80, rows: 50, hudCols: 28, orientation: "landscape" };
}

/** Subscribe to layout changes (resize + orientationchange). Returns cleanup fn.
 *
 * Invokes `onChange` whenever the layout category changes (orientation or
 * compact breakpoint). Callers should re-resize canvas and redraw.
 */
export function watchLayout(onChange: (layout: Layout) => void): () => void {
  if (typeof window === "undefined") return () => {};
  let last: Layout = getLayout();
  const handler = (): void => {
    const next = getLayout();
    if (next.orientation !== last.orientation) {
      last = next;
      onChange(next);
      return;
    }
    if (next.cols !== last.cols || next.rows !== last.rows || next.hudCols !== last.hudCols) {
      last = next;
      onChange(next);
    }
  };
  window.addEventListener("resize", handler);
  window.addEventListener("orientationchange", handler);
  return () => {
    window.removeEventListener("resize", handler);
    window.removeEventListener("orientationchange", handler);
  };
}