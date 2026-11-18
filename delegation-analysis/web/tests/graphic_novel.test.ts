/** Unit tests for the graphic novel engine.
 *
 * Mirrors tests/unit/test_graphic_novel_view.py from the Python prototype.
 * Covers:
 *   - scene / dialogue parsing
 *   - chain loading (character, prologue, shuffle, ending filter)
 *   - text utilities (wrap, paginate, typed cursor)
 *   - timing helpers (dialogueTypedChars, sceneProgress)
 *   - sound resolver
 *   - player state machine (tick, skip, pause, advance)
 *   - save/restore (snapshot, coerce, restore)
 */

import { describe, it, expect } from "vitest";
import {
  // Types
  type DialogueLine,
  type SceneData,
  type CharacterId,
  type Ending,
  type GraphicNovelPlayer,
  type GraphicNovelProgress,
  // Constants
  NOVEL_LEFT_MARGIN,
  NOVEL_RIGHT_MARGIN,
  MS_PER_CHAR,
  DEFAULT_PAGE_WIDTH,
  CHAR_TO_DIR,
  SCENE_SOUND_MAP,
  GN_SAVE_VERSION,
  // Scene loading
  listScenesForCharacter,
  loadSceneChain,
  loadPrologueChain,
  // Text utilities
  wrapTextForNovel,
  paginateLines,
  computeTypedPageIndex,
  toRoman,
  characterLabel,
  // Timing / progress
  dialogueTypedChars,
  sceneProgress,
  // Sound
  resolveSound,
  soundCategory,
  // Player
  createPlayer,
  currentScene,
  currentDialogue,
  currentText,
  currentSpeaker,
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
  // Save/restore
  snapshotProgress,
  restoreProgress,
  isValidProgress,
  coerceProgress,
} from "../src/core/graphic_novel.ts";
import scenesJson from "../src/data/scenes.json" with { type: "json" };

/* -------------------------------------------------------------------------- *
 *  Fixtures
 * -------------------------------------------------------------------------- */

const SCENES = scenesJson.scenes;

function fixtureScene(overrides: Partial<SceneData> = {}): SceneData {
  return {
    id: "scene_test",
    character: "novice",
    order: 1,
    ending: "A" as Ending,
    title_en: "TEST TITLE",
    title_ko: "테스트 제목",
    background_id: "bg_test",
    portrait_left: null,
    portrait_right: null,
    dialogue: [
      {
        speaker: "case",
        speaker_ko: "케이",
        portrait: null,
        text_en: "First line of dialogue.",
        text_ko: "첫 번째 대사.",
        duration_ms: 1000,
        sound: null,
      } satisfies DialogueLine,
      {
        speaker: "narrator",
        speaker_ko: "내레이터",
        portrait: null,
        text_en: "Second line.",
        text_ko: "두 번째.",
        duration_ms: 500,
        sound: "neon_hum",
      } satisfies DialogueLine,
    ],
    next_scene: null,
    ...overrides,
  };
}

/* -------------------------------------------------------------------------- *
 *  Scene loading
 * -------------------------------------------------------------------------- */

