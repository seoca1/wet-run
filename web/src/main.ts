import { AsciiRenderer } from "./renderer/canvas";
import { KeyboardInput } from "./input/keyboard";
import { GamepadInput, isGamepadConnected } from "./input/gamepad";
import {
  mountVirtualGamepad,
  updateProgramRow,
  isTouchDevice,
} from "./input/touch";
import { MENU_OPTIONS, type MenuOption } from "./renderer/menu";
import { renderPreGameScreen } from "./renderer/pre_game_screen";
import {
  renderRunScreen,
  renderCombatScreen,
  composeCombatScreen,
} from "./renderer/run_screen";
import {
  beginMatrixTravel,
  matrixTravelFrame,
  type MatrixTravel,
} from "./renderer/matrix_travel";
import { renderCombatHints } from "./renderer/combat_hints";
import { filterMissionsByUniverse } from "./core/missions_filter";
import {
  FAR_GRID_LOCKED_MESSAGE,
  isFarGridUnlocked,
} from "./core/dungeon/far_grid_gate";
import {
  advanceVfxListBy,
  WEB_TICK_MS,
  type CombatVfxInstance,
} from "./renderer/combat_vfx";
import { hitStopActiveAt, hitStopDeadlineFor } from "./renderer/screen_shake";
import { pickTransitionSfx } from "./core/combat/combat_sfx";
import {
  programAffordances,
  rewardAffordances,
} from "./core/combat/program_affordance";
import { idleAlarmAction } from "./core/combat/idle_alarm";
import { startingDeck } from "./core/state/starting_deck";
import {
  beginLootCommit,
  beginMatrixArrival,
  lootCommitStage,
  matrixArrivalActive,
  resolveGrowthReveal,
  type LootCommit,
  type MatrixArrival,
} from "./renderer/growth_reveal";
import { offeredCardIds, rewardProgram } from "./core/state/card_reward";
import { programEffectTag } from "./core/combat/program_effects";
import { everyProgramBlocked } from "./core/combat/program_affordance";
import { renderRunIntro } from "./renderer/run_intro";
import { renderJockeySelect } from "./renderer/jockey_select";
import { JOCKEYS, jockeyHandle } from "./core/state/jockey";
import { tick as gnTick } from "./core/graphic_novel/graphic_novel_player";
import type { ArcId } from "./core/combat/ending_resolver";
import { FpsCounter, getMetrics } from "./core/state/performance";
import { createTutorialOverlay, resetTutorial } from "./renderer/tutorial";
import {
  combatEntryHintFits,
  shouldAutoShowTutorial,
  shouldShowMatrixEntryHint,
} from "./core/state/onboarding";
import {
  IDLE_PRESS_FEEDBACK,
  expirePressFeedback,
  hasPressFeedback,
  pressFeedbackLabel,
  pressProgramButton,
  type PressFeedbackState,
} from "./core/state/touch_feedback";
import {
  DungeonCrawler,
  createDungeonCrawlerFromMission,
} from "./core/dungeon/dungeon_crawler";
import {
  getInitialSettingsState,
  persistLanguage,
  cycleLanguage,
  adjustVolume,
  type SettingsField,
} from "./renderer/settings";
import {
  loadColorblindMode,
  loadHighContrastOverride,
  loadReducedMotionOverride,
  loadTextScale,
  nextColorblindMode,
  nextTextScale,
  previousTextScale,
  persistColorblindMode,
  persistHighContrastOverride,
  persistReducedMotionOverride,
  persistTextScale,
  resolveHighContrast,
  resolveReducedMotion,
  textScaleFactor,
  type ColorblindMode,
  type TextScaleStep,
} from "./renderer/accessibility_modes";
import { applyPaletteMode } from "./renderer/palette";
import { bootPwaController, type PwaController } from "./core/pwa_boot";
import type {
  GameState,
  GameAction,
  GamePhase,
  Ice,
  Mission,
  Program,
  ScreenKind,
  Inventory,
  EquipmentLoadout,
} from "./core/types";
import {
  applyAction,
  makeInitialState,
  resolveProgramSelection,
  slotToGameState,
  stateToSaveSlot,
} from "./core/state/state";
import {
  openArrivalEncounter,
  runAbandoned,
} from "./core/state/encounter_verbs";
import { missionIce } from "./core/state/mission_ice";
import { applyPrep } from "./core/state/prep";
import {
  autosaveIntent,
  FLATLINE_MESSAGE,
  isTerminalNode,
  runCompleted,
  runFailed,
  RUN_COMPLETE_MESSAGE,
} from "./core/state/run_end";
import { makeGrid, type Grid } from "./core/grid";
import {
  save as saveToSlot,
  load as loadFromSlot,
  clear as clearSlot,
  hasSave as slotHasSave,
  getSaveMeta,
} from "./save/storage";
import { getLayout, watchLayout, type Layout } from "./core/layout";
import {
  craftItem,
  makeRecipesFromData,
  makeMaterialsFromData,
  type Recipe,
  type MaterialDef,
  makeInfoMarket,
} from "./core/state/crafting";
import {
  equipOn,
  DEFAULT_REGISTRY,
  EQUIP_SLOTS,
  makeLoadout,
} from "./core/state/equipment";
import type { InfoMarket } from "./core/info_market";
import { loadPersistedLanguage } from "./renderer/settings";
import { formatNavIndex } from "./renderer/nav_index";

function fallbackSettingsState(): import("./renderer/settings.ts").SettingsState {
  return {
    selectedField: "audio",
    audioEnabled: !isAudioOff(),
    masterVolume: 1,
    bgmVolume: 0.4,
    sfxVolume: 0.6,
    muted: false,
    language: loadPersistedLanguage(),
    storageQuota: { state: "unavailable", reason: "not yet fetched" },
    pwa: {
      canInstall: false,
      isInstalled: false,
      isOffline: false,
      hasUpdate: false,
      deferredPrompt: null,
    },
    reducedMotion: resolveReducedMotion(loadReducedMotionOverride()),
    highContrast: resolveHighContrast(loadHighContrastOverride()),
    colorblindMode: loadColorblindMode(),
    textScale: loadTextScale(),
  };
}

const loadStorySystem = () => import("./core/graphic_novel/graphic_novel.ts");

/** Pre-game screens that handle their own keys (ADR-0275). A screen missing
 * from this set is a stub: no run state, ENTER returns to the title. Adding a
 * screen means adding it here, in one place, with a handler. */
const SCREENS_WITH_INPUT: ReadonlySet<ScreenKind> = new Set([
  "menu",
  "mission_select",
  "jockey_select",
  "tutorial",
  "settings",
  "dungeon",
  "pause",
  "graphic_novel",
]);
const loadAudioSystemRaw = () => import("./audio/manager.ts");

/** P9 render loop — maximum frame interval (ms) that still advances VFX.
 *
 * A longer frame (GC pause, background-tab wake-up) is a stall: the VFX
 * advance is skipped so instances do not all expire at once on a huge delta.
 */
const MAX_FRAME_ADVANCE_MS = 100;

function isAudioOff(): boolean {
  return localStorage.getItem("wetrun_audio_off") === "1";
}
const loadAudioSystem = () =>
  isAudioOff() ? Promise.resolve(null) : loadAudioSystemRaw();

import missionsData from "./data/missions.json" with { type: "json" };
import programsData from "./data/programs.json" with { type: "json" };
import iceTypesData from "./data/ice_types.json" with { type: "json" };
import {
  loadMissionsCatalog,
  loadProgramsCatalog,
  loadIceCatalog,
} from "./core/data_loaders";

/** Mission catalog (validated at module load — schema mismatches throw early). */
const MISSIONS: ReadonlyArray<Mission> = loadMissionsCatalog(missionsData);

/** Programs catalog (validated). Field aliases (ap_cost → cost) normalized. */
const PROGRAMS: Readonly<Record<string, Program>> =
  loadProgramsCatalog(programsData);

/** ICE types catalog (validated). Field aliases (defense → armor) normalized. */
const ICE_TYPES: Readonly<Record<string, Ice>> = loadIceCatalog(iceTypesData);

/** Format a mission for the select screen (Tier 2a). */
function formatMissionOption(
  mission: Mission,
  index: number,
  language: import("./core/i18n.ts").Language = "en",
): string {
  const grade = `T${mission.grade_max}`;
  const credits = mission.rewards.credits.toLocaleString();
  const titleText =
    language === "ko" &&
    mission.title_ko !== undefined &&
    mission.title_ko.length > 0
      ? mission.title_ko
      : mission.title;
  return `${formatNavIndex(index)} ${titleText}  [${grade} | ${credits}cr]`;
}

