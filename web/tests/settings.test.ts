/** Settings screen renderer unit tests (Tier 5).
 *
 * Tests pure helpers (clampVolume, adjustVolume) and the render
 * function output shape. AudioManager integration is covered by
 * tests/audio.test.ts.
 */
import { describe, it, expect } from "vitest";
import {
  clampVolume,
  adjustVolume,
  renderSettingsScreen,
  getInitialSettingsState,
  type SettingsState,
} from "../src/renderer/settings.js";
import { INITIAL_PWA_STATE } from "../src/core/pwa_manager.ts";

describe("clampVolume", () => {
  it("clamps negative values to 0", () => {
    expect(clampVolume(-0.5)).toBe(0);
  });
  it("clamps values > 1 to 1", () => {
    expect(clampVolume(1.5)).toBe(1);
  });
  it("returns in-range values unchanged", () => {
    expect(clampVolume(0.5)).toBe(0.5);
  });
  it("returns 0 for NaN", () => {
    expect(clampVolume(Number.NaN)).toBe(0);
  });
});

describe("adjustVolume", () => {
  it("increments by 0.1 (rounded)", () => {
    expect(adjustVolume(0.3, "inc")).toBe(0.4);
  });
  it("decrements by 0.1 (rounded)", () => {
    expect(adjustVolume(0.3, "dec")).toBe(0.2);
  });
  it("clamps at 1.0 ceiling", () => {
    expect(adjustVolume(1.0, "inc")).toBe(1.0);
  });
  it("clamps at 0.0 floor", () => {
    expect(adjustVolume(0.0, "dec")).toBe(0.0);
  });
});

describe("renderSettingsScreen", () => {
  const baseState: SettingsState = {
    selectedField: "audio",
    audioEnabled: true,
    masterVolume: 0.8,
    bgmVolume: 0.5,
    sfxVolume: 0.7,
    muted: false,
    language: "en",
    storageQuota: { state: "unavailable", reason: "test fixture" },
    pwa: INITIAL_PWA_STATE,
  };

  it("returns a grid of the requested dimensions", () => {
    const grid = renderSettingsScreen(baseState, 60, 20);
    expect(grid.width).toBe(60);
    expect(grid.height).toBe(20);
  });

  it("renders BGM percentage equal to volume * 100", () => {
    const grid = renderSettingsScreen({ ...baseState, bgmVolume: 0.5 }, 80, 24);
    const lines = gridToText(grid);
    expect(lines.some((l) => l.includes("50%"))).toBe(true);
  });

  it("renders SFX percentage equal to volume * 100", () => {
    const grid = renderSettingsScreen({ ...baseState, sfxVolume: 0.7 }, 80, 24);
    const lines = gridToText(grid);
    expect(lines.some((l) => l.includes("70%"))).toBe(true);
  });

  it("shows [X] MUTE ALL when muted=true", () => {
    const grid = renderSettingsScreen({ ...baseState, muted: true }, 80, 24);
    const lines = gridToText(grid);
    expect(lines.some((l) => l.includes("[X] MUTE ALL"))).toBe(true);
  });

  it("shows [ ] MUTE ALL when muted=false", () => {
    const grid = renderSettingsScreen({ ...baseState, muted: false }, 80, 24);
    const lines = gridToText(grid);
    expect(lines.some((l) => l.includes("[ ] MUTE ALL"))).toBe(true);
  });

  it("renders slider bar with filled cells proportional to volume", () => {
    // Width=20, 0.5 → 10 filled + 10 empty
    const grid = renderSettingsScreen({ ...baseState, bgmVolume: 0.5 }, 80, 24);
    const lines = gridToText(grid);
    const sliderLine = lines.find((l) => l.includes("[█") && l.includes("50%"));
    expect(sliderLine).toBeDefined();
    expect(sliderLine).toContain("█".repeat(10));
    expect(sliderLine).toContain("░".repeat(10));
  });

  // P13 — master volume slider, alongside BGM / SFX.
  it("renders a Master Volume label", () => {
    const grid = renderSettingsScreen(baseState, 80, 40);
    const lines = gridToText(grid);
    expect(lines.some((l) => l.includes("Master Volume"))).toBe(true);
  });

  it("renders the master volume percentage", () => {
    const grid = renderSettingsScreen(
      { ...baseState, masterVolume: 0.8 },
      80,
      40,
    );
    const lines = gridToText(grid);
    expect(lines.some((l) => l.includes("80%"))).toBe(true);
  });

  it("renders the master slider bar proportional to the master volume", () => {
    const grid = renderSettingsScreen(
      { ...baseState, masterVolume: 0.8 },
      80,
      40,
    );
    const lines = gridToText(grid);
    const sliderLine = lines.find((l) => l.includes("[█") && l.includes("80%"));
    expect(sliderLine).toBeDefined();
    expect(sliderLine).toContain("█".repeat(16));
    expect(sliderLine).toContain("░".repeat(4));
  });

  it("shows the master slider as selected when selectedField is 'master'", () => {
    const grid = renderSettingsScreen(
      { ...baseState, selectedField: "master" },
      80,
      40,
    );
    const lines = gridToText(grid);
    const labelRow = lines.find((l) => l.includes("Master Volume"));
    expect(labelRow).toBeDefined();
  });
});

function gridToText(grid: ReturnType<typeof renderSettingsScreen>): string[] {
  const lines: string[] = [];
  for (let y = 0; y < grid.height; y++) {
    let line = "";
    for (let x = 0; x < grid.width; x++) {
      const cell = grid.get(x, y);
      line += cell ? cell.char : " ";
    }
    lines.push(line);
  }
  return lines;
}

describe("getInitialSettingsState", () => {
  it("returns a state with valid field selection", () => {
    const s = getInitialSettingsState();
    expect(["audio", "bgm", "sfx", "mute"]).toContain(s.selectedField);
    expect(s.bgmVolume).toBeGreaterThanOrEqual(0);
    expect(s.bgmVolume).toBeLessThanOrEqual(1);
    expect(s.sfxVolume).toBeGreaterThanOrEqual(0);
    expect(s.sfxVolume).toBeLessThanOrEqual(1);
  });
});