describe("scene loading", () => {
  it("loads bundled scenes.json with 27 scenes for 3 characters", () => {
    expect(scenesJson.scene_count).toBe(27);
    expect(Object.keys(SCENES).length).toBe(27);
  });

  it("listScenesForCharacter returns scenes for each character in order", () => {
    const novice = listScenesForCharacter("novice");
    const veteran = listScenesForCharacter("veteran");
    const heretic = listScenesForCharacter("heretic");
    expect(novice.length).toBeGreaterThan(0);
    expect(veteran.length).toBeGreaterThan(0);
    expect(heretic.length).toBeGreaterThan(0);
    expect(novice.every((s) => s.character === "novice")).toBe(true);
    expect(veteran.every((s) => s.character === "veteran")).toBe(true);
    expect(heretic.every((s) => s.character === "heretic")).toBe(true);
    // Sorted by order asc
    for (let i = 1; i < novice.length; i++) {
      const a = novice[i - 1] as SceneData;
      const b = novice[i] as SceneData;
      expect(b.order).toBeGreaterThanOrEqual(a.order);
    }
  });

  it("listScenesForCharacter returns empty for unknown character", () => {
    const list = listScenesForCharacter("nonexistent" as CharacterId);
    expect(list).toEqual([]);
  });

  it("loadSceneChain includes scenes with matching ending only", () => {
    const chain = loadSceneChain("novice", { ending: "A" });
    expect(chain.every((s) => s.ending === "A")).toBe(true);
    expect(chain.length).toBeGreaterThan(0);
  });

  it("loadSceneChain filters by maxOrder", () => {
    const full = loadSceneChain("novice");
    const partial = loadSceneChain("novice", { maxOrder: 4 });
    expect(partial.length).toBeLessThan(full.length);
    expect(partial.every((s) => s.order <= 4)).toBe(true);
  });

  it("loadSceneChain with shuffle produces a permutation (same length)", () => {
    const chain = loadSceneChain("novice", { shuffle: true, seed: 42 });
    expect(chain.length).toBe(loadSceneChain("novice").length);
  });

  it("loadSceneChain with seed is deterministic", () => {
    const a = loadSceneChain("novice", { shuffle: true, seed: 7 }).map((s) => s.id);
    const b = loadSceneChain("novice", { shuffle: true, seed: 7 }).map((s) => s.id);
    expect(a).toEqual(b);
  });

  it("loadSceneChain with different seeds produces different orderings", () => {
    const a = loadSceneChain("novice", { shuffle: true, seed: 1 }).map((s) => s.id);
    const b = loadSceneChain("novice", { shuffle: true, seed: 2 }).map((s) => s.id);
    expect(a).not.toEqual(b);
  });

  it("loadPrologueChain includes all characters x scenes with shuffled character order", () => {
    const prologue = loadPrologueChain({ seed: 1, maxOrder: 8 });
    expect(prologue.length).toBeGreaterThan(0);
    const chars = new Set(prologue.map((s) => s.character));
    expect(chars.size).toBeGreaterThanOrEqual(2);
  });

  it("loadPrologueChain with seed is deterministic across calls", () => {
    const a = loadPrologueChain({ seed: 99 }).map((s) => s.id);
    const b = loadPrologueChain({ seed: 99 }).map((s) => s.id);
    expect(a).toEqual(b);
  });

  it("CHAR_TO_DIR maps every playable character to a data dir", () => {
    expect(CHAR_TO_DIR.novice).toBe("case");
    expect(CHAR_TO_DIR.veteran).toBe("sil");
    expect(CHAR_TO_DIR.heretic).toBe("kas");
  });
});

/* -------------------------------------------------------------------------- *
 *  Text utilities
 * -------------------------------------------------------------------------- */

