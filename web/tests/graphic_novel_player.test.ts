import { describe, it, expect } from "vitest";
import {
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
} from "../src/core/graphic_novel_player.ts";

describe("createPlayer", () => {
  it("creates player with prologue mode", () => {
    const player = createPlayer({ mode: "prologue", seed: 42 });
    expect(player.mode).toBe("prologue");
    expect(player.scene_index).toBe(0);
    expect(player.dialogue_index).toBe(0);
    expect(player.elapsed_ms).toBe(0);
    expect(player.paused).toBe(false);
    expect(player.done).toBe(false);
    expect(player.ending).toBe("A");
  });

  it("creates player with specific character mode", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    expect(player.mode).toBe("novice");
    expect(player.character_id).toBe("novice");
  });

  it("accepts custom ending parameter", () => {
    const player = createPlayer({ mode: "veteran", ending: "B" });
    expect(player.ending).toBe("B");
  });

  it("accepts maxOrder parameter", () => {
    const player = createPlayer({ mode: "heretic", maxOrder: 4 });
    expect(player.chain.length).toBeGreaterThan(0);
  });

  it("marks done true when chain is empty", () => {
    const player = createPlayer({ mode: "novice", maxOrder: 0 });
    expect(player.done).toBe(true);
  });
});

describe("currentScene", () => {
  it("returns first scene at index 0", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const scene = currentScene(player);
    expect(scene).not.toBeNull();
    if (scene) {
      expect(scene.character).toBe("novice");
    }
  });

  it("returns null when scene_index exceeds chain length", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    player.scene_index = 9999;
    expect(currentScene(player)).toBeNull();
  });

  it("returns null when chain is empty", () => {
    const player = createPlayer({ mode: "novice", maxOrder: 0 });
    expect(currentScene(player)).toBeNull();
  });
});

describe("currentDialogue", () => {
  it("returns first dialogue of first scene", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const dialogue = currentDialogue(player);
    expect(dialogue).not.toBeNull();
    if (dialogue) {
      expect(dialogue.speaker).toBeDefined();
      expect(dialogue.text_en).toBeDefined();
    }
  });

  it("returns null when dialogue_index exceeds dialogue array", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    player.dialogue_index = 9999;
    expect(currentDialogue(player)).toBeNull();
  });

  it("returns null when scene is null", () => {
    const player = createPlayer({ mode: "novice", maxOrder: 0 });
    expect(currentDialogue(player)).toBeNull();
  });
});

describe("currentText", () => {
  it("returns english text when lang is en", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const text = currentText(player, "en");
    expect(typeof text).toBe("string");
    expect(text.length).toBeGreaterThan(0);
  });

  it("returns korean text when lang is ko", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const text = currentText(player, "ko");
    expect(typeof text).toBe("string");
  });

  it("returns empty string when dialogue is null", () => {
    const player = createPlayer({ mode: "novice", maxOrder: 0 });
    expect(currentText(player, "en")).toBe("");
  });
});

describe("currentSpeaker", () => {
  it("returns english speaker name when lang is en", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const speaker = currentSpeaker(player, "en");
    expect(typeof speaker).toBe("string");
  });

  it("returns korean speaker name when lang is ko", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const speaker = currentSpeaker(player, "ko");
    expect(typeof speaker).toBe("string");
  });

  it("returns empty string when dialogue is null", () => {
    const player = createPlayer({ mode: "novice", maxOrder: 0 });
    expect(currentSpeaker(player, "en")).toBe("");
  });
});

describe("currentTitle", () => {
  it("returns english title when lang is en", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const title = currentTitle(player, "en");
    expect(typeof title).toBe("string");
  });

  it("returns korean title when lang is ko", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const title = currentTitle(player, "ko");
    expect(typeof title).toBe("string");
  });

  it("returns empty string when scene is null", () => {
    const player = createPlayer({ mode: "novice", maxOrder: 0 });
    expect(currentTitle(player, "en")).toBe("");
  });
});

describe("currentSound", () => {
  it("returns sound key or null", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const sound = currentSound(player);
    expect(sound === null || typeof sound === "string").toBe(true);
  });

  it("returns null when dialogue is null", () => {
    const player = createPlayer({ mode: "novice", maxOrder: 0 });
    expect(currentSound(player)).toBeNull();
  });
});

describe("progress", () => {
  it("returns 0.0 when at scene 0 with multiple scenes", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const p = progress(player);
    expect(p).toBeGreaterThanOrEqual(0.0);
    expect(p).toBeLessThanOrEqual(1.0);
  });

  it("returns 0.0 when chain is empty", () => {
    const player = createPlayer({ mode: "novice", maxOrder: 0 });
    expect(progress(player)).toBe(0.0);
  });

  it("increases as scene_index increases", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const p1 = progress(player);
    player.scene_index = 1;
    const p2 = progress(player);
    if (player.chain.length > 1) {
      expect(p2).toBeGreaterThan(p1);
    }
  });

  it("caps at 1.0", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    player.scene_index = player.chain.length;
    expect(progress(player)).toBe(1.0);
  });
});

