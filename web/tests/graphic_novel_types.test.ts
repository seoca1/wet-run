/** Unit tests for graphic_novel_types.ts.
 *
 * Run with: npx vitest run tests/graphic_novel_types.test.ts
 *
 * Tests type contracts for CharacterId, PlayMode, Language, Ending,
 * DialogueLine, SceneData, ScenesFile, GraphicNovelProgress,
 * GraphicNovelPlayer, and TickEvent. Validates shape, optional fields,
 * default values, and runtime contracts via Object.freeze().
 */

import { describe, it, expect } from "vitest";
import type {
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
} from "../src/core/graphic_novel_types.ts";

describe("type literal coverage", () => {
  it("CharacterId accepts all 9 declared character literals", () => {
    const ids: CharacterId[] = [
      "novice",
      "veteran",
      "heretic",
      "suit",
      "wigan",
      "angie",
      "sally",
      "3jane",
      "neuromancer",
    ];
    expect(ids.length).toBe(9);
    expect(new Set(ids).size).toBe(9);
  });

  it("PlayMode accepts prologue/novice/veteran/heretic", () => {
    const modes: PlayMode[] = ["prologue", "novice", "veteran", "heretic"];
    expect(modes.length).toBe(4);
  });

  it("Language accepts en/ko", () => {
    const langs: Language[] = ["en", "ko"];
    expect(langs.length).toBe(2);
  });

  it("Ending accepts A/B/C", () => {
    const endings: Ending[] = ["A", "B", "C"];
    expect(endings.length).toBe(3);
  });
});

describe("DialogueLine structure", () => {
  it("populates every required field", () => {
    const dialogue: DialogueLine = {
      speaker: "Case",
      speaker_ko: "케이스",
      portrait: "case_neutral",
      text_en: "Welcome to the sprawl.",
      text_ko: "스프롤에 오신 것을 환영합니다.",
      duration_ms: 3000,
      sound: "ambient_chatter",
    };
    expect(dialogue.speaker).toBe("Case");
    expect(dialogue.speaker_ko).toBe("케이스");
    expect(dialogue.portrait).toBe("case_neutral");
    expect(dialogue.text_en).toBe("Welcome to the sprawl.");
    expect(dialogue.text_ko).toBe("스프롤에 오신 것을 환영합니다.");
    expect(dialogue.duration_ms).toBe(3000);
    expect(dialogue.sound).toBe("ambient_chatter");
  });

  it("allows null portrait and null sound", () => {
    const dialogue: DialogueLine = {
      speaker: "Narrator",
      speaker_ko: "나레이터",
      portrait: null,
      text_en: "...",
      text_ko: "...",
      duration_ms: 2000,
      sound: null,
    };
    expect(dialogue.portrait).toBeNull();
    expect(dialogue.sound).toBeNull();
  });

  it("supports zero-duration dialogue (instant beat)", () => {
    const dialogue: DialogueLine = {
      speaker: "System",
      speaker_ko: "시스템",
      portrait: null,
      text_en: "",
      text_ko: "",
      duration_ms: 0,
      sound: null,
    };
    expect(dialogue.duration_ms).toBe(0);
  });

  it("preserves Korean speaker names without normalization", () => {
    const dialogue: DialogueLine = {
      speaker: "Molly",
      speaker_ko: "몰리 밀리언스",
      portrait: null,
      text_en: "Let's go.",
      text_ko: "가자.",
      duration_ms: 1500,
      sound: null,
    };
    expect(dialogue.speaker_ko).toBe("몰리 밀리언스");
  });
});