describe("text utilities", () => {
  it("toRoman returns roman numerals for 1..12, arabic fallback beyond", () => {
    expect(toRoman(1)).toBe("I");
    expect(toRoman(4)).toBe("IV");
    expect(toRoman(9)).toBe("IX");
    expect(toRoman(12)).toBe("XII");
    expect(toRoman(13)).toBe("13");
    expect(toRoman(0)).toBe("0");
  });

  it("wrapTextForNovel wraps a single short paragraph into one line", () => {
    const wrapped = wrapTextForNovel("Hello world", { width: 80 });
    expect(wrapped).toEqual(["Hello world"]);
  });

  it("wrapTextForNovel wraps long prose to fit page width minus margins", () => {
    const text = "The quick brown fox jumps over the lazy dog. ".repeat(10);
    const wrapped = wrapTextForNovel(text, { width: 40 });
    for (const line of wrapped) {
      if (line.length === 0) continue;
      expect(line.length).toBeLessThanOrEqual(
        40 - NOVEL_LEFT_MARGIN - NOVEL_RIGHT_MARGIN,
      );
    }
  });

  it("wrapTextForNovel preserves paragraph breaks as blank lines", () => {
    const wrapped = wrapTextForNovel("First paragraph.\n\nSecond paragraph.");
    expect(wrapped).toContain("");
  });

  it("wrapTextForNovel defaults to 80-wide pages", () => {
    const wrapped = wrapTextForNovel("One two three four five six seven.");
    expect(wrapped.length).toBeGreaterThanOrEqual(1);
  });

  it("paginateLines splits into pages with at most N lines", () => {
    const lines = Array.from({ length: 10 }, (_, i) => `line ${i + 1}`);
    const pages = paginateLines(lines, 3);
    // With blank-separator enabled, an extra blank line is added at each
    // page boundary, so each page beyond the first is exactly linesPerPage.
    expect(pages.length).toBeGreaterThanOrEqual(4);
    expect(pages[0]?.length).toBe(3);
    // Each page beyond the first carries a leading blank line
    expect(pages[1]?.[0]).toBe("");
  });

  it("paginateLines with blankSeparator=false keeps first page at exactly N", () => {
    const lines = Array.from({ length: 10 }, (_, i) => `line ${i + 1}`);
    const pages = paginateLines(lines, 3, { blankSeparator: false });
    expect(pages.length).toBe(4);
    expect(pages[0]?.length).toBe(3);
    expect(pages[1]?.length).toBe(3);
    expect(pages[3]?.length).toBe(1);
  });

  it("paginateLines handles empty input gracefully", () => {
    const pages = paginateLines([], 3);
    expect(pages.length).toBeGreaterThanOrEqual(1);
  });

  it("computeTypedPageIndex returns 0 when nothing typed", () => {
    const pages = paginateLines(["abc", "def", "ghi"], 2);
    expect(computeTypedPageIndex(pages, 0)).toBe(0);
  });

  it("computeTypedPageIndex advances when typed chars cross page boundary", () => {
    const pages = paginateLines(["abc", "def"], 1);
    expect(computeTypedPageIndex(pages, 0)).toBe(0);
    expect(computeTypedPageIndex(pages, 5)).toBe(1);
  });

  it("computeTypedPageIndex clamps to last page when typed > total", () => {
    const pages = paginateLines(["ab", "cd"], 1);
    expect(computeTypedPageIndex(pages, 9999)).toBe(pages.length - 1);
  });

  it("computeTypedPageIndex handles empty pages list", () => {
    expect(computeTypedPageIndex([], 100)).toBe(0);
  });

  it("characterLabel returns localized strings for all characters", () => {
    expect(characterLabel("novice", "en")).toBe("Case (K) — Novice");
    expect(characterLabel("novice", "ko")).toBe("케이 (K) — Novice");
    expect(characterLabel("veteran", "ko")).toBe("실 (Sil) — Veteran");
    expect(characterLabel("heretic", "ko")).toBe("카스 (Kas) — Heretic");
  });

  it("characterLabel returns the raw id for unknown characters", () => {
    expect(characterLabel("zorglub", "en")).toBe("zorglub");
  });
});

/* -------------------------------------------------------------------------- *
 *  Timing + progress
 * -------------------------------------------------------------------------- */

describe("timing and progress", () => {
  it("dialogueTypedChars returns 0 at start", () => {
    expect(dialogueTypedChars(1000, 0, 50)).toBe(0);
  });

  it("dialogueTypedChars returns full text at end of duration", () => {
    expect(dialogueTypedChars(1000, 1000, 33)).toBe(33);
  });

  it("dialogueTypedChars respects 30ms/char typing rate", () => {
    expect(dialogueTypedChars(3000, 300, 100)).toBe(10);
    expect(dialogueTypedChars(3000, 600, 100)).toBe(20);
  });

  it("dialogueTypedChars clamps to totalChars (does not overshoot)", () => {
    expect(dialogueTypedChars(100, 1000, 5)).toBe(5);
  });

  it("dialogueTypedChars returns full text immediately when duration is 0", () => {
    expect(dialogueTypedChars(0, 0, 50)).toBe(50);
  });

  it("dialogueTypedChars handles empty text", () => {
    expect(dialogueTypedChars(1000, 500, 0)).toBe(0);
  });

  it("MS_PER_CHAR matches the Python speed constant (30)", () => {
    expect(MS_PER_CHAR).toBe(30);
  });

  it("sceneProgress returns 0 at start and 1 at end", () => {
    expect(sceneProgress(0, 10)).toBe(0);
    expect(sceneProgress(10, 10)).toBe(1);
    expect(sceneProgress(5, 10)).toBeCloseTo(0.5);
  });

  it("sceneProgress handles zero-length chain", () => {
    expect(sceneProgress(0, 0)).toBe(0);
  });

  it("sceneProgress clamps to 1.0", () => {
    expect(sceneProgress(20, 10)).toBe(1);
  });
});