describe("isDialogueComplete", () => {
  it("returns false when elapsed_ms is zero", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    player.elapsed_ms = 0;
    expect(isDialogueComplete(player)).toBe(false);
  });

  it("returns true when elapsed_ms exceeds duration", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const dialogue = currentDialogue(player);
    if (dialogue) {
      player.elapsed_ms = dialogue.duration_ms;
      expect(isDialogueComplete(player)).toBe(true);
    }
  });

  it("returns true when dialogue is null", () => {
    const player = createPlayer({ mode: "novice", maxOrder: 0 });
    expect(isDialogueComplete(player)).toBe(true);
  });
});

describe("tick", () => {
  it("returns empty events when paused", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    player.paused = true;
    const events = tick(player, 1000);
    expect(events.length).toBe(0);
  });

  it("returns empty events when done", () => {
    const player = createPlayer({ mode: "novice", maxOrder: 0 });
    expect(player.done).toBe(true);
    const events = tick(player, 1000);
    expect(events.length).toBe(0);
  });

  it("accumulates elapsed_ms", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const before = player.elapsed_ms;
    tick(player, 100);
    expect(player.elapsed_ms).toBeGreaterThanOrEqual(before);
  });

  it("emits dialogue_complete event when dialogue finishes", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const dialogue = currentDialogue(player);
    if (dialogue) {
      const events = tick(player, dialogue.duration_ms + 100);
      expect(events.some((e) => e.type === "dialogue_complete")).toBe(true);
    }
  });

  it("advances dialogue_index after dialogue_complete", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const initial = player.dialogue_index;
    const dialogue = currentDialogue(player);
    if (dialogue) {
      tick(player, dialogue.duration_ms + 100);
      expect(player.dialogue_index).toBeGreaterThan(initial);
    }
  });

  it("emits scene_complete when last dialogue finishes", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const scene = currentScene(player);
    if (scene && scene.dialogue.length > 0) {
      const totalDuration = scene.dialogue.reduce((sum, d) => sum + d.duration_ms, 0);
      const events = tick(player, totalDuration + 1000);
      expect(events.some((e) => e.type === "scene_complete")).toBe(true);
    }
  });

  it("emits chain_complete when last scene finishes", () => {
    const player = createPlayer({ mode: "novice", seed: 42, maxOrder: 1 });
    const scene = currentScene(player);
    if (scene) {
      const totalDuration = scene.dialogue.reduce((sum, d) => sum + d.duration_ms, 0);
      const events = tick(player, totalDuration + 1000);
      expect(events.some((e) => e.type === "chain_complete")).toBe(true);
    }
  });

  it("sets done to true after chain_complete", () => {
    const player = createPlayer({ mode: "novice", seed: 42, maxOrder: 1 });
    const scene = currentScene(player);
    if (scene) {
      const totalDuration = scene.dialogue.reduce((sum, d) => sum + d.duration_ms, 0);
      tick(player, totalDuration + 1000);
      expect(player.done).toBe(true);
    }
  });
});

describe("skipCurrentDialogue", () => {
  it("returns true and advances elapsed_ms to duration", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const dialogue = currentDialogue(player);
    if (dialogue) {
      const result = skipCurrentDialogue(player);
      expect(result).toBe(true);
      expect(player.elapsed_ms).toBe(dialogue.duration_ms);
    }
  });

  it("returns false when dialogue is null", () => {
    const player = createPlayer({ mode: "novice", maxOrder: 0 });
    expect(skipCurrentDialogue(player)).toBe(false);
  });
});

describe("skipCurrentScene", () => {
  it("advances to next scene", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const sceneBefore = currentScene(player);
    if (sceneBefore && player.chain.length > 1) {
      skipCurrentScene(player);
      const sceneAfter = currentScene(player);
      expect(sceneAfter?.id).not.toBe(sceneBefore.id);
    }
  });

  it("returns true when scene exists", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    expect(skipCurrentScene(player)).toBe(true);
  });

  it("returns false when scene is null", () => {
    const player = createPlayer({ mode: "novice", maxOrder: 0 });
    expect(skipCurrentScene(player)).toBe(false);
  });
});

describe("togglePause", () => {
  it("toggles paused state from false to true", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    expect(player.paused).toBe(false);
    togglePause(player);
    expect(player.paused).toBe(true);
  });

  it("toggles paused state from true to false", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    player.paused = true;
    togglePause(player);
    expect(player.paused).toBe(false);
  });

  it("returns current paused state", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const result = togglePause(player);
    expect(result).toBe(player.paused);
  });

  it("does not toggle when done", () => {
    const player = createPlayer({ mode: "novice", maxOrder: 0 });
    expect(player.done).toBe(true);
    const before = player.paused;
    togglePause(player);
    expect(player.paused).toBe(before);
  });
});

