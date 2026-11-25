import { AsciiRenderer } from "./renderer/canvas";
import { KeyboardInput } from "./input/keyboard";
import { GamepadInput, isGamepadConnected } from "./input/gamepad";
import { mountVirtualGamepad, updateProgramRow, isTouchDevice } from "./input/touch";
import { visibleMenuOptions, type MenuEntry, type MenuOption } from "./renderer/menu";
import {
  renderRunScreen,
  renderCombatScreen,
  composeCombatScreen,
  type RunNarrative,
} from "./renderer/run_screen";
import { matrixTravelFrame, type MatrixTravel } from "./renderer/matrix_travel";
import { renderCombatHints } from "./renderer/combat_hints";
import { FAR_GRID_LOCKED_MESSAGE, isFarGridUnlocked } from "./core/dungeon/far_grid_gate";
import { advanceVfxListBy, WEB_TICK_MS, type CombatVfxInstance } from "./renderer/combat_vfx";
import { hitStopActiveAt, hitStopDeadlineFor } from "./renderer/screen_shake";
import { pickTransitionSfx } from "./core/combat/combat_sfx";
import { programAffordances, rewardAffordances } from "./core/combat/program_affordance";
import { idleAlarmAction } from "./core/combat/idle_alarm";
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
import { iceIntroBeat, endingSignoffBeat, type DialogueBeat } from "./core/state/event_beats";
import { seenIceIntros } from "./core/state/ice_intros";
import { seenPrologues } from "./core/state/prologue_seen";
import { jockeyHandle } from "./core/state/jockey";
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
import type { DungeonCrawler } from "./core/dungeon/dungeon_crawler";
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
import { applyAction, resolveProgramSelection } from "./core/state/state";
import { encounterRoster } from "./core/state/encounter_verbs";
import type { PrepChoice } from "./core/state/prep";
import { isTerminalNode } from "./core/state/run_end";
import type { Grid } from "./core/grid";
import { getLayout, watchLayout, type Layout } from "./core/layout";
import {
  makeRecipesFromData,
  makeMaterialsFromData,
  type Recipe,
  type MaterialDef,
  makeInfoMarket,
} from "./core/state/crafting";
import { DEFAULT_REGISTRY } from "./core/state/equipment";
import { hydrateLoadout, readEquippedIds } from "./core/state/equipment_store";
import { readOwnedIds, type OwnedSet } from "./core/state/owned_equipment";
import { readWalletMaterials } from "./core/state/wallet";
import type { InfoMarket } from "./core/info_market";
import { loadPersistedLanguage } from "./renderer/settings";
import { drawPrep, drawPreGame } from "./app/pre_game_render";
import { handleGameAction } from "./app/game_input";
import {
  autosaveRun,
  continueRun,
  refreshSaveCache,
  startDungeonCrawl,
  startRun,
} from "./app/run_lifecycle";

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

/** A story card: a title, and the voice it carries (ADR-0317 3b).
 * Lives in `app/pre_game_input.ts` now; re-exported here for the beat queue. */
type BeatCard = import("./app/pre_game_input.ts").BeatCard;

