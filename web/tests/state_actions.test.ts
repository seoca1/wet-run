import { describe, it, expect } from "vitest";
import { 
  applyMatrixAction, 
  applyLootAction, 
  applyDeathAction, 
  applyEndingAction, 
  applyMenuAction, 
  applyApproachAction, 
  applyCombatAction,
  applyEndAction
} from "../src/core/state_actions.ts";
import type { GameState, Ice, GameAction, Mission, Program } from "../src/core/types.ts";
import { makeInitialState } from "../src/core/state.ts";

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

function createMockGameState(overrides: Partial<GameState> = {}): GameState {
  const base = makeInitialState(mockMission, mockIce, [mockProgram]);
  return { ...base, ...overrides };
}

function createMockIce(overrides: Partial<Ice> = {}): Ice {
  return { ...mockIce, ...overrides };
}

describe("applyMatrixAction", () => {
  it("transitions to combat phase when confirming on a node with ICE", () => {
    const state = createMockGameState({
      phase: "approach",
      runPhase: "matrix",
      matrix: {
        nodes: [
          { id: 0, zone: "surface", iceIds: ["ice1"], iceHp: [50], reward: { credits: 100 }, isBoss: false, adjacent: [1] }
        ],
        startNode: 0,
        bossNode: 0
      },
      currentNodeIndex: 0,
      iceRoster: [createMockIce({ id: "ice1", hp: 50 })]
    });
    const action: GameAction = { type: "confirm" };
    const result = applyMatrixAction(state, action);
    expect(result.runPhase).toBe("combat");
    expect(result.phase).toBe("approach");
    expect(result.iceRoster.length).toBeGreaterThan(0);
  });

  it("does nothing when confirming on a node with no ICE", () => {
    const state = createMockGameState({
      matrix: {
        nodes: [
          { id: 0, zone: "surface", iceIds: [], iceHp: [], reward: { credits: 0 }, isBoss: false, adjacent: [] }
        ],
        startNode: 0,
        bossNode: 0
      },
      currentNodeIndex: 0
    });
    const action: GameAction = { type: "confirm" };
    const result = applyMatrixAction(state, action);
    expect(result).toBe(state);
  });

  it("sets boss phase to 1 when entering boss node", () => {
    const state = createMockGameState({
      matrix: {
        nodes: [
          { id: 0, zone: "core", iceIds: ["boss1"], iceHp: [200], reward: { credits: 500 }, isBoss: true, adjacent: [] }
        ],
        startNode: 0,
        bossNode: 0
      },
      currentNodeIndex: 0,
      bossPhase: 0
    });
    const action: GameAction = { type: "confirm" };
    const result = applyMatrixAction(state, action);
    expect(result.bossPhase).toBe(1);
  });

  it("jacks out to menu when jack_out action", () => {
    const state = createMockGameState({ phase: "approach" });
    const action: GameAction = { type: "jack_out" };
    const result = applyMatrixAction(state, action);
    expect(result.phase).toBe("menu");
    expect(result.message).toContain("Jacked out");
  });

  it("adds VFX when entering matrix node", () => {
    const state = createMockGameState({
      matrix: {
        nodes: [
          { id: 0, zone: "surface", iceIds: ["ice1"], iceHp: [50], reward: { credits: 100 }, isBoss: false, adjacent: [] }
        ],
        startNode: 0,
        bossNode: 0
      },
      currentNodeIndex: 0,
      vfxInstances: []
    });
    const action: GameAction = { type: "confirm" };
    const result = applyMatrixAction(state, action);
    expect(result.vfxInstances.length).toBeGreaterThan(0);
    expect(result.vfxInstances.some(v => v.kind === "room_flash")).toBe(true);
  });

  it("caps ICE roster at 4 enemies", () => {
    const state = createMockGameState({
      matrix: {
        nodes: [
          { id: 0, zone: "surface", iceIds: ["ice1", "ice2", "ice3", "ice4", "ice5", "ice6"], iceHp: [50, 50, 50, 50, 50, 50], reward: { credits: 300 }, isBoss: false, adjacent: [] }
        ],
        startNode: 0,
        bossNode: 0
      },
      currentNodeIndex: 0
    });
    const action: GameAction = { type: "confirm" };
    const result = applyMatrixAction(state, action);
    expect(result.iceRoster.length).toBeLessThanOrEqual(4);
  });

  it("adds data_acquired VFX for cache nodes", () => {
    const state = createMockGameState({
      matrix: {
        nodes: [
          { id: 0, zone: "surface", iceIds: ["ice1"], iceHp: [50], reward: { credits: 100 }, isBoss: false, adjacent: [], eventKind: "cache" }
        ],
        startNode: 0,
        bossNode: 0
      },
      currentNodeIndex: 0,
      vfxInstances: []
    });
    const action: GameAction = { type: "confirm" };
    const result = applyMatrixAction(state, action);
    expect(result.vfxInstances.some(v => v.kind === "data_acquired")).toBe(true);
  });

  it("increments turn count when entering combat", () => {
    const state = createMockGameState({
      matrix: {
        nodes: [
          { id: 0, zone: "surface", iceIds: ["ice1"], iceHp: [50], reward: { credits: 100 }, isBoss: false, adjacent: [] }
        ],
        startNode: 0,
        bossNode: 0
      },
      currentNodeIndex: 0,
      turnCount: 5
    });
    const action: GameAction = { type: "confirm" };
    const result = applyMatrixAction(state, action);
    expect(result.turnCount).toBe(6);
  });
});

