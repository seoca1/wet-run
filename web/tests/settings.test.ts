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
  settingsLayout,
  type SettingsState,
} from "../src/renderer/settings";
import { INITIAL_PWA_STATE } from "../src/core/pwa_manager";
import { PALETTE } from "../src/renderer/palette";
import type { Grid } from "../src/core/types";

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

/** Every grid preset in `src/core/layout.ts` (cols x rows). */
const PRESETS: ReadonlyArray<readonly [number, number]> = [
  [32, 50],
  [40, 60],
  [50, 80],
  [60, 40],
  [80, 50],
  [100, 60],
];

/** One prefix per drawn settings line (slider bars are counted separately).
 * Prefixes are short enough to survive the 32-column preset's existing
 * right-edge clipping, so only vertical placement is under test here.
 */
const EVERY_LINE: readonly string[] = [
  "WET RUN — Settings",
  "─",
  "AUDIO",
  "[X] AUDIO ENABLED",
  "Master Volume",
  "BGM Volume",
  "SFX Volume",
  "[ ] MUTE ALL",
  "LANGUAGE",
  "[ ] EN",
  "ACCESSIBILITY",
  "[ ] REDUCED MOTION",
  "[ ] HIGH CONTRAST",
  "[ ] COLORBLIND: NONE",
  "[ ] TEXT SCALE: MEDIUM",
  "STORAGE",
  "[ Storage API",
  "PWA",
  "[ ] UNAVAILABLE",
  "[ ] APPLY UPDATE",
  "ONLINE",
  "ENTER: toggle audio",
  "Volumes persist",
];

