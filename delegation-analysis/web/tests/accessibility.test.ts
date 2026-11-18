/** Tests for accessibility module (WCAG compliance, ARIA, keyboard nav). */
// @vitest-environment jsdom

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import {
  DEFAULT_ACCESSIBILITY_STATE,
  prefersReducedMotion,
  prefersHighContrast,
  getMenuAriaLabel,
  getAriaLiveText,
  getKeyboardShortcuts,
  meetsContrastRatio,
  getHighContrastColors,
  formatScreenReaderText,
  type AccessibilityState,
  type ContrastMode,
} from "../src/core/accessibility.ts";

describe("DEFAULT_ACCESSIBILITY_STATE", () => {
  it("is frozen", () => {
    expect(Object.isFrozen(DEFAULT_ACCESSIBILITY_STATE)).toBe(true);
  });

  it("has correct default values", () => {
    expect(DEFAULT_ACCESSIBILITY_STATE.highContrast).toBe(false);
    expect(DEFAULT_ACCESSIBILITY_STATE.screenReaderMode).toBe(false);
    expect(DEFAULT_ACCESSIBILITY_STATE.keyboardNavigation).toBe(true);
    expect(DEFAULT_ACCESSIBILITY_STATE.reducedMotion).toBe(false);
  });
});

describe("prefersReducedMotion", () => {
  let originalMatchMedia: typeof window.matchMedia | undefined;

  beforeEach(() => {
    originalMatchMedia = window.matchMedia;
    window.matchMedia = window.matchMedia || ((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => true,
    }));
  });

  afterEach(() => {
    if (originalMatchMedia) {
      window.matchMedia = originalMatchMedia;
    }
  });

  it("returns false in test environment (default)", () => {
    expect(prefersReducedMotion()).toBe(false);
  });

  it("returns true when prefers-reduced-motion is set", () => {
    window.matchMedia = (query: string) => ({
      matches: query === "(prefers-reduced-motion: reduce)",
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => true,
    });
    expect(prefersReducedMotion()).toBe(true);
  });
});

describe("prefersHighContrast", () => {
  let originalMatchMedia: typeof window.matchMedia | undefined;

  beforeEach(() => {
    originalMatchMedia = window.matchMedia;
    window.matchMedia = window.matchMedia || ((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => true,
    }));
  });

  afterEach(() => {
    if (originalMatchMedia) {
      window.matchMedia = originalMatchMedia;
    }
  });

  it("returns false in test environment (default)", () => {
    expect(prefersHighContrast()).toBe(false);
  });

  it("returns true when prefers-contrast is high", () => {
    window.matchMedia = (query: string) => ({
      matches: query === "(prefers-contrast: high)",
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => true,
    });
    expect(prefersHighContrast()).toBe(true);
  });
});

describe("getMenuAriaLabel", () => {
  it("formats enabled item correctly", () => {
    expect(getMenuAriaLabel(0, "NEW RUN", true)).toBe("NEW RUN, option 1, enabled");
    expect(getMenuAriaLabel(2, "SETTINGS", true)).toBe("SETTINGS, option 3, enabled");
  });

  it("formats disabled item correctly", () => {
    expect(getMenuAriaLabel(1, "CONTINUE", false)).toBe("CONTINUE, option 2, disabled");
  });

  it("handles zero index", () => {
    expect(getMenuAriaLabel(0, "First", true)).toBe("First, option 1, enabled");
  });

  it("handles large index", () => {
    expect(getMenuAriaLabel(99, "Item", true)).toBe("Item, option 100, enabled");
  });
});

describe("getAriaLiveText", () => {
  it("formats damage event", () => {
    expect(getAriaLiveText("damage", 10)).toBe("Took 10 damage");
    expect(getAriaLiveText("damage", 0)).toBe("Took 0 damage");
  });

  it("formats heal event", () => {
    expect(getAriaLiveText("heal", 5)).toBe("Healed 5 HP");
    expect(getAriaLiveText("heal", 100)).toBe("Healed 100 HP");
  });

  it("formats victory event", () => {
    expect(getAriaLiveText("victory")).toBe("Victory!");
    expect(getAriaLiveText("victory", 0)).toBe("Victory!");
  });

  it("formats defeat event", () => {
    expect(getAriaLiveText("defeat")).toBe("Defeated");
  });

  it("formats levelup event", () => {
    expect(getAriaLiveText("levelup", 2)).toBe("Level up! Now level 2");
    expect(getAriaLiveText("levelup", 10)).toBe("Level up! Now level 10");
  });

  it("handles missing value with default 0", () => {
    expect(getAriaLiveText("damage")).toBe("Took 0 damage");
    expect(getAriaLiveText("heal")).toBe("Healed 0 HP");
  });

  it("returns empty string for unknown event", () => {
    expect(getAriaLiveText("unknown" as "damage")).toBe("");
  });
});

