/** Rendering for the screens that exist before (and around) a run.
 *
 * Refactoring Stage 3a-2 (2026-11-25). `draw` routes every frame, and the
 * branch that owns the pre-game screens was the largest single piece of it —
 * menu, jockey select, briefing, prep, mission select, the far-grid hub, plus
 * the crafting / equipment / dungeon / settings panels. `drawPrep` renders the
 * fixer's advance for both the pre-game path and the between-legs path, and
 * `formatMissionOption` is only ever used by the mission list, so they travel
 * together.
 *
 * `main.ts` is outside the balance harness's import graph, so e2e is the guard.
 * Behaviour is preserved exactly.
 */
import type {
  GamePhase,
  Ice,
  Inventory,
  EquipmentLoadout,
  Mission,
  ScreenKind,
} from "../core/types";
import type { Layout } from "../core/layout";
import type { MenuEntry } from "../renderer/menu";
import type { SettingsState } from "../renderer/settings";
import type { InfoMarket } from "../core/info_market";
import type { DungeonCrawler } from "../core/dungeon/dungeon_crawler";
import type { MaterialDef, Recipe } from "../core/state/crafting";
import type { AsciiRenderer } from "../renderer/canvas";
import { createTutorialOverlay } from "../renderer/tutorial";
import { EQUIP_SLOTS } from "../core/state/equipment";
import { JOCKEYS } from "../core/state/jockey";
import { PREP_OPTIONS, prepGrantFor } from "../core/state/prep";
import { readPrepWallet } from "../core/state/prep_wallet";
import { missionGradeOf } from "../core/combat/ice_scaling";
import { filterMissionsByUniverse } from "../core/missions_filter";
import { contractFor } from "../core/state/campaign";
import { missionIce } from "../core/state/mission_ice";
import { FAR_GRID_LOCKED_MESSAGE } from "../core/dungeon/far_grid_gate";
import { formatNavIndex } from "../renderer/nav_index";
import { getInitialSettingsState } from "../renderer/settings";
import { renderPrep } from "../renderer/prep";
import { renderJockeySelect } from "../renderer/jockey_select";
import { renderMissionBriefing } from "../renderer/menu_dialogue";
import { renderPreGameScreen } from "../renderer/pre_game_screen";
import { updateProgramRow } from "../input/touch";

/** What the pre-game renderers need from the game controller. */
export interface PreGameRenderHost {
  screen: ScreenKind;
  farGridUnlockedCache: boolean;
  _message: string;
  settingsState: SettingsState | null;
  selectedMission: number;
  selectedJockey: number;
  selectedMenuIndex: number;
  menuSelectionNormalized: boolean;
  tutorialActive: boolean;
  tutorialOverlay: ReturnType<typeof createTutorialOverlay> | null;
  hasSaveCache: boolean;
  saveMetaCache: { missionId: string; turnCount: number; savedAt: string } | null;
  inventory: Inventory;
  recipes: ReadonlyArray<Recipe>;
  materials: ReadonlyArray<MaterialDef>;
  infoMarket: InfoMarket;
  equipmentLoadout: EquipmentLoadout;
  dungeonCrawler: DungeonCrawler | null;
  missions: ReadonlyArray<Mission>;
  iceTypes: Readonly<Record<string, Ice>>;
  layout: Layout;
  prepCursor: number;
  renderer: AsciiRenderer;
  syncPhase(phase: GamePhase): void;
  normalizeMenuSelection(): void;
  visibleMenu(): ReadonlyArray<MenuEntry>;
  renderGraphicNovel(): void;
  fallbackSettings(): SettingsState;
}

function formatMissionOption(
  mission: Mission,
  index: number,
  language: import("../core/i18n.ts").Language = "en",
): string {
  const grade = `T${mission.grade_max}`;
  const credits = mission.rewards.credits.toLocaleString();
  const titleText =
    language === "ko" && mission.title_ko !== undefined && mission.title_ko.length > 0
      ? mission.title_ko
      : mission.title;
  return `${formatNavIndex(index)} ${titleText}  [${grade} | ${credits}cr]`;
}

/** The fixer's advance (ADR-0283 C · ADR-0318 (a)). */
export function drawPrep(host: PreGameRenderHost, mission: Mission): void {
    const grade = missionGradeOf(mission);
    updateProgramRow([]);
    host.renderer.render(
      renderPrep(
        {
          missionTitle: mission.title,
          grade,
          cursor: host.prepCursor,
          wallet: readPrepWallet(),
          options: PREP_OPTIONS.map((option) => {
            const grant = prepGrantFor(grade, option.id, readPrepWallet());
            return {
              id: option.id,
              label: option.label,
              amount: grant.total,
              fromWallet: grant.fromWallet,
              unit: option.id === "ice" ? "shield" : "HP",
              note: option.short,
            };
          }),
        },
        host.layout.cols,
        host.layout.rows,
      ),
      ["PREP", "", `T${grade}`],
    );
}

