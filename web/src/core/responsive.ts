/** Responsive UI Manager — viewport detection, layout, touch/mouse.
 *
 * Handles mobile/desktop layout switching, virtual joystick for touch,
 * and viewport-aware canvas sizing.
 */

export type DeviceType = "mobile" | "tablet" | "desktop";

export interface ViewportSize {
  readonly width: number;
  readonly height: number;
}

export interface ResponsiveState {
  readonly device: DeviceType;
  readonly viewport: ViewportSize;
  readonly isTouch: boolean;
  readonly isPortrait: boolean;
  readonly scale: number;
}

/** Breakpoint thresholds. */
export const BREAKPOINTS = Object.freeze({
  mobile: 640,
  tablet: 1024,
  desktop: 1280,
});

/** Detect device type from viewport width. */
export function detectDevice(width: number): DeviceType {
  if (width < BREAKPOINTS.mobile) return "mobile";
  if (width < BREAKPOINTS.tablet) return "tablet";
  return "desktop";
}

/** Detect if touch is the primary input. */
export function detectTouch(): boolean {
  return "ontouchstart" in window || navigator.maxTouchPoints > 0;
}

/** Calculate canvas scale for device pixel ratio. */
export function calculateScale(): number {
  const dpr = window.devicePixelRatio || 1;
  return Math.min(dpr, 2);
}

/** Get viewport size from window. */
export function getViewport(): ViewportSize {
  return Object.freeze({ width: window.innerWidth, height: window.innerHeight });
}

/** Build responsive state from window. */
export function buildResponsiveState(): ResponsiveState {
  const viewport = getViewport();
  return Object.freeze({
    device: detectDevice(viewport.width),
    viewport,
    isTouch: detectTouch(),
    isPortrait: viewport.height > viewport.width,
    scale: calculateScale(),
  });
}

/** Check if virtual controls should show (mobile/touch). */
export function shouldShowVirtualControls(state: ResponsiveState): boolean {
  return state.isTouch && state.device === "mobile";
}

/** Get recommended canvas size for the viewport. */
export function getCanvasSize(state: ResponsiveState): ViewportSize {
  if (state.device === "mobile") {
    return Object.freeze({ width: state.viewport.width, height: Math.floor(state.viewport.width * 1.5) });
  }
  return Object.freeze({ width: 800, height: 600 });
}

/** Format viewport for display. */
export function formatViewport(vp: ViewportSize): string {
  return `${vp.width}×${vp.height}`;
}
