import { AsciiRenderer } from "./renderer/canvas";
import { KeyboardInput } from "./input/keyboard";
import { GamepadInput, isGamepadConnected } from "./input/gamepad";
import { mountVirtualGamepad, updateProgramRow, isTouchDevice } from "./input/touch";
import { visibleMenuOptions, type MenuEntry, type MenuOption } from "./renderer/menu";
import { renderPreGameScreen } from "./renderer/pre_game_screen";
import {
  renderRunScreen,
  renderCombatScreen,
  composeCombatScreen,
  type RunNarrative,
} from "./renderer/run_screen";
import { beginMatrixTravel, matrixTravelFrame, type MatrixTravel } from "./renderer/matrix_travel";
import { renderCombatHints } from "./renderer/combat_hints";
import { filterMissionsByUniverse } from "./core/missions_filter";
import { FAR_GRID_LOCKED_MESSAGE, isFarGridUnlocked } from "./core/dungeon/far_grid_gate";
import { advanceVfxListBy, WEB_TICK_MS, type CombatVfxInstance } from "./renderer/combat_vfx";
import { hitStopActiveAt, hitStopDeadlineFor } from "./renderer/screen_shake";
import { pickTransitionSfx } from "./core/combat/combat_sfx";
import { programAffordances, rewardAffordances } from "./core/combat/program_affordance";
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
import { offeredCardIds, rewardProgram, UNIQUE_PROGRAMS } from "./core/state/card_reward";
import { programEffectTag } from "./core/combat/program_effects";
import { everyProgramBlocked } from "./core/combat/program_affordance";
import { renderRunIntro } from "./renderer/run_intro";
import { renderBeatCard } from "./renderer/beat_card";
import {
  runOpeningBeat,
  iceIntroBeat,
  firstFightWarningBeat,
  firstVictoryBeat,
  flatlineBeat,
  finnIntroBeat,
  firstReturnBeat,
  ashpoolCallBeat,
  endingSignoffBeat,
  type DialogueBeat,
} from "./core/state/event_beats";
import { markIceIntrosSeen, seenIceIntros } from "./core/state/ice_intros";
import { contractFor } from "./core/state/campaign";
import { markPrologueSeen, seenPrologues } from "./core/state/prologue_seen";
import { hasHeardBeat, markBeatHeard } from "./core/state/story_flags";
import { renderJockeySelect } from "./renderer/jockey_select";
import { renderPrep } from "./renderer/prep";
import { renderMissionBriefing } from "./renderer/menu_dialogue";
import { JOCKEYS, jockeyHandle } from "./core/state/jockey";
import type { PlayMode } from "./core/graphic_novel/graphic_novel_types";
import { tick as gnTick } from "./core/graphic_novel/graphic_novel_player";
import type { ArcId } from "./core/combat/ending_resolver";
import { FpsCounter, getMetrics } from "./core/state/performance";
import { createTutorialOverlay, resetTutorial } from "./renderer/tutorial";
import {
  combatEntryHintFits,
  hasPlayedBefore,
  isTutorialCompleted,
  markPlayed,
  markRunFinished,
  runsFinished,
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
import { DungeonCrawler, createDungeonCrawlerFromMission } from "./core/dungeon/dungeon_crawler";
import { getInitialSettingsState } from "./renderer/settings";
import {
  loadColorblindMode,
  loadHighContrastOverride,
  loadReducedMotionOverride,
  loadTextScale,
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
import { openArrivalEncounter, encounterRoster, runAbandoned } from "./core/state/encounter_verbs";
import { missionIce } from "./core/state/mission_ice";
import { missionGradeOf } from "./core/combat/ice_scaling";
import { applyPrep, PREP_OPTIONS, prepGrantFor, type PrepChoice } from "./core/state/prep";
import { readPrepWallet, spendPrepWallet } from "./core/state/prep_wallet";
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
import { equipOn, DEFAULT_REGISTRY, EQUIP_SLOTS } from "./core/state/equipment";
import { hydrateLoadout, readEquippedIds, writeEquippedIds } from "./core/state/equipment_store";
import {
  isOwned,
  mergeDroppedEquipment,
  ownEquipment,
  readOwnedIds,
  writeOwnedIds,
  type OwnedSet,
} from "./core/state/owned_equipment";
import { applyEquipmentSurvival } from "./core/state/equipment_stats";
import {
  contractSeedMaterials,
  mergeRunIntoWallet,
  readWalletMaterials,
  seedRunWallet,
  writeWalletMaterials,
} from "./core/state/wallet";
import type { InfoMarket } from "./core/info_market";
import { loadPersistedLanguage } from "./renderer/settings";
import { formatNavIndex } from "./renderer/nav_index";
import { handleSettingsInput } from "./app/settings_input";

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
  "briefing",
  "prep",
  "tutorial",
  "settings",
  "dungeon",
  "pause",
  "graphic_novel",
]);
const loadAudioSystemRaw = () => import("./audio/manager.ts");

/** ADR-0311: the unique the run holds, if any. Display-only — the controller
 * uses it to tell "this pick added a unique" from "it added a card". */
function ownUniqueId(state: GameState): string | null {
  for (const pile of [state.deck, state.drawPile, state.discardPile]) {
    for (const card of pile) {
      if (UNIQUE_PROGRAMS.has(card.id)) return card.id;
    }
  }
  return null;
}

/** P9 render loop — maximum frame interval (ms) that still advances VFX.
 *
 * A longer frame (GC pause, background-tab wake-up) is a stall: the VFX
 * advance is skipped so instances do not all expire at once on a huge delta.
 */
const MAX_FRAME_ADVANCE_MS = 100;

function isAudioOff(): boolean {
  return localStorage.getItem("wetrun_audio_off") === "1";
}
const loadAudioSystem = () => (isAudioOff() ? Promise.resolve(null) : loadAudioSystemRaw());

