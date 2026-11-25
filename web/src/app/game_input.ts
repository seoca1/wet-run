/** The input pipeline: one key, from the screen that owns it to the reducer.
 *
 * Refactoring Stage 3a-4 (2026-11-25). This was the `handler` closure inside
 * `Game`'s constructor - 289 lines, the largest single piece left in the
 * controller. It is a layer rather than plumbing: route the key to the screen
 * that owns it, apply the action through the reducer, then fire the beats and
 * detect the three ways a run ends. Unlike `draw`'s frame router it does not
 * persist anything itself, so it moves cleanly.
 *
 * `handleContractPrepInput` comes along: the pipeline was its only caller.
 *
 * `main.ts` is outside the balance harness's import graph, so e2e is the guard.
 * Behaviour is preserved exactly, with one named difference: the constructor's
 * local `resetIdle()` becomes a direct `host.idleSinceMs = Date.now()`, which
 * is the same statement `resetIdle` performed.
 */
import type { GameAction, GameState, ScreenKind } from "../core/types";
import type { MatrixTravel } from "../renderer/matrix_travel";
import type { PrepChoice } from "../core/state/prep";
import type { BeatCard } from "./pre_game_input";
import { applyAction, resolveProgramSelection } from "../core/state/state";
import { encounterRoster, runAbandoned } from "../core/state/encounter_verbs";
import { markIceIntrosSeen } from "../core/state/ice_intros";
import { hasHeardBeat, markBeatHeard } from "../core/state/story_flags";
import {
  firstFightWarningBeat,
  firstVictoryBeat,
  flatlineBeat,
  firstReturnBeat,
  ashpoolCallBeat,
} from "../core/state/event_beats";
import {
  FLATLINE_MESSAGE,
  RUN_COMPLETE_MESSAGE,
  runCompleted,
  runFailed,
} from "../core/state/run_end";
import { pickTransitionSfx } from "../core/combat/combat_sfx";
import { PREP_OPTIONS, prepGrantFor } from "../core/state/prep";
import { readPrepWallet, spendPrepWallet } from "../core/state/prep_wallet";
import { missionGradeOf } from "../core/combat/ice_scaling";
import { applyPrep } from "../core/state/prep";
import { beginMatrixTravel } from "../renderer/matrix_travel";
import {
  handleCraftingInput,
  handleDungeonInput,
  handleEquipmentInput,
  handlePauseInput,
  handleSettingsStubInput,
  handleStubInput,
  type ScreenInputHost,
} from "./screen_input";
import { handlePreGameInput, type PreGameInputHost } from "./pre_game_input";
import { handleGraphicNovelInput, type GraphicNovelInputHost } from "./graphic_novel_input";
import {
  noteRunFinished,
  refreshSaveCache,
  settleRun,
  type RunLifecycleHost,
} from "./run_lifecycle";
import { shouldShowMatrixEntryHint } from "../core/state/onboarding";

/** Pre-game screens that handle their own keys (ADR-0275). A screen missing
 * from this set is a stub: no run state, ENTER returns to the title. Adding a
 * screen means adding it here, in one place, with a handler. */