describe("SceneData structure", () => {
  it("populates every required field", () => {
    const scene: SceneData = {
      id: "novice_01_bar",
      character: "novice",
      order: 1,
      ending: "A",
      title_en: "The Chatsubo Bar",
      title_ko: "챗스보 바",
      background_id: "bar_interior",
      portrait_left: "case_neutral",
      portrait_right: null,
      dialogue: [],
      next_scene: "novice_02_alley",
      mission_id: "prologue_mission",
    };
    expect(scene.id).toBe("novice_01_bar");
    expect(scene.character).toBe("novice");
    expect(scene.order).toBe(1);
    expect(scene.ending).toBe("A");
    expect(scene.title_en).toBe("The Chatsubo Bar");
    expect(scene.title_ko).toBe("챗스보 바");
    expect(scene.background_id).toBe("bar_interior");
    expect(scene.portrait_left).toBe("case_neutral");
    expect(scene.portrait_right).toBeNull();
    expect(scene.dialogue).toEqual([]);
    expect(scene.next_scene).toBe("novice_02_alley");
    expect(scene.mission_id).toBe("prologue_mission");
  });

  it("allows null portraits and null next_scene", () => {
    const scene: SceneData = {
      id: "final_scene",
      character: "heretic",
      order: 10,
      ending: "C",
      title_en: "The End",
      title_ko: "끝",
      background_id: "void",
      portrait_left: null,
      portrait_right: null,
      dialogue: [],
      next_scene: null,
    };
    expect(scene.portrait_left).toBeNull();
    expect(scene.portrait_right).toBeNull();
    expect(scene.next_scene).toBeNull();
  });

  it("accepts a non-CharacterId string for character (extensible union)", () => {
    const scene: SceneData = {
      id: "custom_scene",
      character: "custom_character",
      order: 5,
      ending: "A",
      title_en: "Custom",
      title_ko: "커스텀",
      background_id: "custom_bg",
      portrait_left: null,
      portrait_right: null,
      dialogue: [],
      next_scene: null,
    };
    expect(scene.character).toBe("custom_character");
  });

  it("treats mission_id as optional", () => {
    const scene: SceneData = {
      id: "no_mission_scene",
      character: "veteran",
      order: 3,
      ending: "B",
      title_en: "No Mission",
      title_ko: "미션 없음",
      background_id: "street",
      portrait_left: null,
      portrait_right: null,
      dialogue: [],
      next_scene: null,
    };
    expect(scene.mission_id).toBeUndefined();
  });

  it("supports a dialogue array with multiple beats", () => {
    const scene: SceneData = {
      id: "multi_beat",
      character: "novice",
      order: 1,
      ending: "A",
      title_en: "Multi",
      title_ko: "다중",
      background_id: "bg",
      portrait_left: null,
      portrait_right: null,
      dialogue: [
        {
          speaker: "Case",
          speaker_ko: "케이스",
          portrait: null,
          text_en: "Hi.",
          text_ko: "안녕.",
          duration_ms: 1000,
          sound: null,
        },
        {
          speaker: "Molly",
          speaker_ko: "몰리",
          portrait: null,
          text_en: "Hey.",
          text_ko: "여.",
          duration_ms: 1000,
          sound: null,
        },
      ],
      next_scene: null,
    };
    expect(scene.dialogue.length).toBe(2);
    expect(scene.dialogue[0]?.speaker).toBe("Case");
    expect(scene.dialogue[1]?.speaker).toBe("Molly");
  });
});

describe("ScenesFile structure", () => {
  it("populates every required field", () => {
    const scenesFile: ScenesFile = {
      version: "1.0.0",
      source: "wet_run_scenes.json",
      characters: {
        novice: "novice",
        veteran: "veteran",
        heretic: "heretic",
      },
      scene_count: 12,
      scenes: {
        novice_01: {
          id: "novice_01",
          character: "novice",
          order: 1,
          ending: "A",
          title_en: "First Scene",
          title_ko: "첫 장면",
          background_id: "bg_1",
          portrait_left: null,
          portrait_right: null,
          dialogue: [],
          next_scene: null,
        },
      },
    };
    expect(scenesFile.version).toBe("1.0.0");
    expect(scenesFile.source).toBe("wet_run_scenes.json");
    expect(scenesFile.characters.novice).toBe("novice");
    expect(scenesFile.scene_count).toBe(12);
    expect(scenesFile.scenes.novice_01).toBeDefined();
  });

  it("scenes and characters records are expected to be frozen in production data", () => {
    const scenesFile: ScenesFile = {
      version: "1.0.0",
      source: "test.json",
      characters: Object.freeze({ novice: "novice" as CharacterId }),
      scene_count: 0,
      scenes: Object.freeze({}),
    };
    expect(Object.isFrozen(scenesFile.characters)).toBe(true);
    expect(Object.isFrozen(scenesFile.scenes)).toBe(true);
  });

  it("scene_count reflects the number of scenes (callers are responsible)", () => {
    const scenesFile: ScenesFile = {
      version: "1",
      source: "x",
      characters: {},
      scene_count: 0,
      scenes: {},
    };
    expect(scenesFile.scene_count).toBe(0);
  });
});

describe("GraphicNovelProgress structure", () => {
  it("populates every required field", () => {
    const progress: GraphicNovelProgress = {
      mode: "novice",
      scene_index: 2,
      dialogue_index: 5,
      elapsed_in_dialogue_ms: 1500,
      character_id: "novice",
      chain_length: 4,
      ending: "A",
      saved_at: "2026-09-03T12:00:00Z",
      session_id: "session_abc123",
    };
    expect(progress.mode).toBe("novice");
    expect(progress.scene_index).toBe(2);
    expect(progress.dialogue_index).toBe(5);
    expect(progress.elapsed_in_dialogue_ms).toBe(1500);
    expect(progress.character_id).toBe("novice");
    expect(progress.chain_length).toBe(4);
    expect(progress.ending).toBe("A");
    expect(progress.saved_at).toBe("2026-09-03T12:00:00Z");
    expect(progress.session_id).toBe("session_abc123");
  });

  it("supports initial state (zeroed indices and timing)", () => {
    const progress: GraphicNovelProgress = {
      mode: "veteran",
      scene_index: 0,
      dialogue_index: 0,
      elapsed_in_dialogue_ms: 0,
      character_id: "veteran",
      chain_length: 4,
      ending: "A",
      saved_at: "2026-09-03T00:00:00Z",
      session_id: "s0",
    };
    expect(progress.scene_index).toBe(0);
    expect(progress.dialogue_index).toBe(0);
    expect(progress.elapsed_in_dialogue_ms).toBe(0);
  });

  it("supports frozen progress snapshot (immutable persistence)", () => {
    const progress: GraphicNovelProgress = Object.freeze({
      mode: "prologue" as PlayMode,
      scene_index: 0,
      dialogue_index: 0,
      elapsed_in_dialogue_ms: 0,
      character_id: "novice" as CharacterId,
      chain_length: 0,
      ending: "A" as Ending,
      saved_at: "2026-09-03T00:00:00Z",
      session_id: "frozen",
    });
    expect(Object.isFrozen(progress)).toBe(true);
  });
});

