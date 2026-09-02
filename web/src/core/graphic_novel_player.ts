/** Graphic novel — playback state machine.
 *
 * Mirrors the auto-play semantics in
 * wet_run/prototype/src/wet_run/engine/main_loop.py:
 *   - elapsed_ms accumulates wall time per frame
 *   - when elapsed_ms >= dialogue.duration_ms, advance dialogue (or scene)
 *   - chain_complete fires when scene_index exceeds chain.length
 *
 * Drain semantics: a single tick() may advance through many dialogues if
 * deltaMs is large (e.g. tab was backgrounded) so the engine always catches
 * up to wall time.
 */

import {
  loadPrologueChain,
  loadSceneChain,
  resolveSound,
} from "./graphic_novel_loaders.ts";
import { dialogueTypedChars, sceneProgress } from "./graphic_novel_text.ts";
import type {
  CharacterId,
  DialogueLine,
  Ending,
  GraphicNovelPlayer,
  GraphicNovelProgress,
  Language,
  PlayMode,
  SceneData,
  TickEvent,
} from "./graphic_novel_types.ts";

export const GN_SAVE_VERSION = "1.2.0";

/* -------------------------------------------------------------------------- *
 *  Factory
 * -------------------------------------------------------------------------- */

let sessionCounter = 0;

function nextSessionId(): string {
  sessionCounter = (sessionCounter + 1) >>> 0;
  const rand = Math.floor(Math.random() * 0x100000).toString(16).padStart(5, "0");
  return `${Date.now().toString(36)}-${sessionCounter.toString(36)}-${rand}`;
}

/** Construct a fresh player for the given mode. */
export function createPlayer(options: {
  readonly mode: PlayMode;
  readonly ending?: Ending;
  readonly seed?: number;
  readonly maxOrder?: number;
}): GraphicNovelPlayer {
  const ending = options.ending ?? "A";
  const chain = options.mode === "prologue"
    ? loadPrologueChain({
        seed: options.seed,
        ending,
        maxOrder: options.maxOrder ?? 8,
      })
    : loadSceneChain(options.mode, {
        shuffle: true,
        seed: options.seed,
        ending,
        maxOrder: options.maxOrder,
      });
  const characterId: CharacterId = options.mode === "prologue"
    ? (chain[0]?.character as CharacterId | undefined) ?? "novice"
    : options.mode;
  return {
    mode: options.mode,
    chain,
    character_id: characterId,
    ending,
    scene_index: 0,
    dialogue_index: 0,
    elapsed_ms: 0,
    paused: false,
    done: chain.length === 0,
  };
}

/* -------------------------------------------------------------------------- *
 *  Read-only queries
 * -------------------------------------------------------------------------- */

export function currentScene(p: GraphicNovelPlayer): SceneData | null {
  return p.chain[p.scene_index] ?? null;
}

export function currentDialogue(p: GraphicNovelPlayer): DialogueLine | null {
  const scene = currentScene(p);
  if (scene === null) return null;
  return scene.dialogue[p.dialogue_index] ?? null;
}

export function currentText(p: GraphicNovelPlayer, lang: Language): string {
  const d = currentDialogue(p);
  if (d === null) return "";
  return lang === "ko" ? d.text_ko : d.text_en;
}

export function currentSpeaker(p: GraphicNovelPlayer, lang: Language): string {
  const d = currentDialogue(p);
  if (d === null) return "";
  return lang === "ko" ? d.speaker_ko : d.speaker;
}

export function currentTitle(p: GraphicNovelPlayer, lang: Language): string {
  const s = currentScene(p);
  if (s === null) return "";
  return lang === "ko" ? s.title_ko : s.title_en;
}

export function currentSound(p: GraphicNovelPlayer): string | null {
  const d = currentDialogue(p);
  return resolveSound(d?.sound ?? null);
}

export function progress(p: GraphicNovelPlayer): number {
  return sceneProgress(p.scene_index, p.chain.length);
}

export function isDialogueComplete(p: GraphicNovelPlayer): boolean {
  const d = currentDialogue(p);
  if (d === null) return true;
  return dialogueTypedChars(d.duration_ms, p.elapsed_ms, d.text_en.length)
    >= d.text_en.length;
}

/* -------------------------------------------------------------------------- *
 *  Reducers
 * -------------------------------------------------------------------------- */

/** Advance playback by deltaMs of wall time. Returns events for the renderer. */
export function tick(p: GraphicNovelPlayer, deltaMs: number): ReadonlyArray<TickEvent> {
  if (p.done || p.paused) return Object.freeze([]);
  const events: TickEvent[] = [];
  p.elapsed_ms += deltaMs;

  let safety = 0;
  while (!p.done && !p.paused && safety++ < 1000) {
    const scene = currentScene(p);
    if (scene === null) {
      p.done = true;
      events.push({ type: "chain_complete", sceneId: "", dialogueIndex: 0 });
      break;
    }
    const dlg = scene.dialogue[p.dialogue_index];
    if (dlg === undefined) {
      events.push({
        type: "scene_complete",
        sceneId: scene.id,
        dialogueIndex: p.dialogue_index,
      });
      advanceSceneInternal(p);
      continue;
    }
    if (p.elapsed_ms < dlg.duration_ms) break;
    p.elapsed_ms -= dlg.duration_ms;
    events.push({
      type: "dialogue_complete",
      sceneId: scene.id,
      dialogueIndex: p.dialogue_index,
    });
    p.dialogue_index += 1;
    if (p.dialogue_index >= scene.dialogue.length) {
      events.push({
        type: "scene_complete",
        sceneId: scene.id,
        dialogueIndex: p.dialogue_index - 1,
      });
      advanceSceneInternal(p);
      if (p.done) {
        events.push({
          type: "chain_complete",
          sceneId: scene.id,
          dialogueIndex: p.dialogue_index - 1,
        });
        break;
      }
    }
  }
  return Object.freeze(events);
}

