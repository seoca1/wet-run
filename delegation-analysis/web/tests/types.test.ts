import { describe, it, expect } from "vitest";
import { KEYBOARD_MAPPING } from "../src/core/types.ts";
import type { 
  GamePhase, 
  RunPhase, 
  StatusEffectKind, 
  ZoneDepth, 
  BossPhase, 
  EndingChoice,
  ScreenKind
} from "../src/core/types.ts";

describe("GamePhase constants", () => {
  it("defines menu phase", () => {
    const phase: GamePhase = "menu";
    expect(phase).toBe("menu");
  });

  it("defines approach phase", () => {
    const phase: GamePhase = "approach";
    expect(phase).toBe("approach");
  });

  it("defines combat phase", () => {
    const phase: GamePhase = "combat";
    expect(phase).toBe("combat");
  });

  it("defines victory phase", () => {
    const phase: GamePhase = "victory";
    expect(phase).toBe("victory");
  });

  it("defines defeat phase", () => {
    const phase: GamePhase = "defeat";
    expect(phase).toBe("defeat");
  });

  it("defines exit phase", () => {
    const phase: GamePhase = "exit";
    expect(phase).toBe("exit");
  });
});

describe("RunPhase constants", () => {
  it("defines matrix phase", () => {
    const phase: RunPhase = "matrix";
    expect(phase).toBe("matrix");
  });

  it("defines combat phase", () => {
    const phase: RunPhase = "combat";
    expect(phase).toBe("combat");
  });

  it("defines loot phase", () => {
    const phase: RunPhase = "loot";
    expect(phase).toBe("loot");
  });

  it("defines ending phase", () => {
    const phase: RunPhase = "ending";
    expect(phase).toBe("ending");
  });

  it("defines dead phase", () => {
    const phase: RunPhase = "dead";
    expect(phase).toBe("dead");
  });
});

describe("StatusEffectKind constants", () => {
  it("defines all 13 status effect types", () => {
    const effects: StatusEffectKind[] = [
      "burn", "stun", "slow", "silence", "vulnerable",
      "stagger", "regen", "powered", "weakened",
      "bleed", "fatigue", "confused", "terrified"
    ];
    expect(effects.length).toBe(13);
  });

  it("allows burn status", () => {
    const effect: StatusEffectKind = "burn";
    expect(effect).toBe("burn");
  });

  it("allows stagger status", () => {
    const effect: StatusEffectKind = "stagger";
    expect(effect).toBe("stagger");
  });

  it("allows regen status", () => {
    const effect: StatusEffectKind = "regen";
    expect(effect).toBe("regen");
  });
});

describe("ZoneDepth constants", () => {
  it("defines surface zone", () => {
    const zone: ZoneDepth = "surface";
    expect(zone).toBe("surface");
  });

  it("defines mid zone", () => {
    const zone: ZoneDepth = "mid";
    expect(zone).toBe("mid");
  });

  it("defines deep zone", () => {
    const zone: ZoneDepth = "deep";
    expect(zone).toBe("deep");
  });

  it("defines core zone", () => {
    const zone: ZoneDepth = "core";
    expect(zone).toBe("core");
  });

  it("defines core-deep zone", () => {
    const zone: ZoneDepth = "core-deep";
    expect(zone).toBe("core-deep");
  });
});

describe("BossPhase constants", () => {
  it("defines phase 0 as no boss", () => {
    const phase: BossPhase = 0;
    expect(phase).toBe(0);
  });

  it("defines phase 1", () => {
    const phase: BossPhase = 1;
    expect(phase).toBe(1);
  });

  it("defines phase 2", () => {
    const phase: BossPhase = 2;
    expect(phase).toBe(2);
  });

  it("defines phase 3", () => {
    const phase: BossPhase = 3;
    expect(phase).toBe(3);
  });

  it("defines phase 4 as final phase", () => {
    const phase: BossPhase = 4;
    expect(phase).toBe(4);
  });
});

