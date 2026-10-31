import { makeGrid } from "../core/grid";
import type { ScreenKind, Mission } from "../core/types";
import type { Language } from "../core/i18n";
import type { DungeonCrawler } from "../core/dungeon/dungeon_crawler";
import { MENU_OPTIONS, renderMainMenu, renderStubScreen } from "./menu";
import { renderMissionList } from "./mission_select";
import { renderFarGridHub } from "./far_grid_hub";
import { renderSettingsScreen, type SettingsState } from "./settings";
import { renderDungeonMap, renderDungeonUi } from "./dungeon";
import { renderCraftingScreen, type CraftingView } from "./crafting_screen";
import { renderEquipmentScreen } from "./equipment_screen";
import type { EquipmentLoadout } from "../core/types";
import type { EquipSlot } from "../core/state/equipment";
import type { ScreenView } from "./screen_view";
import { PALETTE } from "./palette";

export interface PreGameView {
  readonly screen: ScreenKind;
  readonly menuIndex: number;
  readonly missionIndex: number;
  readonly missionRows: readonly string[];
  readonly farGridMissions: readonly Mission[];
  readonly hasSave: boolean;
  readonly saveMeta: {
    readonly missionId: string;
    readonly turnCount: number;
    readonly savedAt: string;
  } | null;
  readonly message: string;
  readonly farGridUnlocked: boolean;
  readonly language: Language;
  readonly settings: SettingsState;
  readonly crafting: CraftingView;
  readonly loadout: EquipmentLoadout;
  readonly equipmentSlots: readonly EquipSlot[];
  readonly dungeon: DungeonCrawler | null;
}

/** Pause intentionally has a blank grid; its instructions live only in the HUD. */
export function pauseLayout(cols: number, rows: number) {
  return { cols, rows } as const;
}

/** Compose a pre-game screen from a read-only presentation snapshot. */
export function renderPreGameScreen(
  view: PreGameView,
  cols: number,
  rows: number,
): ScreenView {
  switch (view.screen) {
    case "menu":
      return {
        grid: renderMainMenu(
          view.menuIndex,
          cols,
          rows,
          view.hasSave,
          view.saveMeta,
          view.message,
          view.farGridUnlocked,
          view.language,
        ),
        hud: [
          "MAIN MENU",
          "",
          `Selected: ${view.menuIndex + 1}/${MENU_OPTIONS.length}`,
        ],
      };
    case "mission_select":
      return {
        grid: renderMissionList(
          view.missionRows,
          view.missionIndex,
          cols,
          rows,
        ),
        hud: [
          "MISSION SELECT",
          "",
          `Selected: ${view.missionIndex + 1}/${view.missionRows.length}`,
        ],
      };
    case "far_grid_hub":
      return {
        grid: renderFarGridHub(
          view.farGridMissions,
          view.missionIndex,
          cols,
          rows,
          "",
          view.language,
        ),
        hud: [
          "FAR GRID HUB",
          "",
          `Selected: ${view.missionIndex + 1}/${view.farGridMissions.length}`,
        ],
      };
    case "settings":
      return {
        grid: renderSettingsScreen(view.settings, cols, rows),
        hud: ["SETTINGS", "", "Audio controls — volumes persist"],
      };
    case "pause": {
      const layout = pauseLayout(cols, rows);
      return {
        grid: makeGrid(layout.cols, layout.rows),
        hud: [
          "PAUSED",
          "",
          "ESC: Resume | SETTINGS: Enter | ESC: Quit to Menu",
        ],
      };
    }
    case "crafting":
      return {
        grid: renderCraftingScreen(view.crafting, cols, rows),
        hud: ["CRAFTING", "", ""],
      };
    case "equipment":
      return {
        grid: renderEquipmentScreen(
          {
            loadout: view.loadout,
            slots: view.equipmentSlots,
            message: view.message,
          },
          cols,
          rows,
        ),
        hud: ["EQUIPMENT", "", ""],
      };
    case "dungeon": {
      if (!view.dungeon)
        return {
          grid: makeGrid(cols, rows),
          hud: ["DUNGEON", "", "No dungeon active"],
        };
      const alarm = view.dungeon.state.playerAlarm;
      return {
        grid: renderDungeonMap(view.dungeon, cols, rows),
        hud: renderDungeonUi(view.dungeon, cols, rows),
        colorFor: (line: string): string | undefined => {
          if (!line.startsWith("ALM:")) return undefined;
          if (alarm >= 100) return PALETTE.RED_BRIGHT;
          if (alarm >= 75) return PALETTE.YELLOW_AMBER;
          return undefined;
        },
      };
    }
    default: {
      const opt = MENU_OPTIONS[view.menuIndex];
      const label = opt ? opt.label.toUpperCase() : "WET RUN";
      return {
        grid: renderStubScreen(label, cols, rows),
        hud: ["STUB", "", "Coming soon — Tier 5+"],
      };
    }
  }
}