import missionsData from "./data/missions.json" with { type: "json" };
import programsData from "./data/programs.json" with { type: "json" };
import iceTypesData from "./data/ice_types.json" with { type: "json" };
import recipesData from "./data/recipes.json" with { type: "json" };
import materialsData from "./data/materials.json" with { type: "json" };
import { loadMissionsCatalog, loadProgramsCatalog, loadIceCatalog } from "./core/data_loaders";

/** Mission catalog (validated at module load — schema mismatches throw early). */
const MISSIONS: ReadonlyArray<Mission> = loadMissionsCatalog(missionsData);

/** Programs catalog (validated). Field aliases (ap_cost → cost) normalized. */
const PROGRAMS: Readonly<Record<string, Program>> = loadProgramsCatalog(programsData);

/** ICE types catalog (validated). Field aliases (defense → armor) normalized. */
const ICE_TYPES: Readonly<Record<string, Ice>> = loadIceCatalog(iceTypesData);

/** The craft registry, loaded from data (ADR-0325).
 *
 * The recipes (16 equipment) and materials (28) are static imports. An empty
 * registry is a developer error — a missing or malformed data file — so it
 * throws at boot rather than rendering an empty crafting screen. (The Python
 * prototype's `makeRecipesFromData({})` stub is what this replaces.) */
function loadCraftingData(): {
  readonly recipes: ReadonlyArray<Recipe>;
  readonly materials: ReadonlyArray<MaterialDef>;
} {
  const recipes = makeRecipesFromData(recipesData as unknown as Record<string, unknown>);
  const materials = makeMaterialsFromData(materialsData as unknown as Record<string, unknown>);
  if (recipes.length === 0 || materials.length === 0) {
    throw new Error(
      "crafting: empty registry — recipes.json / materials.json missing or malformed",
    );
  }
  return { recipes, materials };
}

/** Format a mission for the select screen (Tier 2a). */
function formatMissionOption(
  mission: Mission,
  index: number,
  language: import("./core/i18n.ts").Language = "en",
): string {
  const grade = `T${mission.grade_max}`;
  const credits = mission.rewards.credits.toLocaleString();
  const titleText =
    language === "ko" && mission.title_ko !== undefined && mission.title_ko.length > 0
      ? mission.title_ko
      : mission.title;
  return `${formatNavIndex(index)} ${titleText}  [${grade} | ${credits}cr]`;
}

/** A story card: a title, and the voice it carries (ADR-0317 3b). */
interface BeatCard {
  readonly title: string;
  readonly beat: DialogueBeat;
}

class Game {
  private state: GameState | null = null;
  screen: ScreenKind = "menu";
  private selectedMenuIndex = 0;
  /** ADR-0315: the cursor is normalized once per visit, not per frame. */
  private menuSelectionNormalized = false;
  private selectedMission = 0;
  /** ADR-0274 — the jockey chosen for the next run (index into JOCKEYS). */
  private selectedJockey = 0;
  /** ADR-0283: the prep row under the cursor, and what it will buy. */
  private prepCursor = 0;
  /** Where the run's screen was before the between-leg advance took over
   * (ADR-0318 (a)). Restoring it keeps the run's screen invariant intact — a
   * CONTINUE resumes with `menu`, a fresh run with `prep`. */
  private contractPrepReturn: ScreenKind = "prep";
  private prepChoice: PrepChoice = "stim";
  /** ADR-0284: what the stockpile will pay for the run about to start. */
  private prepWalletOutlay = 0;
  renderer: AsciiRenderer;
  /** Lazy audio loader, gated on the audio-off flag. Exposed as a field so the
   * settings handler (app/settings_input.ts) takes the same gate everything
   * else does. */
  loadAudio = loadAudioSystem;
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
  /** ADR-0323: the wallet this run was seeded with, so the merge back into the
   * hoard can tell what the run EARNED from what it inherited. */
  private runWalletSeed: Inventory | null = null;
  private equipmentLoadout: EquipmentLoadout;
  private recipes: ReadonlyArray<Recipe>;
  private materials: ReadonlyArray<MaterialDef>;
  private infoMarket: InfoMarket;
  /** ADR-0325: the gear the runner owns (starters + crafted). The EQUIPMENT
   *  menu equips only from this set, so a craft finally buys something wearable. */
  private ownedEquipment: OwnedSet;
  private layout: Layout;
  private tutorialActive = false;
  private tutorialOverlay: ReturnType<typeof createTutorialOverlay> | null = null;
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
  /** ADR-0311 — the unique taken at the free pick. The loot commit panel owns
   * the offer rows (a card ends the stop), so the unique is confirmed inline
   * and its name is carried to the board arrival instead. */
  private uniqueCommitName: string | null = null;
  private matrixArrival: MatrixArrival | null = null;
  /** ADR-0272 — the arc's framing beat, shown once when a run starts. Null
   * when there is no run, or once a key has dismissed it. Never saved, so a
   * resumed run does not replay its introduction. */
  private runIntroArc: ArcId | null = null;
  /** ADR-0317 (3b): the companion's first words, spoken on the run's opening
   * card. Set with `runIntroArc` and cleared with it — display-only, never
   * saved. Null once the player has finished a run, or after the first key. */
  private runIntroBeat: DialogueBeat | null = null;
  /** ADR-0317 (3b): a one-time beat card that owns the screen until a key.
   * Same shape as the run intro, but for beats that arrive mid-run (the first
   * fight, the first win) and would not fit inline on a dense panel. */
  private beatCard: BeatCard | null = null;
  /** Cards waiting their turn. A transition can have more than one thing to say
   * (the fixer's debrief, then the next job), and a card owns the screen. */
  private beatQueue: BeatCard[] = [];
  /** The commit stage last drawn — the loop redraws only when the clock
   * pushes the panel to a new stage, then stops (ADR-0262). */
  private lootCommitStageShown = -1;
  /** ADR-0252: slot-0 writes and the retirement run in order. */
  private persistQueue: Promise<void> = Promise.resolve();
  private lastPersistedState: GameState | null = null;
  /** P10 — effective reduced-motion state. True suppresses the P1 canvas
   * shake and the hit-stop hold. */
  reducedMotion = false;
  /** P10 — effective high-contrast state. */
  highContrast = false;
  /** P10 — the active colorblind palette mode (ADR-0196). */
  colorblindMode: ColorblindMode = "none";
  /** P10 — the active text-scale step. */
  textScale: TextScaleStep = "medium";
  /** P12 — the in-game acknowledgement of a touch program-button press. */
  private pressFeedback: PressFeedbackState = IDLE_PRESS_FEEDBACK;
  /** ADR-0251 — name of the program the acknowledged tap played. */
  private pressedProgramName: string | null = null;
  /** ADR-0251 — true while the touch overlay (and its program row) is up. */
  private touchOverlayMounted = false;
  private graphicNovelPlayer:
    import("./core/graphic_novel/graphic_novel.ts").GraphicNovelPlayer | null = null;
  private gnLanguage: import("./core/graphic_novel/graphic_novel_types.ts").Language = "en";
  private graphicNovelState: import("./core/types.ts").GraphicNovelState | null = null;