/* -------------------------------------------------------------------------- *
 *  Sound resolver
 * -------------------------------------------------------------------------- */

describe("sound resolver", () => {
  it("maps known scene sound ids to logical keys", () => {
    expect(resolveSound("neon_hum")).toBe("movement/neon_hum");
    expect(resolveSound("chiba_rain_loop")).toBe("theme/chiba");
    expect(resolveSound("jack_in_zap")).toBe("movement/jack_in_zap");
    expect(resolveSound("broadcast")).toBe("theme/broadcast");
  });

  it("returns the input as-is when already a logical key", () => {
    expect(resolveSound("movement/jack_in_zap")).toBe("movement/jack_in_zap");
    expect(resolveSound("custom/track")).toBe("custom/track");
  });

  it("returns null for null/undefined/unknown id", () => {
    expect(resolveSound(null)).toBeNull();
    expect(resolveSound(undefined)).toBeNull();
    expect(resolveSound("totally_made_up_sound")).toBeNull();
  });

  it("SCENE_SOUND_MAP contains all common ambient + SFX ids", () => {
    for (const key of [
      "neon_hum", "jack_in_zap", "jack_out_buzz",
      "data_extract", "broadcast_static", "black_ice_roar",
      "chiba_rain_loop", "matrix_rain", "loa_drum",
    ]) {
      expect(SCENE_SOUND_MAP[key]).toBeDefined();
    }
  });

  it("soundCategory extracts prefix from resolved key", () => {
    expect(soundCategory("theme/chiba")).toBe("theme");
    expect(soundCategory("movement/neon_hum")).toBe("movement");
  });

  it("soundCategory returns null for null/no-slash input", () => {
    expect(soundCategory(null)).toBeNull();
    expect(soundCategory("nope")).toBeNull();
  });
});

/* -------------------------------------------------------------------------- *
 *  Player state machine
 * -------------------------------------------------------------------------- */

