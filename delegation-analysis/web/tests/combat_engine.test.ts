/** Unit tests for combat damage calculation engine. */
import { describe, it, expect } from "vitest";
import {
  calculateDamage,
  tickCombo,
  tickAlarm,
  countRoleSynergy,
  COMBO_WINDOW_MS,
  type DamageContext,
} from "../src/core/combat_engine.ts";

describe("combat_engine", () => {
  describe("calculateDamage", () => {
    it("basic damage with no bonuses returns damage within variance range", () => {
      const mockRng = () => 0.5; // middle of range → variance = 1.0
      const ctx: DamageContext = {
        baseDamage: 10,
        attackerTeam: "player",
        attackerAttackBonus: 0,
        attackerCritBonusPct: 0,
        defenderDefenseBonus: 0,
        defenderIceResistance: 0,
        defenderIceKind: null,
        lastSkillRole: null,
        lastSkillCritBonus: 0,
        playerCombo: 1,
        roleSynergyCount: 1,
        defenderVulnerabilityPct: 0,
        defenderSlowReductionPct: 0,
        rng: mockRng,
      };
      const result = calculateDamage(ctx);
      // variance = 0.5 * (1.2 - 0.8) + 0.8 = 1.0
      // damage = 10 * 1.0 = 10
      expect(result.damage).toBe(10);
      expect(result.isCrit).toBe(false);
    });

    it("variance min returns 80% damage", () => {
      let callCount = 0;
      const mockRng = () => {
        callCount++;
        // First call: variance (0.0 → min)
        // Second call: crit check (0.99 → no crit)
        if (callCount === 1) return 0.0;
        return 0.99;
      };
      const ctx: DamageContext = {
        baseDamage: 100,
        attackerTeam: "player",
        attackerAttackBonus: 0,
        attackerCritBonusPct: 0,
        defenderDefenseBonus: 0,
        defenderIceResistance: 0,
        defenderIceKind: null,
        lastSkillRole: null,
        lastSkillCritBonus: 0,
        playerCombo: 1,
        roleSynergyCount: 1,
        defenderVulnerabilityPct: 0,
        defenderSlowReductionPct: 0,
        rng: mockRng,
      };
      const result = calculateDamage(ctx);
      // variance = 0.0 * 0.4 + 0.8 = 0.8
      // damage = 100 * 0.8 = 80
      expect(result.damage).toBe(80);
      expect(result.isCrit).toBe(false);
    });

    it("variance max returns 120% damage", () => {
      const mockRng = () => 1.0; // max variance
      const ctx: DamageContext = {
        baseDamage: 100,
        attackerTeam: "player",
        attackerAttackBonus: 0,
        attackerCritBonusPct: 0,
        defenderDefenseBonus: 0,
        defenderIceResistance: 0,
        defenderIceKind: null,
        lastSkillRole: null,
        lastSkillCritBonus: 0,
        playerCombo: 1,
        roleSynergyCount: 1,
        defenderVulnerabilityPct: 0,
        defenderSlowReductionPct: 0,
        rng: mockRng,
      };
      const result = calculateDamage(ctx);
      // variance = 1.0 * 0.4 + 0.8 = 1.2
      // damage = 100 * 1.2 = 120
      expect(result.damage).toBe(120);
      expect(result.isCrit).toBe(false);
    });

    it("crit when rng < crit chance", () => {
      let callCount = 0;
      const mockRng = () => {
        callCount++;
        // First call: variance (middle)
        // Second call: crit check (0.01 < 0.15 = crit)
        // Third call: crit multiplier (middle = 2.0)
        if (callCount === 1) return 0.5;
        if (callCount === 2) return 0.01; // below CRIT_CHANCE
        return 0.5; // crit mult middle
      };
      const ctx: DamageContext = {
        baseDamage: 10,
        attackerTeam: "player",
        attackerAttackBonus: 0,
        attackerCritBonusPct: 0,
        defenderDefenseBonus: 0,
        defenderIceResistance: 0,
        defenderIceKind: null,
        lastSkillRole: null,
        lastSkillCritBonus: 0,
        playerCombo: 1,
        roleSynergyCount: 1,
        defenderVulnerabilityPct: 0,
        defenderSlowReductionPct: 0,
        rng: mockRng,
      };
      const result = calculateDamage(ctx);
      expect(result.isCrit).toBe(true);
      // damage = 10 * 1.0 * 2.0 = 20
      expect(result.damage).toBe(20);
    });

    it("no crit when rng >= crit chance", () => {
      let callCount = 0;
      const mockRng = () => {
        callCount++;
        if (callCount === 1) return 0.5; // variance middle
        return 0.99; // above CRIT_CHANCE
      };
      const ctx: DamageContext = {
        baseDamage: 10,
        attackerTeam: "player",
        attackerAttackBonus: 0,
        attackerCritBonusPct: 0,
        defenderDefenseBonus: 0,
        defenderIceResistance: 0,
        defenderIceKind: null,
        lastSkillRole: null,
        lastSkillCritBonus: 0,
        playerCombo: 1,
        roleSynergyCount: 1,
        defenderVulnerabilityPct: 0,
        defenderSlowReductionPct: 0,
        rng: mockRng,
      };
      const result = calculateDamage(ctx);
      expect(result.isCrit).toBe(false);
      expect(result.damage).toBe(10);
    });

    it("weakness multiplier: standard ICE vs strike role", () => {
      const mockRng = () => 0.5;
      const ctx: DamageContext = {
        baseDamage: 10,
        attackerTeam: "player",
        attackerAttackBonus: 0,
        attackerCritBonusPct: 0,
        defenderDefenseBonus: 0,
        defenderIceResistance: 0,
        defenderIceKind: "standard",
        lastSkillRole: "strike",
        lastSkillCritBonus: 0,
        playerCombo: 1,
        roleSynergyCount: 1,
        defenderVulnerabilityPct: 0,
        defenderSlowReductionPct: 0,
        rng: mockRng,
      };
      const result = calculateDamage(ctx);
      // damage = 10 * 1.0 (variance) * 1.5 (weakness) = 15
      expect(result.damage).toBe(15);
      expect(result.isCrit).toBe(false);
    });

    it("resistance reduces damage: 30% resistance", () => {
      const mockRng = () => 0.5;
      const ctx: DamageContext = {
        baseDamage: 10,
        attackerTeam: "player",
        attackerAttackBonus: 0,
        attackerCritBonusPct: 0,
        defenderDefenseBonus: 0,
        defenderIceResistance: 0.3,
        defenderIceKind: null,
        lastSkillRole: null,
        lastSkillCritBonus: 0,
        playerCombo: 1,
        roleSynergyCount: 1,
        defenderVulnerabilityPct: 0,
        defenderSlowReductionPct: 0,
        rng: mockRng,
      };
      const result = calculateDamage(ctx);
      // damage = 10 * 1.0 * (1 - 0.3) = 7
      expect(result.damage).toBe(7);
    });

    it("combo bonus: combo 3 = 1.2x multiplier", () => {
      const mockRng = () => 0.5;
      const ctx: DamageContext = {
        baseDamage: 10,
        attackerTeam: "player",
        attackerAttackBonus: 0,
        attackerCritBonusPct: 0,
        defenderDefenseBonus: 0,
        defenderIceResistance: 0,
        defenderIceKind: null,
        lastSkillRole: null,
        lastSkillCritBonus: 0,
        playerCombo: 3,
        roleSynergyCount: 1,
        defenderVulnerabilityPct: 0,
        defenderSlowReductionPct: 0,
        rng: mockRng,
      };
      const result = calculateDamage(ctx);
      // damage = 10 * 1.0 * 1.2 (combo) = 12
      expect(result.damage).toBe(12);
    });

    it("role synergy: 2 matching skills = 1.15x multiplier", () => {
      const mockRng = () => 0.5;
      const ctx: DamageContext = {
        baseDamage: 10,
        attackerTeam: "player",
        attackerAttackBonus: 0,
        attackerCritBonusPct: 0,
        defenderDefenseBonus: 0,
        defenderIceResistance: 0,
        defenderIceKind: null,
        lastSkillRole: "strike",
        lastSkillCritBonus: 0,
        playerCombo: 1,
        roleSynergyCount: 2,
        defenderVulnerabilityPct: 0,
        defenderSlowReductionPct: 0,
        rng: mockRng,
      };
      const result = calculateDamage(ctx);
      // damage = 10 * 1.0 * 1.15 (synergy) = 11 (floored)
      expect(result.damage).toBe(11);
    });

    it("vulnerability: 25% vulnerability increases damage", () => {
      const mockRng = () => 0.5;
      const ctx: DamageContext = {
        baseDamage: 10,
        attackerTeam: "player",
        attackerAttackBonus: 0,
        attackerCritBonusPct: 0,
        defenderDefenseBonus: 0,
        defenderIceResistance: 0,
        defenderIceKind: null,
        lastSkillRole: null,
        lastSkillCritBonus: 0,
        playerCombo: 1,
        roleSynergyCount: 1,
        defenderVulnerabilityPct: 25,
        defenderSlowReductionPct: 0,
        rng: mockRng,
      };
      const result = calculateDamage(ctx);
      // damage = floor(10 * 1.0 * 1.25) = 12
      expect(result.damage).toBe(12);
    });

    it("attack bonus adds flat damage", () => {
      const mockRng = () => 0.5;
      const ctx: DamageContext = {
        baseDamage: 10,
        attackerTeam: "player",
        attackerAttackBonus: 5,
        attackerCritBonusPct: 0,
        defenderDefenseBonus: 0,
        defenderIceResistance: 0,
        defenderIceKind: null,
        lastSkillRole: null,
        lastSkillCritBonus: 0,
        playerCombo: 1,
        roleSynergyCount: 1,
        defenderVulnerabilityPct: 0,
        defenderSlowReductionPct: 0,
        rng: mockRng,
      };
      const result = calculateDamage(ctx);
      // damage = 10 + 5 = 15
      expect(result.damage).toBe(15);
    });

    it("defense bonus reduces damage", () => {
      const mockRng = () => 0.5;
      const ctx: DamageContext = {
        baseDamage: 10,
        attackerTeam: "player",
        attackerAttackBonus: 0,
        attackerCritBonusPct: 0,
        defenderDefenseBonus: 3,
        defenderIceResistance: 0,
        defenderIceKind: null,
        lastSkillRole: null,
        lastSkillCritBonus: 0,
        playerCombo: 1,
        roleSynergyCount: 1,
        defenderVulnerabilityPct: 0,
        defenderSlowReductionPct: 0,
        rng: mockRng,
      };
      const result = calculateDamage(ctx);
      // damage = max(0, 10 - 3) = 7
      expect(result.damage).toBe(7);
    });

    it("minimum damage is 1 (all reductions)", () => {
      const mockRng = () => 0.0; // min variance
      const ctx: DamageContext = {
        baseDamage: 1,
        attackerTeam: "player",
        attackerAttackBonus: 0,
        attackerCritBonusPct: 0,
        defenderDefenseBonus: 100,
        defenderIceResistance: 0.9,
        defenderIceKind: null,
        lastSkillRole: null,
        lastSkillCritBonus: 0,
        playerCombo: 1,
        roleSynergyCount: 1,
        defenderVulnerabilityPct: 0,
        defenderSlowReductionPct: 0,
        rng: mockRng,
      };
      const result = calculateDamage(ctx);
      // damage reduced to ~0, but min is 1
      expect(result.damage).toBe(1);
    });

    it("enemy attacker does not get player bonuses", () => {
      const mockRng = () => 0.5;
      const ctx: DamageContext = {
        baseDamage: 10,
        attackerTeam: "enemy",
        attackerAttackBonus: 0,
        attackerCritBonusPct: 0,
        defenderDefenseBonus: 0,
        defenderIceResistance: 0,
        defenderIceKind: "standard",
        lastSkillRole: "strike",
        lastSkillCritBonus: 0,
        playerCombo: 3,
        roleSynergyCount: 2,
        defenderVulnerabilityPct: 0,
        defenderSlowReductionPct: 0,
        rng: mockRng,
      };
      const result = calculateDamage(ctx);
      // enemy ignores weakness, combo, synergy → damage = 10
      expect(result.damage).toBe(10);
    });

    it("stacked bonuses: combo + synergy + weakness + vulnerability", () => {
      const mockRng = () => 0.5;
      const ctx: DamageContext = {
        baseDamage: 10,
        attackerTeam: "player",
        attackerAttackBonus: 0,
        attackerCritBonusPct: 0,
        defenderDefenseBonus: 0,
        defenderIceResistance: 0,
        defenderIceKind: "standard",
        lastSkillRole: "strike",
        lastSkillCritBonus: 0,
        playerCombo: 3,
        roleSynergyCount: 2,
        defenderVulnerabilityPct: 20,
        defenderSlowReductionPct: 0,
        rng: mockRng,
      };
      const result = calculateDamage(ctx);
      // damage = 10 * 1.0 (var) * 1.5 (weak) * 1.15 (syn) * 1.2 (combo) * 1.2 (vuln)
      // = 10 * 1.5 * 1.15 * 1.2 = 20.7 → floor = 20
      // then vulnerability: floor(20 * 1.2) = 24
      expect(result.damage).toBeGreaterThanOrEqual(24);
    });
  });

  describe("tickCombo", () => {
    it("combo within window stays unchanged", () => {
      const result = tickCombo(3, 1000, 3000);
      expect(result).toBe(3);
    });

    it("combo expired when beyond COMBO_WINDOW_MS", () => {
      const result = tickCombo(3, 1000, 5000);
      expect(result).toBe(0);
    });

    it("zero combo returns 0", () => {
      const result = tickCombo(0, 1000, 5000);
      expect(result).toBe(0);
    });

    it("combo at exact window boundary stays", () => {
      const lastHit = 1000;
      const current = lastHit + COMBO_WINDOW_MS;
      const result = tickCombo(5, lastHit, current);
      expect(result).toBe(5);
    });

    it("combo just past window expires", () => {
      const lastHit = 1000;
      const current = lastHit + COMBO_WINDOW_MS + 1;
      const result = tickCombo(5, lastHit, current);
      expect(result).toBe(0);
    });
  });

  describe("tickAlarm", () => {
    it("no tick when interval not reached", () => {
      const result = tickAlarm(2, 0, 5000, 1.0);
      expect(result.alarmLevel).toBe(2);
      expect(result.lastAlarmTickMs).toBe(0);
      expect(result.message).toBeNull();
    });

    it("tick increases level when interval reached", () => {
      const result = tickAlarm(2, 0, 10000, 1.0);
      expect(result.alarmLevel).toBe(3);
      expect(result.lastAlarmTickMs).toBe(10000);
      expect(result.message).toContain("alarm level 3");
    });

    it("max level stays at ALARM_MAX_LEVEL", () => {
      const result = tickAlarm(5, 0, 10000, 1.0);
      expect(result.alarmLevel).toBe(5);
    });

    it("alarm speed 2.0 halves tick interval", () => {
      // With speed 2.0, interval = 10000 / 2.0 = 5000ms
      const noTick = tickAlarm(2, 0, 4999, 2.0);
      expect(noTick.alarmLevel).toBe(2);

      const yesTick = tickAlarm(2, 0, 5000, 2.0);
      expect(yesTick.alarmLevel).toBe(3);
    });

    it("alarm speed 0.5 doubles tick interval", () => {
      // With speed 0.5, interval = 10000 / 0.5 = 20000ms
      const noTick = tickAlarm(1, 0, 19999, 0.5);
      expect(noTick.alarmLevel).toBe(1);

      const yesTick = tickAlarm(1, 0, 20000, 0.5);
      expect(yesTick.alarmLevel).toBe(2);
    });

    it("multiple ticks in one call", () => {
      // If 20 seconds pass, should tick twice: level 1 → 2 → 3
      // But tickAlarm only increments ONCE per call
      const result = tickAlarm(1, 0, 20000, 1.0);
      expect(result.alarmLevel).toBe(2);
    });
  });

  describe("countRoleSynergy", () => {
    it("no role returns 0", () => {
      const skills = [
        { role: "strike" },
        { role: "burst" },
      ];
      const result = countRoleSynergy(null, skills);
      expect(result).toBe(0);
    });

    it("matching role counts skills with same role", () => {
      const skills = [
        { role: "strike" },
        { role: "burst" },
        { role: "strike" },
      ];
      const result = countRoleSynergy("strike", skills);
      expect(result).toBe(2);
    });

    it("no match returns 0", () => {
      const skills = [
        { role: "strike" },
        { role: "strike" },
      ];
      const result = countRoleSynergy("burst", skills);
      expect(result).toBe(0);
    });

    it("empty skills array returns 0", () => {
      const result = countRoleSynergy("strike", []);
      expect(result).toBe(0);
    });

    it("skills with null role do not count", () => {
      const skills = [
        { role: "strike" },
        { role: null },
        { role: "strike" },
      ];
      const result = countRoleSynergy("strike", skills);
      expect(result).toBe(2);
    });
  });
});