function advanceSceneInternal(p: GraphicNovelPlayer): void {
  p.scene_index += 1;
  p.dialogue_index = 0;
  p.elapsed_ms = 0;
  if (p.scene_index >= p.chain.length) {
    p.done = true;
    p.scene_index = p.chain.length;
  }
}

export function skipCurrentDialogue(p: GraphicNovelPlayer): boolean {
  const d = currentDialogue(p);
  if (d === null) return false;
  p.elapsed_ms = d.duration_ms;
  return true;
}

export function skipCurrentScene(p: GraphicNovelPlayer): boolean {
  const scene = currentScene(p);
  if (scene === null) return false;
  skipCurrentDialogue(p);
  while (!p.done) {
    const s = currentScene(p);
    if (s === null || s.id !== scene.id) break;
    const dlgs = s.dialogue;
    if (p.dialogue_index >= dlgs.length) break;
    const d = dlgs[p.dialogue_index];
    if (d === undefined) break;
    p.elapsed_ms = d.duration_ms;
    const typed = dialogueTypedChars(d.duration_ms, p.elapsed_ms, d.text_en.length);
    if (typed >= d.text_en.length) {
      p.dialogue_index += 1;
      if (p.dialogue_index >= dlgs.length) {
        advanceSceneInternal(p);
        break;
      }
    }
  }
  return true;
}

export function togglePause(p: GraphicNovelPlayer): boolean {
  if (p.done) return p.paused;
  p.paused = !p.paused;
  return p.paused;
}

export function advanceScene(p: GraphicNovelPlayer): boolean {
  if (currentScene(p) === null) return false;
  advanceSceneInternal(p);
  return true;
}

export function advanceDialogue(p: GraphicNovelPlayer): boolean {
  const scene = currentScene(p);
  if (scene === null) return false;
  if (p.dialogue_index + 1 < scene.dialogue.length) {
    p.dialogue_index += 1;
    p.elapsed_ms = 0;
    return true;
  }
  return false;
}

export function restart(p: GraphicNovelPlayer): void {
  p.scene_index = 0;
  p.dialogue_index = 0;
  p.elapsed_ms = 0;
  p.paused = false;
  p.done = p.chain.length === 0;
}

/* -------------------------------------------------------------------------- *
 *  Save / restore (ADR-0044) — pure data layer (no I/O).
 * -------------------------------------------------------------------------- */

export function snapshotProgress(p: GraphicNovelPlayer): GraphicNovelProgress {
  return {
    mode: p.mode,
    scene_index: p.scene_index,
    dialogue_index: p.dialogue_index,
    elapsed_in_dialogue_ms: p.elapsed_ms,
    character_id: p.character_id,
    chain_length: p.chain.length,
    ending: p.ending,
    saved_at: new Date().toISOString(),
    session_id: nextSessionId(),
  };
}

export function restoreProgress(
  progress: GraphicNovelProgress,
  options: { readonly seed?: number } = {},
): GraphicNovelPlayer {
  const chain = progress.mode === "prologue"
    ? loadPrologueChain({
        seed: options.seed,
        ending: progress.ending,
        maxOrder: 8,
      })
    : loadSceneChain(progress.character_id, {
        seed: options.seed,
        ending: progress.ending,
      });
  const clampedScene = Math.min(progress.scene_index, chain.length);
  const scene = chain[clampedScene];
  const clampedDialogue = scene === undefined
    ? 0
    : Math.min(progress.dialogue_index, scene.dialogue.length);
  return {
    mode: progress.mode,
    chain,
    character_id: progress.character_id,
    ending: progress.ending,
    scene_index: clampedScene,
    dialogue_index: clampedDialogue,
    elapsed_ms: Math.max(0, progress.elapsed_in_dialogue_ms),
    paused: false,
    done: chain.length === 0,
  };
}

export function isValidProgress(value: unknown): value is GraphicNovelProgress {
  if (typeof value !== "object" || value === null) return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.mode === "string" &&
    typeof v.scene_index === "number" &&
    typeof v.dialogue_index === "number" &&
    typeof v.elapsed_in_dialogue_ms === "number" &&
    typeof v.character_id === "string" &&
    typeof v.chain_length === "number" &&
    typeof v.saved_at === "string" &&
    typeof v.ending === "string" &&
    (v.ending === "A" || v.ending === "B" || v.ending === "C") &&
    typeof v.session_id === "string"
  );
}

/** Coerce a parsed JSON value into a safe GraphicNovelProgress (forward-compat). */
export function coerceProgress(value: unknown): GraphicNovelProgress {
  const fallback: GraphicNovelProgress = {
    mode: "prologue",
    scene_index: 0,
    dialogue_index: 0,
    elapsed_in_dialogue_ms: 0,
    character_id: "novice",
    chain_length: 0,
    ending: "A",
    saved_at: new Date(0).toISOString(),
    session_id: nextSessionId(),
  };
  if (!isValidProgress(value)) return fallback;
  return {
    mode: (value.mode === "novice" || value.mode === "veteran" || value.mode === "heretic" || value.mode === "prologue")
      ? value.mode
      : "prologue",
    scene_index: Math.max(0, Math.floor(value.scene_index)),
    dialogue_index: Math.max(0, Math.floor(value.dialogue_index)),
    elapsed_in_dialogue_ms: Math.max(0, value.elapsed_in_dialogue_ms),
    character_id: value.character_id,
    chain_length: Math.max(0, Math.floor(value.chain_length)),
    ending: value.ending,
    saved_at: value.saved_at,
    session_id: value.session_id || nextSessionId(),
  };
}