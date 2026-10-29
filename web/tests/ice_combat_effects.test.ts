import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { applyAction, makeInitialState } from "../src/core/state.ts";
import {
  absorbIceDamage,
  iceAttackBonus,
  iceShieldPool,
  tickIceEffects,
  ICE_BUFF_DURATION_TICKS,
  ICE_REGEN_DURATION_TICKS,
  ICE_SHIELD_DURATION_TICKS,
} from "../src/core/ice_combat_effects.ts";
import { applyIceNonDamageEffect } from "../src/core/ice_combat_effect_apply.ts";
import type { GameState, Ice, Mission, Program } from "../src/core/types.ts";

const MOCK_MISSION: Mission = {
  id: "test",
  title: "Test",
  fixer: "test",
  arc: 1,
  zone: "test",
  grade_min: 1,
  grade_max: 1,
  rewards: { credits: 10, materials: {} },
};

const MOCK_PROGRAM: Program = {
  id: "p1",
  name: "Atk",
  tier: 1,
  cost: 0,
  effect: "damage",
  description: "test",
  aoe: false,
};

function makeCombatState(overrides: Partial<GameState> = {}): GameState {
  const mockIce: Ice = {
    id: "enemy1",
    name: "Enemy",
    tier: 2,
    hp: 50,
    maxHp: 50,
    armor: 0,
    personality: "aggressive",
    aggression: "standard",
  };
  const state = makeInitialState(MOCK_MISSION, mockIce, [MOCK_PROGRAM]);
  return {
    ...state,
    iceRoster: [mockIce],
    activeIceIndex: 0,
    phase: "combat" as const,
    runPhase: "combat" as const,
    lastEnemyAttackMs: 0,
    dixieLastAttackMs: Date.now(),
    skillCooldowns: {},
    ...overrides,
  };
}

/** An ICE carrying one non-damaging skill. */
function makeEffectIce(
  effect: string,
  magnitude: number,
  overrides: Partial<Ice> = {},
): Ice {
  return {
    id: "caster",
    name: "Caster",
    tier: 2,
    hp: 50,
    maxHp: 50,
    armor: 0,
    personality: "defensive",
    aggression: "standard",
    skills: [
      {
        id: "effect_skill",
        name: "Effect Skill",
        effect,
        cooldownMs: 0,
        damage: 0,
        magnitude,
      },
    ],
    ...overrides,
  };
}

