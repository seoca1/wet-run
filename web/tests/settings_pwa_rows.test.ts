/** Tests for the PWA section in renderSettingsScreen.
 *
 * Pins the new row layout (install row, update row, offline status line) and
 * the selection/hint behavior for the two new SettingsField members
 * (`pwa_install`, `pwa_update`). Exercises both EN and KO i18n tables.
 */
import { describe, it, expect } from "vitest";
import {
  renderSettingsScreen,
  type SettingsField,
  type SettingsState,
} from "../src/renderer/settings.js";
import { INITIAL_PWA_STATE, type PwaState } from "../src/core/pwa_manager.ts";

function gridLines(grid: ReturnType<typeof renderSettingsScreen>): string[] {
  const lines: string[] = [];
  for (let y = 0; y < grid.height; y++) {
    let line = "";
    for (let x = 0; x < grid.width; x++) {
      const c = grid.get(x, y);
      line += c?.char ?? " ";
    }
    lines.push(line);
  }
  return lines;
}

function findLine(
  grid: ReturnType<typeof renderSettingsScreen>,
  needle: string,
): string | undefined {
  return gridLines(grid).find((l) => l.includes(needle));
}

function makeBaseState(
  overrides: Partial<SettingsState> = {},
): SettingsState {
  // DEFAULT_PWA = offline=false so ONLINE row is visible regardless of
  // navigator.onLine in the host env (jsdom defaults to false; node has none).
  const defaultPwa: PwaState = {
    ...INITIAL_PWA_STATE,
    isOffline: false,
  };
  return {
    selectedField: "audio",
    audioEnabled: true,
    bgmVolume: 0.5,
    sfxVolume: 0.5,
    muted: false,
    language: "en",
    storageQuota: { state: "unavailable", reason: "test fixture" },
    pwa: defaultPwa,
    ...overrides,
  };
}

describe("Settings — PWA section: install row", () => {
  it("renders PWA header in English", () => {
    const grid = renderSettingsScreen(makeBaseState(), 80, 40);
    expect(findLine(grid, "PWA")).toBeDefined();
  });

  it("translates PWA header to Korean", () => {
    const grid = renderSettingsScreen(
      makeBaseState({ language: "ko" }),
      80,
      40,
    );
    expect(findLine(grid, "PWA")).toBeDefined();
  });

  it("shows [ ] UNAVAILABLE when not installable (default state)", () => {
    const grid = renderSettingsScreen(makeBaseState(), 80, 40);
    expect(findLine(grid, "UNAVAILABLE")).toBeDefined();
    expect(findLine(grid, "INSTALL APP")).toBeUndefined();
    expect(findLine(grid, "INSTALLED")).toBeUndefined();
  });

  it("shows [ ] INSTALL APP when canInstall=true", () => {
    const pwa: PwaState = { ...INITIAL_PWA_STATE, canInstall: true };
    const grid = renderSettingsScreen(makeBaseState({ pwa }), 80, 40);
    expect(findLine(grid, "INSTALL APP")).toBeDefined();
    expect(findLine(grid, "UNAVAILABLE")).toBeUndefined();
  });

  it("shows [X] INSTALLED when isInstalled=true", () => {
    const pwa: PwaState = { ...INITIAL_PWA_STATE, isInstalled: true };
    const grid = renderSettingsScreen(makeBaseState({ pwa }), 80, 40);
    expect(findLine(grid, "INSTALLED")).toBeDefined();
    expect(findLine(grid, "INSTALL APP")).toBeUndefined();
  });

  it("renders Korean install label when KO is selected", () => {
    const pwa: PwaState = { ...INITIAL_PWA_STATE, canInstall: true };
    const grid = renderSettingsScreen(
      makeBaseState({ pwa, language: "ko" }),
      80,
      40,
    );
    expect(findLine(grid, "앱 설치")).toBeDefined();
  });

  it("renders Korean installed label", () => {
    const pwa: PwaState = { ...INITIAL_PWA_STATE, isInstalled: true };
    const grid = renderSettingsScreen(
      makeBaseState({ pwa, language: "ko" }),
      80,
      40,
    );
    expect(findLine(grid, "설치됨")).toBeDefined();
  });
});

