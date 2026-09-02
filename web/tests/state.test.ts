/** Smoke tests for wetrun-web MVP core.
 *
 * Run with: npm test
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  applyAction,
  buildHudLines,
  makeInitialState,
  resolveProgramSelection,
} from "../src/core/state.js";
import type { Ice, Mission, Program } from "../src/core/types.js";
import { KEYBOARD_MAPPING } from "../src/core/types.js";
import { makeGrid, setCell, setText } from "../src/core/grid.js";
import { PALETTE } from "../src/renderer/palette.js";

const mockMission: Mission = {
  id: "test",
  title: "Test Mission",
  fixer: "test",
  arc: 1,
  zone: "test",
  grade_min: 1,
  grade_max: 1,
  rewards: { credits: 100, materials: {} },
};

const mockIce: Ice = {
  id: "watchdog",
  name: "Watchdog",
  hp: 100,
  armor: 0,
  tier: 1,
};

const mockProgram: Program = {
  id: "test_prog",
  name: "Test Program",
  tier: 1,
  cost: 10,
  effect: "test",
  description: "Test",
  aoe: false,
};

describe("state machine", () => {
  it("starts in matrix phase (Tier 5 default)", () => {
    const state = makeInitialState(mockMission, mockIce, [mockProgram]);
    expect(state.runPhase).toBe("matrix");
  });

  it("matrix → combat on confirm (when matrix has nodes)", () => {
    const state = makeInitialState(mockMission, mockIce, [mockProgram]);
    const withMatrix = { ...state, matrix: { nodes: [], startNode: 0, bossNode: 0 } };
    // Empty matrix returns state unchanged (no combat available).
    expect(applyAction(withMatrix, { type: "confirm" })).toBe(withMatrix);
  });

  it("approach → combat on confirm", () => {
    let state = makeInitialState(mockMission, mockIce, [mockProgram]);
    state = { ...state, runPhase: "combat", phase: "approach" };
    state = applyAction(state, { type: "confirm" }); // approach → combat
    expect(state.phase).toBe("combat");
  });

  it("jack_out exits to menu from matrix", () => {
    const state = makeInitialState(mockMission, mockIce, [mockProgram]);
    const next = applyAction(state, { type: "jack_out" });
    expect(next.phase).toBe("menu");
  });
});

describe("combat", () => {
  /** Build a state already in combat (Tier 5: runPhase="combat", phase="combat")
   * with the active ICE in iceRoster. This is the state machine post-Tier 5.
   */
  function buildCombatState(ice: Ice = mockIce): ReturnType<typeof makeInitialState> {
    const base = makeInitialState(mockMission, ice, [mockProgram]);
    return {
      ...base,
      runPhase: "combat",
      phase: "combat",
      iceRoster: [{ ...ice }],
      activeIceIndex: 0,
      dixieLastAttackMs: Date.now(),
    };
  }

  // Mock Math.random to suppress the 20% burn proc — tests need deterministic
  // damage values (95 = 100 - 5 base damage). >1.0 means proc never fires.
  beforeEach(() => {
    vi.spyOn(Math, "random").mockReturnValue(0.99);
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("use_program deals damage and increments alarm", () => {
    const inCombat = buildCombatState();
    const afterUse = applyAction(inCombat, {
      type: "use_program",
      programId: "test_prog",
    });
    expect(afterUse.iceRoster[0]?.hp).toBe(95); // tier 1 * 5 = 5 dmg
    expect(afterUse.player.alarm).toBe(10);
    expect(afterUse.deck.length).toBe(0); // card consumed
  });

  it("defeats ICE when HP reaches 0 (transitions to loot)", () => {
    const fastIce: Ice = { ...mockIce, hp: 5 };
    const inCombat = buildCombatState(fastIce);
    const afterUse = applyAction(inCombat, {
      type: "use_program",
      programId: "test_prog",
    });
    expect(afterUse.runPhase).toBe("loot");
    expect(afterUse.phase).toBe("victory");
    expect(afterUse.message).toContain("defeated");
  });
});

describe("hud", () => {
  it("includes hp, alarm, credits lines", () => {
    const state = makeInitialState(mockMission, mockIce, [mockProgram]);
    const lines = buildHudLines(state);
    expect(lines.some((l) => l.startsWith("HP "))).toBe(true);
    expect(lines.some((l) => l.startsWith("Alarm "))).toBe(true);
    expect(lines.some((l) => l.startsWith("Credits "))).toBe(true);
  });
});

