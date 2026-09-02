import { describe, it, expect } from "vitest";
import {
  listScenesForCharacter,
  loadSceneChain,
  loadPrologueChain,
  resolveSound,
  soundCategory,
  CHAR_TO_DIR,
  SCENE_SOUND_MAP,
} from "../src/core/graphic_novel_loaders.ts";
import type { SceneData, CharacterId } from "../src/core/graphic_novel_types.ts";

describe("CHAR_TO_DIR", () => {
  it("maps novice to case", () => {
    expect(CHAR_TO_DIR.novice).toBe("case");
  });

  it("maps veteran to sil", () => {
    expect(CHAR_TO_DIR.veteran).toBe("sil");
  });

  it("maps heretic to kas", () => {
    expect(CHAR_TO_DIR.heretic).toBe("kas");
  });

  it("includes all expected characters", () => {
    expect(CHAR_TO_DIR.suit).toBeDefined();
    expect(CHAR_TO_DIR.wigan).toBeDefined();
    expect(CHAR_TO_DIR.angie).toBeDefined();
    expect(CHAR_TO_DIR.sally).toBeDefined();
    expect(CHAR_TO_DIR["3jane"]).toBeDefined();
    expect(CHAR_TO_DIR.neuromancer).toBeDefined();
  });
});

describe("listScenesForCharacter", () => {
  it("returns scenes for novice", () => {
    const scenes = listScenesForCharacter("novice");
    expect(Array.isArray(scenes)).toBe(true);
    expect(scenes.every((s) => s.character === "novice")).toBe(true);
  });

  it("returns scenes for veteran", () => {
    const scenes = listScenesForCharacter("veteran");
    expect(Array.isArray(scenes)).toBe(true);
    expect(scenes.every((s) => s.character === "veteran")).toBe(true);
  });

  it("returns scenes for heretic", () => {
    const scenes = listScenesForCharacter("heretic");
    expect(Array.isArray(scenes)).toBe(true);
    expect(scenes.every((s) => s.character === "heretic")).toBe(true);
  });

  it("sorts scenes by order ascending", () => {
    const scenes = listScenesForCharacter("novice");
    for (let i = 1; i < scenes.length; i++) {
      const prev = scenes[i - 1];
      const curr = scenes[i];
      if (prev && curr) {
        expect(curr.order).toBeGreaterThanOrEqual(prev.order);
      }
    }
  });

  it("returns empty array for unknown character", () => {
    const scenes = listScenesForCharacter("unknown" as CharacterId);
    expect(scenes).toEqual([]);
  });

  it("accepts custom scenes parameter", () => {
    const customScenes: Record<string, SceneData> = {
      test1: {
        id: "test1",
        character: "novice",
        order: 1,
        title_en: "Test",
        title_ko: "테스트",
        ending: "A",
        background_id: "bg1",
        portrait_left: null,
        portrait_right: null,
        dialogue: [],
        next_scene: null,
      },
    };
    const result = listScenesForCharacter("novice", customScenes);
    expect(result.length).toBe(1);
    expect(result[0]?.id).toBe("test1");
  });

  it("filters out other characters", () => {
    const customScenes: Record<string, SceneData> = {
      scene1: {
        id: "scene1",
        character: "novice",
        order: 1,
        title_en: "Test",
        title_ko: "테스트",
        ending: "A",
        background_id: "bg1",
        portrait_left: null,
        portrait_right: null,
        dialogue: [],
        next_scene: null,
      },
      scene2: {
        id: "scene2",
        character: "veteran",
        order: 1,
        title_en: "Test",
        title_ko: "테스트",
        ending: "A",
        background_id: "bg1",
        portrait_left: null,
        portrait_right: null,
        dialogue: [],
        next_scene: null,
      },
    };
    const result = listScenesForCharacter("novice", customScenes);
    expect(result.length).toBe(1);
    expect(result[0]?.character).toBe("novice");
  });
});

