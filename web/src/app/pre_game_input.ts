/** The pre-game input ladder.
 *
 * Refactoring Stage 3a-1c (2026-11-25). `handlePreGameInput` was the
 * `if (this.screen === …)` ladder that routes every key while no run is live —
 * menu, jockey select, briefing, prep, mission select, far-grid hub, and the
 * pre-game settings screen. `main.ts` is outside the balance harness's import
 * graph, so e2e is the guard.
 *
 * The settings branch hands off to `app/settings_input.ts`, so this host
 * extends that one rather than repeating its members.
 *
 * Behaviour is preserved exactly.
 */
import type { GameAction, Mission } from "../core/types";
import type { MenuEntry, MenuOption } from "../renderer/menu";
import type { DialogueBeat } from "../core/state/event_beats";
import type { PlayMode } from "../core/graphic_novel/graphic_novel_types";
import { JOCKEYS } from "../core/state/jockey";
import { PREP_OPTIONS, prepGrantFor, type PrepChoice } from "../core/state/prep";
import { readPrepWallet, spendPrepWallet } from "../core/state/prep_wallet";
import { missionGradeOf } from "../core/combat/ice_scaling";
import { filterMissionsByUniverse } from "../core/missions_filter";
import { FAR_GRID_LOCKED_MESSAGE } from "../core/dungeon/far_grid_gate";
import { finnIntroBeat } from "../core/state/event_beats";
import { hasHeardBeat, markBeatHeard } from "../core/state/story_flags";
import { handleSettingsInput, type SettingsInputHost } from "./settings_input";

/** A story card: a title, and the voice it carries (ADR-0317 3b). */
export interface BeatCard {
  readonly title: string;
  readonly beat: DialogueBeat;
}

/** What the pre-game ladder needs from the game controller. */
export interface PreGameInputHost extends SettingsInputHost {
  _message: string;
  selectedMenuIndex: number;
  selectedJockey: number;
  selectedMission: number;
  prepCursor: number;
  prepChoice: PrepChoice;
  prepWalletOutlay: number;
  farGridUnlockedCache: boolean;
  missions: ReadonlyArray<Mission>;
  visibleMenu(): ReadonlyArray<MenuEntry>;
  selectMenuOption(option: MenuOption | undefined): void;
  initGraphicNovel(mode: PlayMode): void;
  launchSelected(): void;
  showBeat(card: BeatCard): void;
}

