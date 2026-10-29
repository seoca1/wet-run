/** P10 — accessibility modes: reduced-motion gate, colorblind palette, text scale.
 *
 * These are the pure-logic tests for the ADR-0236 surface. The wiring in
 * `main.ts` is NOT exercised here — `main.ts` self-boots on import and cannot
 * be imported under vitest's `node` environment (see ADR-0232 §"검증 한계").
 */
// @vitest-environment jsdom
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import {
  COLORBLIND_MODES,
  TEXT_SCALE_STEPS,
  TEXT_SCALE_FACTORS,
  isColorblindMode,
  nextColorblindMode,
  nextTextScale,
  textScaleFactor,
  suppressMotion,
  resolveReducedMotion,
  loadColorblindMode,
  persistColorblindMode,
  loadTextScale,
  persistTextScale,
  loadReducedMotionOverride,
  persistReducedMotionOverride,
  loadHighContrastOverride,
  persistHighContrastOverride,
  resolveHighContrast,
  COLORBLIND_STORAGE_KEY,
  TEXT_SCALE_STORAGE_KEY,
  REDUCED_MOTION_STORAGE_KEY,
  HIGH_CONTRAST_STORAGE_KEY,
  type ColorblindMode,
  type TextScaleStep,
  type MotionKind,
} from "../src/renderer/accessibility_modes.ts";

describe("COLORBLIND_MODES", () => {
  it("has the 4 ADR-0196 modes in ADR-0196 cycle order", () => {
    expect(COLORBLIND_MODES).toEqual([
      "none",
      "deuteranopia",
      "protanopia",
      "tritanopia",
    ]);
  });

  it("is frozen", () => {
    expect(Object.isFrozen(COLORBLIND_MODES)).toBe(true);
  });

  it("starts with the default mode", () => {
    expect(COLORBLIND_MODES[0]).toBe("none");
  });
});

describe("isColorblindMode", () => {
  it("accepts all 4 modes", () => {
    for (const mode of COLORBLIND_MODES) {
      expect(isColorblindMode(mode)).toBe(true);
    }
  });

  it("rejects unknown values", () => {
    expect(isColorblindMode("nonexistent")).toBe(false);
    expect(isColorblindMode("")).toBe(false);
    expect(isColorblindMode("DEUTERANOPIA")).toBe(false);
  });
});

describe("nextColorblindMode", () => {
  it("cycles none → deuteranopia → protanopia → tritanopia → none", () => {
    expect(nextColorblindMode("none")).toBe("deuteranopia");
    expect(nextColorblindMode("deuteranopia")).toBe("protanopia");
    expect(nextColorblindMode("protanopia")).toBe("tritanopia");
    expect(nextColorblindMode("tritanopia")).toBe("none");
  });

  it("returns to the starting mode after 4 steps", () => {
    let mode: ColorblindMode = "none";
    for (let i = 0; i < 4; i++) mode = nextColorblindMode(mode);
    expect(mode).toBe("none");
  });
});

describe("TEXT_SCALE_STEPS / TEXT_SCALE_FACTORS", () => {
  it("has small / medium / large in ascending order", () => {
    expect(TEXT_SCALE_STEPS).toEqual(["small", "medium", "large"]);
  });

  it("defaults to medium = 1.0 (no visual change)", () => {
    expect(TEXT_SCALE_FACTORS.medium).toBe(1.0);
  });

  it("small is below 1.0 and large is above 1.0", () => {
    expect(TEXT_SCALE_FACTORS.small).toBeLessThan(1.0);
    expect(TEXT_SCALE_FACTORS.large).toBeGreaterThan(1.0);
  });

  it("is frozen", () => {
    expect(Object.isFrozen(TEXT_SCALE_STEPS)).toBe(true);
    expect(Object.isFrozen(TEXT_SCALE_FACTORS)).toBe(true);
  });
});

describe("textScaleFactor", () => {
  it("returns the factor for each step", () => {
    expect(textScaleFactor("small")).toBe(TEXT_SCALE_FACTORS.small);
    expect(textScaleFactor("medium")).toBe(1.0);
    expect(textScaleFactor("large")).toBe(TEXT_SCALE_FACTORS.large);
  });
});

describe("nextTextScale", () => {
  it("cycles small → medium → large → small", () => {
    expect(nextTextScale("small")).toBe("medium");
    expect(nextTextScale("medium")).toBe("large");
    expect(nextTextScale("large")).toBe("small");
  });
});