export const SCREENS_WITH_INPUT: ReadonlySet<ScreenKind> = new Set([
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

/** What the input pipeline needs from the game controller.
 *
 * The pipeline is the thing that dispatches to every other layer, so its host
 * composes theirs rather than restating them - the same shape as
 * `PreGameInputHost extends SettingsInputHost`. Only the members the pipeline
 * itself owns are declared here. */
export interface GameInputHost
  extends ScreenInputHost, PreGameInputHost, GraphicNovelInputHost, RunLifecycleHost {
  idleSinceMs: number;
  beatCard: BeatCard | null;
  beatQueue: BeatCard[];
  tutorialActive: boolean;
  tutorialOverlay: ReturnType<typeof import("../renderer/tutorial").createTutorialOverlay> | null;
  matrixEntryHintShown: boolean;
  matrixTravel: MatrixTravel | null;
  contractPrepReturn: ScreenKind;
  syncGrowthReveal(previous: GameState, next: GameState): void;
}

/** Route one key through the pipeline. */
export function handleGameAction(host: GameInputHost, action: GameAction): void {
  host.idleSinceMs = Date.now();
  // ADR-0317 (3b): a beat card owns the screen until a key, whatever is
  // behind it. It has to be checked FIRST: the fixer's introduction fires on
  // the mission list, and a card that draws over a screen without consuming
  // its keys let the briefing and prep advance invisibly behind it.
  if (host.beatCard !== null) {
    host.beatCard = host.beatQueue.shift() ?? null;
    host.draw();
    return;
  }
  // Screens that own their input. This used to be an inline list of
  // screens to *exclude*, so any screen someone forgot to add fell into
  // `handleStubInput` and ENTER bounced to the menu -- which is exactly
  // what happened to the graphic novel (ADR-0273) and then to the jockey
  // select (ADR-0274) in the same session. Anything with no run state that
  // is not in this set is a stub, by construction.
  if (host.state === null && !SCREENS_WITH_INPUT.has(host.screen)) {
    handleStubInput(host, action);
    return;
  }
  if (host.tutorialActive && host.tutorialOverlay) {
    const result = host.tutorialOverlay.handleInput(
      action.type === "jack_out" || action.type === "cancel"
        ? "Escape"
        : action.type === "confirm"
          ? "Enter"
          : action.type,
    );
    if (result.action === "next" || result.action === "skip") {
      if (result.action === "skip" || host.tutorialOverlay.state.currentStep >= 6) {
        host.tutorialActive = false;
        host.tutorialOverlay = null;
        host.screen = "menu";
      }
      host.draw();
    }
    return;
  }
  // Dungeon crawler has its own self-contained state (DungeonCrawler instance);
  // it must be handled before the `state === null` pre-game shortcut.
  if (host.screen === "dungeon") {
    handleDungeonInput(host, action);
    host.draw();
    return;
  }
  // ADR-0273: the graphic novel is its own screen with its own keys. The
  // renderer had always printed "ENTER: skip dialogue | P: pause | ESC:
  // exit", but nothing routed them: the mode showed one frame and ENTER
  // fell through to the menu, so the prologue could not be read at all.
  if (host.screen === "graphic_novel") {
    handleGraphicNovelInput(host, action);
    return;
  }
  if (host.state === null) {
    handlePreGameInput(host, action);
    return;
  }
  // ADR-0318 (a): the advance between a contract's legs owns the input the
  // same way the crafting screens do — the run state is live behind it.
  if (host.screen === "contract_prep") {
    handleContractPrepInput(host, action);
    return;
  }
  if (host.screen === "crafting" || host.screen === "equipment") {
    if (host.screen === "crafting") handleCraftingInput(host, action);
    else handleEquipmentInput(host, action);
    host.draw();
    return;
  }
  if (host.screen === "settings") {
    handleSettingsStubInput(host, action);
    host.draw();
    return;
  }
  if (host.screen === "pause") {
    handlePauseInput(host, action);
    host.draw();
    return;
  }
  // ADR-0272: the opening beat consumes the first key. It is a screen, not
  // an animation gate: nothing advances on its own and nothing is queued.
  if (host.runIntroArc !== null) {
    host.runIntroArc = null;
    host.runIntroBeat = null;
    host.draw();
    return;
  }
  const resolved: GameAction = (() => {
    if (host.state === null) return action;
    const r = resolveProgramSelection(host.state, action);
    return r ?? action;
  })();
  const previous = host.state;
  if (shouldShowMatrixEntryHint(host.matrixEntryHintShown, host.state))
    host.matrixEntryHintShown = true;
  host.state = applyAction(host.state, resolved);
  // ADR-0317 (3b): the reveal is the one moment this ICE's voice is new.
  // Remember it so the tagline is spoken once per profile, not per node.
  const revealed = host.state;
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
    const language = host.settingsState?.language ?? "en";
    if (
      previous?.phase !== "combat" &&
      revealed.phase === "combat" &&
      !hasHeardBeat(storage, "first_fight_warning")
    ) {
      const beat = firstFightWarningBeat(language);
      if (beat !== null) {
        host.showBeat({ title: "ICE AHEAD", beat });
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
        host.showBeat({ title: "FIRST BLOOD", beat });
        markBeatHeard(storage, "first_victory");
      }
    }
    // ADR-0317 3b: the one moment the story went silent was the one it had
    // been building to. She warned that she can only watch; this is her
    // watching. Once per run, right after the killing blow.
    if (previous?.runPhase !== "dead" && revealed.runPhase === "dead") {
      const beat = flatlineBeat(language);
      if (beat !== null) host.showBeat({ title: "FLATLINE", beat });
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
        host.showBeat({
          title: `CONTRACT ${contract?.completed ?? 0}/${contract?.legs.length ?? 0} · DONE`,
          beat: debrief,
        });
      }
      // ADR-0318 (a): the next leg's advance. The reducer built the leg
      // already; the prep screen spends the fixer's advance on it. The
      // briefing card is read first (a card owns the screen).
      host.prepCursor = 0;
      host.contractPrepReturn = host.screen;
      host.screen = "contract_prep";
      host.showBeat({
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
  if (runAbandoned(previous, host.state)) {
    // JACK OUT ends the run: leave the board for the main menu.
    // ADR-0323: the run is over — bank what it earned before dropping it.
    settleRun(host);
    host.state = null;
    host.matrixTravel = null;
    host.lootCommit = null;
    host.matrixArrival = null;
    host.screen = "menu";
    void refreshSaveCache(host);
    host.draw();
    return;
  }
  if (runCompleted(previous, host.state)) {
    // ADR-0252: the ending is the end. The slot was retired on arrival.
    // ADR-0323: the run is over — bank what it earned before dropping it.
    settleRun(host);
    host.state = null;
    host.matrixTravel = null;
    host.lootCommit = null;
    host.matrixArrival = null;
    host.screen = "menu";
    host._message = RUN_COMPLETE_MESSAGE;
    noteRunFinished(host);
    host.persistQueue = host.persistQueue.then(() => refreshSaveCache(host)).catch(() => undefined);
    host.draw();
    return;
  }
  if (runFailed(previous, host.state)) {
    // ADR-0263: a flatline must not trap the player. ENTER / ESC leave the
    // defeat screen and the run ends at the title, the same shape as the
    // ending. The dead frame itself was already autosaved (ADR-0252 §A).
    // ADR-0323: the run is over — bank what it earned before dropping it.
    settleRun(host);
    host.state = null;
    host.matrixTravel = null;
    host.lootCommit = null;
    host.matrixArrival = null;
    host.screen = "menu";
    host._message = FLATLINE_MESSAGE;
    noteRunFinished(host);
    void refreshSaveCache(host);
    host.draw();
    return;
  }
  // The reducer has already moved `@`; this only chooses the next frames.
  // Every input re-derives it, so input never waits on (or redirects) it.
  host.matrixTravel = beginMatrixTravel(
    previous,
    host.state,
    performance.now(),
    host.reducedMotion,
  );
  host.syncGrowthReveal(previous, host.state);
  void host.loadAudio().then((audio) => {
    if (!audio) return;
    const manager = audio.AudioManager.getInstance();
    // P5 — the player taking damage had no sound at all (proposal §1.2
    // U13). `pickTransitionSfx` decides the transition's audio from the
    // (previous → next) state pair: the combat layers plus the ADR-0251
    // event ids (boss intro / phase change, credits, loot, heal, death).
    const nextState = host.state;
    if (nextState !== null) {
      for (const id of pickTransitionSfx(previous, nextState)) {
        manager.playSfx(id);
      }
    }
    if (
      resolved.type === "use_program" &&
      previous.phase === "combat" &&
      host.state?.phase === "combat"
    ) {
      // The ICE-hit sound now comes from `pickTransitionSfx` above.
      // The old `state.ice.hp` delta check was provably dead — the
      // reducers only ever write `iceRoster`, so `state.ice.hp` never
      // changed after init and `COMBAT_HIT` never fired from here.
      const iceDelta = host.state.ice.hp - previous.ice.hp;
      // (The boss-phase sound used to sit in this dead branch as
      // VICTORY; `pickTransitionSfx` now plays PHASE_CHANGE for it.)
      if (iceDelta < 0) {
        host._lastIceHp = host.state.ice.hp;
        host._lastPlayerHp = host.state.player.hp;
      }
      if (previous.runPhase === "matrix" && host.state.runPhase === "combat") {
        manager.playSfx(audio.SFX_IDS.COMBAT_HIT);
      }
      const burnTickDmg = host.state.player.hp - previous.player.hp;
      if (burnTickDmg > 0 && previous.runPhase === "combat" && host.state.runPhase === "combat") {
        manager.playSfx(audio.SFX_IDS.DEFEAT);
      }
    }
  });
  host.draw();
}

/** The advance between a contract's legs (ADR-0318 (a)). */
function handleContractPrepInput(host: GameInputHost, action: GameAction): void {
  const state = host.state;
  if (state === null) return;
  const count = PREP_OPTIONS.length;
  if (action.type === "move_south" || action.type === "move_east") {
    host.prepCursor = (host.prepCursor + 1) % count;
    host.draw();
    return;
  }
  if (action.type === "move_north" || action.type === "move_west") {
    host.prepCursor = (host.prepCursor - 1 + count) % count;
    host.draw();
    return;
  }
  const spent = action.type === "confirm" || action.type === "jack_out" || action.type === "cancel";
  if (!spent) return;
  if (action.type === "confirm") {
    const choice: PrepChoice = PREP_OPTIONS[host.prepCursor]?.id ?? "stim";
    const grant = prepGrantFor(missionGradeOf(state.mission), choice, readPrepWallet());
    host.prepWalletOutlay = grant.fromWallet;
    spendPrepWallet(grant.fromWallet);
    host.state = applyPrep(state, choice, host.prepWalletOutlay);
  }
  // Back to the run: `draw()` routes by runPhase once the screen is not the
  // prep, so the leg's board takes over.
  host.screen = host.contractPrepReturn;
  host.draw();
}
