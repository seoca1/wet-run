/** Tests for main menu renderer (Tier 4). */
import { describe, it, expect } from "vitest";
import { renderMainMenu, renderStubScreen, MENU_OPTIONS } from "../src/renderer/menu.ts";

describe("main menu renderer", () => {
  it("has 9 options matching Python OPTION_* constants", () => {
    expect(MENU_OPTIONS.length).toBe(9);
    expect(MENU_OPTIONS.map((o) => o.key)).toEqual([
      "new_run",
      "graphic_novel",
      "continue",
      "settings",
      "credits",
      "hall_of_dead",
      "help",
      "endings",
      "stats",
    ]);
  });

  it("all options marked available (Tier 4 — stubs render 'Coming soon')", () => {
    expect(MENU_OPTIONS.every((o) => o.available)).toBe(true);
  });

  it("renders all options as visible text in the grid", () => {
    const cols = 80;
    const rows = 50;
    const grid = renderMainMenu(0, cols, rows);

    let allText = "";
    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        const cell = grid.get(x, y);
        if (cell) allText += cell.char;
      }
    }

    // Title visible
    expect(allText).toContain("WET RUN");
    // All 9 labels visible
    for (const opt of MENU_OPTIONS) {
      expect(allText).toContain(opt.label);
    }
  });

  it("selected option shows ▸ marker at the right index", () => {
    const cols = 80;
    const rows = 50;
    // Select index 2 (CONTINUE)
    const grid = renderMainMenu(2, cols, rows);

    let rowWithMarker = -1;
    for (let y = 0; y < rows; y++) {
      let rowText = "";
      for (let x = 0; x < cols; x++) {
        const cell = grid.get(x, y);
        if (cell) rowText += cell.char;
      }
      if (rowText.includes("▸")) {
        rowWithMarker = y;
        break;
      }
    }
    expect(rowWithMarker).toBeGreaterThan(0);
    // Marker at row = startY (8) + selectedIndex (2) = 10
    expect(rowWithMarker).toBe(8 + 2);
  });

  it("grid dimensions match requested cols/rows", () => {
    const grid = renderMainMenu(0, 40, 60);
    expect(grid.width).toBe(40);
    expect(grid.height).toBe(60);
  });

  it("renders footer with controls hint", () => {
    const grid = renderMainMenu(0, 80, 50);
    let allText = "";
    for (let y = 0; y < 50; y++) {
      for (let x = 0; x < 80; x++) {
        const cell = grid.get(x, y);
        if (cell) allText += cell.char;
      }
    }
    expect(allText).toContain("ENTER");
    expect(allText).toContain("Arrow");
  });
});

describe("stub screen renderer", () => {
  it("shows the option label and 'Coming soon' message", () => {
    const grid = renderStubScreen("SETTINGS", 80, 50);
    let allText = "";
    for (let y = 0; y < 50; y++) {
      for (let x = 0; x < 80; x++) {
        const cell = grid.get(x, y);
        if (cell) allText += cell.char;
      }
    }
    expect(allText).toContain("SETTINGS");
    expect(allText).toContain("Coming soon");
  });
});