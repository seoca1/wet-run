import { describe, it, expect } from "vitest";
import {
  DEFAULT_FACTION_SCORES,
  scoreToTier,
  getMultiplier,
  applyScoreChange,
  onMissionComplete,
  onIceKill,
  getFactionSummary,
  TIER_THRESHOLDS,
  TIER_MULTIPLIERS,
  MISSION_REWARD_MAP,
  KILL_PENALTY_MAP,
} from "../src/core/faction_reputation.ts";

describe("Faction Reputation System", () => {
  describe("DEFAULT_FACTION_SCORES", () => {
    it("all factions start at 0", () => {
      expect(DEFAULT_FACTION_SCORES.hosaka).toBe(0);
      expect(DEFAULT_FACTION_SCORES.maas).toBe(0);
      expect(DEFAULT_FACTION_SCORES.sense_net).toBe(0);
      expect(DEFAULT_FACTION_SCORES.ta).toBe(0);
    });
  });

  describe("scoreToTier", () => {
    it("returns ALLIED for score 80+", () => {
      expect(scoreToTier(80)).toBe("ALLIED");
      expect(scoreToTier(90)).toBe("ALLIED");
      expect(scoreToTier(100)).toBe("ALLIED");
    });

    it("returns FRIENDLY for score 50-79", () => {
      expect(scoreToTier(50)).toBe("FRIENDLY");
      expect(scoreToTier(65)).toBe("FRIENDLY");
      expect(scoreToTier(79)).toBe("FRIENDLY");
    });

    it("returns TRUSTED for score 20-49", () => {
      expect(scoreToTier(20)).toBe("TRUSTED");
      expect(scoreToTier(35)).toBe("TRUSTED");
      expect(scoreToTier(49)).toBe("TRUSTED");
    });

    it("returns NEUTRAL for score -19 to 19", () => {
      expect(scoreToTier(-19)).toBe("NEUTRAL");
      expect(scoreToTier(0)).toBe("NEUTRAL");
      expect(scoreToTier(19)).toBe("NEUTRAL");
    });

    it("returns HOSTILE for score -49 to -20", () => {
      expect(scoreToTier(-20)).toBe("HOSTILE");
      expect(scoreToTier(-35)).toBe("HOSTILE");
      expect(scoreToTier(-49)).toBe("HOSTILE");
    });

    it("returns ENEMY for score -79 to -50", () => {
      expect(scoreToTier(-50)).toBe("ENEMY");
      expect(scoreToTier(-65)).toBe("ENEMY");
      expect(scoreToTier(-79)).toBe("ENEMY");
    });

    it("returns OUTCAST for score -100 to -80", () => {
      expect(scoreToTier(-80)).toBe("OUTCAST");
      expect(scoreToTier(-90)).toBe("OUTCAST");
      expect(scoreToTier(-100)).toBe("OUTCAST");
    });

    it("clamps scores above 100", () => {
      expect(scoreToTier(150)).toBe("ALLIED");
      expect(scoreToTier(200)).toBe("ALLIED");
    });

    it("clamps scores below -100", () => {
      expect(scoreToTier(-150)).toBe("OUTCAST");
      expect(scoreToTier(-200)).toBe("OUTCAST");
    });
  });

  describe("getMultiplier", () => {
    it("returns 0.5 for ALLIED", () => {
      expect(getMultiplier(90)).toBe(0.5);
    });

    it("returns 0.65 for FRIENDLY", () => {
      expect(getMultiplier(60)).toBe(0.65);
    });

    it("returns 0.85 for TRUSTED", () => {
      expect(getMultiplier(30)).toBe(0.85);
    });

    it("returns 1.0 for NEUTRAL", () => {
      expect(getMultiplier(0)).toBe(1.0);
    });

    it("returns 1.15 for HOSTILE", () => {
      expect(getMultiplier(-30)).toBe(1.15);
    });

    it("returns 1.35 for ENEMY", () => {
      expect(getMultiplier(-60)).toBe(1.35);
    });

    it("returns 1.5 for OUTCAST", () => {
      expect(getMultiplier(-90)).toBe(1.5);
    });
  });

  describe("applyScoreChange", () => {
    it("increases score for positive change", () => {
      const result = applyScoreChange(DEFAULT_FACTION_SCORES, "hosaka", 10);
      expect(result.hosaka).toBe(10);
      expect(result.maas).toBe(0);
    });

    it("decreases score for negative change", () => {
      const result = applyScoreChange(DEFAULT_FACTION_SCORES, "maas", -5);
      expect(result.maas).toBe(-5);
      expect(result.hosaka).toBe(0);
    });

    it("clamps at 100", () => {
      const scores = { ...DEFAULT_FACTION_SCORES, hosaka: 95 };
      const result = applyScoreChange(scores, "hosaka", 20);
      expect(result.hosaka).toBe(100);
    });

    it("clamps at -100", () => {
      const scores = { ...DEFAULT_FACTION_SCORES, sense_net: -95 };
      const result = applyScoreChange(scores, "sense_net", -20);
      expect(result.sense_net).toBe(-100);
    });

    it("multiple changes accumulate", () => {
      let scores = applyScoreChange(DEFAULT_FACTION_SCORES, "ta", 10);
      scores = applyScoreChange(scores, "ta", 10);
      scores = applyScoreChange(scores, "ta", 10);
      expect(scores.ta).toBe(30);
    });

    it("does not mutate original scores", () => {
      const original = { ...DEFAULT_FACTION_SCORES };
      applyScoreChange(original, "hosaka", 10);
      expect(original.hosaka).toBe(0);
    });
  });

  describe("onMissionComplete", () => {
    it("awards +10 reputation for hosaka mission", () => {
      const result = onMissionComplete(DEFAULT_FACTION_SCORES, "hosaka");
      expect(result.hosaka).toBe(10);
    });

    it("awards +10 reputation for maas mission", () => {
      const result = onMissionComplete(DEFAULT_FACTION_SCORES, "maas");
      expect(result.maas).toBe(10);
    });

    it("awards +10 reputation for sense_net mission", () => {
      const result = onMissionComplete(DEFAULT_FACTION_SCORES, "sense_net");
      expect(result.sense_net).toBe(10);
    });

    it("awards +10 reputation for ta mission", () => {
      const result = onMissionComplete(DEFAULT_FACTION_SCORES, "ta");
      expect(result.ta).toBe(10);
    });

    it("stacks multiple mission completions", () => {
      let scores = onMissionComplete(DEFAULT_FACTION_SCORES, "hosaka");
      scores = onMissionComplete(scores, "hosaka");
      scores = onMissionComplete(scores, "hosaka");
      expect(scores.hosaka).toBe(30);
    });
  });

  describe("onIceKill", () => {
    it("penalizes -5 reputation for hosaka ICE kill", () => {
      const result = onIceKill(DEFAULT_FACTION_SCORES, "hosaka");
      expect(result.hosaka).toBe(-5);
    });

    it("penalizes -5 reputation for maas ICE kill", () => {
      const result = onIceKill(DEFAULT_FACTION_SCORES, "maas");
      expect(result.maas).toBe(-5);
    });

    it("penalizes -5 reputation for sense_net ICE kill", () => {
      const result = onIceKill(DEFAULT_FACTION_SCORES, "sense_net");
      expect(result.sense_net).toBe(-5);
    });

    it("penalizes -5 reputation for ta ICE kill", () => {
      const result = onIceKill(DEFAULT_FACTION_SCORES, "ta");
      expect(result.ta).toBe(-5);
    });

    it("stacks multiple ICE kills", () => {
      let scores = onIceKill(DEFAULT_FACTION_SCORES, "maas");
      scores = onIceKill(scores, "maas");
      scores = onIceKill(scores, "maas");
      expect(scores.maas).toBe(-15);
    });
  });

  describe("getFactionSummary", () => {
    it("returns summary for all 4 factions", () => {
      const summary = getFactionSummary(DEFAULT_FACTION_SCORES);
      expect(summary).toHaveLength(4);
    });

    it("includes faction, score, tier, and multiplier", () => {
      const scores = { ...DEFAULT_FACTION_SCORES, hosaka: 60 };
      const summary = getFactionSummary(scores);
      const hosaka = summary.find(s => s.faction === "hosaka");
      expect(hosaka).toBeDefined();
      expect(hosaka?.score).toBe(60);
      expect(hosaka?.tier).toBe("FRIENDLY");
      expect(hosaka?.multiplier).toBe(0.65);
    });

    it("correctly calculates for all factions with different scores", () => {
      const scores = {
        hosaka: 85,
        maas: 25,
        sense_net: -30,
        ta: -85,
      };
      const summary = getFactionSummary(scores);
      expect(summary.find(s => s.faction === "hosaka")?.tier).toBe("ALLIED");
      expect(summary.find(s => s.faction === "maas")?.tier).toBe("TRUSTED");
      expect(summary.find(s => s.faction === "sense_net")?.tier).toBe("HOSTILE");
      expect(summary.find(s => s.faction === "ta")?.tier).toBe("OUTCAST");
    });
  });

  describe("TIER_THRESHOLDS", () => {
    it("is frozen", () => {
      expect(Object.isFrozen(TIER_THRESHOLDS)).toBe(true);
    });

    it("has correct thresholds", () => {
      expect(TIER_THRESHOLDS).toEqual([
        { tier: "ALLIED", min: 80 },
        { tier: "FRIENDLY", min: 50 },
        { tier: "TRUSTED", min: 20 },
        { tier: "NEUTRAL", min: -19 },
        { tier: "HOSTILE", min: -49 },
        { tier: "ENEMY", min: -79 },
        { tier: "OUTCAST", min: -100 },
      ]);
    });
  });

  describe("TIER_MULTIPLIERS", () => {
    it("is frozen", () => {
      expect(Object.isFrozen(TIER_MULTIPLIERS)).toBe(true);
    });

    it("has correct multipliers", () => {
      expect(TIER_MULTIPLIERS.ALLIED).toBe(0.5);
      expect(TIER_MULTIPLIERS.FRIENDLY).toBe(0.65);
      expect(TIER_MULTIPLIERS.TRUSTED).toBe(0.85);
      expect(TIER_MULTIPLIERS.NEUTRAL).toBe(1.0);
      expect(TIER_MULTIPLIERS.HOSTILE).toBe(1.15);
      expect(TIER_MULTIPLIERS.ENEMY).toBe(1.35);
      expect(TIER_MULTIPLIERS.OUTCAST).toBe(1.5);
    });
  });

  describe("Mission and Kill reward maps", () => {
    it("MISSION_REWARD_MAP is frozen and consistent", () => {
      expect(Object.isFrozen(MISSION_REWARD_MAP)).toBe(true);
      expect(MISSION_REWARD_MAP.hosaka).toBe(10);
      expect(MISSION_REWARD_MAP.maas).toBe(10);
      expect(MISSION_REWARD_MAP.sense_net).toBe(10);
      expect(MISSION_REWARD_MAP.ta).toBe(10);
    });

    it("KILL_PENALTY_MAP is frozen and consistent", () => {
      expect(Object.isFrozen(KILL_PENALTY_MAP)).toBe(true);
      expect(KILL_PENALTY_MAP.hosaka).toBe(-5);
      expect(KILL_PENALTY_MAP.maas).toBe(-5);
      expect(KILL_PENALTY_MAP.sense_net).toBe(-5);
      expect(KILL_PENALTY_MAP.ta).toBe(-5);
    });
  });

  describe("Edge cases and interactions", () => {
    it("completing missions and killing ICE balance each other", () => {
      let scores = DEFAULT_FACTION_SCORES;
      scores = onMissionComplete(scores, "hosaka");
      scores = onIceKill(scores, "hosaka");
      scores = onIceKill(scores, "hosaka");
      expect(scores.hosaka).toBe(0);
    });

    it("multiple factions can have different reputations", () => {
      let scores = DEFAULT_FACTION_SCORES;
      scores = onMissionComplete(scores, "hosaka");
      scores = onMissionComplete(scores, "hosaka");
      scores = onIceKill(scores, "maas");
      scores = onIceKill(scores, "maas");
      scores = onIceKill(scores, "maas");
      expect(scores.hosaka).toBe(20);
      expect(scores.maas).toBe(-15);
      expect(scores.sense_net).toBe(0);
      expect(scores.ta).toBe(0);
    });

    it("crossing tier boundaries updates multiplier", () => {
      let scores = DEFAULT_FACTION_SCORES;
      expect(getMultiplier(scores.hosaka)).toBe(1.0);
      scores = applyScoreChange(scores, "hosaka", 20);
      expect(getMultiplier(scores.hosaka)).toBe(0.85);
      scores = applyScoreChange(scores, "hosaka", 30);
      expect(getMultiplier(scores.hosaka)).toBe(0.65);
      scores = applyScoreChange(scores, "hosaka", 30);
      expect(getMultiplier(scores.hosaka)).toBe(0.5);
    });

    it("reputation tier at exact boundaries", () => {
      expect(scoreToTier(80)).toBe("ALLIED");
      expect(scoreToTier(50)).toBe("FRIENDLY");
      expect(scoreToTier(20)).toBe("TRUSTED");
      expect(scoreToTier(-20)).toBe("HOSTILE");
      expect(scoreToTier(-50)).toBe("ENEMY");
      expect(scoreToTier(-80)).toBe("OUTCAST");
    });
  });
});
