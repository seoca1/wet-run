import { describe, it, expect } from "vitest";
import {
  createCombatStats,
  createCombatant,
  createCombatState,
  getTarget,
  pushLog,
  isAlive,
  isStunned,
  isStaggered,
  consumeStagger,
  getAttackBonus,
  getDefenseBonus,
  getTotalAttack,
} from "../src/core/combat_models.ts";
import type {
  StatusEffect,
  Skill,
} from "../src/core/combat_models.ts";

describe("createCombatStats", () => {
  it("initializes all stats to zero", () => {
    const stats = createCombatStats();
    expect(stats.damageDealt).toBe(0);
    expect(stats.damageReceived).toBe(0);
    expect(stats.critsLanded).toBe(0);
    expect(stats.critsReceived).toBe(0);
    expect(stats.skillsUsed).toBe(0);
    expect(stats.maxComboReached).toBe(0);
    expect(stats.peakAlarmLevel).toBe(0);
    expect(stats.turnsElapsed).toBe(0);
  });

  it("creates independent objects", () => {
    const stats1 = createCombatStats();
    const stats2 = createCombatStats();
    stats1.damageDealt = 100;
    expect(stats2.damageDealt).toBe(0);
  });
});

describe("createCombatant", () => {
  it("requires id, name, hp, and maxHp", () => {
    const combatant = createCombatant({
      id: "test",
      name: "Test",
      hp: 100,
      maxHp: 100,
    });
    expect(combatant.id).toBe("test");
    expect(combatant.name).toBe("Test");
    expect(combatant.hp).toBe(100);
    expect(combatant.maxHp).toBe(100);
  });

  it("uses default values for optional fields", () => {
    const combatant = createCombatant({
      id: "test",
      name: "Test",
      hp: 100,
      maxHp: 100,
    });
    expect(combatant.portrait).toBe("");
    expect(combatant.color).toBe("#ffffff");
    expect(combatant.ap).toBe(0);
    expect(combatant.maxAp).toBe(6);
    expect(combatant.autoAttackDamage).toBe(5);
    expect(combatant.skills).toEqual([]);
    expect(combatant.team).toBe("enemy");
    expect(combatant.statuses).toEqual([]);
  });

  it("accepts partial overrides", () => {
    const combatant = createCombatant({
      id: "test",
      name: "Test",
      hp: 100,
      maxHp: 100,
      ap: 3,
      maxAp: 8,
      team: "player",
    });
    expect(combatant.ap).toBe(3);
    expect(combatant.maxAp).toBe(8);
    expect(combatant.team).toBe("player");
  });

  it("initializes equipment bonuses to zero", () => {
    const combatant = createCombatant({
      id: "test",
      name: "Test",
      hp: 100,
      maxHp: 100,
    });
    expect(combatant.equipAttackBonus).toBe(0);
    expect(combatant.equipDefenseBonus).toBe(0);
    expect(combatant.equipHpBonus).toBe(0);
    expect(combatant.equipShieldBonus).toBe(0);
    expect(combatant.equipApBonus).toBe(0);
    expect(combatant.equipProgramPower).toBe(0);
    expect(combatant.equipIceResistance).toBe(0);
    expect(combatant.equipDamageBonusPct).toBe(0);
    expect(combatant.equipCritBonusPct).toBe(0);
  });

  it("initializes combat attributes", () => {
    const combatant = createCombatant({
      id: "test",
      name: "Test",
      hp: 100,
      maxHp: 100,
    });
    expect(combatant.baseAttack).toBe(0);
    expect(combatant.baseDefense).toBe(0);
    expect(combatant.iceKind).toBeNull();
    expect(combatant.iceResistance).toBe(0);
    expect(combatant.alarmSpeed).toBe(1);
    expect(combatant.currentPhase).toBe(1);
    expect(combatant.aggression).toBe("standard");
    expect(combatant.personality).toBe("aggressive");
  });

  it("accepts custom skills", () => {
    const skill: Skill = {
      id: "s1",
      name: "Slash",
      tier: 1,
      effect: "attack",
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
      effectColor: "#ff0000",
      effectGlyph: "X",
    };
    const combatant = createCombatant({
      id: "test",
      name: "Test",
      hp: 100,
      maxHp: 100,
      skills: [skill],
    });
    expect(combatant.skills.length).toBe(1);
    expect(combatant.skills[0]).toBe(skill);
  });
});

