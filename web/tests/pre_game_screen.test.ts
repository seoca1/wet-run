import { describe, expect, it } from "vitest";
import {
  pauseLayout,
  renderPreGameScreen,
} from "../src/renderer/pre_game_screen";
import {
  MENU_OPTIONS,
  renderMainMenu,
  renderStubScreen,
} from "../src/renderer/menu";
import { renderMissionList } from "../src/renderer/mission_select";
import { renderFarGridHub } from "../src/renderer/far_grid_hub";
import { renderSettingsScreen } from "../src/renderer/settings";
import { renderCraftingScreen } from "../src/renderer/crafting_screen";
import { renderEquipmentScreen } from "../src/renderer/equipment_screen";
import { renderDungeonMap, renderDungeonUi } from "../src/renderer/dungeon";
import { DungeonCrawler } from "../src/core/dungeon/dungeon_crawler";
import { PALETTE } from "../src/renderer/palette";
import { preGameView } from "./view_fixtures";

describe("pre-game screen composition", () => {
  it("preserves the complete framed menu with save, language and gated option inputs", () => {
    const input = preGameView({
      screen: "menu",
      menuIndex: 4,
      hasSave: true,
      saveMeta: { missionId: "test", turnCount: 3, savedAt: "2026-01-01" },
      message: "x".repeat(200),
      language: "ko",
      farGridUnlocked: false,
    });
    const view = renderPreGameScreen(input, 80, 50);
    const expected = renderMainMenu(
      4,
      80,
      50,
      true,
      input.saveMeta,
      input.message,
      false,
      "ko",
    );
    expect(view.grid.cells).toEqual(expected.cells);
    expect(view.hud).toEqual([
      "MAIN MENU",
      "",
      `Selected: 5/${MENU_OPTIONS.length}`,
    ]);
  });

  it("preserves mission frame cells and selected-row HUD on a compact grid", () => {
    const input = preGameView({
      screen: "mission_select",
      missionIndex: 1,
      missionRows: ["[1] First", "[2] Second"],
    });
    const view = renderPreGameScreen(input, 40, 30);
    expect(view.grid.cells).toEqual(
      renderMissionList(input.missionRows, 1, 40, 30).cells,
    );
    expect(view.hud).toEqual(["MISSION SELECT", "", "Selected: 2/2"]);
  });

  it("preserves Far Grid mission ordering, language and HUD", () => {
    const input = preGameView({ screen: "far_grid_hub", language: "ko" });
    const view = renderPreGameScreen(input, 80, 50);
    expect(view.grid.cells).toEqual(
      renderFarGridHub(input.farGridMissions, 0, 80, 50, "", "ko").cells,
    );
    expect(view.hud).toEqual(["FAR GRID HUB", "", "Selected: 1/1"]);
  });

  it("delegates settings without changing volume or accessibility presentation", () => {
    const input = preGameView({ screen: "settings" });
    const view = renderPreGameScreen(input, 80, 50);
    expect(view.grid.cells).toEqual(
      renderSettingsScreen(input.settings, 80, 50).cells,
    );
    expect(view.hud).toEqual([
      "SETTINGS",
      "",
      "Audio controls — volumes persist",
    ]);
  });

  it("keeps pause grid blank and all instructions in the HUD", () => {
    const input = preGameView({ screen: "pause" });
    const view = renderPreGameScreen(input, 40, 30);
    expect(pauseLayout(40, 30)).toEqual({ cols: 40, rows: 30 });
    expect(
      view.grid.cells.every((row) => row.every((cell) => cell.char === " ")),
    ).toBe(true);
    expect(view.hud).toEqual([
      "PAUSED",
      "",
      "ESC: Resume | SETTINGS: Enter | ESC: Quit to Menu",
    ]);
  });

  it("delegates crafting with inventory feedback and its unchanged HUD", () => {
    const input = preGameView({
      screen: "crafting",
      crafting: { ...preGameView().crafting, message: "No recipe" },
    });
    const view = renderPreGameScreen(input, 80, 50);
    expect(view.grid.cells).toEqual(
      renderCraftingScreen(input.crafting, 80, 50).cells,
    );
    expect(view.hud).toEqual(["CRAFTING", "", ""]);
  });

  it("delegates equipment with controller feedback and its unchanged HUD", () => {
    const input = preGameView({
      screen: "equipment",
      message: "No available equipment",
    });
    const view = renderPreGameScreen(input, 80, 50);
    expect(view.grid.cells).toEqual(
      renderEquipmentScreen(
        {
          loadout: input.loadout,
          slots: input.equipmentSlots,
          message: input.message,
        },
        80,
        50,
      ).cells,
    );
    expect(view.hud).toEqual(["EQUIPMENT", "", ""]);
  });

  it("keeps the inactive dungeon blank with its existing message", () => {
    const view = renderPreGameScreen(
      preGameView({ screen: "dungeon" }),
      80,
      50,
    );
    expect(
      view.grid.cells.every((row) => row.every((cell) => cell.char === " ")),
    ).toBe(true);
    expect(view.hud).toEqual(["DUNGEON", "", "No dungeon active"]);
  });

  it.each([74, 75, 100])(
    "preserves dungeon cells and alarm-only tint at %i alarm",
    (alarm) => {
      const dungeon = new DungeonCrawler(42);
      dungeon["_state"].playerAlarm = alarm;
      const view = renderPreGameScreen(
        preGameView({ screen: "dungeon", dungeon }),
        80,
        50,
      );
      expect(view.grid.cells).toEqual(renderDungeonMap(dungeon, 80, 50).cells);
      expect(view.hud).toEqual(renderDungeonUi(dungeon, 80, 50));
      expect(view.colorFor?.("ALM: test")).toBe(
        alarm >= 100
          ? PALETTE.RED_BRIGHT
          : alarm >= 75
            ? PALETTE.YELLOW_AMBER
            : undefined,
      );
      expect(view.colorFor?.("HP: test")).toBeUndefined();
      expect(dungeon.state.playerAlarm).toBe(alarm);
    },
  );

  it.each([0, -1])(
    "keeps the stub label fallback for menu index %i",
    (menuIndex) => {
      const view = renderPreGameScreen(
        preGameView({ screen: "credits", menuIndex }),
        80,
        50,
      );
      const label = menuIndex === 0 ? "NEW RUN" : "WET RUN";
      expect(view.grid.cells).toEqual(renderStubScreen(label, 80, 50).cells);
      expect(view.hud).toEqual(["STUB", "", "Coming soon — Tier 5+"]);
    },
  );
});
