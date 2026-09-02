/** Unit tests for status effect state machine (Tier 5.5). */
import { describe, it, expect } from "vitest";
import {
  applyStatus,
  tickStatus,
  applyTickEffects,
  applyBurnDamage,
  rollStatusProc,
} from "../src/core/status.ts";
import type { GameState, Ice, Mission, Program } from "../src/core/types.ts";
import { makeInitialState } from "../src/core/state.ts";

const mockMission: Mission = {
  id: "test", title: "T", fixer: "x", arc: 1, zone: "test",
  grade_min: 1, grade_max: 1, rewards: { credits: 0, materials: {} },
};
const mockIce: Ice = { id: "ice1", name: "ICE", hp: 100, armor: 0, tier: 1 };
const mockPrograms: ReadonlyArray<Program> = [
  { id: "p1", name: "P1", tier: 1, cost: 10, effect: "e", description: "", aoe: false },
];

function baseState(): GameState {
  const state = makeInitialState(mockMission, mockIce, mockPrograms);
  return {
    ...state,
    runPhase: "combat",
    iceRoster: [mockIce],
    activeIceIndex: 0,
  };
}

describe("status state machine (Tier 5.5)", () => {
  describe("applyStatus", () => {
    it("adds a new effect to state", () => {
      const s = baseState();
      const next = applyStatus(s, "ice", "burn", 2, 3);
      expect(next.statusEffects.length).toBe(1);
      expect(next.statusEffects[0]?.kind).toBe("burn");
      expect(next.statusEffects[0]?.remaining).toBe(2);
      expect(next.statusEffects[0]?.magnitude).toBe(3);
      expect(next.statusEffects[0]?.target).toBe("ice");
    });

    it("appends multiple effects (stacks)", () => {
      let s = baseState();
      s = applyStatus(s, "ice", "burn", 2, 3);
      s = applyStatus(s, "player", "stun", 1, 1);
      expect(s.statusEffects.length).toBe(2);
    });
  });

  describe("tickStatus", () => {
    it("decrements remaining on each call", () => {
      let s = applyStatus(baseState(), "ice", "burn", 2, 3);
      s = tickStatus(s);
      expect(s.statusEffects[0]?.remaining).toBe(1);
    });

    it("removes effect when remaining reaches 0", () => {
      let s = applyStatus(baseState(), "ice", "burn", 1, 3);
      s = tickStatus(s);
      expect(s.statusEffects.length).toBe(0);
    });

    it("no-op when no effects to tick (preserves statusEffects array)", () => {
      const s = baseState();
      const next = tickStatus(s);
      // Returns a new state object (post-fix; was buggy same-reference return),
      // but statusEffects array stays empty since no effects to tick.
      expect(next.statusEffects.length).toBe(0);
      expect(next.statusEffects).toEqual(s.statusEffects);
    });
  });

  describe("applyTickEffects", () => {
    it("returns burn damage for ICE", () => {
      let s = applyStatus(baseState(), "ice", "burn", 2, 3);
      const r = applyTickEffects(s);
      expect(r.burnDamageIce).toBe(3);
      expect(r.burnDamagePlayer).toBe(0);
    });

    it("returns burn damage for player", () => {
      let s = applyStatus(baseState(), "player", "burn", 2, 5);
      const r = applyTickEffects(s);
      expect(r.burnDamagePlayer).toBe(5);
      expect(r.burnDamageIce).toBe(0);
    });

    it("detects stun/silence flags", () => {
      let s = applyStatus(baseState(), "ice", "stun", 2, 1);
      s = applyStatus(s, "player", "silence", 2, 1);
      const r = applyTickEffects(s);
      expect(r.iceStunned).toBe(true);
      expect(r.playerSilenced).toBe(true);
    });
  });

  describe("applyBurnDamage", () => {
    it("reduces player HP by player burn damage", () => {
      const s = baseState();
      const next = applyBurnDamage(s, 5, 0);
      expect(next.player.hp).toBe(s.player.hp - 5);
    });

    it("reduces active ICE HP by ice burn damage", () => {
      const s = baseState();
      const next = applyBurnDamage(s, 0, 7);
      expect(next.iceRoster[0]?.hp).toBe(s.iceRoster[0]?.hp! - 7);
    });

    it("clamps HP at 0 (no negative)", () => {
      const s = baseState();
      const next = applyBurnDamage(s, 999, 999);
      expect(next.player.hp).toBe(0);
      expect(next.iceRoster[0]?.hp).toBe(0);
    });

    it("handles no damage (both 0)", () => {
      const s = baseState();
      const next = applyBurnDamage(s, 0, 0);
      expect(next.player.hp).toBe(s.player.hp);
    });
  });

  describe("rollStatusProc (deterministic via rng)", () => {
    it("procs when rng < 0.2", () => {
      expect(rollStatusProc("burn", () => 0.1)).toBe(true);
    });

    it("does not proc when rng >= 0.2", () => {
      expect(rollStatusProc("burn", () => 0.5)).toBe(false);
      expect(rollStatusProc("burn", () => 0.99)).toBe(false);
    });

    it("boundary: rng = 0.19 procs, rng = 0.2 does not", () => {
      expect(rollStatusProc("burn", () => 0.19)).toBe(true);
      expect(rollStatusProc("burn", () => 0.2)).toBe(false);
    });
  });

  describe("end-to-end: apply → tick → burn damage", () => {
    it("burn damage accumulates from multiple burn effects on same target", () => {
      let s = baseState();
      s = applyStatus(s, "ice", "burn", 2, 3);
      s = applyStatus(s, "ice", "burn", 2, 2);
      const r = applyTickEffects(s);
      expect(r.burnDamageIce).toBe(5); // 3 + 2
    });

    it("burn expires after 2 ticks (duration 2)", () => {
      let s = baseState();
      s = applyStatus(s, "ice", "burn", 2, 3);
      s = tickStatus(s); // 2 → 1
      s = tickStatus(s); // 1 → 0, removed
      expect(s.statusEffects.length).toBe(0);
    });
  });

  describe("new status effects (stagger, regen, bleed, fatigue, confused, terrified)", () => {
    it("stagger flag set when stagger effect on ICE", () => {
      let s = applyStatus(baseState(), "ice", "stagger", 2, 1);
      const r = applyTickEffects(s);
      expect(r.iceStaggered).toBe(true);
      expect(r.playerStaggered).toBe(false);
    });

    it("regen heals ICE with healPerTick override", () => {
      let s = applyStatus(baseState(), "ice", "regen", 3, 0, { healPerTick: 3 });
      const r = applyTickEffects(s);
      expect(r.healIce).toBe(3);
      expect(r.healPlayer).toBe(0);
    });

    it("bleed deals dotDamage to ICE", () => {
      let s = applyStatus(baseState(), "ice", "bleed", 2, 5, { dotDamage: 2 });
      const r = applyTickEffects(s);
      expect(r.bleedDamageIce).toBe(2);
      expect(r.bleedDamagePlayer).toBe(0);
    });

    it("fatigue flag set when fatigue on player", () => {
      let s = applyStatus(baseState(), "player", "fatigue", 2, 1);
      const r = applyTickEffects(s);
      expect(r.playerFatigued).toBe(true);
    });

    it("confused flag set when confused on player", () => {
      let s = applyStatus(baseState(), "player", "confused", 2, 1);
      const r = applyTickEffects(s);
      expect(r.playerConfused).toBe(true);
    });

    it("terrified flag set when terrified on player", () => {
      let s = applyStatus(baseState(), "player", "terrified", 3, 1);
      const r = applyTickEffects(s);
      expect(r.playerTerrified).toBe(true);
    });

    it("applyStatus with healPerTick override sets correct field", () => {
      let s = applyStatus(baseState(), "player", "regen", 2, 0, { healPerTick: 5 });
      expect(s.statusEffects[0]?.healPerTick).toBe(5);
    });

    it("applyBurnDamage with heals increases HP", () => {
      let s = baseState();
      s = applyBurnDamage(s, 20, 0);
      const initial = s.player.hp;
      const next = applyBurnDamage(s, 0, 0, 10, 0);
      expect(next.player.hp).toBe(initial + 10);
    });
  });
});