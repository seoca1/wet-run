/** The graphic novel's keys — the run's prologue screen (ADR-0273/ADR-0317).
 *
 * Refactoring Stage 3a-1d (2026-11-25), the last piece of the pre-run input
 * ladder. `exitGraphicNovel` and `startRunFromGraphicNovel` come along: the
 * handler is their only caller, and leaving the story always hands over to the
 * mission list rather than back to a menu (the mode that let a player browse it
 * was the validation scaffold and is gone).
 *
 * `main.ts` is outside the balance harness's import graph, so e2e is the guard.
 * Behaviour is preserved exactly.
 */
import type { GameAction, GraphicNovelState, ScreenKind } from "../core/types";
import type { GraphicNovelPlayer } from "../core/graphic_novel/graphic_novel";
import type { Language } from "../core/graphic_novel/graphic_novel_types";
import { markPrologueSeen } from "../core/state/prologue_seen";

/** What the prologue's keys need from the game controller. */
export interface GraphicNovelInputHost {
  screen: ScreenKind;
  selectedMission: number;
  graphicNovelPlayer: GraphicNovelPlayer | null;
  graphicNovelState: GraphicNovelState | null;
  gnLanguage: Language;
  storagePort(): Storage | null;
  draw(): void;
  /** Lazy story system, the same loader the renderer uses. */
  loadStory(): Promise<typeof import("../core/graphic_novel/graphic_novel")>;
}

/** ADR-0273 — the graphic novel's keys, as its own footer promises. */
export function handleGraphicNovelInput(host: GraphicNovelInputHost, action: GameAction): void {
  const player = host.graphicNovelPlayer;
  if (!player) {
    exitGraphicNovel(host);
    return;
  }
  if (action.type === "jack_out" || action.type === "cancel") {
    exitGraphicNovel(host);
    return;
  }
  if (action.type === "cycle_target") {
    void host.loadStory().then((gn) => {
      gn.togglePause(player);
      host.graphicNovelState = host.graphicNovelState
        ? { ...host.graphicNovelState, isPaused: player.paused }
        : host.graphicNovelState;
      host.draw();
    });
    return;
  }
  if (action.type !== "confirm") return;
  void host.loadStory().then((gn) => {
    if (host.graphicNovelPlayer !== player) return;
    if (player.done) {
      // Watched to the end. A player who skips has not seen it, so the
      // marker would be a lie — only a finish counts.
      markPrologueSeen(host.storagePort(), player.mode);
      startRunFromGraphicNovel(host);
      return;
    }
    // First press finishes the typed page, the next moves the story on.
    if (!gn.isDialogueComplete(player)) gn.skipCurrentDialogue(player);
    else if (!gn.advanceDialogue(player)) gn.advanceScene(player);
    host.draw();
  });
}

/** Leave the story — finished or skipped. */
export function exitGraphicNovel(host: GraphicNovelInputHost): void {
  host.graphicNovelPlayer = null;
  host.graphicNovelState = null;
  // ADR-0317: the graphic novel is only reachable as the run's prologue, so
  // leaving it (finished or skipped) skips the STORY, not the run.
  startRunFromGraphicNovel(host);
}

/** ADR-0273: the prologue's epilogue hands over to the run — "the next jack"
 * is the player. The arc intro (ADR-0272) then opens the run. */
export function startRunFromGraphicNovel(host: GraphicNovelInputHost): void {
  host.graphicNovelPlayer = null;
  host.graphicNovelState = null;
  host.screen = "mission_select";
  host.selectedMission = 0;
  host.draw();
}