describe("advanceScene", () => {
  it("increments scene_index", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const before = player.scene_index;
    advanceScene(player);
    expect(player.scene_index).toBe(before + 1);
  });

  it("resets dialogue_index to 0", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    player.dialogue_index = 5;
    advanceScene(player);
    expect(player.dialogue_index).toBe(0);
  });

  it("resets elapsed_ms to 0", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    player.elapsed_ms = 1000;
    advanceScene(player);
    expect(player.elapsed_ms).toBe(0);
  });

  it("returns false when scene is null", () => {
    const player = createPlayer({ mode: "novice", maxOrder: 0 });
    expect(advanceScene(player)).toBe(false);
  });

  it("returns true when scene exists", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    expect(advanceScene(player)).toBe(true);
  });
});

describe("advanceDialogue", () => {
  it("increments dialogue_index", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const before = player.dialogue_index;
    const result = advanceDialogue(player);
    if (result) {
      expect(player.dialogue_index).toBe(before + 1);
    }
  });

  it("resets elapsed_ms to 0", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    player.elapsed_ms = 1000;
    const result = advanceDialogue(player);
    if (result) {
      expect(player.elapsed_ms).toBe(0);
    }
  });

  it("returns false when at last dialogue", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const scene = currentScene(player);
    if (scene) {
      player.dialogue_index = scene.dialogue.length - 1;
      expect(advanceDialogue(player)).toBe(false);
    }
  });

  it("returns false when scene is null", () => {
    const player = createPlayer({ mode: "novice", maxOrder: 0 });
    expect(advanceDialogue(player)).toBe(false);
  });
});

describe("restart", () => {
  it("resets scene_index to 0", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    player.scene_index = 5;
    restart(player);
    expect(player.scene_index).toBe(0);
  });

  it("resets dialogue_index to 0", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    player.dialogue_index = 10;
    restart(player);
    expect(player.dialogue_index).toBe(0);
  });

  it("resets elapsed_ms to 0", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    player.elapsed_ms = 5000;
    restart(player);
    expect(player.elapsed_ms).toBe(0);
  });

  it("unpauses player", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    player.paused = true;
    restart(player);
    expect(player.paused).toBe(false);
  });

  it("sets done to false when chain is not empty", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    player.done = true;
    restart(player);
    if (player.chain.length > 0) {
      expect(player.done).toBe(false);
    }
  });

  it("keeps done as true when chain is empty", () => {
    const player = createPlayer({ mode: "novice", maxOrder: 0 });
    restart(player);
    expect(player.done).toBe(true);
  });
});

describe("snapshotProgress", () => {
  it("captures current player state", () => {
    const player = createPlayer({ mode: "veteran", seed: 42 });
    player.scene_index = 2;
    player.dialogue_index = 3;
    player.elapsed_ms = 500;
    const snapshot = snapshotProgress(player);
    expect(snapshot.mode).toBe("veteran");
    expect(snapshot.scene_index).toBe(2);
    expect(snapshot.dialogue_index).toBe(3);
    expect(snapshot.elapsed_in_dialogue_ms).toBe(500);
  });

  it("includes character_id", () => {
    const player = createPlayer({ mode: "heretic", seed: 42 });
    const snapshot = snapshotProgress(player);
    expect(snapshot.character_id).toBe("heretic");
  });

  it("includes chain_length", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const snapshot = snapshotProgress(player);
    expect(snapshot.chain_length).toBe(player.chain.length);
  });

  it("includes saved_at timestamp", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const snapshot = snapshotProgress(player);
    expect(typeof snapshot.saved_at).toBe("string");
    expect(new Date(snapshot.saved_at).getTime()).toBeGreaterThan(0);
  });

  it("includes session_id", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const snapshot = snapshotProgress(player);
    expect(typeof snapshot.session_id).toBe("string");
    expect(snapshot.session_id.length).toBeGreaterThan(0);
  });

  it("includes ending", () => {
    const player = createPlayer({ mode: "novice", ending: "B" });
    const snapshot = snapshotProgress(player);
    expect(snapshot.ending).toBe("B");
  });
});

