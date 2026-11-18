import { describe, it, expect } from "vitest";
import {
  AGGRESSION_PROBABILITY,
  AGGRESSIVE_CRIT_BONUS,
  STEALTH_ALARM_MULTIPLIER,
  coerceAggression,
  coercePersonality,
  enemyShouldUseSkill,
  chooseSkill,
  selectSkillByPersonality,
  shouldDefensiveAct,
  getAlarmMultiplier,
  getCritBonus,
  shouldTargetAlly,
} from "../src/core/ice_ai.ts";
import { createCombatant } from "../src/core/combat_models.ts";
import type { Combatant, Skill, AggressionTier } from "../src/core/combat_models.ts";

function makeSkill(overrides: Partial<Skill> & Pick<Skill, "id" | "name" | "effect">): Skill {
  return {
    tier: 1,
    apCost: 2,
    damage: 10,
    shield: 0,
    heal: 0,
    dotDamage: 0,
    dotDurationMs: 0,
    buffAmount: 0,
    buffDurationMs: 0,
    stunDurationMs: 0,
    hitCount: 1,
    cooldownMs: 0,
    critBonus: 0,
    role: null,
    aoe: false,
    effectColor: "#ffffff",
    effectGlyph: "*",
    ...overrides,
  };
}

function makeEnemy(overrides: Partial<Combatant> = {}): Combatant {
  return createCombatant({
    id: "enemy-1",
    name: "Test ICE",
    hp: 50,
    maxHp: 50,
    ...overrides,
  });
}