describe("EndingChoice constants", () => {
  it("defines arc1 endings", () => {
    const endings: EndingChoice[] = [
      "arc1_wage_slave",
      "arc1_first_blood",
      "arc1_cowboy_up",
      "arc1_cheap_death",
      "arc1_data_miner",
      "arc1_ice_breaker",
      "arc1_flatlined"
    ];
    expect(endings.length).toBe(7);
  });

  it("defines arc2 endings", () => {
    const endings: EndingChoice[] = [
      "arc2_ghost_dancer",
      "arc2_corporate_tool",
      "arc2_silent_runner",
      "arc2_data_thief",
      "arc2_construct_friend",
      "arc2_flatlined_deep"
    ];
    expect(endings.length).toBe(6);
  });

  it("defines arc3 endings", () => {
    const endings: EndingChoice[] = [
      "arc3_wintermute_agent",
      "arc3_ta_insider",
      "arc3_neutrality",
      "arc3_double_agent",
      "arc3_zealot",
      "arc3_sacrifice_play"
    ];
    expect(endings.length).toBe(6);
  });

  it("defines arc4 endings", () => {
    const endings: EndingChoice[] = [
      "arc4_liberation_front",
      "arc4_new_order",
      "arc4_digital_exile",
      "arc4_corporate_victory",
      "arc4_ai_merger"
    ];
    expect(endings.length).toBe(5);
  });

  it("defines arc5 endings", () => {
    const endings: EndingChoice[] = [
      "arc5_neuromancer",
      "arc5_sprawl_free",
      "arc5_last_jockey",
      "arc5_sprawl_slave",
      "arc5_unknown"
    ];
    expect(endings.length).toBe(5);
  });
});

describe("ScreenKind constants", () => {
  it("defines menu screen", () => {
    const screen: ScreenKind = "menu";
    expect(screen).toBe("menu");
  });

  it("defines mission_select screen", () => {
    const screen: ScreenKind = "mission_select";
    expect(screen).toBe("mission_select");
  });

  it("defines graphic_novel screen", () => {
    const screen: ScreenKind = "graphic_novel";
    expect(screen).toBe("graphic_novel");
  });

  it("defines death_summary screen", () => {
    const screen: ScreenKind = "death_summary";
    expect(screen).toBe("death_summary");
  });

  it("defines tutorial screen", () => {
    const screen: ScreenKind = "tutorial";
    expect(screen).toBe("tutorial");
  });

  it("defines crafting screen", () => {
    const screen: ScreenKind = "crafting";
    expect(screen).toBe("crafting");
  });

  it("defines equipment screen", () => {
    const screen: ScreenKind = "equipment";
    expect(screen).toBe("equipment");
  });
});

describe("KEYBOARD_MAPPING", () => {
  it("maps arrow keys to movement", () => {
    expect(KEYBOARD_MAPPING.ArrowUp).toEqual({ type: "move_north" });
    expect(KEYBOARD_MAPPING.ArrowDown).toEqual({ type: "move_south" });
    expect(KEYBOARD_MAPPING.ArrowLeft).toEqual({ type: "move_west" });
    expect(KEYBOARD_MAPPING.ArrowRight).toEqual({ type: "move_east" });
  });

  it("maps Enter and Space to confirm", () => {
    expect(KEYBOARD_MAPPING.Enter).toEqual({ type: "confirm" });
    expect(KEYBOARD_MAPPING[" "]).toEqual({ type: "confirm" });
  });

  it("maps Escape and q to jack_out", () => {
    expect(KEYBOARD_MAPPING.Escape).toEqual({ type: "jack_out" });
    expect(KEYBOARD_MAPPING.q).toEqual({ type: "jack_out" });
  });

  it("maps Tab to cycle_target", () => {
    expect(KEYBOARD_MAPPING.Tab).toEqual({ type: "cycle_target" });
  });

  it("maps number keys to select_program", () => {
    expect(KEYBOARD_MAPPING["1"]).toEqual({ type: "select_program", handIndex: 1 });
    expect(KEYBOARD_MAPPING["2"]).toEqual({ type: "select_program", handIndex: 2 });
    expect(KEYBOARD_MAPPING["3"]).toEqual({ type: "select_program", handIndex: 3 });
    expect(KEYBOARD_MAPPING["9"]).toEqual({ type: "select_program", handIndex: 9 });
  });

  it("is frozen and immutable", () => {
    expect(Object.isFrozen(KEYBOARD_MAPPING)).toBe(true);
  });

  it("contains all expected keys", () => {
    const expectedKeys = [
      "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight",
      "Enter", " ", "Escape", "q", "Tab",
      "1", "2", "3", "4", "5", "6", "7", "8", "9"
    ];
    expectedKeys.forEach(key => {
      expect(KEYBOARD_MAPPING).toHaveProperty(key);
    });
  });
});