describe("getKeyboardShortcuts", () => {
  it("returns frozen array", () => {
    const shortcuts = getKeyboardShortcuts();
    expect(Object.isFrozen(shortcuts)).toBe(true);
  });

  it("contains expected shortcuts", () => {
    const shortcuts = getKeyboardShortcuts();
    expect(shortcuts.length).toBe(7);
    expect(shortcuts[0]).toEqual({ key: "Enter", action: "Confirm selection" });
    expect(shortcuts[1]).toEqual({ key: "Escape", action: "Cancel / Go back" });
    expect(shortcuts[2]).toEqual({ key: "ArrowUp/Down", action: "Navigate menu" });
    expect(shortcuts[3]).toEqual({ key: "ArrowLeft/Right", action: "Switch target" });
    expect(shortcuts[4]).toEqual({ key: "1-9", action: "Select program" });
    expect(shortcuts[5]).toEqual({ key: "Tab", action: "Switch target" });
    expect(shortcuts[6]).toEqual({ key: "Space", action: "Advance dialogue" });
  });

  it("each shortcut is frozen", () => {
    const shortcuts = getKeyboardShortcuts();
    shortcuts.forEach(shortcut => {
      expect(Object.isFrozen(shortcut)).toBe(true);
    });
  });
});

describe("meetsContrastRatio", () => {
  it("returns true for known good combinations (AA)", () => {
    expect(meetsContrastRatio("#00ff41", "#000000", "AA")).toBe(true);
    expect(meetsContrastRatio("#ffffff", "#000000", "AA")).toBe(true);
    expect(meetsContrastRatio("#000000", "#ffffff", "AA")).toBe(true);
  });

  it("returns true for known good combinations (AAA)", () => {
    expect(meetsContrastRatio("#00ff41", "#000000", "AAA")).toBe(true);
    expect(meetsContrastRatio("#ffffff", "#000000", "AAA")).toBe(true);
  });

  it("returns false for unknown combinations", () => {
    expect(meetsContrastRatio("#ff0000", "#ff00ff", "AA")).toBe(false);
    expect(meetsContrastRatio("#cccccc", "#dddddd", "AA")).toBe(false);
  });

  it("defaults to AA level", () => {
    expect(meetsContrastRatio("#00ff41", "#000000")).toBe(true);
  });

  it("handles case-sensitive color codes", () => {
    expect(meetsContrastRatio("#00FF41", "#000000")).toBe(false);
  });
});

describe("getHighContrastColors", () => {
  it("returns frozen object", () => {
    const colors = getHighContrastColors();
    expect(Object.isFrozen(colors)).toBe(true);
  });

  it("contains required color mappings", () => {
    const colors = getHighContrastColors();
    expect(colors.text).toBe("#ffffff");
    expect(colors.background).toBe("#000000");
    expect(colors.primary).toBe("#00ffff");
    expect(colors.secondary).toBe("#ffff00");
    expect(colors.success).toBe("#00ff00");
    expect(colors.error).toBe("#ff0000");
    expect(colors.warning).toBe("#ffff00");
  });

  it("has valid hex color values", () => {
    const colors = getHighContrastColors();
    const hexPattern = /^#[0-9a-f]{6}$/;
    Object.values(colors).forEach(color => {
      expect(hexPattern.test(color)).toBe(true);
    });
  });
});

describe("formatScreenReaderText", () => {
  it("returns frozen object with polite priority", () => {
    const result = formatScreenReaderText("Test message", "polite");
    expect(Object.isFrozen(result)).toBe(true);
    expect(result.text).toBe("Test message");
    expect(result.priority).toBe("polite");
  });

  it("returns frozen object with assertive priority", () => {
    const result = formatScreenReaderText("Urgent!", "assertive");
    expect(Object.isFrozen(result)).toBe(true);
    expect(result.text).toBe("Urgent!");
    expect(result.priority).toBe("assertive");
  });

  it("defaults to polite priority", () => {
    const result = formatScreenReaderText("Normal message");
    expect(result.priority).toBe("polite");
  });

  it("handles empty string", () => {
    const result = formatScreenReaderText("");
    expect(result.text).toBe("");
    expect(result.priority).toBe("polite");
  });

  it("handles long text", () => {
    const longText = "A".repeat(1000);
    const result = formatScreenReaderText(longText);
    expect(result.text).toBe(longText);
  });
});

describe("ContrastMode type", () => {
  it("accepts valid values", () => {
    const normal: ContrastMode = "normal";
    const high: ContrastMode = "high";
    expect(normal).toBe("normal");
    expect(high).toBe("high");
  });
});

describe("AccessibilityState type", () => {
  it("accepts valid state objects", () => {
    const state: AccessibilityState = {
      highContrast: true,
      screenReaderMode: false,
      keyboardNavigation: true,
      reducedMotion: false,
    };
    expect(state.highContrast).toBe(true);
  });
});