describe("ice_ai", () => {
  describe("coerceAggression", () => {
    it("returns valid aggression values as-is", () => {
      expect(coerceAggression("passive")).toBe("passive");
      expect(coerceAggression("standard")).toBe("standard");
      expect(coerceAggression("aggressive")).toBe("aggressive");
      expect(coerceAggression("boss")).toBe("boss");
    });

    it("falls back to standard for invalid values", () => {
      expect(coerceAggression("invalid")).toBe("standard");
      expect(coerceAggression("")).toBe("standard");
      expect(coerceAggression(null)).toBe("standard");
      expect(coerceAggression(undefined)).toBe("standard");
      expect(coerceAggression(42)).toBe("standard");
    });
  });

  describe("coercePersonality", () => {
    it("returns valid personality values as-is", () => {
      expect(coercePersonality("aggressive")).toBe("aggressive");
      expect(coercePersonality("defensive")).toBe("defensive");
      expect(coercePersonality("stealth")).toBe("stealth");
      expect(coercePersonality("support")).toBe("support");
    });

    it("falls back to aggressive for invalid values", () => {
      expect(coercePersonality("invalid")).toBe("aggressive");
      expect(coercePersonality("")).toBe("aggressive");
      expect(coercePersonality(null)).toBe("aggressive");
      expect(coercePersonality(undefined)).toBe("aggressive");
    });
  });

  describe("enemyShouldUseSkill", () => {
    const AGGRESSION_TIERS: AggressionTier[] = ["passive", "standard", "aggressive", "boss"];
    const SAMPLE_SIZE = 1000;

    for (const tier of AGGRESSION_TIERS) {
      it(`${tier} tier fires skill within probability bucket (${AGGRESSION_PROBABILITY[tier] * 100}%±15%)`, () => {
        const skill = makeSkill({ id: "s1", name: "Attack", effect: "attack" });
        const enemy = makeEnemy({ aggression: tier, skills: [skill] });

        let fires = 0;
        for (let i = 0; i < SAMPLE_SIZE; i++) {
          if (enemyShouldUseSkill(enemy, Math.random)) fires++;
        }

        const expected = AGGRESSION_PROBABILITY[tier] * SAMPLE_SIZE;
        const tolerance = SAMPLE_SIZE * 0.15;
        expect(fires).toBeGreaterThan(expected - tolerance);
        expect(fires).toBeLessThan(expected + tolerance);
      });
    }

    it("returns false when no skills equipped", () => {
      const enemy = makeEnemy({ aggression: "boss", skills: [] });
      expect(enemyShouldUseSkill(enemy, () => 0)).toBe(false);
    });

    it("returns false when hp <= 0", () => {
      const skill = makeSkill({ id: "s1", name: "Attack", effect: "attack" });
      const enemy = makeEnemy({ hp: 0, aggression: "boss", skills: [skill] });
      expect(enemyShouldUseSkill(enemy, () => 0)).toBe(false);
    });

    it("returns true when rng < probability (boss tier, rng=0.1)", () => {
      const skill = makeSkill({ id: "s1", name: "Attack", effect: "attack" });
      const enemy = makeEnemy({ aggression: "boss", skills: [skill] });
      expect(enemyShouldUseSkill(enemy, () => 0.1)).toBe(true);
    });

    it("returns false when rng >= probability (boss tier, rng=0.6)", () => {
      const skill = makeSkill({ id: "s1", name: "Attack", effect: "attack" });
      const enemy = makeEnemy({ aggression: "boss", skills: [skill] });
      expect(enemyShouldUseSkill(enemy, () => 0.6)).toBe(false);
    });

    it("defaults to standard tier for unknown aggression", () => {
      const skill = makeSkill({ id: "s1", name: "Attack", effect: "attack" });
      const enemy = makeEnemy({ aggression: "unknown" as AggressionTier, skills: [skill] });
      // standard = 0.15, rng = 0.10 → should fire
      expect(enemyShouldUseSkill(enemy, () => 0.10)).toBe(true);
      // standard = 0.15, rng = 0.20 → should not fire
      expect(enemyShouldUseSkill(enemy, () => 0.20)).toBe(false);
    });
  });

  describe("chooseSkill", () => {
    it("returns null when no skills equipped", () => {
      const enemy = makeEnemy({ skills: [] });
      expect(chooseSkill(enemy, Math.random)).toBeNull();
    });

    it("returns the only skill when one equipped", () => {
      const skill = makeSkill({ id: "s1", name: "Attack", effect: "attack" });
      const enemy = makeEnemy({ skills: [skill] });
      expect(chooseSkill(enemy, Math.random)).toBe(skill);
    });

    it("selects uniformly random from equipped skills", () => {
      const s1 = makeSkill({ id: "s1", name: "Attack", effect: "attack" });
      const s2 = makeSkill({ id: "s2", name: "Shield", effect: "shield" });
      const s3 = makeSkill({ id: "s3", name: "Heal", effect: "heal" });
      const enemy = makeEnemy({ skills: [s1, s2, s3] });

      const selected = new Map<string, number>();
      const SAMPLES = 3000;
      for (let i = 0; i < SAMPLES; i++) {
        const skill = chooseSkill(enemy, Math.random);
        if (skill) {
          selected.set(skill.id, (selected.get(skill.id) ?? 0) + 1);
        }
      }

      for (const skill of [s1, s2, s3]) {
        const count = selected.get(skill.id) ?? 0;
        const expected = SAMPLES / 3;
        const tolerance = SAMPLES * 0.1;
        expect(count).toBeGreaterThan(expected - tolerance);
        expect(count).toBeLessThan(expected + tolerance);
      }
    });
  });

  describe("selectSkillByPersonality", () => {
    it("returns null when no skills available", () => {
      const enemy = makeEnemy({ personality: "aggressive" });
      expect(selectSkillByPersonality(enemy, [])).toBeNull();
    });

    it("prefers heavy_attack for aggressive personality", () => {
      const heavy = makeSkill({ id: "h", name: "Heavy", effect: "heavy_attack" });
      const attack = makeSkill({ id: "a", name: "Attack", effect: "attack" });
      const enemy = makeEnemy({ personality: "aggressive" });
      expect(selectSkillByPersonality(enemy, [attack, heavy])).toBe(heavy);
    });

    it("prefers shield for defensive personality", () => {
      const shield = makeSkill({ id: "sh", name: "Shield", effect: "shield" });
      const attack = makeSkill({ id: "a", name: "Attack", effect: "attack" });
      const enemy = makeEnemy({ personality: "defensive" });
      expect(selectSkillByPersonality(enemy, [attack, shield])).toBe(shield);
    });

    it("prefers dot for stealth personality", () => {
      const dot = makeSkill({ id: "d", name: "Dot", effect: "dot" });
      const attack = makeSkill({ id: "a", name: "Attack", effect: "attack" });
      const enemy = makeEnemy({ personality: "stealth" });
      expect(selectSkillByPersonality(enemy, [attack, dot])).toBe(dot);
    });

    it("prefers heal for support personality", () => {
      const heal = makeSkill({ id: "h", name: "Heal", effect: "heal" });
      const attack = makeSkill({ id: "a", name: "Attack", effect: "attack" });
      const enemy = makeEnemy({ personality: "support" });
      expect(selectSkillByPersonality(enemy, [attack, heal])).toBe(heal);
    });

    it("falls back to first available skill when no preference matches", () => {
      const detect = makeSkill({ id: "d", name: "Detect", effect: "detect" });
      const enemy = makeEnemy({ personality: "aggressive" });
      expect(selectSkillByPersonality(enemy, [detect])).toBe(detect);
    });
  });

  describe("shouldDefensiveAct", () => {
    it("returns true for defensive personality below HP threshold", () => {
      const enemy = makeEnemy({ personality: "defensive", hp: 20, maxHp: 50 });
      expect(shouldDefensiveAct(enemy)).toBe(true);
    });

    it("returns false for defensive personality above HP threshold", () => {
      const enemy = makeEnemy({ personality: "defensive", hp: 30, maxHp: 50 });
      expect(shouldDefensiveAct(enemy)).toBe(false);
    });

    it("returns false for non-defensive personality even when low HP", () => {
      const enemy = makeEnemy({ personality: "aggressive", hp: 1, maxHp: 50 });
      expect(shouldDefensiveAct(enemy)).toBe(false);
    });

    it("returns false when maxHp is 0", () => {
      const enemy = makeEnemy({ personality: "defensive", hp: 0, maxHp: 0 });
      expect(shouldDefensiveAct(enemy)).toBe(false);
    });
  });

  describe("getAlarmMultiplier", () => {
    it("returns STEALTH_ALARM_MULTIPLIER for stealth personality", () => {
      const enemy = makeEnemy({ personality: "stealth" });
      expect(getAlarmMultiplier(enemy)).toBe(STEALTH_ALARM_MULTIPLIER);
    });

    it("returns 1.0 for non-stealth personalities", () => {
      expect(getAlarmMultiplier(makeEnemy({ personality: "aggressive" }))).toBe(1.0);
      expect(getAlarmMultiplier(makeEnemy({ personality: "defensive" }))).toBe(1.0);
      expect(getAlarmMultiplier(makeEnemy({ personality: "support" }))).toBe(1.0);
    });
  });

  describe("getCritBonus", () => {
    it("returns AGGRESSIVE_CRIT_BONUS for aggressive personality", () => {
      const enemy = makeEnemy({ personality: "aggressive" });
      expect(getCritBonus(enemy)).toBe(AGGRESSIVE_CRIT_BONUS);
    });

    it("returns 0 for non-aggressive personalities", () => {
      expect(getCritBonus(makeEnemy({ personality: "defensive" }))).toBe(0);
      expect(getCritBonus(makeEnemy({ personality: "stealth" }))).toBe(0);
      expect(getCritBonus(makeEnemy({ personality: "support" }))).toBe(0);
    });
  });

  describe("shouldTargetAlly", () => {
    it("returns true for support personality when ally is wounded", () => {
      const self = makeEnemy({ id: "self", personality: "support", hp: 50, maxHp: 50 });
      const wounded = makeEnemy({ id: "ally", hp: 30, maxHp: 50 });
      expect(shouldTargetAlly(self, [self, wounded])).toBe(true);
    });

    it("returns false for support personality when no ally is wounded", () => {
      const self = makeEnemy({ id: "self", personality: "support", hp: 50, maxHp: 50 });
      const healthy = makeEnemy({ id: "ally", hp: 50, maxHp: 50 });
      expect(shouldTargetAlly(self, [self, healthy])).toBe(false);
    });

    it("returns false for non-support personality", () => {
      const self = makeEnemy({ id: "self", personality: "aggressive", hp: 50, maxHp: 50 });
      const wounded = makeEnemy({ id: "ally", hp: 10, maxHp: 50 });
      expect(shouldTargetAlly(self, [self, wounded])).toBe(false);
    });

    it("returns false when ally is dead", () => {
      const self = makeEnemy({ id: "self", personality: "support", hp: 50, maxHp: 50 });
      const dead = makeEnemy({ id: "ally", hp: 0, maxHp: 50 });
      expect(shouldTargetAlly(self, [self, dead])).toBe(false);
    });

    it("does not target self even if wounded", () => {
      const self = makeEnemy({ id: "self", personality: "support", hp: 10, maxHp: 50 });
      expect(shouldTargetAlly(self, [self])).toBe(false);
    });
  });
});
