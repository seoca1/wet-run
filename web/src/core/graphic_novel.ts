/** Graphic novel engine — public re-exports.
 *
 * TypeScript port of wet_run/prototype/src/wet_run/engine/graphic_novel_{data,
 * loaders,save,render/text,scene,audio}.py.
 *
 * Scope: pure logic + text utilities + state machine. Rendering is intentionally
 * not included (it lives on the canvas-renderer side, mirroring the Python
 * engine's split).
 *
 * Auto-play loop:
 *   - Within a dialogue: type out text at 30ms/char.
 *   - After duration: advance to next dialogue.
 *   - After last dialogue: advance to next scene.
 *   - After last scene: chain_complete + done.
 */

export type {
  CharacterId,
  PlayMode,
  Language,
  Ending,
  DialogueLine,
  SceneData,
  ScenesFile,
  GraphicNovelProgress,
  GraphicNovelPlayer,
  TickEvent,
} from "./graphic_novel_types.ts";

export {
  NOVEL_LEFT_MARGIN,
  NOVEL_RIGHT_MARGIN,
  MS_PER_CHAR,
  DEFAULT_PAGE_WIDTH,
  DEFAULT_LINES_PER_PAGE,
  toRoman,
  wrapTextForNovel,
  paginateLines,
  computeTypedPageIndex,
  dialogueTypedChars,
  sceneProgress,
  characterLabel,
} from "./graphic_novel_text.ts";

export {
  CHAR_TO_DIR,
  SCENE_SOUND_MAP,
  listScenesForCharacter,
  loadSceneChain,
  loadPrologueChain,
  resolveSound,
  soundCategory,
} from "./graphic_novel_loaders.ts";

export {
  GN_SAVE_VERSION,
  createPlayer,
  currentScene,
  currentDialogue,
  currentText,
  currentSpeaker,
  currentTitle,
  currentSound,
  progress,
  isDialogueComplete,
  tick,
  skipCurrentDialogue,
  skipCurrentScene,
  togglePause,
  advanceScene,
  advanceDialogue,
  restart,
  snapshotProgress,
  restoreProgress,
  isValidProgress,
  coerceProgress,
} from "./graphic_novel_player.ts";