  settingsState: import("./renderer/settings.ts").SettingsState | null = null;
  pwaController: PwaController | null = null;
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

  constructor(canvas: HTMLCanvasElement, iceTypes: Readonly<Record<string, Ice>>) {
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
    // ADR-0323: the hoard outlives the session.
    this.inventory = {
      credits: 0,
      materials: readWalletMaterials(),
      programs: [],
    };
    // ADR-0322: the menu's gear survives a reload and reaches the run.
    this.equipmentLoadout = hydrateLoadout(DEFAULT_REGISTRY, readEquippedIds());
    this.ownedEquipment = readOwnedIds();
    const crafting = loadCraftingData();
    this.recipes = crafting.recipes;
    this.materials = crafting.materials;
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
    // ADR-0315 progressive disclosure, decided SYNCHRONOUSLY before the first
    // frame: a profile that has never started a run has nothing to continue and
    // nothing to archive, so the title menu is a wall of words between the
    // player and the game. The flag is localStorage, so no IDB round-trip is
    // needed — doing this in the async save-cache refresh flashed the menu for
    // a frame and raced the first keypress.
    if (typeof localStorage !== "undefined" && !hasPlayedBefore(localStorage)) {
      markPlayed(localStorage);
      this.screen = "jockey_select";
      this.selectedJockey = 0;
    }
    void this.refreshSaveCache();
    const resetIdle = (): void => {
      this.idleSinceMs = Date.now();
    };
    document.addEventListener("keydown", resetIdle);
    document.addEventListener("pointerdown", resetIdle);
    document.addEventListener("visibilitychange", resetIdle);
    const handler = (action: GameAction): void => {
      resetIdle();
      // ADR-0317 (3b): a beat card owns the screen until a key, whatever is
      // behind it. It has to be checked FIRST: the fixer's introduction fires on
      // the mission list, and a card that draws over a screen without consuming
      // its keys let the briefing and prep advance invisibly behind it.
      if (this.beatCard !== null) {
        this.beatCard = this.beatQueue.shift() ?? null;
        this.draw();
        return;
      }
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
          if (result.action === "skip" || this.tutorialOverlay.state.currentStep >= 6) {
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
      // ADR-0318 (a): the advance between a contract's legs owns the input the
      // same way the crafting screens do — the run state is live behind it.
      if (this.screen === "contract_prep") {
        this.handleContractPrepInput(action);
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
        this.runIntroBeat = null;
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
      // ADR-0317 (3b): the reveal is the one moment this ICE's voice is new.
      // Remember it so the tagline is spoken once per profile, not per node.
      const revealed = this.state;
      if (
        revealed !== null &&
        previous?.encounterDecision?.probed !== true &&
        revealed.encounterDecision?.probed === true
      ) {
        markIceIntrosSeen(
          typeof localStorage === "undefined" ? null : localStorage,
          encounterRoster(revealed).map((ice) => ice.id),
        );
      }
      // ADR-0317 (3b): the two moments that are new to the profile. The
      // construct is in the deck for the whole run, so she speaks when the
      // player first fights and when they first win, and never again.
      if (revealed !== null) {
        const storage = typeof localStorage === "undefined" ? null : localStorage;
        const language = this.settingsState?.language ?? "en";
        if (
          previous?.phase !== "combat" &&
          revealed.phase === "combat" &&
          !hasHeardBeat(storage, "first_fight_warning")
        ) {
          const beat = firstFightWarningBeat(language);
          if (beat !== null) {
            this.showBeat({ title: "ICE AHEAD", beat });
            markBeatHeard(storage, "first_fight_warning");
          }
        }
        if (
          previous?.runPhase !== "loot" &&
          revealed.runPhase === "loot" &&
          !hasHeardBeat(storage, "first_victory")
        ) {
          const beat = firstVictoryBeat(language);
          if (beat !== null) {
            this.showBeat({ title: "FIRST BLOOD", beat });
            markBeatHeard(storage, "first_victory");
          }
        }
        // ADR-0317 3b: the one moment the story went silent was the one it had
        // been building to. She warned that she can only watch; this is her
        // watching. Once per run, right after the killing blow.
        if (previous?.runPhase !== "dead" && revealed.runPhase === "dead") {
          const beat = flatlineBeat(language);
          if (beat !== null) this.showBeat({ title: "FLATLINE", beat });
        }
        // ADR-0315 slice 2: a contract's next leg opens with the fixer handing
        // over the job — the mission's own briefing (ADR-0316), on the card the
        // other beats use, so the chain is a beat rather than a silent reload.
        const advanced =
          previous?.campaign !== undefined &&
          revealed.campaign !== undefined &&
          revealed.campaign.completed > previous.campaign.completed;
        if (advanced) {
          const contract = revealed.campaign;
          const leg = contract?.legs[contract.completed];
          const story = leg
            ? (language === "ko" && leg.mission.briefing_ko) || leg.mission.briefing || ""
            : "";
          // ADR-0317 3b: the campaign created two moments that nothing spoke at
          // — returning from the first job, and Tessier-Ashpool noticing. Both
          // scenes were authored for exactly these beats and had no trigger.
          // The debrief comes first; the queue holds the job behind it.
          const debrief =
            contract?.completed === 1
              ? firstReturnBeat(language)
              : contract?.completed === 2
                ? ashpoolCallBeat(language)
                : null;
          if (debrief !== null) {
            this.showBeat({
              title: `CONTRACT ${contract?.completed ?? 0}/${contract?.legs.length ?? 0} · DONE`,
              beat: debrief,
            });
          }
          // ADR-0318 (a): the next leg's advance. The reducer built the leg
          // already; the prep screen spends the fixer's advance on it. The
          // briefing card is read first (a card owns the screen).
          this.prepCursor = 0;
          this.contractPrepReturn = this.screen;
          this.screen = "contract_prep";
          this.showBeat({
            title: `CONTRACT ${(contract?.completed ?? 0) + 1}/${contract?.legs.length ?? 0}`,
            // No speaker: the briefing is the job's file, not a line the fixer
            // says (2026-11-17). The card names the job and prints it.
            beat: {
              speaker: "",
              lines: story.length > 0 ? [story] : ["The next job."],
            },
          });
        }
      }
      if (runAbandoned(previous, this.state)) {
        // JACK OUT ends the run: leave the board for the main menu.
        // ADR-0323: the run is over — bank what it earned before dropping it.
        this.endRun();
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
        // ADR-0323: the run is over — bank what it earned before dropping it.
        this.endRun();
        this.state = null;
        this.matrixTravel = null;
        this.lootCommit = null;
        this.matrixArrival = null;
        this.screen = "menu";
        this._message = RUN_COMPLETE_MESSAGE;
        this.noteRunFinished();
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
        // ADR-0323: the run is over — bank what it earned before dropping it.
        this.endRun();
        this.state = null;
        this.matrixTravel = null;
        this.lootCommit = null;
        this.matrixArrival = null;
        this.screen = "menu";
        this._message = FLATLINE_MESSAGE;
        this.noteRunFinished();
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
          if (previous.runPhase === "matrix" && this.state.runPhase === "combat") {
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
      // ADR-0325: one transaction — spend the materials AND take ownership of
      // the piece. The recipe's itemId is a catalog equipment id.
      const result = craftItem(this.recipes, recipe.itemId, this.inventory.materials);
      if (result.ok) {
        this.inventory = { ...this.inventory, materials: result.newInventory };
        writeWalletMaterials(this.inventory.materials);
        this.ownedEquipment = ownEquipment(this.ownedEquipment, recipe.itemId);
        writeOwnedIds(this.ownedEquipment);
        this._message = `Crafted ${recipe.name} — it's yours now.`;
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
      // ADR-0325: equip only what the runner owns — tier-0 starters plus
      // anything crafted. Crafting is what makes the menu grow.
      const candidate = DEFAULT_REGISTRY.all.find(
        (e) =>
          e.slot === slot &&
          isOwned(this.ownedEquipment, e.id) &&
          this.equipmentLoadout.get(slot) === null,
      );
      if (!candidate) {
        this._message = `No owned equipment for slot ${slot}`;
        this.draw();
        return;
      }
      const result = equipOn(this.equipmentLoadout, candidate);
      this.equipmentLoadout = result.loadout;
      writeEquippedIds(this.equipmentLoadout);
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
        const dx = action.type === "move_east" ? 1 : action.type === "move_west" ? -1 : 0;
        const dy = action.type === "move_south" ? 1 : action.type === "move_north" ? -1 : 0;
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

  /** ADR-0317: the graphic novel is the run's opening, not a menu mode. The
   * menu entry that let a player browse it was the validation scaffold and is
   * gone (2026-11-17), so leaving the story — finished or skipped — always hands
   * over to the mission list. */
  private initGraphicNovel(mode: PlayMode = "novice"): void {
    void loadStorySystem().then((gn) => {
      const player = gn.createPlayer({ mode });
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
      void import("./renderer/graphic_novel_screen.ts").then(({ renderGraphicNovelScreen }) => {
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
            // ADR-0317 3b: the story does not change between runs, so a
            // watched prologue says so and ESC stops looking like a gamble.
            seen: seenPrologues(this.storagePort()).has(player.mode),
          },
          this.layout.cols,
          this.layout.rows,
        );
        this.renderer.render(grid, ["GRAPHIC NOVEL", "", ""]);
      });
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
        // Watched to the end. A player who skips has not seen it, so the
        // marker would be a lie — only a finish counts.
        markPrologueSeen(this.storagePort(), player.mode);
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
    // ADR-0317: the graphic novel is only reachable as the run's prologue, so
    // leaving it (finished or skipped) skips the STORY, not the run.
    this.startRunFromGraphicNovel();
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
      const options = this.visibleMenu();
      const idx = action.handIndex - 1;
      if (idx >= 0 && idx < options.length) {
        this.selectedMenuIndex = idx;
        const opt = options[idx];
        this.selectMenuOption(opt ? opt.key : undefined);
      }
      return;
    }
    if (this.screen === "menu") {
      const options = this.visibleMenu();
      const count = Math.max(1, options.length);
      if (action.type === "move_south") {
        this.selectedMenuIndex = (this.selectedMenuIndex + 1) % count;
        this.draw();
      } else if (action.type === "move_north") {
        this.selectedMenuIndex = (this.selectedMenuIndex - 1 + count) % count;
        this.draw();
      } else if (action.type === "confirm") {
        const opt = options[this.selectedMenuIndex];
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
        this.selectedJockey = (this.selectedJockey - 1 + JOCKEYS.length) % JOCKEYS.length;
        this.draw();
      } else if (action.type === "confirm") {
        // ADR-0317: the prologue opens the run — this jockey's story plays,
        // then the mission list. ESC skips the story, not the run.
        this.screen = "graphic_novel";
        this.selectedMission = 0;
        const jockeyId = JOCKEYS[this.selectedJockey]?.id;
        this.initGraphicNovel(
          jockeyId === "veteran" || jockeyId === "heretic" ? jockeyId : "novice",
        );
      } else if (action.type === "jack_out") {
        this.screen = "menu";
        this.draw();
      }
      return;
    }
    if (this.screen === "briefing") {
      // ADR-0317: ENTER continues to the advance; ESC goes back to the list.
      this.screen = action.type === "jack_out" ? "mission_select" : "prep";
      this.draw();
      return;
    }
    if (this.screen === "prep") {
      // ADR-0283 C: spend the fixer's advance. Two rows, so the screen needs no
      // new key -- ↑↓ picks, ENTER jacks in with the pick, ESC goes back.
      const count = PREP_OPTIONS.length;
      if (action.type === "move_south" || action.type === "move_east") {
        this.prepCursor = (this.prepCursor + 1) % count;
        this.draw();
      } else if (action.type === "move_north" || action.type === "move_west") {
        this.prepCursor = (this.prepCursor - 1 + count) % count;
        this.draw();
      } else if (action.type === "confirm") {
        const picked = PREP_OPTIONS[this.prepCursor];
        this.prepChoice = picked?.id ?? "stim";
        // Spend the stockpile's share, then launch.
        const mission = MISSIONS[this.selectedMission];
        if (mission) {
          const grant = prepGrantFor(missionGradeOf(mission), this.prepChoice, readPrepWallet());
          this.prepWalletOutlay = grant.fromWallet;
          spendPrepWallet(grant.fromWallet);
        }
        this.launchSelected();
      } else if (action.type === "jack_out") {
        this.screen = "mission_select";
        this.draw();
      }
      return;
    }
    if (this.screen === "mission_select") {
      // ADR-0213 isolation: the Sprawl board lists sprawl-universe missions
      // only; far-grid missions live behind the gated hub.
      const sprawlMissions = filterMissionsByUniverse(MISSIONS, "sprawl");
      if (action.type === "move_south") {
        this.selectedMission = (this.selectedMission + 1) % sprawlMissions.length;
        this.draw();
      } else if (action.type === "move_north") {
        this.selectedMission =
          (this.selectedMission - 1 + sprawlMissions.length) % sprawlMissions.length;
        this.draw();
      } else if (action.type === "confirm") {
        const picked = sprawlMissions[this.selectedMission];
        const fullIndex = picked ? MISSIONS.indexOf(picked) : -1;
        if (fullIndex >= 0) {
          this.selectedMission = fullIndex;
          this.prepCursor = 0;
          // ADR-0317: the fixer briefs you on the job before you choose the
          // advance. ENTER there continues to prep; ESC comes back here.
          // ADR-0317 3b: the first time, he also introduces himself — the
          // screen is his office, and the game never opened it.
          const storage = typeof localStorage === "undefined" ? null : localStorage;
          if (!hasHeardBeat(storage, "met_the_finn")) {
            const intro = finnIntroBeat(this.settingsState?.language ?? "en");
            if (intro !== null) {
              this.showBeat({ title: "THE FINN", beat: intro });
              markBeatHeard(storage, "met_the_finn");
            }
          }
          this.screen = "briefing";
          this.draw();
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
        this.selectedMission = (this.selectedMission + 1) % farGridMissions.length;
        this.draw();
      } else if (action.type === "move_north") {
        this.selectedMission =
          (this.selectedMission - 1 + farGridMissions.length) % farGridMissions.length;
        this.draw();
      } else if (action.type === "confirm") {
        const picked = farGridMissions[this.selectedMission];
        const fullIndex = picked ? MISSIONS.indexOf(picked) : -1;
        if (fullIndex >= 0) {
          this.selectedMission = fullIndex;
          this.prepCursor = 0;
          this.screen = "prep";
          this.draw();
        }
      } else if (action.type === "jack_out") {
        this.screen = "menu";
        this.draw();
      }
      return;
    }
    if (this.screen === "settings") {
      handleSettingsInput(this, action);
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

  private async selectMenuOption(option: MenuOption | undefined): Promise<void> {
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
      case "settings":
        this.screen = "settings";
        try {
          if (this.settingsState === null) {
            this.settingsState = getInitialSettingsState();
          }
        } catch (e) {
          console.error("[Game] Failed to initialize settingsState on menu select:", e);
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

  /** ADR-0315: the menu grows with the player. A finished run (ending or
   * flatline) unlocks the archive/workshop entries, which otherwise open onto
   * nothing. Also re-normalizes the cursor, since the visible list just grew. */
  private noteRunFinished(): void {
    if (typeof localStorage === "undefined") return;
    markRunFinished(localStorage);
    this.menuSelectionNormalized = false;
  }

  /** ADR-0315: the entries this profile has unlocked (the menu grows). */
  private visibleMenu(): ReadonlyArray<MenuEntry> {
    const storage = typeof localStorage === "undefined" ? null : localStorage;
    return visibleMenuOptions({
      hasSave: this.hasSaveCache,
      farGridUnlocked: this.farGridUnlockedCache,
      runsFinished: runsFinished(storage),
      tutorialCompleted: isTutorialCompleted(storage),
    });
  }

  /** ADR-0315: never OPEN the menu with the cursor on an entry that cannot be
   * taken — CONTINUE sits first and FAR GRID is gated. Applied once per visit
   * to the menu: normalizing on every frame would snap the cursor back off a
   * gated row the player deliberately walked to. */
  private normalizeMenuSelection(): void {
    if (this.menuSelectionNormalized) return;
    this.menuSelectionNormalized = true;
    const options = this.visibleMenu();
    if (options.length === 0) return;
    // The list is already filtered, so index 0 is always available.
    if (this.selectedMenuIndex >= options.length) this.selectedMenuIndex = 0;
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
    // ADR-0317 (3b): the construct introduces herself on the first jack-in, and
    // only then — a profile that has finished a run has already met her.
    this.runIntroBeat = runOpeningBeat(
      runsFinished(typeof localStorage === "undefined" ? null : localStorage),
      this.settingsState?.language ?? "en",
    );
    const programs = PROGRAMS;
    // ADR-0276: the jockey decides the opening deck, not just the name.
    const deck = startingDeck(programs, JOCKEYS[this.selectedJockey]?.id ?? null);
    const ice = missionIce(mission, this.iceTypes);
    const initial = makeInitialState(mission, ice, deck);
    this.state = openArrivalEncounter({
      // ADR-0284: whatever the stockpile paid for is spent here, so it is a
      // hoard rather than a permanent bonus.
      // ADR-0326: the gear's hpBonus/shieldBonus join it — same run-start shape.
      ...applyEquipmentSurvival(
        applyPrep(initial, this.prepChoice, this.prepWalletOutlay),
        this.equipmentLoadout,
      ),
      // ADR-0315 slice 2: the run is a contract — this mission, then the rest
      // of its arc. The chosen mission decides the arc; the length is the
      // resolver's (`CONTRACT_LENGTH`).
      campaign: contractFor(mission, MISSIONS, (m) => missionIce(m, this.iceTypes)),
      jockeyId: JOCKEYS[this.selectedJockey]?.id ?? null,
      grid: makeGrid(this.layout.cols, this.layout.rows),
      currentNodeIndex: 0,
      runPhase: "matrix",
      phase: "approach",
    });
    // ADR-0323 / ADR-0338: the run is seeded from the HOARD, and the seed spans
    // the WHOLE contract's rewards (the run accumulates every leg's reward, see
    // `startNextLeg`), so `mergeRunIntoWallet` banks only what the run EARNED —
    // jacking out on frame one mints nothing. The span lives in `wallet.ts` now
    // (`contractSeedMaterials`), where a unit test pins it.
    const seedRewards = contractSeedMaterials(
      this.state.campaign?.legs,
      this.state.mission.rewards.materials,
    );
    this.runWalletSeed = seedRunWallet(this.inventory, { credits: 0, materials: seedRewards });
    // ADR-0322: the run reads `state.equipmentLoadout`, so the menu's gear has
    // to be ON the state — not merely next to it. `makeInitialState` builds it
    // empty, which is why the menu used to change no number at all.
    this.state = {
      ...this.state,
      equipmentLoadout: this.equipmentLoadout,
      inventory: seedRunWallet(this.inventory, this.state.mission.rewards),
    };
    const crafting = loadCraftingData();
    this.recipes = crafting.recipes;
    this.materials = crafting.materials;
    this.infoMarket = makeInfoMarket({});
    this.draw();
  }

  /** ADR-0323: bank the run's earnings into the hoard and clear the seed.
   *
   * Called on every way a run ends — jack out, the ending, and a flatline — so
   * a failed run keeps what it picked up. That is the owner's decision: without
   * it, no recipe can cost more than one run's yield. */
  private endRun(): void {
    const run = this.state?.inventory ?? null;
    this.inventory = mergeRunIntoWallet(this.inventory, run, this.runWalletSeed);
    this.runWalletSeed = null;
    writeWalletMaterials(this.inventory.materials);
    // ADR-0329 / ADR-0346: gear salvaged during the run becomes owned when it
    // ends. The fold lives in `owned_equipment.ts` (tested); the same record is
    // returned when nothing was added, so the write is skipped then.
    const owned = mergeDroppedEquipment(
      this.ownedEquipment,
      this.state?.droppedEquipment ?? [],
    );
    if (owned !== this.ownedEquipment) {
      this.ownedEquipment = owned;
      writeOwnedIds(owned);
    }
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
      pressLabel = pressFeedbackLabel(this.pressFeedback, this.pressedProgramName ?? undefined);
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

  /** ADR-0317 (3b): the ICE's tagline for this encounter, or null.
   *
   * Only after the threat is revealed: the ICE's identity is what PROBE sells,
   * so the voice waits for the reveal rather than handing it over. Only the
   * first time this profile meets that ICE — a heard tagline is not repeated.
   * A silent ICE (most of them) returns null.
   */
  private encounterVoice(): DialogueBeat | null {
    const state = this.state;
    if (state?.runPhase !== "matrix" || state.encounterDecision?.probed !== true) return null;
    const seen = seenIceIntros(typeof localStorage === "undefined" ? null : localStorage);
    const language = this.settingsState?.language ?? "en";
    for (const ice of encounterRoster(state)) {
      if (seen.has(ice.id)) continue;
      const beat = iceIntroBeat(ice.id, language);
      if (beat !== null) return beat;
    }
    return null;
  }

  /** The profile's storage, or null where there is none (tests, SSR). */
  private storagePort(): Storage | null {
    return typeof localStorage === "undefined" ? null : localStorage;
  }

  /** The fixer's advance, as a screen (ADR-0283 C · ADR-0318 (a)).
   *
   * Shared by the pre-run prep and the between-leg prep so the amounts shown
   * come from the same tables `applyPrep` reads — the screen and the run cannot
   * disagree (ADR-0251 rule 5). */
  private drawPrep(mission: Mission): void {
    const grade = missionGradeOf(mission);
    updateProgramRow([]);
    this.renderer.render(
      renderPrep(
        {
          missionTitle: mission.title,
          grade,
          cursor: this.prepCursor,
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
        this.layout.cols,
        this.layout.rows,
      ),
      ["PREP", "", `T${grade}`],
    );
  }

  /** The advance between a contract's legs (ADR-0318 (a)).
   *
   * ↑↓ picks, ENTER spends it and jacks in, ESC keeps it and jacks in anyway.
   * The leg is already built by the reducer, so this is the one moment the
   * player chooses what the next job's capacity is worth. */
  private handleContractPrepInput(action: GameAction): void {
    const state = this.state;
    if (state === null) return;
    const count = PREP_OPTIONS.length;
    if (action.type === "move_south" || action.type === "move_east") {
      this.prepCursor = (this.prepCursor + 1) % count;
      this.draw();
      return;
    }
    if (action.type === "move_north" || action.type === "move_west") {
      this.prepCursor = (this.prepCursor - 1 + count) % count;
      this.draw();
      return;
    }
    const spent =
      action.type === "confirm" || action.type === "jack_out" || action.type === "cancel";
    if (!spent) return;
    if (action.type === "confirm") {
      const choice: PrepChoice = PREP_OPTIONS[this.prepCursor]?.id ?? "stim";
      const grant = prepGrantFor(missionGradeOf(state.mission), choice, readPrepWallet());
      this.prepWalletOutlay = grant.fromWallet;
      spendPrepWallet(grant.fromWallet);
      this.state = applyPrep(state, choice, this.prepWalletOutlay);
    }
    // Back to the run: `draw()` routes by runPhase once the screen is not the
    // prep, so the leg's board takes over.
    this.screen = this.contractPrepReturn;
    this.draw();
  }

  /** Queue a story card (ADR-0317 3b). One owns the screen at a time; the rest
   * wait their turn, so a transition can say two things in order. */
  private showBeat(card: BeatCard): void {
    if (this.beatCard === null) this.beatCard = card;
    else this.beatQueue.push(card);
  }

  /** ADR-0317 (3b): the construct's last word on the ending screen. */
  private endingSignoff(): DialogueBeat | null {
    if (this.state?.runPhase !== "ending") return null;
    return endingSignoffBeat(this.settingsState?.language ?? "en");
  }

  /** Render the current state. `persist` is false for render-loop frames:
   * a redraw must not trigger the autosave side effect. */
  draw(persist: boolean = true): void {
    // ADR-0317 (3b): a mid-run beat card owns the screen until a key, the same
    // way the run's opening beat does.
    if (this.beatCard !== null) {
      updateProgramRow([]);
      this.renderer.render(
        renderBeatCard(this.beatCard.title, this.beatCard.beat, this.layout.cols, this.layout.rows),
        ["STORY", "", "ANY KEY"],
      );
      return;
    }
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
          this.runIntroBeat,
        ),
        ["JACK-IN", "", "ANY KEY"],
      );
      return;
    }
    // ADR-0318 (a): the advance between a contract's legs. The reducer has
    // already built the next leg, so this spends the advance on it — which is
    // what ADR-0315 Q3 meant by "the prep handles between-mission recovery".
    // It sits after the beat card so the fixer's briefing is read first.
    if (this.screen === "contract_prep" && this.state !== null) {
      this.drawPrep(this.state.mission);
      return;
    }
    // Tier 5: matrix / loot / ending screens render with a real GameState
    // but their UI is non-combat. Route by runPhase.
    if (this.state !== null && ["matrix", "ending", "loot"].includes(this.state.runPhase)) {
      // ADR-0252: a committed move, a won fight and the ending are saved
      // (or retire the slot) like combat frames are.
      if (persist) this.autosave();
      // ADR-0259: on a non-terminal loot screen the same row picks the card
      // reward, so touch players get the same choice as the digits.
      const rewards =
        this.state.runPhase === "loot" && !isTerminalNode(this.state)
          ? rewardAffordances(this.state)
          : [];
      updateProgramRow(rewards, rewards.length > 0 ? (i) => this.handleRewardButton(i) : undefined);
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
      // ADR-0317 (3b): the beats this frame may speak. They depend on the
      // profile (heard flags, language), not on the run, so they are read here
      // and passed in. Each getter short-circuits on the runPhase it belongs to.
      const narrative: RunNarrative = {
        iceVoice: this.encounterVoice(),
        signoff: this.endingSignoff(),
      };
      const view =
        travel === null
          ? renderRunScreen(
              this.state,
              this.layout.cols,
              this.layout.rows,
              shouldShowMatrixEntryHint(this.matrixEntryHintShown, this.state),
              null,
              growth,
              narrative,
            )
          : renderRunScreen(
              this.state,
              this.layout.cols,
              this.layout.rows,
              shouldShowMatrixEntryHint(this.matrixEntryHintShown, this.state),
              travel,
              growth,
              narrative,
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
        const tutorialGrid = this.tutorialOverlay.render(this.layout.cols, this.layout.rows);
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
            console.error("[Game] Failed to initialize settingsState in render:", e);
            this.settingsState = fallbackSettingsState();
          }
        }
      }
      if (this.screen === "graphic_novel") {
        this.renderGraphicNovel();
        return;
      }
      if (this.screen === "briefing") {
        // ADR-0317: the fixer hands over the job — the mission's story from
        // ADR-0316 — right before the advance (prep) and the jack-in.
        const mission = MISSIONS[this.selectedMission];
        if (mission) {
          const language = this.settingsState?.language ?? "en";
          const story =
            (language === "ko" && mission.briefing_ko) ||
            mission.briefing ||
            "No briefing on file. Jack in and see for yourself.";
          updateProgramRow([]);
          this.renderer.render(
            renderMissionBriefing(
              mission.title,
              mission.fixer,
              story,
              this.layout.cols,
              this.layout.rows,
            ),
            ["BRIEFING", "", "ENTER: continue"],
          );
          return;
        }
      }
      if (this.screen === "prep") {
        const mission = MISSIONS[this.selectedMission];
        if (mission) {
          this.drawPrep(mission);
          return;
        }
      }
      if (this.screen === "jockey_select") {
        updateProgramRow([]);
        this.renderer.render(
          renderJockeySelect(this.selectedJockey, this.layout.cols, this.layout.rows),
          ["JOCKEY", "", `${this.selectedJockey + 1}/${JOCKEYS.length}`],
        );
        return;
      }
      if (this.screen === "menu") this.normalizeMenuSelection();
      else this.menuSelectionNormalized = false;
      const language = this.settingsState?.language ?? "en";
      const view = renderPreGameScreen(
        {
          screen: this.screen,
          menuIndex: this.selectedMenuIndex,
          menuOptions: this.visibleMenu(),
          missionIndex: this.selectedMission,
          missionRows:
            this.screen === "mission_select"
              ? filterMissionsByUniverse(MISSIONS, "sprawl").map((m, i) =>
                  formatMissionOption(m, i, language),
                )
              : [],
          // ADR-0316: the story the mission carries, lifted from the derivative
          // fiction, so the screen says what it is about.
          missionBriefing: (() => {
            if (this.screen !== "mission_select") return null;
            const m = filterMissionsByUniverse(MISSIONS, "sprawl")[this.selectedMission];
            if (!m) return null;
            return (language === "ko" && m.briefing_ko) || m.briefing || null;
          })(),
          // ADR-0318: a mission pick starts a three-mission contract, and the
          // grade in the row is the contract's whole shape. Say it — a contract
          // that completes 2.5% of the time must not look like a 51% mission
          // (owner principle: no choice whose meaning cannot be grasped).
          missionContract: (() => {
            if (this.screen !== "mission_select") return null;
            const m = filterMissionsByUniverse(MISSIONS, "sprawl")[this.selectedMission];
            if (!m) return null;
            const contract = contractFor(m, MISSIONS, (x) => missionIce(x, this.iceTypes));
            const grades = contract.legs.map((leg) => `T${missionGradeOf(leg.mission)}`);
            return `CONTRACT: ${contract.legs.length} missions · ${grades.join("→")}`;
          })(),
          farGridMissions:
            this.screen === "far_grid_hub" ? filterMissionsByUniverse(MISSIONS, "far-grid") : [],
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
            marketItemCount: this.screen === "crafting" ? this.infoMarket.allItems().length : 0,
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
    const iceDelta = this._lastIceHp !== null ? previous.ice.hp - this._lastIceHp : null;
    const playerDelta =
      this._lastPlayerHp !== null ? previous.player.hp - this._lastPlayerHp : null;
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
    this.renderer.render(combatView.grid, combatView.hud, undefined, combatView.shake);
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
  resizeRenderer(): void {
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
      // A live run keeps the last menu screen in `this.screen` (draw() routes
      // by runPhase), so this list has to name every screen a run can be
      // launched from. PREP (ADR-0283 C''') was missing, and the idle alarm
      // stopped firing entirely -- the same "register the screen" footgun as
      // ADR-0275's input handlers.
      ["menu", "mission_select", "prep", "far_grid_hub"].includes(this.screen) &&
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
      if (matrixTravelFrame(this.matrixTravel, now) === null) this.matrixTravel = null;
      if (this.state !== null) this.draw(false);
    }

    // ADR-0262 — the arrival note is a display-only window on the clock;
    // when it lapses the board redraws without it. No input is affected.
    if (this.matrixArrival !== null && !matrixArrivalActive(this.matrixArrival, now)) {
      this.matrixArrival = null;
      if (this.state !== null) this.draw(false);
    }

    // ADR-0262 — the commit panel steps through its fixed stages on the
    // clock. Redraw only when the clock moves it to a new stage, so it
    // settles into its final frame and then stops (no per-frame churn).
    if (
      this.lootCommit !== null &&
      lootCommitStage(this.lootCommit, now, this.reducedMotion) !== this.lootCommitStageShown
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

  /** E2E hook (ADR-0317 3b): the companion's beat while it is on screen, or
   * null once a key has dismissed it (or when the profile has finished a run).
   * Display-only state that never touches GameState. */
  getRunIntroBeat(): DialogueBeat | null {
    return this.runIntroBeat;
  }

  /** E2E hook (ADR-0317 3b): the mid-run beat card while it owns the screen,
   * or null. Also display-only. */
  getBeatCard(): { title: string; speaker: string; lines: string[] } | null {
    if (this.beatCard === null) return null;
    return {
      title: this.beatCard.title,
      speaker: this.beatCard.beat.speaker,
      lines: [...this.beatCard.beat.lines],
    };
  }

  /** E2E hook (ADR-0317 3b): the sign-off the ending screen is showing. */
  getEndingSignoff(): DialogueBeat | null {
    return this.endingSignoff();
  }

  /** E2E hook: current highlighted menu index (position-independent specs). */
  getSelectedMenuIndex(): number {
    return this.selectedMenuIndex;
  }

  /** E2E hook: menu option keys in order (pair with getSelectedMenuIndex). */
  getMenuOptionKeys(): string[] {
    return this.visibleMenu().map((o) => o.key);
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
    if (next.cardRewardTaken && next.cardRewardTaken !== previous.cardRewardTaken) {
      const card = rewardProgram(next.cardRewardTaken);
      const slot = offeredCardIds(next).indexOf(next.cardRewardTaken) + 1;
      this.lootCommit = beginLootCommit(
        card?.name ?? next.cardRewardTaken,
        card ? programEffectTag(card) : "",
        slot > 0 ? slot : 1,
        now,
      );
    } else {
      // ADR-0311: a unique taken at the free pick is deck growth too, but it
      // does not spend the stop — so it must not take the offer rows. Record
      // the name for the inline confirmation and the board arrival.
      const before = ownUniqueId(previous);
      const after = ownUniqueId(next);
      if (before === null && after !== null) {
        const card = rewardProgram(after);
        this.uniqueCommitName = card?.name ?? after;
      }
    }
    // Leaving the loot screen retires the commit and — only when the run
    // stepped back out onto the board — announces the card there. A terminal
    // node goes to the ending, which draws its own screen, so no note.
    if (previous.runPhase === "loot" && next.runPhase !== "loot") {
      const taken = this.lootCommit?.cardName ?? this.uniqueCommitName;
      this.lootCommit = null;
      this.uniqueCommitName = null;
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
    this.pressedProgramName = this.state.deck[handIndex - 1]?.name.toUpperCase() ?? null;
    // P12 — acknowledge the tap inside the game, not only via the button's
    // CSS `:active` state (which vanishes as soon as the finger lifts).
    this.pressFeedback = pressProgramButton(this.pressFeedback, handIndex, Date.now());
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
        console.error("[Game] Failed to initialize settingsState in getter:", e);
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
    "getRunIntroBeat",
    "getBeatCard",
    "getEndingSignoff",
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
        console.info(`[audio] BGM ${muted ? "muted" : "unmuted"} (M to toggle)`);
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