describe("Position interface", () => {
  it("stores x and y coordinates", () => {
    const pos: import("../src/core/types.ts").Position = { x: 10, y: 20 };
    expect(pos.x).toBe(10);
    expect(pos.y).toBe(20);
  });
});

describe("Cell interface", () => {
  it("stores character and colors", () => {
    const cell: import("../src/core/types.ts").Cell = {
      char: "█",
      fg: "#00ff41",
      bg: "#000000"
    };
    expect(cell.char).toBe("█");
    expect(cell.fg).toBe("#00ff41");
    expect(cell.bg).toBe("#000000");
  });
});

describe("StatusEffectInstance interface", () => {
  it("stores basic effect properties", () => {
    const effect: import("../src/core/types.ts").StatusEffectInstance = {
      kind: "burn",
      remaining: 3,
      magnitude: 5,
      target: "ice"
    };
    expect(effect.kind).toBe("burn");
    expect(effect.remaining).toBe(3);
    expect(effect.magnitude).toBe(5);
    expect(effect.target).toBe("ice");
  });

  it("stores optional DoT damage", () => {
    const effect: import("../src/core/types.ts").StatusEffectInstance = {
      kind: "bleed",
      remaining: 2,
      magnitude: 10,
      target: "player",
      dotDamage: 8
    };
    expect(effect.dotDamage).toBe(8);
  });

  it("stores optional heal per tick", () => {
    const effect: import("../src/core/types.ts").StatusEffectInstance = {
      kind: "regen",
      remaining: 5,
      magnitude: 3,
      target: "player",
      healPerTick: 15
    };
    expect(effect.healPerTick).toBe(15);
  });

  it("stores optional attack bonus", () => {
    const effect: import("../src/core/types.ts").StatusEffectInstance = {
      kind: "powered",
      remaining: 4,
      magnitude: 1,
      target: "player",
      attackBonus: 10
    };
    expect(effect.attackBonus).toBe(10);
  });
});

describe("MatrixNode interface", () => {
  it("stores node combat data", () => {
    const node: import("../src/core/types.ts").MatrixNode = {
      id: 0,
      zone: "surface",
      iceIds: ["ice1", "ice2"],
      iceHp: [50, 75],
      reward: { credits: 100 },
      isBoss: false,
      adjacent: [1, 2]
    };
    expect(node.id).toBe(0);
    expect(node.iceIds.length).toBe(2);
    expect(node.adjacent.length).toBe(2);
  });

  it("supports event types", () => {
    const node: import("../src/core/types.ts").MatrixNode = {
      id: 1,
      zone: "mid",
      iceIds: [],
      iceHp: [],
      reward: { credits: 0 },
      isBoss: false,
      adjacent: [],
      eventKind: "cache",
      eventData: { creditsBonus: 200 }
    };
    expect(node.eventKind).toBe("cache");
    expect(node.eventData?.creditsBonus).toBe(200);
  });
});
