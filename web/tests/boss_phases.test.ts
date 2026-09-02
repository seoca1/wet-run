/** Unit tests for boss phase transition system. */
import { describe, it, expect } from "vitest";
import {
  createBossTracker,
  checkPhaseTransition,
  getPhaseDamageMultiplier,
  getPhaseLabel,
  getPhaseMechanic,
  getPhaseColor,
  DEFAULT_BOSS_PROFILE,
  type BossPhaseTrackerState,
} from "../src/core/boss_phases.ts";

describe("boss_phases", () => {
  describe("createBossTracker", () => {
    it("creates tracker with profile: phase 1, timestamp 0", () => {
      const tracker = createBossTracker(DEFAULT_BOSS_PROFILE);
      expect(tracker.bossProfile).toBe(DEFAULT_BOSS_PROFILE);
      expect(tracker.currentPhase).toBe(1);
      expect(tracker.phaseChangeMs).toBe(0);
      expect(tracker.phaseChangeColor).toBe("#ffffff");
    });

    it("creates tracker without profile: phase 0", () => {
      const tracker = createBossTracker(null);
      expect(tracker.bossProfile).toBeNull();
      expect(tracker.currentPhase).toBe(0);
      expect(tracker.phaseChangeMs).toBe(0);
    });
  });

  describe("checkPhaseTransition", () => {
    it("no transition when HP above threshold (phase 1 → stays 1)", () => {
      const tracker = createBossTracker(DEFAULT_BOSS_PROFILE);
      const result = checkPhaseTransition(tracker, 80, 100, 5000);
      expect(result.currentPhase).toBe(1);
      expect(result.phaseChangeMs).toBe(0);
    });

    it("transitions to phase 2 when HP ≤ 75%", () => {
      const tracker = createBossTracker(DEFAULT_BOSS_PROFILE);
      const result = checkPhaseTransition(tracker, 74, 100, 5000);
      expect(result.currentPhase).toBe(2);
      expect(result.phaseChangeMs).toBe(5000);
      expect(result.phaseChangeColor).toBe("#ffff00");
    });

    it("skips to highest qualifying phase (phase 1 → 3)", () => {
      const tracker = createBossTracker(DEFAULT_BOSS_PROFILE);
      // HP = 49/100 = 0.49 → phase 3 threshold (0.5)
      const result = checkPhaseTransition(tracker, 49, 100, 8000);
      expect(result.currentPhase).toBe(3);
      expect(result.phaseChangeMs).toBe(8000);
      expect(result.phaseChangeColor).toBe("#ff8800");
    });

    it("transitions to phase 4 when HP ≤ 25%", () => {
      const tracker = createBossTracker(DEFAULT_BOSS_PROFILE);
      const result = checkPhaseTransition(tracker, 24, 100, 12000);
      expect(result.currentPhase).toBe(4);
      expect(result.phaseChangeMs).toBe(12000);
      expect(result.phaseChangeColor).toBe("#ff0000");
    });

    it("no transition when already at max phase (phase 4)", () => {
      const tracker: BossPhaseTrackerState = {
        bossProfile: DEFAULT_BOSS_PROFILE,
        currentPhase: 4,
        phaseChangeMs: 10000,
        phaseChangeColor: "#ff0000",
      };
      const result = checkPhaseTransition(tracker, 10, 100, 15000);
      expect(result.currentPhase).toBe(4);
      expect(result.phaseChangeMs).toBe(10000); // unchanged
    });

    it("no transition when no boss profile", () => {
      const tracker = createBossTracker(null);
      const result = checkPhaseTransition(tracker, 50, 100, 5000);
      expect(result.currentPhase).toBe(0);
    });

    it("handles maxHp = 0 gracefully (no crash)", () => {
      const tracker = createBossTracker(DEFAULT_BOSS_PROFILE);
      const result = checkPhaseTransition(tracker, 0, 0, 5000);
      expect(result).toBe(tracker); // unchanged
    });

    it("phase 2 → 3 transition works", () => {
      const tracker: BossPhaseTrackerState = {
        bossProfile: DEFAULT_BOSS_PROFILE,
        currentPhase: 2,
        phaseChangeMs: 5000,
        phaseChangeColor: "#ffff00",
      };
      const result = checkPhaseTransition(tracker, 50, 100, 10000);
      expect(result.currentPhase).toBe(3);
      expect(result.phaseChangeMs).toBe(10000);
      expect(result.phaseChangeColor).toBe("#ff8800");
    });

    it("exact threshold boundary triggers transition", () => {
      const tracker = createBossTracker(DEFAULT_BOSS_PROFILE);
      // HP = 75/100 = 0.75 exactly → phase 2 threshold
      const result = checkPhaseTransition(tracker, 75, 100, 6000);
      expect(result.currentPhase).toBe(2);
    });
  });

  describe("getPhaseDamageMultiplier", () => {
    it("phase 1 returns 1.0", () => {
      const tracker = createBossTracker(DEFAULT_BOSS_PROFILE);
      const mult = getPhaseDamageMultiplier(tracker);
      expect(mult).toBe(1.0);
    });

    it("phase 2 returns 1.25", () => {
      const tracker: BossPhaseTrackerState = {
        bossProfile: DEFAULT_BOSS_PROFILE,
        currentPhase: 2,
        phaseChangeMs: 5000,
        phaseChangeColor: "#ffff00",
      };
      const mult = getPhaseDamageMultiplier(tracker);
      expect(mult).toBe(1.25);
    });

    it("phase 3 returns 1.5", () => {
      const tracker: BossPhaseTrackerState = {
        bossProfile: DEFAULT_BOSS_PROFILE,
        currentPhase: 3,
        phaseChangeMs: 8000,
        phaseChangeColor: "#ff8800",
      };
      const mult = getPhaseDamageMultiplier(tracker);
      expect(mult).toBe(1.5);
    });

    it("phase 4 returns 2.0", () => {
      const tracker: BossPhaseTrackerState = {
        bossProfile: DEFAULT_BOSS_PROFILE,
        currentPhase: 4,
        phaseChangeMs: 12000,
        phaseChangeColor: "#ff0000",
      };
      const mult = getPhaseDamageMultiplier(tracker);
      expect(mult).toBe(2.0);
    });

    it("no boss profile returns 1.0", () => {
      const tracker = createBossTracker(null);
      const mult = getPhaseDamageMultiplier(tracker);
      expect(mult).toBe(1.0);
    });
  });

  describe("getPhaseLabel", () => {
    it("phase 1 returns 'Standard'", () => {
      const tracker = createBossTracker(DEFAULT_BOSS_PROFILE);
      const label = getPhaseLabel(tracker);
      expect(label).toBe("Standard");
    });

    it("phase 2 returns 'Alert'", () => {
      const tracker: BossPhaseTrackerState = {
        bossProfile: DEFAULT_BOSS_PROFILE,
        currentPhase: 2,
        phaseChangeMs: 5000,
        phaseChangeColor: "#ffff00",
      };
      const label = getPhaseLabel(tracker);
      expect(label).toBe("Alert");
    });

    it("phase 3 returns 'Berserk'", () => {
      const tracker: BossPhaseTrackerState = {
        bossProfile: DEFAULT_BOSS_PROFILE,
        currentPhase: 3,
        phaseChangeMs: 8000,
        phaseChangeColor: "#ff8800",
      };
      const label = getPhaseLabel(tracker);
      expect(label).toBe("Berserk");
    });

    it("phase 4 returns 'Terminal'", () => {
      const tracker: BossPhaseTrackerState = {
        bossProfile: DEFAULT_BOSS_PROFILE,
        currentPhase: 4,
        phaseChangeMs: 12000,
        phaseChangeColor: "#ff0000",
      };
      const label = getPhaseLabel(tracker);
      expect(label).toBe("Terminal");
    });

    it("no boss profile returns empty string", () => {
      const tracker = createBossTracker(null);
      const label = getPhaseLabel(tracker);
      expect(label).toBe("");
    });
  });

  describe("getPhaseMechanic", () => {
    it("phase 1 has no mechanic", () => {
      const tracker = createBossTracker(DEFAULT_BOSS_PROFILE);
      const mechanic = getPhaseMechanic(tracker);
      expect(mechanic).toBeUndefined();
    });

    it("phase 4 returns 'desperation' mechanic", () => {
      const tracker: BossPhaseTrackerState = {
        bossProfile: DEFAULT_BOSS_PROFILE,
        currentPhase: 4,
        phaseChangeMs: 12000,
        phaseChangeColor: "#ff0000",
      };
      const mechanic = getPhaseMechanic(tracker);
      expect(mechanic).toBe("desperation");
    });

    it("no boss profile returns undefined", () => {
      const tracker = createBossTracker(null);
      const mechanic = getPhaseMechanic(tracker);
      expect(mechanic).toBeUndefined();
    });
  });

  describe("getPhaseColor", () => {
    it("phase 1 returns white", () => {
      const tracker = createBossTracker(DEFAULT_BOSS_PROFILE);
      const color = getPhaseColor(tracker);
      expect(color).toBe("#ffffff");
    });

    it("phase 2 returns yellow", () => {
      const tracker: BossPhaseTrackerState = {
        bossProfile: DEFAULT_BOSS_PROFILE,
        currentPhase: 2,
        phaseChangeMs: 5000,
        phaseChangeColor: "#ffff00",
      };
      const color = getPhaseColor(tracker);
      expect(color).toBe("#ffff00");
    });

    it("phase 3 returns orange", () => {
      const tracker: BossPhaseTrackerState = {
        bossProfile: DEFAULT_BOSS_PROFILE,
        currentPhase: 3,
        phaseChangeMs: 8000,
        phaseChangeColor: "#ff8800",
      };
      const color = getPhaseColor(tracker);
      expect(color).toBe("#ff8800");
    });

    it("phase 4 returns red", () => {
      const tracker: BossPhaseTrackerState = {
        bossProfile: DEFAULT_BOSS_PROFILE,
        currentPhase: 4,
        phaseChangeMs: 12000,
        phaseChangeColor: "#ff0000",
      };
      const color = getPhaseColor(tracker);
      expect(color).toBe("#ff0000");
    });

    it("no boss profile returns white", () => {
      const tracker = createBossTracker(null);
      const color = getPhaseColor(tracker);
      expect(color).toBe("#ffffff");
    });
  });
});