class Game {
  private state: GameState | null = null;
  private screen: ScreenKind = "menu";
  private selectedMenuIndex = 0;
  private selectedMission = 0;
  /** ADR-0274 — the jockey chosen for the next run (index into JOCKEYS). */
  private selectedJockey = 0;
  private renderer: AsciiRenderer;
  private input: KeyboardInput;
  private gamepad: GamepadInput;
  private iceTypes: Readonly<Record<string, Ice>>;
  private programs: Readonly<Record<string, Program>>;
  private missions: ReadonlyArray<Mission>;
  private hasSaveCache: boolean = false;
  private saveMetaCache: {
    missionId: string;
    turnCount: number;
    savedAt: string;
  } | null = null;
  private unmountTouch: () => void = () => {};
  private unwatchLayout: () => void = () => {};
  private _lastPhase: GamePhase | null = null;
  private _lastIceHp: number | null = null;
  private _lastPlayerHp: number | null = null;
  private inventory: Inventory;
  private equipmentLoadout: EquipmentLoadout;
  private recipes: ReadonlyArray<Recipe>;
  private materials: ReadonlyArray<MaterialDef>;
  private infoMarket: InfoMarket;
  private layout: Layout;
  private tutorialActive = false;
  private tutorialOverlay: ReturnType<typeof createTutorialOverlay> | null =
    null;
  /** P11 — the combat-entry hint is shown once per run, on the first combat
   * screen the player reaches. */
  private combatEntryHintShown = false;
  /** The Matrix-entry hint, same once-per-session pattern: shown on the
   * first board with a route, dismissed by the first input made there. */
  private matrixEntryHintShown = false;
  /** The Matrix board's traversal after a confirmed move: visual only and
   * never on `GameState`, so it is neither saved nor seen by the reducer.
   * Null under reduced motion, and replaced by the next input. */
  private matrixTravel: MatrixTravel | null = null;
  /** ADR-0262 — display-only growth reveal. Controller-owned and transient:
   * never on `GameState`, so it cannot reach a save, the reducer or the
   * harness. The `matrixTravel` pattern, applied to a card joining the deck. */
  private lootCommit: LootCommit | null = null;
  private matrixArrival: MatrixArrival | null = null;
  /** ADR-0272 — the arc's framing beat, shown once when a run starts. Null
   * when there is no run, or once a key has dismissed it. Never saved, so a
   * resumed run does not replay its introduction. */
  private runIntroArc: ArcId | null = null;
  /** The commit stage last drawn — the loop redraws only when the clock
   * pushes the panel to a new stage, then stops (ADR-0262). */
  private lootCommitStageShown = -1;
  /** ADR-0252: slot-0 writes and the retirement run in order. */
  private persistQueue: Promise<void> = Promise.resolve();
  private lastPersistedState: GameState | null = null;
  /** P10 — effective reduced-motion state. True suppresses the P1 canvas
   * shake and the hit-stop hold. */
  private reducedMotion = false;
  /** P10 — effective high-contrast state. */
  private highContrast = false;
  /** P10 — the active colorblind palette mode (ADR-0196). */
  private colorblindMode: ColorblindMode = "none";
  /** P10 — the active text-scale step. */
  private textScale: TextScaleStep = "medium";
  /** P12 — the in-game acknowledgement of a touch program-button press. */
  private pressFeedback: PressFeedbackState = IDLE_PRESS_FEEDBACK;
  /** ADR-0251 — name of the program the acknowledged tap played. */
  private pressedProgramName: string | null = null;
  /** ADR-0251 — true while the touch overlay (and its program row) is up. */
  private touchOverlayMounted = false;
  private graphicNovelPlayer:
    import("./core/graphic_novel/graphic_novel.ts").GraphicNovelPlayer | null =
    null;
  private gnLanguage: import("./core/graphic_novel/graphic_novel_types.ts").Language =
    "en";
  private graphicNovelState:
    import("./core/types.ts").GraphicNovelState | null = null;

  private settingsState: import("./renderer/settings.ts").SettingsState | null =
    null;
  private pwaController: PwaController | null = null;
  private dungeonCrawler: DungeonCrawler | null = null;
  private _message: string = "";
  private farGridUnlockedCache: boolean = false;
  private rafId: number | null = null;
  private loopRunning = false;
  private lastLoopMs = 0;
  private idleSinceMs = Date.now();
  /** Wall-clock deadline of the active P1 hit-stop hold (0 = none). */
  private hitStopDeadlineMs = 0;
  /** The VFX instance list from the previous frame — the hit-stop uses it to
   * detect a *newly appeared* `player_hit` without reading `elapsedMs`. */
  private previousVfxInstances: ReadonlyArray<CombatVfxInstance> = [];
  private readonly fpsCounter = new FpsCounter();