describe("createCombatState", () => {
  it("initializes with player and enemies", () => {
    const player = createCombatant({
      id: "p1",
      name: "Player",
      hp: 100,
      maxHp: 100,
      team: "player",
    });
    const enemy = createCombatant({
      id: "e1",
      name: "Enemy",
      hp: 50,
      maxHp: 50,
    });
    const state = createCombatState(player, [enemy]);
    expect(state.player).toBe(player);
    expect(state.enemies).toEqual([enemy]);
  });

  it("initializes targetIndex to 0", () => {
    const player = createCombatant({
      id: "p1",
      name: "Player",
      hp: 100,
      maxHp: 100,
    });
    const state = createCombatState(player, []);
    expect(state.targetIndex).toBe(0);
  });

  it("initializes combat tracking fields", () => {
    const player = createCombatant({
      id: "p1",
      name: "Player",
      hp: 100,
      maxHp: 100,
    });
    const state = createCombatState(player, []);
    expect(state.tickMs).toBe(0);
    expect(state.lastPlayerAttackMs).toBe(-2000);
    expect(state.lastEnemyAttackMs).toBe(-2000);
    expect(state.lastApRegenMs).toBe(0);
    expect(state.shield).toBe(0);
  });

  it("initializes log as empty array", () => {
    const player = createCombatant({
      id: "p1",
      name: "Player",
      hp: 100,
      maxHp: 100,
    });
    const state = createCombatState(player, []);
    expect(state.log).toEqual([]);
  });

  it("initializes as not finished", () => {
    const player = createCombatant({
      id: "p1",
      name: "Player",
      hp: 100,
      maxHp: 100,
    });
    const state = createCombatState(player, []);
    expect(state.finished).toBe(false);
    expect(state.outcome).toBe("ongoing");
  });

  it("initializes combo and alarm tracking", () => {
    const player = createCombatant({
      id: "p1",
      name: "Player",
      hp: 100,
      maxHp: 100,
    });
    const state = createCombatState(player, []);
    expect(state.playerCombo).toBe(0);
    expect(state.enemyCombo).toBe(0);
    expect(state.alarmLevel).toBe(0);
    expect(state.lastAlarmTickMs).toBe(0);
  });

  it("initializes stats", () => {
    const player = createCombatant({
      id: "p1",
      name: "Player",
      hp: 100,
      maxHp: 100,
    });
    const state = createCombatState(player, []);
    expect(state.stats).toBeDefined();
    expect(state.stats.damageDealt).toBe(0);
  });

  it("initializes special mechanics", () => {
    const player = createCombatant({
      id: "p1",
      name: "Player",
      hp: 100,
      maxHp: 100,
    });
    const state = createCombatState(player, []);
    expect(state.counterWindowOpenMs).toBe(0);
    expect(state.dixieLastAttackMs).toBe(-2000);
    expect(state.wardroneLastCounterMs).toBe(-5000);
    expect(state.bossPhase4Mechanic).toBeNull();
    expect(state.phaseChangeMs).toBe(0);
    expect(state.friendlyNodeHp).toBe(100);
  });
});

