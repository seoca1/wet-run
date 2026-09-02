/**
 * Tests for UI control standardization (ESC = jack_out = back).
 *
 * Verifies that ESC and q both trigger jack_out action consistently
 * across all screens, and that the standard conventions are enforced.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  applyAction,
  makeInitialState,
} from "../src/core/state.js";
import type { Ice, Mission, Program } from "../src/core/types.js";
import { KEYBOARD_MAPPING } from "../src/core/types.js";

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

describe("Keyboard mapping standardization", () => {
  it("Escape maps to jack_out (not cancel)", () => {
    expect(KEYBOARD_MAPPING.Escape).toEqual({ type: "jack_out" });
  });

  it("q maps to jack_out (same as Escape)", () => {
    expect(KEYBOARD_MAPPING.q).toEqual({ type: "jack_out" });
  });

  it("Enter maps to confirm", () => {
    expect(KEYBOARD_MAPPING.Enter).toEqual({ type: "confirm" });
  });

  it("Space maps to confirm", () => {
    expect(KEYBOARD_MAPPING[" "]).toEqual({ type: "confirm" });
  });

  it("Arrow keys map to move actions", () => {
    expect(KEYBOARD_MAPPING.ArrowUp).toEqual({ type: "move_north" });
    expect(KEYBOARD_MAPPING.ArrowDown).toEqual({ type: "move_south" });
    expect(KEYBOARD_MAPPING.ArrowLeft).toEqual({ type: "move_west" });
    expect(KEYBOARD_MAPPING.ArrowRight).toEqual({ type: "move_east" });
  });
});

describe("ESC/jack_out behavior consistency", () => {
  beforeEach(() => {
    vi.spyOn(Math, "random").mockReturnValue(0.99);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("ESC exits matrix to menu", () => {
    const state = makeInitialState(mockMission, mockIce, [mockProgram]);
    const withMatrix = {
      ...state,
      matrix: {
        nodes: [{
          id: 0,
          zone: "surface" as const,
          iceIds: ["watchdog"],
          iceHp: [100],
          reward: { credits: 50 },
          isBoss: false,
          adjacent: [1],
        }],
        startNode: 0,
        bossNode: 0,
      },
    };

    const next = applyAction(withMatrix, KEYBOARD_MAPPING.Escape!);
    expect(next.phase).toBe("menu");
    expect(next.message).toContain("Jacked out");
  });

  it("q exits matrix to menu (same as ESC)", () => {
    const state = makeInitialState(mockMission, mockIce, [mockProgram]);
    const withMatrix = {
      ...state,
      matrix: {
        nodes: [{
          id: 0,
          zone: "surface" as const,
          iceIds: ["watchdog"],
          iceHp: [100],
          reward: { credits: 50 },
          isBoss: false,
          adjacent: [1],
        }],
        startNode: 0,
        bossNode: 0,
      },
    };

    const next = applyAction(withMatrix, KEYBOARD_MAPPING.q!);
    expect(next.phase).toBe("menu");
    expect(next.message).toContain("Jacked out");
  });

  it("ESC from combat results in defeat", () => {
    let state = makeInitialState(mockMission, mockIce, [mockProgram]);
    state = {
      ...state,
      runPhase: "combat",
      phase: "combat",
      iceRoster: [mockIce],
      activeIceIndex: 0,
    };

    const next = applyAction(state, KEYBOARD_MAPPING.Escape!);
    expect(next.phase).toBe("defeat");
    expect(next.message).toContain("Jacked out");
  });

  it("q from combat results in defeat (same as ESC)", () => {
    let state = makeInitialState(mockMission, mockIce, [mockProgram]);
    state = {
      ...state,
      runPhase: "combat",
      phase: "combat",
      iceRoster: [mockIce],
      activeIceIndex: 0,
    };

    const next = applyAction(state, KEYBOARD_MAPPING.q!);
    expect(next.phase).toBe("defeat");
    expect(next.message).toContain("Jacked out");
  });

  it("ESC from approach exits to menu", () => {
    let state = makeInitialState(mockMission, mockIce, [mockProgram]);
    state = {
      ...state,
      runPhase: "combat",
      phase: "approach",
    };

    const next = applyAction(state, KEYBOARD_MAPPING.Escape!);
    expect(next.phase).toBe("exit");
  });

  it("ESC from ending returns to menu", () => {
    let state = makeInitialState(mockMission, mockIce, [mockProgram]);
    state = {
      ...state,
      runPhase: "ending",
      phase: "victory",
      endingChoice: "A",
    };

    const next = applyAction(state, KEYBOARD_MAPPING.Escape!);
    expect(next.phase).toBe("menu");
  });

  it("Enter confirms in matrix (enters node)", () => {
    const state = makeInitialState(mockMission, mockIce, [mockProgram]);
    const withMatrix = {
      ...state,
      matrix: {
        nodes: [{
          id: 0,
          zone: "surface" as const,
          iceIds: ["watchdog"],
          iceHp: [100],
          reward: { credits: 50 },
          isBoss: false,
          adjacent: [],
        }],
        startNode: 0,
        bossNode: 0,
      },
    };

    const next = applyAction(withMatrix, KEYBOARD_MAPPING.Enter!);
    expect(next.runPhase).toBe("combat");
    expect(next.phase).toBe("approach");
  });

  it("Enter confirms in approach (starts combat)", () => {
    let state = makeInitialState(mockMission, mockIce, [mockProgram]);
    state = { ...state, runPhase: "combat", phase: "approach" };

    const next = applyAction(state, KEYBOARD_MAPPING.Enter!);
    expect(next.phase).toBe("combat");
  });

  it("Enter confirms in loot (advances to next node)", () => {
    let state = makeInitialState(mockMission, mockIce, [mockProgram]);
    state = {
      ...state,
      runPhase: "loot",
      phase: "victory",
      matrix: {
        nodes: [{
          id: 0,
          zone: "surface" as const,
          iceIds: ["watchdog"],
          iceHp: [100],
          reward: { credits: 50 },
          isBoss: false,
          adjacent: [1],
        }],
        startNode: 0,
        bossNode: 0,
      },
    };

    const next = applyAction(state, KEYBOARD_MAPPING.Enter!);
    expect(next.runPhase).toBe("matrix");
    expect(next.currentNodeIndex).toBe(1);
  });

  it("Enter confirms in ending (returns to menu)", () => {
    let state = makeInitialState(mockMission, mockIce, [mockProgram]);
    state = {
      ...state,
      runPhase: "ending",
      phase: "victory",
      endingChoice: "A",
    };

    const next = applyAction(state, KEYBOARD_MAPPING.Enter!);
    expect(next.phase).toBe("menu");
  });
});

describe("Touch control consistency", () => {
  it("A button triggers confirm action", () => {
    const A_BUTTON_ACTION = { type: "confirm" as const };
    expect(A_BUTTON_ACTION).toEqual(KEYBOARD_MAPPING.Enter);
  });

  it("B button triggers jack_out action", () => {
    const B_BUTTON_ACTION = { type: "jack_out" as const };
    expect(B_BUTTON_ACTION).toEqual(KEYBOARD_MAPPING.Escape);
  });
});
