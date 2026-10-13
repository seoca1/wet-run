/** Tests for the Settings screen language toggle (ADR-0010 activation).
 *
 * Pins:
 *  - `SettingsState` exposes a `language: Language` field + "language" is in
 *    the `SettingsField` union so the settings screen can highlight it.
 *  - `getInitialSettingsState` reads `wetrun_language` from localStorage and
 *    falls back to "en" when missing or malformed (defends against a stale
 *    user setting or a corrupted browser storage).
 *  - `persistLanguage` writes the canonical `wetrun_language` key so the
 *    toggle survives reloads.
 *  - `cycleLanguage` toggles en → ko → en (and back).
 *  - `renderSettingsScreen` reflects the persisted language: shows
 *    `[ ] EN` / `[X] KO` depending on the state and uses the right hint.
 *  - `renderMainMenu` / `renderFarGridHub` honor the `language` arg — KO
 *    output is byte-different (Korean literals resolved) and EN output
 *    matches the default-parameter call (no regression).
 */
import { afterEach, beforeEach, describe, it, expect } from "vitest";
import {
  LANGUAGE_STORAGE_KEY,
  cycleLanguage,
  getInitialSettingsState,
  loadPersistedLanguage,
  persistLanguage,
  renderSettingsScreen,
  type SettingsState,
} from "../src/renderer/settings.js";
import { renderMainMenu } from "../src/renderer/menu_main";
import { renderFarGridHub } from "../src/renderer/far_grid_hub";
import type { Cell, Mission, MissionRewards } from "../src/core/types";
import { INITIAL_PWA_STATE } from "../src/core/pwa_manager.ts";

type GridLike = { cells: ReadonlyArray<ReadonlyArray<Cell>> };

function gridText(grid: GridLike): string {
  return grid.cells
    .map((row) => row.map((c) => c?.char ?? " ").join(""))
    .join("\n");
}

function getRowText(
  grid: GridLike,
  y: number,
  x: number,
  length: number,
): string {
  let result = "";
  const row = grid.cells[y];
  if (!row) return result;
  for (let i = 0; i < length; i++) {
    result += row[x + i]?.char ?? " ";
  }
  return result;
}

function gridLines(
  grid: { cells: ReadonlyArray<ReadonlyArray<Cell>>; width: number; height: number },
): string[] {
  const out: string[] = [];
  for (let y = 0; y < grid.height; y++) {
    let line = "";
    for (let x = 0; x < grid.width; x++) {
      line += grid.cells[y]?.[x]?.char ?? " ";
    }
    out.push(line);
  }
  return out;
}

const EMPTY_REWARDS: MissionRewards = { credits: 0, materials: {} };
function makeMission(id: string, title: string): Mission {
  return {
    id,
    title,
    fixer: "test_fixer",
    arc: 1,
    zone: "far_grid_test",
    grade_min: 1,
    grade_max: 1,
    rewards: EMPTY_REWARDS,
    source_universe: "far-grid",
  };
}

const baseSettingsState: SettingsState = {
  selectedField: "audio",
  audioEnabled: true,
  bgmVolume: 0.5,
  sfxVolume: 0.5,
  muted: false,
  language: "en",
  storageQuota: { state: "unavailable", reason: "test fixture" },
  pwa: INITIAL_PWA_STATE,
};

beforeEach(() => {
  localStorage.removeItem(LANGUAGE_STORAGE_KEY);
});

afterEach(() => {
  localStorage.removeItem(LANGUAGE_STORAGE_KEY);
});

describe("LANGUAGE_STORAGE_KEY", () => {
  it("uses the wetrun_* namespace convention (settings persistence parity)", () => {
    expect(LANGUAGE_STORAGE_KEY).toBe("wetrun_language");
  });
});

describe("loadPersistedLanguage", () => {
  it("returns 'en' when the key is absent", () => {
    expect(loadPersistedLanguage()).toBe("en");
  });

  it("returns 'ko' when persisted", () => {
    localStorage.setItem(LANGUAGE_STORAGE_KEY, "ko");
    expect(loadPersistedLanguage()).toBe("ko");
  });

  it("returns 'en' when persisted value is malformed (defensive read)", () => {
    localStorage.setItem(LANGUAGE_STORAGE_KEY, "fr");
    expect(loadPersistedLanguage()).toBe("en");
    localStorage.setItem(LANGUAGE_STORAGE_KEY, "");
    expect(loadPersistedLanguage()).toBe("en");
    localStorage.setItem(LANGUAGE_STORAGE_KEY, "ja");
    expect(loadPersistedLanguage()).toBe("en");
  });
});

describe("persistLanguage", () => {
  it("writes 'ko' to the canonical key", () => {
    persistLanguage("ko");
    expect(localStorage.getItem(LANGUAGE_STORAGE_KEY)).toBe("ko");
  });

  it("writes 'en' to the canonical key", () => {
    persistLanguage("en");
    expect(localStorage.getItem(LANGUAGE_STORAGE_KEY)).toBe("en");
  });
});

describe("cycleLanguage", () => {
  it("toggles en → ko", () => {
    expect(cycleLanguage("en")).toBe("ko");
  });

  it("toggles ko → en", () => {
    expect(cycleLanguage("ko")).toBe("en");
  });
});