describe("applyLootAction", () => {
  it("advances to next node when confirming with adjacent nodes", () => {
    const state = createMockGameState({
      runPhase: "loot",
      matrix: {
        nodes: [
          { id: 0, zone: "surface", iceIds: [], iceHp: [], reward: { credits: 0 }, isBoss: false, adjacent: [1] },
          { id: 1, zone: "mid", iceIds: ["ice2"], iceHp: [75], reward: { credits: 150 }, isBoss: false, adjacent: [] }
        ],
        startNode: 0,
        bossNode: 1
      },
      currentNodeIndex: 0,
      visitedNodes: [0]
    });
    const action: GameAction = { type: "confirm" };
    const result = applyLootAction(state, action);
    expect(result.currentNodeIndex).toBe(1);
    expect(result.visitedNodes).toContain(1);
    expect(result.runPhase).toBe("matrix");
  });

  it("transitions to ending phase when no adjacent nodes", () => {
    const state = createMockGameState({
      runPhase: "loot",
      matrix: {
        nodes: [
          { id: 0, zone: "core", iceIds: [], iceHp: [], reward: { credits: 0 }, isBoss: false, adjacent: [] }
        ],
        startNode: 0,
        bossNode: 0
      },
      currentNodeIndex: 0
    });
    const action: GameAction = { type: "confirm" };
    const result = applyLootAction(state, action);
    expect(result.runPhase).toBe("ending");
    expect(result.endingChoice).toBeTruthy();
  });

  it("does not duplicate visited nodes", () => {
    const state = createMockGameState({
      runPhase: "loot",
      matrix: {
        nodes: [
          { id: 0, zone: "surface", iceIds: [], iceHp: [], reward: { credits: 0 }, isBoss: false, adjacent: [0] }
        ],
        startNode: 0,
        bossNode: 0
      },
      currentNodeIndex: 0,
      visitedNodes: [0]
    });
    const action: GameAction = { type: "confirm" };
    const result = applyLootAction(state, action);
    expect(result.visitedNodes.filter(n => n === 0).length).toBe(1);
  });

  it("transitions to ending when matrix is null", () => {
    const state = createMockGameState({
      runPhase: "loot",
      matrix: null
    });
    const action: GameAction = { type: "confirm" };
    const result = applyLootAction(state, action);
    expect(result.runPhase).toBe("ending");
  });
});

describe("applyDeathAction", () => {
  it("transitions to defeat phase when trigger_death", () => {
    const state = createMockGameState({ phase: "combat" });
    const action: GameAction = { type: "trigger_death" };
    const result = applyDeathAction(state, action);
    expect(result.phase).toBe("defeat");
    expect(result.message).toBe("FLATLINE");
    expect(result.totalDeaths).toBe(state.totalDeaths + 1);
  });

  it("adds deceased jockey to archive on death", () => {
    const state = createMockGameState({ deceasedJockeys: [] });
    const action: GameAction = { type: "trigger_death" };
    const result = applyDeathAction(state, action);
    expect(result.deceasedJockeys.length).toBe(1);
    expect(result.lastDeathSummary).not.toBeNull();
  });

  it("restarts with new jockey when select_restart new_jockey", () => {
    const state = createMockGameState({ phase: "defeat" });
    const action: GameAction = { type: "select_restart", choice: "new_jockey" };
    const result = applyDeathAction(state, action);
    expect(result.phase).toBe("menu");
    expect(result.runPhase).toBe("matrix");
  });

  it("restarts with same jockey and full HP when select_restart same_jockey", () => {
    const state = createMockGameState({ 
      phase: "defeat", 
      player: { hp: 0, maxHp: 100, alarm: 50, credits: 0, handSize: 5 }
    });
    const action: GameAction = { type: "select_restart", choice: "same_jockey" };
    const result = applyDeathAction(state, action);
    expect(result.phase).toBe("menu");
    expect(result.player.hp).toBe(100);
    expect(result.player.alarm).toBe(0);
  });

  it("transitions to hall of dead when select_restart hall_of_dead", () => {
    const state = createMockGameState({ phase: "defeat" });
    const action: GameAction = { type: "select_restart", choice: "hall_of_dead" };
    const result = applyDeathAction(state, action);
    expect(result.phase).toBe("menu");
    expect(result.message).toContain("Hall of Dead");
  });

  it("returns to menu when select_restart main_menu", () => {
    const state = createMockGameState({ phase: "defeat" });
    const action: GameAction = { type: "select_restart", choice: "main_menu" };
    const result = applyDeathAction(state, action);
    expect(result.phase).toBe("menu");
    expect(result.runPhase).toBe("matrix");
  });
});