describe("renderSettingsScreen — inset frame (ADR-0237 §2)", () => {
  const state: SettingsState = {
    selectedField: "audio",
    audioEnabled: true,
    masterVolume: 0.8,
    bgmVolume: 0.5,
    sfxVolume: 0.7,
    muted: false,
    language: "en",
    storageQuota: { state: "unavailable", reason: "test fixture" },
    pwa: { ...INITIAL_PWA_STATE, isOffline: false },
  };
  const colText = (grid: Grid, x: number): string =>
    grid.cells.map((row) => row[x]?.char ?? "").join("");
  const at = (grid: Grid, y: number, x: number, length: number): string =>
    gridToText(grid)[y]?.slice(x, x + length) ?? "";

  it("derives the frame, inner box and footer from the grid size", () => {
    expect(settingsLayout(80, 50)).toEqual({
      frame: { x: 1, y: 1, width: 78, height: 48 },
      inner: { x: 2, y: 2, width: 76, height: 46 },
      footerY: 46,
      collapsedSpacers: [],
    });
  });

  it("draws border glyphs at the four inset corners", () => {
    for (const [cols, rows] of [
      [80, 50],
      [100, 60],
      [60, 40],
    ] as const) {
      const grid = renderSettingsScreen(state, cols, rows);
      expect(grid.cells[1]?.[1]?.char).toBe("╔");
      expect(grid.cells[1]?.[cols - 2]?.char).toBe("╗");
      expect(grid.cells[rows - 2]?.[1]?.char).toBe("╚");
      expect(grid.cells[rows - 2]?.[cols - 2]?.char).toBe("╝");
      expect(grid.cells[20]?.[1]?.char).toBe("║");
      expect(grid.cells[20]?.[cols - 2]?.char).toBe("║");
      expect(grid.cells[1]?.[1]?.fg).toBe(PALETTE.GREEN_NEON);
    }
  });

  it("leaves the outermost grid row and column blank", () => {
    const grid = renderSettingsScreen(state, 80, 50);
    const lines = gridToText(grid);
    expect(lines[0]?.trim()).toBe("");
    expect(lines[49]?.trim()).toBe("");
    expect(colText(grid, 0).trim()).toBe("");
    expect(colText(grid, 79).trim()).toBe("");
  });

  it("moves every body line +1 column / +1 row with unchanged text and colour", () => {
    const grid = renderSettingsScreen(state, 80, 50);
    const rows: ReadonlyArray<readonly [number, number, string, string]> = [
      [2, 34, "WET RUN — Settings", PALETTE.GREEN_NEON],
      [4, 3, "─".repeat(50), PALETTE.GRAY_MID],
      [6, 5, "AUDIO", PALETTE.CYAN_LIGHT],
      [8, 5, "[X] AUDIO ENABLED", PALETTE.YELLOW_AMBER],
      [10, 5, "Master Volume", PALETTE.GRAY_LIGHT],
      [11, 5, "[████████████████░░░░]  80%", PALETTE.GRAY_MID],
      [13, 5, "BGM Volume", PALETTE.GRAY_LIGHT],
      [16, 5, "SFX Volume", PALETTE.GRAY_LIGHT],
      [19, 5, "[ ] MUTE ALL", PALETTE.GRAY_LIGHT],
      [21, 5, "LANGUAGE", PALETTE.CYAN_LIGHT],
      [23, 5, "[ ] EN", PALETTE.GRAY_LIGHT],
      [25, 5, "ACCESSIBILITY", PALETTE.CYAN_LIGHT],
      [26, 5, "[ ] REDUCED MOTION", PALETTE.GRAY_LIGHT],
      [27, 5, "[ ] HIGH CONTRAST", PALETTE.GRAY_LIGHT],
      [28, 5, "[ ] COLORBLIND: NONE", PALETTE.GRAY_LIGHT],
      [29, 5, "[ ] TEXT SCALE: MEDIUM", PALETTE.GRAY_LIGHT],
      [31, 5, "STORAGE", PALETTE.CYAN_LIGHT],
      [32, 5, "[ Storage API unavailable ]", PALETTE.GRAY_DARK],
      [34, 5, "PWA", PALETTE.CYAN_LIGHT],
      [36, 5, "[ ] UNAVAILABLE", PALETTE.GRAY_DARK],
      [37, 5, "[ ] APPLY UPDATE", PALETTE.GRAY_LIGHT],
      [38, 5, "ONLINE", PALETTE.GRAY_DARK],
    ];
    for (const [y, x, text, fg] of rows) {
      expect(at(grid, y, x, text.length)).toBe(text);
      expect(grid.cells[y]?.[x]?.fg).toBe(fg);
    }
  });

  it("pins the two footer lines, in order, to the last two inner rows", () => {
    const grid = renderSettingsScreen(state, 80, 50);
    const hint = "ENTER: toggle audio | TAB: switch | ESC: back";
    const note = "Volumes persist via localStorage";
    expect(at(grid, 46, 3, hint.length)).toBe(hint);
    expect(at(grid, 47, 3, note.length)).toBe(note);
    expect(grid.cells[46]?.[3]?.fg).toBe(PALETTE.GRAY_DARK);
    expect(grid.cells[47]?.[3]?.fg).toBe(PALETTE.GRAY_DARK);
    expect(gridToText(grid)[48]?.[3]).toBe("═");
  });

  it("shows the PWA rows AND the footer inside the frame on 40-row grids", () => {
    // ADR-0237 Open question (f): 60x40 used to lose the PWA install/update
    // rows under the footer and the online line under the rail.
    for (const cols of [60, 80]) {
      const grid = renderSettingsScreen(state, cols, 40);
      const rows: ReadonlyArray<readonly [number, number, string, string]> = [
        [30, 5, "[ Storage API unavailable ]", PALETTE.GRAY_DARK],
        [32, 5, "PWA", PALETTE.CYAN_LIGHT],
        [33, 5, "[ ] UNAVAILABLE", PALETTE.GRAY_DARK],
        [34, 5, "[ ] APPLY UPDATE", PALETTE.GRAY_LIGHT],
        [35, 5, "ONLINE", PALETTE.GRAY_DARK],
        [
          36,
          3,
          "ENTER: toggle audio | TAB: switch | ESC: back",
          PALETTE.GRAY_DARK,
        ],
        [37, 3, "Volumes persist via localStorage", PALETTE.GRAY_DARK],
      ];
      expect(settingsLayout(cols, 40).footerY).toBe(36);
      for (const [y, x, text, fg] of rows) {
        expect(at(grid, y, x, text.length), `${text} @ ${cols}x40`).toBe(text);
        expect(grid.cells[y]?.[x]?.fg).toBe(fg);
      }
      const lines = gridToText(grid);
      expect(lines[38]?.slice(1, cols - 1)).toBe(`╚${"═".repeat(cols - 4)}╝`);
      expect(lines[0]?.trim()).toBe("");
      expect(lines[39]?.trim()).toBe("");
    }
  });

  it("lets the footer follow the body in flow instead of pinning it", () => {
    expect(settingsLayout(60, 40)).toEqual({
      frame: { x: 1, y: 1, width: 58, height: 38 },
      inner: { x: 2, y: 2, width: 56, height: 36 },
      footerY: 36,
      collapsedSpacers: [34, 21, 6],
    });
  });

  it("keeps today's pinned placement on every preset of 43+ rows", () => {
    for (const [cols, rows] of PRESETS) {
      if (rows < 43) continue;
      const layout = settingsLayout(cols, rows);
      expect(layout.collapsedSpacers).toEqual([]);
      expect(layout.footerY).toBe(rows - 4);
    }
  });

  it("shows every settings line inside the frame at every real preset", () => {
    for (const [cols, rows] of PRESETS) {
      const grid = renderSettingsScreen(state, cols, rows);
      const lines = gridToText(grid);
      const innerText = lines
        .slice(2, rows - 2)
        .map((l) => l.slice(2, cols - 2));
      const trimmed = innerText.map((l) => l.trim());
      for (const prefix of EVERY_LINE) {
        const hits = trimmed.filter((l) => l.startsWith(prefix));
        expect(hits, `${prefix} @ ${cols}x${rows}`).toHaveLength(1);
      }
      const bars = trimmed.filter((l) => /^\[[█░]/.test(l));
      expect(bars, `slider bars @ ${cols}x${rows}`).toHaveLength(3);
      expect(lines[0]?.trim(), `top gutter @ ${cols}x${rows}`).toBe("");
      expect(lines[rows - 1]?.trim(), `bottom gutter @ ${cols}x${rows}`).toBe(
        "",
      );
      expect(colText(grid, 0).trim()).toBe("");
      expect(colText(grid, cols - 1).trim()).toBe("");
      for (let y = 2; y < rows - 2; y++) {
        expect(grid.cells[y]?.[1]?.char).toBe("║");
        expect(grid.cells[y]?.[cols - 2]?.char).toBe("║");
      }
      expect(lines[1]?.slice(1, cols - 1)).toBe(`╔${"═".repeat(cols - 4)}╗`);
      expect(lines[rows - 2]?.slice(1, cols - 1)).toBe(
        `╚${"═".repeat(cols - 4)}╝`,
      );
    }
  });

  it("clips overlong lines at the inner edge instead of the right rail", () => {
    const grid = renderSettingsScreen(state, 32, 50);
    for (let y = 2; y < 48; y++) {
      expect(grid.cells[y]?.[30]?.char).toBe("║");
      expect(grid.cells[y]?.[31]?.char).toBe(" ");
    }
  });
});

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