describe("restoreProgress", () => {
  it("restores saved state", () => {
    const player = createPlayer({ mode: "veteran", seed: 42 });
    player.scene_index = 1;
    player.dialogue_index = 2;
    player.elapsed_ms = 300;
    const progress = snapshotProgress(player);
    const restored = restoreProgress(progress, { seed: 42 });
    expect(restored.scene_index).toBe(1);
    expect(restored.dialogue_index).toBe(2);
    expect(restored.elapsed_ms).toBe(300);
  });

  it("clamps scene_index to chain length", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const progress = snapshotProgress(player);
    const modified = { ...progress, scene_index: 9999 };
    const restored = restoreProgress(modified, { seed: 42 });
    expect(restored.scene_index).toBeLessThanOrEqual(restored.chain.length);
  });

  it("clamps dialogue_index to scene dialogue length", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const progress = snapshotProgress(player);
    const modified = { ...progress, dialogue_index: 9999 };
    const restored = restoreProgress(modified, { seed: 42 });
    const scene = currentScene(restored);
    if (scene) {
      expect(restored.dialogue_index).toBeLessThanOrEqual(scene.dialogue.length);
    }
  });

  it("clamps negative elapsed_ms to 0", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const progress = snapshotProgress(player);
    const modified = { ...progress, elapsed_in_dialogue_ms: -100 };
    const restored = restoreProgress(modified, { seed: 42 });
    expect(restored.elapsed_ms).toBeGreaterThanOrEqual(0);
  });

  it("starts unpaused", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const progress = snapshotProgress(player);
    const restored = restoreProgress(progress);
    expect(restored.paused).toBe(false);
  });
});

describe("isValidProgress", () => {
  it("returns true for valid progress object", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const progress = snapshotProgress(player);
    expect(isValidProgress(progress)).toBe(true);
  });

  it("returns false for null", () => {
    expect(isValidProgress(null)).toBe(false);
  });

  it("returns false for non-object", () => {
    expect(isValidProgress("string")).toBe(false);
    expect(isValidProgress(123)).toBe(false);
  });

  it("returns false when mode is missing", () => {
    const obj = { scene_index: 0, dialogue_index: 0 };
    expect(isValidProgress(obj)).toBe(false);
  });

  it("returns false when ending is invalid", () => {
    const obj = {
      mode: "novice",
      scene_index: 0,
      dialogue_index: 0,
      elapsed_in_dialogue_ms: 0,
      character_id: "novice",
      chain_length: 4,
      saved_at: new Date().toISOString(),
      ending: "Z",
      session_id: "test",
    };
    expect(isValidProgress(obj)).toBe(false);
  });

  it("returns true for ending A, B, or C", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const progressA = { ...snapshotProgress(player), ending: "A" as const };
    expect(isValidProgress(progressA)).toBe(true);
    const progressB = { ...snapshotProgress(player), ending: "B" as const };
    expect(isValidProgress(progressB)).toBe(true);
    const progressC = { ...snapshotProgress(player), ending: "C" as const };
    expect(isValidProgress(progressC)).toBe(true);
  });
});

describe("coerceProgress", () => {
  it("returns fallback for invalid input", () => {
    const result = coerceProgress(null);
    expect(result.mode).toBe("prologue");
    expect(result.scene_index).toBe(0);
  });

  it("coerces valid progress object", () => {
    const player = createPlayer({ mode: "veteran", seed: 42 });
    const progress = snapshotProgress(player);
    const coerced = coerceProgress(progress);
    expect(coerced.mode).toBe("veteran");
  });

  it("defaults invalid mode to prologue", () => {
    const obj = {
      mode: "invalid_mode",
      scene_index: 0,
      dialogue_index: 0,
      elapsed_in_dialogue_ms: 0,
      character_id: "novice",
      chain_length: 4,
      saved_at: new Date().toISOString(),
      ending: "A",
      session_id: "test",
    };
    const coerced = coerceProgress(obj);
    expect(coerced.mode).toBe("prologue");
  });

  it("clamps negative scene_index to 0", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const progress = snapshotProgress(player);
    const modified = { ...progress, scene_index: -5 };
    const coerced = coerceProgress(modified);
    expect(coerced.scene_index).toBe(0);
  });

  it("clamps negative dialogue_index to 0", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const progress = snapshotProgress(player);
    const modified = { ...progress, dialogue_index: -3 };
    const coerced = coerceProgress(modified);
    expect(coerced.dialogue_index).toBe(0);
  });

  it("floors fractional indices", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const progress = snapshotProgress(player);
    const modified = { ...progress, scene_index: 1.7, dialogue_index: 2.9 };
    const coerced = coerceProgress(modified);
    expect(coerced.scene_index).toBe(1);
    expect(coerced.dialogue_index).toBe(2);
  });

  it("generates session_id when missing", () => {
    const player = createPlayer({ mode: "novice", seed: 42 });
    const progress = snapshotProgress(player);
    const { session_id, ...withoutSessionId } = progress;
    const coerced = coerceProgress(withoutSessionId);
    expect(typeof coerced.session_id).toBe("string");
    expect(coerced.session_id.length).toBeGreaterThan(0);
  });
});