  constructor(
    canvas: HTMLCanvasElement,
    iceTypes: Readonly<Record<string, Ice>>,
  ) {
    this.iceTypes = iceTypes;
    this.programs = PROGRAMS;
    this.missions = MISSIONS;
    this.layout = getLayout();
    this.renderer = new AsciiRenderer(canvas, { cellWidth: 8, cellHeight: 16 });
    this.layout = this.renderer.resizeGrid(
      this.layout.cols,
      this.layout.rows,
      this.layout.hudCols,
      this.layout.orientation,
      this.layout.breakpoint,
    );
    // Ensure canvas can receive focus for keyboard input (especially on mobile/e-ink)
    canvas.tabIndex = 0;
    canvas.addEventListener("click", () => canvas.focus());
    canvas.addEventListener("touchstart", () => canvas.focus(), {
      passive: true,
    });
    this.input = new KeyboardInput();
    this.gamepad = new GamepadInput();
    this.inventory = { credits: 0, materials: {}, programs: [] };
    this.equipmentLoadout = makeLoadout();
    this.recipes = makeRecipesFromData({});
    this.materials = makeMaterialsFromData({});
    this.infoMarket = makeInfoMarket({});
    // Initialize settings state synchronously at construction time with robust fallback
    try {
      this.settingsState = getInitialSettingsState();
    } catch (e) {
      console.error("[Game] Failed to initialize settingsState:", e);
      this.settingsState = fallbackSettingsState();
    }
    // PWA controller is booted in `boot()` after the Game exists so the
    // subscriber can call `draw()`. Seed the PWA slot with the controller's
    // initial state once it's available; until then leave the default shape.
    // Ensure settingsState is never null/undefined
    if (!this.settingsState) {
      this.settingsState = fallbackSettingsState();
    }
    // P10 — apply the persisted accessibility settings. This must happen
    // before the first frame so the boot screen already honours them.
    this.applyAccessibilitySettings();
    // ADR-0213 Phase 2: load Far Grid unlock cache synchronously. localStorage
    // read is cheap and synchronous — no need for async refresh.
    this.farGridUnlockedCache = isFarGridUnlocked();
    void this.refreshSaveCache();
    const resetIdle = (): void => {
      this.idleSinceMs = Date.now();
    };
    document.addEventListener("keydown", resetIdle);
    document.addEventListener("pointerdown", resetIdle);
    document.addEventListener("visibilitychange", resetIdle);
    const handler = (action: GameAction): void => {
      resetIdle();
      // Screens that own their input. This used to be an inline list of
      // screens to *exclude*, so any screen someone forgot to add fell into
      // `handleStubInput` and ENTER bounced to the menu -- which is exactly
      // what happened to the graphic novel (ADR-0273) and then to the jockey
      // select (ADR-0274) in the same session. Anything with no run state that
      // is not in this set is a stub, by construction.
      if (this.state === null && !SCREENS_WITH_INPUT.has(this.screen)) {
        this.handleStubInput(action);
        return;
      }
      if (this.tutorialActive && this.tutorialOverlay) {
        const result = this.tutorialOverlay.handleInput(
          action.type === "jack_out" || action.type === "cancel"
            ? "Escape"
            : action.type === "confirm"
              ? "Enter"
              : action.type,
        );
        if (result.action === "next" || result.action === "skip") {
          if (
            result.action === "skip" ||
            this.tutorialOverlay.state.currentStep >= 6
          ) {
            this.tutorialActive = false;
            this.tutorialOverlay = null;
            this.screen = "menu";
          }
          this.draw();
        }
        return;
      }
      // Dungeon crawler has its own self-contained state (DungeonCrawler instance);
      // it must be handled before the `state === null` pre-game shortcut.
      if (this.screen === "dungeon") {
        this.handleDungeonInput(action);
        this.draw();
        return;
      }
      // ADR-0273: the graphic novel is its own screen with its own keys. The
      // renderer had always printed "ENTER: skip dialogue | P: pause | ESC:
      // exit", but nothing routed them: the mode showed one frame and ENTER
      // fell through to the menu, so the prologue could not be read at all.
      if (this.screen === "graphic_novel") {
        this.handleGraphicNovelInput(action);
        return;
      }
      if (this.state === null) {
        this.handlePreGameInput(action);
        return;
      }
      if (this.screen === "crafting" || this.screen === "equipment") {
        if (this.screen === "crafting") this.handleCraftingInput(action);
        else this.handleEquipmentInput(action);
        this.draw();
        return;
      }
      if (this.screen === "settings") {
        this.handleSettingsInput(action);
        this.draw();
        return;
      }
      if (this.screen === "pause") {
        this.handlePauseInput(action);
        this.draw();
        return;
      }
      // ADR-0272: the opening beat consumes the first key. It is a screen, not
      // an animation gate: nothing advances on its own and nothing is queued.
      if (this.runIntroArc !== null) {
        this.runIntroArc = null;
        this.draw();
        return;
      }
      const resolved: GameAction = (() => {
        if (this.state === null) return action;
        const r = resolveProgramSelection(this.state, action);
        return r ?? action;
      })();
      const previous = this.state;
      if (shouldShowMatrixEntryHint(this.matrixEntryHintShown, this.state))
        this.matrixEntryHintShown = true;
      this.state = applyAction(this.state, resolved);
      if (runAbandoned(previous, this.state)) {
        // JACK OUT ends the run: leave the board for the main menu.
        this.state = null;
        this.matrixTravel = null;
        this.lootCommit = null;
        this.matrixArrival = null;
        this.screen = "menu";
        void this.refreshSaveCache();
        this.draw();
        return;
      }
      if (runCompleted(previous, this.state)) {
        // ADR-0252: the ending is the end. The slot was retired on arrival.
        this.state = null;
        this.matrixTravel = null;
        this.lootCommit = null;
        this.matrixArrival = null;
        this.screen = "menu";
        this._message = RUN_COMPLETE_MESSAGE;
        this.persistQueue = this.persistQueue
          .then(() => this.refreshSaveCache())
          .catch(() => undefined);
        this.draw();
        return;
      }
      if (runFailed(previous, this.state)) {
        // ADR-0263: a flatline must not trap the player. ENTER / ESC leave the
        // defeat screen and the run ends at the title, the same shape as the
        // ending. The dead frame itself was already autosaved (ADR-0252 §A).
        this.state = null;
        this.matrixTravel = null;
        this.lootCommit = null;
        this.matrixArrival = null;
        this.screen = "menu";
        this._message = FLATLINE_MESSAGE;
        void this.refreshSaveCache();
        this.draw();
        return;
      }
      // The reducer has already moved `@`; this only chooses the next frames.
      // Every input re-derives it, so input never waits on (or redirects) it.
      this.matrixTravel = beginMatrixTravel(
        previous,
        this.state,
        performance.now(),
        this.reducedMotion,
      );
      this.syncGrowthReveal(previous, this.state);
      void loadAudioSystem().then((audio) => {
        if (!audio) return;
        const manager = audio.AudioManager.getInstance();
        // P5 — the player taking damage had no sound at all (proposal §1.2
        // U13). `pickTransitionSfx` decides the transition's audio from the
        // (previous → next) state pair: the combat layers plus the ADR-0251
        // event ids (boss intro / phase change, credits, loot, heal, death).
        const nextState = this.state;
        if (nextState !== null) {
          for (const id of pickTransitionSfx(previous, nextState)) {
            manager.playSfx(id);
          }
        }
        if (
          resolved.type === "use_program" &&
          previous.phase === "combat" &&
          this.state?.phase === "combat"
        ) {
          // The ICE-hit sound now comes from `pickTransitionSfx` above.
          // The old `state.ice.hp` delta check was provably dead — the
          // reducers only ever write `iceRoster`, so `state.ice.hp` never
          // changed after init and `COMBAT_HIT` never fired from here.
          const iceDelta = this.state.ice.hp - previous.ice.hp;
          // (The boss-phase sound used to sit in this dead branch as
          // VICTORY; `pickTransitionSfx` now plays PHASE_CHANGE for it.)
          if (iceDelta < 0) {
            this._lastIceHp = this.state.ice.hp;
            this._lastPlayerHp = this.state.player.hp;
          }
          if (
            previous.runPhase === "matrix" &&
            this.state.runPhase === "combat"
          ) {
            manager.playSfx(audio.SFX_IDS.COMBAT_HIT);
          }
          const burnTickDmg = this.state.player.hp - previous.player.hp;
          if (
            burnTickDmg > 0 &&
            previous.runPhase === "combat" &&
            this.state.runPhase === "combat"
          ) {
            manager.playSfx(audio.SFX_IDS.DEFEAT);
          }
        }
      });
      this.draw();
    };
    this.input.setHandler(handler);
    this.input.start();
    if (isTouchDevice()) {
      this.unmountTouch = mountVirtualGamepad(handler);
      this.touchOverlayMounted = true;
    }
    this.gamepad.setHandler(handler);
    this.gamepad.start();
    this.unwatchLayout = watchLayout((next) => {
      this.layout = this.renderer.resizeGrid(
        next.cols,
        next.rows,
        next.hudCols,
        next.orientation,
        next.breakpoint,
      );
      this.draw();
    });
  }

  private handleCraftingInput(action: GameAction): void {
    if (action.type === "jack_out" || action.type === "cancel") {
      this.screen = "menu";
      this._message = "";
      this.draw();
      return;
    }
    if (action.type === "select_program") {
      const index = action.handIndex - 1;
      if (index < 0) return;
      // Build list of craftable recipes (those with sufficient materials).
      const craftable: Recipe[] = [];
      for (const recipe of this.recipes) {
        let canCraft = true;
        for (const [mat, qty] of Object.entries(recipe.materials)) {
          if (this.inventory.materials[mat] ?? 0 < qty) {
            canCraft = false;
            break;
          }
        }
        if (canCraft) craftable.push(recipe);
      }
      if (index >= craftable.length) {
        this._message = "No craftable recipe at that slot.";
        this.draw();
        return;
      }
      const recipe = craftable[index];
      if (!recipe) {
        this.draw();
        return;
      }
      // Use real craftItem API: (recipes, itemId, inventory).
      const result = craftItem(
        this.recipes,
        recipe.itemId,
        this.inventory.materials,
      );
      if (result.ok) {
        // Update inventory: deduct materials + grant credits back is unchanged.
        // Crafting yields a virtual program entry; map craftedItemId back into inventory.programs.
        const craftedProgram: Program = {
          id: result.craftedItemId,
          name: recipe.name,
          tier: recipe.tierLevel,
          cost: 0,
          effect: "craft",
          description: `Crafted from recipe ${recipe.name}`,
          aoe: false,
        };
        this.inventory = {
          ...this.inventory,
          materials: result.newInventory,
          programs: [...this.inventory.programs, craftedProgram],
        };
        this._message = `Crafted ${recipe.name}!`;
      } else {
        this._message = `Failed to craft ${recipe.name}: ${result.reason}`;
      }
      this.draw();
      return;
    }
  }

  private handleEquipmentInput(action: GameAction): void {
    if (action.type === "jack_out" || action.type === "cancel") {
      this.screen = "menu";
      this._message = "";
      this.draw();
      return;
    }
    if (action.type === "select_program") {
      const slotIndex = action.handIndex - 1;
      if (slotIndex < 0 || slotIndex >= EQUIP_SLOTS.length) return;
      const slot = EQUIP_SLOTS[slotIndex];
      if (!slot) {
        this.draw();
        return;
      }
      // Find the first equipment for this slot in the default registry that isn't already equipped.
      const candidate = DEFAULT_REGISTRY.all.find(
        (e) => e.slot === slot && this.equipmentLoadout.get(slot) === null,
      );
      if (!candidate) {
        this._message = `No available equipment for slot ${slot}`;
        this.draw();
        return;
      }
      const result = equipOn(this.equipmentLoadout, candidate);
      this.equipmentLoadout = result.loadout;
      this._message = `Equipped ${candidate.name} to ${slot}`;
      this.draw();
      return;
    }
  }

  private handleDungeonInput(action: GameAction): void {
    if (!this.dungeonCrawler) return;

    switch (action.type) {
      case "move_north":
      case "move_south":
      case "move_east":
      case "move_west": {
        const dx =
          action.type === "move_east"
            ? 1
            : action.type === "move_west"
              ? -1
              : 0;
        const dy =
          action.type === "move_south"
            ? 1
            : action.type === "move_north"
              ? -1
              : 0;
        this.dungeonCrawler.tryMovePlayer(dx, dy);
        // Drive monster AI + FOV update each player turn.
        this.dungeonCrawler.processTurn();
        if (this.dungeonCrawler.isGameOver()) {
          this._message = "FLATLINE — dungeon crawl failed";
          this.screen = "menu";
          this.dungeonCrawler = null;
        }
        break;
      }
      case "confirm":
        this.dungeonCrawler.confirm();
        break;
      case "cancel":
        this.dungeonCrawler.cancel();
        break;
      case "jack_out":
        this.screen = "menu";
        this.dungeonCrawler = null;
        this.draw();
        return;
      default:
        break;
    }
    this.draw();
  }

  private handleSettingsInput(action: GameAction): void {
    if (action.type === "cancel" || action.type === "jack_out") {
      this.screen = "menu";
      this.draw();
      return;
    }
    if (action.type === "confirm") {
      // Toggle settings
      this.draw();
    }
  }