describe("suppressMotion", () => {
  const KINDS: ReadonlyArray<MotionKind> = [
    "shake",
    "hit_stop",
    "flash",
    "floating_damage",
  ];

  it("suppresses nothing when reduced motion is off", () => {
    for (const kind of KINDS) {
      expect(suppressMotion(kind, false)).toBe(false);
    }
  });

  it("suppresses every motion kind when reduced motion is on", () => {
    for (const kind of KINDS) {
      expect(suppressMotion(kind, true)).toBe(true);
    }
  });

  it("suppresses the P1 canvas shake", () => {
    expect(suppressMotion("shake", true)).toBe(true);
    expect(suppressMotion("shake", false)).toBe(false);
  });

  it("suppresses the hit-stop hold", () => {
    expect(suppressMotion("hit_stop", true)).toBe(true);
    expect(suppressMotion("hit_stop", false)).toBe(false);
  });
});

describe("resolveReducedMotion", () => {
  let originalMatchMedia: typeof window.matchMedia | undefined;

  beforeEach(() => {
    originalMatchMedia = window.matchMedia;
  });

  afterEach(() => {
    if (originalMatchMedia) window.matchMedia = originalMatchMedia;
  });

  it("returns the explicit override when it is set", () => {
    expect(resolveReducedMotion(true)).toBe(true);
    expect(resolveReducedMotion(false)).toBe(false);
  });

  it("falls back to prefersReducedMotion() when the override is null", () => {
    window.matchMedia = ((query: string) => ({
      matches: query === "(prefers-reduced-motion: reduce)",
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => true,
    })) as typeof window.matchMedia;
    expect(resolveReducedMotion(null)).toBe(true);
  });

  it("the override beats the media query", () => {
    window.matchMedia = ((query: string) => ({
      matches: query === "(prefers-reduced-motion: reduce)",
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => true,
    })) as typeof window.matchMedia;
    // OS says reduce, but the player explicitly turned it OFF.
    expect(resolveReducedMotion(false)).toBe(false);
  });
});

describe("persistence", () => {
  const keys = [
    COLORBLIND_STORAGE_KEY,
    TEXT_SCALE_STORAGE_KEY,
    REDUCED_MOTION_STORAGE_KEY,
    HIGH_CONTRAST_STORAGE_KEY,
  ];

  beforeEach(() => {
    for (const key of keys) localStorage.removeItem(key);
  });

  afterEach(() => {
    for (const key of keys) localStorage.removeItem(key);
  });

  it("uses the wetrun_ key convention", () => {
    for (const key of keys) {
      expect(key.startsWith("wetrun_")).toBe(true);
    }
  });

  it("round-trips the colorblind mode", () => {
    expect(loadColorblindMode()).toBe("none");
    persistColorblindMode("protanopia");
    expect(loadColorblindMode()).toBe("protanopia");
    expect(localStorage.getItem(COLORBLIND_STORAGE_KEY)).toBe("protanopia");
  });

  it("rejects a malformed persisted colorblind mode", () => {
    localStorage.setItem(COLORBLIND_STORAGE_KEY, "bogus");
    expect(loadColorblindMode()).toBe("none");
  });

  it("round-trips the text scale", () => {
    expect(loadTextScale()).toBe("medium");
    persistTextScale("large");
    expect(loadTextScale()).toBe("large");
  });

  it("rejects a malformed persisted text scale", () => {
    localStorage.setItem(TEXT_SCALE_STORAGE_KEY, "huge");
    expect(loadTextScale()).toBe("medium");
  });

  it("round-trips the reduced-motion override", () => {
    expect(loadReducedMotionOverride()).toBeNull();
    persistReducedMotionOverride(true);
    expect(loadReducedMotionOverride()).toBe(true);
    persistReducedMotionOverride(false);
    expect(loadReducedMotionOverride()).toBe(false);
  });

  it("clears the reduced-motion override when persisted as null", () => {
    persistReducedMotionOverride(true);
    persistReducedMotionOverride(null);
    expect(loadReducedMotionOverride()).toBeNull();
  });

  it("round-trips the high-contrast override", () => {
    expect(loadHighContrastOverride()).toBeNull();
    persistHighContrastOverride(true);
    expect(loadHighContrastOverride()).toBe(true);
    persistHighContrastOverride(false);
    expect(loadHighContrastOverride()).toBe(false);
  });

  it("clears the high-contrast override when persisted as null", () => {
    persistHighContrastOverride(true);
    persistHighContrastOverride(null);
    expect(loadHighContrastOverride()).toBeNull();
  });
});

describe("resolveHighContrast", () => {
  it("returns the explicit override when it is set", () => {
    expect(resolveHighContrast(true)).toBe(true);
    expect(resolveHighContrast(false)).toBe(false);
  });

  it("falls back to the media query when the override is null", () => {
    const original = window.matchMedia;
    window.matchMedia = ((query: string) => ({
      matches: query === "(prefers-contrast: high)",
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => true,
    })) as typeof window.matchMedia;
    expect(resolveHighContrast(null)).toBe(true);
    window.matchMedia = original;
  });
});

describe("TextScaleStep type", () => {
  it("accepts the 3 steps", () => {
    const steps: ReadonlyArray<TextScaleStep> = ["small", "medium", "large"];
    expect(steps).toHaveLength(3);
  });
});