describe("loadSceneChain", () => {
  it("loads scenes for a character", () => {
    const chain = loadSceneChain("novice");
    expect(Array.isArray(chain)).toBe(true);
    expect(chain.every((s) => s.character === "novice")).toBe(true);
  });

  it("filters by ending", () => {
    const chain = loadSceneChain("novice", { ending: "A" });
    expect(chain.every((s) => s.ending === "A")).toBe(true);
  });

  it("filters by maxOrder", () => {
    const chain = loadSceneChain("novice", { maxOrder: 2 });
    expect(chain.every((s) => s.order <= 2)).toBe(true);
  });

  it("shuffles when shuffle is true", () => {
    const chain1 = loadSceneChain("novice", { shuffle: false });
    const chain2 = loadSceneChain("novice", { shuffle: true, seed: 42 });
    if (chain1.length > 1 && chain2.length > 1) {
      const ids1 = chain1.map((s) => s.id).join(",");
      const ids2 = chain2.map((s) => s.id).join(",");
      expect(ids1).not.toBe(ids2);
    }
  });

  it("produces deterministic shuffle with same seed", () => {
    const chain1 = loadSceneChain("novice", { shuffle: true, seed: 42 });
    const chain2 = loadSceneChain("novice", { shuffle: true, seed: 42 });
    expect(chain1.map((s) => s.id)).toEqual(chain2.map((s) => s.id));
  });

  it("produces different shuffle with different seed", () => {
    const chain1 = loadSceneChain("novice", { shuffle: true, seed: 1 });
    const chain2 = loadSceneChain("novice", { shuffle: true, seed: 2 });
    if (chain1.length > 1 && chain2.length > 1) {
      expect(chain1.map((s) => s.id)).not.toEqual(chain2.map((s) => s.id));
    }
  });

  it("returns empty array when no scenes match filters", () => {
    const customScenes: Record<string, SceneData> = {
      scene1: {
        id: "scene1",
        character: "novice",
        order: 10,
        title_en: "Test",
        title_ko: "테스트",
        ending: "B",
        background_id: "bg1",
        portrait_left: null,
        portrait_right: null,
        dialogue: [],
        next_scene: null,
      },
    };
    const chain = loadSceneChain(
      "novice",
      { ending: "A", maxOrder: 5, scenes: customScenes },
    );
    expect(chain).toEqual([]);
  });

  it("uses ending A by default", () => {
    const chain = loadSceneChain("novice");
    expect(chain.every((s) => s.ending === "A")).toBe(true);
  });

  it("accepts custom scenes parameter", () => {
    const customScenes: Record<string, SceneData> = {
      custom1: {
        id: "custom1",
        character: "novice",
        order: 1,
        title_en: "Custom",
        title_ko: "커스텀",
        ending: "A",
        background_id: "bg1",
        portrait_left: null,
        portrait_right: null,
        dialogue: [],
        next_scene: null,
      },
    };
    const chain = loadSceneChain("novice", { scenes: customScenes });
    expect(chain[0]?.id).toBe("custom1");
  });
});

describe("loadPrologueChain", () => {
  it("loads scenes from multiple characters", () => {
    const chain = loadPrologueChain({ seed: 42 });
    expect(chain.length).toBeGreaterThan(0);
    const characters = new Set(chain.map((s) => s.character));
    expect(characters.size).toBeGreaterThan(1);
  });

  it("shuffles character order", () => {
    const chain1 = loadPrologueChain({ seed: 1 });
    const chain2 = loadPrologueChain({ seed: 2 });
    if (chain1.length > 0 && chain2.length > 0) {
      expect(chain1[0]?.character).not.toBe(chain2[0]?.character);
    }
  });

  it("is deterministic with same seed", () => {
    const chain1 = loadPrologueChain({ seed: 42 });
    const chain2 = loadPrologueChain({ seed: 42 });
    expect(chain1.map((s) => s.id)).toEqual(chain2.map((s) => s.id));
  });

  it("filters by ending", () => {
    const chain = loadPrologueChain({ ending: "B" });
    expect(chain.every((s) => s.ending === "B")).toBe(true);
  });

  it("filters by maxOrder", () => {
    const chain = loadPrologueChain({ maxOrder: 2 });
    expect(chain.every((s) => s.order <= 2)).toBe(true);
  });

  it("accepts custom scenes parameter", () => {
    const customScenes: Record<string, SceneData> = {
      scene1: {
        id: "scene1",
        character: "novice",
        order: 1,
        title_en: "Scene 1",
        title_ko: "씬 1",
        ending: "A",
        background_id: "bg1",
        portrait_left: null,
        portrait_right: null,
        dialogue: [],
        next_scene: null,
      },
      scene2: {
        id: "scene2",
        character: "veteran",
        order: 1,
        title_en: "Scene 2",
        title_ko: "씬 2",
        ending: "A",
        background_id: "bg1",
        portrait_left: null,
        portrait_right: null,
        dialogue: [],
        next_scene: null,
      },
    };
    const chain = loadPrologueChain({ scenes: customScenes, seed: 42 });
    expect(chain.length).toBeGreaterThan(0);
  });

  it("accepts custom characters parameter", () => {
    const chain = loadPrologueChain({
      characters: ["novice", "veteran"],
      seed: 42,
    });
    const characters = new Set(chain.map((s) => s.character));
    expect(characters.size).toBeLessThanOrEqual(2);
  });

  it("returns empty array when custom characters array is empty", () => {
    const chain = loadPrologueChain({ characters: [] });
    expect(chain).toEqual([]);
  });
});