  private handlePauseInput(action: GameAction): void {
    if (action.type === "cancel" || action.type === "jack_out") {
      this.screen = "menu";
      this.draw();
      return;
    }
    if (action.type === "confirm") {
      this.screen = "settings";
      this.draw();
    }
  }

  private initGraphicNovel(): void {
    void loadStorySystem().then((gn) => {
      const player = gn.createPlayer({ mode: "novice" });
      this.graphicNovelPlayer = player;
      this.graphicNovelState = {
        player,
        currentScene: gn.currentScene(player),
        currentText: gn.currentText(player, this.gnLanguage),
        isPaused: false,
      };
      this.draw();
    });
  }

  private renderGraphicNovel(): void {
    if (!this.graphicNovelState || !this.graphicNovelPlayer) return;
    void loadStorySystem().then((gn) => {
      void import("./renderer/graphic_novel_screen.ts").then(
        ({ renderGraphicNovelScreen }) => {
          if (!this.graphicNovelState || !this.graphicNovelPlayer) return;
          const player = this.graphicNovelPlayer;

          const live = gn.currentScene(player);
          const grid = renderGraphicNovelScreen(
            {
              chapter: live
                ? {
                    order: live.order,
                    title: gn.currentTitle(player, this.gnLanguage),
                    speaker: gn.currentSpeaker(player, this.gnLanguage),
                  }
                : null,
              // Read from the player, not from the snapshot taken at entry:
              // the wall-clock tick advances it and the snapshot would be stale.
              text: gn.currentText(player, this.gnLanguage),
              dialogueText: gn.currentDialogue(player)?.text_en ?? null,
              progress: gn.progress(player),
              isPaused: player.paused,
              done: player.done,
            },
            this.layout.cols,
            this.layout.rows,
          );
          this.renderer.render(grid, ["GRAPHIC NOVEL", "", ""]);
        },
      );
    });
  }

  /** ADR-0273 — the graphic novel's keys, as its own footer promises. */
  private handleGraphicNovelInput(action: GameAction): void {
    const player = this.graphicNovelPlayer;
    if (!player) {
      this.exitGraphicNovel();
      return;
    }
    if (action.type === "jack_out" || action.type === "cancel") {
      this.exitGraphicNovel();
      return;
    }
    if (action.type === "cycle_target") {
      void loadStorySystem().then((gn) => {
        gn.togglePause(player);
        this.graphicNovelState = this.graphicNovelState
          ? { ...this.graphicNovelState, isPaused: player.paused }
          : this.graphicNovelState;
        this.draw();
      });
      return;
    }
    if (action.type !== "confirm") return;
    void loadStorySystem().then((gn) => {
      if (this.graphicNovelPlayer !== player) return;
      if (player.done) {
        this.startRunFromGraphicNovel();
        return;
      }
      // First press finishes the typed page, the next moves the story on.
      if (!gn.isDialogueComplete(player)) gn.skipCurrentDialogue(player);
      else if (!gn.advanceDialogue(player)) gn.advanceScene(player);
      this.draw();
    });
  }

  private exitGraphicNovel(): void {
    this.graphicNovelPlayer = null;
    this.graphicNovelState = null;
    this.screen = "menu";
    this.draw();
  }

  /** ADR-0273: the prologue's epilogue hands over to the run — "the next
   * jack" is the player. The arc intro (ADR-0272) then opens the run. */
  private startRunFromGraphicNovel(): void {
    this.graphicNovelPlayer = null;
    this.graphicNovelState = null;
    this.screen = "mission_select";
    this.selectedMission = 0;
    this.draw();
  }

