/** P10 — ADR-0196 4-mode colorblind palette (pure palette data).
 *
 * The DEFAULT mode ("none") must be byte-identical to the pre-P10 palette —
 * that is the invariant that keeps every existing rendering test green.
 */
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import {
  PALETTE,
  PALETTE_VARIANTS,
  paletteFor,
  activePaletteMode,
  activeHighContrast,
  applyPaletteMode,
  resolveColorHint,
} from "../src/renderer/palette.ts";
import { COLORBLIND_MODES } from "../src/renderer/accessibility_modes.ts";
import { getHighContrastColors } from "../src/core/accessibility.ts";

/** The pre-P10 palette, spelled out so a regression is visible. */
const LEGACY_PALETTE: Readonly<Record<string, string>> = Object.freeze({
  BACKGROUND: "#000000",
  FOREGROUND: "#d0d0d0",
  GRAY_DARK: "#606060",
  GRAY_MID: "#909090",
  GRAY_LIGHT: "#c0c0c0",
  GRAY: "#808080",
  CYAN_LIGHT: "#00ffff",
  CYAN_DIM: "#00a0a0",
  GREEN_NEON: "#00ff41",
  GREEN_DIM: "#008020",
  RED_DEEP: "#a00020",
  RED_BRIGHT: "#ff2030",
  YELLOW_AMBER: "#ffa500",
  YELLOW: "#ffff00",
  MAGENTA_NEON: "#ff00ff",
  MAGENTA_LIGHT: "#ff80ff",
  BLUE_BRIGHT: "#4080ff",
  ICE_BLUE: "#4080ff",
  ALARM_RED: "#ff4040",
  PLAYER_CYAN: "#40ffff",
  HEAL_COLOR: "#80ff80",
  SHIELD_COLOR: "#a0e0ff",
  BUFF_COLOR: "#ffe080",
  DEBUFF_COLOR: "#e080ff",
  CRIT_COLOR: "#ffd700",
  DAMAGE_COLOR: "#ff8060",
  ICE_CYAN_DIM: "#00a0a0",
  ICE_FADE_PURPLE: "#a050c0",
  ICE_GREEN_BRIGHT: "#80ffa0",
  HIT_FLASH_COLOR: "#ffe0e0",
  ORANGE: "#ff8040",
  WARM: "#e0a060",
  OLIVE: "#a0a040",
  TIER_GOLD: "#ffd040",
  WHITE: "#ffffff",
});

describe("PALETTE (default mode) is unchanged", () => {
  it("every token matches the pre-P10 value byte-for-byte", () => {
    for (const [key, value] of Object.entries(LEGACY_PALETTE)) {
      expect((PALETTE as Readonly<Record<string, string>>)[key]).toBe(value);
    }
  });

  it("has exactly the legacy token set (no tokens added or removed)", () => {
    expect(Object.keys(PALETTE).sort()).toEqual(
      Object.keys(LEGACY_PALETTE).sort(),
    );
  });
});

describe("PALETTE_VARIANTS", () => {
  it("has an entry for every one of the 4 ADR-0196 modes", () => {
    for (const mode of COLORBLIND_MODES) {
      expect(PALETTE_VARIANTS[mode]).toBeDefined();
    }
  });

  it("the default mode's variant is empty (no overrides)", () => {
    expect(Object.keys(PALETTE_VARIANTS.none)).toHaveLength(0);
  });

  it("every non-default mode overrides at least one token", () => {
    for (const mode of COLORBLIND_MODES) {
      if (mode === "none") continue;
      expect(Object.keys(PALETTE_VARIANTS[mode]).length).toBeGreaterThan(0);
    }
  });

  it("every override targets a token that exists in PALETTE", () => {
    for (const mode of COLORBLIND_MODES) {
      for (const key of Object.keys(PALETTE_VARIANTS[mode])) {
        expect(key in PALETTE).toBe(true);
      }
    }
  });

  it("every override value is a valid lowercase hex colour", () => {
    const hexPattern = /^#[0-9a-f]{6}$/;
    for (const mode of COLORBLIND_MODES) {
      for (const value of Object.values(PALETTE_VARIANTS[mode])) {
        expect(hexPattern.test(value)).toBe(true);
      }
    }
  });

  it("is frozen", () => {
    expect(Object.isFrozen(PALETTE_VARIANTS)).toBe(true);
    for (const mode of COLORBLIND_MODES) {
      expect(Object.isFrozen(PALETTE_VARIANTS[mode])).toBe(true);
    }
  });
});

describe("paletteFor", () => {
  it("returns the default palette unchanged for the default mode", () => {
    const palette = paletteFor("none");
    for (const [key, value] of Object.entries(LEGACY_PALETTE)) {
      expect((palette as Readonly<Record<string, string>>)[key]).toBe(value);
    }
  });

  it("applies the mode's overrides on top of the default palette", () => {
    const palette = paletteFor("deuteranopia");
    const overrides = PALETTE_VARIANTS.deuteranopia;
    for (const [key, value] of Object.entries(overrides)) {
      expect((palette as Readonly<Record<string, string>>)[key]).toBe(value);
    }
  });

  it("keeps non-overridden tokens at their default values", () => {
    const palette = paletteFor("tritanopia");
    const overridden = new Set(Object.keys(PALETTE_VARIANTS.tritanopia));
    for (const [key, value] of Object.entries(LEGACY_PALETTE)) {
      if (overridden.has(key)) continue;
      expect((palette as Readonly<Record<string, string>>)[key]).toBe(value);
    }
  });

  it("is pure — repeated calls return equal palettes", () => {
    expect(paletteFor("protanopia")).toEqual(paletteFor("protanopia"));
  });

  it("the 3 colorblind modes differ from the default palette", () => {
    for (const mode of ["deuteranopia", "protanopia", "tritanopia"] as const) {
      expect(paletteFor(mode)).not.toEqual(paletteFor("none"));
    }
  });
});