class Game {
  state: GameState | null = null;
  screen: ScreenKind = "menu";
  selectedMenuIndex = 0;
  /** ADR-0315: the cursor is normalized once per visit, not per frame. */
  menuSelectionNormalized = false;
  selectedMission = 0;
  /** ADR-0274 — the jockey chosen for the next run (index into JOCKEYS). */
  selectedJockey = 0;
  /** ADR-0283: the prep row under the cursor, and what it will buy. */
  prepCursor = 0;
  /** Where the run's screen was before the between-leg advance took over
   * (ADR-0318 (a)). Restoring it keeps the run's screen invariant intact — a
   * CONTINUE resumes with `menu`, a fresh run with `prep`. */
  contractPrepReturn: ScreenKind = "prep";
  prepChoice: PrepChoice = "stim";
  /** ADR-0284: what the stockpile will pay for the run about to start. */
  prepWalletOutlay = 0;
  renderer: AsciiRenderer;
  /** Lazy audio loader, gated on the audio-off flag. Exposed as a field so the
   * settings handler (app/settings_input.ts) takes the same gate everything
   * else does. */
  loadAudio = loadAudioSystem;
  /** Lazy story system, the same loader the graphic-novel screen uses. */
  loadStory = loadStorySystem;
  /** The settings default when the real read fails; shared with the renderer. */
  fallbackSettings = fallbackSettingsState;
  /** The crafting registry loader, shared with the run life cycle. */
  loadCrafting = loadCraftingData;
  private input: KeyboardInput;
  private gamepad: GamepadInput;
  iceTypes: Readonly<Record<string, Ice>>;
  programs: Readonly<Record<string, Program>>;
  missions: ReadonlyArray<Mission>;
  hasSaveCache: boolean = false;
  saveMetaCache: {
    missionId: string;
    turnCount: number;
    savedAt: string;
  } | null = null;
  private unmountTouch: () => void = () => {};
  private unwatchLayout: () => void = () => {};
  private _lastPhase: GamePhase | null = null;
  _lastIceHp: number | null = null;
  _lastPlayerHp: number | null = null;
  inventory: Inventory;
  /** ADR-0323: the wallet this run was seeded with, so the merge back into the
   * hoard can tell what the run EARNED from what it inherited. */
  runWalletSeed: Inventory | null = null;
  equipmentLoadout: EquipmentLoadout;
  recipes: ReadonlyArray<Recipe>;
  materials: ReadonlyArray<MaterialDef>;
  infoMarket: InfoMarket;
  /** ADR-0325: the gear the runner owns (starters + crafted). The EQUIPMENT
   *  menu equips only from this set, so a craft finally buys something wearable. */
  ownedEquipment: OwnedSet;
  layout: Layout;
  tutorialActive = false;
  tutorialOverlay: ReturnType<typeof createTutorialOverlay> | null = null;
  /** P11 — the combat-entry hint is shown once per run, on the first combat
   * screen the player reaches. */
  private combatEntryHintShown = false;
  /** The Matrix-entry hint, same once-per-session pattern: shown on the
   * first board with a route, dismissed by the first input made there. */
  matrixEntryHintShown = false;
  /** The Matrix board's traversal after a confirmed move: visual only and
   * never on `GameState`, so it is neither saved nor seen by the reducer.
   * Null under reduced motion, and replaced by the next input. */
  matrixTravel: MatrixTravel | null = null;
  /** ADR-0262 — display-only growth reveal. Controller-owned and transient:
   * never on `GameState`, so it cannot reach a save, the reducer or the
   * harness. The `matrixTravel` pattern, applied to a card joining the deck. */
  lootCommit: LootCommit | null = null;
  /** ADR-0311 — the unique taken at the free pick. The loot commit panel owns
   * the offer rows (a card ends the stop), so the unique is confirmed inline
   * and its name is carried to the board arrival instead. */
  private uniqueCommitName: string | null = null;
  matrixArrival: MatrixArrival | null = null;
  /** ADR-0272 — the arc's framing beat, shown once when a run starts. Null
   * when there is no run, or once a key has dismissed it. Never saved, so a
   * resumed run does not replay its introduction. */
  runIntroArc: ArcId | null = null;
  /** ADR-0317 (3b): the companion's first words, spoken on the run's opening
   * card. Set with `runIntroArc` and cleared with it — display-only, never
   * saved. Null once the player has finished a run, or after the first key. */
  runIntroBeat: DialogueBeat | null = null;
  /** ADR-0317 (3b): a one-time beat card that owns the screen until a key.
   * Same shape as the run intro, but for beats that arrive mid-run (the first
   * fight, the first win) and would not fit inline on a dense panel. */
  beatCard: BeatCard | null = null;
  /** Cards waiting their turn. A transition can have more than one thing to say
   * (the fixer's debrief, then the next job), and a card owns the screen. */
  beatQueue: BeatCard[] = [];
  /** The commit stage last drawn — the loop redraws only when the clock
   * pushes the panel to a new stage, then stops (ADR-0262). */
  private lootCommitStageShown = -1;
  /** ADR-0252: slot-0 writes and the retirement run in order. */
  persistQueue: Promise<void> = Promise.resolve();
  lastPersistedState: GameState | null = null;
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
  graphicNovelPlayer: import("./core/graphic_novel/graphic_novel.ts").GraphicNovelPlayer | null =
    null;
  gnLanguage: import("./core/graphic_novel/graphic_novel_types.ts").Language = "en";
  graphicNovelState: import("./core/types.ts").GraphicNovelState | null = null;