describe("getTarget", () => {
  it("returns first enemy when targetIndex is 0", () => {
    const player = createCombatant({
      id: "p1",
      name: "Player",
      hp: 100,
      maxHp: 100,
    });
    const enemy = createCombatant({
      id: "e1",
      name: "Enemy",
      hp: 50,
      maxHp: 50,
    });
    const state = createCombatState(player, [enemy]);
    expect(getTarget(state)).toBe(enemy);
  });

  it("returns null when enemies array is empty", () => {
    const player = createCombatant({
      id: "p1",
      name: "Player",
      hp: 100,
      maxHp: 100,
    });
    const state = createCombatState(player, []);
    expect(getTarget(state)).toBeNull();
  });

  it("returns null when targetIndex exceeds array length", () => {
    const player = createCombatant({
      id: "p1",
      name: "Player",
      hp: 100,
      maxHp: 100,
    });
    const enemy = createCombatant({
      id: "e1",
      name: "Enemy",
      hp: 50,
      maxHp: 50,
    });
    const state = createCombatState(player, [enemy]);
    state.targetIndex = 5;
    expect(getTarget(state)).toBeNull();
  });

  it("returns correct enemy for non-zero targetIndex", () => {
    const player = createCombatant({
      id: "p1",
      name: "Player",
      hp: 100,
      maxHp: 100,
    });
    const enemy1 = createCombatant({
      id: "e1",
      name: "Enemy 1",
      hp: 50,
      maxHp: 50,
    });
    const enemy2 = createCombatant({
      id: "e2",
      name: "Enemy 2",
      hp: 60,
      maxHp: 60,
    });
    const state = createCombatState(player, [enemy1, enemy2]);
    state.targetIndex = 1;
    expect(getTarget(state)).toBe(enemy2);
  });
});

describe("pushLog", () => {
  it("adds message to log", () => {
    const player = createCombatant({
      id: "p1",
      name: "Player",
      hp: 100,
      maxHp: 100,
    });
    const state = createCombatState(player, []);
    pushLog(state, "Test message");
    expect(state.log).toEqual(["Test message"]);
  });

  it("maintains log size limit of 6", () => {
    const player = createCombatant({
      id: "p1",
      name: "Player",
      hp: 100,
      maxHp: 100,
    });
    const state = createCombatState(player, []);
    for (let i = 0; i < 10; i++) {
      pushLog(state, `Message ${i}`);
    }
    expect(state.log.length).toBe(6);
  });

  it("removes oldest message when exceeding limit", () => {
    const player = createCombatant({
      id: "p1",
      name: "Player",
      hp: 100,
      maxHp: 100,
    });
    const state = createCombatState(player, []);
    for (let i = 0; i < 7; i++) {
      pushLog(state, `Message ${i}`);
    }
    expect(state.log[0]).toBe("Message 1");
    expect(state.log[5]).toBe("Message 6");
  });
});

describe("isAlive", () => {
  it("returns true when hp is positive", () => {
    const combatant = createCombatant({
      id: "test",
      name: "Test",
      hp: 100,
      maxHp: 100,
    });
    expect(isAlive(combatant)).toBe(true);
  });

  it("returns false when hp is zero", () => {
    const combatant = createCombatant({
      id: "test",
      name: "Test",
      hp: 0,
      maxHp: 100,
    });
    expect(isAlive(combatant)).toBe(false);
  });

  it("returns false when hp is negative", () => {
    const combatant = createCombatant({
      id: "test",
      name: "Test",
      hp: -10,
      maxHp: 100,
    });
    expect(isAlive(combatant)).toBe(false);
  });
});

describe("isStunned", () => {
  it("returns false when no statuses", () => {
    const combatant = createCombatant({
      id: "test",
      name: "Test",
      hp: 100,
      maxHp: 100,
    });
    expect(isStunned(combatant)).toBe(false);
  });

  it("returns true when status has isStunned flag", () => {
    const combatant = createCombatant({
      id: "test",
      name: "Test",
      hp: 100,
      maxHp: 100,
    });
    const status: StatusEffect = {
      effectId: "stun",
      remainingMs: 1000,
      dotDamage: 0,
      healPerTick: 0,
      attackBonus: 0,
      defenseBonus: 0,
      isStunned: true,
      isStaggered: false,
      isShield: false,
      slowPct: 0,
      isSilenced: false,
      vulnerabilityPct: 0,
    };
    combatant.statuses.push(status);
    expect(isStunned(combatant)).toBe(true);
  });

  it("returns false when no stun status", () => {
    const combatant = createCombatant({
      id: "test",
      name: "Test",
      hp: 100,
      maxHp: 100,
    });
    const status: StatusEffect = {
      effectId: "buff",
      remainingMs: 1000,
      dotDamage: 0,
      healPerTick: 0,
      attackBonus: 5,
      defenseBonus: 0,
      isStunned: false,
      isStaggered: false,
      isShield: false,
      slowPct: 0,
      isSilenced: false,
      vulnerabilityPct: 0,
    };
    combatant.statuses.push(status);
    expect(isStunned(combatant)).toBe(false);
  });
});

