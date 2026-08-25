/** Smoke tests for wetrun-web MVP core.
 *
 * Run with: npm test
 */
import { describe, it, expect } from "vitest";
import { applyAction, buildHudLines, makeInitialState } from "../src/core/state.js";
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
};

describe("state machine", () => {
  it("starts in menu phase", () => {
    const state = makeInitialState(mockMission, mockIce, [mockProgram]);
    expect(state.phase).toBe("menu");
  });

  it("transitions menu → approach on confirm", () => {
    const state = makeInitialState(mockMission, mockIce, [mockProgram]);
    const next = applyAction(state, { type: "confirm" });
    expect(next.phase).toBe("approach");
  });

  it("transitions approach → combat on confirm", () => {
    let state = makeInitialState(mockMission, mockIce, [mockProgram]);
    state = applyAction(state, { type: "confirm" }); // menu → approach
    state = applyAction(state, { type: "confirm" }); // approach → combat
    expect(state.phase).toBe("combat");
  });

  it("jack_out exits from menu", () => {
    const state = makeInitialState(mockMission, mockIce, [mockProgram]);
    const next = applyAction(state, { type: "jack_out" });
    expect(next.phase).toBe("exit");
  });
});

describe("combat", () => {
  it("use_program deals damage and increments alarm", () => {
    const state = makeInitialState(mockMission, mockIce, [mockProgram]);
    const inCombat = applyAction(applyAction(state, { type: "confirm" }), {
      type: "confirm",
    });
    const afterUse = applyAction(inCombat, {
      type: "use_program",
      programId: "test_prog",
    });
    expect(afterUse.ice.hp).toBe(95); // tier 1 * 5 = 5 dmg
    expect(afterUse.player.alarm).toBe(10);
    expect(afterUse.deck.length).toBe(0); // card consumed
  });

  it("defeats ICE when HP reaches 0", () => {
    const fastIce: Ice = { ...mockIce, hp: 5 };
    const state = makeInitialState(mockMission, fastIce, [mockProgram]);
    const inCombat = applyAction(applyAction(state, { type: "confirm" }), {
      type: "confirm",
    });
    const afterUse = applyAction(inCombat, {
      type: "use_program",
      programId: "test_prog",
    });
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