  settingsState: import("./renderer/settings.ts").SettingsState | null = null;
  pwaController: PwaController | null = null;
  dungeonCrawler: DungeonCrawler | null = null;
  _message: string = "";
  farGridUnlockedCache: boolean = false;
  private rafId: number | null = null;
  private loopRunning = false;
  private lastLoopMs = 0;
  idleSinceMs = Date.now();
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
    void refreshSaveCache(this);
    const resetIdle = (): void => {
      this.idleSinceMs = Date.now();
    };
    document.addEventListener("keydown", resetIdle);
    document.addEventListener("pointerdown", resetIdle);
    document.addEventListener("visibilitychange", resetIdle);
    const handler = (action: GameAction): void => handleGameAction(this, action);
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

  /** ADR-0317: the graphic novel is the run's opening, not a menu mode. The
   * menu entry that let a player browse it was the validation scaffold and is
   * gone (2026-11-17), so leaving the story — finished or skipped — always hands
   * over to the mission list. */
  initGraphicNovel(mode: PlayMode = "novice"): void {
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

  renderGraphicNovel(): void {
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
  /** ADR-0273: the prologue's epilogue hands over to the run — "the next
   * jack" is the player. The arc intro (ADR-0272) then opens the run. */
  async selectMenuOption(option: MenuOption | undefined): Promise<void> {
    if (!option) return Promise.resolve();
    switch (option) {
      case "new_run":
        // ADR-0274: choose the jockey first, so the run belongs to someone.
        this.screen = "jockey_select";
        this.selectedJockey = 0;
        this.draw();
        break;
      case "dungeon_crawl":
        startDungeonCrawl(this);
        break;
      case "continue":
        void continueRun(this);
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

  /** ADR-0315: the entries this profile has unlocked (the menu grows). */
  visibleMenu(): ReadonlyArray<MenuEntry> {
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
  normalizeMenuSelection(): void {
    if (this.menuSelectionNormalized) return;
    this.menuSelectionNormalized = true;
    const options = this.visibleMenu();
    if (options.length === 0) return;
    // The list is already filtered, so index 0 is always available.
    if (this.selectedMenuIndex >= options.length) this.selectedMenuIndex = 0;
  }

  launchSelected(): void {
    startRun(this);
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
  storagePort(): Storage | null {
    return typeof localStorage === "undefined" ? null : localStorage;
  }

  /** Queue a story card (ADR-0317 3b). One owns the screen at a time; the rest
   * wait their turn, so a transition can say two things in order. */
  showBeat(card: BeatCard): void {
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
      drawPrep(this, this.state.mission);
      return;
    }
    // Tier 5: matrix / loot / ending screens render with a real GameState
    // but their UI is non-combat. Route by runPhase.
    if (this.state !== null && ["matrix", "ending", "loot"].includes(this.state.runPhase)) {
      // ADR-0252: a committed move, a won fight and the ending are saved
      // (or retire the slot) like combat frames are.
      if (persist) autosaveRun(this);
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
      drawPreGame(this);
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
    if (persist) autosaveRun(this);
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

  syncPhase(current: GamePhase): void {
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
  syncGrowthReveal(previous: GameState, next: GameState): void {
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