describe("isStaggered", () => {
  it("returns false when no statuses", () => {
    const combatant = createCombatant({
      id: "test",
      name: "Test",
      hp: 100,
      maxHp: 100,
    });
    expect(isStaggered(combatant)).toBe(false);
  });

  it("returns true when status has isStaggered flag", () => {
    const combatant = createCombatant({
      id: "test",
      name: "Test",
      hp: 100,
      maxHp: 100,
    });
    const status: StatusEffect = {
      effectId: "stagger",
      remainingMs: 500,
      dotDamage: 0,
      healPerTick: 0,
      attackBonus: 0,
      defenseBonus: 0,
      isStunned: false,
      isStaggered: true,
      isShield: false,
      slowPct: 0,
      isSilenced: false,
      vulnerabilityPct: 0,
    };
    combatant.statuses.push(status);
    expect(isStaggered(combatant)).toBe(true);
  });
});

describe("consumeStagger", () => {
  it("removes stagger status", () => {
    const combatant = createCombatant({
      id: "test",
      name: "Test",
      hp: 100,
      maxHp: 100,
    });
    const stagger: StatusEffect = {
      effectId: "stagger",
      remainingMs: 500,
      dotDamage: 0,
      healPerTick: 0,
      attackBonus: 0,
      defenseBonus: 0,
      isStunned: false,
      isStaggered: true,
      isShield: false,
      slowPct: 0,
      isSilenced: false,
      vulnerabilityPct: 0,
    };
    combatant.statuses.push(stagger);
    consumeStagger(combatant);
    expect(combatant.statuses.length).toBe(0);
  });

  it("preserves non-stagger statuses", () => {
    const combatant = createCombatant({
      id: "test",
      name: "Test",
      hp: 100,
      maxHp: 100,
    });
    const buff: StatusEffect = {
      effectId: "buff",
      remainingMs: 1000,
      dotDamage: 0,
      healPerTick: 0,
      attackBonus: 5,
      defenseBonus: 0,
      isStunned: false,
      isStaggered: false,
      isShield: false,
      slowPct: 0,
      isSilenced: false,
      vulnerabilityPct: 0,
    };
    const stagger: StatusEffect = {
      effectId: "stagger",
      remainingMs: 500,
      dotDamage: 0,
      healPerTick: 0,
      attackBonus: 0,
      defenseBonus: 0,
      isStunned: false,
      isStaggered: true,
      isShield: false,
      slowPct: 0,
      isSilenced: false,
      vulnerabilityPct: 0,
    };
    combatant.statuses.push(buff, stagger);
    consumeStagger(combatant);
    expect(combatant.statuses.length).toBe(1);
    expect(combatant.statuses[0]).toBe(buff);
  });
});