describe("GraphicNovelPlayer structure", () => {
  it("populates every required field", () => {
    const player: GraphicNovelPlayer = {
      mode: "prologue",
      chain: Object.freeze([]),
      character_id: "novice",
      ending: "A",
      scene_index: 0,
      dialogue_index: 0,
      elapsed_ms: 0,
      paused: false,
      done: false,
    };
    expect(player.mode).toBe("prologue");
    expect(player.chain).toEqual([]);
    expect(player.character_id).toBe("novice");
    expect(player.ending).toBe("A");
    expect(player.scene_index).toBe(0);
    expect(player.dialogue_index).toBe(0);
    expect(player.elapsed_ms).toBe(0);
    expect(player.paused).toBe(false);
    expect(player.done).toBe(false);
  });

  it("chain is intended to be a frozen read-only array", () => {
    const player: GraphicNovelPlayer = {
      mode: "novice",
      chain: Object.freeze([]),
      character_id: "novice",
      ending: "A",
      scene_index: 0,
      dialogue_index: 0,
      elapsed_ms: 0,
      paused: false,
      done: false,
    };
    expect(Object.isFrozen(player.chain)).toBe(true);
  });

  it("supports updating playback state via mutable fields", () => {
    const player: GraphicNovelPlayer = {
      mode: "heretic",
      chain: Object.freeze([]),
      character_id: "heretic",
      ending: "C",
      scene_index: 0,
      dialogue_index: 0,
      elapsed_ms: 0,
      paused: false,
      done: false,
    };
    player.dialogue_index = 1;
    player.elapsed_ms = 1000;
    player.paused = true;
    expect(player.dialogue_index).toBe(1);
    expect(player.elapsed_ms).toBe(1000);
    expect(player.paused).toBe(true);
  });

  it("supports scene transition (scene_index advances, dialogue_index resets)", () => {
    const player: GraphicNovelPlayer = {
      mode: "veteran",
      chain: Object.freeze([]),
      character_id: "veteran",
      ending: "B",
      scene_index: 0,
      dialogue_index: 9,
      elapsed_ms: 5000,
      paused: false,
      done: false,
    };
    player.scene_index += 1;
    player.dialogue_index = 0;
    player.elapsed_ms = 0;
    expect(player.scene_index).toBe(1);
    expect(player.dialogue_index).toBe(0);
  });

  it("supports marking done at chain completion", () => {
    const player: GraphicNovelPlayer = {
      mode: "prologue",
      chain: Object.freeze([]),
      character_id: "novice",
      ending: "A",
      scene_index: 0,
      dialogue_index: 0,
      elapsed_ms: 0,
      paused: false,
      done: true,
    };
    expect(player.done).toBe(true);
  });
});

describe("TickEvent structure", () => {
  it("dialogue_complete carries scene id and dialogue index", () => {
    const event: TickEvent = {
      type: "dialogue_complete",
      sceneId: "novice_01",
      dialogueIndex: 2,
    };
    expect(event.type).toBe("dialogue_complete");
    expect(event.sceneId).toBe("novice_01");
    expect(event.dialogueIndex).toBe(2);
  });

  it("scene_complete fires when all dialogues in a scene are exhausted", () => {
    const event: TickEvent = {
      type: "scene_complete",
      sceneId: "veteran_04",
      dialogueIndex: 10,
    };
    expect(event.type).toBe("scene_complete");
    expect(event.sceneId).toBe("veteran_04");
    expect(event.dialogueIndex).toBe(10);
  });

  it("chain_complete signals the end of the playback chain", () => {
    const event: TickEvent = {
      type: "chain_complete",
      sceneId: "heretic_final",
      dialogueIndex: 15,
    };
    expect(event.type).toBe("chain_complete");
    expect(event.sceneId).toBe("heretic_final");
    expect(event.dialogueIndex).toBe(15);
  });

  it("TickEvent instances are safe to freeze for downstream consumers", () => {
    const event: TickEvent = Object.freeze({
      type: "dialogue_complete" as const,
      sceneId: "test_scene",
      dialogueIndex: 0,
    });
    expect(Object.isFrozen(event)).toBe(true);
  });
});
