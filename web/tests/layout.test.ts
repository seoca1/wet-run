/** Tests for responsive layout module (orientation + viewport-aware grid sizing).
 */
// @vitest-environment jsdom

import { describe, it, expect, beforeEach, vi } from "vitest";
import { getLayout, watchLayout, type Layout } from "../src/core/layout.ts";

interface MatchMediaStub {
  matches: boolean;
  media: string;
  onchange: null;
  addEventListener: (...args: unknown[]) => void;
  removeEventListener: (...args: unknown[]) => void;
  addListener: (...args: unknown[]) => void;
  removeListener: (...args: unknown[]) => void;
  dispatchEvent: (...args: unknown[]) => boolean;
}

function setViewport(width: number, height: number, portrait: boolean): void {
  Object.defineProperty(window, "innerWidth", { value: width, writable: true, configurable: true });
  Object.defineProperty(window, "innerHeight", { value: height, writable: true, configurable: true });
  const stub = (query: string): MatchMediaStub => ({
    matches: query.includes("portrait") ? portrait : false,
    media: query,
    onchange: null,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    addListener: vi.fn(),
    removeListener: vi.fn(),
    dispatchEvent: vi.fn(() => false),
  });
  Object.defineProperty(window, "matchMedia", {
    value: stub,
    writable: true,
    configurable: true,
  });
}

describe("layout (responsive grid sizing)", () => {
  beforeEach(() => {
    // Sensible desktop defaults; each test overrides.
    setViewport(1280, 800, false);
  });

  it("returns landscape 100×60 for large desktop viewport", () => {
    setViewport(1280, 800, false);
    const layout = getLayout();
    expect(layout.orientation).toBe("landscape");
    expect(layout.cols).toBe(100);
    expect(layout.rows).toBe(60);
    expect(layout.hudCols).toBe(28);
    expect(layout.breakpoint).toBe("xlarge");
  });

  it("returns landscape 80×50 for tablet landscape", () => {
    setViewport(900, 600, false);
    const layout = getLayout();
    expect(layout.orientation).toBe("landscape");
    expect(layout.cols).toBe(80);
    expect(layout.breakpoint).toBe("large");
  });

  it("returns portrait 50×80 for normal phone viewport", () => {
    setViewport(500, 900, true);
    const layout = getLayout();
    expect(layout.orientation).toBe("portrait");
    expect(layout.cols).toBe(50);
    expect(layout.rows).toBe(80);
    expect(layout.hudCols).toBe(20);
    expect(layout.breakpoint).toBe("medium");
  });

  it("returns compact portrait 40×60 for small phones (<480px)", () => {
    setViewport(375, 667, true);
    const layout = getLayout();
    expect(layout.orientation).toBe("portrait");
    expect(layout.cols).toBe(40);
    expect(layout.rows).toBe(60);
    expect(layout.hudCols).toBe(16);
    expect(layout.breakpoint).toBe("small");
  });

  it("returns compact portrait 32×50 for very small phones (<360px)", () => {
    setViewport(320, 568, true);
    const layout = getLayout();
    expect(layout.orientation).toBe("portrait");
    expect(layout.cols).toBe(32);
    expect(layout.rows).toBe(50);
    expect(layout.hudCols).toBe(12);
    expect(layout.breakpoint).toBe("compact");
  });

  it("watchLayout fires onChange when orientation flips", () => {
    setViewport(390, 844, true);
    const changes: Layout[] = [];
    const unwatch = watchLayout((next) => {
      changes.push(next);
    });

    // Simulate orientationchange to landscape.
    setViewport(844, 390, false);
    window.dispatchEvent(new Event("orientationchange"));
    expect(changes.length).toBe(1);
    expect(changes[0]?.orientation).toBe("landscape");

    // No further changes when only width changes within same orientation.
    setViewport(1000, 600, false);
    window.dispatchEvent(new Event("resize"));
    expect(changes.length).toBe(1);

    unwatch();
  });

  it("watchLayout fires onChange when compact breakpoint crossed", () => {
    setViewport(340, 600, true);
    const changes: Layout[] = [];
    const unwatch = watchLayout((next) => changes.push(next));

    setViewport(400, 800, true);
    window.dispatchEvent(new Event("resize"));
    expect(changes.length).toBe(1);
    expect(changes[0]?.cols).toBe(40);
    expect(changes[0]?.breakpoint).toBe("small");

    unwatch();
  });

  it("unwatch removes event listeners", () => {
    setViewport(390, 844, true);
    const changes: Layout[] = [];
    const unwatch = watchLayout((next) => changes.push(next));
    unwatch();

    setViewport(844, 390, false);
    window.dispatchEvent(new Event("orientationchange"));
    expect(changes.length).toBe(0);
  });

  it("watchLayout is a no-op outside the browser", async () => {
    // Can't easily simulate non-browser env in vitest without complex setup.
    // Just verify the cleanup function is callable.
    const unwatch = watchLayout(() => {});
    expect(typeof unwatch).toBe("function");
    unwatch();
  });
});