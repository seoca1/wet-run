/** Tests for responsive UI module (viewport detection, layout, touch/mouse).
 */
// @vitest-environment jsdom

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import {
  detectDevice,
  detectTouch,
  calculateScale,
  getViewport,
  buildResponsiveState,
  shouldShowVirtualControls,
  getCanvasSize,
  formatViewport,
  BREAKPOINTS,
  type ViewportSize,
  type ResponsiveState,
} from "../src/core/responsive.ts";

describe("detectDevice", () => {
  it("returns mobile for width < 640", () => {
    expect(detectDevice(320)).toBe("mobile");
    expect(detectDevice(639)).toBe("mobile");
  });

  it("returns tablet for width >= 640 and < 1024", () => {
    expect(detectDevice(640)).toBe("tablet");
    expect(detectDevice(768)).toBe("tablet");
    expect(detectDevice(1023)).toBe("tablet");
  });

  it("returns desktop for width >= 1024", () => {
    expect(detectDevice(1024)).toBe("desktop");
    expect(detectDevice(1280)).toBe("desktop");
    expect(detectDevice(1920)).toBe("desktop");
  });

  it("handles edge cases at breakpoints", () => {
    expect(detectDevice(BREAKPOINTS.mobile - 1)).toBe("mobile");
    expect(detectDevice(BREAKPOINTS.mobile)).toBe("tablet");
    expect(detectDevice(BREAKPOINTS.tablet - 1)).toBe("tablet");
    expect(detectDevice(BREAKPOINTS.tablet)).toBe("desktop");
  });
});

describe("detectTouch", () => {
  let originalOntouchstart: unknown;
  let originalMaxTouchPoints: number;

  beforeEach(() => {
    originalOntouchstart = (window as { ontouchstart?: unknown }).ontouchstart;
    originalMaxTouchPoints = navigator.maxTouchPoints;
  });

  afterEach(() => {
    if (originalOntouchstart === undefined) {
      delete (window as { ontouchstart?: unknown }).ontouchstart;
    } else {
      (window as { ontouchstart?: unknown }).ontouchstart = originalOntouchstart;
    }
    Object.defineProperty(navigator, "maxTouchPoints", {
      value: originalMaxTouchPoints,
      configurable: true,
    });
  });

  it("returns true when ontouchstart exists", () => {
    (window as { ontouchstart?: unknown }).ontouchstart = null;
    expect(detectTouch()).toBe(true);
  });

  it("returns true when maxTouchPoints > 0", () => {
    delete (window as { ontouchstart?: unknown }).ontouchstart;
    Object.defineProperty(navigator, "maxTouchPoints", {
      value: 5,
      configurable: true,
    });
    expect(detectTouch()).toBe(true);
  });

  it("returns false when neither touch indicator present", () => {
    delete (window as { ontouchstart?: unknown }).ontouchstart;
    Object.defineProperty(navigator, "maxTouchPoints", {
      value: 0,
      configurable: true,
    });
    expect(detectTouch()).toBe(false);
  });
});

describe("calculateScale", () => {
  let originalDpr: number;

  beforeEach(() => {
    originalDpr = window.devicePixelRatio;
  });

  afterEach(() => {
    Object.defineProperty(window, "devicePixelRatio", {
      value: originalDpr,
      configurable: true,
    });
  });

  it("returns 1 for devicePixelRatio = 1", () => {
    Object.defineProperty(window, "devicePixelRatio", {
      value: 1,
      configurable: true,
    });
    expect(calculateScale()).toBe(1);
  });

  it("returns 2 for devicePixelRatio = 2 (capped)", () => {
    Object.defineProperty(window, "devicePixelRatio", {
      value: 2,
      configurable: true,
    });
    expect(calculateScale()).toBe(2);
  });

  it("caps at 2 for devicePixelRatio = 3", () => {
    Object.defineProperty(window, "devicePixelRatio", {
      value: 3,
      configurable: true,
    });
    expect(calculateScale()).toBe(2);
  });

  it("handles fractional devicePixelRatio", () => {
    Object.defineProperty(window, "devicePixelRatio", {
      value: 1.5,
      configurable: true,
    });
    expect(calculateScale()).toBe(1.5);
  });

  it("defaults to 1 when devicePixelRatio is undefined", () => {
    Object.defineProperty(window, "devicePixelRatio", {
      value: undefined,
      configurable: true,
    });
    expect(calculateScale()).toBe(1);
  });
});

describe("getViewport", () => {
  it("returns window dimensions", () => {
    const viewport = getViewport();
    expect(viewport.width).toBe(window.innerWidth);
    expect(viewport.height).toBe(window.innerHeight);
  });

  it("returns frozen object", () => {
    const viewport = getViewport();
    expect(Object.isFrozen(viewport)).toBe(true);
  });
});

