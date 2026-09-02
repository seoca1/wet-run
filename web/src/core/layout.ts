/** Responsive layout — single source of truth for grid sizing.
 *
 * Decides canvas + HUD dimensions based on viewport orientation + size.
 * Used by main.ts to build the grid and by canvas.ts to size the surface.
 *
 * Breakpoints (viewport width):
 * - < 360px (compact phones): portrait 32×50 + 12 HUD
 * - 360-480px (small phones): portrait 40×60 + 16 HUD
 * - 480-768px (tablets, large phones landscape): landscape 60×40 + 20 HUD
 * - 768-1024px (small desktop): landscape 80×50 + 24 HUD
 * - ≥ 1024px (large desktop): landscape 100×60 + 28 HUD
 */

export interface Layout {
  readonly cols: number;
  readonly rows: number;
  readonly hudCols: number;
  readonly orientation: "portrait" | "landscape";
  readonly breakpoint: "compact" | "small" | "medium" | "large" | "xlarge";
}

/** Width breakpoints */
const BREAKPOINTS = {
  COMPACT: 360,
  SMALL: 480,
  MEDIUM: 768,
  LARGE: 1024,
} as const;

function isPortraitViewport(): boolean {
  if (typeof window === "undefined") return false;
  if (typeof window.matchMedia === "function") {
    return window.matchMedia("(orientation: portrait)").matches;
  }
  return window.innerHeight > window.innerWidth;
}

/** Decide layout from current viewport. Pure-ish (reads window at call time). */
export function getLayout(): Layout {
  const portrait = isPortraitViewport();
  const width = typeof window !== "undefined" ? window.innerWidth : 1280;

  if (portrait) {
    if (width < BREAKPOINTS.COMPACT) {
      return { cols: 32, rows: 50, hudCols: 12, orientation: "portrait", breakpoint: "compact" };
    }
    if (width < BREAKPOINTS.SMALL) {
      return { cols: 40, rows: 60, hudCols: 16, orientation: "portrait", breakpoint: "small" };
    }
    return { cols: 50, rows: 80, hudCols: 20, orientation: "portrait", breakpoint: "medium" };
  }

  if (width < BREAKPOINTS.MEDIUM) {
    return { cols: 60, rows: 40, hudCols: 20, orientation: "landscape", breakpoint: "medium" };
  }
  if (width < BREAKPOINTS.LARGE) {
    return { cols: 80, rows: 50, hudCols: 24, orientation: "landscape", breakpoint: "large" };
  }
  return { cols: 100, rows: 60, hudCols: 28, orientation: "landscape", breakpoint: "xlarge" };
}

/** Subscribe to layout changes (resize + orientationchange). Returns cleanup fn.
 *
 * Invokes `onChange` whenever the layout category changes (orientation or
 * breakpoint). Callers should re-resize canvas and redraw.
 */
export function watchLayout(onChange: (layout: Layout) => void): () => void {
  if (typeof window === "undefined") return () => {};
  let last: Layout = getLayout();
  const handler = (): void => {
    const next = getLayout();
    if (next.orientation !== last.orientation || next.breakpoint !== last.breakpoint) {
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

/** Get CSS variables for layout-dependent styling. */
export function getLayoutVars(layout: Layout): Record<string, string> {
  const isPortrait = layout.orientation === "portrait";
  return {
    "--gamepad-area-top": isPortrait ? "60vh" : "70vh",
    "--gamepad-area-bottom": "5vh",
    "--gamepad-dpad-left": isPortrait ? "5vw" : "10vw",
    "--gamepad-dpad-right": isPortrait ? "95vw" : "85vw",
    "--gamepad-btn-left": isPortrait ? "5vw" : "10vw",
    "--gamepad-btn-right": isPortrait ? "95vw" : "85vw",
    "--hud-width": `${layout.hudCols * 8}px`,
    "--grid-width": `${layout.cols * 8}px`,
    "--grid-height": `${layout.rows * 16}px`,
  };
}