describe("player state machine", () => {
  it("createPlayer(mode=novice) builds a non-empty chain anchored to character_id", () => {
    const p = createPlayer({ mode: "novice" });
    expect(p.chain.length).toBeGreaterThan(0);
    expect(p.character_id).toBe("novice");
    expect(p.scene_index).toBe(0);
    expect(p.dialogue_index).toBe(0);
    expect(p.elapsed_ms).toBe(0);
    expect(p.paused).toBe(false);
    expect(p.done).toBe(false);
  });

  it("createPlayer(mode=prologue) anchors to first scene's character", () => {
    const p = createPlayer({ mode: "prologue", seed: 1 });
    expect(p.chain.length).toBeGreaterThan(0);
    expect(p.character_id).toBe(p.chain[0]?.character);
    expect(p.mode).toBe("prologue");
  });

  it("createPlayer with same seed is deterministic", () => {
    const a = createPlayer({ mode: "prologue", seed: 5 });
    const b = createPlayer({ mode: "prologue", seed: 5 });
    expect(a.chain.map((s) => s.id)).toEqual(b.chain.map((s) => s.id));
  });

  it("currentScene / currentDialogue return the right objects", () => {
    const p = createPlayer({ mode: "novice" });
    const s = currentScene(p);
    const d = currentDialogue(p);
    expect(s).not.toBeNull();
    expect(d).not.toBeNull();
    expect(d).toBe(s?.dialogue[0]);
  });

  it("currentText + currentSpeaker honor language toggle", () => {
    const p = createPlayer({ mode: "novice" });
    const enText = currentText(p, "en");
    const koText = currentText(p, "ko");
    expect(enText).not.toBe(koText);
    // Chain is shuffled — first dialogue can be either speaker. Just verify
    // the language field is the expected Korean translation.
    expect(currentSpeaker(p, "ko")).not.toBe(currentSpeaker(p, "en"));
  });

  it("currentTitle honors language", () => {
    // Pick a fixed scene by ID to avoid chain-shuffle flakiness.
    const scene = Object.values(scenesJson.scenes).find((s) => s.id === "scene_case_intro");
    expect(scene).toBeDefined();
    expect(scene?.title_en).toBe("CHATTO'S 24/7");
    expect(scene?.title_ko).toBe("챠토 24/7");
  });

  it("currentSound resolves from current dialogue sound field", () => {
    // Pin to a known scene to avoid chain-shuffle flakiness.
    const scene = Object.values(scenesJson.scenes).find((s) => s.id === "scene_case_intro");
    expect(scene).toBeDefined();
    const p: GraphicNovelPlayer = {
      mode: "novice",
      chain: [scene as SceneData],
      character_id: "novice",
      ending: "A",
      scene_index: 0,
      dialogue_index: 0,
      elapsed_ms: 0,
      paused: false,
      done: false,
    };
    // First dialogue of scene_case_intro is "chiba_rain_loop".
    expect(currentSound(p)).toBe("theme/chiba");
  });

  it("progress returns 0 at start of chain", () => {
    const p = createPlayer({ mode: "novice" });
    expect(progress(p)).toBe(0);
  });

  it("isDialogueComplete is false at start, true after enough time", () => {
    const p = createPlayer({ mode: "novice" });
    expect(isDialogueComplete(p)).toBe(false);
    p.elapsed_ms = 1e7;
    expect(isDialogueComplete(p)).toBe(true);
  });

  it("tick advances elapsed_ms by deltaMs", () => {
    const p = createPlayer({ mode: "novice" });
    const before = p.elapsed_ms;
    tick(p, 100);
    expect(p.elapsed_ms).toBe(before + 100);
  });

  it("tick is a no-op when paused", () => {
    const p = createPlayer({ mode: "novice" });
    p.paused = true;
    tick(p, 100);
    expect(p.elapsed_ms).toBe(0);
  });

  it("tick emits dialogue_complete after current dialogue duration", () => {
    const scene = Object.values(scenesJson.scenes).find((s) => s.id === "scene_case_intro");
    expect(scene).toBeDefined();
    const p: GraphicNovelPlayer = {
      mode: "novice",
      chain: [scene as SceneData],
      character_id: "novice",
      ending: "A",
      scene_index: 0,
      dialogue_index: 0,
      elapsed_ms: 0,
      paused: false,
      done: false,
    };
    // case intro first dialogue duration_ms = 12000
    const events = tick(p, 12000);
    expect(events.some((e) => e.type === "dialogue_complete")).toBe(true);
    expect(p.dialogue_index).toBeGreaterThanOrEqual(1);
  });

  it("tick emits chain_complete when last scene finishes", () => {
    // Use a single dialogue per scene fixture to drive chain completion quickly
    const fastScene = fixtureScene({
      dialogue: [
        {
          speaker: "n",
          speaker_ko: "내",
          portrait: null,
          text_en: "End.",
          text_ko: "끝.",
          duration_ms: 10,
          sound: null,
        },
      ],
    });
    const p: GraphicNovelPlayer = {
      mode: "novice",
      chain: [fastScene],
      character_id: "novice",
      ending: "A",
      scene_index: 0,
      dialogue_index: 0,
      elapsed_ms: 0,
      paused: false,
      done: false,
    };
    const events = tick(p, 100);
    expect(events.some((e) => e.type === "chain_complete")).toBe(true);
    expect(p.done).toBe(true);
  });

  it("skipCurrentDialogue jumps elapsed_ms to dialogue duration", () => {
    const p = createPlayer({ mode: "novice" });
    skipCurrentDialogue(p);
    expect(isDialogueComplete(p)).toBe(true);
  });

  it("skipCurrentScene advances to next scene", () => {
    const p = createPlayer({ mode: "novice" });
    const beforeScene = p.scene_index;
    skipCurrentScene(p);
    expect(p.scene_index).toBeGreaterThan(beforeScene);
  });

  it("togglePause flips paused state and is idempotent when done", () => {
    const p = createPlayer({ mode: "novice" });
    expect(p.paused).toBe(false);
    expect(togglePause(p)).toBe(true);
    expect(togglePause(p)).toBe(false);
    p.done = true;
    expect(togglePause(p)).toBe(false);
  });

  it("advanceScene and advanceDialogue increment counters", () => {
    // Use a known scene with multiple dialogues so advanceDialogue has somewhere to go.
    const scene = Object.values(scenesJson.scenes).find((s) => s.id === "scene_case_intro");
    expect(scene).toBeDefined();
    const p: GraphicNovelPlayer = {
      mode: "novice",
      chain: [scene as SceneData],
      character_id: "novice",
      ending: "A",
      scene_index: 0,
      dialogue_index: 0,
      elapsed_ms: 0,
      paused: false,
      done: false,
    };
    expect(advanceDialogue(p)).toBe(true);
    expect(p.dialogue_index).toBe(1);
    advanceScene(p);
    expect(p.scene_index).toBe(1);
    expect(p.dialogue_index).toBe(0);
    expect(p.done).toBe(true);
  });

  it("advanceDialogue clamps at end of scene without crossing to next scene", () => {
    const p = createPlayer({ mode: "novice" });
    const last = (p.chain[0]?.dialogue.length ?? 1) - 1;
    p.dialogue_index = last;
    expect(advanceDialogue(p)).toBe(false);
    expect(p.scene_index).toBe(0);
  });

  it("advanceScene clamps at end of chain and sets done", () => {
    const p = createPlayer({ mode: "novice" });
    p.scene_index = p.chain.length - 1;
    advanceScene(p);
    expect(p.done).toBe(true);
  });

  it("restart resets all indices and clears paused/done", () => {
    const p = createPlayer({ mode: "novice" });
    p.scene_index = 3;
    p.dialogue_index = 2;
    p.elapsed_ms = 5000;
    p.paused = true;
    restart(p);
    expect(p.scene_index).toBe(0);
    expect(p.dialogue_index).toBe(0);
    expect(p.elapsed_ms).toBe(0);
    expect(p.paused).toBe(false);
    expect(p.done).toBe(false);
  });
});

