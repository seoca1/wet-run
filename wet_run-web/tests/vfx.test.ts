import { describe, it, expect } from "vitest";
import { healthBar, healthColor, formatStatusLabel } from "../src/renderer/vfx.js";
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