describe("keyboard mapping", () => {
  it("has all required keys", () => {
    expect(KEYBOARD_MAPPING.ArrowUp).toBeDefined();
    expect(KEYBOARD_MAPPING.ArrowDown).toBeDefined();
    expect(KEYBOARD_MAPPING.ArrowLeft).toBeDefined();
    expect(KEYBOARD_MAPPING.ArrowRight).toBeDefined();
    expect(KEYBOARD_MAPPING.Enter).toBeDefined();
    expect(KEYBOARD_MAPPING[" "]).toBeDefined();
    expect(KEYBOARD_MAPPING.Escape).toBeDefined();
    expect(KEYBOARD_MAPPING.q).toBeDefined();
  });

  it("emits select_program for digits 1-9 (regression: progress bug)", () => {
    for (let i = 1; i <= 9; i++) {
      const action = KEYBOARD_MAPPING[String(i)];
      expect(action, `key "${i}" should be mapped`).toBeDefined();
      expect(action?.type).toBe("select_program");
      if (action?.type === "select_program") {
        expect(action.handIndex).toBe(i);
      }
    }
  });
});

describe("resolveProgramSelection (input → reducer bridge)", () => {
  it("resolves hand index 1 to first program", () => {
    const state = makeInitialState(mockMission, mockIce, [mockProgram]);
    const resolved = resolveProgramSelection(state, { type: "select_program", handIndex: 1 });
    expect(resolved).toEqual({ type: "use_program", programId: "test_prog" });
  });

  it("returns null for out-of-range index", () => {
    const state = makeInitialState(mockMission, mockIce, [mockProgram]);
    const resolved = resolveProgramSelection(state, { type: "select_program", handIndex: 5 });
    expect(resolved).toBeNull();
  });

  it("returns null for non-select actions", () => {
    const state = makeInitialState(mockMission, mockIce, [mockProgram]);
    expect(resolveProgramSelection(state, { type: "confirm" })).toBeNull();
    expect(resolveProgramSelection(state, { type: "move_north" })).toBeNull();
  });
});

describe("end-to-end combat progression (regression: 'stuck in combat')", () => {
  it("matrix → approach → combat → use_program → loot via digit key (Tier 5)", () => {
    const fastIce: Ice = { ...mockIce, hp: 1 };
    const state = makeInitialState(mockMission, fastIce, [mockProgram]);
    // Tier 5: state defaults to runPhase="matrix" — set up a matrix with
    // 1 ICE at node 0 so the test exercises the matrix→combat transition.
    const withMatrix = {
      ...state,
      matrix: { nodes: [{ id: 0, zone: "surface" as const, iceIds: ["watchdog"], iceHp: [1], reward: { credits: 50 }, isBoss: false, adjacent: [] }], startNode: 0, bossNode: 0 },
      currentNodeIndex: 0,
    };
    // Press Enter (matrix → approach).
    let next = applyAction(withMatrix, KEYBOARD_MAPPING.Enter!);
    expect(next.phase).toBe("approach");
    // Press Enter (approach → combat).
    next = applyAction(next, KEYBOARD_MAPPING.Enter!);
    expect(next.phase).toBe("combat");
    expect(next.runPhase).toBe("combat");
    // Press "1" (select_program[1]).
    const selectAction = KEYBOARD_MAPPING["1"]!;
    expect(selectAction.type).toBe("select_program");
    const resolved = resolveProgramSelection(next, selectAction);
    expect(resolved).not.toBeNull();
    next = applyAction(next, resolved!);
    // Tier 5: ICE defeated → transition to loot (was 'victory' phase).
    expect(next.runPhase).toBe("loot");
    expect(next.iceRoster[0]?.hp).toBe(0);
  });
});

describe("grid", () => {
  it("makeGrid creates correct dimensions", () => {
    const g = makeGrid(80, 50);
    expect(g.width).toBe(80);
    expect(g.height).toBe(50);
    expect(g.cells.length).toBe(50);
    expect(g.cells[0]?.length).toBe(80);
  });

  it("setCell writes to correct position", () => {
    let g = makeGrid(10, 10);
    g = setCell(g, { x: 3, y: 4 }, { char: "@", fg: PALETTE.GREEN_NEON, bg: PALETTE.BACKGROUND });
    const cell = g.get(3, 4);
    expect(cell?.char).toBe("@");
    expect(cell?.fg).toBe(PALETTE.GREEN_NEON);
  });

  it("setText writes string across cells", () => {
    let g = makeGrid(20, 5);
    g = setText(g, 2, 1, "HI");
    expect(g.get(2, 1)?.char).toBe("H");
    expect(g.get(3, 1)?.char).toBe("I");
  });
});
