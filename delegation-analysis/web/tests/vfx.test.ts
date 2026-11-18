import { describe, it, expect } from "vitest";
import {
  healthBar,
  healthColor,
  formatStatusLabel,
  hitFlashColor,
  centerArt,
  formatStatusGlyph,
  STATUS_GLYPHS,
  ICE_DEFEAT_ART,
  PLAYER_DEFEAT_ART,
} from "../src/renderer/vfx.js";
import { PALETTE } from "../src/renderer/palette.js";

describe("healthBar", () => {
  it("renders full bar at 100%", () => {
    expect(healthBar(100, 100)).toBe("[████████████]");
  });

  it("renders empty bar at 0%", () => {
    expect(healthBar(0, 100)).toBe("[░░░░░░░░░░░░]");
  });

  it("renders half bar at 50%", () => {
    const bar = healthBar(50, 100);
    expect(bar.startsWith("[")).toBe(true);
    expect(bar.endsWith("]")).toBe(true);
    expect(bar.length).toBe(14);
    const filled = (bar.match(/█/g) ?? []).length;
    expect(filled).toBeGreaterThanOrEqual(5);
    expect(filled).toBeLessThanOrEqual(7);
  });

  it("clamps filled > total to full bar", () => {
    expect(healthBar(150, 100)).toBe("[████████████]");
  });

  it("clamps filled < 0 to empty bar", () => {
    expect(healthBar(-10, 100)).toBe("[░░░░░░░░░░░░]");
  });

  it("returns spaces for total = 0", () => {
    expect(healthBar(0, 0)).toBe("[            ]");
  });

  it("respects custom cell count", () => {
    expect(healthBar(50, 100, 4)).toBe("[██░░]");
  });
});

describe("healthColor", () => {
  it("returns GREEN_NEON above 60%", () => {
    expect(healthColor(70, 100)).toBe(PALETTE.GREEN_NEON);
  });

  it("returns YELLOW_AMBER between 30% and 60%", () => {
    expect(healthColor(50, 100)).toBe(PALETTE.YELLOW_AMBER);
    expect(healthColor(31, 100)).toBe(PALETTE.YELLOW_AMBER);
  });

  it("returns RED_BRIGHT below 30%", () => {
    expect(healthColor(20, 100)).toBe(PALETTE.RED_BRIGHT);
    expect(healthColor(0, 100)).toBe(PALETTE.RED_BRIGHT);
  });

  it("returns GRAY_LIGHT for total = 0", () => {
    expect(healthColor(0, 0)).toBe(PALETTE.GRAY_LIGHT);
  });
});

describe("formatStatusLabel", () => {
  it("returns victory label", () => {
    expect(formatStatusLabel("victory")).toBe("[ VICTORY ]");
  });

  it("returns defeat label", () => {
    expect(formatStatusLabel("defeat")).toBe("[ DEFEATED ]");
  });

  it("returns empty string for non-terminal phases", () => {
    expect(formatStatusLabel("menu")).toBe("");
    expect(formatStatusLabel("combat")).toBe("");
    expect(formatStatusLabel("approach")).toBe("");
    expect(formatStatusLabel("exit")).toBe("");
  });
});
describe("hitFlashColor", () => {
  it("returns RED_BRIGHT for damage taken", () => {
    expect(hitFlashColor(-10)).toBe(PALETTE.RED_BRIGHT);
    expect(hitFlashColor(-1)).toBe(PALETTE.RED_BRIGHT);
  });

  it("returns GREEN_NEON for heal", () => {
    expect(hitFlashColor(10)).toBe(PALETTE.GREEN_NEON);
    expect(hitFlashColor(1)).toBe(PALETTE.GREEN_NEON);
  });

  it("returns GRAY_LIGHT for no change", () => {
    expect(hitFlashColor(0)).toBe(PALETTE.GRAY_LIGHT);
  });
});

describe("ICE_DEFEAT_ART", () => {
  it("contains ICE OFFLINE label", () => {
    const joined = ICE_DEFEAT_ART.join("\n");
    expect(joined).toContain("ICE OFFLINE");
  });

  it("has at least 5 lines", () => {
    expect(ICE_DEFEAT_ART.length).toBeGreaterThanOrEqual(5);
  });
});

describe("PLAYER_DEFEAT_ART", () => {
  it("contains JACKED OUT label", () => {
    const joined = PLAYER_DEFEAT_ART.join("\n");
    expect(joined).toContain("JACKED OUT");
  });

  it("has at least 5 lines", () => {
    expect(PLAYER_DEFEAT_ART.length).toBeGreaterThanOrEqual(5);
  });
});

describe("centerArt", () => {
  it("pads short lines to width", () => {
    const art = ["hi"];
    const result = centerArt(art, 5);
    expect(result[0]).toBe(" hi  ");
  });

  it("truncates long lines to width", () => {
    const art = ["abcdef"];
    const result = centerArt(art, 3);
    expect(result[0]).toBe("abc");
  });

  it("preserves exact-width lines", () => {
    const art = ["abcd"];
    const result = centerArt(art, 4);
    expect(result[0]).toBe("abcd");
  });

  it("returns empty array for empty input", () => {
    expect(centerArt([], 10)).toEqual([]);
  });
});

describe("STATUS_GLYPHS", () => {
  it("exposes 5 glyph mappings", () => {
    expect(Object.keys(STATUS_GLYPHS).length).toBe(5);
  });

  it("maps each effect to a single letter", () => {
    expect(STATUS_GLYPHS.burn).toBe("B");
    expect(STATUS_GLYPHS.stun).toBe("S");
    expect(STATUS_GLYPHS.slow).toBe("L");
    expect(STATUS_GLYPHS.silence).toBe("M");
    expect(STATUS_GLYPHS.vulnerable).toBe("V");
  });
});

describe("formatStatusGlyph", () => {
  it("returns empty string for no effects", () => {
    expect(formatStatusGlyph([])).toBe("");
  });

  it("returns bracketed single glyph", () => {
    expect(formatStatusGlyph(["burn"])).toBe("[B]");
  });

  it("concatenates multiple glyphs in order", () => {
    expect(formatStatusGlyph(["burn", "stun"])).toBe("[BS]");
  });

  it("ignores unknown effects", () => {
    expect(formatStatusGlyph(["burn", "unknown_effect"])).toBe("[B]");
  });
});
