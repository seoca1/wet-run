/** Tests for main menu renderer (Tier 4). */
import { describe, it, expect } from "vitest";
import {
  renderMainMenu,
  renderStubScreen,
  MENU_OPTIONS,
} from "../src/renderer/menu";
import { t } from "../src/core/i18n";

describe("main menu renderer", () => {
  it("has 13 options including far_grid_hub, craft, equipment, and dungeon_crawl", () => {
    expect(MENU_OPTIONS.length).toBe(13);
    // ADR-0315: grouped order, CONTINUE first (the likely action).
    // ADR-0317: GRAPHIC NOVEL is gone — the story is the run's prologue now.
    expect(MENU_OPTIONS.map((o) => o.key)).toEqual([
      "continue",
      "new_run",
      "far_grid_hub",
      "dungeon_crawl",
      "tutorial",
      "craft",
      "equipment",
      "hall_of_dead",
      "endings",
      "stats",
      "settings",
      "help",
      "credits",
    ]);
  });

  it("every entry names what it is (ADR-0315)", () => {
    // The point of the redesign: no option is a bare word. Each has a
    // description key that resolves to a one-liner, and each belongs to a
    // group whose header is printed above it.
    for (const opt of MENU_OPTIONS) {
      expect(t(opt.desc, "en").length).toBeGreaterThan(0);
    }
    expect(MENU_OPTIONS.filter((o) => o.group !== undefined).length).toBe(4);
  });

  it("all options marked available (Tier 4 — stubs render 'Coming soon')", () => {
    expect(MENU_OPTIONS.every((o) => o.available)).toBe(true);
  });

  it("renders all options as visible text in the grid", () => {
    const cols = 80;
    const rows = 50;
    // hasSave=true so CONTINUE is not gated (its description shows instead of
    // "(no save)") — the point is that every entry explains itself.
    const grid = renderMainMenu(0, cols, rows, true);

    let allText = "";
    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        const cell = grid.get(x, y);
        if (cell) allText += cell.char;
      }
    }

    // Title visible
    expect(allText).toContain("WET RUN");
    // Every label AND its description are on screen — that is the redesign.
    for (const opt of MENU_OPTIONS) {
      expect(allText).toContain(t(opt.label, "en"));
      expect(allText).toContain(t(opt.desc, "en"));
    }
  });

  it("selected option shows ▸ marker on its own row", () => {
    const cols = 80;
    const rows = 50;
    // Index 2 is FAR GRID in the grouped order.
    const grid = renderMainMenu(2, cols, rows);

    let markerRow = "";
    for (let y = 0; y < rows; y++) {
      let rowText = "";
      for (let x = 0; x < cols; x++) {
        const cell = grid.get(x, y);
        if (cell) rowText += cell.char;
      }
      if (rowText.includes("▸")) markerRow = rowText;
    }
    expect(markerRow).toContain(t("menu.far_grid_hub", "en"));
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
    expect(allText).toContain("↑↓");
    expect(allText).toContain("ESC");
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