/** The pre-game screens: no run state exists yet, so this routes by `screen`. */
export function drawPreGame(host: PreGameRenderHost): void {
      // Pre-game screen routing
      updateProgramRow([]); // hide row outside combat
      if (host.tutorialActive && host.tutorialOverlay) {
        // Tutorial overlay takes priority
        const tutorialGrid = host.tutorialOverlay.render(host.layout.cols, host.layout.rows);
        host.renderer.render(tutorialGrid, ["TUTORIAL", "", ""]);
        host.syncPhase("menu");
        return;
      }
      if (host.screen === "far_grid_hub" && !host.farGridUnlockedCache) {
        host.screen = "menu";
        host._message = FAR_GRID_LOCKED_MESSAGE;
        host.syncPhase("menu");
        return;
      }
      if (host.screen === "settings") {
        if (host.settingsState === null || host.settingsState === undefined) {
          try {
            host.settingsState = getInitialSettingsState();
          } catch (e) {
            console.error("[Game] Failed to initialize settingsState in render:", e);
            host.settingsState = host.fallbackSettings();
          }
        }
      }
      if (host.screen === "graphic_novel") {
        host.renderGraphicNovel();
        return;
      }
      if (host.screen === "briefing") {
        // ADR-0317: the fixer hands over the job — the mission's story from
        // ADR-0316 — right before the advance (prep) and the jack-in.
        const mission = host.missions[host.selectedMission];
        if (mission) {
          const language = host.settingsState?.language ?? "en";
          const story =
            (language === "ko" && mission.briefing_ko) ||
            mission.briefing ||
            "No briefing on file. Jack in and see for yourself.";
          updateProgramRow([]);
          host.renderer.render(
            renderMissionBriefing(
              mission.title,
              mission.fixer,
              story,
              host.layout.cols,
              host.layout.rows,
            ),
            ["BRIEFING", "", "ENTER: continue"],
          );
          return;
        }
      }
      if (host.screen === "prep") {
        const mission = host.missions[host.selectedMission];
        if (mission) {
          drawPrep(host, mission);
          return;
        }
      }
      if (host.screen === "jockey_select") {
        updateProgramRow([]);
        host.renderer.render(
          renderJockeySelect(host.selectedJockey, host.layout.cols, host.layout.rows),
          ["JOCKEY", "", `${host.selectedJockey + 1}/${JOCKEYS.length}`],
        );
        return;
      }
      if (host.screen === "menu") host.normalizeMenuSelection();
      else host.menuSelectionNormalized = false;
      const language = host.settingsState?.language ?? "en";
      const view = renderPreGameScreen(
        {
          screen: host.screen,
          menuIndex: host.selectedMenuIndex,
          menuOptions: host.visibleMenu(),
          missionIndex: host.selectedMission,
          missionRows:
            host.screen === "mission_select"
              ? filterMissionsByUniverse(host.missions, "sprawl").map((m, i) =>
                  formatMissionOption(m, i, language),
                )
              : [],
          // ADR-0316: the story the mission carries, lifted from the derivative
          // fiction, so the screen says what it is about.
          missionBriefing: (() => {
            if (host.screen !== "mission_select") return null;
            const m = filterMissionsByUniverse(host.missions, "sprawl")[host.selectedMission];
            if (!m) return null;
            return (language === "ko" && m.briefing_ko) || m.briefing || null;
          })(),
          // ADR-0318: a mission pick starts a three-mission contract, and the
          // grade in the row is the contract's whole shape. Say it — a contract
          // that completes 2.5% of the time must not look like a 51% mission
          // (owner principle: no choice whose meaning cannot be grasped).
          missionContract: (() => {
            if (host.screen !== "mission_select") return null;
            const m = filterMissionsByUniverse(host.missions, "sprawl")[host.selectedMission];
            if (!m) return null;
            const contract = contractFor(m, host.missions, (x) => missionIce(x, host.iceTypes));
            const grades = contract.legs.map((leg) => `T${missionGradeOf(leg.mission)}`);
            return `CONTRACT: ${contract.legs.length} missions · ${grades.join("→")}`;
          })(),
          farGridMissions:
            host.screen === "far_grid_hub" ? filterMissionsByUniverse(host.missions, "far-grid") : [],
          hasSave: host.hasSaveCache,
          saveMeta: host.saveMetaCache,
          message: host._message,
          farGridUnlocked: host.farGridUnlockedCache,
          language,
          settings: host.settingsState ?? host.fallbackSettings(),
          crafting: {
            inventory: host.inventory,
            recipes: host.recipes,
            materials: host.materials,
            marketItemCount: host.screen === "crafting" ? host.infoMarket.allItems().length : 0,
            message: host._message,
          },
          loadout: host.equipmentLoadout,
          equipmentSlots: EQUIP_SLOTS,
          dungeon: host.dungeonCrawler,
        },
        host.layout.cols,
        host.layout.rows,
      );
      host.renderer.render(view.grid, view.hud, view.colorFor);
      if (host.screen === "dungeon") return;
      host.syncPhase("menu");
      return;
}