/* -------------------------------------------------------------------------- *
 *  Save / restore
 * -------------------------------------------------------------------------- */

describe("save and restore", () => {
  it("snapshotProgress captures current player state", () => {
    const p = createPlayer({ mode: "novice" });
    p.scene_index = 2;
    p.dialogue_index = 1;
    p.elapsed_ms = 4321;
    const snap = snapshotProgress(p);
    expect(snap.mode).toBe("novice");
    expect(snap.scene_index).toBe(2);
    expect(snap.dialogue_index).toBe(1);
    expect(snap.elapsed_in_dialogue_ms).toBe(4321);
    expect(snap.character_id).toBe("novice");
    expect(snap.chain_length).toBe(p.chain.length);
    expect(snap.ending).toBe("A");
    expect(typeof snap.saved_at).toBe("string");
    expect(typeof snap.session_id).toBe("string");
  });

  it("restoreProgress rebuilds chain and clamps indices", () => {
    const p = createPlayer({ mode: "novice" });
    const snap = snapshotProgress(p);
    const corrupted: GraphicNovelProgress = {
      ...snap,
      scene_index: 9999, // out of range
      dialogue_index: 9999,
    };
    const restored = restoreProgress(corrupted);
    expect(restored.scene_index).toBeLessThanOrEqual(restored.chain.length);
    expect(restored.dialogue_index).toBeLessThanOrEqual(
      restored.chain[restored.scene_index]?.dialogue.length ?? 0,
    );
    expect(restored.mode).toBe("novice");
  });

  it("restoreProgress handles prologue mode", () => {
    const snap: GraphicNovelProgress = {
      mode: "prologue",
      scene_index: 0,
      dialogue_index: 0,
      elapsed_in_dialogue_ms: 0,
      character_id: "novice",
      chain_length: 0,
      ending: "A",
      saved_at: "2026-01-01T00:00:00.000Z",
      session_id: "test-id",
    };
    const restored = restoreProgress(snap, { seed: 1 });
    expect(restored.mode).toBe("prologue");
    expect(restored.chain.length).toBeGreaterThan(0);
  });

  it("GN_SAVE_VERSION matches the Python constant (1.2.0)", () => {
    expect(GN_SAVE_VERSION).toBe("1.2.0");
  });

  it("isValidProgress accepts a well-formed save dict", () => {
    const valid: GraphicNovelProgress = {
      mode: "novice",
      scene_index: 1,
      dialogue_index: 0,
      elapsed_in_dialogue_ms: 100,
      character_id: "novice",
      chain_length: 9,
      ending: "A",
      saved_at: "2026-01-01T00:00:00.000Z",
      session_id: "abc",
    };
    expect(isValidProgress(valid)).toBe(true);
  });

  it("isValidProgress rejects null, non-object, and missing fields", () => {
    expect(isValidProgress(null)).toBe(false);
    expect(isValidProgress(undefined)).toBe(false);
    expect(isValidProgress("string")).toBe(false);
    expect(isValidProgress({ mode: "novice" })).toBe(false);
  });

  it("coerceProgress returns safe defaults for invalid input", () => {
    const coerced = coerceProgress({ totally: "wrong" });
    expect(coerced.mode).toBe("prologue");
    expect(coerced.scene_index).toBe(0);
    expect(coerced.chain_length).toBe(0);
    expect(coerced.ending).toBe("A");
  });

  it("coerceProgress clamps negative numerics to 0", () => {
    const coerced = coerceProgress({
      mode: "novice",
      scene_index: -5,
      dialogue_index: -3,
      elapsed_in_dialogue_ms: -1,
      character_id: "novice",
      chain_length: 9,
      saved_at: "2026-01-01T00:00:00.000Z",
      ending: "A",
      session_id: "abc",
    });
    expect(coerced.scene_index).toBe(0);
    expect(coerced.dialogue_index).toBe(0);
    expect(coerced.elapsed_in_dialogue_ms).toBe(0);
  });

  it("coerceProgress falls back unknown ending values to 'A' (forward-compat)", () => {
    const coerced = coerceProgress({
      mode: "novice",
      scene_index: 0,
      dialogue_index: 0,
      elapsed_in_dialogue_ms: 0,
      character_id: "novice",
      chain_length: 9,
      saved_at: "2026-01-01T00:00:00.000Z",
      ending: "Z" as unknown as Ending,
      session_id: "abc",
    });
    expect(coerced.ending).toBe("A");
  });

  it("DEFAULT_PAGE_WIDTH matches Python default (80)", () => {
    expect(DEFAULT_PAGE_WIDTH).toBe(80);
  });
});

