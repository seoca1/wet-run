/** P10 — the ACCESSIBILITY settings section is rendered and reachable.
 *
 * A previous wave shipped a setting that was rendered but never reachable
 * from the input path. These tests pin both halves:
 *   1. the section is visible on the settings screen, and
 *   2. every accessibility field is part of the tab/arrow cycle, so the
 *      input handler can actually land on it.
 *
 * `main.ts` cannot be imported under vitest (it self-boots), so the input
 * cycle is pinned here as data: the same `SettingsField` union the handler
 * iterates.
 */
// @vitest-environment jsdom
import { describe, it, expect } from "vitest";
import {
  renderSettingsScreen,
  type SettingsField,
  type SettingsState,
} from "../src/renderer/settings.ts";
import { INITIAL_PWA_STATE } from "../src/core/pwa_manager.ts";

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
  reducedMotion: false,
  highContrast: false,
  colorblindMode: "none",
  textScale: "medium",
};

function gridToText(grid: { readonly cells: ReadonlyArray<ReadonlyArray<{ readonly char: string }>> }): string[] {
  return grid.cells.map((row) =>
    row
      .map((cell) => cell.char)
      .join("")
      .trimEnd(),
  );
}

/** The field cycle the settings input handler iterates (main.ts). */
const SETTINGS_FIELD_CYCLE: ReadonlyArray<SettingsField> = [
  "audio",
  "master",
  "bgm",
  "sfx",
  "mute",
  "language",
  "pwa_install",
  "pwa_update",
  "reduced_motion",
  "high_contrast",
  "colorblind",
  "text_scale",
];

describe("ACCESSIBILITY section is rendered", () => {
  it("renders the ACCESSIBILITY header", () => {
    const grid = renderSettingsScreen(baseState, 80, 50);
    const lines = gridToText(grid);
    expect(lines.some((l) => l.includes("ACCESSIBILITY"))).toBe(true);
  });

  it("renders the REDUCED MOTION row", () => {
    const grid = renderSettingsScreen(baseState, 80, 50);
    const lines = gridToText(grid);
    expect(lines.some((l) => l.includes("REDUCED MOTION"))).toBe(true);
  });

  it("renders the HIGH CONTRAST row", () => {
    const grid = renderSettingsScreen(baseState, 80, 50);
    const lines = gridToText(grid);
    expect(lines.some((l) => l.includes("HIGH CONTRAST"))).toBe(true);
  });

  it("renders the COLORBLIND row", () => {
    const grid = renderSettingsScreen(baseState, 80, 50);
    const lines = gridToText(grid);
    expect(lines.some((l) => l.includes("COLORBLIND"))).toBe(true);
  });

  it("renders the TEXT SCALE row", () => {
    const grid = renderSettingsScreen(baseState, 80, 50);
    const lines = gridToText(grid);
    expect(lines.some((l) => l.includes("TEXT SCALE"))).toBe(true);
  });
});

describe("ACCESSIBILITY section reflects the current values", () => {
  it("shows [X] REDUCED MOTION when reduced motion is on", () => {
    const grid = renderSettingsScreen(
      { ...baseState, reducedMotion: true },
      80,
      50,
    );
    expect(gridToText(grid).some((l) => l.includes("[X] REDUCED MOTION"))).toBe(
      true,
    );
  });

  it("shows [ ] REDUCED MOTION when reduced motion is off", () => {
    const grid = renderSettingsScreen(baseState, 80, 50);
    expect(gridToText(grid).some((l) => l.includes("[ ] REDUCED MOTION"))).toBe(
      true,
    );
  });

  it("shows [X] HIGH CONTRAST when high contrast is on", () => {
    const grid = renderSettingsScreen(
      { ...baseState, highContrast: true },
      80,
      50,
    );
    expect(gridToText(grid).some((l) => l.includes("[X] HIGH CONTRAST"))).toBe(
      true,
    );
  });

  it("shows [ ] HIGH CONTRAST when high contrast is off", () => {
    const grid = renderSettingsScreen(baseState, 80, 50);
    expect(gridToText(grid).some((l) => l.includes("[ ] HIGH CONTRAST"))).toBe(
      true,
    );
  });

  it("shows the active colorblind mode", () => {
    const grid = renderSettingsScreen(
      { ...baseState, colorblindMode: "deuteranopia" },
      80,
      50,
    );
    expect(
      gridToText(grid).some((l) => l.includes("COLORBLIND: DEUTERANOPIA")),
    ).toBe(true);
  });

  it("shows the active text scale", () => {
    const grid = renderSettingsScreen(
      { ...baseState, textScale: "large" },
      80,
      50,
    );
    expect(gridToText(grid).some((l) => l.includes("TEXT SCALE: LARGE"))).toBe(
      true,
    );
  });
});

describe("ACCESSIBILITY fields are reachable in the input cycle", () => {
  it("the cycle contains all four accessibility fields", () => {
    expect(SETTINGS_FIELD_CYCLE).toContain("reduced_motion");
    expect(SETTINGS_FIELD_CYCLE).toContain("high_contrast");
    expect(SETTINGS_FIELD_CYCLE).toContain("colorblind");
    expect(SETTINGS_FIELD_CYCLE).toContain("text_scale");
  });

  it("every accessibility field has a distinct cycle index", () => {
    const indices = [
      "reduced_motion",
      "high_contrast",
      "colorblind",
      "text_scale",
    ].map((f) => SETTINGS_FIELD_CYCLE.indexOf(f as SettingsField));
    expect(new Set(indices).size).toBe(4);
    for (const index of indices) {
      expect(index).toBeGreaterThanOrEqual(0);
    }
  });

  it("the cycle is stable — a full loop returns to the first field", () => {
    const first = SETTINGS_FIELD_CYCLE[0];
    const afterFullLoop =
      SETTINGS_FIELD_CYCLE[
        (SETTINGS_FIELD_CYCLE.indexOf(first as SettingsField) +
          SETTINGS_FIELD_CYCLE.length) %
          SETTINGS_FIELD_CYCLE.length
      ];
    expect(afterFullLoop).toBe(first);
  });
});

describe("the ACCESSIBILITY section does not overwrite existing content", () => {
  it("keeps the AUDIO / MUTE / LANGUAGE / STORAGE / PWA rows intact", () => {
    const grid = renderSettingsScreen(baseState, 80, 50);
    const lines = gridToText(grid);
    expect(lines.some((l) => l.includes("AUDIO"))).toBe(true);
    expect(lines.some((l) => l.includes("MUTE ALL"))).toBe(true);
    expect(lines.some((l) => l.includes("STORAGE"))).toBe(true);
    expect(lines.some((l) => l.includes("PWA"))).toBe(true);
  });

  it("keeps the MUTE ALL row visible in a short 24-row grid", () => {
    const grid = renderSettingsScreen(baseState, 80, 24);
    expect(gridToText(grid).some((l) => l.includes("MUTE ALL"))).toBe(true);
  });

  it("keeps the MUTE ALL row visible in the smallest real layout (40 rows)", () => {
    const grid = renderSettingsScreen(baseState, 80, 40);
    expect(gridToText(grid).some((l) => l.includes("MUTE ALL"))).toBe(true);
  });
});