describe("resolveSound", () => {
  it("returns null for null input", () => {
    expect(resolveSound(null)).toBeNull();
  });

  it("returns null for undefined input", () => {
    expect(resolveSound(undefined)).toBeNull();
  });

  it("maps chiba_rain_loop to theme/chiba", () => {
    expect(resolveSound("chiba_rain_loop")).toBe("theme/chiba");
  });

  it("maps matrix_rain to theme/matrix_rain", () => {
    expect(resolveSound("matrix_rain")).toBe("theme/matrix_rain");
  });

  it("maps jack_in_zap to movement/jack_in_zap", () => {
    expect(resolveSound("jack_in_zap")).toBe("movement/jack_in_zap");
  });

  it("maps jack_out_buzz to movement/jack_out_buzz", () => {
    expect(resolveSound("jack_out_buzz")).toBe("movement/jack_out_buzz");
  });

  it("passes through keys with slash", () => {
    expect(resolveSound("custom/sound")).toBe("custom/sound");
  });

  it("returns null for unmapped keys without slash", () => {
    expect(resolveSound("unknown_sound")).toBeNull();
  });

  it("maps theme_broadcast to theme/broadcast", () => {
    expect(resolveSound("theme_broadcast")).toBe("theme/broadcast");
  });

  it("maps movement_neon_hum to movement/neon_hum", () => {
    expect(resolveSound("movement_neon_hum")).toBe("movement/neon_hum");
  });

  it("maps neon_hum to movement/neon_hum", () => {
    expect(resolveSound("neon_hum")).toBe("movement/neon_hum");
  });

  it("maps black_ice_roar to movement/black_ice_roar", () => {
    expect(resolveSound("black_ice_roar")).toBe("movement/black_ice_roar");
  });
});

describe("soundCategory", () => {
  it("returns category from resolved key", () => {
    expect(soundCategory("theme/chiba")).toBe("theme");
  });

  it("returns movement category", () => {
    expect(soundCategory("movement/neon_hum")).toBe("movement");
  });

  it("returns null for keys without slash", () => {
    expect(soundCategory("nosound")).toBeNull();
  });

  it("returns null for null input", () => {
    expect(soundCategory(null)).toBeNull();
  });

  it("returns null for empty string", () => {
    expect(soundCategory("")).toBeNull();
  });

  it("handles multiple slashes", () => {
    expect(soundCategory("theme/sub/sound")).toBe("theme");
  });

  it("returns null when slash is at position 0", () => {
    expect(soundCategory("/sound")).toBeNull();
  });
});

describe("SCENE_SOUND_MAP", () => {
  it("is frozen", () => {
    expect(Object.isFrozen(SCENE_SOUND_MAP)).toBe(true);
  });

  it("maps all theme sounds", () => {
    expect(SCENE_SOUND_MAP.chiba_rain_loop).toBeDefined();
    expect(SCENE_SOUND_MAP.matrix_rain).toBeDefined();
    expect(SCENE_SOUND_MAP.finn_office).toBeDefined();
    expect(SCENE_SOUND_MAP.loa_drum).toBeDefined();
  });

  it("maps all movement sounds", () => {
    expect(SCENE_SOUND_MAP.jack_in_zap).toBeDefined();
    expect(SCENE_SOUND_MAP.jack_out_buzz).toBeDefined();
    expect(SCENE_SOUND_MAP.neon_hum).toBeDefined();
  });

  it("includes ADR-0049 prefixed aliases", () => {
    expect(SCENE_SOUND_MAP.theme_broadcast).toBeDefined();
    expect(SCENE_SOUND_MAP.theme_hammer_alert).toBeDefined();
    expect(SCENE_SOUND_MAP.movement_neon_hum).toBeDefined();
  });

  it("maps data_extract", () => {
    expect(SCENE_SOUND_MAP.data_extract).toBe("movement/data_extract");
  });

  it("maps broadcast sounds", () => {
    expect(SCENE_SOUND_MAP.broadcast_static).toBe("movement/broadcast_static");
    expect(SCENE_SOUND_MAP.broadcast_out).toBe("movement/broadcast_out");
  });
});