describe("getAttackBonus", () => {
  it("returns zero when no statuses or equipment", () => {
    const combatant = createCombatant({
      id: "test",
      name: "Test",
      hp: 100,
      maxHp: 100,
    });
    expect(getAttackBonus(combatant)).toBe(0);
  });

  it("sums attack bonuses from statuses", () => {
    const combatant = createCombatant({
      id: "test",
      name: "Test",
      hp: 100,
      maxHp: 100,
    });
    const buff1: StatusEffect = {
      effectId: "buff1",
      remainingMs: 1000,
      dotDamage: 0,
      healPerTick: 0,
      attackBonus: 5,
      defenseBonus: 0,
      isStunned: false,
      isStaggered: false,
      isShield: false,
      slowPct: 0,
      isSilenced: false,
      vulnerabilityPct: 0,
    };
    const buff2: StatusEffect = {
      effectId: "buff2",
      remainingMs: 1000,
      dotDamage: 0,
      healPerTick: 0,
      attackBonus: 3,
      defenseBonus: 0,
      isStunned: false,
      isStaggered: false,
      isShield: false,
      slowPct: 0,
      isSilenced: false,
      vulnerabilityPct: 0,
    };
    combatant.statuses.push(buff1, buff2);
    expect(getAttackBonus(combatant)).toBe(8);
  });

  it("includes equipment attack bonus", () => {
    const combatant = createCombatant({
      id: "test",
      name: "Test",
      hp: 100,
      maxHp: 100,
      equipAttackBonus: 10,
    });
    expect(getAttackBonus(combatant)).toBe(10);
  });

  it("combines status and equipment bonuses", () => {
    const combatant = createCombatant({
      id: "test",
      name: "Test",
      hp: 100,
      maxHp: 100,
      equipAttackBonus: 10,
    });
    const buff: StatusEffect = {
      effectId: "buff",
      remainingMs: 1000,
      dotDamage: 0,
      healPerTick: 0,
      attackBonus: 5,
      defenseBonus: 0,
      isStunned: false,
      isStaggered: false,
      isShield: false,
      slowPct: 0,
      isSilenced: false,
      vulnerabilityPct: 0,
    };
    combatant.statuses.push(buff);
    expect(getAttackBonus(combatant)).toBe(15);
  });
});

describe("getDefenseBonus", () => {
  it("returns zero when no statuses or equipment", () => {
    const combatant = createCombatant({
      id: "test",
      name: "Test",
      hp: 100,
      maxHp: 100,
    });
    expect(getDefenseBonus(combatant)).toBe(0);
  });

  it("sums defense bonuses from statuses", () => {
    const combatant = createCombatant({
      id: "test",
      name: "Test",
      hp: 100,
      maxHp: 100,
    });
    const buff1: StatusEffect = {
      effectId: "buff1",
      remainingMs: 1000,
      dotDamage: 0,
      healPerTick: 0,
      attackBonus: 0,
      defenseBonus: 4,
      isStunned: false,
      isStaggered: false,
      isShield: false,
      slowPct: 0,
      isSilenced: false,
      vulnerabilityPct: 0,
    };
    const buff2: StatusEffect = {
      effectId: "buff2",
      remainingMs: 1000,
      dotDamage: 0,
      healPerTick: 0,
      attackBonus: 0,
      defenseBonus: 6,
      isStunned: false,
      isStaggered: false,
      isShield: false,
      slowPct: 0,
      isSilenced: false,
      vulnerabilityPct: 0,
    };
    combatant.statuses.push(buff1, buff2);
    expect(getDefenseBonus(combatant)).toBe(10);
  });

  it("includes equipment defense bonus", () => {
    const combatant = createCombatant({
      id: "test",
      name: "Test",
      hp: 100,
      maxHp: 100,
      equipDefenseBonus: 8,
    });
    expect(getDefenseBonus(combatant)).toBe(8);
  });
});

describe("getTotalAttack", () => {
  it("sums autoAttackDamage and attack bonus", () => {
    const combatant = createCombatant({
      id: "test",
      name: "Test",
      hp: 100,
      maxHp: 100,
      autoAttackDamage: 10,
      equipAttackBonus: 5,
    });
    expect(getTotalAttack(combatant)).toBe(15);
  });

  it("includes status buffs", () => {
    const combatant = createCombatant({
      id: "test",
      name: "Test",
      hp: 100,
      maxHp: 100,
      autoAttackDamage: 10,
    });
    const buff: StatusEffect = {
      effectId: "buff",
      remainingMs: 1000,
      dotDamage: 0,
      healPerTick: 0,
      attackBonus: 3,
      defenseBonus: 0,
      isStunned: false,
      isStaggered: false,
      isShield: false,
      slowPct: 0,
      isSilenced: false,
      vulnerabilityPct: 0,
    };
    combatant.statuses.push(buff);
    expect(getTotalAttack(combatant)).toBe(13);
  });

  it("uses default autoAttackDamage of 5", () => {
    const combatant = createCombatant({
      id: "test",
      name: "Test",
      hp: 100,
      maxHp: 100,
    });
    expect(getTotalAttack(combatant)).toBe(5);
  });
});