describe("getInitialSettingsState — language field", () => {
  it("defaults language to 'en' when no key is set", () => {
    const s = getInitialSettingsState();
    expect(s.language).toBe("en");
  });

  it("reads 'ko' from localStorage into language", () => {
    localStorage.setItem(LANGUAGE_STORAGE_KEY, "ko");
    const s = getInitialSettingsState();
    expect(s.language).toBe("ko");
  });
});

describe("renderSettingsScreen — language row", () => {
  it("shows '[ ] EN' when language is 'en' and language field is unselected", () => {
    const grid = renderSettingsScreen(
      { ...baseSettingsState, language: "en", selectedField: "audio" },
      80,
      30,
    );
    const lines = gridLines(grid);
    expect(lines.some((l) => l.includes("[ ] EN"))).toBe(true);
    expect(lines.some((l) => l.includes("[X] KO"))).toBe(false);
  });

  it("shows '[X] KO' when language is 'ko'", () => {
    const grid = renderSettingsScreen(
      { ...baseSettingsState, language: "ko", selectedField: "audio" },
      80,
      30,
    );
    const lines = gridLines(grid);
    expect(lines.some((l) => l.includes("[X] KO"))).toBe(true);
    expect(lines.some((l) => l.includes("[ ] EN"))).toBe(false);
  });

  it("renders the LANGUAGE section header (English label by default)", () => {
    const grid = renderSettingsScreen(
      { ...baseSettingsState, language: "en" },
      80,
      30,
    );
    const lines = gridLines(grid);
    expect(lines.some((l) => l.trim() === "LANGUAGE")).toBe(true);
  });

  it("translates the LANGUAGE section header to Korean when KO is selected", () => {
    const grid = renderSettingsScreen(
      { ...baseSettingsState, language: "ko" },
      80,
      30,
    );
    const lines = gridLines(grid);
    expect(lines.some((l) => l.trim() === "언어")).toBe(true);
    expect(lines.some((l) => l.trim() === "LANGUAGE")).toBe(false);
  });

  it("shows the language hint when the language row is selected", () => {
    const grid = renderSettingsScreen(
      { ...baseSettingsState, selectedField: "language", language: "en" },
      80,
      30,
    );
    const lines = gridLines(grid);
    expect(
      lines.some((l) =>
        l.includes("ENTER: toggle language | TAB: switch | ESC: back"),
      ),
    ).toBe(true);
  });

  it("highlights the language row with the selection color", () => {
    // Selected row at y=22 should be exact text without relying on color.
    // We can verify the row exists and is well-formed (no clipping).
    const grid = renderSettingsScreen(
      { ...baseSettingsState, selectedField: "language", language: "ko" },
      80,
      30,
    );
    expect(getRowText(grid, 22, 4, "[X] KO".length)).toBe("[X] KO");
  });
});

describe("renderMainMenu — language wiring is now active", () => {
  it("EN default is unchanged (default arg matches explicit 'en')", () => {
    const defaultCall = renderMainMenu(1, 80, 50, false, null, "", false);
    const explicitEn = renderMainMenu(1, 80, 50, false, null, "", false, "en");
    expect(gridText(defaultCall)).toBe(gridText(explicitEn));
    // Spot-check that EN literals are on the page.
    expect(gridText(defaultCall)).toContain("[1] NEW RUN");
    expect(gridText(defaultCall)).toContain("[7] CRAFT");
  });

  it("KO renders the menu labels in Korean", () => {
    const text = gridText(
      renderMainMenu(1, 80, 50, false, null, "", false, "ko"),
    );
    expect(text).toContain("[1] 새 런");
    expect(text).toContain("[7] 제작");
    expect(text).toContain("↑↓: 이동 | ENTER: 선택 | ESC: 뒤로");
  });

  it("KO renders the (no save) suffix in Korean", () => {
    const text = gridText(
      renderMainMenu(4, 80, 50, false, null, "", true, "ko"),
    );
    expect(text).toContain("이어서 하기    (저장 없음)");
  });
});

describe("renderFarGridHub — language wiring is now active", () => {
  const missions: ReadonlyArray<Mission> = [
    makeMission("m1", "Echo Lattice"),
  ];

  it("EN default is unchanged (default arg matches explicit 'en')", () => {
    const defaultCall = renderFarGridHub(missions, 0, 80, 24);
    const explicitEn = renderFarGridHub(missions, 0, 80, 24, "", "en");
    expect(gridText(defaultCall)).toBe(gridText(explicitEn));
  });

  it("KO renders the hub header in Korean", () => {
    const grid = renderFarGridHub(missions, 0, 80, 24, "", "ko");
    expect(getRowText(grid, 1, 2, "FAR GRID 허브".length)).toBe(
      "FAR GRID 허브",
    );
  });

  it("KO renders the intro and footer in Korean", () => {
    const text = gridText(renderFarGridHub(missions, 0, 80, 24, "", "ko"));
    expect(text).toContain("스프롤 너머 — FAR GRID 임무");
    expect(text).toContain("↑↓: 이동 | ENTER: 출격 | ESC: 뒤로");
  });
});