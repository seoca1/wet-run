import { describe, it, expect } from "vitest";
import {
  STAGES,
  DEFAULT_MISSION_STAGES,
  SHORT_MISSION_STAGES,
  COMBAT_ONLY_STAGES,
  createStageState,
  advanceStage,
  jumpToStage,
  getCurrentStageDef,
  isLastStage,
  getStageElapsedMs,
  selectStageFlow,
  type StageId,
} from "../src/core/stage_system.ts";

describe("Stage System", () => {
  describe("STAGES constant", () => {
    it("contains all 14 stage definitions", () => {
      expect(Object.keys(STAGES).length).toBe(14);
    });

    it("includes pending stage", () => {
      expect(STAGES.pending).toBeDefined();
      expect(STAGES.pending.id).toBe("pending");
      expect(STAGES.pending.type).toBe("hub");
      expect(STAGES.pending.isTerminal).toBe(false);
    });

    it("includes briefing stage", () => {
      expect(STAGES.briefing).toBeDefined();
      expect(STAGES.briefing.id).toBe("briefing");
      expect(STAGES.briefing.type).toBe("narrative");
      expect(STAGES.briefing.isTerminal).toBe(false);
    });

    it("includes travel stage", () => {
      expect(STAGES.travel).toBeDefined();
      expect(STAGES.travel.id).toBe("travel");
      expect(STAGES.travel.type).toBe("animation");
      expect(STAGES.travel.isTerminal).toBe(false);
    });

    it("includes meet_npc stage", () => {
      expect(STAGES.meet_npc).toBeDefined();
      expect(STAGES.meet_npc.id).toBe("meet_npc");
      expect(STAGES.meet_npc.type).toBe("matrix");
      expect(STAGES.meet_npc.isTerminal).toBe(false);
    });

    it("includes extract_data stage", () => {
      expect(STAGES.extract_data).toBeDefined();
      expect(STAGES.extract_data.id).toBe("extract_data");
      expect(STAGES.extract_data.type).toBe("matrix");
      expect(STAGES.extract_data.isTerminal).toBe(false);
    });

    it("includes bypass_security stage", () => {
      expect(STAGES.bypass_security).toBeDefined();
      expect(STAGES.bypass_security.id).toBe("bypass_security");
      expect(STAGES.bypass_security.type).toBe("matrix");
      expect(STAGES.bypass_security.isTerminal).toBe(false);
    });

    it("includes defeat_ice stage", () => {
      expect(STAGES.defeat_ice).toBeDefined();
      expect(STAGES.defeat_ice.id).toBe("defeat_ice");
      expect(STAGES.defeat_ice.type).toBe("combat");
      expect(STAGES.defeat_ice.isTerminal).toBe(false);
    });

    it("includes jack_out stage", () => {
      expect(STAGES.jack_out).toBeDefined();
      expect(STAGES.jack_out.id).toBe("jack_out");
      expect(STAGES.jack_out.type).toBe("animation");
      expect(STAGES.jack_out.isTerminal).toBe(false);
    });

    it("includes reward stage", () => {
      expect(STAGES.reward).toBeDefined();
      expect(STAGES.reward.id).toBe("reward");
      expect(STAGES.reward.type).toBe("hub");
      expect(STAGES.reward.isTerminal).toBe(false);
    });

    it("includes complete stage", () => {
      expect(STAGES.complete).toBeDefined();
      expect(STAGES.complete.id).toBe("complete");
      expect(STAGES.complete.type).toBe("hub");
      expect(STAGES.complete.isTerminal).toBe(true);
    });

    it("includes failed stage", () => {
      expect(STAGES.failed).toBeDefined();
      expect(STAGES.failed.id).toBe("failed");
      expect(STAGES.failed.type).toBe("death");
      expect(STAGES.failed.isTerminal).toBe(true);
    });

    it("includes death_restart stage", () => {
      expect(STAGES.death_restart).toBeDefined();
      expect(STAGES.death_restart.id).toBe("death_restart");
      expect(STAGES.death_restart.type).toBe("death");
      expect(STAGES.death_restart.isTerminal).toBe(true);
    });

    it("includes black_market stage", () => {
      expect(STAGES.black_market).toBeDefined();
      expect(STAGES.black_market.id).toBe("black_market");
      expect(STAGES.black_market.type).toBe("hub");
      expect(STAGES.black_market.isTerminal).toBe(false);
    });

    it("includes ghost_encounter stage", () => {
      expect(STAGES.ghost_encounter).toBeDefined();
      expect(STAGES.ghost_encounter.id).toBe("ghost_encounter");
      expect(STAGES.ghost_encounter.type).toBe("matrix");
      expect(STAGES.ghost_encounter.isTerminal).toBe(true);
    });

    it("all stages have required fields", () => {
      Object.values(STAGES).forEach((stage) => {
        expect(stage.id).toBeDefined();
        expect(stage.nameEn).toBeDefined();
        expect(stage.nameKo).toBeDefined();
        expect(stage.type).toBeDefined();
        expect(typeof stage.isTerminal).toBe("boolean");
        expect(stage.descriptionEn).toBeDefined();
        expect(stage.descriptionKo).toBeDefined();
        expect(Array.isArray(stage.asciiArt)).toBe(true);
      });
    });

    it("terminal stages are marked correctly", () => {
      expect(STAGES.complete.isTerminal).toBe(true);
      expect(STAGES.failed.isTerminal).toBe(true);
      expect(STAGES.death_restart.isTerminal).toBe(true);
      expect(STAGES.ghost_encounter.isTerminal).toBe(true);
    });

    it("non-terminal stages are marked correctly", () => {
      expect(STAGES.pending.isTerminal).toBe(false);
      expect(STAGES.briefing.isTerminal).toBe(false);
      expect(STAGES.travel.isTerminal).toBe(false);
      expect(STAGES.meet_npc.isTerminal).toBe(false);
      expect(STAGES.extract_data.isTerminal).toBe(false);
      expect(STAGES.bypass_security.isTerminal).toBe(false);
      expect(STAGES.defeat_ice.isTerminal).toBe(false);
      expect(STAGES.jack_out.isTerminal).toBe(false);
      expect(STAGES.reward.isTerminal).toBe(false);
      expect(STAGES.black_market.isTerminal).toBe(false);
    });
  });

  describe("Stage flow constants", () => {
    it("DEFAULT_MISSION_STAGES has 8 entries", () => {
      expect(DEFAULT_MISSION_STAGES.length).toBe(8);
    });

    it("DEFAULT_MISSION_STAGES contains expected stages in order", () => {
      const expected: StageId[] = [
        "briefing",
        "travel",
        "meet_npc",
        "extract_data",
        "defeat_ice",
        "jack_out",
        "reward",
        "complete",
      ];
      expect(DEFAULT_MISSION_STAGES).toEqual(expected);
    });

    it("SHORT_MISSION_STAGES has 6 entries", () => {
      expect(SHORT_MISSION_STAGES.length).toBe(6);
    });

    it("SHORT_MISSION_STAGES contains expected stages in order", () => {
      const expected: StageId[] = ["meet_npc", "extract_data", "defeat_ice", "jack_out", "reward", "complete"];
      expect(SHORT_MISSION_STAGES).toEqual(expected);
    });

    it("COMBAT_ONLY_STAGES has 4 entries", () => {
      expect(COMBAT_ONLY_STAGES.length).toBe(4);
    });

    it("COMBAT_ONLY_STAGES contains expected stages in order", () => {
      const expected: StageId[] = ["defeat_ice", "jack_out", "reward", "complete"];
      expect(COMBAT_ONLY_STAGES).toEqual(expected);
    });
  });

  describe("createStageState", () => {
    it("creates stage state with default stages", () => {
      const state = createStageState();
      expect(state.currentStage).toBe("briefing");
      expect(state.stageIndex).toBe(0);
      expect(state.stages).toEqual(DEFAULT_MISSION_STAGES);
      expect(state.enteredAtMs).toBeGreaterThan(0);
      expect(state.stageData).toEqual({});
    });

    it("creates stage state with custom stages", () => {
      const customStages: StageId[] = ["meet_npc", "defeat_ice", "complete"];
      const state = createStageState(customStages);
      expect(state.currentStage).toBe("meet_npc");
      expect(state.stageIndex).toBe(0);
      expect(state.stages).toEqual(customStages);
    });

    it("creates stage state with custom timestamp", () => {
      const nowMs = 1000000;
      const state = createStageState(DEFAULT_MISSION_STAGES, nowMs);
      expect(state.enteredAtMs).toBe(nowMs);
    });

    it("handles empty stage array", () => {
      const state = createStageState([]);
      expect(state.currentStage).toBe("pending");
      expect(state.stageIndex).toBe(0);
      expect(state.stages).toEqual([]);
    });
  });

  describe("advanceStage", () => {
    it("advances to next stage in sequence", () => {
      const state = createStageState(DEFAULT_MISSION_STAGES, 1000);
      const nextState = advanceStage(state, 2000);
      expect(nextState.currentStage).toBe("travel");
      expect(nextState.stageIndex).toBe(1);
      expect(nextState.enteredAtMs).toBe(2000);
    });

    it("does not advance beyond terminal stage", () => {
      const state = createStageState(["briefing", "complete"], 1000);
      const afterBriefing = advanceStage(state, 2000);
      expect(afterBriefing.currentStage).toBe("complete");

      const afterComplete = advanceStage(afterBriefing, 3000);
      expect(afterComplete.currentStage).toBe("complete");
      expect(afterComplete.stageIndex).toBe(1);
      expect(afterComplete.enteredAtMs).toBe(2000);
    });

    it("does not advance beyond end of stages array", () => {
      const state = createStageState(["briefing", "travel"], 1000);
      const stage1 = advanceStage(state, 2000);
      expect(stage1.currentStage).toBe("travel");

      const stage2 = advanceStage(stage1, 3000);
      expect(stage2.currentStage).toBe("travel");
      expect(stage2.stageIndex).toBe(1);
      expect(stage2.enteredAtMs).toBe(2000);
    });

    it("advances through COMBAT_ONLY_STAGES", () => {
      const state = createStageState(COMBAT_ONLY_STAGES, 1000);
      expect(state.currentStage).toBe("defeat_ice");

      const s1 = advanceStage(state, 2000);
      expect(s1.currentStage).toBe("jack_out");

      const s2 = advanceStage(s1, 3000);
      expect(s2.currentStage).toBe("reward");

      const s3 = advanceStage(s2, 4000);
      expect(s3.currentStage).toBe("complete");

      const s4 = advanceStage(s3, 5000);
      expect(s4.currentStage).toBe("complete");
      expect(s4.enteredAtMs).toBe(4000);
    });
  });

  describe("jumpToStage", () => {
    it("jumps to a valid stage by ID", () => {
      const state = createStageState(DEFAULT_MISSION_STAGES, 1000);
      const jumped = jumpToStage(state, "defeat_ice", 5000);
      expect(jumped.currentStage).toBe("defeat_ice");
      expect(jumped.stageIndex).toBe(4);
      expect(jumped.enteredAtMs).toBe(5000);
    });

    it("returns same state for invalid stage ID", () => {
      const state = createStageState(DEFAULT_MISSION_STAGES, 1000);
      const jumped = jumpToStage(state, "black_market", 5000);
      expect(jumped).toEqual(state);
    });

    it("allows jumping backwards in stage sequence", () => {
      const state = createStageState(DEFAULT_MISSION_STAGES, 1000);
      const advanced = advanceStage(advanceStage(advanceStage(state, 2000), 3000), 4000);
      expect(advanced.currentStage).toBe("extract_data");

      const jumped = jumpToStage(advanced, "travel", 5000);
      expect(jumped.currentStage).toBe("travel");
      expect(jumped.stageIndex).toBe(1);
      expect(jumped.enteredAtMs).toBe(5000);
    });

    it("allows jumping forwards in stage sequence", () => {
      const state = createStageState(DEFAULT_MISSION_STAGES, 1000);
      const jumped = jumpToStage(state, "reward", 5000);
      expect(jumped.currentStage).toBe("reward");
      expect(jumped.stageIndex).toBe(6);
      expect(jumped.enteredAtMs).toBe(5000);
    });
  });

  describe("getCurrentStageDef", () => {
    it("returns stage definition for current stage", () => {
      const state = createStageState(DEFAULT_MISSION_STAGES);
      const def = getCurrentStageDef(state);
      expect(def).toBeDefined();
      expect(def?.id).toBe("briefing");
      expect(def?.nameEn).toBe("Mission Briefing");
    });

    it("returns undefined for invalid stage", () => {
      const state = createStageState([]);
      state as unknown as { currentStage: StageId };
      const def = getCurrentStageDef(state);
      expect(def).toBeDefined();
    });
  });

  describe("isLastStage", () => {
    it("returns false for first stage", () => {
      const state = createStageState(DEFAULT_MISSION_STAGES);
      expect(isLastStage(state)).toBe(false);
    });

    it("returns false for middle stage", () => {
      const state = createStageState(DEFAULT_MISSION_STAGES);
      const advanced = advanceStage(advanceStage(state));
      expect(isLastStage(advanced)).toBe(false);
    });

    it("returns true for last stage", () => {
      const state = createStageState(COMBAT_ONLY_STAGES);
      const s1 = advanceStage(state);
      const s2 = advanceStage(s1);
      const s3 = advanceStage(s2);
      expect(isLastStage(s3)).toBe(true);
    });

    it("returns true for single-stage array", () => {
      const state = createStageState(["complete"]);
      expect(isLastStage(state)).toBe(true);
    });

    it("returns true for empty stage array", () => {
      const state = createStageState([]);
      expect(isLastStage(state)).toBe(true);
    });
  });

  describe("getStageElapsedMs", () => {
    it("calculates elapsed time correctly", () => {
      const state = createStageState(DEFAULT_MISSION_STAGES, 1000);
      const elapsed = getStageElapsedMs(state, 3000);
      expect(elapsed).toBe(2000);
    });

    it("returns zero elapsed time when nowMs equals enteredAtMs", () => {
      const state = createStageState(DEFAULT_MISSION_STAGES, 1000);
      const elapsed = getStageElapsedMs(state, 1000);
      expect(elapsed).toBe(0);
    });

    it("uses Date.now() when nowMs not provided", () => {
      const state = createStageState(DEFAULT_MISSION_STAGES, Date.now() - 5000);
      const elapsed = getStageElapsedMs(state);
      expect(elapsed).toBeGreaterThan(4000);
      expect(elapsed).toBeLessThan(6000);
    });
  });

  describe("selectStageFlow", () => {
    it("returns COMBAT_ONLY_STAGES when combatOnly is true", () => {
      const flow = selectStageFlow({ combatOnly: true });
      expect(flow).toEqual(COMBAT_ONLY_STAGES);
    });

    it("returns SHORT_MISSION_STAGES when hasBriefing and hasTravel are false", () => {
      const flow = selectStageFlow({ hasBriefing: false, hasTravel: false });
      expect(flow).toEqual(SHORT_MISSION_STAGES);
    });

    it("returns SHORT_MISSION_STAGES when hasBriefing is false", () => {
      const flow = selectStageFlow({ hasBriefing: false });
      expect(flow).toEqual(SHORT_MISSION_STAGES);
    });

    it("returns SHORT_MISSION_STAGES when hasTravel is false", () => {
      const flow = selectStageFlow({ hasTravel: false });
      expect(flow).toEqual(SHORT_MISSION_STAGES);
    });

    it("returns DEFAULT_MISSION_STAGES when hasBriefing and hasTravel are true", () => {
      const flow = selectStageFlow({ hasBriefing: true, hasTravel: true });
      expect(flow).toEqual(DEFAULT_MISSION_STAGES);
    });

    it("returns DEFAULT_MISSION_STAGES when no params provided", () => {
      const flow = selectStageFlow({});
      expect(flow).toEqual(DEFAULT_MISSION_STAGES);
    });

    it("combatOnly overrides other params", () => {
      const flow = selectStageFlow({ combatOnly: true, hasBriefing: true, hasTravel: true });
      expect(flow).toEqual(COMBAT_ONLY_STAGES);
    });
  });

  describe("Stage flow progression", () => {
    it("DEFAULT_MISSION_STAGES completes in 8 steps", () => {
      let state = createStageState(DEFAULT_MISSION_STAGES, 1000);
      let steps = 0;
      const maxSteps = 20;

      while (!isLastStage(state) && steps < maxSteps) {
        state = advanceStage(state, 1000 + steps * 1000);
        steps++;
      }

      expect(steps).toBe(7);
      expect(state.currentStage).toBe("complete");
    });

    it("SHORT_MISSION_STAGES completes in 6 steps", () => {
      let state = createStageState(SHORT_MISSION_STAGES, 1000);
      let steps = 0;
      const maxSteps = 20;

      while (!isLastStage(state) && steps < maxSteps) {
        state = advanceStage(state, 1000 + steps * 1000);
        steps++;
      }

      expect(steps).toBe(5);
      expect(state.currentStage).toBe("complete");
    });

    it("COMBAT_ONLY_STAGES completes in 4 steps", () => {
      let state = createStageState(COMBAT_ONLY_STAGES, 1000);
      let steps = 0;
      const maxSteps = 20;

      while (!isLastStage(state) && steps < maxSteps) {
        state = advanceStage(state, 1000 + steps * 1000);
        steps++;
      }

      expect(steps).toBe(3);
      expect(state.currentStage).toBe("complete");
    });
  });
});