describe("ICE non-damaging skill effects (ADR-0219 Option A)", () => {
  beforeEach(() => {
    vi.spyOn(Math, "random").mockReturnValue(0.01);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("shield", () => {
    it("absorbs incoming damage before the ICE's HP", () => {
      const ice = makeEffectIce("shield", 20);
      const state = makeCombatState({ iceRoster: [ice] });

      const shielded = applyIceNonDamageEffect(state, 0, ice, ice.skills![0]!);
      expect(shielded.message).toContain("shield");

      const absorbed = absorbIceDamage(shielded.state, 0, 12);
      expect(absorbed.absorbed).toBe(12);
      expect(absorbed.damage).toBe(0);
    });

    it("passes the surplus damage to the ICE's HP and shrinks the pool", () => {
      const ice = makeEffectIce("shield", 20);
      const state = makeCombatState({ iceRoster: [ice] });

      const shielded = applyIceNonDamageEffect(state, 0, ice, ice.skills![0]!);
      const absorbed = absorbIceDamage(shielded.state, 0, 30);
      expect(absorbed.absorbed).toBe(20);
      expect(absorbed.damage).toBe(10);
      expect(iceShieldPool(absorbed.state, 0)).toBe(0);
    });

    it("is consumed when the pool is exhausted", () => {
      const ice = makeEffectIce("shield", 20);
      const state = makeCombatState({ iceRoster: [ice] });

      const shielded = applyIceNonDamageEffect(state, 0, ice, ice.skills![0]!);
      expect(shielded.state.statusEffects.filter((e) => e.kind === "shield")).toHaveLength(1);

      const absorbed = absorbIceDamage(shielded.state, 0, 20);
      expect(absorbed.state.statusEffects.filter((e) => e.kind === "shield")).toHaveLength(0);
    });

    it("expires when its duration runs out", () => {
      const ice = makeEffectIce("shield", 20);
      const state = makeCombatState({ iceRoster: [ice] });

      const shielded = applyIceNonDamageEffect(state, 0, ice, ice.skills![0]!);
      expect(shielded.state.statusEffects.filter((e) => e.kind === "shield")).toHaveLength(1);

      let ticked = shielded.state;
      for (let i = 0; i < ICE_SHIELD_DURATION_TICKS; i++) {
        ticked = tickIceEffects(ticked);
      }
      expect(ticked.statusEffects.filter((e) => e.kind === "shield")).toHaveLength(0);
    });

    it("stacks the pool but refreshes the duration instead of adding to it", () => {
      const ice = makeEffectIce("shield", 20);
      const state = makeCombatState({ iceRoster: [ice] });

      const first = applyIceNonDamageEffect(state, 0, ice, ice.skills![0]!);
      const ticked = tickIceEffects(first.state);
      const second = applyIceNonDamageEffect(ticked, 0, ice, ice.skills![0]!);

      expect(iceShieldPool(second.state, 0)).toBe(40);
      const shield = second.state.statusEffects.find((e) => e.kind === "shield");
      expect(shield?.remaining).toBe(ICE_SHIELD_DURATION_TICKS);
    });

    it("protects the ICE from a player program in the combat path", () => {
      // A skill-less ICE so only the pre-applied shield is in play, and a
      // 0.5 RNG so the program deals exactly tier * 5 damage with no crit
      // and no burn / slow proc.
      vi.spyOn(Math, "random").mockReturnValue(0.5);
      const ice: Ice = {
        id: "caster",
        name: "Caster",
        tier: 2,
        hp: 100,
        maxHp: 100,
        armor: 0,
        personality: "defensive",
        aggression: "standard",
      };
      const state = makeCombatState({
        iceRoster: [ice],
        statusEffects: [
          {
            kind: "shield",
            remaining: ICE_SHIELD_DURATION_TICKS,
            magnitude: 20,
            target: "ice",
            iceIndex: 0,
            tickSource: "enemy",
          },
        ],
      });

      const result = applyAction(state, { type: "use_program", programId: "p1" });
      // The program is tier 1 → 5 damage, fully absorbed by the 20 pt pool:
      // the ICE's HP is untouched and the pool is down by exactly 5.
      expect(result.iceRoster[0]?.hp).toBe(100);
      expect(iceShieldPool(result, 0)).toBe(15);
    });

    it("lets the surplus damage reach the ICE's HP in the combat path", () => {
      vi.spyOn(Math, "random").mockReturnValue(0.5);
      const ice: Ice = {
        id: "caster",
        name: "Caster",
        tier: 2,
        hp: 100,
        maxHp: 100,
        armor: 0,
        personality: "defensive",
        aggression: "standard",
      };
      const state = makeCombatState({
        iceRoster: [ice],
        statusEffects: [
          {
            kind: "shield",
            remaining: ICE_SHIELD_DURATION_TICKS,
            magnitude: 3,
            target: "ice",
            iceIndex: 0,
            tickSource: "enemy",
          },
        ],
      });

      const result = applyAction(state, { type: "use_program", programId: "p1" });
      // 5 damage, 3 absorbed by the pool, 2 reaches HP.
      expect(result.iceRoster[0]?.hp).toBe(98);
      expect(iceShieldPool(result, 0)).toBe(0);
    });
  });

  describe("heal", () => {
    it("restores HP immediately", () => {
      const ice = makeEffectIce("heal", 12, { hp: 30, maxHp: 50 });
      const state = makeCombatState({ iceRoster: [ice] });

      const healed = applyIceNonDamageEffect(state, 0, ice, ice.skills![0]!);
      expect(healed.state.iceRoster[0]?.hp).toBe(42);
      expect(healed.message).toContain("restores 12 HP");
    });

    it("never heals above maxHp", () => {
      const ice = makeEffectIce("heal", 40, { hp: 30, maxHp: 50 });
      const state = makeCombatState({ iceRoster: [ice] });

      const healed = applyIceNonDamageEffect(state, 0, ice, ice.skills![0]!);
      expect(healed.state.iceRoster[0]?.hp).toBe(50);
    });

    it("never heals above maxHp in the combat path", () => {
      const ice = makeEffectIce("heal", 40, { hp: 30, maxHp: 50 });
      const state = makeCombatState({ iceRoster: [ice] });

      const result = applyAction(state, { type: "use_program", programId: "p1" });
      // The heal fired (the ICE is above its starting HP) but never past 50.
      expect(result.iceRoster[0]?.hp).toBeGreaterThan(30);
      expect(result.iceRoster[0]?.hp).toBeLessThanOrEqual(50);
    });
  });

  describe("regen", () => {
    it("restores HP over time on every enemy tick", () => {
      const ice = makeEffectIce("regen", 4, { hp: 30, maxHp: 50 });
      const state = makeCombatState({ iceRoster: [ice] });

      const started = applyIceNonDamageEffect(state, 0, ice, ice.skills![0]!);
      const ticked = tickIceEffects(started.state);
      expect(ticked.iceRoster[0]?.hp).toBe(34);
    });

    it("never regenerates above maxHp", () => {
      const ice = makeEffectIce("regen", 40, { hp: 30, maxHp: 50 });
      const state = makeCombatState({ iceRoster: [ice] });

      const started = applyIceNonDamageEffect(state, 0, ice, ice.skills![0]!);
      const ticked = tickIceEffects(started.state);
      expect(ticked.iceRoster[0]?.hp).toBe(50);
    });

    it("expires after its duration", () => {
      const ice = makeEffectIce("regen", 4, { hp: 30, maxHp: 50 });
      const state = makeCombatState({ iceRoster: [ice] });

      const started = applyIceNonDamageEffect(state, 0, ice, ice.skills![0]!);
      expect(started.state.statusEffects.filter((e) => e.kind === "regen")).toHaveLength(1);

      let ticked = started.state;
      for (let i = 0; i < ICE_REGEN_DURATION_TICKS; i++) {
        ticked = tickIceEffects(ticked);
      }
      expect(ticked.statusEffects.filter((e) => e.kind === "regen")).toHaveLength(0);
    });
  });

  describe("buff", () => {
    it("raises the ICE's outgoing damage while it is active", () => {
      const ice = makeEffectIce("buff", 6);
      const state = makeCombatState({ iceRoster: [ice] });

      const buffed = applyIceNonDamageEffect(state, 0, ice, ice.skills![0]!);
      expect(iceAttackBonus(buffed.state, 0)).toBe(6);
    });

    it("expires after its duration", () => {
      const ice = makeEffectIce("buff", 6);
      const state = makeCombatState({ iceRoster: [ice] });

      const buffed = applyIceNonDamageEffect(state, 0, ice, ice.skills![0]!);
      expect(buffed.state.statusEffects.filter((e) => e.kind === "powered")).toHaveLength(1);

      let ticked = buffed.state;
      for (let i = 0; i < ICE_BUFF_DURATION_TICKS; i++) {
        ticked = tickIceEffects(ticked);
      }
      expect(iceAttackBonus(ticked, 0)).toBe(0);
    });

    it("adds to the ICE's auto-attack damage in the combat path", () => {
      // A skill-less ICE so it auto-attacks and the pre-applied buff is the
      // only source of the extra damage.
      vi.spyOn(Math, "random").mockReturnValue(0.5);
      const ice: Ice = {
        id: "caster",
        name: "Caster",
        tier: 2,
        hp: 100,
        maxHp: 100,
        armor: 0,
        personality: "defensive",
        aggression: "standard",
      };
      const buffedState = makeCombatState({
        iceRoster: [ice],
        statusEffects: [
          {
            kind: "powered",
            remaining: ICE_BUFF_DURATION_TICKS,
            magnitude: 6,
            target: "ice",
            iceIndex: 0,
            tickSource: "enemy",
            attackBonus: 6,
          },
        ],
      });
      const plainState = makeCombatState({ iceRoster: [ice] });

      const buffed = applyAction(buffedState, { type: "use_program", programId: "p1" });
      const plain = applyAction(plainState, { type: "use_program", programId: "p1" });

      const buffedDamage = 100 - buffed.player.hp;
      const plainDamage = 100 - plain.player.hp;
      // Base auto-attack is tier 2 * 3 = 6; the buff adds exactly 6 on top.
      expect(buffedDamage - plainDamage).toBe(6);
    });
  });

  describe("inert effects", () => {
    it("leaves every unimplemented effect inert", () => {
      const inert = ["detect", "silence", "slow", "stun", "debuff"];
      for (const effect of inert) {
        const ice = makeEffectIce(effect, 10);
        const state = makeCombatState({ iceRoster: [ice] });
        const outcome = applyIceNonDamageEffect(state, 0, ice, ice.skills![0]!);
        expect(outcome.message).toBeNull();
        expect(outcome.state.statusEffects).toHaveLength(0);
      }
    });
  });
});

describe("ICE effect VFX spawns (ADR-0219 Option A, P2)", () => {
  beforeEach(() => {
    vi.spyOn(Math, "random").mockReturnValue(0.01);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shield spawns a `shield` VFX", () => {
    const ice = makeEffectIce("shield", 20);
    const state = makeCombatState({ iceRoster: [ice] });

    const outcome = applyIceNonDamageEffect(state, 0, ice, ice.skills![0]!);
    expect(outcome.vfx.map((v) => v.kind)).toContain("shield");
  });

  it("heal spawns a `heal` VFX", () => {
    const ice = makeEffectIce("heal", 12, { hp: 30, maxHp: 50 });
    const state = makeCombatState({ iceRoster: [ice] });

    const outcome = applyIceNonDamageEffect(state, 0, ice, ice.skills![0]!);
    expect(outcome.vfx.map((v) => v.kind)).toContain("heal");
  });

  it("regen spawns a `regen` VFX", () => {
    const ice = makeEffectIce("regen", 4, { hp: 30, maxHp: 50 });
    const state = makeCombatState({ iceRoster: [ice] });

    const outcome = applyIceNonDamageEffect(state, 0, ice, ice.skills![0]!);
    expect(outcome.vfx.map((v) => v.kind)).toContain("regen");
  });

  it("buff spawns a `buff` VFX", () => {
    const ice = makeEffectIce("buff", 6);
    const state = makeCombatState({ iceRoster: [ice] });

    const outcome = applyIceNonDamageEffect(state, 0, ice, ice.skills![0]!);
    expect(outcome.vfx.map((v) => v.kind)).toContain("buff");
  });

  it("an inert effect spawns no VFX", () => {
    const ice = makeEffectIce("stun", 10);
    const state = makeCombatState({ iceRoster: [ice] });

    const outcome = applyIceNonDamageEffect(state, 0, ice, ice.skills![0]!);
    expect(outcome.vfx).toHaveLength(0);
  });

  it("the combat path merges the effect VFX into state.vfxInstances", () => {
    // `lastEnemyAttackMs: 0` lets the enemy turn run; the defensive
    // archetype makes the ICE prefer its `shield` skill.
    vi.spyOn(Math, "random").mockReturnValue(0.01);
    const ice = makeEffectIce("shield", 20);
    const state = makeCombatState({
      iceRoster: [ice],
      lastEnemyAttackMs: 0,
    });

    const result = applyAction(state, { type: "use_program", programId: "p1" });
    expect(result.vfxInstances.map((v) => v.kind)).toContain("shield");
  });
});
