/**
 * Integration tests for Menu → Stage → Combat flow.
 *
 * Tests the complete game flow from main menu through stage selection to combat.
 * Focuses on state transitions, phase management, and edge cases.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  applyAction,
  makeInitialState,
  resolveProgramSelection,
} from "../src/core/state.js";
import type { Ice, Mission, Program, GameState } from "../src/core/types.js";
import { KEYBOARD_MAPPING } from "../src/core/types.js";

// ============================================================================
// Test fixtures
// ============================================================================

const mockMission: Mission = {
  id: "test_mission",
  title: "Test Mission",
  fixer: "test_fixer",
  arc: 1,
  zone: "surface",
  grade_min: 1,
  grade_max: 3,
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
  effect: "attack",
  description: "Test attack program",
  aoe: false,
};

const mockMatrix = {
  nodes: [
    {
      id: 0,
      zone: "surface" as const,
      iceIds: ["watchdog"],
      iceHp: [100],
      reward: { credits: 50 },
      isBoss: false,
      adjacent: [1],
    },
    {
      id: 1,
      zone: "mid" as const,
      iceIds: ["watchdog"],
      iceHp: [100],
      reward: { credits: 75 },
      isBoss: false,
      adjacent: [],
    },
  ],
  startNode: 0,
  bossNode: 1,
};

// ============================================================================
// Helper functions
// ============================================================================

/** Build a state at menu phase (initial state) */
function buildMenuState(): GameState {
  return makeInitialState(mockMission, mockIce, [mockProgram]);
}

/** Build a state ready for stage selection (matrix phase) */
function buildMatrixState(): GameState {
  const base = buildMenuState();
  return {
    ...base,
    runPhase: "matrix",
    phase: "approach",
    matrix: mockMatrix,
    currentNodeIndex: 0,
  };
}

/** Build a state in combat */
function buildCombatState(): GameState {
  const base = buildMatrixState();
  return {
    ...base,
    runPhase: "combat",
    phase: "combat",
    iceRoster: [{ ...mockIce }],
    activeIceIndex: 0,
    dixieLastAttackMs: Date.now(),
  };
}

// ============================================================================
// Test Suite: Menu → Stage Flow
// ============================================================================