describe("buildResponsiveState", () => {
  it("returns complete ResponsiveState object", () => {
    const state = buildResponsiveState();
    expect(state).toHaveProperty("device");
    expect(state).toHaveProperty("viewport");
    expect(state).toHaveProperty("isTouch");
    expect(state).toHaveProperty("isPortrait");
    expect(state).toHaveProperty("scale");
  });

  it("detects portrait orientation when height > width", () => {
    Object.defineProperty(window, "innerWidth", {
      value: 600,
      configurable: true,
    });
    Object.defineProperty(window, "innerHeight", {
      value: 800,
      configurable: true,
    });
    const state = buildResponsiveState();
    expect(state.isPortrait).toBe(true);
  });

  it("detects landscape orientation when width > height", () => {
    Object.defineProperty(window, "innerWidth", {
      value: 1024,
      configurable: true,
    });
    Object.defineProperty(window, "innerHeight", {
      value: 768,
      configurable: true,
    });
    const state = buildResponsiveState();
    expect(state.isPortrait).toBe(false);
  });

  it("returns frozen state object", () => {
    const state = buildResponsiveState();
    expect(Object.isFrozen(state)).toBe(true);
  });
});

describe("shouldShowVirtualControls", () => {
  it("returns true for mobile + touch", () => {
    const state: ResponsiveState = {
      device: "mobile",
      viewport: { width: 375, height: 667 },
      isTouch: true,
      isPortrait: true,
      scale: 2,
    };
    expect(shouldShowVirtualControls(state)).toBe(true);
  });

  it("returns false for mobile + no touch", () => {
    const state: ResponsiveState = {
      device: "mobile",
      viewport: { width: 375, height: 667 },
      isTouch: false,
      isPortrait: true,
      scale: 1,
    };
    expect(shouldShowVirtualControls(state)).toBe(false);
  });

  it("returns false for tablet + touch", () => {
    const state: ResponsiveState = {
      device: "tablet",
      viewport: { width: 768, height: 1024 },
      isTouch: true,
      isPortrait: true,
      scale: 2,
    };
    expect(shouldShowVirtualControls(state)).toBe(false);
  });

  it("returns false for desktop + touch", () => {
    const state: ResponsiveState = {
      device: "desktop",
      viewport: { width: 1920, height: 1080 },
      isTouch: true,
      isPortrait: false,
      scale: 1,
    };
    expect(shouldShowVirtualControls(state)).toBe(false);
  });
});

describe("getCanvasSize", () => {
  it("returns viewport-based size for mobile (width x 1.5)", () => {
    const state: ResponsiveState = {
      device: "mobile",
      viewport: { width: 375, height: 667 },
      isTouch: true,
      isPortrait: true,
      scale: 2,
    };
    const size = getCanvasSize(state);
    expect(size.width).toBe(375);
    expect(size.height).toBe(Math.floor(375 * 1.5));
  });

  it("returns standard 800x600 for tablet", () => {
    const state: ResponsiveState = {
      device: "tablet",
      viewport: { width: 768, height: 1024 },
      isTouch: true,
      isPortrait: true,
      scale: 2,
    };
    const size = getCanvasSize(state);
    expect(size.width).toBe(800);
    expect(size.height).toBe(600);
  });

  it("returns standard 800x600 for desktop", () => {
    const state: ResponsiveState = {
      device: "desktop",
      viewport: { width: 1920, height: 1080 },
      isTouch: false,
      isPortrait: false,
      scale: 1,
    };
    const size = getCanvasSize(state);
    expect(size.width).toBe(800);
    expect(size.height).toBe(600);
  });

  it("returns frozen ViewportSize object", () => {
    const state: ResponsiveState = {
      device: "mobile",
      viewport: { width: 375, height: 667 },
      isTouch: true,
      isPortrait: true,
      scale: 2,
    };
    const size = getCanvasSize(state);
    expect(Object.isFrozen(size)).toBe(true);
  });
});

describe("formatViewport", () => {
  it("formats viewport with × separator", () => {
    const vp: ViewportSize = { width: 1920, height: 1080 };
    expect(formatViewport(vp)).toBe("1920×1080");
  });

  it("formats mobile viewport", () => {
    const vp: ViewportSize = { width: 375, height: 667 };
    expect(formatViewport(vp)).toBe("375×667");
  });

  it("formats square viewport", () => {
    const vp: ViewportSize = { width: 1024, height: 1024 };
    expect(formatViewport(vp)).toBe("1024×1024");
  });
});

describe("BREAKPOINTS", () => {
  it("is frozen", () => {
    expect(Object.isFrozen(BREAKPOINTS)).toBe(true);
  });

  it("has expected values", () => {
    expect(BREAKPOINTS.mobile).toBe(640);
    expect(BREAKPOINTS.tablet).toBe(1024);
    expect(BREAKPOINTS.desktop).toBe(1280);
  });
});