/** Route one key while no run is live. */
export function handlePreGameInput(host: PreGameInputHost, action: GameAction): void {
  // Digit keys 1-9 → menu selection on menu screen (otherwise → combat program select).
  if (action.type === "select_program" && host.screen === "menu") {
    const options = host.visibleMenu();
    const idx = action.handIndex - 1;
    if (idx >= 0 && idx < options.length) {
      host.selectedMenuIndex = idx;
      const opt = options[idx];
      host.selectMenuOption(opt ? opt.key : undefined);
    }
    return;
  }
  if (host.screen === "menu") {
    const options = host.visibleMenu();
    const count = Math.max(1, options.length);
    if (action.type === "move_south") {
      host.selectedMenuIndex = (host.selectedMenuIndex + 1) % count;
      host.draw();
    } else if (action.type === "move_north") {
      host.selectedMenuIndex = (host.selectedMenuIndex - 1 + count) % count;
      host.draw();
    } else if (action.type === "confirm") {
      const opt = options[host.selectedMenuIndex];
      host.selectMenuOption(opt ? opt.key : undefined);
    } else if (action.type === "jack_out") {
      // No-op: already at top-level menu
      host.draw();
    }
    return;
  }
  if (host.screen === "jockey_select") {
    if (action.type === "move_south") {
      host.selectedJockey = (host.selectedJockey + 1) % JOCKEYS.length;
      host.draw();
    } else if (action.type === "move_north") {
      host.selectedJockey = (host.selectedJockey - 1 + JOCKEYS.length) % JOCKEYS.length;
      host.draw();
    } else if (action.type === "confirm") {
      // ADR-0317: the prologue opens the run — this jockey's story plays,
      // then the mission list. ESC skips the story, not the run.
      host.screen = "graphic_novel";
      host.selectedMission = 0;
      const jockeyId = JOCKEYS[host.selectedJockey]?.id;
      host.initGraphicNovel(
        jockeyId === "veteran" || jockeyId === "heretic" ? jockeyId : "novice",
      );
    } else if (action.type === "jack_out") {
      host.screen = "menu";
      host.draw();
    }
    return;
  }
  if (host.screen === "briefing") {
    // ADR-0317: ENTER continues to the advance; ESC goes back to the list.
    host.screen = action.type === "jack_out" ? "mission_select" : "prep";
    host.draw();
    return;
  }
  if (host.screen === "prep") {
    // ADR-0283 C: spend the fixer's advance. Two rows, so the screen needs no
    // new key -- ↑↓ picks, ENTER jacks in with the pick, ESC goes back.
    const count = PREP_OPTIONS.length;
    if (action.type === "move_south" || action.type === "move_east") {
      host.prepCursor = (host.prepCursor + 1) % count;
      host.draw();
    } else if (action.type === "move_north" || action.type === "move_west") {
      host.prepCursor = (host.prepCursor - 1 + count) % count;
      host.draw();
    } else if (action.type === "confirm") {
      const picked = PREP_OPTIONS[host.prepCursor];
      host.prepChoice = picked?.id ?? "stim";
      // Spend the stockpile's share, then launch.
      const mission = host.missions[host.selectedMission];
      if (mission) {
        const grant = prepGrantFor(missionGradeOf(mission), host.prepChoice, readPrepWallet());
        host.prepWalletOutlay = grant.fromWallet;
        spendPrepWallet(grant.fromWallet);
      }
      host.launchSelected();
    } else if (action.type === "jack_out") {
      host.screen = "mission_select";
      host.draw();
    }
    return;
  }
  if (host.screen === "mission_select") {
    // ADR-0213 isolation: the Sprawl board lists sprawl-universe missions
    // only; far-grid missions live behind the gated hub.
    const sprawlMissions = filterMissionsByUniverse(host.missions, "sprawl");
    if (action.type === "move_south") {
      host.selectedMission = (host.selectedMission + 1) % sprawlMissions.length;
      host.draw();
    } else if (action.type === "move_north") {
      host.selectedMission =
        (host.selectedMission - 1 + sprawlMissions.length) % sprawlMissions.length;
      host.draw();
    } else if (action.type === "confirm") {
      const picked = sprawlMissions[host.selectedMission];
      const fullIndex = picked ? host.missions.indexOf(picked) : -1;
      if (fullIndex >= 0) {
        host.selectedMission = fullIndex;
        host.prepCursor = 0;
        // ADR-0317: the fixer briefs you on the job before you choose the
        // advance. ENTER there continues to prep; ESC comes back here.
        // ADR-0317 3b: the first time, he also introduces himself — the
        // screen is his office, and the game never opened it.
        const storage = typeof localStorage === "undefined" ? null : localStorage;
        if (!hasHeardBeat(storage, "met_the_finn")) {
          const intro = finnIntroBeat(host.settingsState?.language ?? "en");
          if (intro !== null) {
            host.showBeat({ title: "THE FINN", beat: intro });
            markBeatHeard(storage, "met_the_finn");
          }
        }
        host.screen = "briefing";
        host.draw();
      }
    } else if (action.type === "jack_out") {
      host.screen = "menu";
      host.draw();
    }
    return;
  }
  if (host.screen === "far_grid_hub") {
    // ADR-0213 Phase 2: defense in depth — if the unlock flag is missing,
    // bounce back to the main menu rather than running the hub.
    if (!host.farGridUnlockedCache) {
      host.screen = "menu";
      host._message = FAR_GRID_LOCKED_MESSAGE;
      host.draw();
      return;
    }
    const farGridMissions = filterMissionsByUniverse(host.missions, "far-grid");
    if (farGridMissions.length === 0) {
      if (action.type === "jack_out") {
        host.screen = "menu";
        host.draw();
      }
      return;
    }
    if (action.type === "move_south") {
      host.selectedMission = (host.selectedMission + 1) % farGridMissions.length;
      host.draw();
    } else if (action.type === "move_north") {
      host.selectedMission =
        (host.selectedMission - 1 + farGridMissions.length) % farGridMissions.length;
      host.draw();
    } else if (action.type === "confirm") {
      const picked = farGridMissions[host.selectedMission];
      const fullIndex = picked ? host.missions.indexOf(picked) : -1;
      if (fullIndex >= 0) {
        host.selectedMission = fullIndex;
        host.prepCursor = 0;
        host.screen = "prep";
        host.draw();
      }
    } else if (action.type === "jack_out") {
      host.screen = "menu";
      host.draw();
    }
    return;
  }
  if (host.screen === "settings") {
    handleSettingsInput(host, action);
    return;
  }
}