describe("applyPaletteMode / activePaletteMode", () => {
  beforeEach(() => {
    applyPaletteMode("none");
  });

  afterEach(() => {
    applyPaletteMode("none");
  });

  it("defaults to the none mode", () => {
    expect(activePaletteMode()).toBe("none");
  });

  it("mutates the exported PALETTE so every renderer sees the mode", () => {
    applyPaletteMode("deuteranopia");
    const overrides = PALETTE_VARIANTS.deuteranopia;
    for (const [key, value] of Object.entries(overrides)) {
      expect((PALETTE as Readonly<Record<string, string>>)[key]).toBe(value);
    }
  });

  it("restores the byte-identical default palette", () => {
    applyPaletteMode("protanopia");
    applyPaletteMode("none");
    for (const [key, value] of Object.entries(LEGACY_PALETTE)) {
      expect((PALETTE as Readonly<Record<string, string>>)[key]).toBe(value);
    }
  });

  it("tracks the active mode", () => {
    applyPaletteMode("tritanopia");
    expect(activePaletteMode()).toBe("tritanopia");
    applyPaletteMode("none");
    expect(activePaletteMode()).toBe("none");
  });
});

describe("resolveColorHint follows the active palette", () => {
  beforeEach(() => {
    applyPaletteMode("none", false);
  });

  afterEach(() => {
    applyPaletteMode("none", false);
  });

  it("resolves against the default palette in the default mode", () => {
    expect(resolveColorHint("HEAL_COLOR")).toBe(PALETTE.HEAL_COLOR);
  });

  it("resolves against the active palette in a colorblind mode", () => {
    applyPaletteMode("deuteranopia");
    expect(resolveColorHint("HEAL_COLOR")).toBe(
      PALETTE_VARIANTS.deuteranopia.HEAL_COLOR,
    );
  });

  it("resolves against the active palette in high-contrast mode", () => {
    applyPaletteMode("none", true);
    expect(resolveColorHint("FOREGROUND")).toBe(
      getHighContrastColors().text,
    );
  });

  it("still falls back to FOREGROUND for an unknown hint", () => {
    applyPaletteMode("tritanopia");
    expect(resolveColorHint("NOT_A_TOKEN")).toBe(PALETTE.FOREGROUND);
  });
});

describe("high-contrast overrides", () => {
  beforeEach(() => {
    applyPaletteMode("none", false);
  });

  afterEach(() => {
    applyPaletteMode("none", false);
  });

  it("is off by default", () => {
    expect(activeHighContrast()).toBe(false);
  });

  it("paletteFor without high contrast equals the default palette", () => {
    expect(paletteFor("none", false)).toEqual(paletteFor("none"));
  });

  it("the high-contrast palette differs from the default palette", () => {
    expect(paletteFor("none", true)).not.toEqual(paletteFor("none", false));
  });

  it("uses the canonical getHighContrastColors() values", () => {
    const high = getHighContrastColors();
    const palette = paletteFor("none", true);
    expect(palette.FOREGROUND).toBe(high.text);
    expect(palette.BACKGROUND).toBe(high.background);
    expect(palette.CYAN_LIGHT).toBe(high.primary);
    expect(palette.GREEN_NEON).toBe(high.success);
    expect(palette.RED_BRIGHT).toBe(high.error);
  });

  it("the high-contrast overrides are applied to the exported PALETTE", () => {
    applyPaletteMode("none", true);
    expect(activeHighContrast()).toBe(true);
    expect(PALETTE.FOREGROUND).toBe(getHighContrastColors().text);
  });

  it("turning high contrast off restores the byte-identical default palette", () => {
    applyPaletteMode("none", true);
    applyPaletteMode("none", false);
    for (const [key, value] of Object.entries(LEGACY_PALETTE)) {
      expect((PALETTE as Readonly<Record<string, string>>)[key]).toBe(value);
    }
  });

  it("high contrast is applied on top of the colorblind overrides", () => {
    const both = paletteFor("deuteranopia", true);
    const colorblindOnly = paletteFor("deuteranopia", false);
    const highOnly = paletteFor("none", true);
    expect(both.FOREGROUND).toBe(highOnly.FOREGROUND);
    expect(both.GREEN_NEON).toBe(highOnly.GREEN_NEON);
    expect(both.GREEN_NEON).not.toBe(colorblindOnly.GREEN_NEON);
  });

  it("applies the high-contrast overrides when the mode is switched too", () => {
    applyPaletteMode("tritanopia", true);
    expect(PALETTE.FOREGROUND).toBe(getHighContrastColors().text);
    expect(activePaletteMode()).toBe("tritanopia");
    expect(activeHighContrast()).toBe(true);
  });
});