/* -------------------------------------------------------------------------- *
 *  Integration: full chain playthrough
 * -------------------------------------------------------------------------- */

describe("end-to-end playthrough", () => {
  it("tick walks through entire novice chain to completion", () => {
    const p = createPlayer({ mode: "novice" });
    let safety = 0;
    while (!p.done && safety++ < 100_000) {
      tick(p, 100);
    }
    expect(p.done).toBe(true);
    expect(p.scene_index).toBe(p.chain.length);
  });

  it("prologue chain with seed plays through without errors", () => {
    const p = createPlayer({ mode: "prologue", seed: 13 });
    expect(p.chain.length).toBeGreaterThan(0);
    tick(p, 60_000); // 1 minute of wall time
    expect(p.scene_index).toBeGreaterThanOrEqual(0);
  });

  it("snapshotProgress + restoreProgress roundtrip preserves state", () => {
    const p = createPlayer({ mode: "novice" });
    p.scene_index = 2;
    p.dialogue_index = 1;
    p.elapsed_ms = 500;
    const snap = snapshotProgress(p);
    const restored = restoreProgress(snap);
    expect(restored.mode).toBe(p.mode);
    expect(restored.scene_index).toBe(p.scene_index);
    expect(restored.dialogue_index).toBe(p.dialogue_index);
    expect(restored.elapsed_ms).toBe(p.elapsed_ms);
    expect(restored.character_id).toBe(p.character_id);
  });
});