/** Graphic novel — type definitions.
 *
 * Mirrors the @dataclass(frozen=True, slots=True) shapes from
 * wet_run/prototype/src/wet_run/engine/graphic_novel_data.py.
 *
 * Module breakdown:
 *   - graphic_novel_types.ts: this file — type contracts only
 *   - graphic_novel_loaders.ts: scene/chain loading
 *   - graphic_novel_text.ts: text utilities (wrap, paginate, typed cursor)
 *   - graphic_novel_player.ts: state machine + tick + reducers
 *   - graphic_novel.ts: public re-exports
 */

/** Character identifiers used in scene.character and dialogue.portrait refs. */
export type CharacterId =
  | "novice"     // Case (K)
  | "veteran"    // Marly (Sil)
  | "heretic"    // Kumiko (Kas)
  | "suit"       // reserved (data not bundled)
  | "wigan"
  | "angie"
  | "sally"
  | "3jane"
  | "neuromancer";

/** Play mode for the engine. */
export type PlayMode = "prologue" | "novice" | "veteran" | "heretic";

/** Language toggle for text + speaker selection. */
export type Language = "en" | "ko";

/** Ending variant (ADR-0048). Only "A" is bundled for MVP. */
export type Ending = "A" | "B" | "C";

/** A single dialogue beat within a scene. */
export interface DialogueLine {
  readonly speaker: string;
  readonly speaker_ko: string;
  readonly portrait: string | null;
  readonly text_en: string;
  readonly text_ko: string;
  readonly duration_ms: number;
  readonly sound: string | null;
}

/** A complete scene — art refs + dialogue beats + chain link. */
export interface SceneData {
  readonly id: string;
  readonly character: CharacterId | string;
  readonly order: number;
  readonly ending: Ending;
  readonly title_en: string;
  readonly title_ko: string;
  readonly background_id: string;
  readonly portrait_left: string | null;
  readonly portrait_right: string | null;
  readonly dialogue: ReadonlyArray<DialogueLine>;
  readonly next_scene: string | null;
  /** Mission hook (Python attribute; informational). */
  readonly mission_id?: string;
}

/** Top-level scenes.json envelope. */
export interface ScenesFile {
  readonly version: string;
  readonly source: string;
  readonly characters: Readonly<Record<string, CharacterId>>;
  readonly scene_count: number;
  readonly scenes: Readonly<Record<string, SceneData>>;
}

/** Persisted progress snapshot (ADR-0044). */
export interface GraphicNovelProgress {
  readonly mode: PlayMode;
  readonly scene_index: number;
  readonly dialogue_index: number;
  readonly elapsed_in_dialogue_ms: number;
  readonly character_id: CharacterId;
  readonly chain_length: number;
  readonly ending: Ending;
  readonly saved_at: string;
  readonly session_id: string;
}

/** Live playback state — mutated only via engine reducers. */
export interface GraphicNovelPlayer {
  mode: PlayMode;
  readonly chain: ReadonlyArray<SceneData>;
  character_id: CharacterId;
  ending: Ending;
  scene_index: number;
  dialogue_index: number;
  elapsed_ms: number;
  paused: boolean;
  done: boolean;
}

/** Event emitted by tick() for the renderer / sound layer. */
export interface TickEvent {
  readonly type: "dialogue_complete" | "scene_complete" | "chain_complete";
  readonly sceneId: string;
  readonly dialogueIndex: number;
}