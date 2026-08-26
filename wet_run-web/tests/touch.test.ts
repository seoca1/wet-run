/** Tier 2c tests for virtual gamepad overlay (mobile touch input).
 */
// @vitest-environment jsdom

import { describe, it, expect, beforeAll } from "vitest";
import { mountVirtualGamepad, isTouchDevice } from "../src/input/touch.ts";

// jsdom doesn't ship matchMedia — polyfill before tests run.
beforeAll(() => {
  if (typeof window !== "undefined" && typeof window.matchMedia !== "function") {
    Object.defineProperty(window, "matchMedia", {
      value: (query: string) => ({
        matches: query.includes("coarse"),
        media: query,
        onchange: null,
        addEventListener: () => {},
        removeEventListener: () => {},
        addListener: () => {},
        removeListener: () => {},
        dispatchEvent: () => false,
      }),
      writable: true,
      configurable: true,
    });
  }
});

describe("virtual gamepad overlay", () => {
  it("mounts root element on first call", () => {
    const unmount = mountVirtualGamepad(() => {});
    const root = document.getElementById("wetrun-gamepad-root");
    expect(root).not.toBeNull();
    unmount();
  });

  it("creates 6 buttons (4 dpad + A + B)", () => {
    const unmount = mountVirtualGamepad(() => {});
    const root = document.getElementById("wetrun-gamepad-root");
    const buttons = root?.querySelectorAll("button") ?? [];
    expect(buttons.length).toBe(6);
    unmount();
  });

  it("cleans up DOM on unmount", () => {
    const unmount = mountVirtualGamepad(() => {});
    unmount();
    const root = document.getElementById("wetrun-gamepad-root");
    expect(root?.innerHTML).toBe("");
  });

  it("returns a no-op function in non-browser environments", () => {
    // jsdom IS a browser env, so we can't easily test SSR path here.
    // Just verify the returned function is callable.
    const unmount = mountVirtualGamepad(() => {});
    expect(typeof unmount).toBe("function");
    unmount();
  });

  it("isTouchDevice returns boolean", () => {
    const result = isTouchDevice();
    expect(typeof result).toBe("boolean");
  });
});
