import { describe, it, expect } from "vitest";
import {
  selectEpitaph,
  createDeceasedJockey,
  generateDeathSummary,
  EPITAPHS,
} from "../src/core/death_cycle.ts";
import type { GameState, Ice, Mission, Program } from "../src/core/types.ts";
import { makeInitialState, applyAction } from "../src/core/state.ts";

const mockMission: Mission = {
  id: "test_mission",
  title: "Test Mission",
  fixer: "test_fixer",
  arc: 1,
  zone: "test_zone",
  grade_min: 1,
  grade_max: 3,
  rewards: { credits: 100, materials: {} },
  grade: 2,
  seed: 42,
};

const mockIce: Ice = {
  id: "test_ice",
  name: "Test ICE",
  hp: 50,
  armor: 5,
  tier: 2,
};

const mockPrograms: ReadonlyArray<Program> = [
  { id: "p1", name: "Program 1", tier: 1, cost: 10, effect: "damage", description: "Test", aoe: false },
  { id: "p2", name: "Program 2", tier: 2, cost: 15, effect: "shield", description: "Test", aoe: false },
];

function baseState(): GameState {
  return makeInitialState(mockMission, mockIce, mockPrograms);
}

describe("Death Cycle (ADR-0040)", () => {
  describe("selectEpitaph", () => {
    it("returns a novice epitaph for novice character", () => {
      const epitaph = selectEpitaph("novice");
      expect(EPITAPHS.novice).toContain(epitaph);
    });

    it("returns a veteran epitaph for veteran character", () => {
      const epitaph = selectEpitaph("veteran");
      expect(EPITAPHS.veteran).toContain(epitaph);
    });

    it("returns a heretic epitaph for heretic character", () => {
      const epitaph = selectEpitaph("heretic");
      expect(EPITAPHS.heretic).toContain(epitaph);
    });

    it("falls back to novice epitaph for unknown character", () => {
      const epitaph = selectEpitaph("unknown_character");
      expect(EPITAPHS.novice).toContain(epitaph);
    });

    it("uses provided RNG for deterministic selection", () => {
      const seededRng = () => 0.0;
      const epitaph1 = selectEpitaph("novice", seededRng);
      const epitaph2 = selectEpitaph("novice", seededRng);
      expect(epitaph1).toBe(epitaph2);
      expect(epitaph1).toBe(EPITAPHS.novice[0]);
    });

    it("selects last epitaph with rng close to 1.0", () => {
      const seededRng = () => 0.99;
      const epitaph = selectEpitaph("novice", seededRng);
      expect(epitaph).toBe(EPITAPHS.novice[EPITAPHS.novice.length - 1]);
    });
  });

  describe("createDeceasedJockey", () => {
    it("creates a deceased jockey with all required fields", () => {
      const jockey = createDeceasedJockey({
        name: "Test Jockey",
        characterId: "veteran",
        grade: 3,
        missionId: "mission_01",
        inventory: ["prog1", "prog2", "prog3"],
        missionsCompleted: 5,
        dataRecovered: 1000,
        playtimeMinutes: 42,
      });

      expect(jockey.name).toBe("Test Jockey");
      expect(jockey.characterId).toBe("veteran");
      expect(jockey.grade).toBe(3);
      expect(jockey.diedAtMission).toBe("mission_01");
      expect(jockey.inventorySnapshot).toEqual(["prog1", "prog2", "prog3"]);
      expect(jockey.missionsCompleted).toBe(5);
      expect(jockey.dataRecovered).toBe(1000);
      expect(jockey.playtimeMinutes).toBe(42);
      expect(EPITAPHS.veteran).toContain(jockey.epitaph);
    });

    it("generates unique jockey IDs", async () => {
      const jockey1 = createDeceasedJockey({
        name: "J1",
        characterId: "novice",
        grade: 1,
        missionId: "m1",
        inventory: [],
        missionsCompleted: 0,
        dataRecovered: 0,
        playtimeMinutes: 1,
      });

      await new Promise(resolve => setTimeout(resolve, 5));

      const jockey2 = createDeceasedJockey({
        name: "J2",
        characterId: "novice",
        grade: 1,
        missionId: "m1",
        inventory: [],
        missionsCompleted: 0,
        dataRecovered: 0,
        playtimeMinutes: 1,
      });

      expect(jockey1.jockeyId).not.toBe(jockey2.jockeyId);
    });

    it("includes timestamp in milliseconds", () => {
      const before = Date.now();
      const jockey = createDeceasedJockey({
        name: "J",
        characterId: "novice",
        grade: 1,
        missionId: "m",
        inventory: [],
        missionsCompleted: 0,
        dataRecovered: 0,
        playtimeMinutes: 1,
      });
      const after = Date.now();

      expect(jockey.diedAtTimestamp).toBeGreaterThanOrEqual(before);
      expect(jockey.diedAtTimestamp).toBeLessThanOrEqual(after);
    });

    it("uses seeded RNG for deterministic epitaph", () => {
      const seededRng = () => 0.5;
      const jockey = createDeceasedJockey({
        name: "J",
        characterId: "heretic",
        grade: 2,
        missionId: "m",
        inventory: [],
        missionsCompleted: 0,
        dataRecovered: 0,
        playtimeMinutes: 5,
        rng: seededRng,
      });

      const expectedIndex = Math.floor(0.5 * EPITAPHS.heretic.length);
      expect(jockey.epitaph).toBe(EPITAPHS.heretic[expectedIndex]);
    });

    it("freezes inventory snapshot", () => {
      const jockey = createDeceasedJockey({
        name: "J",
        characterId: "novice",
        grade: 1,
        missionId: "m",
        inventory: ["a", "b"],
        missionsCompleted: 0,
        dataRecovered: 0,
        playtimeMinutes: 1,
      });

      expect(Object.isFrozen(jockey.inventorySnapshot)).toBe(true);
    });
  });

  describe("generateDeathSummary", () => {
    it("creates a death summary with all fields", () => {
      const jockey = createDeceasedJockey({
        name: "Test Jockey",
        characterId: "veteran",
        grade: 4,
        missionId: "mission_99",
        inventory: ["p1", "p2"],
        missionsCompleted: 10,
        dataRecovered: 5000,
        playtimeMinutes: 120,
      });

      const summary = generateDeathSummary(jockey, 15, 3, 150);

      expect(summary.jockey).toBe(jockey);
      expect(summary.totalRuns).toBe(15);
      expect(summary.totalDeaths).toBe(3);
      expect(summary.longestRunMinutes).toBe(150);
    });

    it("handles zero stats", () => {
      const jockey = createDeceasedJockey({
        name: "J",
        characterId: "novice",
        grade: 1,
        missionId: "m",
        inventory: [],
        missionsCompleted: 0,
        dataRecovered: 0,
        playtimeMinutes: 0,
      });

      const summary = generateDeathSummary(jockey, 0, 0, 0);

      expect(summary.totalRuns).toBe(0);
      expect(summary.totalDeaths).toBe(0);
      expect(summary.longestRunMinutes).toBe(0);
    });
  });

  describe("Death state transitions", () => {
    it("transitions to dead phase when HP reaches 0", () => {
      const state = baseState();
      const deadState = {
        ...state,
        runPhase: "dead" as const,
        player: { ...state.player, hp: 0 },
      };

      const afterDeath = applyAction(deadState, { type: "trigger_death" });

      expect(afterDeath.runPhase).toBe("dead");
      expect(afterDeath.phase).toBe("defeat");
      expect(afterDeath.lastDeathSummary).not.toBeNull();
      expect(afterDeath.totalDeaths).toBe(state.totalDeaths + 1);
      expect(afterDeath.deceasedJockeys.length).toBe(state.deceasedJockeys.length + 1);
    });

    it("creates deceased jockey record on death", () => {
      const state = {
        ...baseState(),
        runPhase: "dead" as const,
        player: { ...baseState().player, hp: 0 },
        turnCount: 20,
      };

      const afterDeath = applyAction(state, { type: "trigger_death" });
      const deceased = afterDeath.deceasedJockeys[0];

      expect(deceased).toBeDefined();
      expect(deceased?.name).toBe(state.mission.title);
      expect(deceased?.characterId).toBe("novice");
      expect(deceased?.grade).toBe(state.mission.grade);
      expect(deceased?.diedAtMission).toBe(state.mission.id);
    });
  });

  describe("Restart choices", () => {
    function makeDeadState(): GameState {
      const base = baseState();
      return {
        ...base,
        runPhase: "dead",
        phase: "defeat",
        player: { ...base.player, hp: 0 },
        totalDeaths: 1,
      };
    }

    it("new_jockey returns to menu", () => {
      const deadState = makeDeadState();
      const afterRestart = applyAction(deadState, {
        type: "select_restart",
        choice: "new_jockey",
      });

      expect(afterRestart.phase).toBe("menu");
      expect(afterRestart.runPhase).toBe("matrix");
      expect(afterRestart.message).toContain("new jockey");
    });

    it("same_jockey restores HP and returns to menu", () => {
      const deadState = makeDeadState();
      const afterRestart = applyAction(deadState, {
        type: "select_restart",
        choice: "same_jockey",
      });

      expect(afterRestart.phase).toBe("menu");
      expect(afterRestart.runPhase).toBe("matrix");
      expect(afterRestart.player.hp).toBe(afterRestart.player.maxHp);
      expect(afterRestart.player.alarm).toBe(0);
      expect(afterRestart.message).toContain("Finn");
    });

    it("hall_of_dead transitions to menu with hall message", () => {
      const deadState = makeDeadState();
      const afterRestart = applyAction(deadState, {
        type: "select_restart",
        choice: "hall_of_dead",
      });

      expect(afterRestart.phase).toBe("menu");
      expect(afterRestart.message).toContain("Hall of Dead");
    });

    it("main_menu returns to menu", () => {
      const deadState = makeDeadState();
      const afterRestart = applyAction(deadState, {
        type: "select_restart",
        choice: "main_menu",
      });

      expect(afterRestart.phase).toBe("menu");
      expect(afterRestart.runPhase).toBe("matrix");
    });

    it("view_hall_of_dead action transitions to menu with hall message", () => {
      const deadState = makeDeadState();
      const afterView = applyAction(deadState, { type: "view_hall_of_dead" });

      expect(afterView.phase).toBe("menu");
      expect(afterView.message).toContain("Hall of Dead");
    });
  });

  describe("Multiple deaths accumulation", () => {
    it("accumulates deceased jockeys across multiple deaths", () => {
      let state = baseState();

      state = { ...state, runPhase: "dead", player: { ...state.player, hp: 0 } };
      state = applyAction(state, { type: "trigger_death" });
      expect(state.deceasedJockeys.length).toBe(1);
      expect(state.totalDeaths).toBe(1);

      state = { ...state, runPhase: "dead", player: { ...state.player, hp: 0 } };
      state = applyAction(state, { type: "trigger_death" });
      expect(state.deceasedJockeys.length).toBe(2);
      expect(state.totalDeaths).toBe(2);

      state = { ...state, runPhase: "dead", player: { ...state.player, hp: 0 } };
      state = applyAction(state, { type: "trigger_death" });
      expect(state.deceasedJockeys.length).toBe(3);
      expect(state.totalDeaths).toBe(3);
    });

    it("preserves deceased jockey records", () => {
      const state1 = {
        ...baseState(),
        runPhase: "dead" as const,
        player: { ...baseState().player, hp: 0 },
        mission: { ...mockMission, id: "mission_1", title: "First Mission" },
      };
      const afterDeath1 = applyAction(state1, { type: "trigger_death" });
      const firstJockey = afterDeath1.deceasedJockeys[0];

      const state2 = {
        ...afterDeath1,
        runPhase: "dead" as const,
        player: { ...afterDeath1.player, hp: 0 },
        mission: { ...mockMission, id: "mission_2", title: "Second Mission" },
      };
      const afterDeath2 = applyAction(state2, { type: "trigger_death" });

      expect(afterDeath2.deceasedJockeys.length).toBe(2);
      expect(afterDeath2.deceasedJockeys[0]).toEqual(firstJockey);
      expect(afterDeath2.deceasedJockeys[1]?.diedAtMission).toBe("mission_2");
    });
  });

  describe("Longest run tracking", () => {
    it("tracks longest run across deaths", () => {
      let state = baseState();
      state = {
        ...state,
        runPhase: "dead" as const,
        player: { ...state.player, hp: 0 },
        turnCount: 10,
        longestRunMinutes: 0,
      };

      state = applyAction(state, { type: "trigger_death" });
      const firstRunMinutes = Math.floor(10 * 0.5);
      expect(state.lastDeathSummary?.longestRunMinutes).toBe(firstRunMinutes);

      state = {
        ...state,
        runPhase: "dead" as const,
        player: { ...state.player, hp: 0 },
        turnCount: 100,
      };
      state = applyAction(state, { type: "trigger_death" });
      const secondRunMinutes = Math.floor(100 * 0.5);
      expect(state.lastDeathSummary?.longestRunMinutes).toBe(secondRunMinutes);
    });

    it("preserves longest run when current run is shorter", () => {
      let state = baseState();
      state = {
        ...state,
        runPhase: "dead" as const,
        player: { ...state.player, hp: 0 },
        turnCount: 100,
        longestRunMinutes: 50,
      };

      state = applyAction(state, { type: "trigger_death" });

      state = {
        ...state,
        runPhase: "dead" as const,
        player: { ...state.player, hp: 0 },
        turnCount: 10,
      };
      state = applyAction(state, { type: "trigger_death" });

      expect(state.lastDeathSummary?.longestRunMinutes).toBe(50);
    });
  });

  describe("Edge cases", () => {
    it("handles death with empty inventory", () => {
      const state = {
        ...baseState(),
        runPhase: "dead" as const,
        player: { ...baseState().player, hp: 0 },
        inventory: { credits: 0, materials: {}, programs: [] },
      };

      const afterDeath = applyAction(state, { type: "trigger_death" });
      const deceased = afterDeath.deceasedJockeys[0];

      expect(deceased?.inventorySnapshot).toEqual([]);
    });

    it("handles death at turn 0", () => {
      const state = {
        ...baseState(),
        runPhase: "dead" as const,
        player: { ...baseState().player, hp: 0 },
        turnCount: 0,
      };

      const afterDeath = applyAction(state, { type: "trigger_death" });
      const deceased = afterDeath.deceasedJockeys[0];

      expect(deceased?.playtimeMinutes).toBe(0);
    });

    it("no-op when applying non-death actions in dead phase", () => {
      const state = {
        ...baseState(),
        runPhase: "dead" as const,
        phase: "defeat" as const,
      };

      const afterAction = applyAction(state, { type: "confirm" });
      expect(afterAction.runPhase).toBe("dead");
    });
  });
});