describe("Menu → Stage flow", () => {
  beforeEach(() => {
    vi.spyOn(Math, "random").mockReturnValue(0.99);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("initial state starts in menu phase with matrix runPhase", () => {
    const state = buildMenuState();
    expect(state.runPhase).toBe("matrix");
    expect(state.phase).toBe("menu");
  });

  it("matrix confirm transitions to combat phase", () => {
    const state = buildMatrixState();
    const next = applyAction(state, { type: "confirm" });

    expect(next.runPhase).toBe("combat");
    expect(next.phase).toBe("approach");
    expect(next.message).toContain("Entering");
  });

  it("matrix confirm with no nodes returns unchanged", () => {
    const state = buildMatrixState();
    const noNodeMatrix = { ...state, matrix: { ...mockMatrix, nodes: [] } };
    const next = applyAction(noNodeMatrix, { type: "confirm" });

    expect(next).toBe(noNodeMatrix);
  });

  it("matrix confirm with no ice returns unchanged", () => {
    const state = buildMatrixState();
    const noIceMatrix = {
      ...state,
      matrix: {
        ...mockMatrix,
        nodes: [{ ...mockMatrix.nodes[0], iceIds: [] }],
      },
    };
    const next = applyAction(noIceMatrix, { type: "confirm" });

    expect(next).toBe(noIceMatrix);
  });

  it("matrix jack_out returns to menu", () => {
    const state = buildMatrixState();
    const next = applyAction(state, { type: "jack_out" });

    expect(next.phase).toBe("menu");
    expect(next.message).toContain("Jacked out");
  });
});

// ============================================================================
// Test Suite: Stage → Combat Flow
// ============================================================================

describe("Stage → Combat flow", () => {
  beforeEach(() => {
    vi.spyOn(Math, "random").mockReturnValue(0.99);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("approach confirm transitions to combat", () => {
    let state = buildMatrixState();
    // Matrix → approach
    state = applyAction(state, { type: "confirm" });
    expect(state.runPhase).toBe("combat");
    expect(state.phase).toBe("approach");

    // Approach → combat
    state = applyAction(state, { type: "confirm" });
    expect(state.phase).toBe("combat");
    expect(state.runPhase).toBe("combat");
  });

  it("approach use_program transitions to combat", () => {
    let state = buildMatrixState();
    // Matrix → approach
    state = applyAction(state, { type: "confirm" });

    // Approach → combat via use_program
    state = applyAction(state, {
      type: "use_program",
      programId: "test_prog",
    });
    expect(state.phase).toBe("combat");
    expect(state.runPhase).toBe("combat");
  });

  it("approach jack_out exits to menu", () => {
    let state = buildMatrixState();
    // Matrix → approach
    state = applyAction(state, { type: "confirm" });

    // Approach → exit
    state = applyAction(state, { type: "jack_out" });
    expect(state.phase).toBe("exit");
  });
});

// ============================================================================
// Test Suite: Combat → Victory → Loot Flow
// ============================================================================

describe("Combat → Victory → Loot flow", () => {
  beforeEach(() => {
    vi.spyOn(Math, "random").mockReturnValue(0.99);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("use_program that defeats all ICE transitions to loot", () => {
    const fastIce: Ice = { ...mockIce, hp: 5 };
    let state = buildMatrixState();
    // Matrix → approach
    state = applyAction(state, { type: "confirm" });
    state = { ...state, iceRoster: [fastIce] };

    // Approach → combat
    state = applyAction(state, { type: "confirm" });

    // Combat → victory (ICE HP: 5, damage: 5)
    state = applyAction(state, {
      type: "use_program",
      programId: "test_prog",
    });

    expect(state.runPhase).toBe("loot");
    expect(state.phase).toBe("victory");
    expect(state.iceRoster[0]?.hp).toBe(0);
    expect(state.message).toContain("defeated");
  });

  it("use_program that doesn't defeat ICE stays in combat", () => {
    let state = buildMatrixState();
    state = applyAction(state, { type: "confirm" });
    state = applyAction(state, { type: "confirm" });

    // Combat - ICE has 100 HP, damage is 5 from program + 11 from Dixie (8 base + 3 from combo 1)
    state = applyAction(state, {
      type: "use_program",
      programId: "test_prog",
    });

    expect(state.runPhase).toBe("combat");
    expect(state.phase).toBe("combat");
    expect(state.iceRoster[0]?.hp).toBe(84);
  });

  it("loot confirm advances to next node", () => {
    let state = buildMatrixState();
    state = applyAction(state, { type: "confirm" }); // matrix → approach
    state = applyAction(state, { type: "confirm" }); // approach → combat

    const fastIce: Ice = { ...mockIce, hp: 5 };
    state = { ...state, iceRoster: [fastIce] };
    state = applyAction(state, {
      type: "use_program",
      programId: "test_prog",
    }); // combat → loot

    expect(state.runPhase).toBe("loot");

    // Loot → matrix (next node)
    state = applyAction(state, { type: "confirm" });
    expect(state.runPhase).toBe("matrix");
    expect(state.currentNodeIndex).toBe(1); // advanced to node 1
  });

  it("loot confirm on boss node (no adjacent) transitions to ending", () => {
    let state = buildMatrixState();
    // Set up boss node with no adjacent
    const bossMatrix = {
      ...mockMatrix,
      nodes: [
        {
          ...mockMatrix.nodes[0],
          isBoss: true,
          adjacent: [], // no next node
        },
      ],
      bossNode: 0,
    };
    state = { ...state, matrix: bossMatrix, currentNodeIndex: 0 };

    state = applyAction(state, { type: "confirm" }); // matrix → approach
    state = applyAction(state, { type: "confirm" }); // approach → combat

    const fastIce: Ice = { ...mockIce, hp: 5 };
    state = { ...state, iceRoster: [fastIce] };
    state = applyAction(state, {
      type: "use_program",
      programId: "test_prog",
    }); // combat → loot

    // Loot → ending
    state = applyAction(state, { type: "confirm" });
    expect(state.runPhase).toBe("ending");
    expect(state.endingChoice).toMatch(/^arc[1-5]_[a-z_]+$/);
  });
});

// ============================================================================
// Test Suite: Full Run Completion
// ============================================================================

describe("Full run completion", () => {
  beforeEach(() => {
    vi.spyOn(Math, "random").mockReturnValue(0.99);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("complete run: matrix → combat → loot → matrix → combat → loot → ending", () => {
    const fastMatrix = {
      nodes: [
        {
          id: 0,
          zone: "surface" as const,
          iceIds: ["watchdog"],
          iceHp: [5],
          reward: { credits: 50 },
          isBoss: false,
          adjacent: [1],
        },
        {
          id: 1,
          zone: "mid" as const,
          iceIds: ["watchdog"],
          iceHp: [5],
          reward: { credits: 75 },
          isBoss: false,
          adjacent: [],
        },
      ],
      startNode: 0,
      bossNode: 1,
    };

    const prog1: Program = { ...mockProgram, id: "prog1" };
    const prog2: Program = { ...mockProgram, id: "prog2" };

    let state = buildMenuState();
    state = { ...state, matrix: fastMatrix, currentNodeIndex: 0, deck: [prog1, prog2] };

    state = applyAction(state, { type: "confirm" });
    expect(state.runPhase).toBe("combat");
    expect(state.phase).toBe("approach");

    state = applyAction(state, { type: "confirm" });
    expect(state.phase).toBe("combat");

    state = applyAction(state, {
      type: "use_program",
      programId: "prog1",
    });
    expect(state.runPhase).toBe("loot");
    expect(state.iceRoster[0]?.hp).toBe(0);

    state = applyAction(state, { type: "confirm" });
    expect(state.runPhase).toBe("matrix");
    expect(state.currentNodeIndex).toBe(1);

    state = applyAction(state, { type: "confirm" });
    expect(state.runPhase).toBe("combat");
    expect(state.phase).toBe("approach");

    state = applyAction(state, { type: "confirm" });
    expect(state.phase).toBe("combat");

    state = applyAction(state, {
      type: "use_program",
      programId: "prog2",
    });
    expect(state.runPhase).toBe("loot");

    state = applyAction(state, { type: "confirm" });
    expect(state.runPhase).toBe("ending");
    expect(state.endingChoice).toMatch(/^arc[1-5]_[a-z_]+$/);

    state = applyAction(state, { type: "confirm" });
    expect(state.phase).toBe("menu");
  });
});

// ============================================================================
// Test Suite: State Consistency
// ============================================================================

describe("State consistency during transitions", () => {
  beforeEach(() => {
    vi.spyOn(Math, "random").mockReturnValue(0.99);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("player stats persist across phase transitions", () => {
    let state = buildMatrixState();
    state = applyAction(state, { type: "confirm" }); // matrix → approach
    state = applyAction(state, { type: "confirm" }); // approach → combat

    const initialAlarm = state.player.alarm;
    const iceTier = state.iceRoster[state.activeIceIndex]?.tier ?? 1;
    const iceArmor = state.iceRoster[state.activeIceIndex]?.armor ?? 0;
    const enemyDmg = Math.max(1, iceTier * 3 + iceArmor);

    state = applyAction(state, {
      type: "use_program",
      programId: "test_prog",
    });

    expect(state.player.hp).toBe(100 - enemyDmg);
    expect(state.player.alarm).toBe(initialAlarm + mockProgram.cost);
  });

  it("mission data persists across transitions", () => {
    let state = buildMatrixState();
    state = applyAction(state, { type: "confirm" });
    state = applyAction(state, { type: "confirm" });

    expect(state.mission.id).toBe(mockMission.id);
    expect(state.mission.title).toBe(mockMission.title);
  });

  it("deck is consumed during combat", () => {
    let state = buildMatrixState();
    state = applyAction(state, { type: "confirm" });
    state = applyAction(state, { type: "confirm" });

    expect(state.deck.length).toBe(1);

    state = applyAction(state, {
      type: "use_program",
      programId: "test_prog",
    });

    expect(state.deck.length).toBe(0);
    expect(state.discardPile.length).toBe(1);
  });

  it("turn count increments during transitions", () => {
    let state = buildMatrixState();
    const initialTurn = state.turnCount;

    state = applyAction(state, { type: "confirm" }); // matrix → approach
    expect(state.turnCount).toBe(initialTurn + 1);

    state = applyAction(state, { type: "confirm" }); // approach → combat
    expect(state.turnCount).toBe(initialTurn + 2);
  });
});

// ============================================================================
// Test Suite: Edge Cases
// ============================================================================

describe("Edge cases", () => {
  beforeEach(() => {
    vi.spyOn(Math, "random").mockReturnValue(0.99);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("program not in hand returns unchanged state", () => {
    let state = buildMatrixState();
    state = applyAction(state, { type: "confirm" });
    state = applyAction(state, { type: "confirm" });

    const beforeHp = state.player.hp;
    const beforeAlarm = state.player.alarm;
    state = applyAction(state, {
      type: "use_program",
      programId: "nonexistent_program",
    });

    // State should be unchanged (new object but same values)
    expect(state.player.hp).toBe(beforeHp);
    expect(state.player.alarm).toBe(beforeAlarm);
    expect(state.message).toContain("not in hand");
  });

  it("alarm too high blocks program use", () => {
    let state = buildMatrixState();
    state = applyAction(state, { type: "confirm" });
    state = applyAction(state, { type: "confirm" });

    // Set alarm to 95
    state = { ...state, player: { ...state.player, alarm: 95 } };

    // Try to use program with cost 10 (would exceed 100)
    const beforeHp = state.player.hp;
    state = applyAction(state, {
      type: "use_program",
      programId: "test_prog",
    });

    // State should be unchanged (new object but same values)
    expect(state.player.hp).toBe(beforeHp);
    expect(state.player.alarm).toBe(95);
    expect(state.message).toContain("Alarm too high");
  });

  it("invalid confirm actions in menu phase are no-ops", () => {
    const state = buildMenuState();
    // applyMenuAction is dead code (menu is handled by main.ts), but test it anyway
    const next = applyAction(state, { type: "confirm" });
    // Should return unchanged since applyMenuAction is not called
    expect(next).toBe(state);
  });

  it("jack_out from any phase exits appropriately", () => {
    let state = buildMatrixState();

    // Jack out from matrix
    state = applyAction(state, { type: "jack_out" });
    expect(state.phase).toBe("menu");

    // Jack out from approach
    state = buildMatrixState();
    state = applyAction(state, { type: "confirm" }); // → approach
    state = applyAction(state, { type: "jack_out" });
    expect(state.phase).toBe("exit");

    // Jack out from combat
    state = buildCombatState();
    state = applyAction(state, { type: "jack_out" });
    expect(state.phase).toBe("defeat");
  });
});

// ============================================================================
// Test Suite: Keyboard Mapping Integration
// ============================================================================

describe("Keyboard mapping integration", () => {
  beforeEach(() => {
    vi.spyOn(Math, "random").mockReturnValue(0.99);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("Enter key triggers matrix → approach transition", () => {
    const state = buildMatrixState();
    const next = applyAction(state, KEYBOARD_MAPPING.Enter!);
    expect(next.phase).toBe("approach");
  });

  it("Escape key triggers jack_out from matrix", () => {
    const state = buildMatrixState();
    const next = applyAction(state, KEYBOARD_MAPPING.Escape!);
    expect(next.phase).toBe("menu");
  });

  it("digit keys select programs in combat", () => {
    let state = buildMatrixState();
    state = applyAction(state, { type: "confirm" });
    state = applyAction(state, { type: "confirm" });

    const selectAction = KEYBOARD_MAPPING["1"]!;
    const resolved = resolveProgramSelection(state, selectAction);
    expect(resolved).not.toBeNull();
    expect(resolved?.type).toBe("use_program");
  });
});

// ============================================================================
// Test Suite: Multi-ICE Combat
// ============================================================================

describe("Multi-ICE combat", () => {
  beforeEach(() => {
    vi.spyOn(Math, "random").mockReturnValue(0.99);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("defeats all ICE in roster to win", () => {
    const multiIceMatrix = {
      nodes: [
        {
          id: 0,
          zone: "surface" as const,
          iceIds: ["ice1", "ice2"],
          iceHp: [5, 5],
          reward: { credits: 50 },
          isBoss: false,
          adjacent: [],
        },
      ],
      startNode: 0,
      bossNode: 0,
    };

    let state = buildMenuState();
    state = { ...state, matrix: multiIceMatrix, currentNodeIndex: 0 };

    state = applyAction(state, { type: "confirm" });
    expect(state.iceRoster).toHaveLength(2);
    expect(state.iceRoster[0]?.id).toBe("ice1");
    expect(state.iceRoster[1]?.id).toBe("ice2");

    state = applyAction(state, { type: "confirm" });

    state = applyAction(state, {
      type: "use_program",
      programId: "test_prog",
    });

    // Player program kills ice1 (5 dmg), then Dixie kills ice2 (11 dmg: 8 base + 3 combo)
    expect(state.iceRoster[0]?.hp).toBe(0);
    expect(state.iceRoster[1]?.hp).toBe(0);
    expect(state.runPhase).toBe("loot");

    const ice2Prog: Program = { ...mockProgram, id: "prog2" };
    state = { ...state, deck: [ice2Prog], activeIceIndex: 1 };

    state = applyAction(state, {
      type: "use_program",
      programId: "prog2",
    });

    expect(state.iceRoster[1]?.hp).toBe(0);
    expect(state.runPhase).toBe("loot");
    expect(state.phase).toBe("victory");
  });
});