describe("applyEndingAction", () => {
  it("returns to menu on confirm", () => {
    const state = createMockGameState({ runPhase: "ending", endingChoice: "arc1_cowboy_up" });
    const action: GameAction = { type: "confirm" };
    const result = applyEndingAction(state, action);
    expect(result.phase).toBe("menu");
    expect(result.message).toContain("Ending");
  });

  it("returns to menu on jack_out", () => {
    const state = createMockGameState({ runPhase: "ending", endingChoice: "arc1_first_blood" });
    const action: GameAction = { type: "jack_out" };
    const result = applyEndingAction(state, action);
    expect(result.phase).toBe("menu");
  });
});

describe("applyMenuAction", () => {
  it("transitions to approach phase on confirm", () => {
    const state = createMockGameState({ phase: "menu" });
    const action: GameAction = { type: "confirm" };
    const result = applyMenuAction(state, action);
    expect(result.phase).toBe("approach");
    expect(result.message).toContain("Jacking in");
  });

  it("adds jackin VFX on confirm", () => {
    const state = createMockGameState({ phase: "menu", vfxInstances: [] });
    const action: GameAction = { type: "confirm" };
    const result = applyMenuAction(state, action);
    expect(result.vfxInstances.some(v => v.kind === "jackin_glitch")).toBe(true);
  });

  it("exits game on jack_out", () => {
    const state = createMockGameState({ phase: "menu" });
    const action: GameAction = { type: "jack_out" };
    const result = applyMenuAction(state, action);
    expect(result.phase).toBe("exit");
  });
});

describe("applyApproachAction", () => {
  it("transitions to combat phase on confirm", () => {
    const state = createMockGameState({ phase: "approach" });
    const action: GameAction = { type: "confirm" };
    const result = applyApproachAction(state, action);
    expect(result.phase).toBe("combat");
    expect(result.turnCount).toBe(state.turnCount + 1);
  });

  it("transitions to combat phase on use_program", () => {
    const state = createMockGameState({ phase: "approach" });
    const action: GameAction = { type: "use_program", programId: "test" };
    const result = applyApproachAction(state, action);
    expect(result.phase).toBe("combat");
  });

  it("exits to defeat on jack_out", () => {
    const state = createMockGameState({ phase: "approach" });
    const action: GameAction = { type: "jack_out" };
    const result = applyApproachAction(state, action);
    expect(result.phase).toBe("exit");
  });
});

describe("applyCombatAction", () => {
  it("cycles to next alive target on cycle_target", () => {
    const state = createMockGameState({
      phase: "combat",
      iceRoster: [
        createMockIce({ hp: 100 }),
        createMockIce({ hp: 50 }),
        createMockIce({ hp: 0 })
      ],
      activeIceIndex: 0
    });
    const action: GameAction = { type: "cycle_target" };
    const result = applyCombatAction(state, action);
    expect(result.activeIceIndex).toBe(1);
  });

  it("returns unchanged state when using non-existent program", () => {
    const state = createMockGameState({ 
      phase: "combat",
      deck: []
    });
    const action: GameAction = { type: "use_program", programId: "nonexistent" };
    const result = applyCombatAction(state, action);
    expect(result.message).toContain("not in hand");
  });

  it("transitions to defeat on jack_out", () => {
    const state = createMockGameState({ phase: "combat" });
    const action: GameAction = { type: "jack_out" };
    const result = applyCombatAction(state, action);
    expect(result.phase).toBe("defeat");
    expect(result.message).toContain("Jacked out");
  });
});

describe("applyEndAction", () => {
  it("exits game on confirm", () => {
    const state = createMockGameState({ phase: "victory" });
    const action: GameAction = { type: "confirm" };
    const result = applyEndAction(state, action);
    expect(result.phase).toBe("exit");
  });

  it("returns unchanged state for other actions", () => {
    const state = createMockGameState({ phase: "victory" });
    const action: GameAction = { type: "jack_out" };
    const result = applyEndAction(state, action);
    expect(result).toBe(state);
  });
});