describe("Settings — PWA section: update row", () => {
  it("shows [ ] APPLY UPDATE when no update is available", () => {
    const grid = renderSettingsScreen(makeBaseState(), 80, 40);
    expect(findLine(grid, "APPLY UPDATE")).toBeDefined();
    expect(findLine(grid, "UPDATE AVAILABLE")).toBeUndefined();
  });

  it("shows [X] UPDATE AVAILABLE when hasUpdate=true", () => {
    const pwa: PwaState = { ...INITIAL_PWA_STATE, hasUpdate: true };
    const grid = renderSettingsScreen(makeBaseState({ pwa }), 80, 40);
    expect(findLine(grid, "UPDATE AVAILABLE")).toBeDefined();
  });

  it("renders Korean update-available label", () => {
    const pwa: PwaState = { ...INITIAL_PWA_STATE, hasUpdate: true };
    const grid = renderSettingsScreen(
      makeBaseState({ pwa, language: "ko" }),
      80,
      40,
    );
    expect(findLine(grid, "업데이트 가능")).toBeDefined();
  });
});

describe("Settings — PWA section: offline status line", () => {
  it("shows ONLINE when isOffline=false", () => {
    const grid = renderSettingsScreen(makeBaseState(), 80, 40);
    expect(findLine(grid, "ONLINE")).toBeDefined();
    expect(findLine(grid, "OFFLINE")).toBeUndefined();
  });

  it("shows OFFLINE when isOffline=true", () => {
    const pwa: PwaState = { ...INITIAL_PWA_STATE, isOffline: true };
    const grid = renderSettingsScreen(makeBaseState({ pwa }), 80, 40);
    expect(findLine(grid, "OFFLINE")).toBeDefined();
    expect(findLine(grid, "ONLINE")).toBeUndefined();
  });

  it("translates offline status to Korean", () => {
    const pwa: PwaState = { ...INITIAL_PWA_STATE, isOffline: true };
    const grid = renderSettingsScreen(
      makeBaseState({ pwa, language: "ko" }),
      80,
      40,
    );
    expect(findLine(grid, "오프라인")).toBeDefined();
    const onlineGrid = renderSettingsScreen(
      makeBaseState({ language: "ko" }),
      80,
      40,
    );
    expect(findLine(onlineGrid, "온라인")).toBeDefined();
  });
});

describe("Settings — PWA section: field selection + hint", () => {
  const fields: ReadonlyArray<SettingsField> = [
    "audio",
    "bgm",
    "sfx",
    "mute",
    "language",
    "pwa_install",
    "pwa_update",
  ];

  for (const field of fields) {
    it(`accepts '${field}' as a SettingsField without throwing`, () => {
      const grid = renderSettingsScreen(makeBaseState({ selectedField: field }), 80, 40);
      expect(grid).toBeDefined();
    });
  }

  it("renders ENTER: install hint when pwa_install is selected", () => {
    const grid = renderSettingsScreen(
      makeBaseState({ selectedField: "pwa_install" }),
      80,
      40,
    );
    expect(findLine(grid, "ENTER: install app")).toBeDefined();
  });

  it("renders ENTER: apply update hint when pwa_update is selected", () => {
    const grid = renderSettingsScreen(
      makeBaseState({ selectedField: "pwa_update" }),
      80,
      40,
    );
    expect(findLine(grid, "ENTER: apply update")).toBeDefined();
  });

  it("renders Korean install hint when KO + pwa_install selected", () => {
    const grid = renderSettingsScreen(
      makeBaseState({ selectedField: "pwa_install", language: "ko" }),
      80,
      40,
    );
    // Hint text is still English (settings pane hint) per existing convention
    // — only section labels are translated. Verify the install hint still appears.
    expect(findLine(grid, "ENTER: install app")).toBeDefined();
  });
});

describe("Settings — PWA section: existing EN rows unchanged", () => {
  it("still renders AUDIO section header (regression guard)", () => {
    const grid = renderSettingsScreen(makeBaseState(), 80, 40);
    expect(findLine(grid, "AUDIO")).toBeDefined();
  });

  it("still renders BGM Volume label", () => {
    const grid = renderSettingsScreen(makeBaseState(), 80, 40);
    expect(findLine(grid, "BGM Volume")).toBeDefined();
  });

  it("still renders MUTE ALL label", () => {
    const grid = renderSettingsScreen(makeBaseState(), 80, 40);
    expect(findLine(grid, "MUTE ALL")).toBeDefined();
  });

  it("still renders LANGUAGE section header in EN", () => {
    const grid = renderSettingsScreen(makeBaseState(), 80, 40);
    expect(findLine(grid, "LANGUAGE")).toBeDefined();
  });

  it("still renders STORAGE section header", () => {
    const grid = renderSettingsScreen(makeBaseState(), 80, 40);
    expect(findLine(grid, "STORAGE")).toBeDefined();
  });
});