  private handlePreGameInput(action: GameAction): void {
    // Digit keys 1-9 → menu selection on menu screen (otherwise → combat program select).
    if (action.type === "select_program" && this.screen === "menu") {
      const idx = action.handIndex - 1;
      if (idx >= 0 && idx < MENU_OPTIONS.length) {
        this.selectedMenuIndex = idx;
        const opt = MENU_OPTIONS[idx];
        this.selectMenuOption(opt ? opt.key : undefined);
      }
      return;
    }
    if (this.screen === "menu") {
      if (action.type === "move_south") {
        this.selectedMenuIndex =
          (this.selectedMenuIndex + 1) % MENU_OPTIONS.length;
        this.draw();
      } else if (action.type === "move_north") {
        this.selectedMenuIndex =
          (this.selectedMenuIndex - 1 + MENU_OPTIONS.length) %
          MENU_OPTIONS.length;
        this.draw();
      } else if (action.type === "confirm") {
        const opt = MENU_OPTIONS[this.selectedMenuIndex];
        this.selectMenuOption(opt ? opt.key : undefined);
      } else if (action.type === "jack_out") {
        // No-op: already at top-level menu
        this.draw();
      }
      return;
    }
    if (this.screen === "jockey_select") {
      if (action.type === "move_south") {
        this.selectedJockey = (this.selectedJockey + 1) % JOCKEYS.length;
        this.draw();
      } else if (action.type === "move_north") {
        this.selectedJockey =
          (this.selectedJockey - 1 + JOCKEYS.length) % JOCKEYS.length;
        this.draw();
      } else if (action.type === "confirm") {
        this.screen = "mission_select";
        this.selectedMission = 0;
        this.draw();
      } else if (action.type === "jack_out") {
        this.screen = "menu";
        this.draw();
      }
      return;
    }
    if (this.screen === "mission_select") {
      // ADR-0213 isolation: the Sprawl board lists sprawl-universe missions
      // only; far-grid missions live behind the gated hub.
      const sprawlMissions = filterMissionsByUniverse(MISSIONS, "sprawl");
      if (action.type === "move_south") {
        this.selectedMission =
          (this.selectedMission + 1) % sprawlMissions.length;
        this.draw();
      } else if (action.type === "move_north") {
        this.selectedMission =
          (this.selectedMission - 1 + sprawlMissions.length) %
          sprawlMissions.length;
        this.draw();
      } else if (action.type === "confirm") {
        const picked = sprawlMissions[this.selectedMission];
        const fullIndex = picked ? MISSIONS.indexOf(picked) : -1;
        if (fullIndex >= 0) {
          this.selectedMission = fullIndex;
          this.launchSelected();
        }
      } else if (action.type === "jack_out") {
        this.screen = "menu";
        this.draw();
      }
      return;
    }
    if (this.screen === "far_grid_hub") {
      // ADR-0213 Phase 2: defense in depth — if the unlock flag is missing,
      // bounce back to the main menu rather than running the hub.
      if (!this.farGridUnlockedCache) {
        this.screen = "menu";
        this._message = FAR_GRID_LOCKED_MESSAGE;
        this.draw();
        return;
      }
      const farGridMissions = filterMissionsByUniverse(MISSIONS, "far-grid");
      if (farGridMissions.length === 0) {
        if (action.type === "jack_out") {
          this.screen = "menu";
          this.draw();
        }
        return;
      }
      if (action.type === "move_south") {
        this.selectedMission =
          (this.selectedMission + 1) % farGridMissions.length;
        this.draw();
      } else if (action.type === "move_north") {
        this.selectedMission =
          (this.selectedMission - 1 + farGridMissions.length) %
          farGridMissions.length;
        this.draw();
      } else if (action.type === "confirm") {
        const picked = farGridMissions[this.selectedMission];
        const fullIndex = picked ? MISSIONS.indexOf(picked) : -1;
        if (fullIndex >= 0) {
          this.selectedMission = fullIndex;
          this.launchSelected();
        }
      } else if (action.type === "jack_out") {
        this.screen = "menu";
        this.draw();
      }
      return;
    }
    if (this.screen === "settings") {
      void loadAudioSystem().then(async (audio) => {
        if (!audio) return;
        const manager = audio.AudioManager.getInstance();
        // Ensure defaults are persisted
        if (localStorage.getItem("wetrun_audio_bgm_volume") === null) {
          manager.setBgmVolume(manager.getBgmVolume());
        }
        if (localStorage.getItem("wetrun_audio_sfx_volume") === null) {
          manager.setSfxVolume(manager.getSfxVolume());
        }
        if (this.settingsState === null) {
          this.settingsState = getInitialSettingsState();
        }
        if (this.settingsState.audioEnabled === undefined) {
          this.settingsState = {
            ...this.settingsState,
            audioEnabled: !isAudioOff(),
          };
        }
        const fields: ReadonlyArray<SettingsField> = [
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
        const idx = fields.indexOf(this.settingsState.selectedField);
        if (
          action.type === "cycle_target" ||
          action.type === "move_south" ||
          action.type === "move_north"
        ) {
          const direction = action.type === "move_north" ? -1 : 1;
          const nextIdx = (idx + direction + fields.length) % fields.length;
          const nextField = fields[nextIdx] ?? fields[0];
          if (nextField)
            this.settingsState = {
              ...this.settingsState,
              selectedField: nextField,
            };
          this.draw();
        } else if (action.type === "move_east") {
          if (this.settingsState.selectedField === "master") {
            const v = adjustVolume(this.settingsState.masterVolume ?? 1, "inc");
            this.settingsState = { ...this.settingsState, masterVolume: v };
            manager.setMasterVolume(v);
          } else if (this.settingsState.selectedField === "bgm") {
            const v =
              this.settingsState.bgmVolume + 0.1 > 1
                ? 1
                : Math.round((this.settingsState.bgmVolume + 0.1) * 10) / 10;
            this.settingsState = { ...this.settingsState, bgmVolume: v };
            manager.setBgmVolume(v);
          } else if (this.settingsState.selectedField === "sfx") {
            const v =
              this.settingsState.sfxVolume + 0.1 > 1
                ? 1
                : Math.round((this.settingsState.sfxVolume + 0.1) * 10) / 10;
            this.settingsState = { ...this.settingsState, sfxVolume: v };
            manager.setSfxVolume(v);
          } else if (this.settingsState.selectedField === "text_scale") {
            const next = nextTextScale(this.textScale);
            persistTextScale(next);
            this.textScale = next;
            this.renderer.setTextScale(textScaleFactor(next));
            this.resizeRenderer();
            this.settingsState = { ...this.settingsState, textScale: next };
          }
          this.draw();
        } else if (action.type === "move_west") {
          if (this.settingsState.selectedField === "master") {
            const v = adjustVolume(this.settingsState.masterVolume ?? 1, "dec");
            this.settingsState = { ...this.settingsState, masterVolume: v };
            manager.setMasterVolume(v);
          } else if (this.settingsState.selectedField === "bgm") {
            const v =
              this.settingsState.bgmVolume - 0.1 < 0
                ? 0
                : Math.round((this.settingsState.bgmVolume - 0.1) * 10) / 10;
            this.settingsState = { ...this.settingsState, bgmVolume: v };
            manager.setBgmVolume(v);
          } else if (this.settingsState.selectedField === "sfx") {
            const v =
              this.settingsState.sfxVolume - 0.1 < 0
                ? 0
                : Math.round((this.settingsState.sfxVolume - 0.1) * 10) / 10;
            this.settingsState = { ...this.settingsState, sfxVolume: v };
            manager.setSfxVolume(v);
          } else if (this.settingsState.selectedField === "text_scale") {
            const next = previousTextScale(this.textScale);
            persistTextScale(next);
            this.textScale = next;
            this.renderer.setTextScale(textScaleFactor(next));
            this.resizeRenderer();
            this.settingsState = { ...this.settingsState, textScale: next };
          }
          this.draw();
        } else if (action.type === "confirm") {
          if (this.settingsState.selectedField === "audio") {
            const newEnabled = !this.settingsState.audioEnabled;
            if (newEnabled) {
              localStorage.removeItem("wetrun_audio_off");
            } else {
              localStorage.setItem("wetrun_audio_off", "1");
            }
            this.settingsState = {
              ...this.settingsState,
              audioEnabled: newEnabled,
            };
          } else if (this.settingsState.selectedField === "mute") {
            const muted = manager.toggleMute();
            this.settingsState = { ...this.settingsState, muted };
          } else if (this.settingsState.selectedField === "language") {
            const next = cycleLanguage(this.settingsState.language);
            persistLanguage(next);
            this.settingsState = { ...this.settingsState, language: next };
          } else if (this.settingsState.selectedField === "pwa_install") {
            // ENTER fires the install prompt (user gesture). Only effective
            // when canInstall is true; the controller also clears the
            // deferredPrompt after a successful install.
            if (this.pwaController) {
              void this.pwaController.tryPromptInstall();
            }
          } else if (this.settingsState.selectedField === "pwa_update") {
            // ENTER triggers SKIP_WAITING. Controller sets hasUpdate=false on
            // success; the page should be reloaded to activate the new worker.
            if (this.pwaController) {
              void this.pwaController.tryApplyUpdate();
            }
          } else if (this.settingsState.selectedField === "reduced_motion") {
            // P10 — toggle reduced motion. The override wins over the OS
            // media query in both directions.
            const next = !this.reducedMotion;
            persistReducedMotionOverride(next);
            this.reducedMotion = next;
            this.settingsState = {
              ...this.settingsState,
              reducedMotion: next,
            };
          } else if (this.settingsState.selectedField === "high_contrast") {
            // P10 — toggle the high-contrast palette overrides.
            const next = !this.highContrast;
            persistHighContrastOverride(next);
            this.highContrast = next;
            applyPaletteMode(this.colorblindMode, next);
            this.settingsState = {
              ...this.settingsState,
              highContrast: next,
            };
          } else if (this.settingsState.selectedField === "colorblind") {
            // P10 — cycle the ADR-0196 4-mode colorblind palette.
            const next = nextColorblindMode(this.colorblindMode);
            persistColorblindMode(next);
            this.colorblindMode = next;
            applyPaletteMode(next, this.highContrast);
            this.settingsState = {
              ...this.settingsState,
              colorblindMode: next,
            };
          } else if (this.settingsState.selectedField === "text_scale") {
            // P10 — cycle the text scale and re-derive the cell geometry.
            const next = nextTextScale(this.textScale);
            persistTextScale(next);
            this.textScale = next;
            this.renderer.setTextScale(textScaleFactor(next));
            this.resizeRenderer();
            this.settingsState = {
              ...this.settingsState,
              textScale: next,
            };
          }
          this.draw();
        } else if (action.type === "jack_out") {
          this.screen = "menu";
          this.draw();
        }
      });
      return;
    }
  }

  private handleStubInput(action: GameAction): void {
    // Stub screens: ENTER/ESC/Q all return to main menu.
    if (action.type === "confirm" || action.type === "jack_out") {
      this.screen = "menu";
      this.draw();
    }
  }

  private async selectMenuOption(
    option: MenuOption | undefined,
  ): Promise<void> {
    if (!option) return Promise.resolve();
    switch (option) {
      case "new_run":
        // ADR-0274: choose the jockey first, so the run belongs to someone.
        this.screen = "jockey_select";
        this.selectedJockey = 0;
        this.draw();
        break;
      case "dungeon_crawl":
        this.startDungeonCrawl();
        break;
      case "continue":
        void this.handleContinue();
        break;
      case "craft":
        this.screen = "crafting";
        this._message = "";
        this.draw();
        break;
      case "equipment":
        this.screen = "equipment";
        this._message = "";
        this.draw();
        break;
      case "graphic_novel":
        this.screen = "graphic_novel";
        this.initGraphicNovel();
        this.draw();
        break;
      case "settings":
        this.screen = "settings";
        try {
          if (this.settingsState === null) {
            this.settingsState = getInitialSettingsState();
          }
        } catch (e) {
          console.error(
            "[Game] Failed to initialize settingsState on menu select:",
            e,
          );
          this.settingsState = fallbackSettingsState();
        }
        this.draw();
        break;
      case "tutorial":
        this.enterTutorial();
        break;
      case "far_grid_hub":
        // ADR-0213 Phase 2: FAR GRID is gated by Arc 1 clear. Defense in depth:
        // even if the screen was reached programmatically, we re-check here.
        if (!this.farGridUnlockedCache) {
          this._message = FAR_GRID_LOCKED_MESSAGE;
          this.screen = "menu";
          this.draw();
          break;
        }
        this.screen = "far_grid_hub";
        this.selectedMission = 0;
        this.draw();
        break;
      default:
        this._message = `${(option ?? "this option").toString().replace(/_/g, " ")} — coming soon in a future tier`;
        this.draw();
        break;
    }
  }

  /** Reload hasSave + meta caches from storage. Call after save/load/clear. */
  private async refreshSaveCache(): Promise<void> {
    this.hasSaveCache = await slotHasSave(0);
    this.saveMetaCache = await getSaveMeta(0);
    // Re-draw the title menu to reflect availability. In a run `screen` can
    // also be "menu" (after CONTINUE); redrawing it would re-trigger the
    // autosave and loop on every write.
    if (this.screen === "menu" && this.state === null) this.draw();
  }

  /** Load autosave (slot 0) and resume from saved state.
   *
   * Returns silently if no save exists (gated by hasSaveCache). On success,
   * transitions to the in-game state and resets _lastIceHp/_lastPlayerHp
   * so hit-flash VFX doesn't trigger immediately on resume.
   */
  private async handleContinue(): Promise<void> {
    if (!this.hasSaveCache) {
      // No save — show stub message (should be unreachable from menu but safe).
      this.draw();
      return;
    }
    const slot = await loadFromSlot(0);
    if (!slot) {
      // Stale cache: hasSave said true but load failed. Refresh + stub.
      await this.refreshSaveCache();
      this.draw();
      return;
    }
    const fallbackIce = Object.values(this.iceTypes)[0];
    if (!fallbackIce) {
      this.draw();
      return;
    }
    const restored = slotToGameState(
      slot,
      this.missions,
      this.programs,
      fallbackIce,
      this.iceTypes,
    );
    if (!restored) {
      // Mission no longer in catalog or all programs disappeared.
      this.draw();
      return;
    }
    this.state = {
      ...restored,
      grid: makeGrid(this.layout.cols, this.layout.rows),
    };
    this.screen = "menu"; // game-internal state; main screen renderer picks up state != null
    this._lastIceHp = restored.ice.hp;
    this._lastPlayerHp = restored.player.hp;
    this.draw();
  }

  private launchSelected(): void {
    const mission = MISSIONS[this.selectedMission];
    if (!mission) return;
    // A fresh run carries no reveal from the previous one (ADR-0262).
    this.lootCommit = null;
    this.matrixArrival = null;
    // ADR-0272: the run opens on the arc's framing beat. CONTINUE does not set
    // this (a resumed run is mid-story); only a fresh run does.
    this.runIntroArc = ((mission.arc as ArcId) || 1) as ArcId;
    const programs = PROGRAMS;
    // ADR-0276: the jockey decides the opening deck, not just the name.
    const deck = startingDeck(
      programs,
      JOCKEYS[this.selectedJockey]?.id ?? null,
    );
    const ice = missionIce(mission, this.iceTypes);
    const initial = makeInitialState(mission, ice, deck);
    this.state = openArrivalEncounter({
      ...applyPrep(initial),
      jockeyId: JOCKEYS[this.selectedJockey]?.id ?? null,
      grid: makeGrid(this.layout.cols, this.layout.rows),
      currentNodeIndex: 0,
      runPhase: "matrix",
      phase: "approach",
    });
    this.inventory = initial.inventory;
    this.equipmentLoadout = initial.equipmentLoadout;
    this.recipes = makeRecipesFromData({});
    this.materials = makeMaterialsFromData({});
    this.infoMarket = makeInfoMarket({});
    this.draw();
  }

  private startDungeonCrawl(): void {
    const mission = MISSIONS[0] ?? null;
    this.dungeonCrawler = createDungeonCrawlerFromMission(mission);
    this.screen = "dungeon";
    this.draw();
  }

  /** ADR-0252: write the rendered run state to slot 0, or retire the slot
   * once the run has reached its ending. Storage operations are chained so
   * a retirement can never be overtaken by an earlier, slower write. */
  private autosave(): void {
    const state = this.state;
    const intent = autosaveIntent(state);
    if (state === null || intent === "skip") return;
    if (state === this.lastPersistedState) return; // unchanged frame
    this.lastPersistedState = state;
    // Snapshot now: the slot must hold this frame, not a later one.
    const slot = intent === "write" ? stateToSaveSlot(state) : null;
    this.persistQueue = this.persistQueue
      .then(() => (slot === null ? clearSlot(0) : saveToSlot(0, slot)))
      .then(() => this.refreshSaveCache())
      .catch(() => {
        // Best-effort (fire-and-forget, ADR-0209); the chain must stay usable.
      });
  }

  /** Track the once-per-run hint; delegate drawing beneath the VFX layer. */
  private composeCombatOverlays(grid: Grid, previousPhase: GamePhase): Grid {
    const showHint =
      !this.combatEntryHintShown &&
      previousPhase !== "combat" &&
      this.state?.phase === "combat" &&
      combatEntryHintFits(this.layout.rows);
    let pressLabel: string | null = null;
    if (hasPressFeedback(this.pressFeedback)) {
      pressLabel = pressFeedbackLabel(
        this.pressFeedback,
        this.pressedProgramName ?? undefined,
      );
    }
    // ADR-0266: state the cap when it blocks every program, so the pass is
    // discoverable instead of the screen going quiet. Same predicate the
    // reducer uses, so the line cannot promise a key that does nothing.
    const costCapped =
      this.state?.phase === "combat" &&
      everyProgramBlocked(this.state) &&
      combatEntryHintFits(this.layout.rows);
    const out = renderCombatHints(grid, { showHint, pressLabel, costCapped });
    if (showHint) this.combatEntryHintShown = true;
    return out;
  }

  /** Render the current state. `persist` is false for render-loop frames:
   * a redraw must not trigger the autosave side effect. */
  private draw(persist: boolean = true): void {
    // ADR-0272: the run's opening beat owns the screen until a key dismisses
    // it. Display-only, static text — no clock, no animation, no save.
    if (this.runIntroArc !== null && this.state !== null) {
      updateProgramRow([]);
      this.renderer.render(
        renderRunIntro(
          this.runIntroArc,
          this.layout.cols,
          this.layout.rows,
          jockeyHandle(this.state?.jockeyId),
        ),
        ["JACK-IN", "", "ANY KEY"],
      );
      return;
    }
    // Tier 5: matrix / loot / ending screens render with a real GameState
    // but their UI is non-combat. Route by runPhase.
    if (
      this.state !== null &&
      ["matrix", "ending", "loot"].includes(this.state.runPhase)
    ) {
      // ADR-0252: a committed move, a won fight and the ending are saved
      // (or retire the slot) like combat frames are.
      if (persist) this.autosave();
      // ADR-0259: on a non-terminal loot screen the same row picks the card
      // reward, so touch players get the same choice as the digits.
      const rewards =
        this.state.runPhase === "loot" && !isTerminalNode(this.state)
          ? rewardAffordances(this.state)
          : [];
      updateProgramRow(
        rewards,
        rewards.length > 0 ? (i) => this.handleRewardButton(i) : undefined,
      );
      // A traversal frame (visual only) replaces the board for ~220 ms.
      const travel = matrixTravelFrame(this.matrixTravel, performance.now());
      const growth = resolveGrowthReveal(
        this.lootCommit,
        this.matrixArrival,
        performance.now(),
        this.reducedMotion,
      );
      // Remember which commit stage this frame drew, so the loop can tell
      // when the clock has moved the panel on (ADR-0262).
      this.lootCommitStageShown = growth?.lootCommit?.stage ?? -1;
      const view =
        travel === null
          ? renderRunScreen(
              this.state,
              this.layout.cols,
              this.layout.rows,
              shouldShowMatrixEntryHint(this.matrixEntryHintShown, this.state),
              null,
              growth,
            )
          : renderRunScreen(
              this.state,
              this.layout.cols,
              this.layout.rows,
              shouldShowMatrixEntryHint(this.matrixEntryHintShown, this.state),
              travel,
              growth,
            );
      if (view) this.renderer.render(view.grid, view.hud);
      return;
    }
    // In-game graphic novel screen (graphicNovel state populated).
    if (this.state !== null && this.screen === "graphic_novel") {
      this.renderGraphicNovel();
      return;
    }
    if (this.state === null) {
      // Pre-game screen routing
      updateProgramRow([]); // hide row outside combat
      if (this.tutorialActive && this.tutorialOverlay) {
        // Tutorial overlay takes priority
        const tutorialGrid = this.tutorialOverlay.render(
          this.layout.cols,
          this.layout.rows,
        );
        this.renderer.render(tutorialGrid, ["TUTORIAL", "", ""]);
        this.syncPhase("menu");
        return;
      }
      if (this.screen === "far_grid_hub" && !this.farGridUnlockedCache) {
        this.screen = "menu";
        this._message = FAR_GRID_LOCKED_MESSAGE;
        this.syncPhase("menu");
        return;
      }
      if (this.screen === "settings") {
        if (this.settingsState === null || this.settingsState === undefined) {
          try {
            this.settingsState = getInitialSettingsState();
          } catch (e) {
            console.error(
              "[Game] Failed to initialize settingsState in render:",
              e,
            );
            this.settingsState = fallbackSettingsState();
          }
        }
      }
      if (this.screen === "graphic_novel") {
        this.renderGraphicNovel();
        return;
      }
      if (this.screen === "jockey_select") {
        updateProgramRow([]);
        this.renderer.render(
          renderJockeySelect(
            this.selectedJockey,
            this.layout.cols,
            this.layout.rows,
          ),
          ["JOCKEY", "", `${this.selectedJockey + 1}/${JOCKEYS.length}`],
        );
        return;
      }
      const language = this.settingsState?.language ?? "en";
      const view = renderPreGameScreen(
        {
          screen: this.screen,
          menuIndex: this.selectedMenuIndex,
          missionIndex: this.selectedMission,
          missionRows:
            this.screen === "mission_select"
              ? filterMissionsByUniverse(MISSIONS, "sprawl").map((m, i) =>
                  formatMissionOption(m, i, language),
                )
              : [],
          farGridMissions:
            this.screen === "far_grid_hub"
              ? filterMissionsByUniverse(MISSIONS, "far-grid")
              : [],
          hasSave: this.hasSaveCache,
          saveMeta: this.saveMetaCache,
          message: this._message,
          farGridUnlocked: this.farGridUnlockedCache,
          language,
          settings: this.settingsState ?? fallbackSettingsState(),
          crafting: {
            inventory: this.inventory,
            recipes: this.recipes,
            materials: this.materials,
            marketItemCount:
              this.screen === "crafting"
                ? this.infoMarket.allItems().length
                : 0,
            message: this._message,
          },
          loadout: this.equipmentLoadout,
          equipmentSlots: EQUIP_SLOTS,
          dungeon: this.dungeonCrawler,
        },
        this.layout.cols,
        this.layout.rows,
      );
      this.renderer.render(view.grid, view.hud, view.colorFor);
      if (this.screen === "dungeon") return;
      this.syncPhase("menu");
      return;
    }
    // In-game (combat) rendering path.
    const previous = this.state;
    const iceDelta =
      this._lastIceHp !== null ? previous.ice.hp - this._lastIceHp : null;
    const playerDelta =
      this._lastPlayerHp !== null
        ? previous.player.hp - this._lastPlayerHp
        : null;
    this.state = {
      ...this.state,
      grid: this.composeCombatOverlays(
        renderCombatScreen(
          {
            state: this.state,
            iceDelta,
            playerDelta,
            handOnOverlay: this.touchOverlayMounted,
          },
          this.layout.cols,
          this.layout.rows,
        ),
        previous.phase,
      ),
    };
    const combatView = composeCombatScreen(this.state, this.reducedMotion);
    this.renderer.render(
      combatView.grid,
      combatView.hud,
      undefined,
      combatView.shake,
    );
    updateProgramRow(
      this.state.phase === "combat" ? programAffordances(this.state) : [],
      this.state.phase === "combat"
        ? (handIndex) => this.handleProgramButton(handIndex)
        : undefined,
    );
    if (persist) this.autosave();
    this.syncPhase(this.state.phase);
  }

  /** Re-derive the canvas surface from the current layout + text scale. */
  private resizeRenderer(): void {
    const base = getLayout();
    this.layout = this.renderer.resizeGrid(
      base.cols,
      base.rows,
      base.hudCols,
      base.orientation,
      base.breakpoint,
    );
  }

  /** P10 — read the persisted accessibility settings and apply them to the
   * renderer and the palette. Called at boot and after every settings
   * change, so a change is visible on the very next frame.
   *
   * Purely presentational: no reducer, clock or RNG is touched, so the
   * balance harness is unaffected (ADR-0229 §A1 does not trigger).
   */
  private applyAccessibilitySettings(): void {
    this.reducedMotion = resolveReducedMotion(loadReducedMotionOverride());
    this.highContrast = resolveHighContrast(loadHighContrastOverride());
    this.colorblindMode = loadColorblindMode();
    this.textScale = loadTextScale();
    applyPaletteMode(this.colorblindMode, this.highContrast);
    this.renderer.setTextScale(textScaleFactor(this.textScale));
    this.resizeRenderer();
    if (this.settingsState) {
      this.settingsState = {
        ...this.settingsState,
        reducedMotion: this.reducedMotion,
        highContrast: this.highContrast,
        colorblindMode: this.colorblindMode,
        textScale: this.textScale,
      };
    }
  }

  private syncPhase(current: GamePhase): void {
    if (this._lastPhase === current) return;
    const previous = this._lastPhase;
    this._lastPhase = current;
    void loadAudioSystem().then((audio) => {
      if (!audio) return;
      const manager = audio.AudioManager.getInstance();
      manager.playPhase(current);
      if (current === "victory" && previous !== "victory") {
        manager.playSfx(audio.SFX_IDS.VICTORY);
      } else if (current === "defeat" && previous !== "defeat") {
        manager.playSfx(audio.SFX_IDS.DEFEAT);
      } else if (current === "exit") {
        manager.stopAllSfx();
      }
    });
  }

  /** Start the continuous render loop (P9). Idempotent — a second call while
   * the loop is already running is a no-op, so the loop cannot double-start. */
  private startLoop(): void {
    if (this.loopRunning) return;
    this.loopRunning = true;
    this.lastLoopMs = 0;
    this.hitStopDeadlineMs = 0;
    this.previousVfxInstances = [];
    this.fpsCounter.reset();
    this.rafId = requestAnimationFrame(this.loop);
  }

  /** Render-loop frame. Advances VFX by the elapsed frame interval and
   * redraws only when an instance advanced to a new animation tick or expired. */
  private readonly loop = (now: number): void => {
    if (!this.loopRunning) return;
    this.rafId = requestAnimationFrame(this.loop);

    this.fpsCounter.tick();
    const deltaMs = this.lastLoopMs > 0 ? now - this.lastLoopMs : WEB_TICK_MS;
    this.lastLoopMs = now;

    if (
      this.state !== null &&
      ["menu", "mission_select", "far_grid_hub"].includes(this.screen) &&
      !this.tutorialActive &&
      !document.hidden
    ) {
      const tick = idleAlarmAction(this.state, this.idleSinceMs, Date.now());
      if (tick !== null) {
        this.state = applyAction(this.state, tick);
        this.draw(false);
      }
      if (this.state.runPhase !== "combat" || this.state.phase !== "combat")
        this.idleSinceMs = Date.now();
    } else {
      this.idleSinceMs = Date.now();
    }

    // ADR-0273: the graphic novel plays on the wall clock, like every other
    // display-only animation here. Redraw only when the story actually moved.
    if (
      this.screen === "graphic_novel" &&
      this.state === null &&
      this.graphicNovelPlayer !== null
    ) {
      const events = gnTick(this.graphicNovelPlayer, deltaMs);
      if (events.length > 0) this.draw(false);
    }

    // Matrix traversal frames run on the wall clock; the last one restores
    // the static board. Drawing only: the state already holds the arrival.
    if (this.matrixTravel !== null) {
      if (matrixTravelFrame(this.matrixTravel, now) === null)
        this.matrixTravel = null;
      if (this.state !== null) this.draw(false);
    }

    // ADR-0262 — the arrival note is a display-only window on the clock;
    // when it lapses the board redraws without it. No input is affected.
    if (
      this.matrixArrival !== null &&
      !matrixArrivalActive(this.matrixArrival, now)
    ) {
      this.matrixArrival = null;
      if (this.state !== null) this.draw(false);
    }

    // ADR-0262 — the commit panel steps through its fixed stages on the
    // clock. Redraw only when the clock moves it to a new stage, so it
    // settles into its final frame and then stops (no per-frame churn).
    if (
      this.lootCommit !== null &&
      lootCommitStage(this.lootCommit, now, this.reducedMotion) !==
        this.lootCommitStageShown
    ) {
      if (this.state !== null) this.draw(false);
    }

    // P12 — expire the touch press acknowledgement on the wall clock. This
    // runs before the VFX early-return so the acknowledgement clears even
    // when no VFX instance is alive.
    if (hasPressFeedback(this.pressFeedback)) {
      const expired = expirePressFeedback(this.pressFeedback, now);
      if (expired !== this.pressFeedback) {
        this.pressFeedback = expired;
        if (this.state !== null) this.draw(false);
        return;
      }
    }

    const state = this.state;
    if (state === null || state.vfxInstances.length === 0) return;

    const frameMs = getMetrics(this.fpsCounter.getFps(), 0).frameTime;
    if (deltaMs > MAX_FRAME_ADVANCE_MS || frameMs > MAX_FRAME_ADVANCE_MS) {
      this.draw(false);
      return;
    }

    const before = state.vfxInstances;
    // P1 hit-stop: hold the impact frame briefly so the shake reads as an
    // impact. This only slows the VFX advance — the reducer, the clock and
    // therefore the enemy turn are untouched (proposal §R3 forbids using
    // hit-stop to delay an enemy turn, which would be a balance change).
    //
    // The hold is bounded by WALL CLOCK (`hitStopDeadlineMs`), never by the
    // VFX instance's own `elapsedMs`: deriving the hold from `elapsedMs`
    // deadlocked, because the hold is precisely what freezes `elapsedMs`.
    this.hitStopDeadlineMs = hitStopDeadlineFor(
      this.hitStopDeadlineMs,
      now,
      before,
      this.previousVfxInstances,
      this.reducedMotion,
    );
    const holding = hitStopActiveAt(this.hitStopDeadlineMs, now);
    const advanceMs = holding ? 0 : deltaMs;
    const after = advanceVfxListBy(before, advanceMs);
    const changed =
      after.length !== before.length ||
      after.some((instance, index) => instance.tick !== before[index]?.tick) ||
      holding;
    this.state = { ...state, vfxInstances: after };
    this.previousVfxInstances = after;
    if (changed) this.draw(false);
  };

  start(): void {
    this.draw();
    this.startLoop();
  }

  /** Read-only phase accessor for e2e/integration tests. */
  getPhase(): GamePhase | null {
    return this.state?.phase ?? null;
  }

  /** Read-only screen accessor for e2e/integration tests. */
  getScreen(): ScreenKind {
    return this.screen;
  }

  /** E2E hook: current highlighted menu index (position-independent specs). */
  getSelectedMenuIndex(): number {
    return this.selectedMenuIndex;
  }

  /** E2E hook: menu option keys in order (pair with getSelectedMenuIndex). */
  getMenuOptionKeys(): string[] {
    return MENU_OPTIONS.map((o) => o.key);
  }

  /** Read-only BGM volume accessor for e2e/integration tests. */
  async getBgmVolume(): Promise<number> {
    const audio = await loadAudioSystem();
    if (!audio) return 0;
    return audio.AudioManager.getInstance().getBgmVolume();
  }

  /** External entry point for touch gamepad program buttons.
   * Resolves hand index → programId via resolveProgramSelection, then applies.
   */
  /** Touch path for a loot card reward (ADR-0259). The digit path and this
   * both dispatch `select_program`, which `applyLootAction` handles. */
  handleRewardButton(handIndex: number): void {
    this.idleSinceMs = Date.now();
    if (this.state === null || this.state.runPhase !== "loot") return;
    const previous = this.state;
    this.state = applyAction(this.state, { type: "select_program", handIndex });
    // ADR-0262: the touch reward path must stage the commit like the digit
    // path does, or a touch player gets the old colour-only change.
    this.syncGrowthReveal(previous, this.state);
    this.draw(false);
  }

  /**
   * ADR-0262: derive the growth reveal from a (previous → next) state pair,
   * the same way `beginMatrixTravel` derives the traversal. Pure bookkeeping
   * on the controller: no reducer state, no RNG, no input lock.
   */
  private syncGrowthReveal(previous: GameState, next: GameState): void {
    const now = performance.now();
    if (
      next.cardRewardTaken &&
      next.cardRewardTaken !== previous.cardRewardTaken
    ) {
      const card = rewardProgram(next.cardRewardTaken);
      const slot = offeredCardIds(next).indexOf(next.cardRewardTaken) + 1;
      this.lootCommit = beginLootCommit(
        card?.name ?? next.cardRewardTaken,
        card ? programEffectTag(card) : "",
        slot > 0 ? slot : 1,
        now,
      );
    }
    // Leaving the loot screen retires the commit and — only when the run
    // stepped back out onto the board — announces the card there. A terminal
    // node goes to the ending, which draws its own screen, so no note.
    if (previous.runPhase === "loot" && next.runPhase !== "loot") {
      const taken = this.lootCommit?.cardName ?? null;
      this.lootCommit = null;
      this.matrixArrival =
        taken !== null && next.runPhase === "matrix"
          ? beginMatrixArrival(taken, now, this.reducedMotion)
          : null;
    }
  }

  handleProgramButton(handIndex: number): void {
    this.idleSinceMs = Date.now();
    if (this.state === null) return;
    const action: GameAction = { type: "select_program", handIndex };
    const resolved = resolveProgramSelection(this.state, action);
    if (resolved === null) return;
    // ADR-0251: name the program this tap plays, read before the play
    // removes it from the hand (reading the hand afterwards named the card
    // that slid into the slot, not the one played).
    this.pressedProgramName =
      this.state.deck[handIndex - 1]?.name.toUpperCase() ?? null;
    // P12 — acknowledge the tap inside the game, not only via the button's
    // CSS `:active` state (which vanishes as soon as the finger lifts).
    this.pressFeedback = pressProgramButton(
      this.pressFeedback,
      handIndex,
      Date.now(),
    );
    const previous = this.state;
    this.state = applyAction(this.state, resolved);
    if (previous.phase === "combat" && this.state.phase === "combat") {
      this._lastIceHp = this.state.ice.hp;
      this._lastPlayerHp = this.state.player.hp;
    }
    const nextState = this.state;
    const layers = pickTransitionSfx(previous, nextState);
    if (layers.length > 0) {
      void loadAudioSystem().then((audio) => {
        if (!audio) return;
        const manager = audio.AudioManager.getInstance();
        for (const id of layers) manager.playSfx(id);
      });
    }
    this.draw();
  }

  /** P11 — enter the onboarding tutorial overlay.
   *
   * Called by `boot()` on a first boot (the localStorage completion flag is
   * absent) and by the menu's TUTORIAL option. The overlay writes the
   * completion flag itself when the player finishes or skips it, so the
   * tutorial is shown exactly once per profile.
   */
  enterTutorial(): void {
    resetTutorial();
    this.tutorialActive = true;
    this.tutorialOverlay = createTutorialOverlay();
    this.draw();
  }

  stop(): void {
    this.loopRunning = false;
    this.hitStopDeadlineMs = 0;
    this.previousVfxInstances = [];
    this.pressFeedback = IDLE_PRESS_FEEDBACK;
    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
    this.input.stop();
    this.gamepad.stop();
    this.unmountTouch();
    this.touchOverlayMounted = false;
    this.unwatchLayout();
    if (this.pwaController) {
      this.pwaController.dispose();
      this.pwaController = null;
    }
  }

  getSettingsState(): import("./renderer/settings.ts").SettingsState {
    if (this.settingsState === null || this.settingsState === undefined) {
      try {
        this.settingsState = getInitialSettingsState();
      } catch (e) {
        console.error(
          "[Game] Failed to initialize settingsState in getter:",
          e,
        );
        this.settingsState = fallbackSettingsState();
      }
    }
    return this.settingsState;
  }

  /** Replace the live settingsState. Used by the PWA controller subscriber. */
  setSettingsState(next: import("./renderer/settings.ts").SettingsState): void {
    this.settingsState = next;
  }

  /** Attach the PWA controller (booted in `boot()`). */
  attachPwaController(controller: PwaController): void {
    this.pwaController = controller;
  }

  /** Public redraw — invoked by external subscribers (e.g. PWA controller). */
  redraw(): void {
    this.draw();
  }

  /** Expose methods for e2e testing */
  static readonly e2eMethods = [
    "getScreen",
    "getSelectedMenuIndex",
    "getMenuOptionKeys",
    "getPhase",
    "getBgmVolume",
    "getSettingsState",
    "setSettingsState",
    "attachPwaController",
    "redraw",
    "handleProgramButton",
    "start",
    "stop",
  ];
}

function boot(): void {
  const loading = document.getElementById("loading");
  const canvas = document.getElementById("game-canvas");
  const gamepadStatus = document.getElementById("gamepad-status");
  if (!canvas || !(canvas instanceof HTMLCanvasElement)) {
    console.error("Canvas element not found");
    return;
  }

  let game: Game;
  try {
    const iceTypes = ICE_TYPES;
    game = new Game(canvas, iceTypes);
  } catch (err) {
    console.error("Failed to boot Wet Run:", err);
    if (loading) loading.textContent = `Error: ${(err as Error).message}`;
    return;
  }

  if (loading) loading.style.display = "none";
  // P11 — first boot shows the onboarding tutorial automatically. The gate is
  // the same localStorage flag the tutorial overlay writes on completion, so
  // the tutorial appears exactly once per profile.
  if (shouldAutoShowTutorial(localStorage)) {
    game.enterTutorial();
  }
  game.start();
  (window as unknown as { wetrun: Game }).wetrun = game;

  // Boot PWA controller and pipe state changes into the live settingsState
  // so the PWA rows reflect install/update/offline events as they happen.
  // Subscribing to draw() guarantees the settings screen redraws when a
  // `beforeinstallprompt` arrives while the user is on the settings screen.
  const pwa = bootPwaController();
  const initialSettings = game.getSettingsState();
  game.setSettingsState({
    ...initialSettings,
    pwa: pwa.state,
  });
  pwa.subscribe((next) => {
    const current = game.getSettingsState();
    game.setSettingsState({ ...current, pwa: next });
    if (game.getScreen() === "settings") game.redraw();
  });
  // Expose the controller for the settings input handler (ENTER → prompt/apply).
  game.attachPwaController(pwa);

  void loadAudioSystem().then((audio) => {
    if (!audio) return;
    const manager = audio.AudioManager.getInstance();
    audio.AudioManager.unlockOnFirstGesture(() => {
      manager.play();
    });
    document.addEventListener("keydown", (ev: KeyboardEvent) => {
      if (ev.key === "m" || ev.key === "M") {
        const muted = manager.toggleMute();
        console.info(
          `[audio] BGM ${muted ? "muted" : "unmuted"} (M to toggle)`,
        );
      }
    });
  });

  // Gamepad connection monitoring
  const updateGamepadStatus = (): void => {
    if (!gamepadStatus) return;
    if (isGamepadConnected()) {
      gamepadStatus.textContent = "🎮 Gamepad Connected";
      gamepadStatus.classList.add("connected");
    } else {
      gamepadStatus.textContent = "";
      gamepadStatus.classList.remove("connected");
    }
  };

  if (typeof window !== "undefined") {
    window.addEventListener("gamepadconnected", updateGamepadStatus);
    window.addEventListener("gamepaddisconnected", updateGamepadStatus);
    updateGamepadStatus();
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}
